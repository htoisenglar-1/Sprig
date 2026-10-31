"""The deliberately small standard library. No host-code execution."""

import re

from .errors import RuntimeFault
from .values import BuiltinFunction, checked_number, format_value, is_number, type_name


def fail(message, token):
    raise RuntimeFault(message, token.line, token.column)


def integer(value, token):
    if type(value) is not int:
        fail("Expected an integer (booleans and decimal numbers are not indices).", token)
    return value


def sequence(value, token):
    if not isinstance(value, (str, list)):
        fail("Expected a string or list.", token)
    return value


def mutable_list(value, token):
    if not isinstance(value, list):
        fail("Expected a list.", token)
    return value


def sprig_print(interpreter, arguments, token):
    print(*(format_value(value) for value in arguments), file=interpreter.stdout)


def sprig_input(interpreter, arguments, token):
    if arguments:
        interpreter.stdout.write(format_value(arguments[0]))
        interpreter.stdout.flush()
    line = interpreter.stdin.readline()
    if line == "":
        fail("input() reached end of input.", token)
    return line.rstrip('\r\n')


def sprig_len(interpreter, arguments, token):
    return len(sequence(arguments[0], token))


def sprig_append(interpreter, arguments, token):
    mutable_list(arguments[0], token).append(arguments[1])


def sprig_pop(interpreter, arguments, token):
    items = mutable_list(arguments[0], token)
    if not items:
        fail("Cannot pop from an empty list.", token)
    return items.pop()


def sprig_range(interpreter, arguments, token):
    numbers = [integer(value, token) for value in arguments]
    if len(numbers) == 3 and numbers[2] == 0:
        fail("range() step cannot be zero.", token)
    result = range(*numbers)
    try:
        size = len(result)
    except OverflowError:
        fail("range() is limited to 100000 elements.", token)
    if size > 100000:
        fail("range() is limited to 100000 elements.", token)
    return list(result)


def sprig_str(interpreter, arguments, token):
    return format_value(arguments[0])


def sprig_number(interpreter, arguments, token):
    value = arguments[0]
    if is_number(value):
        return checked_number(value, token)
    if not isinstance(value, str):
        fail("number() expects a numeric string or number.", token)
    text = value.strip()
    # Accept the language's decimal forms with an optional sign; no Python syntax leaks.
    if not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", text):
        fail("number() could not convert this string to a number.", token)
    try:
        result = float(text) if '.' in text else int(text)
    except (ValueError, OverflowError):
        fail("Number is too large to convert.", token)
    return checked_number(result, token)


def sprig_type(interpreter, arguments, token):
    return type_name(arguments[0])


def install_builtins(environment):
    definitions = [
        ("print", 0, None, sprig_print),
        ("input", 0, 1, sprig_input),
        ("len", 1, 1, sprig_len),
        ("append", 2, 2, sprig_append),
        ("pop", 1, 1, sprig_pop),
        ("range", 1, 3, sprig_range),
        ("str", 1, 1, sprig_str),
        ("number", 1, 1, sprig_number),
        ("type", 1, 1, sprig_type),
    ]
    # Only setup writes directly; user assignment goes through Environment.assign.
    for name, minimum, maximum, implementation in definitions:
        environment.values[name] = BuiltinFunction(name, minimum, maximum, implementation)
