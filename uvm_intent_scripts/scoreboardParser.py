from pathlib import Path
import json
import pyslang
from pyslang.syntax import SyntaxTree

# finding any scoreboard files in the OpenTitan repo

def find_scoreboards(root):
    root = Path(root)

    for path in root.rglob("*_scoreboard.sv"): # standard naming conv.

        # only analyze IP-local scoreboards
        if "hw/ip" not in str(path).replace("\\", "/"):
            continue

        yield path


def node_text(node, source_text):
    try:
        rng = node.sourceRange
        return source_text[rng.start.offset:rng.end.offset]
    except Exception:
        try:
            return node.toString()
        except Exception:
            return ""


# classic AST visitor pattern to extract rules from scoreboard

from pathlib import Path
import json
import pyslang
from pyslang.syntax import SyntaxTree

# finding any scoreboard files in the OpenTitan repo

def find_scoreboards(root):
    root = Path(root)

    for path in root.rglob("*_scoreboard.sv"): # standard naming conv.

        # only analyze IP-local scoreboards
        if "hw/ip" not in str(path).replace("\\", "/"):
            continue

        yield path


def node_text(node, source_text):
    try:
        rng = node.sourceRange
        return source_text[rng.start.offset:rng.end.offset]
    except Exception:
        try:
            return node.toString()
        except Exception:
            return ""


# classic AST visitor pattern to extract rules from scoreboard

