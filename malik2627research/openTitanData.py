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
ASSERT_RE = re.compile(r"`ASSERT[A-Z_]*\s*\((.*?)\)", re.DOTALL)

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

def collect_assertions(sv_file):
    tree = SyntaxTree.fromFile(str(sv_file))
    assertions = []

    def visit(node):
        # Tokens are leaf objects with no 'kind' or 'to_json' — skip them
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


# ── 3. Build and save the intent sidecar ──────────────────────────────────────

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
        module_intents[rel] = load_module_intent(sv_file)

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
    intent_doc = build_and_save_intent(ip_dir, ip_name, output_dir)
    ip_intent = intent_doc["ip_intent"]
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
                    # attach both layers of intent
                    "module_intent": module_intents.get(_rel, {}),
                    "ip_intent": ip_intent,
                })
            return True

        tree.root.visit(visit)

    return module_dataset

# must handle cases for multireg/window entries later
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
            {
            "intent_id":
            f"{ip_name}.interrupt.{i['name']}",
            "name": i["name"],
            "desc": i.get("desc", "")
            }
            for i in data.get("interrupt_list", [])
        ],
        "alerts": [
            {"intent_id":
        f"{ip_name}.alert.{a['name']}", "name": a["name"], "desc": a.get("desc", "")}
            for a in data.get("alert_list", [])
        ],
        "registers": [
            {
                "intent_id":
                f"{ip_name}.reg.{r['name']}",
                "name": r["name"],
                "desc": r.get("desc", ""),
                "fields": [
                    {
                        "intent_id":
                        f"{ip_name}.reg.{r['name']}.{f.get('name')}",
                        "name": f.get("name"),
                        "desc": f.get("desc", ""),
                        "bits": f.get("bits"),
                        "swaccess": f.get("swaccess"),
                        "hwaccess": f.get("hwaccess"),
                    }
                    for f in r.get("fields", [])
                ],
            }
            for r in data.get("registers", [])
            if isinstance(r, dict) and "name" in r
        ],
    }

def build_ip_dataset(ip_name, opentitan_root):
    ip_dir = get_ip_root(
        opentitan_root,
        ip_name
    )

    structure = collect_ip(ip_dir)

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
                instances.append(str(node))

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
            all_modules.extend(modules)
        except FileNotFoundError as e:
            # some IPs have no hjson (e.g. vendored or auto-generated ones)
            print(f"  Skipping {ip_name}: {e}")
            continue

    with open("opentitan_dataset.json", "w") as f:
        json.dump(all_modules, f, indent=2)

    print(f"Saved {len(all_modules)} modules to opentitan_dataset.json")
    print(f"Intent sidecars saved to {output_dir}/")

if __name__ == "__main__":
    main()