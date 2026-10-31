"""Language diagnostics, separate from Python's implementation exceptions."""


class SprigError(Exception):
    kind = "Error"

    def __init__(self, message: str, line: int = 1, column: int = 1):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def render(self, source: str, filename: str = "<stdin>") -> str:
        # split on newline rather than splitlines so a final empty line exists.
        lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        line = lines[self.line - 1] if 1 <= self.line <= len(lines) else ""
        prefix = line[:max(0, self.column - 1)].expandtabs(4)
        return (
            f"{filename}:{self.line}:{self.column}: {self.kind}: {self.message}\n"
            f"    {line.expandtabs(4)}\n"
            f"    {' ' * len(prefix)}^"
        )


class LexError(SprigError):
    kind = "LexError"


class ParseError(SprigError):
    kind = "SyntaxError"


class IncompleteInput(ParseError):
    """The parser reached EOF while waiting for more source."""


class RuntimeFault(SprigError):
    kind = "RuntimeError"
