import pytest

from despiste.commands import D1BusControlCommand, AluControlCommand, AluOpcodes, D1BusOpcodes, D1BusDataDestination, \
    D1BusDataSource, YBusControlCommand, YBusOpcodes, XYBusDataSource, XBusOpcodes, XBusControlCommand, EndCommand


# ALU


def test_alu_binary():
    bits = "0001"
    cmd = AluControlCommand.from_binary(bits)
    assert cmd.opcode == AluOpcodes.AND
    assert cmd.to_binary() == bits


def test_alu_text():
    text = ["AD2"]
    cmd = AluControlCommand.from_text(text)
    assert cmd.opcode == AluOpcodes.AD2
    assert cmd.to_text() == text


# D1

@pytest.mark.parametrize(
    "bits,opcode,source,immediate,destination",
    [
        # NOP
        ("00000000000000", D1BusOpcodes.NOP, None, None, None),
        # MOV #3 CT1
        ("01"+"1101"+"00000011", D1BusOpcodes.MOV_IMM_DST, None, 3, D1BusDataDestination.CT1),
        # MOV RAM2 RX
        ("11"+"0100"+"00000010", D1BusOpcodes.MOV_SRC_DST, D1BusDataSource.RAM2, None, D1BusDataDestination.RX),
    ]
)
def test_d1_binary(bits, opcode, source, immediate, destination):
    cmd = D1BusControlCommand.from_binary(bits)
    assert cmd.opcode == opcode
    assert cmd.source == source
    assert cmd.destination == destination
    assert cmd.immediate == immediate
    assert cmd.to_binary() == bits


@pytest.mark.parametrize(
    "opcode,source,expected_source",
    [
        (D1BusOpcodes.MOV_SRC_DST, "ALL", "ALL"),
        (D1BusOpcodes.MOV_IMM_DST, "45", 45),
        (D1BusOpcodes.MOV_IMM_DST, "#45", 45),
    ]
)
def test_d1_text(opcode, source, expected_source):
    text = ["MOV", source, "WA0"]
    cmd = D1BusControlCommand.from_text(text)
    assert cmd.opcode == opcode
    if cmd.opcode == D1BusOpcodes.MOV_SRC_DST:
        assert cmd.source.name == expected_source
        assert cmd.immediate is None
        assert cmd.to_text() == [f"{text[0]} {expected_source},{text[2]}"]
    else:
        assert cmd.source is None
        assert cmd.immediate == expected_source
        assert cmd.to_text() == [f"{text[0]} #{expected_source},{text[2]}"]
    assert cmd.destination == D1BusDataDestination.WA0


# Y Bus


@pytest.mark.parametrize(
    "bits,opcode,source",
    [
        ("100"+"110", YBusOpcodes.MOV_SRC_Y, XYBusDataSource.MC2),
        ("011"+"011", YBusOpcodes.MOV_SRC_A, XYBusDataSource.RAM2),
        ("010"+"000", YBusOpcodes.MOV_ALU_A, None),
        ("001"+"000", YBusOpcodes.CLR_A, None),
        ("000"+"000", YBusOpcodes.NOP, None),
        ("110"+"001", YBusOpcodes.MOV_SRC_Y_ALU_A, XYBusDataSource.RAM1)
    ]
)
def test_y_binary(bits, opcode, source):
    cmd = YBusControlCommand.from_binary(bits)
    assert cmd.opcode == opcode
    assert source == source
    assert cmd.to_binary() == bits


@pytest.mark.parametrize(
    "text,opcode,source",
    [
        (["MOV", "MC2", "Y"], YBusOpcodes.MOV_SRC_Y, XYBusDataSource.MC2),
        (["MOV", "ALU", "A"], YBusOpcodes.MOV_ALU_A, None),
        (["CLR", "A"], YBusOpcodes.CLR_A, None),
        (["NOP"], YBusOpcodes.NOP, None),
    ]
)
def test_y_text(text, opcode, source):
    cmd = YBusControlCommand.from_text(text)
    assert cmd.opcode == opcode
    assert source == source
    if text[0] == 'NOP':
        assert cmd.to_text() == ["NOP"]
    elif text[0] == "CLR":
        assert cmd.to_text() == ["CLR A"]
    else:
        assert cmd.to_text() == [f"{text[0]} {text[1]},{text[2]}"]


def test_y_special_to_text():
    cmd = YBusControlCommand()
    cmd.opcode = YBusOpcodes.MOV_SRC_Y_ALU_A
    cmd.source = XYBusDataSource.RAM1
    output = cmd.to_text()
    assert len(output) == 2
    assert "MOV ALU,A" in output
    assert "MOV RAM1,Y" in output


# X Bus


@pytest.mark.parametrize(
    "bits,opcode,source",
    [
        ("011"+"110", XBusOpcodes.MOV_SRC_P, XYBusDataSource.MC2),
        ("100"+"011", XBusOpcodes.MOV_SRC_X, XYBusDataSource.RAM2),
        ("010"+"000", XBusOpcodes.MOV_MUL_P, None),
        ("000"+"000", XBusOpcodes.NOP, None),
        ("110"+"001", XBusOpcodes.MOV_SRC_X_MUL_P, XYBusDataSource.RAM1)
    ]
)
def test_x_binary(bits, opcode, source):
    cmd = XBusControlCommand.from_binary(bits)
    assert cmd.opcode == opcode
    assert source == source
    assert cmd.to_binary() == bits


@pytest.mark.parametrize(
    "text,opcode,source",
    [
        (["MOV", "MC2", "X"], XBusOpcodes.MOV_SRC_X, XYBusDataSource.MC2),
        (["MOV", "MUL", "P"], XBusOpcodes.MOV_MUL_P, None),
        (["NOP"], XBusOpcodes.NOP, None),
    ]
)
def test_x_text(text, opcode, source):
    cmd = XBusControlCommand.from_text(text)
    assert cmd.opcode == opcode
    assert source == source
    if text[0] == 'NOP':
        assert cmd.to_text() == ["NOP"]
    else:
        assert cmd.to_text() == [f"{text[0]} {text[1]},{text[2]}"]


def test_x_special_to_text():
    cmd = XBusControlCommand()
    cmd.opcode = XBusOpcodes.MOV_SRC_X_MUL_P
    cmd.source = XYBusDataSource.RAM1
    output = cmd.to_text()
    assert len(output) == 2
    assert "MOV MUL,P" in output
    assert "MOV RAM1,X" in output
