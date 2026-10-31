"""AST nodes describe Sprig structure without executing any of it."""

from __future__ import annotations

from dataclasses import dataclass

from .tokens import Token


class Expr:
    pass


class Stmt:
    pass


@dataclass
class Literal(Expr):
    token: Token
    value: object


@dataclass
class Variable(Expr):
    token: Token


@dataclass
class Binary(Expr):
    token: Token
    left: Expr
    right: Expr


@dataclass
class Logical(Expr):
    token: Token
    left: Expr
    right: Expr


@dataclass
class Unary(Expr):
    token: Token
    operand: Expr


@dataclass
class Call(Expr):
    token: Token
    callee: Expr
    arguments: list[Expr]


@dataclass
class ListExpr(Expr):
    token: Token
    elements: list[Expr]


@dataclass
class Index(Expr):
    token: Token
    collection: Expr
    index: Expr


@dataclass
class VarDecl(Stmt):
    token: Token
    name: Token
    initializer: Expr


@dataclass
class Assign(Stmt):
    token: Token
    target: Expr
    value: Expr


@dataclass
class ExpressionStmt(Stmt):
    token: Token
    expression: Expr


@dataclass
class IfStmt(Stmt):
    token: Token
    branches: list[tuple[Expr, list[Stmt]]]
    otherwise: list[Stmt]


@dataclass
class WhileStmt(Stmt):
    token: Token
    condition: Expr
    body: list[Stmt]


@dataclass
class ForStmt(Stmt):
    token: Token
    name: Token
    iterable: Expr
    body: list[Stmt]


@dataclass
class FunctionStmt(Stmt):
    token: Token
    name: Token
    parameters: list[Token]
    body: list[Stmt]


@dataclass
class ReturnStmt(Stmt):
    token: Token
    value: Expr | None


@dataclass
class BreakStmt(Stmt):
    token: Token


@dataclass
class ContinueStmt(Stmt):
    token: Token
