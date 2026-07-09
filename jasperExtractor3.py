import os, re, shutil, subprocess, sqlite3, time, logging, traceback
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from collections import defaultdict
import networkx as nx


import requests

# =========================================================


GITHUB_TOKEN       = os.getenv("GITHUB_TOKEN")
HEADERS            = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
BASE_DIR           = Path("jasper_runs_6.24")   # TCL + logs only
REPOS_DIR          = Path("repos_6.24")         # deleted after processing
DB_PATH            = Path("results.db").resolve()
MAX_FILES          = 80
JASPER_TIMEOUT_SEC = 360
MAX_TOP_TRIES      = 3
CLEAN_CLONES       = True
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
        if CLEAN_CLONES:
            shutil.rmtree(dest, ignore_errors=True)
        else:
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


def find_pkg_files(files: List[Path]) -> List[Path]:
    pkg_map: Dict[str, Path] = {}

    for f in files:
        txt = _read(f)

        m = PACKAGE_DEF_RE.search(txt)
        if m and f.suffix in (".sv", ".v"):
            pkg_map[m.group(1)] = f

    return list(pkg_map.values())

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
# generate tcl

def build_tcl(
    run_dir: Path,
    repo_dir: Path,
    cluster_files: List[Path],
    sva_files: List[Path],
    top: Optional[str],
    idirs: List[str],
) -> Path:

    # Dedupe cluster files by resolved absolute path to avoid re-analyzing same headers
    seen_paths = set()
    uniq_cluster_files = []
    for _f in cluster_files:
        try:
            rp = str(_f.resolve())
        except Exception:
            rp = str(_f)
        if rp not in seen_paths:
            seen_paths.add(rp)
            uniq_cluster_files.append(_f)
    cluster_files = uniq_cluster_files

    tb_set = set(f for f in cluster_files if is_tb(f))

    rtl_files = [
        f for f in cluster_files
        if not is_tb(f) and is_rtl(f)
    ]

    inc_flag = " ".join(f"-incdir {Path(d).resolve()}" for d in idirs)

    lines = ["clear -all\n\n"]

    '''
    # FIRST: Analyze header files (.vh, .svh) with macro definitions
    header_files = find_header_files(cluster_files)
    for f in header_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')
    

    if header_files:
        lines.append("\n")
    '''

    # SECOND: Analyze package files
    pkg_files = find_pkg_files(cluster_files)
    for f in pkg_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')
    
    if pkg_files:
        lines.append("\n")

    # THIRD: Analyze macro-defining files
    macro_files = [
        f for f in find_macro_files(cluster_files)
        if f not in pkg_files
        ]    
    for f in macro_files:
        lines.append(f'catch {{ analyze -sv {inc_flag} {f.resolve()} }}\n')
    
    if macro_files:
        lines.append("\n")

    # FOURTH: Analyze remaining RTL files
    analyzed_set = set(pkg_files) | set(macro_files)
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
            exit
            }}
        """)
    else:
        lines.append("catch {elaborate}\n")

    lines.append("""
        clock -infer
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
    # create a timestamped log file for each run to avoid reusing/overwriting
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
        # Capture output so it can be inspected and logged
        result = subprocess.run(
            cmd,
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=JASPER_TIMEOUT_SEC,
        )

        out = result.stdout or ""

        # ----------------------------
        # FIXED: single clean write
        # ----------------------------
        try:
            log_path.write_text(out)
        except Exception as e:
            log.warning("Failed writing jasper log: %s", e)

        # optional: debug signal for empty runs
        if result.returncode == 0 and not out.strip():
            log.warning("Jasper produced EMPTY LOG for %s", repo_dir)

        log.info(
            "Jasper exited with code %d; log size=%d",
            result.returncode,
            len(out)
        )

    except subprocess.TimeoutExpired as e:
        out = getattr(e, "stdout", "") or ""

        try:
            log_path.write_text(out + "\n[TIMEOUT]\n")
        except Exception as ex:
            log.warning("Failed writing timeout log: %s", ex)

        log.warning("Jasper timed out after %ds", JASPER_TIMEOUT_SEC)

    except Exception as e:
        tb = traceback.format_exc()

        try:
            log_path.write_text(f"Exception running jg: {e}\n\n{tb}")
        except Exception as ex:
            log.error("Failed writing exception log: %s", ex)

        log.error("Error running Jasper: %s", e)

    return log_path


