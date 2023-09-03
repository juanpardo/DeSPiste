from enum import Enum
from typing import List, Optional

from despiste.instruction_context import InstructionContext
from despiste.utils import cut


def get_immediate_value_label_aware(value: str, context: Optional[InstructionContext]):
    if value.endswith(":"):
        value = value[:-1]
    return get_immediate_value(value, context, False)


def get_immediate_value_constant_aware(value: str, context: Optional[InstructionContext]):
    return get_immediate_value(value, context, True)


def get_immediate_value(value: str, context: Optional[InstructionContext], use_constant = True):
    # Check if starts with '#' it is an immediate value
    if value.startswith('#'):
        return int(value[1:])

    # It must be either a number or a constant
    try:
        return int(value)
    except ValueError:
        if context:
            if use_constant and context.constants.get(value, None):
                return context.constants.get(value)
            elif not use_constant and context.labels.get(value, None):
                return context.labels.get(value)
            else:
                use = 'constant' if use_constant else 'label'
                msg = f"Immediate value uses a {use} that does not exist: {value}"
                raise Exception(msg)
        else:
            raise Exception(f"Immediate value is must be a number because no context was passed.")


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
    M0 = '0000'  # DATA RAM0
    M1 = '0001'  # DATA RAM1
    M2 = '0010'  # DATA RAM2
    M3 = '0011'  # DATA RAM3
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
    def get_noop() -> 'D1BusControlCommand':
        cmd = D1BusControlCommand()
        cmd.opcode = D1BusOpcodes.NOP
        return cmd

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
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
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
    M0 = '000'  # DATA RAM0
    M1 = '001'  # DATA RAM1
    M2 = '010'  # DATA RAM2
    M3 = '011'  # DATA RAM3
    MC0 = '100'  # DATA RAM0, CT0++
    MC1 = '101'  # DATA RAM1, CT1++
    MC2 = '110'  # DATA RAM2, CT2++
    MC3 = '111'  # DATA RAM3, CT3++


class YBusControlCommand(Command):
    source: XYBusDataSource = None

    @staticmethod
    def get_noop() -> 'YBusControlCommand':
        cmd = YBusControlCommand()
        cmd.opcode = YBusOpcodes.NOP
        return cmd

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
    def from_text(source: List[str], context: Optional[InstructionContext] = None):
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
    source: XYBusDataSource = None

    _ops_with_source = [
        XBusOpcodes.MOV_SRC_X,
        XBusOpcodes.MOV_SRC_X_MUL_P,
        XBusOpcodes.MOV_SRC_P
    ]

    @staticmethod
    def get_noop() -> 'XBusControlCommand':
        cmd = XBusControlCommand()
        cmd.opcode = XBusOpcodes.NOP
        return cmd


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
    def from_text(source: List[str], context: Optional[InstructionContext] = None):
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
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
        assert len(source) == 1
        cmd = AluControlCommand()
        cmd.opcode = AluOpcodes[source[0]]
        return cmd

    def to_text(self) -> List[str]:
        return [self.opcode.name]

    @staticmethod
    def get_noop() -> 'AluControlCommand':
        cmd = AluControlCommand()
        cmd.opcode = AluOpcodes.NOP
        return cmd


class SpecialCommand(Command):
    """
    Represents commands that are lonely: DMA, END, JMP...
    """
    pass


class EndOpcodes(OpCodes):
    END = "11110"
    ENDI = "11111"


class EndCommand(SpecialCommand):
    opcode: EndOpcodes

    @staticmethod
    def from_binary(source: str) -> Command:
        cmd = EndCommand()
        cmd.opcode = EndOpcodes(source)
        return cmd

    def to_binary(self) -> str:
        return self.opcode.value.ljust(32, "0")

    @staticmethod
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
        assert len(source) == 1
        cmd = EndCommand()
        cmd.opcode = EndOpcodes[source[0]]
        return cmd

    def to_text(self) -> List[str]:
        return [self.opcode.name]


class LoopOpcodes(OpCodes):
    BTM = "11100"
    LPS = "11101"


class LoopCommand(SpecialCommand):
    opcode = LoopOpcodes

    @staticmethod
    def from_binary(source: str) -> Command:
        cmd = LoopCommand()
        cmd.opcode = LoopOpcodes(source)
        return cmd

    def to_binary(self) -> str:
        return self.opcode.value.ljust(32, "0")

    @staticmethod
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
        assert len(source) == 1
        cmd = LoopCommand()
        cmd.opcode = LoopOpcodes[source[0]]
        return cmd

    def to_text(self) -> List[str]:
        return [self.opcode.name]


class DMAOpcodes(OpCodes):
    DMA = "1100"
    DMAH = "1100"


class DMADataRam(Enum):
    MC0 = "000"
    MC1 = "001"
    MC2 = "010"
    MC3 = "011"
    PRG = "100"


class DMATransferMode(Enum):
    D0_TO_RAM = "0"
    RAM_TO_D0 = "1"


