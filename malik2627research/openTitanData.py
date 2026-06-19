import os
import re
import requests
from bs4 import BeautifulSoup as bs
from pathlib import Path
import subprocess
import random
import hjson
import pyslang # specifically for parsing SystemVerilog
import networkx as nx

# global config
OPENTITAN_REPO = "https://github.com/lowRISC/opentitan.git"

#regex
MODULE_RE = re.compile(r"module\s+([a-zA-Z0-9_]+)")
ASSERT_RE = re.compile(
    r"`ASSERT[A-Z_]*\s*\("
)

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
    try:
        tree = pyslang.driver.Driver(str(sv_file))
        compilation = pyslang.Compilation()
        compilation.addSyntaxTree(tree)

        root = compilation.getRoot()

        assertions = []

        # Walk AST
        def visit(node):
            if isinstance(node, pyslang.ast.ConcurrentAssertionStatement):
                assertions.append(str(node))

            if isinstance(node, pyslang.ast.ImmediateAssertionStatement):
                assertions.append(str(node))

            # recursive traversal (generic)
            for child in getattr(node, "children", []):
                visit(child)

        visit(root)

        return assertions

    except Exception:
        return []

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

def extract_modules(sv_file):
    text = sv_file.read_text(errors="ignore")
    return MODULE_RE.findall(text)

# thin AST layer for ports
def extract_ports(sv_path):
    tree = pyslang.driver.Driver(str(sv_path))
    comp = pyslang.Compilation()
    comp.addSyntaxTree(tree)
    ports = []
    for inst in comp.getRoot().topInstances:
        for port in inst.body.portList:
            ports.append({"name": port.name, "direction": str(port.direction)})
    return ports

# must handle cases for multireg/window entries later
def load_ip_intent(ip_dir, ip_name):
    data = hjson.loads((Path(ip_dir) / "data" / f"{ip_name}.hjson").read_text())
    return {
        "ip_name": ip_name,
        "interrupts": [{"name": i["name"], "desc": i.get("desc", "")} for i in data.get("interrupt_list", [])],
        "alerts": [{"name": a["name"], "desc": a.get("desc", "")} for a in data.get("alert_list", [])],
        "registers": [
            {"name": r["name"], "desc": r.get("desc", ""),
             "fields": [{"name": f.get("name"), "desc": f.get("desc", ""), "bits": f.get("bits")} for f in r.get("fields", [])]}
            for r in data.get("registers", []) if isinstance(r, dict) and "name" in r
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

def collect_ip(ip_dir):

    ip_dir = Path(ip_dir)

    """
    structure = {
        "rtl": [],
        "sva": [],
        "packages": [],
        "reg_top": [],
        "reg_pkg": [],
        "dv": [],
        "other": []
    }
    """
    structure = defaultdict(list)

    module_map = {}

    for p in ip_dir.rglob("*.sv"):

        category = classify_sv_file(p)

        structure[category].append(str(p.relative_to(ip_dir)))

        # only parse actual RTL modules
        if category == "rtl":

            modules = extract_modules(p)
            assertions = collect_assertions(p)

            for mod in modules:
                module_map[mod] = {
                    "file": str(p.relative_to(ip_dir)),
                    "assertions": collect_assertions(p)
                }

    return {
        "ip_name": ip_dir.name,
        "structure": structure,
        "modules": module_map
    }

def main():
    opentitan_root = ensure_opentitan()

    ips = discover_ips(opentitan_root)
    dataset = {}

    # filling dataset
    for ip_name in ips:
        ip_dir = get_ip_root(opentitan_root, ip_name)

        if not ip_dir.exists():
            continue
        
        print(f"Processing IP: {ip_name}")
        dataset[ip_name] = collect_ip(ip_dir)
    print(dataset)  

if __name__ == "__main__":
    main()