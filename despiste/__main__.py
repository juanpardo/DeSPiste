import sys

from despiste.compile import do_compile
from despiste.decompile import do_decompile
from despiste.utils import print_help_message


def main():
    print("\n *** DeSPiste. A cross-platform Sega Saturn SCU DSP compiler and decompiler ***\n")
    args_count = len(sys.argv)
    if args_count not in [3, 4]:
        print(f"Error: Two or three arguments are expected, got {args_count - 1} instead.")
        print_help_message()
        raise SystemExit(1)
    command = sys.argv[1]
    input_file = sys.argv[2]
    output_file = None

    if args_count == 4:
        output_file = sys.argv[3]

    if command == 'compile':
        do_compile(input_file, output_file)
    elif command == 'decompile':
        do_decompile(input_file, output_file)
    else:
        print(f"Error: First argument must be either 'compile' or 'decompile', got {command} instead.")
        print_help_message()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
