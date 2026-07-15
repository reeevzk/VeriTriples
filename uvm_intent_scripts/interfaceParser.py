from pathlib import Path
from dataclasses import dataclass, field
import json
import pyslang
from pyslang.syntax import SyntaxTree


@dataclass
class InterfaceSignal:
    interface_name: str
    signal_name: str
    direction: str = "logic"
    width: str = ""
    data_type: str = ""
    source_file: str = ""

    # later used by linker / KG construction
    clock: str = None
    reset: str = None

    provenance: str = ""


@dataclass
class InterfaceModport:
    interface_name: str
    modport_name: str
    ports: list = field(default_factory=list)

    source_file: str = ""
    provenance: str = ""


@dataclass
class ClockingBlock:
    interface_name: str
    clocking_name: str
    clock_signal: str
    edge: str = "posedge"

    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)

    source_file: str = ""
    provenance: str = ""


@dataclass
class InterfaceIntent:
    interface_name: str

    signals: list = field(default_factory=list)
    modports: list = field(default_factory=list)
    clocking_blocks: list = field(default_factory=list)

    source_file: str = ""



def node_text(node, source_text):

    if node is None:
        return ""

    try:
        rng = node.sourceRange
        return source_text[
            rng.start.offset:rng.end.offset
        ]

    except Exception:

        try:
            return node.toString()

        except Exception:
            return ""



def node_range(node):

    try:
        rng = node.sourceRange
        return (
            rng.start.offset,
            rng.end.offset
        )

    except Exception:
        return None, None



class InterfaceExtractor:


    def __init__(self, source_text, source_file):

        self.source_text = source_text
        self.source_file = source_file


        self.interface_name = None

        self.signals = []
        self.modports = []
        self.clocking_blocks = []


        self.scope_stack = []


    def update_scope(self, node):

        start, _ = node_range(node)

        if start is None:
            return


        while (
            self.scope_stack
            and self.scope_stack[-1]["end"] < start
        ):
            self.scope_stack.pop()



    def push_scope(self, node):

        typename = type(node).__name__


        if "InterfaceDeclarationSyntax" in typename:

            _, end = node_range(node)

            if end:

                name = self.extract_name(node)

                self.scope_stack.append(
                    {
                        "kind": "interface",
                        "name": name,
                        "end": end
                    }
                )


                self.interface_name = name



    def current_interface(self):

        for item in reversed(self.scope_stack):

            if item["kind"] == "interface":
                return item["name"]

        return self.interface_name


    def extract_name(self,node):

        """
        Handles:

        interface aes_if;

        depending on pyslang version
        """

        try:

            return str(
                node.name.valueText
            )

        except Exception:
            pass


        try:

            return str(
                node.name.value
            )

        except Exception:
            pass


        return None


    def extract_signal(self,node):

        """
        Extract declarations:

        logic valid;
        input logic req;
        output logic [31:0] data;

        """

        text = node_text(
            node,
            self.source_text
        )


        signal_name = None


        try:

            signal_name = str(
                node.declarators[0].name.valueText
            )

        except Exception:
            pass


        if signal_name is None:
            return



        direction = "logic"

        if "input" in text:
            direction = "input"

        elif "output" in text:
            direction = "output"

        elif "inout" in text:
            direction = "inout"



        width = ""

        if "[" in text and "]" in text:

            left = text.find("[")
            right = text.find("]")

            width = text[left:right+1]



        self.signals.append(

            InterfaceSignal(

                interface_name=self.current_interface(),

                signal_name=signal_name,

                direction=direction,

                width=width,

                source_file=self.source_file,

                provenance=text.strip()

            )

        )

    def extract_modport(self,node):

        text = node_text(
            node,
            self.source_text
        )


        name = None


        try:

            name = str(
                node.name.valueText
            )

        except Exception:
            return



        ports = []


        if "(" in text and ")" in text:

            body = text.split("(",1)[1]
            body = body.split(")",1)[0]


            for item in body.split(","):

                item = item.strip()

                if item:

                    ports.append(item)



        self.modports.append(

            InterfaceModport(

                interface_name=self.current_interface(),

                modport_name=name,

                ports=ports,

                source_file=self.source_file,

                provenance=text.strip()

            )

        )


    def extract_clocking_block(self, node):

        """
        Extract:

        clocking cb @(posedge clk);
            input req;
            output rsp;
        endclocking

        """

        text = node_text(
            node,
            self.source_text
        )


        name = None

        try:
            name = str(node.name.valueText)

        except Exception:
            pass


        if name is None:
            return



        clock_signal = None
        edge = "posedge"

        if "@(" in text:

            event = text.split("@(",1)[1]
            event = event.split(")",1)[0]

            tokens = event.split()

            if len(tokens) >= 2:

                edge = tokens[0]
                clock_signal = tokens[1]

            elif len(tokens) == 1:

                clock_signal = tokens[0]



        inputs = []
        outputs = []


        for line in text.splitlines():

            line = line.strip()


            if line.startswith("input"):

                pieces = line.replace(
                    ";",""
                ).split()

                if len(pieces):

                    inputs.append(
                        pieces[-1]
                    )


            elif line.startswith("output"):

                pieces = line.replace(
                    ";",""
                ).split()

                if len(pieces):

                    outputs.append(
                        pieces[-1]
                    )



        self.clocking_blocks.append(

            ClockingBlock(

                interface_name=self.current_interface(),

                clocking_name=name,

                clock_signal=clock_signal,

                edge=edge,

                inputs=inputs,

                outputs=outputs,

                source_file=self.source_file,

                provenance=text.strip()

            )

        )

    def infer_clock_reset(self):

        """
        Adds clock/reset hints to signals.

        This is intentionally conservative.
        We do not want incorrect mappings.
        """

        clock = None
        reset = None


        for sig in self.signals:

            name = sig.signal_name.lower()


            if clock is None:

                if name in (
                    "clk",
                    "clock",
                    "clk_i",
                    "clk_in",
                    "pclk"
                ):
                    clock = sig.signal_name



            if reset is None:

                if name in (
                    "rst",
                    "reset",
                    "rst_n",
                    "reset_n",
                    "rst_ni"
                ):
                    reset = sig.signal_name



        for sig in self.signals:

            sig.clock = clock
            sig.reset = reset


    def extract(self, root):


        def callback(node):

            self.update_scope(node)

            self.push_scope(node)


            typename = type(node).__name__



            if (
                "NetDeclarationSyntax" in typename
                or
                "VariableDeclarationSyntax" in typename
            ):

                self.extract_signal(node)



            elif "ModportDeclarationSyntax" in typename:

                self.extract_modport(node)



            elif "ClockingDeclarationSyntax" in typename:

                self.extract_clocking_block(node)



        root.visit(
            f=callback
        )


        self.infer_clock_reset()


        return InterfaceIntent(

            interface_name=self.interface_name,

            signals=self.signals,

            modports=self.modports,

            clocking_blocks=self.clocking_blocks,

            source_file=self.source_file

        )