class GraphExtractor:
    SEVERITY_MACROS = ("uvm_fatal", "uvm_error", "uvm_warning", "uvm_info")
    CHECK_MACROS = ("DV_CHECK", "DV_CHECK_EQ", "DV_CHECK_NE", "DV_CHECK_FATAL")

    def __init__(self, source_text):
        self.source_text = source_text
        self.graph = {
            "nodes": [],
            "edges": [],
        }
        # stack of dicts: {"end": offset, "kind": "class"/"function", "name": str}
        self.scope_stack = []
        # track which if-nodes we've already consumed as an else-if link,
        # so the flat visit doesn't double-process them as top-level ifs
        self._seen_if_ranges = []
        self.condition_stack = []
    # ---------- text / range helpers ----------

    def node_text(self, node):
        if node is None:
            return ""
        try:
            rng = node.sourceRange
            return self.source_text[rng.start.offset:rng.end.offset]
        except Exception:
            try:
                return node.toString()
            except Exception:
                return ""

    def _range(self, node):
        try:
            rng = node.sourceRange
            return rng.start.offset, rng.end.offset
        except Exception:
            return None, None

    # ---------- scope tracking (flat-visit workaround) ----------

    def _update_scope_stack(self, offset):
        while self.scope_stack and self.scope_stack[-1]["end"] < offset:
            self.scope_stack.pop()

    def _update_parent_stack(self, offset):
        while self.parent_stack and self.parent_stack[-1]["end"] < offset:
            self.parent_stack.pop()
    
    def _push_scope_if_applicable(self, node, typename):
        if "ClassDeclarationSyntax" in typename:
            _, end = self._range(node)
            name = self._safe_name(node)
            if end is not None:
                self.scope_stack.append({"end": end, "kind": "class", "name": name})
        elif "SubroutineDeclarationSyntax" in typename:
            # covers both function and task in slang's grammar
            _, end = self._range(node)
            name = self._safe_name(node)
            if end is not None:
                self.scope_stack.append({"end": end, "kind": "function", "name": name})

    def _safe_name(self, node):
        # adjust to match your pyslang binding; class/subroutine headers usually
        # expose a `.name` token with a `.value` or `.valueText`
        for path in ("name.valueText", "name.value"):
            obj = node
            try:
                for attr in path.split("."):
                    obj = getattr(obj, attr)
                if obj:
                    return str(obj)
            except Exception:
                continue
        return None

    def _current_class(self):
        for entry in reversed(self.scope_stack):
            if entry["kind"] == "class":
                return entry["name"]
        return None

    def _current_function(self):
        for entry in reversed(self.scope_stack):
            if entry["kind"] == "function":
                return entry["name"]
        return None

    
    def add_node(self, node_type, text, node):

        start,end = self._range(node)

        node_id = len(self.graph["nodes"])

        self.graph["nodes"].append({
            "id": node_id,
            "type": node_type,
            "text": text,
            "class": self._current_class(),
            "function": self._current_function(),
            "start": start,
            "end": end
        })

        return node_id
    
    def add_edge(self, src, dst, edge_type, branch=None):

        self.graph["edges"].append({
            "src": src,
            "dst": dst,
            "type": edge_type,
            "branch": branch
        })
    
    def is_action(self, node):
        typename = type(node).__name__

        if typename not in (
            "ExpressionStatementSyntax",
            "InvocationExpressionSyntax",
            "VoidCastedCallStatementSyntax",
        ):
            return False

        text = self.node_text(node)

        return (
            "`uvm_" in text or
            "DV_CHECK" in text or
            ".sample(" in text or
            ".predict(" in text or
            ".compare(" in text
        )

    """
    def walk(self, node, parent=None):

        if node is None:
            return

        self._update_scope_stack(node)
        self._push_scope_if_applicable(node, type(node).__name__)

        typename = type(node).__name__

        #
        # Function
        #
        if typename == "FunctionDeclarationSyntax":

            fn = self.add_node(
                "function",
                self._current_function() or "anonymous",
                node
            )

            for item in node.items:
                self.walk(item, fn)

            return

        #
        # Block
        #
        if typename == "BlockStatementSyntax":

            for item in node.items:
                self.walk(item, parent)

            return

        #
        # IF
        #
        if typename == "ConditionalStatementSyntax":

            cond = self.add_node(
                "condition",
                self.node_text(node.predicate),
                node
            )

            if parent is not None:
                self.add_edge(parent, cond, "contains")

            #
            # TRUE branch
            #

            self.walk(node.statement, cond)

            #
            # FALSE branch
            #

            if node.elseClause is not None:
                self.walk(node.elseClause, cond)

            return

        #
        # CASE
        #
        if typename == "CaseStatementSyntax":

            case = self.add_node(
                "case",
                self.node_text(node.expr),
                node
            )

            if parent is not None:
                self.add_edge(parent, case, "contains")

            for item in node.items:
                self.walk(item, case)

            return

        #
        # DEFAULT
        #
        if typename == "DefaultCaseItemSyntax":

            default = self.add_node(
                "default",
                "default",
                node
            )

            if parent is not None:
                self.add_edge(parent, default, "contains")

            self.walk(node.clause, default)

            return

        #
        # Verification action
        #

        if self.is_action(node):

            action = self.add_node(
                "action",
                self.node_text(node),
                node
            )

            if parent is not None:
                self.add_edge(parent, action, "contains")

        #
        # Generic recursion
        #

        node.visit(lambda child: self.walk(child, parent))
    """

    def inside_any_if(self, macro_node):
        # crude but effective: since we don't have parent pointers, re-derive
        # "is this macro inside some if-statement" by checking offset containment
        # against all if-statements seen so far. Cheap enough at this scale;
        # swap for a real parent-tracking pass if file sizes get large.
        s, e = self._range(macro_node)
        if s is None:
            return False
        for entry in getattr(self, "_seen_if_ranges", []):
            ns, ne = entry
            if ns <= s and e <= ne:
                return True
        return False
    
    def extract(self, root):

        def callback(node):

            if not hasattr(node, "sourceRange"):
                return
            typename = type(node).__name__

            offset = node.sourceRange.start.offset
            self._update_parent_stack(offset)

            #
            # ENTER IF
            #
            if typename == "ConditionalStatementSyntax":

                cond = self.add_node(
                    "condition",
                    self.node_text(node.predicate),
                    node
                )

                if self.condition_stack:
                    parent = self.condition_stack[-1]
                    self.add_edge(
                        parent["id"],
                        cond_id,
                        "contains",
                        parent["branch"]
                    )

                self.condition_stack.append({
                    "id": cond_id,
                    "end": node.sourceRange.end.offset,
                    "branch": "then"
                })

            #
            # ENTER ELSE
            #
            elif typename == "ElseClauseSyntax":

                print("ENTER ELSE")
                print(self.node_text(node))

                if self.parent_stack:
                    self.parent_stack[-1]["branch"] = "else"

                print("STACK UPDATE:", self.parent_stack)
                print()

            #
            # ACTION
            #
            elif self.is_action(node):

                action = self.add_node(
                    "action",
                    self.node_text(node),
                    node
                )

                if self.condition_stack:
                    parent = self.condition_stack[-1]["id"]
                    self.add_edge(
                        parent,
                        action_id,
                        "contains",
                        self.condition_stack[-1]["branch"]
                    )


        root.visit(f=callback)

        return self.graph

"""
def debug_macro_text(root, source_text):

    def callback(n):
        try:
            rng = n.sourceRange
            text = source_text[rng.start.offset:rng.end.offset]
        except Exception:
            return

        if (
            "`uvm_" in text or
            "DV_CHECK" in text or
            "DV_ASSERT" in text
        ):
            print("\n====================")
            print(type(n).__name__)
            print(text)

    root.visit(f=callback)
"""
# one sb at a time

def parse_scoreboard(path):

    tree = SyntaxTree.fromFile(str(path))
    root = tree.root
    source_text = Path(path).read_text()
     # debug_macro_text(root, source_text)
    extractor = GraphExtractor(source_text)

    graph = extractor.extract(root)

    print("\n========== GRAPH ==========")

    for node in graph["nodes"]:
        print(
            node["id"],
            node["type"],
            node["text"][:80].replace("\n", " ")
        )

    print("\n---------- EDGES ----------")

    for edge in graph["edges"]:
        print(edge)

    return graph

# main

if __name__ == "__main__":

    ROOT = "/home/rk6650/VeriTriples/data/opentitan/hw/ip"

    results = {}

    for sb in find_scoreboards(ROOT):
        print(sb)
        results[str(sb)] = parse_scoreboard(sb)
        break

    with open("scoreboard_rules.json", "w") as f:
        json.dump(results, f, indent=2)