import os, re, shutil, subprocess, sqlite3, time, logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from collections import defaultdict


import requests

# =========================================================


GITHUB_TOKEN       = os.getenv("GITHUB_TOKEN")
HEADERS            = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
BASE_DIR           = Path("jasper_runs_6.11")   # TCL + logs only
REPOS_DIR          = Path("repos_6.11")         # deleted after processing
DB_PATH            = Path("results.db").resolve()
MAX_FILES          = 80
JASPER_TIMEOUT_SEC = 360
#KEEP_REPOS         = False                 # flip to True for debugging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# regex

MODULE_RE      = re.compile(r'\bmodule\s+(\w+)\s*[#(;]', re.M)
ALWAYS_RE      = re.compile(r'\balways\b|\balways_ff\b|\balways_comb\b', re.I)
ASSERT_RE      = re.compile(r'\bassert\s+property\s*\(', re.M)
ASSUME_RE      = re.compile(r'\bassume\s+property\s*\(', re.M)
INCLUDE_RE     = re.compile(r'`include\s+"([^"]+)"')
PACKAGE_USE_RE = re.compile(r'\bimport\s+([\w:]+)\s*;', re.M)
PACKAGE_SCOPE_RE = re.compile(r'\b([\w]+)::')
PACKAGE_DEF_RE = re.compile(r'\bpackage\s+(\w+)\s*;', re.M)
DEFINE_RE      = re.compile(r'`define\s+(\w+)')

# sva capture
SVA_RE = re.compile(
    r'(?:(?P<label>\w+)\s*:\s*)?'
    r'\b(?P<kind>assert|assume|cover)\s+property\s*\((?P<body>[^;]{1,800})\)\s*;',
    re.S,
)

ASSERT_START_RE = re.compile(
    r'(?:(?P<label>\w+)\s*:\s*)?'
    r'(?P<kind>assert|assume|cover)\s+property\s*\(',
    re.I
)

PROPERTY_DEF_RE = re.compile(
    r'property\s+(\w+)\s*;(.*?)endproperty',
    re.S | re.I
)

TB_CONTENT_RE = re.compile(
    r'`uvm_\w+'
    r'|\bclass\s+\w+\s+extends\b'
    r'|\bprogram\s+\w+'
    r'|\binitial\s+begin\b'
    r'|\$finish\b',
    re.M,
)

TB_NAME_RE = re.compile(
    r'(_tb|_test|_sim|_bench|_uvm|tb_|test_|sim_|bench_)', re.I
)


JG_PROP_RE = re.compile(
    r'^\s*(proven|vacuous|cex|unproved|unreachable|inconclusive)\s+(\S+)',
    re.M | re.I,
)

