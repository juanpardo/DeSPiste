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

        instruction_lines = []
        instruction_line_number = []

        # Labels and constants must be registered first so that they can be used before their declaration
        instruction_counter = 0
        for line_number, line in enumerate(lines):
            line = line.replace(',', ' ').replace('\t', ' ').upper().strip()
            # Is it a full line comment? Or perhaps empty?
            if line.startswith(';') or line == '':
                continue
            # Remove any trailing comment
            line = line.split(';', 1)[0]
            elements = line.split()
            # Is it a label line?
            # The check for spaces is needed to avoid stuff like 'JMP LABEL:'
            if elements[0].endswith(':'):
                # The label should point to the next instruction to be registered
                p.context.register_label(elements[0], instruction_counter)
                if len(elements) > 1:
                    instruction_counter += 1
                    instruction_lines.append(elements[1:])
                    instruction_line_number.append(line_number+1)
            # Is it a constant?
            elif '=' in line:
                p.context.register_constant(line)
            else:
                instruction_counter += 1
                instruction_lines.append(elements)
                instruction_line_number.append(line_number+1)

        # Second pass is for instructions only
        for idx, line in enumerate(instruction_lines):
            try:
                inst = Instruction.from_text(line, p.context)
                p.instructions.append(inst)
            except Exception as e:
                print(f"An error ({str(e)}) occurred in line {instruction_line_number[idx]}!\n")
                print(f"  {line}")
                raise e

        return p

    def __str__(self):
        return "\n".join([str(x) for x in self.instructions])
