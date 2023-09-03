# End Commands
import pytest

from despiste.commands import EndCommand, EndOpcodes, LoopCommand, LoopOpcodes


# END and Loop commands


@pytest.mark.parametrize(
    "bits,ctype,opcode,expected_bits",
    [
        ("11110", EndCommand, EndOpcodes.END, "11110000000000000000000000000000"),
        ("11111", EndCommand, EndOpcodes.ENDI, "11111000000000000000000000000000"),
        ("11100", LoopCommand, LoopOpcodes.BTM, "11100000000000000000000000000000"),
        ("11101", LoopCommand, LoopOpcodes.LPS, "11101000000000000000000000000000"),
    ]
)
def test_end_binary(bits, ctype, opcode, expected_bits):
    cmd = ctype.from_binary(bits)
    assert cmd.opcode == opcode
    assert cmd.to_binary() == expected_bits


@pytest.mark.parametrize(
    "text, ctype",
    [
        ("END", EndCommand),
        ("ENDI", EndCommand),
        ("BTM", LoopCommand),
        ("LPS", LoopCommand),
    ]
)
def test_end_text(text, ctype):
    cmd = ctype.from_text([text])
    assert cmd.opcode.name == text
    assert cmd.to_text() == [text]
