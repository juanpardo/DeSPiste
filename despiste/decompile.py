from despiste.program import Program
from despiste.utils import read_file_content, write_file_content


def program_to_text(p: Program) -> str:
    result = ""
    if len(p.context.constants):
        result += "; CONSTANTS\n"
    for k, v in p.context.constants:
        result += f" {k}={v}\n"

    result += "\n"

    header = [";ALU", "X-bus", "Y-bus", "D1-bus"]
    header = [x.ljust(12) for x in header]
    print("".join(header))

    for idx, inst in enumerate(p.instructions):
        for label, pc in p.context.labels:
            if pc == idx:
                result += f"{label}:\n"

        for cmd in inst.to_text():
            result += cmd.ljust(12)
        result += "\n"

    return result


def do_decompile(input_file: str, output_file: str):
    input_bytes = read_file_content(input_file)

    check_input_length = len(input_bytes) % 4
    if check_input_length != 0:
        print(f"Input binary file must have a size multiple of 4 (32 bits per instruction), but it is {len(input_bytes)} instead.")
        raise SystemExit(3)

    bit_string = ""
    foo = ""
    for idx, b in enumerate(input_bytes):
        if idx % 4 == 0:
            bit_string = foo + bit_string
            foo = ""
        foo += bin(b)[2:].rjust(8, '0')

    if foo != "":
        bit_string = foo + bit_string

    print(f"Decompiling {len(input_bytes) // 4} instructions...")
    p = Program.from_binary(bit_string)

    print("Decompiled!\n")

    output = program_to_text(p)

    print(output)

    if output_file:
        write_file_content(output_file, output.encode("utf-8"))

    raise SystemExit(0)
