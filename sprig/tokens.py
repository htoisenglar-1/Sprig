"""The small vocabulary shared by Sprig's lexer and parser."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    NEWLINE = auto()
    EOF = auto()
    LET = auto()
    WHEN = auto()
    ELIF = auto()
    OTHERWISE = auto()
    END = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    FN = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    COLON = auto()


KEYWORDS = {
    word: TokenType[word.upper()]
    for word in (
        "let", "when", "elif", "otherwise", "end", "while", "for", "in",
        "fn", "return", "break", "continue", "true", "false", "nil",
        "and", "or", "not",
    )
}


@dataclass(frozen=True)
class Token:
    kind: TokenType
    lexeme: str
    literal: object
    line: int
    column: int
