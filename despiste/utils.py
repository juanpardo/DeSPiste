from pathlib import Path


def cut(source: str, start: int, end: int) -> str:
    """
    Used to help parsing binary strings.
    Given a string meant to represent a list of bits, returns a substring.
    start and end will be interpreted reversed
    :param source: A string comprised of 1's and 0's
    :param start: Where to start cutting
    :param end: Where to end cutting (exclusive)
    :return: A string that comprises the numbers between start and end.
    """
    size = len(source)
    return source[size-end: size-start]


def print_help_message():
    print("\nUsage:")
    print("\tdespite compile input.dsp [output.bin]")
    print("\tdespite decompile input.bin [output.dsp]")
    print("\nIf a third parameter is specified, it will be used as the name for the "
          "output file. Otherwise the standard output will be used.")


def read_file_content(input_file) -> bytes:
    try:
        finput = Path(input_file)
        return finput.read_bytes()
    except FileNotFoundError:
        print(f"Error: Could not find the input file {input_file}")
        print_help_message()
        raise SystemExit(2)


def write_file_content(output_file, content):
    newFile = open(output_file, "wb")
    newFile.write(bytearray(content))
