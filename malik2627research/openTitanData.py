import os
import re
import requests
import json
from pathlib import Path
import subprocess
import hjson
import pyslang
from pyslang.syntax import SyntaxTree
import networkx as nx
from collections import defaultdict

# global config
OPENTITAN_REPO = "https://github.com/lowRISC/opentitan.git"

#regex
MODULE_RE = re.compile(
    r"^\s*module\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    re.MULTILINE
)

#later should omit ASSERT_RE
ASSERT_RE = re.compile(r"`ASSERT[A-Z_]*\s*\((.*?)\)", re.DOTALL)
ASSERT_MACRO_RE = re.compile(
    r'`(?P<macro>'
    r'ASSERT_KNOWN_IF'
    r'|ASSERT_KNOWN'
    r'|ASSERT_NEVER_KNOWN'
    r'|ASSERT_NEVER'
    r'|ASSERT_IF'
    r'|ASSERT_INIT_NET'
    r'|ASSERT_INIT'
    r'|ASSERT_FINAL'
    r'|ASSERT_ERROR_TRIGGER_ALERT'
    r'|ASSUME_FPV'
    r'|ASSUME'
    r'|COVER'
    r'|ASSERT'           # keep generic ASSERT last so named ones match first
    r')\s*\((?P<args>[^;]+?)\)',
    re.MULTILINE | re.DOTALL
)

# to extract in-file info
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENTS  = re.compile(r"((?:^\s*//[^\n]*\n)+)", re.MULTILINE)

def ensure_opentitan(repo_dir="data/opentitan"):

    repo_dir = Path(repo_dir)

    if not repo_dir.exists():

        subprocess.run([
            "git",
            "clone",
            "--depth", "1",
            "--filter=blob:none",
            OPENTITAN_REPO,
            str(repo_dir)
        ], check=True)

    else:

        subprocess.run(
            ["git", "-C", str(repo_dir), "pull"],
            check=True
        )

    return repo_dir

def classify_sv_file(path):

    s = str(path)

    if "/dv/sva/" in s:
        return "sva"

    if "/rtl/" in s:

        name = path.name.lower()

        if "reg_top" in name:
            return "reg_top"

        if "reg_pkg" in name:
            return "reg_pkg"

        if "pkg" in name:
            return "packages"

        return "rtl"

    return "other"

def get_ip_root(opentitan_root, ip_name):
    return Path(opentitan_root) / "hw" / "ip" / ip_name

def discover_ips(opentitan_root):

    ip_root = Path(opentitan_root) / "hw" / "ip"

    return sorted(
        p.name
        for p in ip_root.iterdir()
        if p.is_dir()
    )

def parse_macro_assert(macro_name: str, args_raw: str, lineno: int) -> dict:
    """Split macro args into structured fields where possible."""
    # Strip comments from args
    args_clean = re.sub(r'//[^\n]*', '', args_raw).strip()
    parts = [a.strip() for a in re.split(r',(?![^()]*\))', args_clean)]

    result = {
        "kind":  "macro",
        "macro": macro_name,
        "line":  lineno,
        "raw":   f"`{macro_name}({args_raw.strip()})",
    }

    # Most OpenTitan assert macros follow: (NAME, EXPRESSION [, CLK, RST])
    if len(parts) >= 1:
        result["name"]       = parts[0]
    if len(parts) >= 2:
        result["expression"] = parts[1]
    if len(parts) >= 3:
        result["clock"]      = parts[2]
    if len(parts) >= 4:
        result["reset"]      = parts[3]

    return result

def collect_macro_assertions(sv_path: Path) -> list[dict]:
    """Regex scan for backtick assert macros — catches what pyslang misses."""
    text = sv_path.read_text(errors="replace")
    results = []
    for m in ASSERT_MACRO_RE.finditer(text):
        lineno = text[: m.start()].count("\n") + 1
        results.append(parse_macro_assert(m.group("macro"), m.group("args"), lineno))
    return results

def collect_assertions(sv_file):
    ast_assertions  = collect_ast_assertions(sv_file)
    macro_assertions = collect_macro_assertions(sv_file)
    return ast_assertions + macro_assertions

def collect_ast_assertions(sv_file: Path) -> list[dict]:
        # Tokens are leaf objects with no 'kind' or 'to_json' — skip them
    tree = SyntaxTree.fromFile(str(sv_file))
    assertions = []

    def visit(node):
        if not hasattr(node, "to_json"):
            return True
        k = str(node.kind)
        if "Assert" in k:
            try:
                assertions.append(node.to_json())
            except Exception:
                assertions.append({"raw": str(node), "kind": k})
        return True

    tree.root.visit(visit)
    return assertions

