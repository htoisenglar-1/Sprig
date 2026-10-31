"""Execute the AST with Sprig's own rules and lexical environments."""

import sys

from . import ast_nodes as ast
from .builtins import install_builtins, integer, sequence
from .environment import Environment
from .errors import RuntimeFault
from .tokens import TokenType as T
from .values import (BuiltinFunction, UserFunction, checked_number, equal_values,
                     is_number, require_boolean, type_name)


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class Interpreter:
    def __init__(self, stdout=None, stdin=None, args=None, max_steps=None):
        if max_steps is not None and (type(max_steps) is not int or max_steps <= 0):
            raise ValueError("max_steps must be a positive integer or None")
        self.stdout = sys.stdout if stdout is None else stdout
        self.stdin = sys.stdin if stdin is None else stdin
        builtins = Environment(readonly=True)
        install_builtins(builtins)
        self.globals = Environment(builtins)
        self.globals.values["args"] = list(args or [])
        self.environment = self.globals
        self.max_steps = max_steps
        self.steps = 0
        self.source = ""
        self.filename = "<stdin>"
        self.current_token = None

    def tick(self, token):
        self.current_token = token
        self.steps += 1
        if self.max_steps is not None and self.steps > self.max_steps:
            self.fail("Execution step limit exceeded.", token)

    def fail(self, message, token):
        error = RuntimeFault(message, token.line, token.column)
        error.source, error.filename = self.source, self.filename
        raise error

    def execute(self, statements):
        for statement in statements:
            self.execute_statement(statement)

    def execute_block(self, statements, environment):
        previous = self.environment
        self.environment = environment
        try:
            self.execute(statements)
        finally:
            self.environment = previous

    def execute_statement(self, node):
        self.tick(node.token)
        if isinstance(node, ast.VarDecl):
            value = self.evaluate(node.initializer)
            self.environment.define(node.name.lexeme, value, node.name)
        elif isinstance(node, ast.Assign):
            if isinstance(node.target, ast.Variable):
                value = self.evaluate(node.value)
                self.environment.assign(node.target.token.lexeme, value, node.target.token)
            else:
                collection = self.evaluate(node.target.collection)
                index = self.evaluate(node.target.index)
                self.validate_index(collection, index, node.target.token)
                if not isinstance(collection, list):
                    self.fail("Strings are immutable; index assignment requires a list.", node.target.token)
                value = self.evaluate(node.value)
                # The RHS may call a function that mutates this very list.
                self.validate_index(collection, index, node.target.token)
                collection[index] = value
        elif isinstance(node, ast.ExpressionStmt):
            self.evaluate(node.expression)
        elif isinstance(node, ast.IfStmt):
            for condition, body in node.branches:
                if require_boolean(self.evaluate(condition), condition.token):
                    self.execute(body)
                    break
            else:
                self.execute(node.otherwise)
        elif isinstance(node, ast.WhileStmt):
            while require_boolean(self.evaluate(node.condition), node.condition.token):
                try:
                    self.execute(node.body)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif isinstance(node, ast.ForStmt):
            values = list(sequence(self.evaluate(node.iterable), node.token))
            for value in values:
                # Count iterations too: an empty body must respect a step budget.
                self.tick(node.token)
                self.environment.values[node.name.lexeme] = value
                try:
                    self.execute(node.body)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif isinstance(node, ast.FunctionStmt):
            function = UserFunction(node, self.environment, self.source, self.filename)
            self.environment.define(node.name.lexeme, function, node.name)
        elif isinstance(node, ast.ReturnStmt):
            raise ReturnSignal(None if node.value is None else self.evaluate(node.value))
        elif isinstance(node, ast.BreakStmt):
            raise BreakSignal()
        elif isinstance(node, ast.ContinueStmt):
            raise ContinueSignal()
        else:
            raise TypeError(f"Unknown statement node: {type(node).__name__}")

    def evaluate(self, node):
        self.tick(node.token)
        if isinstance(node, ast.Literal):
            return node.value
        if isinstance(node, ast.Variable):
            return self.environment.get(node.token.lexeme, node.token)
        if isinstance(node, ast.ListExpr):
            return [self.evaluate(item) for item in node.elements]
        if isinstance(node, ast.Unary):
            value = self.evaluate(node.operand)
            if node.token.kind == T.NOT:
                return not require_boolean(value, node.token)
            return checked_number(-checked_number(value, node.token), node.token)
        if isinstance(node, ast.Logical):
            left = require_boolean(self.evaluate(node.left), node.token)
            if node.token.kind == T.OR and left:
                return True
            if node.token.kind == T.AND and not left:
                return False
            return require_boolean(self.evaluate(node.right), node.token)
        if isinstance(node, ast.Binary):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            return self.binary(node.token, left, right)
        if isinstance(node, ast.Index):
            collection = self.evaluate(node.collection)
            index = self.evaluate(node.index)
            self.validate_index(collection, index, node.token)
            return collection[index]
        if isinstance(node, ast.Call):
            callee = self.evaluate(node.callee)
            arguments = [self.evaluate(argument) for argument in node.arguments]
            if not isinstance(callee, (BuiltinFunction, UserFunction)):
                self.fail(f"Cannot call a {type_name(callee)} value.", node.token)
            try:
                return callee.call(self, arguments, node.token)
            except RuntimeFault:
                raise
            except (RecursionError, OverflowError, ValueError) as error:
                self.fail(self.host_error_message(error), node.token)
        raise TypeError(f"Unknown expression node: {type(node).__name__}")

    def validate_index(self, collection, index, token):
        sequence(collection, token)
        integer(index, token)
        if not -len(collection) <= index < len(collection):
            self.fail("Index out of range.", token)

    def binary(self, token, left, right):
        kind = token.kind
        if kind in (T.EQUAL_EQUAL, T.BANG_EQUAL):
            try:
                answer = equal_values(left, right)
            except RecursionError as error:
                self.fail(self.host_error_message(error), token)
            return answer if kind == T.EQUAL_EQUAL else not answer
        if kind == T.PLUS and isinstance(left, str) and isinstance(right, str):
            return left + right
        if kind == T.PLUS and isinstance(left, list) and isinstance(right, list):
            return left + right
        if not is_number(left) or not is_number(right):
            self.fail(f"Operator '{token.lexeme}' requires numbers; got {type_name(left)} and {type_name(right)}.", token)
        if kind in (T.LESS, T.LESS_EQUAL, T.GREATER, T.GREATER_EQUAL):
            if kind == T.LESS:
                return left < right
            if kind == T.LESS_EQUAL:
                return left <= right
            if kind == T.GREATER:
                return left > right
            return left >= right
        try:
            if kind == T.PLUS:
                result = left + right
            elif kind == T.MINUS:
                result = left - right
            elif kind == T.STAR:
                result = left * right
            elif kind == T.SLASH:
                if right == 0:
                    self.fail("Division by zero.", token)
                result = left / right
            elif kind == T.PERCENT:
                if right == 0:
                    self.fail("Modulo by zero.", token)
                result = left % right
            else:
                raise TypeError("Unknown binary operator.")
        except (OverflowError, ValueError) as error:
            self.fail(self.host_error_message(error), token)
        return checked_number(result, token)

    @staticmethod
    def host_error_message(error):
        if isinstance(error, RecursionError):
            return "Nesting or function recursion limit exceeded. Simplify the expression or check the function's stopping condition."
        return "Numeric or value limit exceeded. Use a smaller value."
