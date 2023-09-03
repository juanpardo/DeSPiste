from pathlib import Path


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