class DMACounterMode(Enum):
    IMMEDIATE = "0"
    REFERENCED = "1"


class DMACounterRam(Enum):
    MC0 = "000"
    MC1 = "001"
    MC2 = "010"
    MC3 = "011"
    CT0 = '100'
    CT1 = '101'
    CT2 = '110'
    CT3 = '111'


class DMACommand(SpecialCommand):
    opcode: DMAOpcodes
    hold: bool  # Determines if the DSP is to wait for the DMA transfer to finish?
    address_add_mode: int = 1  # Default is 1
    ram_address_pointer: DMADataRam
    dma_mode: DMATransferMode
    data_size: int = None
    dma_counter_mode: DMACounterMode
    dma_counter_ram: DMACounterRam

    @staticmethod
    def from_binary(source: str):
        assert len(source) == 32
        cmd = DMACommand()
        # Opcode
        cmd.opcode = DMAOpcodes(cut(source, 28, 32))

        # DMA mode
        cmd.dma_mode = DMATransferMode(cut(source, 12, 13))
        cmd.hold = cut(source, 14, 15) == "1"
        if cmd.hold:
            cmd.opcode = DMAOpcodes.DMAH

        if cut(source, 13, 14) == "1":
            cmd.dma_counter_mode = DMACounterMode.REFERENCED
        else:
            cmd.dma_counter_mode = DMACounterMode.IMMEDIATE

        # padding
        assert cut(source, 18, 28) == "0000000000"
        # Add mode
        cmd.address_add_mode = int(cut(source, 15, 18))

        # Destination
        cmd.ram_address_pointer = DMADataRam(cut(source, 8, 11))
        if cmd.dma_counter_mode == DMACounterMode.IMMEDIATE:
            cmd.data_size = int(cut(source, 0, 8), 2)
        else:
            cmd.dma_counter_ram = DMACounterRam(cut(source, 0, 3))

        return cmd

    def to_binary(self) -> str:
        result = self.opcode.value + "0000000000"               # opcode + padding
        result += bin(self.address_add_mode)[2:].rjust(3, "0")  # add mode

        # DMA modes
        result += "1" if self.hold else "0"
        result += self.dma_counter_mode.value
        result += self.dma_mode.value

        result += "0"  # padding

        result += self.ram_address_pointer.value
        if self.dma_counter_mode == DMACounterMode.IMMEDIATE:
            result += bin(self.data_size)[2:].rjust(8, "0")
        else:
            result += self.dma_counter_ram.value.rjust(8, "0")

        return result

    @staticmethod
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
        assert source[0] in ["DMA", "DMAH"]
# TODO Handle address-add instructions DMA0, DMA1, DMA2, DMA4, DMA8... DMA64 LOL
        cmd = DMACommand()
        if source[0] == "DMA":
            cmd.opcode = DMAOpcodes.DMA
            cmd.hold = False
        else:
            cmd.opcode = DMAOpcodes.DMAH
            cmd.hold = True

        if source[1] == "D0":
            cmd.dma_mode = DMATransferMode.D0_TO_RAM
            cmd.ram_address_pointer = DMADataRam[source[2]]
        else:
            cmd.dma_mode = DMATransferMode.RAM_TO_D0
            cmd.ram_address_pointer = DMADataRam[source[1]]

        try:
            cmd.dma_counter_ram = DMACounterRam[source[3]]
            cmd.dma_counter_mode = DMACounterMode.REFERENCED
        except KeyError:
            cmd.data_size = int(source[3])
            cmd.dma_counter_mode = DMACounterMode.IMMEDIATE

        return cmd

    def to_text(self) -> List[str]:
        result = "DMA"
        if self.hold:
            result += "H"

        if self.dma_mode == DMATransferMode.D0_TO_RAM:
            result += f" D0,{self.ram_address_pointer.name},"
        else:
            result += f" {self.ram_address_pointer.name},D0,"

        if self.dma_counter_mode == DMACounterMode.IMMEDIATE:
            result += str(self.data_size)
        else:
            result += self.dma_counter_ram.name

        return [result]


class MVIOpcodes(OpCodes):
    MVI = "10"


class MVIStorageDestination(Enum):
    MC0 = "0000"
    MC1 = "0001"
    MC2 = "0010"
    MC3 = "0011"
    RX = "0100"
    PL = "0101"
    RA0 = "0110"
    WA0 = "0111"

    LOP = "1010"

    PC = "1100"


class MVIConditionStatus(Enum):
    Z   = "100001"  # If Z == 1
    NZ  = "000001"  # If Z == 0
    S   = "100010"  # If S == 1
    NS  = "000010"  # If S == 0
    C   = "100100"  # If C == 1
    NC  = "000100"  # If C == 0
    T0  = "101000"  # If T0 == 1
    NT0 = "001000"  # If T0 == 0
    ZS  = "100011"  # If Z == 1 OR S == 1
    NZS = "000011"  # If Z == 0 AND S == 0