def parse_interface(path):

    path = str(path)


    tree = SyntaxTree.fromFile(
        path
    )


    source_text = Path(
        path
    ).read_text()


    extractor = InterfaceExtractor(

        source_text,

        path

    )


    return extractor.extract(
        tree.root
    )

def interface_to_dict(intent):


    return {

        "interface_name":
            intent.interface_name,


        "source_file":
            intent.source_file,


        "signals":

            [

                {

                    "name":
                        s.signal_name,

                    "direction":
                        s.direction,

                    "width":
                        s.width,

                    "clock":
                        s.clock,

                    "reset":
                        s.reset,

                    "provenance":
                        s.provenance

                }

                for s in intent.signals

            ],


        "modports":

            [

                {

                    "name":
                        m.modport_name,

                    "ports":
                        m.ports,

                    "provenance":
                        m.provenance

                }

                for m in intent.modports

            ],


        "clocking_blocks":

            [

                {

                    "name":
                        c.clocking_name,

                    "clock":
                        c.clock_signal,

                    "edge":
                        c.edge,

                    "inputs":
                        c.inputs,

                    "outputs":
                        c.outputs

                }

                for c in intent.clocking_blocks

            ]

    }


def find_interfaces(root):

    """
    Find OpenTitan IP-local interface files.

    Typical examples:

        hw/ip/aes/dv/env/aes_if.sv
        hw/ip/spi_device/dv/env/spi_if.sv

    """

    root = Path(root)


    for path in root.rglob("*_if.sv"):

        normalized = str(path).replace("\\", "/")


        if "hw/ip" not in normalized:
            continue


        yield path


def parse_multiple_interfaces(root):

    results = {}


    for path in find_interfaces(root):

        print(
            f"Parsing interface: {path}"
        )


        try:

            intent = parse_interface(
                path
            )


            results[str(path)] = interface_to_dict(
                intent
            )


        except Exception as e:

            print(
                f"FAILED: {path}"
            )

            print(e)


            results[str(path)] = {

                "error": str(e)

            }


    return results


if __name__ == "__main__":


    ROOT = (
        "/home/rk6650/VeriTriples/"
        "data/opentitan"
    )


    results = parse_multiple_interfaces(
        ROOT
    )


    with open(
        "interface_intent.json",
        "w"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

