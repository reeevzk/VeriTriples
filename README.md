VeriTriples is an ongoing research project investigating LLM-assisted SystemVerilog Assertion generation through structured hardware design/verification intent extraction.

Completed components include:

- Automated collection and analysis of open-source Verilog/SystemVerilog hardware repositories
- Python infrastructure for dependency resolution and scalable Cadence JasperGold formal verification
- RTL structural analysis using the `pyslang` SystemVerilog frontend
- Extraction of module interfaces, ports, signals, state elements, and structural relationships into machine-readable representations
- Automated parsing of OpenTitan IP metadata and natural-language testplans
- Generation of dependency-aware Tcl build environments for OpenTitan formal verification
- Construction of datasets linking RTL structure, verification artifacts, and natural-language design intent

Current work focuses on:

- Extracting semantic information from UVM testbench infrastructure (scoreboards, monitors, sequences, and testbench hierarchy)
- Improving design-intent representations for downstream LLM prompting
- Evaluating how structured design intent affects generated SystemVerilog Assertion quality
