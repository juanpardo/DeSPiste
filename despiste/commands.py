from enum import Enum
from typing import List

from despiste.utils import cut


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

    @staticmethod
    def from_binary(source: str) -> Command:
        cmd = D1BusControlCommand()
        cmd.opcode = D1BusOpcodes(cut(source, 12, 14))
        if cmd.opcode != D1BusOpcodes.NOP:
            cmd.destination = D1BusDataDestination(cut(source, 8, 12))

        # if source is IMMEDIATE
        if cmd.opcode == D1BusOpcodes.MOV_IMM_DST:
            cmd.immediate = int(cut(source, 0, 8), 2)
            cmd.source = None
        elif cmd.opcode == D1BusOpcodes.MOV_SRC_DST:
            cmd.immediate = None
            cmd.source = D1BusDataSource(cut(source, 0, 4))

        return cmd

    def to_binary(self) -> str:
        result = self.opcode.value

        if self.opcode == D1BusOpcodes.NOP:
            result += "000000000000"

        if self.destination:
            result += self.destination.value

        if self.immediate is not None:
            result += bin(self.immediate)[2:].zfill(8)
        elif self.source:
            result += "0000" + self.source.value

        return result

    @staticmethod
    def from_text(source: List[str]) -> Command:
        cmd = D1BusControlCommand()
        if source[0] == "NOP":
            assert len(source) == 1
            cmd.opcode = D1BusOpcodes.NOP
            return cmd

        cmd.destination = D1BusDataDestination[source[2]]
        # Using SRC?
        try:
            cmd.source = D1BusDataSource[source[1]]
            cmd.opcode = D1BusOpcodes.MOV_SRC_DST
        except KeyError:
            if source[1].startswith('#'):
                source[1] = source[1][1:]
            cmd.immediate = int(source[1])
            cmd.opcode = D1BusOpcodes.MOV_IMM_DST
        return cmd

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

    @staticmethod
    def from_binary(source):
        cmd = YBusControlCommand()
        cmd.opcode = YBusOpcodes(cut(source, 3, 6))
        ops_with_source = [
            YBusOpcodes.MOV_SRC_Y,
            YBusOpcodes.MOV_SRC_Y_ALU_A,
            YBusOpcodes.MOV_SRC_A
        ]
        if cmd.opcode in ops_with_source:
            cmd.source = XYBusDataSource(cut(source, 0, 3))
        else:
            cmd.source = None

        return cmd

    def to_binary(self) -> str:
        if self.source is None:
            return f"{self.opcode.value}000"
        else:
            return f"{self.opcode.value}{self.source.value}"

    @staticmethod
    def from_text(source):
        cmd = YBusControlCommand()

        if source[0] == 'NOP':
            assert len(source) == 1
            cmd.opcode = YBusOpcodes.NOP
            return cmd

        if source[0] == 'CLR':
            assert len(source) == 2
            assert source[1] == "A"
            cmd.opcode = YBusOpcodes.CLR_A
            return cmd

        assert source[0] == "MOV"
        if source[2] == 'Y':
            cmd.opcode = YBusOpcodes.MOV_SRC_Y
            cmd.source = XYBusDataSource[source[1]]
        else:
            try:
                cmd.source = XYBusDataSource[source[1]]
                cmd.opcode = YBusOpcodes.MOV_SRC_A
            except KeyError:
                cmd.opcode = YBusOpcodes.MOV_ALU_A
        return cmd

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

    _ops_with_source = [
        XBusOpcodes.MOV_SRC_X,
        XBusOpcodes.MOV_SRC_X_MUL_P,
        XBusOpcodes.MOV_SRC_P
    ]

    @staticmethod
    def from_binary(source: str):
        cmd = XBusControlCommand()
        cmd.opcode = XBusOpcodes(cut(source, 3, 6))
        if cmd.opcode in cmd._ops_with_source:
            cmd.source = XYBusDataSource(cut(source, 0, 3))
        else:
            cmd.source = None
        return cmd

    def to_binary(self) -> str:
        if self.source is None:
            return f"{self.opcode.value}000"
        else:
            return f"{self.opcode.value}{self.source.value}"

    @staticmethod
    def from_text(source: List[str]):
        cmd = XBusControlCommand()

        if source[0] == 'NOP':
            cmd.opcode = XBusOpcodes.NOP
            return cmd

        if source[2] == 'X':
            cmd.opcode = XBusOpcodes.MOV_SRC_X
            cmd.source = XYBusDataSource[source[1]]
        else:
            try:
                cmd.source = XYBusDataSource[source[1]]
                cmd.opcode = XBusOpcodes.MOV_SRC_P
            except KeyError:
                cmd.opcode = XBusOpcodes.MOV_MUL_P
        return cmd

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

    @staticmethod
    def from_binary(source: str):
        cmd = AluControlCommand()
        cmd.opcode = AluOpcodes(source)
        return cmd

    def to_binary(self) -> str:
        return self.opcode.value

    @staticmethod
    def from_text(source: List[str]) -> Command:
        assert len(source) == 1
        cmd = AluControlCommand()
        cmd.opcode = AluOpcodes[source[0]]
        return cmd

    def to_text(self) -> List[str]:
        return [self.opcode.name]


class SpecialCommand(Command):
    """
    Represents commands that are lonely: DMA, END, JMP...
    """
    pass


class EndOpcodes(OpCodes):
    END = "11110"
    ENDI = "11111"


class EndCommand(SpecialCommand):
    @staticmethod
    def from_binary(source: str) -> Command:
        cmd = EndCommand()
        cmd.opcode = EndOpcodes(source)
        return cmd

    def to_binary(self) -> str:
        return self.opcode.value.ljust(32, "0")

    @staticmethod
    def from_text(source: List[str]) -> Command:
        assert len(source) == 1
        cmd = EndCommand()
        cmd.opcode = EndOpcodes[source[0]]
        return cmd

    def to_text(self) -> List[str]:
        return [self.opcode.name]