def collect_docs(ip_dir):

    docs = []

    for p in ip_dir.rglob("*.md"):

        docs.append({
            "file": str(p.relative_to(ip_dir)),
            "text": p.read_text(
                errors="ignore"
            )
        })

    return docs

def extract_modules(tree):
    modules = []

    def visit(node):

        if type(node).__name__ == "ModuleDeclarationSyntax":
            modules.append(node)

        return True

    tree.root.visit(visit)

    return modules

# thin AST layer for ports
def extract_ports(tree):
    """Return a list of port string representations from a parsed SyntaxTree."""
    ports = []

    def visit(node):
        if "Port" in type(node).__name__:
            ports.append(str(node))
        return True

    tree.root.visit(visit)   
    return ports            

def extract_signals(tree):

    signals = []

    def visit(node):

        if type(node).__name__ == "DataDeclarationSyntax":

            try:
                signals.append(node.to_json())
            except:
                pass

        return True

    tree.root.visit(visit)

    return signals

def classify_signal(signal_name):
    name = signal_name.lower()

    if name.endswith("_i"):
        return "input"

    if name.endswith("_o"):
        return "output"

    if name.endswith("_q"):
        return "register"

    if name.endswith("_d"):
        return "next_state"

    if "valid" in name:
        return "valid"

    if "ready" in name:
        return "ready"

    if "req" in name:
        return "request"

    if "rsp" in name:
        return "response"

    if "intr" in name:
        return "interrupt"

    if "alert" in name:
        return "alert"

    return "other"

def extract_signal_roles(tree):
    roles = []

    for sig in extract_signals(tree):
        try:

            name = sig["declarators"][0]["name"]

            roles.append({
                "signal": name,
                "role": classify_signal(name)
            })

        except Exception:
            pass

    return roles

def extract_always_blocks(tree):
    blocks = []

    def visit(node):

        name = type(node).__name__

        if (
            "AlwaysFF" in name
            or "AlwaysComb" in name
            or "Always" in name
        ):

            try:

                blocks.append({
                    "type": name,
                    "text": str(node)[:500]
                })

            except Exception:
                pass

        return True

    tree.root.visit(visit)

    return blocks

def extract_assigns(tree):

    assigns = []

    def visit(node):

        if type(node).__name__ == "ContinuousAssignSyntax":

            try:
                assigns.append(str(node))
            except:
                pass

        return True

    tree.root.visit(visit)

    return assigns


def extract_interface(tree):
    signals = json.dumps(
        extract_signals(tree)
    ).lower()

    interfaces = []

    if "valid" in signals and "ready" in signals:

        interfaces.append({
            "type": "ready_valid"
        })

    if "req" in signals and "rsp" in signals:

        interfaces.append({
            "type": "req_rsp"
        })

    if "tl_h" in signals:

        interfaces.append({
            "type": "tlul"
        })

    return interfaces
#                                                   #
# intent loading, comment extraction, dataset constr.

def extract_module_doc_comment(sv_path: Path) -> str:
    text = sv_path.read_text(errors="replace")

    # Find position of first `module` keyword
    module_match = re.search(r"\bmodule\b", text)
    if not module_match:
        return ""

    preamble = text[: module_match.start()]

    # Prefer the last block comment in the preamble
    block_matches = list(_BLOCK_COMMENT.finditer(preamble))
    if block_matches:
        raw = block_matches[-1].group()
        # Strip /* */ and leading * on each line
        inner = re.sub(r"^/\*+|\*+/$", "", raw, flags=re.MULTILINE).strip()
        inner = re.sub(r"^\s*\*", "", inner, flags=re.MULTILINE)
        return inner.strip()

    # Fallback: last run of // lines
    line_matches = list(_LINE_COMMENTS.finditer(preamble))
    if line_matches:
        raw = line_matches[-1].group()
        lines = [re.sub(r"^\s*//\s?", "", l) for l in raw.splitlines()]
        return "\n".join(lines).strip()

    return ""


def extract_module_params(sv_path: Path) -> list[dict]:
    """
    Extract parameter names and optional inline comments from the .sv source.
    e.g.  parameter int unsigned FifoDepth = 16; // depth of the request FIFO
    """
    text = sv_path.read_text(errors="replace")
    pattern = re.compile(
        r"\bparameter\b[^;]*?\b(\w+)\s*=\s*([^;,\n]+?)(?:\s*//\s*(.+?))?\s*[;,\n]"
    )
    params = []
    for m in pattern.finditer(text):
        params.append({
            "name": m.group(1),
            "default": m.group(2).strip(),
            "desc": (m.group(3) or "").strip(),
        })
    return params


def load_module_intent(sv_path: Path) -> dict:
    return {
        "doc_comment": extract_module_doc_comment(sv_path),
        "params": extract_module_params(sv_path),
    }


# generates intent folders

