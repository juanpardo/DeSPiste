from enum import Enum
from typing import List


def cut(source: str, start: int, end: int) -> str:
    """
    Given a string meant to represent a list of bits, returns a substring.
    start and end will be interpreted reversed
    :param source: A string comprised of 1's and 0's
    :param start: Where to start cutting
    :param end: Where to end cutting (exclusive)
    :return: A string that comprises the numbers between start and end.
    """
    size = len(source)
    return source[size-end: size-start]


class OpCodes(Enum):
    pass


class Command:
    """
    A command tells the DSP to perform a specific action.
    The DSP can execute up to 6 commands in a single cycle (!).
    The Sega SCU official manual uses the Command word in the same meaning.
    """

    opcode: OpCodes

    def to_text(self) -> List[str]:
        return []

    def __str__(self) -> str:
        return '\t\t\t'.join(self.to_text())


class D1BusOpcodes(OpCodes):
    NOP = '00'  # No Operation
    MOV_IMM_DST = '01'  # Transfer SImm to [destination]
    MOV_SRC_DST = '11'  # Transfer [source] to [destination]


class D1BusDataSource(Enum):
    RAM0 = '0000'  # DATA RAM0
    RAM1 = '0001'  # DATA RAM1
    RAM2 = '0010'  # DATA RAM2
    RAM3 = '0011'  # DATA RAM3
    MC0 = '0100'  # DATA RAM0, CT0++
    MC1 = '0101'  # DATA RAM1, CT1++
    MC2 = '0110'  # DATA RAM2, CT2++
    MC3 = '0111'  # DATA RAM3, CT3++
    ALL = '1001'  # ALU LOW
    ALH = '1010'  # ALU HIGH


class D1BusDataDestination(Enum):
    MC0 = '0000'  # DATA RAM0, CT0++
    MC1 = '0001'  # DATA RAM1, CT1++
    MC2 = '0010'  # DATA RAM2, CT2++
    MC3 = '0011'  # DATA RAM3, CT3++
    RX = '0100'
    PL = '0101'
    RA0 = '0110'
    WA0 = '0111'
    LOP = '1010'
    TOP = '1011'
    CT0 = '1100'
    CT1 = '1101'
    CT2 = '1110'
    CT3 = '1111'


class D1BusControlCommand(Command):
    source: D1BusDataSource = None
    destination: D1BusDataDestination = None
    immediate: int = None

    def from_binary(self, source):

        self.opcode = D1BusOpcodes(cut(source, 12, 14))
        if self.opcode != D1BusOpcodes.NOP:
            self.destination = D1BusDataDestination(cut(source, 8, 12))

        # if source is IMMEDIATE
        if self.opcode == D1BusOpcodes.MOV_IMM_DST:
            self.immediate = int(cut(source, 0, 8), 2)
            self.source = None
        elif self.opcode == D1BusOpcodes.MOV_SRC_DST:
            self.immediate = None
            self.source = D1BusDataSource(cut(source, 0, 4))

    def to_text(self) -> List[str]:
        result = self.opcode.name[:3]

        if self.immediate is not None:
            result += f" #{self.immediate}"
        elif self.source:
            result += f" {self.source.name}"

        if self.destination:
            result += f",{self.destination.name}"

        return [result]


class YBusOpcodes(OpCodes):
    NOP         = '000'
    MOV_SRC_Y   = '100' # Moves [source] to Y
    CLR_A       = '001'  # 0 clears the ACH and ACL
    MOV_ALU_A = '010'  # Moves [ALU] to [ACH][ACL] (ACH is 16 bits, ACL is 32 bits)
    MOV_SRC_A = '011'  # Moves [SRC] to [ACL]

    # Undocumented?
    MOV_SRC_Y_ALU_A = '110'  # Undocumented combined operation


class XYBusDataSource(Enum):
    RAM0 = '000'  # DATA RAM0
    RAM1 = '001'  # DATA RAM1
    RAM2 = '010'  # DATA RAM2
    RAM3 = '011'  # DATA RAM3
    MC0 = '100'  # DATA RAM0, CT0++
    MC1 = '101'  # DATA RAM1, CT1++
    MC2 = '110'  # DATA RAM2, CT2++
    MC3 = '111'  # DATA RAM3, CT3++


class YBusControlCommand(Command):
    source: XYBusDataSource

    def from_binary(self, source):
        self.opcode = YBusOpcodes(cut(source, 3, 6))
        ops_with_source = [
            YBusOpcodes.MOV_SRC_Y,
            YBusOpcodes.MOV_SRC_Y_ALU_A,
            YBusOpcodes.MOV_SRC_A
        ]
        if self.opcode in ops_with_source:
            self.source = XYBusDataSource(cut(source, 0, 3))
        else:
            self.source = None

    def to_text(self) -> List[str]:
        if self.opcode == YBusOpcodes.NOP:
            return ["NOP"]
        elif self.opcode == YBusOpcodes.CLR_A:
            return ["CLR A"]
        elif self.opcode == YBusOpcodes.MOV_ALU_A:
            return ["MOV ALU,A"]
        # The rest are MOV operations with source
        elif self.opcode == YBusOpcodes.MOV_SRC_Y:
            return [f"MOV {self.source.name},Y"]
        elif self.opcode == YBusOpcodes.MOV_SRC_A:
            return [f"MOV {self.source.name},A"]
        elif self.opcode == YBusOpcodes.MOV_SRC_Y_ALU_A:
            return [f"MOV {self.source.name},Y", "MOV ALU,A"]
        else:
            raise Exception("Unexpected opcode")


