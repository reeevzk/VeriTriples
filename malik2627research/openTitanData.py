import os
import re
import requests
from bs4 import BeautifulSoup as bs
from pathlib import Path
import subprocess
import random
import hjson
import pyslang
import networkx as nx

# global config
OPENTITAN_REPO = "https://github.com/lowRISC/opentitan.git"

def ensure_opentitan(repo_dir="data/opentitan"):
    repo_dir = Path(repo_dir)

    if not repo_dir.exists():
        print("Cloning OpenTitan...")
        subprocess.run(
            ["git", "clone", "--depth", "1", OPENTITAN_REPO, str(repo_dir)],
            check=True
        )

    return repo_dir

def classify_sv_file(path: Path):
    name = path.name.lower()

    if "reg_top" in name:
        return "reg_top"
    if "reg_pkg" in name:
        return "reg_pkg"
    if "pkg" in name:
        return "packages"
    if name.endswith("_tb.sv") or "/dv/" in str(path):
        return "dv"
    if "/rtl/" in str(path):
        return "rtl"
    return "other"

"""
def extract_design_intent(text):

    intent = {
        "ports": [],
        "interrupts": [],
        "alerts": [],
        "registers": []
    }

    lines = text.split("\n")

    mode = None

    for line in lines:
        l = line.lower()

        if "interrupt" in l:
            mode = "interrupts"
        elif "alert" in l:
            mode = "alerts"
        elif "register" in l:
            mode = "registers"
        elif "port" in l:
            mode = "ports"

        if mode and "|" in line:
            intent[mode].append(line.strip())

    return intent
"""

def get_ip_root(opentitan_root, ip_name):
    return Path(opentitan_root) / "hw" / "ip" / ip_name

# thin AST layer for ports
def extract_ports(sv_path):
    tree = pyslang.SyntaxTree.fromFile(str(sv_path))
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
    ip_dir = get_ip_root(opentitan_root, ip_name)
    rtl_data = collect_ip(ip_dir)
    intent = load_ip_intent(ip_dir, ip_name)
    return {"ip_name": ip_name, "rtl_structure": rtl_data, "design_intent": intent}

"""
def fetch_datasheet(ip_name, top="top_earlgrey"):
    url = f"https://opentitan.org/book/hw/{top}/ip/{ip_name}/data/{ip_name}.html"

    r = requests.get(url)
    if r.status_code != 200:
        return None

    soup = bs(r.text, "html.parser")

    text = soup.get_text("\n")
    return text
"""

def collect_ip(ip_dir):

    ip_dir = Path(ip_dir)

    structure = {
        "rtl": [],
        "packages": [],
        "reg_top": [],
        "reg_pkg": [],
        "dv": [],
        "other": []
    }

    for p in ip_dir.rglob("*.sv"):

        category = classify_sv_file(p)

        structure[category].append(str(p.relative_to(ip_dir)))

    return {
        "ip_name": ip_dir.name,
        "structure": structure
    }

def main():
    opentitan_root = ensure_opentitan()

    usbdev_dir = get_ip_root(opentitan_root, "usbdev")

    dataset = collect_ip(usbdev_dir)
    print(dataset)  

if __name__ == "__main__":
    main()