# =========================================================
# DATABASE  — schema stores per-assertion outcomes
# =========================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    repo     TEXT UNIQUE,
    top      TEXT,
    result   TEXT,
    ts       TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS assertions (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    repo     TEXT,
    file     TEXT,
    line     INTEGER,
    kind     TEXT,
    label    TEXT,
    body     TEXT,
    result   TEXT DEFAULT 'UNKNOWN'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_assertion_unique
ON assertions(repo,file,line,label);
"""

def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

def db_save_repo(conn, repo: str, top: Optional[str], result: str):
    conn.execute(
        "INSERT OR REPLACE INTO repos (repo, top, result) VALUES (?,?,?)",
        (repo, top, result)
    )
    conn.commit()

def db_save_assertions(conn, repo: str, assertions: List[dict]):
    for a in assertions:
        conn.execute(
            "INSERT OR IGNORE INTO assertions (repo, file, line, kind, label, body, result) "
            "VALUES (?,?,?,?,?,?,?)",
            (
            repo,
            a["file"],
            a["line"],
            a["kind"],
            a["label"],
            a["body"],
            a.get("result", "UNKNOWN"),
            )
        )
    conn.commit()

# search github

def _search_once(query: str, page: int = 1) -> List[str]:
    while True:
        resp = requests.get(
            "https://api.github.com/search/code",
            headers=HEADERS,
            params={"q": query, "per_page": 50, "page": page},
            timeout=30,
        )
        if resp.status_code in (403, 429):
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 65))
            wait  = max(reset - int(time.time()), 10) + 3
            log.warning("Rate limited — sleeping %ds", wait)
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            log.warning("Search HTTP %d: %s", resp.status_code, resp.text[:120])
            return []
        out = []
        for item in resp.json().get("items", []):
            try:
                out.append(item["repository"]["full_name"])
            except (KeyError, TypeError):
                pass
        return out

def search_repos(max_pages: int = 2) -> List[str]:
    queries = [
        '"assert property" "posedge" language:Verilog',
        '"assert property" "always_ff" language:SystemVerilog',
    ]
    repos: set = set()
    skip_words = ("tutorial","course","homework","lecture","exercise","example","uvm-","uvm_")
    for query in queries:
        for page in range(1, max_pages + 1):
            found = _search_once(query, page=page)
            if not found:
                break
            for name in found:
                if not any(w in name.lower() for w in skip_words):
                    repos.add(name)
            time.sleep(8)
    return sorted(repos)


def clone(repo: str) -> Optional[Path]:
    dest = REPOS_DIR / repo.replace("/", "_")
    if dest.exists():
        return dest
    r = subprocess.run(
        ["git", "clone", "--depth", "1",
         f"https://github.com/{repo}.git", str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        log.warning("Clone failed: %s", r.stderr[:120])
        return None
    return dest



def _read(p: Path) -> str:
    try:
        return p.read_text(errors="ignore")
    except OSError:
        return ""

def strip_comments(txt: str) -> str:
    txt = re.sub(r'//[^\n]*', '', txt)
    txt = re.sub(r'/\*.*?\*/', ' ', txt, flags=re.S)
    return txt

def find_instantiations(files):

    instantiated = set()

    SV_KEYWORDS = {...}

    inst_re = re.compile(
        r'^\s*(\w+)\s*(?:#\s*\(.*?\))?\s+\w+\s*\(',
        re.M | re.S
    )

    for f in files:

        txt = strip_comments(_read(f))

        for m in inst_re.finditer(txt):

            mod_name = m.group(1)

            if mod_name in SV_KEYWORDS:
                continue

            instantiated.add(mod_name)

    return instantiated

def expand_cluster(cluster_files: List[Path]) -> List[Path]:
    # Build proper module -> file map
    module_map = {}
    for f in cluster_files:
        txt = _read(f)
        for m in MODULE_RE.findall(txt):
            module_map[m] = f
    
    expanded = set(cluster_files)

    changed = True
    while changed:
        changed = False

        for f in list(expanded):
            txt = strip_comments(_read(f))

            for inst in find_instantiations([f]):
                if inst in module_map:
                    target = module_map[inst]
                    if target not in expanded:
                        expanded.add(target)
                        changed = True

    return list(expanded)

def collect_files(repo_dir: Path) -> List[Path]:
    found = []
    for p in repo_dir.rglob("*"):
        if p.is_file() and p.suffix in (".v", ".sv", ".svh", ".vh"):
            found.append(p)
        if len(found) >= MAX_FILES * 2:
            break
    return found

def is_tb(p: Path) -> bool:
    if TB_NAME_RE.search(p.stem):
        return True
    return bool(TB_CONTENT_RE.search(_read(p)[:3000]))

def is_rtl(p: Path) -> bool:
    txt = _read(p)
    return bool(MODULE_RE.search(txt))
def has_sva(p: Path) -> bool:
    clean = strip_comments(_read(p))
    return bool(ASSERT_RE.search(clean) or ASSUME_RE.search(clean))

def is_valid(files: List[Path]) -> bool:
    non_tb = [f for f in files if not is_tb(f)]
    return any(is_rtl(f) for f in non_tb) and any(has_sva(f) for f in non_tb)

# finding packages for jasper analysis

"""
def sort_pkg_files(pkg_files):

    pkg_name_to_file = {}
    deps = {}

    for f in pkg_files:

        txt = _read(f)

        m = PACKAGE_DEF_RE.search(txt)

        if not m:
            continue

        pkg_name = m.group(1)

        pkg_name_to_file[pkg_name] = f
        deps[f] = set()

    for f in pkg_files:

        txt = _read(f)

        used_pkgs = set()

        for m in PACKAGE_USE_RE.findall(txt):

            used_pkgs.add(m.split("::")[0])

        for m in PACKAGE_SCOPE_RE.findall(txt):

            used_pkgs.add(m)

        for pkg in used_pkgs:

            if pkg in pkg_name_to_file:

                dep_file = pkg_name_to_file[pkg]

                if dep_file != f:
                    deps[f].add(dep_file)

    ordered = []
    remaining = set(deps.keys())

    while remaining:

        progress = False

        for f in list(remaining):

            if deps[f].issubset(set(ordered)):

                ordered.append(f)
                remaining.remove(f)
                progress = True

        if not progress:

            log.warning(
                "Package dependency cycle detected: %s",
                [x.name for x in remaining]
            )

            ordered.extend(sorted(remaining))
            break

    return ordered
"""

def find_pkg_files(files: List[Path]) -> List[Path]:
    pkg_map: Dict[str, Path] = {}

    for f in files:
        txt = _read(f)

        m = PACKAGE_DEF_RE.search(txt)
        if m and f.suffix in (".sv", ".v"):
            pkg_map[m.group(1)] = f

    return list(pkg_map.values())

def find_header_files(files: List[Path]) -> List[Path]:
    """Find .vh and .svh header files that define macros."""
    headers = []
    for f in files:
        if f.suffix in (".vh", ".svh"):
            headers.append(f)
    return headers

def find_macro_files(files: List[Path]) -> List[Path]:
    """Find files that define macros with `define directive."""
    macro_files = []
    for f in files:
        txt = _read(f)
        if DEFINE_RE.search(txt):
            macro_files.append(f)
    return macro_files

# thus builds include directories

def inc_dirs(repo_dir: Path, files: List[Path]) -> List[str]:
    dirs: set = {repo_dir}
    for f in files:
        dirs.add(f.parent)
        for inc in INCLUDE_RE.findall(_read(f)):
            for base in (f.parent, repo_dir):
                cand = (base / inc).resolve()
                if cand.exists():
                    dirs.add(cand.parent)
    result = []
    for d in sorted(dirs):
        try:
            result.append(str(d.relative_to(repo_dir)))
        except ValueError:
            result.append(str(d))
    return result

# extracting assertions

def extract_property_body(text: str, start_idx: int):
    """
    start_idx should point immediately after
    'assert property('

    Returns:
        (body, end_pos)
    """

    depth = 1
    i = start_idx

    while i < len(text):
        ch = text[i]

        if ch == '(':
            depth += 1

        elif ch == ')':
            depth -= 1

            if depth == 0:
                return text[start_idx:i], i

        i += 1

    return None, None

def extract_assertions(sva_files: List[Path]) -> List[dict]:

    results = []

    seen = set()

    for f in sva_files:

        clean = strip_comments(_read(f))

        property_map = {}

        for name, body in PROPERTY_DEF_RE.findall(clean):
            property_map[name.strip()] = body.strip()

        auto_idx = 0

        for m in ASSERT_START_RE.finditer(clean):

            label = m.group("label") or f"{f.stem}_prop_{auto_idx}"
            auto_idx += 1

            kind = m.group("kind")

            body_start = m.end()

            body, end_pos = extract_property_body(
                clean,
                body_start
            )

            if body is None:
                continue

            body = body.strip()

            # resolve:
            # assert property(my_property);
            if body in property_map:
                body = property_map[body]

            line = clean[:m.start()].count("\n") + 1


            key = (
                f.name,
                line,
                label,
                body
            )

            if key in seen:
                continue
    
            seen.add(key)
            results.append({
                "file": f.name,
                "line": line,
                "kind": kind,
                "label": label,
                "body": body,
                "result": "UNKNOWN",
            })

    return results

def is_standalone_sva_file(p: Path) -> bool:
    """
    True if the file is a dedicated property/checker file (not RTL).
    if has SVA but no always blocks of its own, OR filename
    contains prop/checker/sva/bind.
    """
    name_hints = re.search(r'(prop|checker|sva|bind|assert)', p.stem, re.I)
    if name_hints:
        return True
    txt = _read(p)
    clean = strip_comments(txt)
    has_assert = bool(ASSERT_RE.search(clean) or ASSUME_RE.search(clean))
    has_always = bool(ALWAYS_RE.search(clean))
    return has_assert and not has_always

#def make_bind_file(repo_dir: Path, run_dir: Path, rtl_file: Path,
                   #module_name: str, assertions: List[dict]) -> Optional[Path]:

    #if not assertions:
        #return None

    #checker = f"{module_name}_jg_checker"

    #lines = []
    #lines.append(f"module {checker}(dut);\n")

    #for i, a in enumerate(assertions):
        #label = a["label"] if a["label"] else f"prop_{i}"
        #body = a["body"]

        #lines.append(
            #f"  {label}: assert property ({body});\n"
        #)

    #lines.append("endmodule\n")
    #lines.append(f"bind {module_name} {checker} jg_bind_inst({module_name});\n")

    #path = run_dir / "generated_bindings" / f"{module_name}_bind.sv"
    #path.parent.mkdir(parents=True, exist_ok=True)
    #path.write_text("".join(lines))
    #return path

# top module selection

"""
def pick_top(sva_files, all_files):

    modules = {}

    for f in all_files:
        if is_tb(f):
            continue

        for mod in MODULE_RE.findall(_read(f)):
            modules[mod] = f

    if not modules:
        return None

    instantiated = find_instantiations(all_files)

    candidates = [
        m for m in modules
        if m not in instantiated
    ]

    # debug
    log.info("top candidates: %s", candidates)

    if candidates:
        return max(
            candidates,
            key=lambda m: len(_read(modules[m]))
        )

    return next(iter(modules))
"""

# module hierarchy graph
""""
def build_module_graph(files):
    module_to_file = defaultdict(set)
    edges = defaultdict(set)

    for f in files:
        txt = strip_comments(_read(f))

        mods = MODULE_RE.findall(txt)
        insts = find_instantiations([f])

        for m in mods:
            module_to_file[m].add(f)

        for m in mods:
            for i in insts:
                edges[m].add(i)

    return module_to_file, edges
"""

# generate tcl

def build_tcl(
    run_dir: Path,
    repo_dir: Path,
    cluster_files: List[Path],
    sva_files: List[Path],
    top: Optional[str],
    idirs: List[str],
) -> Path:

    tb_set = set(f for f in cluster_files if is_tb(f))

    rtl_files = [
        f for f in cluster_files
        if not is_tb(f) and is_rtl(f)
    ]

    inc_flag = " ".join(f"-incdir {Path(d).resolve()}" for d in idirs)

    lines = ["clear -all\n\n"]

    # FIRST: Analyze header files (.vh, .svh) with macro definitions
    header_files = find_header_files(cluster_files)
    for f in header_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')
    
    if header_files:
        lines.append("\n")

    # SECOND: Analyze package files
    pkg_files = find_pkg_files(cluster_files)
    for f in pkg_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')
    
    if pkg_files:
        lines.append("\n")

    # THIRD: Analyze macro-defining files
    macro_files = [f for f in find_macro_files(cluster_files) if f not in header_files and f not in pkg_files]
    for f in macro_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')
    
    if macro_files:
        lines.append("\n")

    # FOURTH: Analyze remaining RTL files
    analyzed_set = set(header_files) | set(pkg_files) | set(macro_files)
    remaining_rtl = [f for f in rtl_files if f not in analyzed_set]
    for f in remaining_rtl:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')

    lines.append("\n")

    # FIFTH: Analyze SVA files (may reference packages/macros analyzed above)
    for f in sva_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')

    lines.append("\n")

    if top:
        lines.append(f"""
if {{[catch {{elaborate -top {top}}} err]}} {{
    puts "ELAB ERROR: $err"
}}
""")
    else:
        lines.append("catch {elaborate}\n")

    lines.append("""
clock -list
reset -list
prove -all -time_limit 30s
""")

    lines.append(f"report -all -out {run_dir}/results.rpt\n")
    lines.append(f"report_vacuity -out {run_dir}/vacuity.rpt\n")
    lines.append("exit\n")

    tcl_path = run_dir / "run.tcl"
    tcl_path.write_text("".join(lines))
    return tcl_path


 # running jasper
def run_jasper(run_dir: Path, repo_dir: Path, tcl_path: Path) -> Path:
    log_path = run_dir / "jasper.log"

    # Clean up stale Jasper project directory
    jgproject = repo_dir / "jgproject"
    if jgproject.exists():
        shutil.rmtree(jgproject, ignore_errors=True)

    cmd = [
        "jg",
        "-allow_unsupported_OS",
        "-batch",
        str(tcl_path.resolve())
    ]

    log.info("Running Jasper: %s", " ".join(cmd))
    
    try:
        with open(log_path, "w") as logf:
            result = subprocess.run(
                cmd,
                cwd=repo_dir,
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=JASPER_TIMEOUT_SEC,
            )
            log.info("Jasper exited with code %d", result.returncode)

    except subprocess.TimeoutExpired:
        log.warning(
            "Jasper timed out after %ds",
            JASPER_TIMEOUT_SEC
        )
    except Exception as e:
        log.error("Error running Jasper: %s", e)

    return log_path

# =========================================================
# RESULT PARSING  — per-property AND repo-level
# =========================================================

def parse_results(run_dir: Path, assertions: List[dict]) -> Tuple[str, List[dict]]:
    """
    Returns:
        repo_result  : str  — overall repo outcome
        assertions   : list — each dict updated with 'result' key

    Per-property result values:  PROVEN / VACUOUS / FAIL_CEX / UNPROVED / UNKNOWN
    Repo-level result values:    PROVEN / VACUOUS / FAIL_CEX / FAIL / COMPILE_FAIL / UNKNOWN
    """
    rpt_path = run_dir / "results.rpt"
    vac_path = run_dir / "vacuity.rpt"
    log_path = run_dir / "jasper.log"

    log_txt = log_path.read_text(errors="ignore") if log_path.exists() else ""
    rpt_txt = rpt_path.read_text(errors="ignore") if rpt_path.exists() else ""
    vac_txt = vac_path.read_text(errors="ignore") if vac_path.exists() else ""

    if not rpt_path.exists():
        err_lines = [l for l in log_txt.splitlines() if "ERROR" in l][:10]
        return "COMPILE_FAIL", assertions

    # splits into proven, vacuous, fail+cex, unproven
    prop_results: Dict[str, str] = {}
    for m in JG_PROP_RE.finditer(rpt_txt):
        status = m.group(1).lower()
        name   = m.group(2)
        if "vacuous" in status:
            prop_results[name] = "VACUOUS"
        elif "cex" in status or "fail" in status:
            prop_results[name] = "FAIL_CEX"
        elif "proven" in status or "passed" in status:
            prop_results[name] = "PROVEN"
        elif "unproved" in status or "inconclusive" in status:
            prop_results[name] = "UNPROVED"

    # Also scan vacuity report
    for m in JG_PROP_RE.finditer(vac_txt):
        name = m.group(2)
        if "vacuous" in m.group(1).lower():
            prop_results[name] = "VACUOUS"

    #is this needed?
    for a in assertions:
        label = a.get("label", "")
        if label and label in prop_results:
            a["result"] = prop_results[label]
            if a["result"] == "VACUOUS":
                a["assessment"] = "WEAK"

            elif a["result"] == "PROVEN":
                a["assessment"] = "LIKELY_VALID"

            elif a["result"] == "FAIL_CEX":
                a["assessment"] = "RTL_OR_ASSERTION_BUG"

            elif a["result"] == "UNPROVED":
                a["assessment"] = "INCONCLUSIVE"

            else:
                a["assessment"] = "UNKNOWN"
        # else stays UNKNOWN (property was analyzed but not individually tracked)

    # --- repo-level summary ---
    results_set = set(a["result"] for a in assertions)
    rpt_low = rpt_txt.lower()

    if "VACUOUS" in results_set:
        repo_result = "VACUOUS"
    elif "FAIL_CEX" in results_set:
        repo_result = "FAIL_CEX"
    elif "UNPROVED" in results_set:
        repo_result = "FAIL"
    elif "PROVEN" in results_set:
        repo_result = "PROVEN"
    elif "proven" in rpt_low:
        repo_result = "PROVEN"
    elif "cex" in rpt_low or "counterexample" in rpt_low:
        repo_result = "FAIL_CEX"
    elif "unproved" in rpt_low or "failed" in rpt_low:
        repo_result = "FAIL"
    else:
        repo_result = "UNKNOWN"

    prop_file = run_dir / "properties.csv"
    if prop_file.exists():

        for line in prop_file.read_text(
            errors="ignore"
        ).splitlines():

            parts = line.split(",")

            if len(parts) != 2:
                continue

            name, status = parts

            status = status.lower()

            if "vacuous" in status:
                prop_results[name] = "VACUOUS"

            elif "proven" in status:
                prop_results[name] = "PROVEN"

            elif "cex" in status:
                prop_results[name] = "FAIL_CEX"

            elif "unproved" in status:
                prop_results[name] = "UNPROVED"

    return repo_result, assertions

# debug
def try_elaborate(log_path: Path) -> bool:

    txt = log_path.read_text(errors="ignore")

    if "No design modules are defined" in txt:
        return False

    if "ELAB ERROR" in txt:
        return False

    return True

def cluster_repo_files(files: List[Path]):
    # First pass: separate header files upfront
    header_files = [f for f in files if f.suffix in (".vh", ".svh")]
    non_header_files = [f for f in files if f.suffix not in (".vh", ".svh")]
    
    clusters = defaultdict(list)
    
    # Build module -> file map to find top modules (not instantiated)
    module_map = {}
    instantiated = set()
    
    for f in non_header_files:
        txt = _read(f)
        mods = MODULE_RE.findall(txt)
        for m in mods:
            module_map[m] = f
        instantiated.update(find_instantiations([f]))
    
    # Find uninstantiated modules (top-level candidates)
    top_candidates = set(module_map.keys()) - instantiated

    for f in non_header_files:
        txt = _read(f)
        mods = MODULE_RE.findall(txt)
        pkgs = PACKAGE_DEF_RE.findall(txt)
        asserts = len(ASSERT_RE.findall(txt))

        if pkgs:
            # Packages go in their own cluster
            key = f"pkg_{pkgs[0]}"
        elif mods:
            # Group by top-level (non-instantiated) modules
            top_mod = next((m for m in mods if m in top_candidates), None)
            if top_mod:
                key = f"proj_{top_mod}"
            else:
                # If no top-level, use largest module
                key = f"proj_{max(mods, key=lambda m: len(_read(module_map[m])))}"
        elif asserts:
            key = f"sva_{f.stem}"
        else:
            key = "misc"

        clusters[key].append(f)

    # ADD HEADER FILES TO ALL NON-MISC CLUSTERS
    for cluster_id in list(clusters.keys()):
        if cluster_id != "misc":
            clusters[cluster_id].extend(header_files)

    return clusters

def enforce_project_closure(cluster_files: List[Path]) -> List[Path]:

    # build module -> file map inside this cluster only
    module_map = {}

    for f in cluster_files:
        txt = _read(f)
        for m in MODULE_RE.findall(txt):
            module_map[m] = f

    # expand using instantiation graph until stable
    expanded = set(cluster_files)

    changed = True
    while changed:
        changed = False

        for f in list(expanded):
            txt = strip_comments(_read(f))
            insts = find_instantiations([f])

            for inst in insts:
                if inst in module_map:
                    target = module_map[inst]
                    if target not in expanded:
                        expanded.add(target)
                        changed = True

    return list(expanded)

def process_repo(repo: str, conn: sqlite3.Connection) -> None:
    log.info("== %s", repo)

    repo_dir = clone(repo)
    if repo_dir is None:
        return

    try:
        files = collect_files(repo_dir)

        if not files:
            log.info("skip: no HDL files")
            return

        clusters = cluster_repo_files(files)

        run_dir = BASE_DIR / repo.replace("/", "_")
        run_dir.mkdir(parents=True, exist_ok=True)

        for cluster_id, cluster_files in clusters.items():

            cluster_files = expand_cluster(cluster_files)
            
            non_tb = [f for f in cluster_files if not is_tb(f)]
            
            # Separate headers from RTL/SVA for analysis purposes
            header_files = [f for f in non_tb if f.suffix in (".vh", ".svh")]
            rtl_sva_files = [f for f in non_tb if f.suffix not in (".vh", ".svh")]
            
            rtl_files = [f for f in rtl_sva_files if is_rtl(f)]
            sva_files = [f for f in rtl_sva_files if has_sva(f)]

            log.info("cluster=%s: %d files (%d headers), %d rtl, %d sva", cluster_id, len(cluster_files), len(header_files), len(rtl_files), len(sva_files))

            if not rtl_files or not sva_files:
                log.info("cluster=%s: skipped (no rtl=%s or no sva=%s)", cluster_id, not rtl_files, not sva_files)
                continue

            standalone_sva = [
                f for f in sva_files
                if is_standalone_sva_file(f)
            ]

            embedded_sva = [
                f for f in sva_files
                if not is_standalone_sva_file(f)
            ]

            all_sva = standalone_sva + embedded_sva

            assertions = extract_assertions(all_sva)

            idirs = inc_dirs(repo_dir, cluster_files)

            # TOP SELECTION (cluster-local)
            candidate_tops = []
            for f in rtl_files:
                candidate_tops.extend(MODULE_RE.findall(_read(f)))

            candidate_tops = list(dict.fromkeys(candidate_tops))

            preferred = []
            for t in candidate_tops:
                score = 0
                name = t.lower()

                if "top" in name: score += 10
                if "core" in name: score += 8
                if "tb" in name: score -= 20
                if any(x in name for x in ["fifo", "ram", "mem", "mux"]):
                    score -= 5

                preferred.append((score, t))

            candidate_tops = [t for _, t in sorted(preferred, reverse=True)]

            successful_top = None

            for top in candidate_tops:

                log.info("cluster=%s trying top=%s", cluster_id, top)

                tcl_path = build_tcl(
                    run_dir,
                    repo_dir,
                    cluster_files,
                    all_sva,
                    top,
                    idirs
                )

                log_path = run_jasper(run_dir, repo_dir, tcl_path)

                if try_elaborate(log_path):
                    successful_top = top
                    break

    finally:
        shutil.rmtree(repo_dir, ignore_errors=True)



def main():
    BASE_DIR.mkdir(exist_ok=True)
    REPOS_DIR.mkdir(exist_ok=True)

    conn = init_db()
    repos = search_repos(max_pages=2)
    log.info("Found %d candidate repos", len(repos))

    for repo in repos:
        try:
            process_repo(repo, conn)
        except Exception as exc:
            log.exception("Unhandled error on %s: %s", repo, exc)

    conn.close()


if __name__ == "__main__":
    main()