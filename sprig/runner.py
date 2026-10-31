"""Connect source text -> tokens -> AST -> execution."""

from .errors import RuntimeFault, SprigError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser


def parse_source(source):
    return Parser(Lexer(source).scan_tokens()).parse()


def run_source(source, interpreter=None, filename="<stdin>"):
    interpreter = Interpreter() if interpreter is None else interpreter
    interpreter.source, interpreter.filename = source, filename
    interpreter.steps = 0
    try:
        statements = parse_source(source)
        interpreter.execute(statements)
    except SprigError as error:
        if not hasattr(error, "source"):
            error.source, error.filename = source, filename
        raise
    except (RecursionError, OverflowError, ValueError) as error:
        token = interpreter.current_token
        fault = RuntimeFault(interpreter.host_error_message(error), token.line if token else 1, token.column if token else 1)
        fault.source, fault.filename = source, filename
        raise fault from None
    return interpreter
