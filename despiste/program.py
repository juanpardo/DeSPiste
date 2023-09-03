from enum import Enum
from typing import List, Dict

from despiste.commands import AluControlCommand, XBusControlCommand, YBusControlCommand, D1BusControlCommand, Command, \
    SpecialCommand, XBusOpcodes, YBusOpcodes, EndCommand, LoopCommand, DMACommand, MVICommand, JumpCommand
from despiste.utils import cut


class Instruction:
    """
    An instruction packs commands to be executed in the same DSP cycle.
    The Sega SCU official manual calls them 'Operation Commands'.
    """

    aluControlCommand: AluControlCommand = None
    xBusControlCommand: XBusControlCommand = None
    yBusControlCommand: YBusControlCommand = None
    d1BusControlCommand: D1BusControlCommand = None

    specialCommand: SpecialCommand = None

    @staticmethod
    def from_commands(cmds: List[Command]) -> 'Instruction':
        inst = Instruction()
        if len(cmds) == 1 and isinstance(cmds[0], SpecialCommand):
            inst.specialCommand = cmds[0]
            return inst

        for cmd in cmds:
            match cmd:
                case AluControlCommand():
                    inst.aluControlCommand = cmd
                case XBusControlCommand():
                    if inst.xBusControlCommand is None:
                        inst.xBusControlCommand = cmd
                    elif inst.xBusControlCommand.opcode == XBusOpcodes.MOV_SRC_X and cmd.opcode == XBusOpcodes.MOV_MUL_P:
                        inst.xBusControlCommand.opcode = XBusOpcodes.MOV_SRC_X_MUL_P
                    elif inst.xBusControlCommand.opcode == XBusOpcodes.MOV_MUL_P and cmd.opcode == XBusOpcodes.MOV_SRC_X:
                        inst.xBusControlCommand.source = cmd.source
                        inst.xBusControlCommand.opcode = XBusOpcodes.MOV_SRC_X_MUL_P
                    else:
                        raise Exception(f"Incompatible commands for XBus: {inst.xBusControlCommand.to_text()} and {cmd.to_text()}")
                case YBusControlCommand():
                    if inst.yBusControlCommand is None:
                        inst.yBusControlCommand = cmd
                    elif inst.yBusControlCommand.opcode == YBusOpcodes.MOV_SRC_Y and cmd.opcode == YBusOpcodes.MOV_ALU_A:
                        inst.yBusControlCommand.opcode = YBusOpcodes.MOV_SRC_Y_ALU_A
                    elif inst.yBusControlCommand.opcode == YBusOpcodes.MOV_ALU_A and cmd.opcode == YBusOpcodes.MOV_SRC_Y:
                        inst.yBusControlCommand.source = cmd.source
                        inst.yBusControlCommand.opcode = YBusOpcodes.MOV_SRC_Y_ALU_A
                    else:
                        raise Exception(f"Incompatible commands for YBus: {inst.yBusControlCommand.to_text()} and {cmd.to_text()}")
                case D1BusControlCommand():
                    inst.d1BusControlCommand = cmd
                case _:
                    raise Exception(f"Unexpected command type {type(cmd)}")

        if not inst.aluControlCommand:
            inst.aluControlCommand = AluControlCommand.from_text(["NOP"])
        if not inst.xBusControlCommand:
            inst.xBusControlCommand = XBusControlCommand.from_text(["NOP"])
        if not inst.yBusControlCommand:
            inst.yBusControlCommand = YBusControlCommand.from_text(["NOP"])
        if not inst.d1BusControlCommand:
            inst.d1BusControlCommand = D1BusControlCommand.from_text(["NOP"])
        return inst

    def to_text(self) -> List[str]:
        if self.specialCommand:
            return [self.specialCommand.to_text()]
        else:
            result = []
            if self.aluControlCommand:
                result.extend(self.aluControlCommand.to_text())
            if self.xBusControlCommand:
                result.extend(self.xBusControlCommand.to_text())
            if self.yBusControlCommand:
                result.extend(self.yBusControlCommand.to_text())
            if self.d1BusControlCommand:
                result.extend(self.d1BusControlCommand.to_text())
            return result

    @staticmethod
    def from_binary(source: str):
        # Make sure an instruction is 32 bytes long.
        assert len(source) == 32

        inst = Instruction()

        # Bytes 30 and 31 are meant to be zero for normal instructions
        if cut(source, 30, 32) == '00':
            # First 14 bytes are D1-Bus Control
            inst.d1BusControlCommand = D1BusControlCommand.from_binary(cut(source, 0, 14))

            # Bytes 14 to 19 are Y-Bus Control
            inst.yBusControlCommand = YBusControlCommand.from_binary(cut(source, 14, 20))

            # Bytes 20 to 25 are X-Bus Control
            inst.xBusControlCommand = XBusControlCommand.from_binary(cut(source, 20, 26))

            # Bytes 26 to 29 are ALU Control
            inst.aluControlCommand = AluControlCommand.from_binary(cut(source, 26, 30))

        # END cmds
        elif cut(source, 28, 32) == '1111':
            inst.specialCommand = EndCommand.from_binary(cut(source, 27, 32))
        # Loop cmds
        elif cut(source, 28, 32) == '1110':
            inst.specialCommand = LoopCommand.from_binary(cut(source, 27, 32))
        elif cut(source, 28, 32) == '1100':
            inst.specialCommand = DMACommand.from_binary(source)
        elif cut(source, 30, 32) == '10':
            inst.specialCommand = MVICommand.from_binary(source)
        elif cut(source, 28, 32) == '1101':
            inst.specialCommand = JumpCommand.from_binary(source)
        else:
            raise Exception("Unknown command!")

        return inst

    def to_binary(self) -> str:
        if self.specialCommand is None:
            return f"00{self.aluControlCommand.to_binary()}{self.xBusControlCommand.to_binary()}{self.yBusControlCommand.to_binary()}{self.d1BusControlCommand.to_binary()}"
        else:
            return self.specialCommand.to_binary()

    def __str__(self):
        return "\t\t\t".join([
            str(self.aluControlCommand),
            str(self.xBusControlCommand),
            str(self.yBusControlCommand),
            str(self.d1BusControlCommand),
        ])


