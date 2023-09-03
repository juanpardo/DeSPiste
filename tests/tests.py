from despiste.program import Program


def test1():
    p = Program()
    instruction_bytes = bin(0x00001C00)[2:].rjust(32, '0')
    p.from_binary(instruction_bytes)

    assert len(p.instructions) == 1

    print(p.instructions[0])


def test2():
    binary_code = [
        0x00001C00,
        0x00021D00,
        0x02494000,
        0x01000000,
        0x18003209,
        0x00000000,
        0x00000000,
        0x00000000,
        0x00000000,
        0x00000000,
        0x00000000,
        0x00000000,
        0xF8000000
    ]

    p = Program()
    instruction_bytes = ""
    for line in binary_code:
        instruction_bytes = bin(line)[2:].rjust(32, '0') + instruction_bytes
    p.from_binary(instruction_bytes)

    assert len(p.instructions) == 13

    print(str(p))
