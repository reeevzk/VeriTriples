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
        # stack of dicts: {"end": offset, "kind": "class"/"function", "name": str}
        self.scope_stack = []
        # track which if-nodes we've already consumed as an else-if link,
        # so the flat visit doesn't double-process them as top-level ifs
        self._consumed_elseif_ids = set()

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

    def _update_scope_stack(self, node):
        start, _ = self._range(node)
        if start is None:
            return
        while self.scope_stack and self.scope_stack[-1]["end"] < start:
            self.scope_stack.pop()

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

    # ---------- macro name / severity ----------

    def _macro_name(self, node):
        try:
            return node.directive.value
        except Exception:
            return self.node_text(node)

    def _severity_from_macro_name(self, name):
        for sev in ("fatal", "error", "warning", "info"):
            if f"uvm_{sev}" in name:
                return sev
        return None

    def _check_kind_from_macro_name(self, name):
        for kind in self.CHECK_MACROS:
            if kind in name:
                return kind
        return None

    def _is_macro_usage(self, node):
        typename = type(node).__name__
        return "Macro" in typename  # tighten to your exact MacroUsageSyntax name if narrower

    def _find_direct_macros(self, branch_node):
        """
        Find macro invocations that belong directly to this branch, NOT ones
        inside a nested IfStatementSyntax (per bug #8 from before). We do this
        by running a bounded sub-visit and rejecting any macro whose offset
        falls inside a nested if found in the same branch.
        """
        if branch_node is None:
            return []

        nested_if_ranges = []
        macros = []

        def collector(n):
            typename = type(n).__name__
            if "ConditionalStatementSyntax" in typename and n is not branch_node:
                s, e = self._range(n)
                if s is not None:
                    nested_if_ranges.append((s, e))
            elif self._is_macro_usage(n):
                s, e = self._range(n)
                macros.append((s, e, n))

        branch_node.visit(f=collector)

        direct = []
        for s, e, n in macros:
            if s is None:
                direct.append(n)
                continue
            inside_nested = any(ns <= s and e <= ne for ns, ne in nested_if_ranges)
            if not inside_nested:
                direct.append(n)
        return direct

    def _direct_macro_severity(self, branch_node):
        """Returns (severity_or_checkkind, action_text, is_check_macro) for the
        first direct macro found in priority order fatal > error > warning > info,
        checked among SEVERITY_MACROS, then falls back to CHECK_MACROS."""
        macros = self._find_direct_macros(branch_node)
        if not macros:
            return None, None

        found = {}  # sev -> action text
        found_check = None
        for m in macros:
            mname = self._macro_name(m)
            sev = self._severity_from_macro_name(mname)
            if sev and sev not in found:
                found[sev] = self.node_text(m)
                continue
            if found_check is None:
                ck = self._check_kind_from_macro_name(mname)
                if ck:
                    found_check = (ck, self.node_text(m))

        for sev in ("fatal", "error", "warning", "info"):
            if sev in found:
                return sev, found[sev]

        if found_check:
            return found_check[0], found_check[1]

        return None, None

    # ---------- if handling ----------

    def handle_if(self, node):
        cond_text = self.node_text(node.condition)

        sev, action = self._direct_macro_severity(node.ifTrue)
        if sev:
            self._add_rule(cond_text, action, sev, branch="then")

        if node.ifFalse is not None:
            false_typename = type(node.ifFalse).__name__
            if "ConditionalStatementSyntax" in false_typename:
                # else-if: mark so the flat visit doesn't treat it as an
                # unrelated top-level if later, and recurse manually with
                # accumulated negation so downstream SVA has full chain context
                self._consumed_elseif_ids.add(id(node.ifFalse))
                self._handle_elseif_chain(node.ifFalse, [f"!({cond_text})"])
            else:
                sev, action = self._direct_macro_severity(node.ifFalse)
                if sev:
                    self._add_rule(f"!({cond_text})", action, sev, branch="else")

    def _handle_elseif_chain(self, node, negated_prior):
        # node is itself an IfStatementSyntax reached via an else branch
        cond_text = self.node_text(node.condition)
        full_trigger = " && ".join(negated_prior + [cond_text])

        sev, action = self._direct_macro_severity(node.ifTrue)
        if sev:
            self._add_rule(full_trigger, action, sev, branch="elseif")

        if node.ifFalse is not None:
            false_typename = type(node.ifFalse).__name__
            if "ConditionalStatementSyntax" in false_typename:
                self._consumed_elseif_ids.add(id(node.ifFalse))
                self._handle_elseif_chain(
                    node.ifFalse, negated_prior + [f"!({cond_text})"]
                )
            else:
                sev, action = self._direct_macro_severity(node.ifFalse)
                if sev:
                    neg_trigger = " && ".join(
                        negated_prior + [f"!({cond_text})"]
                    )
                    self._add_rule(neg_trigger, action, sev, branch="else")

    # ---------- bare macro handling ----------

    def handle_bare_macro(self, node):
        mname = self._macro_name(node)
        sev = self._severity_from_macro_name(mname)
        if sev:
            self._add_rule(None, self.node_text(node), sev, branch="unconditional")
            return
        ck = self._check_kind_from_macro_name(mname)
        if ck:
            self._add_rule(None, self.node_text(node), ck, branch="unconditional")

    # ---------- rule sink ----------

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

    # ---------- entry point ----------

    def extract(self, root_node):
        def callback(n):
            self._update_scope_stack(n)
            typename = type(n).__name__
            self._push_scope_if_applicable(n, typename)

            if "ConditionalStatementSyntax" in typename:
                if id(n) in self._consumed_elseif_ids:
                    return  # already handled as part of an else-if chain
                self.handle_if(n)
            elif self._is_macro_usage(n):
                # skip macros that are direct children of an if-branch we
                # already processed via handle_if / _handle_elseif_chain —
                # otherwise they'd double-count as "bare" macros too.
                if not self._inside_any_if(n):
                    self.handle_bare_macro(n)

            if "ConditionalStatementSyntax" in type(n).__name__:
                print("\n=== ConditionalStatementSyntax attrs ===")
                for attr in dir(n):
                    if attr.startswith("_"):
                        continue
                    try:
                        val = getattr(n, attr)
                    except Exception:
                        continue
                    if callable(val):
                        continue
                    print(f"{attr}: {type(val).__name__}")
        root_node.visit(f=callback)
        return self.rules

    def _inside_any_if(self, macro_node):
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


def debug_macro_text(node):

    count = 0

    def callback(n):
        nonlocal count

        typename = type(n).__name__

        # Only inspect the statement types we're interested in
        if typename not in (
            "ExpressionStatementSyntax",
            "VoidCastedCallStatementSyntax",
        ):
            return

        try:
            text = n.toString()
        except Exception:
            return

        # Only print statements containing the macros we're hunting
        if any(x in text for x in (
            "uvm_error",
            "uvm_fatal",
            "DV_CHECK",
            "DV_ASSERT",
        )):
            print("\n====================")
            print("NODE:", typename)
            print("TEXT:")
            print(text)

            count += 1
            if count >= 200:
                return

    node.visit(f=callback)

"""
def debug_tokens(path):

    tree = SyntaxTree.fromFile(str(path))

    for token in tree.tokens:
        text = str(token)

        if "uvm" in text:
            print("FOUND TOKEN:", text)

"""
# one sb at a time

def parse_scoreboard(path):

    tree = SyntaxTree.fromFile(str(path))
    root = tree.root
    debug_macro_text(root)
    source_text = Path(path).read_text()
    extractor = RuleExtractor(source_text)
    return extractor.extract(root)

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