class Program:
    """
    A Program represents a set of instructions that can be loaded to the DSP.
    The maximum amount of instructions that can be loaded is 256 (1KB of Program RAM).
    """
    instructions: List[Instruction] = []
    labels: Dict[str, int]  # Key is the label name and value is the instruction index it points to

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

    def register_label(self, label: str, instruction_offset: int):

        # The maximum offset is 256, as the DSP Program RAM can't hold more instructions
        assert instruction_offset < 256

        # Clean up the label name by removing unwanted spaces and the colon
        key = label.replace(":", "", 1).strip()
        assert not self.labels.has_key(key)
        self.labels[key] = instruction_offset

    def register_constant(self, line):
        assert line.contains('=')
        array = line.split("=")
        assert len(array) == 2
        self.constants[array[0].strip()] = array[1].strip()

    @staticmethod
    def from_text(lines) -> 'Program':
        p = Program()
        for line in lines:
            # Avoid the pesky commas, all upper case and clean
            line = line.replace(',', ' ').upper().strip()
            # Is it a label line?
            if line.endswith(':'):
                # The label should point to the next instruction to be registered
                p.register_label(line, len(p.instructions))
            # Is it a constant?
            elif line.contains('='):
                p.register_constant(line)
            # Is it a full line comment?
            elif line.strip().startswith(';'):
                pass
            else:
                inst = Instruction.from_text(line.split())
                p.instructions.append(inst)

    def __str__(self):
        return "\n".join([str(x) for x in self.instructions])
