from enum import Enum
from typing import List


def s2b(opcode_value: bytes) -> bytes:
    """Converts an opcode value to its bytes representation"""
    return int(opcode_value, 2).to_bytes(len(opcode_value), 'big')


class OpCodes(Enum):
    pass


class Command:
    """
    A command tells the DSP to perform a specific action.
    The DSP can execute up to 6 commands in a single cycle (!).
    The Sega SCU official manual uses the Command word in the same meaning.
    """

    opcode: OpCodes

    @staticmethod
    def opcode_from_bytes(source: bytes, opcode_family: OpCodes):
        for opcode in opcode_family:
            if opcode.value == source:
                return opcode
        raise Exception(f"Could not find opcode for bytes {source}")
    ...


class D1BusOpcodes(OpCodes):
    NOP = s2b(b'00')  # No Operation
    MOV_S_D = s2b(b'01')  # Transfer SImm to [destination]
    MOV_I_D = s2b(b'11')  # Transfer [source] to [destination]


class D1BusDataSource(Enum):
    DATA_RAM0 = s2b(b'0000')  # DATA RAM0
    DATA_RAM1 = s2b(b'0001')  # DATA RAM1
    DATA_RAM2 = s2b(b'0010')  # DATA RAM2
    DATA_RAM3 = s2b(b'0011')  # DATA RAM3
    DATA_RAM0_INC = s2b(b'0100')  # DATA RAM0, CT0++
    DATA_RAM1_INC = s2b(b'0101')  # DATA RAM1, CT1++
    DATA_RAM2_INC = s2b(b'0110')  # DATA RAM2, CT2++
    DATA_RAM3_INC = s2b(b'0111')  # DATA RAM3, CT3++
    ALU_LOW = s2b(b'1101')
    ALU_HIGH = s2b(b'1110')


class D1BusDataDestination(Enum):
    DATA_RAM0_INC = s2b(b'0000')  # DATA RAM0, CT0++
    DATA_RAM1_INC = s2b(b'0001')  # DATA RAM1, CT1++
    DATA_RAM2_INC = s2b(b'0010')  # DATA RAM2, CT2++
    DATA_RAM3_INC = s2b(b'0011')  # DATA RAM3, CT3++
    RX = s2b(b'0100')
    PL = s2b(b'0101')
    RA0 = s2b(b'0110')
    WA0 = s2b(b'0111')
    LOP = s2b(b'1010')
    TOP = s2b(b'1011')
    CT0 = s2b(b'1100')
    CT1 = s2b(b'1101')
    CT2 = s2b(b'1110')
    CT3 = s2b(b'1111')


class D1BusControlCommand(Command):
    source: D1BusDataSource
    destination: D1BusDataDestination
    immediate: int

    def from_binary(self, source):
        source_list = list(source)

        self.opcode = self.opcode_from_bytes(bytes(source_list[12:14]), AluOpcodes)
        self.destination = D1BusDataDestination(bytes(source_list[8:12]))

        # if source is IMMEDIATE
        if self.opcode == D1BusOpcodes.MOV_I_D:
            self.immediate = int(bytes(source_list[0:8]))
            self.source = None
        elif self.opcode == D1BusOpcodes.MOV_S_D:
            self.immediate = None
            self.source = D1BusDataSource(bytes(source_list[0:4]))


class YBusControlCommand(Command):
    def from_binary(self, source):
        ...


class XBusOpcodes(OpCodes):
    NOP     = b'000'


class XBusControlCommand(Command):
    def from_binary(self, source):
        ...


class AluOpcodes(OpCodes):
    NOP     = s2b(b'0000')  # No Operation
    AND     = s2b(b'0001')  # AND on [ACL] and [PL]
    OR      = s2b(b'0010')
    XOR     = s2b(b'0011')
    ADD     = s2b(b'0100')  # Add [ACL] with [PL]
    SUB     = s2b(b'0101')  # Subtract [ACL] from [PL]
    AD2     = s2b(b'0110')  # Add [ACH][ACL] with [PH][PL]
    SR      = s2b(b'1000')  # Shift right [ACL] 1 bit
    RR      = s2b(b'1001')  # Rotate right [ACL] 1 bit
    SL      = s2b(b'1010')  # Shift left [ACL] 1 bit
    RL      = s2b(b'1011')  # Rotate left [ACL] 1 bit
    RL8     = s2b(b'1111')  # Rotate left [ACL] 8 bits


class AluControlCommand(Command):

    def from_binary(self, source: bytes):
        self.opcode = self.opcode_from_bytes(source, AluOpcodes)


class Instruction:
    """
    An instruction packs commands to be executed in the same DSP cycle.
    The Sega SCU official manual calls them 'Operation Commands'.
    """

    aluControlCommand: AluControlCommand
    xBusControlCommand: XBusControlCommand
    yBusControlCommand: YBusControlCommand
    d1BusControlCommand: D1BusControlCommand

    def from_binary(self, source):
        source_list = list(source)

        # Assume we are on a big endian system. We only reverse here, at the entrypoint
        source_list.reverse()

        # Make sure an instruction is 32 bytes long.
        assert len(source_list) == 32

        # First 14 bytes are D1-Bus Control
        self.d1BusControlCommand = D1BusControlCommand()
        self.d1BusControlCommand.from_binary(bytes(source_list[0:14]))

        # Bytes 14 to 19 are Y-Bus Control
        self.yBusControlCommand = YBusControlCommand()
        self.yBusControlCommand.from_binary(bytes(source_list[14:20]))

        # Bytes 20 to 25 are X-Bus Control
        self.xBusControlCommand = XBusControlCommand()
        self.xBusControlCommand.from_binary(bytes(source_list[20:26]))

        # Bytes 26 to 29 are ALU Control
        self.aluControlCommand = AluControlCommand()
        self.aluControlCommand.from_binary(bytes(source_list[26:30]))

        # Bytes 30 and 31 are meant to be zero
        assert source_list[30:32] == [0, 0]
        ...

    def to_binary(self):
        ...


class Program:
    """
    A Program represents a set of instructions that can be loaded to the DSP.
    The maximum amount of instructions that can be loaded is 256 (1KB of Program RAM).
    """
    instructions: List[Instruction]

    def from_binary(self, source: bytes):
        source_list = list(source)
        # Make sure the source is a multiple of 32, since each instruction is 32 bytes.
        assert len(source_list) % 32 == 0

        self.instructions = []

        num_instructions = len(source_list) // 32
        for n in range(0, num_instructions):
            instruction_bytes = bytes(source_list[n:(n + 32)])

            instruction = Instruction()
            instruction.from_binary(instruction_bytes)
            self.instructions.append(instruction)

    def to_binary(self):
        ...
