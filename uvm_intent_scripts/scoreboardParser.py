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

class RuleExtractor:

    SEVERITY_MACROS = ("uvm_fatal", "uvm_error", "uvm_warning", "uvm_info")
    CHECK_MACROS = ("DV_CHECK", "DV_CHECK_EQ", "DV_CHECK_NE", "DV_CHECK_FATAL")

    def __init__(self, source_text):
        self.source_text = source_text
        self.rules = []
        self.function_stack = []   # (kind, name) e.g. ("task", "predict")
        self.class_stack = []      # class names

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

    def visit(self, node):
        if node is None:
            return

        typename = type(node).__name__

        if typename == "ClassDeclarationSyntax":
            self.class_stack.append(node.name.value)

        if typename == "SubroutineDeclarationSyntax":
            self.function_stack.append(node.prototype.name.value)

        if typename == "IfStatementSyntax":
            self.handle_if(node)
        elif typename == "MacroUsageSyntax":
            self.handle_bare_macro(node)

        for child in node.children:
            if child is not None:
                self.visit(child)

        if typename == "SubroutineDeclarationSyntax":
            self.function_stack.pop()

        if typename == "ClassDeclarationSyntax":
            self.class_stack.pop()

    def _macro_name(self, node):
        # adjust attribute name to match your slang binding
        try:
            return node.directive.value
        except Exception:
            return self.node_text(node)

    def _severity_from_macro_name(self, name):
        for sev in ("fatal", "error", "warning", "info"):
            if f"uvm_{sev}" in name:
                return sev
        return None

    def _direct_macro_severity(self, stmt_node):
        """Only look at macro calls that are direct children of this
        branch's statement list, not ones buried in a nested if — those
        get their own rule when the recursive visit reaches them."""
        if stmt_node is None:
            return None, None
        severity = None
        action_text = None
        for child in getattr(stmt_node, "children", []) or []:
            if child is None:
                continue
            cname = type(child).__name__
            if cname == "IfStatementSyntax":
                # nested if handles itself independently — skip
                continue
            if cname == "MacroUsageSyntax":
                mname = self._macro_name(child)
                sev = self._severity_from_macro_name(mname)
                if sev:
                    severity = sev
                    action_text = self.node_text(child)
            # descend one level into blocks (StatementBlockSyntax etc.)
            # without crossing into another IfStatementSyntax
            elif cname != "IfStatementSyntax":
                sub_sev, sub_action = self._direct_macro_severity(child)
                if sub_sev:
                    severity, action_text = sub_sev, sub_action
        return severity, action_text

    def _current_function(self):
        return self.function_stack[-1] if self.function_stack else None

    def _current_class(self):
        return self.class_stack[-1] if self.class_stack else None

    def handle_if(self, node):
        cond_text = self.node_text(node.condition)

        # --- true branch ---
        sev, action = self._direct_macro_severity(node.ifTrue)
        if sev:
            self._add_rule(cond_text, action, sev, branch="then")

        # --- false branch ---
        if node.ifFalse is not None:
            false_typename = type(node.ifFalse).__name__
            if false_typename == "IfStatementSyntax":
                # else-if chain: let recursion pick it up naturally,
                # but we don't have to do anything special here since
                # visit() will reach node.ifFalse via children anyway.
                pass
            else:
                sev, action = self._direct_macro_severity(node.ifFalse)
                if sev:
                    # the check "fails" here, so the meaningful trigger
                    # for an SVA is the negation of cond
                    self._add_rule(
                        f"!({cond_text})", action, sev, branch="else"
                    )

    def handle_bare_macro(self, node):
        """uvm_error/etc. called with no surrounding if — e.g. unconditional
        'should never get here' paths."""
        mname = self._macro_name(node)
        sev = self._severity_from_macro_name(mname)
        if sev:
            self._add_rule(
                cond=None,
                action=self.node_text(node),
                severity=sev,
                branch="unconditional",
            )

    def _add_rule(self, cond, action, severity, branch):
        self.rules.append(
            {
                "class": self._current_class(),
                "function": self._current_function(),
                "trigger": cond,
                "action": action,
                "severity": severity,
                "branch": branch,
            }
        )


