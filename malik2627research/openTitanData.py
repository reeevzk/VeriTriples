import os
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import subprocess
import random

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
        return "package"
    if name.endswith("_tb.sv") or "/dv/" in str(path):
        return "dv"
    if "/rtl/" in str(path):
        return "rtl"
    return "other"

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

def get_ip_root(opentitan_root, ip_name):
    return Path(opentitan_root) / "hw" / "ip" / ip_name

def build_ip_dataset(ip_name, opentitan_root):

    ip_dir = get_ip_root(opentitan_root, ip_name)

    rtl_data = collect_ip_correct(ip_dir)
    docs_text = fetch_datasheet(ip_name)

    if docs_text:
        intent = extract_design_intent(docs_text)
    else:
        intent = {}

    return {
        "ip_name": ip_name,

        # implementation layer
        "rtl_structure": rtl_data,

        # design intent layer (NEW IMPORTANT PART)
        "design_intent": intent
    }

def fetch_datasheet(ip_name, top="top_earlgrey"):
    url = f"https://opentitan.org/book/hw/{top}/ip/{ip_name}/data/{ip_name}.html"

    r = requests.get(url)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text("\n")
    return text

def collect_ip_correct(ip_dir):

    ip_dir = Path(ip_dir)

    structure = {
        "rtl": [],
        "packages": [],
        "reg": [],
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

    def compress(paths):
        paths = [str(p.relative_to(ip_dir)) for p in paths]

        # deterministic + small footprint
        paths = sorted(paths)

        if len(paths) <= max_files_per_category:
            return paths

        # smart sampling: keep first + random spread
        keep = set()
        keep.add(paths[0])  # often top module / entry point
        keep.add(paths[-1]) # sometimes wrapper / top-level

        while len(keep) < max_files_per_category:
            keep.add(random.choice(paths))

        return sorted(list(keep))

    def root_prefix(paths):
        if not paths:
            return None
        common = Path(paths[0]).parts[:-1]
        return "/".join(common)

    rtl_rel = [p for p in rtl]
    sva_rel = [p for p in sva]
    docs_rel = [p for p in docs]

    return {
        "ip_name": ip_dir.name,

        # compressed file views
        "rtl_files": compress(rtl_rel),
        "sva_files": compress(sva_rel),
        "doc_files": compress(docs_rel),

        # metadata (cheap + useful) how
        "rtl_count": len(rtl),
        "sva_count": len(sva),
        "doc_count": len(docs),

        "rtl_root_prefix": root_prefix(rtl),
        "sva_root_prefix": root_prefix(sva),
        "doc_root_prefix": root_prefix(docs),
    }


def main():
    opentitan_root = ensure_opentitan()

    usbdev_dir = get_ip_root(opentitan_root, "usbdev")

    dataset = collect_ip(usbdev_dir)
    print(dataset)  

