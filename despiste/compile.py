from enum import Enum
from typing import List

from despiste.program import Program, Instruction
from despiste.commands import Command, AluOpcodes, AluControlCommand, YBusControlCommand, \
    YBusOpcodes, D1BusControlCommand, D1BusOpcodes, D1BusDataSource, D1BusDataDestination, XYBusDataSource, \
    XBusControlCommand, XBusOpcodes
from despiste.utils import read_file_content, write_file_content

command_args = {
    'NOP': 0,
    # ALU
    'AND': 0,
    'OR': 0,
    'XOR': 0,
    'ADD': 0,
    'SUB': 0,
    'AD2': 0,
    'SR': 0,
    'RR': 0,
    'SL': 0,
    'RL': 0,
    'RL8': 0,

    # OTHER
    'MOV': 2,
    'CLR': 1,
    'DMA': 3,
    'MVI': 2,
    'JMP': [1, 2],
    # LOOPS
    'BTM': 0,
    'LPS': 0,
    # ENDS
    'END': 0,
    'ENDI': 0,
}


def generate_command_from_text(data: List[str]) -> Command:
    print(f"generate_command data: {data}")
    if data[0] == 'NOP':
        return None
    elif data[0] == 'MOV':
        # Y Bus cmd?
        if data[2] in ['Y', 'A']:
            return YBusControlCommand.from_text(data)

        # X Bus cmd?
        elif data[2] in ['X', 'P']:
            return XBusControlCommand.from_text(data)

        # D1 Bus cmd!
        else:
            return D1BusControlCommand.from_text(data)

    elif data[0] == 'CLR':
        # We treat it specially because then only MOV ops are left for YBus ^^
        return YBusControlCommand.from_text(data)

    else:
        try:
            op = AluOpcodes[data[0]]
            return AluControlCommand.from_text(data)
        except KeyError:
            # Not an AluControlCommand
            raise Exception(f"Command not supported. Data: {data}")


def add_command_to_instruction(cmd: Command, instruction: Instruction):
    if type(cmd) == D1BusControlCommand:
        instruction.d1BusControlCommand = cmd

    elif type(cmd) == AluControlCommand:
        instruction.aluControlCommand = cmd

    elif type(cmd) == XBusControlCommand:
        if instruction.xBusControlCommand is None:
            instruction.xBusControlCommand = cmd
        elif instruction.xBusControlCommand.opcode == XBusOpcodes.MOV_SRC_X and cmd.opcode == XBusOpcodes.MOV_MUL_P:
            instruction.xBusControlCommand.opcode = XBusOpcodes.MOV_SRC_X_MUL_P
        elif instruction.xBusControlCommand.opcode == XBusOpcodes.MOV_MUL_P and cmd.opcode == XBusOpcodes.MOV_SRC_X:
            instruction.xBusControlCommand.source = cmd.source
            instruction.xBusControlCommand.opcode = XBusOpcodes.MOV_SRC_X_MUL_P

    elif type(cmd) == YBusControlCommand:
        if instruction.yBusControlCommand is None:
            instruction.yBusControlCommand = cmd
        elif instruction.yBusControlCommand.opcode == YBusOpcodes.MOV_SRC_Y and cmd.opcode == YBusOpcodes.MOV_ALU_A:
            instruction.yBusControlCommand.opcode = YBusOpcodes.MOV_SRC_Y_ALU_A
        elif instruction.yBusControlCommand.opcode == YBusOpcodes.MOV_ALU_A and cmd.opcode == YBusOpcodes.MOV_SRC_Y:
            instruction.yBusControlCommand.source = cmd.source
            instruction.yBusControlCommand.opcode = YBusOpcodes.MOV_SRC_Y_ALU_A


def generate_instruction_from_line(line: str) -> Instruction:

    # Avoid the pesky commas
    line = line.replace(',', ' ').upper()
    print(f"Line to be parsed: {line}")

    elements: List[str] = line.split()

    instruction = Instruction()
    current_command = []

    for element in elements:
        if element.startswith(';'):
            break

        if len(current_command) == 0:
            current_command.append(element)
        elif command_args[current_command[0]] + 1 <= len(current_command):
            cmd = generate_command_from_text(current_command)
            add_command_to_instruction(cmd, instruction)
            current_command = [element]
        else:
            current_command.append(element)

    if len(current_command) > 0:
        cmd = generate_command_from_text(current_command)
        add_command_to_instruction(cmd, instruction)

    if not instruction.specialCommand:

        if not instruction.yBusControlCommand:
            instruction.yBusControlCommand = YBusControlCommand()
            instruction.yBusControlCommand.opcode = YBusOpcodes.NOP

        if not instruction.xBusControlCommand:
            instruction.xBusControlCommand = XBusControlCommand()
            instruction.xBusControlCommand.opcode = XBusOpcodes.NOP

        if not instruction.aluControlCommand:
            instruction.aluControlCommand = AluControlCommand()
            instruction.aluControlCommand.opcode = AluOpcodes.NOP

        if not instruction.d1BusControlCommand:
            instruction.d1BusControlCommand = D1BusControlCommand()
            instruction.d1BusControlCommand.opcode = D1BusOpcodes.NOP
    print(f"Instruction parsed: {instruction.to_text()}")
    return instruction


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
