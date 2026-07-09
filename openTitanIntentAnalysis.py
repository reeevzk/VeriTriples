import json
from pathlib import Path
import re

def load_intent_files(intent_dir):

    docs = []

    for p in Path(intent_dir).glob("*.intent.json"):

        docs.append(
            json.loads(p.read_text())
        )

    return docs

KEYWORDS = {
    "interrupt": "interrupt",
    "alert": "alert",
    "register": "register",
    "timer": "timer",
    "fifo": "fifo",
    "clock": "clock"
}

def classify_requirement(text):

    text = text.lower()

    tags = []

    for k, v in KEYWORDS.items():

        if k in text:
            tags.append(v)

    return tags

def load_module_dataset(dataset_path):
    with open(dataset_path) as f:
        return json.load(f)


def extract_interrupt_requirements(ip_intent):

    reqs = []

    for intr in ip_intent.get(
        "interrupts",
        []
    ):

        reqs.append({

            "req_id":
                f"interrupt:{intr['name']}",

            "origin":
                "interrupt",

            "name":
                intr["name"],

            "text":
                intr["desc"]
        })

    return reqs

def get_module_assertions(module):

    return module.get(
        "assertions",
        []
    )

def analyze_module_assertions(module):

    results = []

    for assertion in module.get(
        "assertions",
        []
    ):

        results.append({

            "assertion":
                assertion,

            "features":
                extract_assertion_features(
                    assertion
                )
        })

    return results

def extract_requirements(ip_intent):

    reqs = []

    for intr in ip_intent.get("interrupts", []):

        reqs.append({
            "origin": "interrupt",
            "name": intr["name"],
            "text": intr["desc"],
            "tags": classify_requirement(
                intr["desc"]
            )
        })

    for alert in ip_intent.get("alerts", []):

        reqs.append({
            "origin": "alert",
            "name": alert["name"],
            "text": alert["desc"],
            "tags": classify_requirement(
                alert["desc"]
            )
        })

    for reg in ip_intent.get("registers", []):

        reqs.append({
            "origin": "register",
            "name": reg["name"],
            "text": reg["desc"],
            "tags": classify_requirement(
                reg["desc"]
            )
        })

    return reqs

def extract_interrupt_requirements(ip_intent):

    reqs = []

    for intr in ip_intent.get(
        "interrupts",
        []
    ):

        reqs.append({

            "req_id":
                f"interrupt:{intr['name']}",

            "origin":
                "interrupt",

            "name":
                intr["name"],

            "text":
                intr["desc"]
        })

    return reqs

def extract_alert_requirements(ip_intent):

    reqs = []

    for alert in ip_intent.get(
        "alerts",
        []
    ):

        reqs.append({

            "req_id":
                f"alert:{alert['name']}",

            "origin":
                "alert",

            "name":
                alert["name"],

            "text":
                alert["desc"]
        })

    return reqs

def extract_register_requirements(ip_intent):

    reqs = []

    for reg in ip_intent.get(
        "registers",
        []
    ):

        reqs.append({

            "req_id":
                f"register:{reg['name']}",

            "origin":
                "register",

            "name":
                reg["name"],

            "text":
                reg["desc"]
        })

    return reqs

def extract_all_requirements(ip_intent):

    reqs = []

    reqs.extend(
        extract_interrupt_requirements(
            ip_intent
        )
    )

    reqs.extend(
        extract_alert_requirements(
            ip_intent
        )
    )

    reqs.extend(
        extract_register_requirements(
            ip_intent
        )
    )

    return reqs

def classify_property_class(assertion):

    text = str(assertion)

    if "|->" in text or "|=>" in text:
        return "sequential"

    return "combinational"

def estimate_temporal_depth(assertion):

    text = str(assertion)

    return text.count("##")

def detect_cross_clock(assertion):

    text = str(assertion)

    return (
        text.count("clk_") > 1
    )

def extract_assertion_features(assertion):

    return {

        "property_class":
            classify_property_class(
                assertion
            ),

        "temporal_depth":
            estimate_temporal_depth(
                assertion
            ),

        "cross_clock":
            detect_cross_clock(
                assertion
            )
    }

def classify_requirement_type(req):

    text = req["text"].lower()

    if "interrupt" in text:
        return "interrupt_behavior"

    if "alert" in text:
        return "fault_detection"

    if "counter" in text:
        return "counter_behavior"

    if "timer" in text:
        return "timing_behavior"

    return "other"

def classify_requirement_scope(req):

    text = req["text"].lower()

    if "clock" in text:
        return "clock_domain"

    if "register" in text:
        return "register_behavior"

    return "module_behavior"

def score_assertion_requirement(
    requirement,
    assertion
):

    req_words = set(
        requirement["text"]
        .lower()
        .split()
    )

    assertion_text = str(
        assertion
    ).lower()

    score = 0

    for word in req_words:

        if word in assertion_text:
            score += 1

    return score

def link_requirements_to_assertions(
    requirements,
    assertions
):

    links = []

    for req in requirements:

        best_score = 0
        best_assertion = None

        for assertion in assertions:

            score = score_assertion_requirement(
                req,
                assertion
            )

            if score > best_score:

                best_score = score
                best_assertion = assertion

        if best_assertion:

            links.append({

                "req_id":
                    req["req_id"],

                "assertion":
                    best_assertion,

                "score":
                    best_score
            })

    return links

def compute_requirement_coverage(
    requirements,
    links
):

    covered = {

        l["req_id"]
        for l in links

    }

    return {

        "total":
            len(requirements),

        "covered":
            len(covered),

        "coverage":
            len(covered)
            / len(requirements)
            if requirements
            else 0
    }

def main():

    modules = load_module_dataset(
        "opentitan_dataset.json"
    )

    for module in modules:

        module_name = module[
            "module_name"
        ]

        requirements = (
            extract_all_requirements(
                module["ip_intent"]
            )
        )

        assertion_data = (
            analyze_module_assertions(
                module
            )
        )

        links = (
            link_requirements_to_assertions(
                requirements,
                assertion_data
            )
        )

        coverage = (
            compute_requirement_coverage(
                requirements,
                links
            )
        )

        print(
            module_name,
            coverage
        )

if __name__ == "__main__":
    main()