# HELPER FUNCTION --GETS ALL AST MACROS AND KEYWORDS
def debug_ast(node, depth=0, max_depth=6):
    """
    Recursively print useful information about a pyslang AST.

    depth: current recursion depth
    max_depth: stop after this many levels to avoid enormous output
    """

    if node is None or depth > max_depth:
        return

    indent = "  " * depth
    typename = type(node).__name__

    print(f"\n{indent}{'='*60}")
    print(f"{indent}NODE TYPE: {typename}")

    # Try printing reconstructed source
    try:
        print(f"{indent}toString():")
        print(f"{indent}{node.toString()}")
    except Exception:
        pass

    # Print sourceRange
    try:
        print(f"{indent}sourceRange:")
        print(f"{indent}{repr(node.sourceRange)}")
    except Exception:
        pass

    # Print all public attributes
    print(f"{indent}Attributes:")

    for attr in sorted(dir(node)):

        if attr.startswith("_"):
            continue

        if attr == "children":
            continue

        try:
            value = getattr(node, attr)

            # don't print giant recursive objects
            if callable(value):
                continue

            if isinstance(value, (str, int, float, bool, type(None))):
                print(f"{indent}  {attr}: {value}")

            else:
                print(f"{indent}  {attr}: <{type(value).__name__}>")

        except Exception:
            pass

    # Show child node types
    try:
        children = list(node.children)
        print(f"{indent}Children ({len(children)}):")

        for child in children:
            if child is None:
                continue
            print(f"{indent}  -> {type(child).__name__}")

        for child in children:
            if child is not None:
                debug_ast(child, depth + 1, max_depth)

    except Exception:
        pass

# another helper
def find_interesting(node):

    interesting = {
        "IfStatementSyntax",
        "SubroutineDeclarationSyntax",
        "MacroUsageSyntax"
    }

    def callback(n):

        name = type(n).__name__

        if name in interesting or "Macro" in name:
            print("\nFOUND:", name)
            print("KIND:", n.kind)

            for attr in dir(n):
                if attr.startswith("_"):
                    continue

                try:
                    value = getattr(n, attr)

                    if callable(value):
                        continue

                    print(f"  {attr}: {type(value).__name__}")

                except Exception:
                    pass

    node.visit(f=callback)



# one sb at a time

def parse_scoreboard(path):

    tree = SyntaxTree.fromFile(str(path))
    root = tree.root

    print("ROOT:", type(root).__name__)

    def callback(node):

        typename = type(node).__name__

        if typename == "Token":
            return

        if typename == "ClassDeclarationSyntax":

            print("\nFOUND CLASS")

            print("Number of items:", len(node.items))

            for i, item in enumerate(node.items):

                print(
                    f"ITEM {i}:",
                    type(item).__name__
                )

                if type(item).__name__ == "SubroutineDeclarationSyntax":

                    print("  ATTRIBUTES:")

                    for attr in dir(item):
                        if attr.startswith("_"):
                            continue

                        try:
                            value = getattr(item, attr)

                            if callable(value):
                                continue

                            print(
                                "   ",
                                attr,
                                type(value).__name__
                            )

                        except Exception:
                            pass

    root.visit(f=callback)

    print("DONE VISITING")

    return []

count = 0

def dump(node):

    global count

    if count >= 20:
        return pyslang.VisitAction.Interrupt

    count += 1

    print("NODE:", type(node).__name__)

    try:
        print("KIND:", node.kind)
    except Exception:
        pass

    for attr in dir(node):
        if attr.startswith("_"):
            continue

        try:
            value = getattr(node, attr)

            if callable(value):
                continue

            print(f"{attr}: {type(value).__name__}")

        except Exception:
            pass

    return None

# main

if __name__ == "__main__":

    ROOT = "/home/rk6650/VeriTriples/data/opentitan/hw/ip"

    for sb in find_scoreboards(ROOT):

        parse_scoreboard(sb)
        break