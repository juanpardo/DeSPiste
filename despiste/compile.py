from despiste.program import Program
from despiste.utils import read_file_content, write_file_content


def print_as_hex_numbers(bin_str: str):
    numbers = [int(bin_str[i:i + 32], 2) for i in range(0, len(bin_str), 32)]
    for n in numbers:
        print(f"{n:#0{10}x}")


def write_to_file(output_file: str, bin_str: str):
    numbers = [int(bin_str[i:i + 32], 2) for i in range(0, len(bin_str), 32)]
    foo = bytearray()
    for n in numbers:
        b = n.to_bytes(4)
        foo += bytearray(b)
    write_file_content(output_file, foo)


def do_compile(input_file: str, output_file: str):
    input_bytes = read_file_content(input_file)
    input_lines = input_bytes.decode("utf-8").splitlines()

    p = Program.from_text(input_lines)

    bin_str = p.to_binary()
    print_as_hex_numbers(bin_str)
    if output_file:
        write_to_file(output_file, bin_str)

    raise SystemExit(0)