class MVICommand(SpecialCommand):
    opcode: MVIOpcodes
    immediate: int
    destination: MVIStorageDestination
    condition: MVIConditionStatus

    @staticmethod
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
        cmd = MVICommand()
        assert source[0] == 'MVI'
        cmd.opcode = MVIOpcodes.MVI
        cmd.destination = MVIStorageDestination[source[2]]
        if cmd.destination == MVIStorageDestination.PC:
            cmd.immediate = get_immediate_value_label_aware(source[1], context)
        else:
            cmd.immediate = get_immediate_value_constant_aware(source[1], context)


        if len(source) == 4:
            cmd.condition = MVIConditionStatus[source[3]]
        else:
            cmd.condition = None

        return cmd

    def to_text(self) -> List[str]:
        result = f"MVI #{self.immediate},{self.destination.name}"
        if self.condition:
            result += f",{self.condition.name}"

        return [result]

    @staticmethod
    def from_binary(source: str) -> Command:
        assert len(source) == 32
        cmd = MVICommand()
        cmd.opcode = MVIOpcodes(cut(source, 30, 32))
        cmd.destination = MVIStorageDestination(cut(source, 26, 30))
        if cut(source, 25, 26) == "1":
            cmd.condition = MVIConditionStatus(cut(source, 19, 25))
            cmd.immediate = int(cut(source, 0, 19), 2)
        else:
            cmd.condition = None
            cmd.immediate = int(cut(source, 0, 25), 2)

        return cmd

    def to_binary(self) -> str:
        result = f"{self.opcode.value}{self.destination.value}"
        if self.condition:
            result += f"1{self.condition.value}"
            result += bin(self.immediate)[2:].zfill(19)
        else:
            result += "0" + bin(self.immediate)[2:].zfill(25)

        return result


class JumpOpcodes(OpCodes):
    JMP = "1101"


class JumpMode(Enum):
    Z               = "1100001"
    NZ              = "1000001"
    S               = "1100010"
    NS              = "1000010"
    C               = "1100100"
    NC              = "1000100"
    T0              = "1101000"
    NT0             = "1001000"
    ZS              = "1100011"
    NZS             = "1000011"


class JumpCommand(SpecialCommand):
    opcode: JumpOpcodes
    condition: JumpMode
    immediate: int

    @staticmethod
    def from_text(source: List[str], context: Optional[InstructionContext] = None) -> Command:
        cmd = JumpCommand()
        assert source[0] == "JMP"
        cmd.opcode = JumpOpcodes.JMP

        # If unconditional...
        if len(source) == 2:
            cmd.condition = None
            immediate = source[1]
        else:
            cmd.condition = JumpMode[source[1]]
            immediate = source[2]

        cmd.immediate = get_immediate_value_label_aware(immediate, context)
        return cmd

    def to_text(self) -> List[str]:
        result = self.opcode.name
        if self.condition:
            result += f" {self.condition.name},#{str(self.immediate)}"
        else:
            result += f" #{str(self.immediate)}"

        return [result]

    @staticmethod
    def from_binary(source: str) -> Command:
        assert len(source) == 32
        cmd = JumpCommand()
        cmd.opcode = JumpOpcodes(cut(source, 28, 32))

        status = cut(source, 19, 26)

        try:
            cmd.condition = JumpMode(status)
        except ValueError:
            # If a jump condition is not found, then it's an unconditional jump!
            cmd.condition = None

        cmd.immediate = int(cut(source, 0, 7), 2)
        return cmd

    def to_binary(self) -> str:
        result = self.opcode.value + "00"
        if self.condition:
            result += self.condition.value
        else:
            result += "0000000"  # Unconditional mode

        result += "".zfill(12)
        result += bin(self.immediate)[2:].zfill(7)
        return result


def generate_command_from_text(data: List[str], context: Optional[InstructionContext] = None) -> Command:
    print(f"generate_command data: {data}")
    if data[0] == 'NOP':
        return None
    elif data[0] == 'MOV':
        # Y Bus cmd?
        if data[2] in ['Y', 'A']:
            return YBusControlCommand.from_text(data, context)

        # X Bus cmd?
        elif data[2] in ['X', 'P']:
            return XBusControlCommand.from_text(data, context)

        # D1 Bus cmd!
        else:
            return D1BusControlCommand.from_text(data, context)

    elif data[0] == 'CLR':
        # We treat it specially because then only MOV ops are left for YBus ^^
        return YBusControlCommand.from_text(data, context)

    elif data[0] in AluOpcodes._member_names_:
        return AluControlCommand.from_text(data, context)
    elif data[0] in EndOpcodes._member_names_:
        return EndCommand.from_text(data, context)
    elif data[0] in LoopOpcodes._member_names_:
        return LoopCommand.from_text(data, context)
    elif data[0] in DMAOpcodes._member_names_:
        return DMACommand.from_text(data, context)
    elif data[0] in MVIOpcodes._member_names_:
        return MVICommand.from_text(data, context)
    elif data[0] in JumpOpcodes._member_names_:
        return JumpCommand.from_text(data, context)

    raise Exception(f"Command not supported. Data: {data}")
