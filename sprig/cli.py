"""File runner and inspection commands, with readable language errors."""

import argparse
from pathlib import Path
import sys

from . import __version__
from .errors import RuntimeFault, SprigError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .repl import repl, report_error
from .runner import run_source


def positive_integer(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer") from None
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sprig", description="Run Sprig source files or start the interactive prompt.")
    parser.add_argument("--version", action="version", version=f"Sprig {__version__}")
    inspection = parser.add_mutually_exclusive_group()
    inspection.add_argument("--tokens", action="store_true", help="display tokens without running the program")
    inspection.add_argument("--ast", action="store_true", help="display the AST without running the program")
    parser.add_argument("--max-steps", type=positive_integer, help="stop after this many evaluation/statement steps")
    parser.add_argument("file", nargs="?", help="a UTF-8 .sprig source file")
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="strings made available in the program's args list")
    options = parser.parse_args(argv)
    if options.file is None:
        if options.tokens or options.ast:
            parser.error("--tokens and --ast require a source file")
        try:
            return repl(max_steps=options.max_steps)
        except (OSError, UnicodeError) as error:
            sys.stderr.write(f"IOError: {error}\n")
            return 1
    path = Path(options.file)
    if path.suffix != ".sprig":
        sys.stderr.write("FileError: source files must use the .sprig extension.\n")
        return 1
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        sys.stderr.write(f"FileError: cannot read '{path}': {error}\n")
        return 1
    try:
        if options.tokens:
            for token in Lexer(source).scan_tokens():
                print(f"{token.line}:{token.column} {token.kind.name} {token.lexeme!r}")
        elif options.ast:
            for statement in Parser(Lexer(source).scan_tokens()).parse():
                try:
                    print(statement)
                except RecursionError:
                    raise RuntimeFault("AST inspection nesting limit exceeded.", statement.token.line, statement.token.column) from None
        else:
            interpreter = Interpreter(args=options.arguments, max_steps=options.max_steps)
            run_source(source, interpreter, str(path))
    except SprigError as error:
        report_error(error, source, str(path), sys.stderr)
        return 1
    except (RecursionError, OverflowError, ValueError) as error:
        sys.stderr.write(f"{path}: RuntimeError: {Interpreter.host_error_message(error)}\n")
        return 1
    except (OSError, UnicodeError) as error:
        sys.stderr.write(f"IOError: {error}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nExecution interrupted.\n")
        return 130
    return 0
