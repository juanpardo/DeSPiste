from typing import Dict


class InstructionContext:
    labels: Dict[str, int] = {}  # Key is the label name and value is the instruction index it points to
    constants: Dict[str, int] = {}  # Key is the constant name

    def register_label(self, label: str, instruction_offset: int):

        # The maximum offset is 256, as the DSP Program RAM can't hold more instructions
        assert instruction_offset < 256

        # Clean up the label name by removing unwanted spaces and the colon
        key = label.replace(":", "", 1).strip()
        assert key not in self.labels
        self.labels[key] = instruction_offset

    def register_constant(self, line):
        assert '=' in line
        array = line.split("=")
        assert len(array) == 2
        self.constants[array[0].strip()] = int(array[1].strip())
