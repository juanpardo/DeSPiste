from despiste.program import Program
from despiste.utils import read_file_content, write_file_content


def do_decompile(input_file: str, output_file: str):
    input_bytes = read_file_content(input_file)

    check_input_length = len(input_bytes) % 32
    if check_input_length != 0:
        print(f"Input binary file must have a size multiple of 32, but it is {len(input_bytes)} instead.")
        raise SystemExit(3)

    bit_string = ""
    for b in input_bytes:
        bit_string += bin(b)[2:].rjust(8, '0')

    print(f"Decompiling {len(input_bytes) // 32} instructions...")
    p = Program()
    p.from_binary(bit_string)

    print("Decompiled!\n")

    if output_file is None:
        print(str(p))
    else:
        write_file_content(output_file, str(p))

    raise SystemExit(0)
