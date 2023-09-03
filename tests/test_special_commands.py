# End Commands
import pytest

from despiste.commands import EndCommand, EndOpcodes


@pytest.mark.parametrize(
    "bits,opcode,expected_bits",
    [
        ("11110", EndOpcodes.END, "11110000000000000000000000000000"),
        ("11111", EndOpcodes.ENDI, "11111000000000000000000000000000"),
    ]
)
def test_end_binary(bits, opcode, expected_bits):
    cmd = EndCommand.from_binary(bits)
    assert cmd.opcode == opcode
    assert cmd.to_binary() == expected_bits


@pytest.mark.parametrize(
    "text", ["END", "ENDI"]
)
def test_end_text(text):
    cmd = EndCommand.from_text([text])
    assert cmd.opcode.name == text
    assert cmd.to_text() == [text]