# RESULT PARSING  — per-property AND repo-level


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
    
    if "could not be elaborated" in txt:
        return False

    return True

def cluster_repo_files(files: List[Path]):

    header_files = [f for f in files if f.suffix in (".vh", ".svh")]
    body_files = [f for f in files if f.suffix not in (".vh", ".svh")]

    # ---------------------------
    # 1. Build module → file map
    # ---------------------------
    module_to_file = {}
    file_to_modules = defaultdict(set)

    for f in body_files:
        txt = _read(f)
        mods = MODULE_RE.findall(txt)

        for m in mods:
            module_to_file[m] = f
            file_to_modules[f].add(m)

    # ---------------------------
    # 2. Build dependency graph
    # ---------------------------
    G = nx.DiGraph()

    for f in body_files:
        insts = find_instantiations([f])
        mods = file_to_modules[f]

        for m in mods:
            G.add_node(m)

        for inst in insts:
            for m in mods:
                G.add_edge(m, inst)

    # ---------------------------
    # 3. Convert to undirected for clustering
    # ---------------------------
    UG = G.to_undirected()

    clusters = defaultdict(list)

    for i, comp in enumerate(nx.connected_components(UG)):
        cluster_id = f"proj_{i}"

        for module in comp:
            if module in module_to_file:
                clusters[cluster_id].append(module_to_file[module])

    # ---------------------------
    # 4. Add orphan / unconnected files
    # ---------------------------
    used = set()
    for lst in clusters.values():
        used.update(lst)

    orphan = [f for f in body_files if f not in used]

    if orphan:
        clusters["misc"] = orphan

    # ---------------------------
    # 5. (optional) add headers globally
    # ---------------------------
    for k in clusters:
        clusters[k].extend(header_files)

    return clusters

def enforce_project_closure(
    cluster_files: List[Path],
    repo_files: Optional[List[Path]] = None
) -> List[Path]:

    """
    Expand cluster by including module-definition files found in repo_files
    (if provided), otherwise only within the cluster.
    """

    module_map = {}

    source_files = (
        repo_files
        if repo_files is not None
        else cluster_files
    )

    for f in source_files:
        txt = _read(f)

        for m in MODULE_RE.findall(txt):
            module_map[m] = f

    expanded = set(cluster_files)

    changed = True

    while changed:
        changed = False

        for f in list(expanded):

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

        '''
        run_dir = BASE_DIR / repo.replace("/", "_")
        run_dir.mkdir(parents=True, exist_ok=True)
        '''
        repo_successful = False

        for cluster_id, cluster_files in clusters.items():
            
            run_dir = (
                BASE_DIR
                / repo.replace("/", "_")
                / cluster_id
            )

            run_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            #cluster_files = expand_cluster(cluster_files)
            # ensure cluster closure across entire repo (include files defining instantiated modules elsewhere)
            before = len(cluster_files)

            cluster_files = enforce_project_closure(
                cluster_files,
                files
            )

            after = len(cluster_files)

            log.info(
                "cluster=%s expanded %d -> %d files",
                cluster_id,
                before,
                after
            )            
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

            tries = 0
            for top in candidate_tops:
                if tries >= MAX_TOP_TRIES:
                    log.info("cluster=%s: reached max top tries (%d), skipping remaining tops", cluster_id, MAX_TOP_TRIES)
                    break
                tries += 1

                log.info("cluster=%s trying top=%s (try %d/%d)", cluster_id, top, tries, MAX_TOP_TRIES)

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
                    repo_successful = True
                    break

        # repo-level DB save
        if repo_successful:
            db_save_repo(conn, repo, None, "PROCESSED")
        else:
            db_save_repo(conn, repo, None, "COMPILE_FAIL")

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