def build_and_save_intent(ip_dir: Path, ip_name: str, output_dir: Path) -> dict:
    """
    Builds a two-layer intent document:
      - ip_intent:      from the hjson
      - module_intents: one entry per .sv RTL file

    Saves to  <output_dir>/<ip_name>.intent.json  and also returns the dict.
    """
    ip_intent = load_ip_intent(ip_dir, ip_name)

    module_intents = {}
    for sv_file in sorted(ip_dir.rglob("*.sv")):
        if classify_sv_file(sv_file) != "rtl":
            continue
        rel = str(sv_file.relative_to(ip_dir))
        module_intents[rel] = {
            **load_module_intent(sv_file),
            "assertions": collect_assertions(sv_file)
        }

    intent_doc = {
        "ip_name": ip_name,
        "ip_intent": ip_intent,
        "module_intents": module_intents,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{ip_name}.intent.json"
    out_path.write_text(json.dumps(intent_doc, indent=2))
    print(f"Saved intent → {out_path}")

    return intent_doc


# ── 4. Merge into collect_ip ───────────────────────────────────────────────────

def collect_ip(ip_dir: Path, ip_name: str, output_dir: Path) -> list[dict]:
    intent_doc = {
    "ip_name": ip_name,
    "ip_intent": load_ip_intent(ip_dir, ip_name),
    "module_intents": {}
    }

    for sv_file in sorted(ip_dir.rglob("*.sv")):
        if classify_sv_file(sv_file) != "rtl":
            continue

        rel = str(sv_file.relative_to(ip_dir))
        intent_doc["module_intents"][rel] = load_module_intent(sv_file)
    ip_intent = intent_doc["ip_intent"]
    field_summary = extract_register_field_summary(ip_intent)
    module_intents = intent_doc["module_intents"]

    module_dataset = []

    for p in ip_dir.rglob("*.sv"):
        if classify_sv_file(p) != "rtl":
            continue

        tree = SyntaxTree.fromFile(str(p))
        raw_assertions = collect_assertions(p)
        assertions = [
            {
                "assertion_id": f"{p.stem}.assert.{i}",
                "raw": a
            }
            for i, a in enumerate(raw_assertions)
        ]
        ports = extract_ports(tree)
        rel = str(p.relative_to(ip_dir))

        def visit(node, _p=p, _rel=rel):
            if type(node).__name__ == "ModuleDeclarationSyntax":
                module_dataset.append({
                    "module_name": get_module_name(node),
                    "instantiations": extract_instantiations(tree),
                    "file": _rel,
                    "assertions": assertions,
                    "ports": ports,
                    "assigns": extract_assigns(tree),
                    "signals": extract_signals(tree),
                    "signal_roles": extract_signal_roles(tree),
                    "interfaces": extract_interface(tree),
                    "field_summary": field_summary,
                    "fsms": extract_fsms(tree),
                    "always_blocks": extract_always_blocks(tree),
                    # attach both layers of intent
                    "module_intent": module_intents.get(_rel, {}),
                    "ip_intent": ip_intent
                })
            return True

        tree.root.visit(visit)

    return module_dataset

def extract_register_field_summary(ip_intent):
    fields = []

    for reg in ip_intent.get("registers", []):
        for field in reg.get(
            "fields",
            []
        ):

            fields.append({

                "register": reg["name"],

                "field": field["name"],

                "desc": field["desc"]
            })

    return fields

# must handle cases for multireg/window entries later
def flatten_registers(registers: list, ip_name: str) -> list:
    """Expand multireg/window entries alongside normal registers."""
    result = []
    for r in registers:
        if not isinstance(r, dict):
            continue

        # Normal register
        if "name" in r:
            result.append({
                "intent_id": f"{ip_name}.reg.{r['name']}",
                "name": r["name"],
                "desc": r.get("desc", ""),
                "kind": "register",
                "field_count": len(r.get("fields", [])),
                "fields": [
                    {
                        "intent_id": f"{ip_name}.reg.{r['name']}.{f.get('name')}",
                        "name": f.get("name"),
                        "desc": f.get("desc", ""),
                        "bits": f.get("bits"),
                        "swaccess": f.get("swaccess"),
                        "hwaccess": f.get("hwaccess"),
                    }
                    for f in r.get("fields", [])
                ],
            })

        # Multireg — contains a repeated register definition
        elif "multireg" in r:
            mr = r["multireg"]
            name = mr.get("name", "UNKNOWN")
            result.append({
                "intent_id": f"{ip_name}.reg.{name}",
                "name": name,
                "desc": mr.get("desc", ""),
                "kind": "multireg",
                "count": mr.get("count"),
                "fields": [
                    {
                        "intent_id": f"{ip_name}.reg.{name}.{f.get('name')}",
                        "name": f.get("name"),
                        "desc": f.get("desc", ""),
                        "bits": f.get("bits"),
                        "swaccess": f.get("swaccess"),
                        "hwaccess": f.get("hwaccess"),
                    }
                    for f in mr.get("fields", [])
                ],
            })

        # Window — a memory-mapped region, no fields
        elif "window" in r:
            w = r["window"]
            name = w.get("name", "UNKNOWN")
            result.append({
                "intent_id": f"{ip_name}.reg.{name}",
                "name": name,
                "desc": w.get("desc", ""),
                "kind": "window",
                "items": w.get("items"),
                "swaccess": w.get("swaccess"),
                "fields": [],
            })

    return result


def load_ip_intent(ip_dir, ip_name):
    hjson_path = Path(ip_dir) / "data" / f"{ip_name}.hjson"
    data = hjson.loads(hjson_path.read_text())

    return {
        "ip_name": ip_name,
        "one_line_desc": data.get("one_line_desc", ""),
        "one_paragraph_desc": data.get("one_paragraph_desc", ""),
        "clocking": [
            {"clock": c.get("clock"), "reset": c.get("reset"), "primary": c.get("primary", False)}
            for c in data.get("clocking", [])
        ],
        "bus_interfaces": [
            {"protocol": b.get("protocol"), "direction": b.get("direction")}
            for b in data.get("bus_interfaces", [])
        ],
        "param_list": [
            {"name": p["name"], "desc": p.get("desc", ""), "default": p.get("default")}
            for p in data.get("param_list", [])
            if isinstance(p, dict) and "name" in p
        ],
        "interrupts": [
            {"intent_id": f"{ip_name}.interrupt.{i['name']}", "name": i["name"], "desc": i.get("desc", "")}
            for i in data.get("interrupt_list", [])
        ],
        "alerts": [
            {"intent_id": f"{ip_name}.alert.{a['name']}", "name": a["name"], "desc": a.get("desc", "")}
            for a in data.get("alert_list", [])
        ],
        "registers": flatten_registers(data.get("registers", []), ip_name),
    }

def build_ip_dataset(ip_name, opentitan_root):
    ip_dir = get_ip_root(
        opentitan_root,
        ip_name
    )

    structure = collect_ip(
        ip_dir,
        ip_name,
        Path("intent")
    )

    docs = collect_docs(ip_dir)

    intent = load_ip_intent(
        ip_dir,
        ip_name
    )

    return {
        "ip_name": ip_name,
        "structure": structure,
        "docs": docs,
        "intent": intent
    }

# module hierarchy construction
def extract_instantiations(tree):
    instances = []

    def visit(node):

        if type(node).__name__ == "HierarchyInstantiationSyntax":

            try:
                instances.append({"instance": str(node)})

            except Exception:
                pass

        return True

    tree.root.visit(visit)

    return instances
# bs module
def get_module_name(node):
    try:
        return node.header.name.value
    except:
        try:
            return node.header.blockName.value
        except:
            return "unknown"

def extract_fsms(tree):
    fsms = []

    states = defaultdict(set)

    def visit(node):

        try:
            text = str(node)

            m = re.search(
                r'(\w+_q)\s*<=\s*(\w+)',
                text
            )

            if m:
                state_reg = m.group(1)
                next_state = m.group(2)

                if re.match(
                    r'[A-Z][A-Z0-9_]*',
                    next_state
                ):
                    states[state_reg].add(
                        next_state
                    )

        except Exception:
            pass

        return True

    tree.root.visit(visit)

    return [
        {
            "state_reg": reg,
            "states": sorted(list(vals))
        }
        for reg, vals in states.items()
    ]

def main():
    opentitan_root = ensure_opentitan()

    ips = discover_ips(opentitan_root)
    all_modules = []
    output_dir = Path("intent")  # sidecar .intent.json files go here

    for ip_name in ips:
        ip_dir = get_ip_root(opentitan_root, ip_name)

        if not ip_dir.exists():
            continue

        print(f"Processing IP: {ip_name}")
        try:
            modules = collect_ip(ip_dir, ip_name, output_dir)

            per_ip_file = output_dir / f"{ip_name}.intent.json"
            per_ip_file.write_text(
                json.dumps(modules, indent=2)
            )
            all_modules.extend(modules)
        except FileNotFoundError as e:
            # some IPs have no hjson (e.g. vendored or auto-generated ones)
            print(f"  Skipping {ip_name}: {e}")
            continue

    print(
    "Total assertions:", sum(
        len(m["assertions"])
        for m in all_modules
    )
    )   

    with open("opentitan_dataset.json", "w") as f:
        json.dump(all_modules, f, indent=2)

    print(f"Saved {len(all_modules)} modules to opentitan_dataset.json")
    print(f"Intent sidecars saved to {output_dir}/")

if __name__ == "__main__":
    main()