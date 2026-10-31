"""Sprig value rules, deliberately independent of Python's coercion rules."""

import math

from .errors import RuntimeFault


def is_number(value):
    # In Python bool subclasses int; in Sprig these are separate value kinds.
    return type(value) in (int, float)


def type_name(value):
    if value is None:
        return "nil"
    if type(value) is bool:
        return "boolean"
    if is_number(value):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, (BuiltinFunction, UserFunction)):
        return "function"
    raise TypeError("Unknown internal Sprig value.")


def checked_number(value, token):
    if not is_number(value) or (isinstance(value, float) and not math.isfinite(value)):
        raise RuntimeFault("Expected a finite number.", token.line, token.column)
    return value


def require_boolean(value, token):
    if type(value) is not bool:
        raise RuntimeFault(f"Expected a boolean, got {type_name(value)}.", token.line, token.column)
    return value


def equal_values(left, right, seen=None):
    if is_number(left) and is_number(right):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        if left is right:
            return True
        if len(left) != len(right):
            return False
        seen = set() if seen is None else seen
        pair = (id(left), id(right))
        if pair in seen:
            return True
        seen.add(pair)
        return all(equal_values(a, b, seen) for a, b in zip(left, right))
    if isinstance(left, (BuiltinFunction, UserFunction)):
        return left is right
    return left == right


def format_value(value, *, nested=False, seen=None):
    if value is None:
        return "nil"
    if type(value) is bool:
        return "true" if value else "false"
    if isinstance(value, str):
        if not nested:
            return value
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + escaped + '"'
    if isinstance(value, list):
        seen = set() if seen is None else seen
        if id(value) in seen:
            return "[...]"
        seen.add(id(value))
        try:
            return "[" + ", ".join(format_value(item, nested=True, seen=seen) for item in value) + "]"
        finally:
            seen.remove(id(value))
    if isinstance(value, (BuiltinFunction, UserFunction)):
        return f"<fn {value.name}>"
    return str(value)


class BuiltinFunction:
    def __init__(self, name, minimum, maximum, implementation):
        self.name = name
        self.minimum = minimum
        self.maximum = maximum
        self.implementation = implementation

    def call(self, interpreter, arguments, token):
        if len(arguments) < self.minimum or (self.maximum is not None and len(arguments) > self.maximum):
            if self.maximum == self.minimum:
                expected = str(self.minimum)
            elif self.maximum is None:
                expected = f"at least {self.minimum}"
            else:
                expected = f"{self.minimum} to {self.maximum}"
            raise RuntimeFault(f"{self.name} expects {expected} arguments, got {len(arguments)}.", token.line, token.column)
        return self.implementation(interpreter, arguments, token)


class UserFunction:
    def __init__(self, declaration, closure, source, filename):
        self.declaration = declaration
        self.closure = closure
        self.source = source
        self.filename = filename
        self.name = declaration.name.lexeme

    def call(self, interpreter, arguments, token):
        # Import here avoids a dependency cycle between values and interpreter.
        from .environment import Environment
        from .interpreter import ReturnSignal

        parameters = self.declaration.parameters
        if len(arguments) != len(parameters):
            raise RuntimeFault(f"{self.name} expects {len(parameters)} arguments, got {len(arguments)}.", token.line, token.column)
        local = Environment(self.closure)
        for parameter, value in zip(parameters, arguments):
            local.define(parameter.lexeme, value, parameter)
        old_source, old_filename = interpreter.source, interpreter.filename
        interpreter.source, interpreter.filename = self.source, self.filename
        try:
            interpreter.execute_block(self.declaration.body, local)
        except ReturnSignal as signal:
            return signal.value
        except RuntimeFault as error:
            if not hasattr(error, "source"):
                error.source, error.filename = self.source, self.filename
            raise
        except (RecursionError, OverflowError, ValueError) as error:
            # Convert while the definition's source is still active. Otherwise
            # a later REPL call would incorrectly point at the caller's text.
            position = interpreter.current_token or token
            interpreter.fail(interpreter.host_error_message(error), position)
        finally:
            interpreter.source, interpreter.filename = old_source, old_filename
        return None
