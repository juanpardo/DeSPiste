import pytest

from despiste.commands import AluControlCommand, XBusControlCommand, YBusControlCommand, D1BusControlCommand, MVICommand
from despiste.program import Instruction


@pytest.mark.parametrize(
    "cmds,result",
    [
        ([], ["NOP", "NOP", "NOP", "NOP"]),
        ([AluControlCommand.from_text(["AD2"])], ["AD2", "NOP", "NOP", "NOP"]),
        (
            [
                AluControlCommand.from_text(["AD2"]),
                XBusControlCommand.from_text(["MOV", "MUL", "P"]),
                YBusControlCommand.from_text(["CLR", "A"]),
                D1BusControlCommand.from_text(["MOV", "#27", "MC2"]),
            ], ["AD2", "MOV MUL,P", "CLR A", "MOV #27,MC2"]),
        (
            [
                AluControlCommand.from_text(["SUB"]),
                XBusControlCommand.from_text(["MOV", "RAM1", "X"]),
                XBusControlCommand.from_text(["MOV", "MUL", "P"]),
                YBusControlCommand.from_text(["MOV", "RAM0", "Y"]),
                YBusControlCommand.from_text(["MOV", "ALU", "A"]),
                D1BusControlCommand.from_text(["MOV", "#27", "MC2"]),
            ], ["SUB", "MOV RAM1,X", "MOV MUL,P", "MOV RAM0,Y", "MOV ALU,A", "MOV #27,MC2"]
        ),
    ]
)
def test_instruction_from_commands_to_text(cmds, result):
    instruction = Instruction.from_commands(cmds)
    assert instruction.to_text() == result


def test_instruction_binary():
    # 00 + (ALU) AND + (X) MOV MC2,P + (Y) MOV ALU,A + (D1) MOV #3 CT1
    bits = "00" + "0001" + "011110" + "010000" + "01110100000011"

    instruction = Instruction.from_binary(bits)
    assert instruction.to_binary() == bits


def test_instruction_special_command_text():
    cmds = [MVICommand.from_text(["MVI", "128", "WA0", "NZ"])]

    instruction = Instruction.from_commands(cmds)
    assert instruction.xBusControlCommand is None
    assert instruction.yBusControlCommand is None
    assert instruction.aluControlCommand is None
    assert instruction.d1BusControlCommand is None
    assert instruction.specialCommand == cmds[0]
    assert instruction.to_text() == ["MVI #128,WA0,NZ"]


def test_instruction_special_command_binary():
    bits = (
        "1100"  # Opcode
        "0000000000"  # padding
        "000"  # Add mode
        "1010"  # DMA mode
        "001"  # Destination
        "00000100"  # Counter immediate value
    )

    instruction = Instruction.from_binary(bits)
    assert instruction.specialCommand
    assert instruction.to_binary() == bits
    assert instruction.to_text() == ["DMAH MC1,D0,4"]
