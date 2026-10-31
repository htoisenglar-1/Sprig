"""A handwritten scanner: source characters in, positioned tokens out."""

import math

from .errors import LexError
from .tokens import KEYWORDS, Token, TokenType as T


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.current = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def scan_tokens(self) -> list[Token]:
        while not self._at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_column = self.column
            self._scan_one()
        self.tokens.append(Token(T.EOF, "", None, self.line, self.column))
        return self.tokens

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _peek(self) -> str:
        return "" if self._at_end() else self.source[self.current]

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _match(self, char: str) -> bool:
        if self._peek() != char:
            return False
        self._advance()
        return True

    def _add(self, kind: T, literal: object = None) -> None:
        self.tokens.append(Token(
            kind, self.source[self.start:self.current], literal,
            self.start_line, self.start_column,
        ))

    def _fail(self, message: str) -> None:
        raise LexError(message, self.start_line, self.start_column)

    @staticmethod
    def _digit(char: str) -> bool:
        return "0" <= char <= "9"

    @staticmethod
    def _letter(char: str) -> bool:
        return "a" <= char <= "z" or "A" <= char <= "Z" or char == "_"

    def _scan_one(self) -> None:
        char = self._advance()
        if char in " \t":
            return
        if char in "\r\n":
            if char == "\r":
                self._match("\n")
            self._add(T.NEWLINE)
            self.line += 1
            self.column = 1
            return
        if char == "#":
            while not self._at_end() and self._peek() not in "\r\n":
                self._advance()
            return
        simple = {
            "+": T.PLUS, "-": T.MINUS, "*": T.STAR, "/": T.SLASH,
            "%": T.PERCENT, "(": T.LEFT_PAREN, ")": T.RIGHT_PAREN,
            "[": T.LEFT_BRACKET, "]": T.RIGHT_BRACKET, ",": T.COMMA,
            ":": T.COLON,
        }
        if char in simple:
            self._add(simple[char])
        elif char == "=":
            self._add(T.EQUAL_EQUAL if self._match("=") else T.EQUAL)
        elif char == "!":
            if not self._match("="):
                self._fail("Expected '=' after '!'; use 'not' for negation.")
            self._add(T.BANG_EQUAL)
        elif char == "<":
            self._add(T.LESS_EQUAL if self._match("=") else T.LESS)
        elif char == ">":
            self._add(T.GREATER_EQUAL if self._match("=") else T.GREATER)
        elif char == '"':
            self._string()
        elif self._digit(char):
            self._number()
        elif self._letter(char):
            while self._letter(self._peek()) or self._digit(self._peek()):
                self._advance()
            word = self.source[self.start:self.current]
            self._add(KEYWORDS.get(word, T.IDENTIFIER))
        else:
            self._fail(f"Unexpected character {char!r}.")

    def _number(self) -> None:
        while self._digit(self._peek()):
            self._advance()
        is_float = False
        if self._peek() == ".":
            is_float = True
            self._advance()
            if not self._digit(self._peek()):
                self._fail("A decimal point must be followed by a digit.")
            while self._digit(self._peek()):
                self._advance()
        text = self.source[self.start:self.current]
        try:
            value = float(text) if is_float else int(text)
        except (ValueError, OverflowError):
            self._fail("Number literal is too large.")
        if is_float and not math.isfinite(value):
            self._fail("Number literal must be finite.")
        self._add(T.NUMBER, value)

    def _string(self) -> None:
        chars: list[str] = []
        escapes = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"'}
        while not self._at_end():
            char = self._advance()
            if char == '"':
                self._add(T.STRING, "".join(chars))
                return
            if char in "\r\n":
                self._fail("Unterminated string; strings cannot contain literal line breaks.")
            if char == "\\":
                if self._at_end():
                    self._fail("Unterminated string.")
                escaped = self._advance()
                if escaped in "\r\n":
                    self._fail("Unterminated string; strings cannot contain literal line breaks.")
                if escaped not in escapes:
                    self._fail(f"Unknown string escape \\{escaped}.")
                chars.append(escapes[escaped])
            else:
                chars.append(char)
        self._fail("Unterminated string.")
