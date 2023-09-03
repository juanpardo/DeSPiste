from typing import List, Optional
from despiste.commands import AluControlCommand, XBusControlCommand, YBusControlCommand, D1BusControlCommand, Command, \
    SpecialCommand, XBusOpcodes, YBusOpcodes, EndCommand, LoopCommand, DMACommand, MVICommand, JumpCommand, \
    generate_command_from_text, JumpMode
from despiste.instruction_context import InstructionContext
from despiste.utils import cut


command_args = {
    'NOP': 0,
    # ALU
    'AND': 0,
    'OR': 0,
    'XOR': 0,
    'ADD': 0,
    'SUB': 0,
    'AD2': 0,
    'SR': 0,
    'RR': 0,
    'SL': 0,
    'RL': 0,
    'RL8': 0,

    # OTHER
    'MOV': 2,
    'CLR': 1,
    'DMA': 3,
    'MVI': 2,
    'JMP': [1, 2],
    # LOOPS
    'BTM': 0,
    'LPS': 0,
    # ENDS
    'END': 0,
    'ENDI': 0,
}


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
    def from_text(elements: List[str], context: Optional[InstructionContext]) -> 'Instruction':
        commands = []
        current_command = []

        for element in elements:
            # If the first element, add it
            if len(current_command) == 0:
                current_command.append(element)
            # If the element is a command keyword, start a new command
            elif element in command_args:
                cmd = generate_command_from_text(current_command, context)
                if cmd:
                    commands.append(cmd)
                current_command = [element]
            # Otherwise it must be a command parameter, add it
            else:
                current_command.append(element)

        if len(current_command) > 0:
            cmd = generate_command_from_text(current_command, context)
            if cmd:
                commands.append(cmd)

        if len(commands):
            return Instruction.from_commands(commands)
        else:
            return Instruction.get_noop()

    @staticmethod
    def get_noop() -> 'Instruction':
        inst = Instruction()
        inst.yBusControlCommand = YBusControlCommand.get_noop()
        inst.xBusControlCommand = XBusControlCommand.get_noop()
        inst.aluControlCommand = AluControlCommand.get_noop()
        inst.d1BusControlCommand = D1BusControlCommand.get_noop()
        return inst

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
                        msg = f"Incompatible commands for YBus: {inst.yBusControlCommand.to_text()} and {cmd.to_text()}"
                        raise Exception(msg)
                case D1BusControlCommand():
                    inst.d1BusControlCommand = cmd
                case _:
                    msg = f"Unexpected command type {type(cmd)}"
                    raise Exception(msg)

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
            return self.specialCommand.to_text()
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
