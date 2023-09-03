# End Commands
import pytest

from despiste.commands import EndCommand, EndOpcodes, LoopCommand, LoopOpcodes, DMACommand


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
def test_end_loop_binary(bits, ctype, opcode, expected_bits):
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
def test_end_loop_text(text, ctype):
    cmd = ctype.from_text([text])
    assert cmd.opcode.name == text
    assert cmd.to_text() == [text]


@pytest.mark.parametrize(
    "expected_text,bits",
    [
        (
            "DMA D0,MC3,4",

            "1100"          # Opcode                    28-31
            "0000000000"    # padding                   18-27
            "000"           # Add mode                  15-17
            "0000"         # DMA mode                   11-14
            "011"            # Destination               8-10
            "00000100"      # Counter immediate value    0- 7
        ),
        (
            "DMAH D0,MC3,4",

            "1100"          # Opcode
            "0000000000"    # padding
            "00"            # Add mode (forced 0)
            "0"             # Add mode (valid only for A-bus
            "1000"          # DMA mode
            "011"           # Destination
            "00000"         # padding
            "100"           # Counter immediate value
        ),
        (
            "DMA MC1,D0,4",

            "1100"          # Opcode
            "0000000000"    # padding
            "000"           # Add mode
            "0010"         # DMA mode
            "001"            # Destination
            "00000100"      # Counter immediate value
        ),
        (
            "DMAH MC1,D0,4",

            "1100"  # Opcode
            "0000000000"  # padding
            "000"  # Add mode
            "1010"  # DMA mode
            "001"  # Destination
            "00000100"  # Counter immediate value
        ),
    ]
)
def test_dma_binary(expected_text, bits):
    assert len(bits) == 32
    cmd = DMACommand.from_binary(bits)
    assert cmd.to_binary() == bits
    assert cmd.to_text() == [expected_text]


@pytest.mark.parametrize(
    "text",
    [
        (["DMA", "D0", "MC3", 5]),
        (["DMAH", "D0", "MC3", 5]),
        (["DMA", "MC1", "D0", 5]),
    ]
)
def test_dma_text(text):
    cmd = DMACommand.from_text(text)
    assert cmd.to_text() == [f"{text[0]} {text[1]},{text[2]},{text[3]}"]
