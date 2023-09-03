from despiste.program import Program


def test1():
    p = Program()
    instruction_bytes = 0x00001C00.to_bytes(32, 'big')
    p.from_binary(instruction_bytes)

    assert len(p.instructions) == 1
