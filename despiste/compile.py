from enum import Enum
from typing import List

from despiste.program import Program, Instruction, Command, AluOpcodes, AluControlCommand, YBusControlCommand, \
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


def generate_command(data: List[str]) -> Command:
    print(f"generate_command data: {data}")
    if data[0] == 'NOP':
        return None
    elif data[0] == 'MOV':
        # Y Bus cmd?
        if data[2] in ['Y', 'A']:
            cmd = YBusControlCommand()
            if data[2] == 'Y':
                cmd.opcode = YBusOpcodes.MOV_SRC_Y
                cmd.source = XYBusDataSource[data[1]]
            else:
                try:
                    cmd.source = XYBusDataSource[data[1]]
                    cmd.opcode = YBusOpcodes.MOV_SRC_A
                except KeyError:
                    cmd.opcode = YBusOpcodes.MOV_ALU_A
            return cmd

        # X Bus cmd?
        elif data[2] in ['X', 'P']:
            cmd = XBusControlCommand()
            if data[2] == 'X':
                cmd.opcode = XBusOpcodes.MOV_SRC_X
                cmd.source = XYBusDataSource[data[1]]
            else:
                try:
                    cmd.source = XYBusDataSource[data[1]]
                    cmd.opcode = XBusOpcodes.MOV_SRC_P
                except KeyError:
                    cmd.opcode = XBusOpcodes.MOV_MUL_P
            return cmd

        # D1 Bus cmd!
        else:
            cmd = D1BusControlCommand()
            cmd.destination = D1BusDataDestination[data[2]]
            # Using SRC?
            try:
                cmd.source = D1BusDataSource[data[1]]
                cmd.opcode = D1BusOpcodes.MOV_IMM_DST
            except KeyError:
                if data[1].startswith('#'):
                    data[1] = data[1][1:]
                cmd.immediate = int(data[1])
                cmd.opcode = D1BusOpcodes.MOV_IMM_DST

    elif data[0] == 'CLR':
        # We treat it specially because then only MOV ops are left for YBus ^^
        cmd = YBusControlCommand()
        cmd.opcode = YBusOpcodes.CLR_A
        return cmd

    else:
        try:
            op = AluOpcodes[data[0]]
            cmd = AluControlCommand()
            cmd.opcode = op
            return cmd
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


class FileParserState(Enum):
    HEADER = 0
    BODY = 1


file_parser_state = FileParserState.HEADER


def generate_instruction_from_line(line: str) -> Instruction:
    global file_parser_state

    # Avoid the pesky commas
    line = line.replace(',', ' ').upper()
    print(f"Line to be parsed: {line}")

    elements: List[str] = line.split()

    instruction = Instruction()
    current_command = []

    for element in elements:
        if element.startswith(';'):
            break

        if file_parser_state == FileParserState.HEADER and element == 'START:':
            file_parser_state = FileParserState.BODY
            return

        elif file_parser_state == FileParserState.BODY:
            if len(current_command) == 0:
                current_command.append(element)
            elif command_args[current_command[0]] + 1 <= len(current_command):
                cmd = generate_command(current_command)
                add_command_to_instruction(cmd, instruction)
                current_command = [element]
            else:
                current_command.append(element)

    if len(current_command) > 0:
        cmd = generate_command(current_command)
        add_command_to_instruction(cmd, instruction)

    if not instruction.yBusControlCommand and not instruction.xBusControlCommand and not instruction.d1BusControlCommand and not instruction.aluControlCommand:
        return None

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

    return instruction


def do_compile(input_file: str, output_file: str):
    input_bytes = read_file_content(input_file)
    input_lines = input_bytes.decode("utf-8").splitlines()

    p = Program()

    for line in input_lines:
        instruction = generate_instruction_from_line(line)
        if instruction:
            p.instructions.append(instruction)

    if output_file is None:
        print(p.to_binary())
    else:
        write_file_content(output_file, p.to_binary())

    raise SystemExit(0)
