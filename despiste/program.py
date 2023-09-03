from typing import List, Dict

from despiste.instruction import Instruction
from despiste.instruction_context import InstructionContext
from despiste.utils import cut


class Program:
    """
    A Program represents a set of instructions that can be loaded to the DSP.
    The maximum amount of instructions that can be loaded is 256 (1KB of Program RAM).
    """
    instructions: List[Instruction] = []
    context: InstructionContext = InstructionContext()

    @staticmethod
    def from_binary(source: str) -> 'Program':
        # Make sure the source is a multiple of 32, since each instruction is 32 bytes.
        assert len(source) % 32 == 0

        p = Program()

        p.instructions = []

        num_instructions = len(source) // 32
        for n in range(0, num_instructions):
            instruction_bytes = cut(source, 32 * n, 32 * n + 32)

            instruction = Instruction.from_binary(instruction_bytes)
            p.instructions.append(instruction)
        return p

    def to_binary(self) -> str:
        result = ""
        for inst in self.instructions:
            result += inst.to_binary()

        return result

    @staticmethod
    def from_text(lines) -> 'Program':
        p = Program()

        # Labels and constants must be registered first so that they can be used before their declaration
        instruction_counter = 0
        for line in lines:
            line = line.replace(',', ' ').replace('\t', ' ').upper().strip()
            # Is it a full line comment? Or perhaps empty?
            if line.startswith(';') or line == '':
                continue
            # Remove any trailing comment
            line = line.split(';', 1)[0]
            # Is it a label line?
            # The check for spaces is needed to avoid stuff like 'JMP LABEL:'
            if line.endswith(':') and " " not in line:
                # The label should point to the next instruction to be registered
                p.context.register_label(line, instruction_counter)
            # Is it a constant?
            elif '=' in line:
                p.context.register_constant(line)
            else:
                instruction_counter += 1

        # Second pass is for instructions only
        for line in lines:
            # Avoid the pesky commas, all upper case and clean
            line = line.replace(',', ' ').replace('\t', ' ').upper().strip()
            # Is it a full line comment? Or perhaps empty?
            if line.startswith(';') or line == '':
                continue

            # Remove any trailing comment
            line = line.split(';', 1)[0]

            # Labels and constants are already registered, so ignore
            if '=' in line:
                continue
            # The check for spaces is needed to avoid stuff like 'JMP LABEL:'
            elif line.endswith(':') and " " not in line:
                continue
            else:
                inst = Instruction.from_text(line.split(), p.context)
                p.instructions.append(inst)

        return p

    def __str__(self):
        return "\n".join([str(x) for x in self.instructions])
