from despiste.program import Program


def test_program_from_binary_to_text():
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

    instruction_bytes = ""
    for line in binary_code:
        instruction_bytes = bin(line)[2:].rjust(32, '0') + instruction_bytes
    p = Program.from_binary(instruction_bytes)

    assert len(p.instructions) == 13