class XBusOpcodes(OpCodes):
    NOP         = '000'
    MOV_SRC_X   = '100' # Moves [source] to X
    MOV_MUL_P   = '010'  # Moves [MUL] to [PH][PL] (PH is 16 bits, PL is 32 bits)
    MOV_SRC_P   = '011'  # Moves [SRC] to [PL]

    # Undocumented?
    MOV_SRC_X_MUL_P = '110'  # Undocumented combined operation


class XBusControlCommand(Command):
    source: XYBusDataSource

    def from_binary(self, source: str):
        self.opcode = XBusOpcodes(cut(source, 3, 6))
        ops_with_source = [
            XBusOpcodes.MOV_SRC_X,
            XBusOpcodes.MOV_SRC_X_MUL_P,
            XBusOpcodes.MOV_SRC_P
        ]
        if self.opcode in ops_with_source:
            self.source = XYBusDataSource(cut(source, 0, 3))
        else:
            self.source = None

    def to_text(self) -> List[str]:
        if self.opcode == XBusOpcodes.NOP:
            return ["NOP"]
        elif self.opcode == XBusOpcodes.MOV_MUL_P:
            return ["MOV MUL,P"]
        elif self.opcode == XBusOpcodes.MOV_SRC_X:
            return [f"MOV {self.source.name},X"]
        elif self.opcode == XBusOpcodes.MOV_SRC_P:
            return [f"MOV {self.source.name},P"]
        elif self.opcode == XBusOpcodes.MOV_SRC_X_MUL_P:
            return [f"MOV {self.source.name},X", "MOV MUL,P"]
        else:
            raise Exception("Unexpected opcode")


class AluOpcodes(OpCodes):
    NOP     = '0000'  # No Operation
    AND     = '0001'  # AND on [ACL] and [PL]
    OR      = '0010'
    XOR     = '0011'
    ADD     = '0100'  # Add [ACL] with [PL]
    SUB     = '0101'  # Subtract [ACL] from [PL]
    AD2     = '0110'  # Add [ACH][ACL] with [PH][PL]
    SR      = '1000'  # Shift right [ACL] 1 bit
    RR      = '1001'  # Rotate right [ACL] 1 bit
    SL      = '1010'  # Shift left [ACL] 1 bit
    RL      = '1011'  # Rotate left [ACL] 1 bit
    RL8     = '1111'  # Rotate left [ACL] 8 bits


class AluControlCommand(Command):

    def from_binary(self, source: str):
        self.opcode = AluOpcodes(source)

    def to_text(self) -> List[str]:
        return [self.opcode.name]


class Instruction:
    """
    An instruction packs commands to be executed in the same DSP cycle.
    The Sega SCU official manual calls them 'Operation Commands'.
    """

    aluControlCommand: AluControlCommand = None
    xBusControlCommand: XBusControlCommand = None
    yBusControlCommand: YBusControlCommand = None
    d1BusControlCommand: D1BusControlCommand = None

    def from_binary(self, source: str):

        # Make sure an instruction is 32 bytes long.
        assert len(source) == 32

        # Bytes 30 and 31 are meant to be zero for normal instructions
        if cut(source, 30, 32) == '00':
            # First 14 bytes are D1-Bus Control
            self.d1BusControlCommand = D1BusControlCommand()
            self.d1BusControlCommand.from_binary(cut(source, 0, 14))

            # Bytes 14 to 19 are Y-Bus Control
            self.yBusControlCommand = YBusControlCommand()
            self.yBusControlCommand.from_binary(cut(source, 14, 20))

            # Bytes 20 to 25 are X-Bus Control
            self.xBusControlCommand = XBusControlCommand()
            self.xBusControlCommand.from_binary(cut(source, 20, 26))

            # Bytes 26 to 29 are ALU Control
            self.aluControlCommand = AluControlCommand()
            self.aluControlCommand.from_binary(cut(source, 26, 30))

    def __str__(self):
        return "\t\t\t".join([
            str(self.aluControlCommand),
            str(self.xBusControlCommand),
            str(self.yBusControlCommand),
            str(self.d1BusControlCommand),
        ])


    def to_binary(self):
        ...


class Program:
    """
    A Program represents a set of instructions that can be loaded to the DSP.
    The maximum amount of instructions that can be loaded is 256 (1KB of Program RAM).
    """
    instructions: List[Instruction] = []

    def from_binary(self, source: str):
        # Make sure the source is a multiple of 32, since each instruction is 32 bytes.
        assert len(source) % 32 == 0

        code = []

        self.instructions = []

        num_instructions = len(source) // 32
        for n in range(0, num_instructions):
            instruction_bytes = cut(source, 32 * n, 32 * n + 32)

            instruction = Instruction()
            instruction.from_binary(instruction_bytes)
            self.instructions.append(instruction)

            code.append(str(instruction))

    def __str__(self):
        return "\n".join([str(x) for x in self.instructions])

    def to_binary(self):
        ...
