"""A persistent prompt; EOF syntax errors tell us to collect another line."""

import sys

from . import __version__
from .errors import IncompleteInput, SprigError
from .interpreter import Interpreter
from .runner import parse_source, run_source


def report_error(error, source, filename, stream):
    stream.write(error.render(getattr(error, "source", source), getattr(error, "filename", filename)) + "\n")


def repl(*, stdin=None, stdout=None, stderr=None, max_steps=None):
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    interpreter = Interpreter(stdin=stdin, stdout=stdout, max_steps=max_steps)
    stdout.write(f"Sprig {__version__} — :help for commands, :quit to exit.\n")
    buffer = ""
    submission = 1
    while True:
        try:
            stdout.write("...> " if buffer else "sprig> ")
            stdout.flush()
            line = stdin.readline()
            if line == "":
                if buffer:
                    try:
                        parse_source(buffer)
                    except SprigError as error:
                        report_error(error, buffer, f"<repl:{submission}>", stderr)
                    except RecursionError:
                        stderr.write("SyntaxError: nesting limit exceeded.\n")
                stdout.write("\n")
                return 0
            command = line.strip()
            if not buffer and command.startswith(":"):
                if command == ":quit":
                    return 0
                if command == ":reset":
                    interpreter = Interpreter(stdin=stdin, stdout=stdout, max_steps=max_steps)
                    stdout.write("Environment reset.\n")
                elif command == ":help":
                    stdout.write(":help  Show commands\n:reset Clear variables\n:quit  Exit\nUse print(value) to display results. Finish each block with end.\n")
                else:
                    stderr.write("Unknown command. Type :help.\n")
                continue
            buffer += line
            try:
                parse_source(buffer)
            except IncompleteInput:
                continue
            except SprigError as error:
                report_error(error, buffer, f"<repl:{submission}>", stderr)
            except RecursionError:
                stderr.write("SyntaxError: nesting limit exceeded.\n")
            else:
                try:
                    run_source(buffer, interpreter, f"<repl:{submission}>")
                except SprigError as error:
                    report_error(error, buffer, f"<repl:{submission}>", stderr)
            buffer = ""
            submission += 1
        except KeyboardInterrupt:
            stdout.write("\nInput cancelled.\n")
            buffer = ""
            submission += 1


if __name__ == "__main__":
    raise SystemExit(repl())
