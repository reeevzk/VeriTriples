from pathlib import Path
import json

from pyslang import SyntaxTree

# finding any scoreboard files in the OpenTitan repo

def find_scoreboards(root):
    root = Path(root)

    for path in root.rglob("*_scoreboard.sv"): # standard naming conv.

        # only analyze IP-local scoreboards
        if "hw/ip" not in str(path).replace("\\", "/"):
            continue

        yield path


def node_text(node):
    try:
        return str(node.sourceRange)
    except Exception:
        try:
            return node.toString()
        except Exception:
            return ""


# classic AST visitor pattern to extract rules from scoreboard

class RuleExtractor:

    def __init__(self):

        self.rules = []

        self.function_stack = []


    def visit(self, node):

        if node is None:
            return

        typename = type(node).__name__

        if typename == "SubroutineDeclarationSyntax":
            self.function_stack.append(node.prototype.name.value)

        if typename == "IfStatementSyntax":
            self.handle_if(node)

        for child in node.children:
            if child is not None:
                self.visit(child)

        if typename == "SubroutineDeclarationSyntax":
            self.function_stack.pop()


    def handle_if(self, node):

        cond = node_text(node.condition)

        then_text = node_text(node.ifTrue)

        severity = None

        if "uvm_fatal" in then_text:
            severity = "fatal"

        elif "uvm_error" in then_text:
            severity = "error"

        elif "uvm_warning" in then_text:
            severity = "warning"

        elif "uvm_info" in then_text:
            severity = "info"

        if severity is None:
            return

        self.rules.append(
            {
                "function":
                    self.function_stack[-1]
                    if self.function_stack
                    else None,

                "trigger":
                    cond,

                "action":
                    then_text,

                "severity":
                    severity,
            }
        )


# one sb at a time

def parse_scoreboard(path):

    tree = SyntaxTree.fromFile(str(path))

    extractor = RuleExtractor()

    extractor.visit(tree.root)

    return extractor.rules

# main

if __name__ == "__main__":

    ROOT = "/path/to/opentitan"

    results = {}

    for sb in find_scoreboards(ROOT):

        print(sb)

        results[str(sb)] = parse_scoreboard(sb)

    with open("scoreboard_rules.json", "w") as f:
        json.dump(results, f, indent=2)