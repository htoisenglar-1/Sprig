"""Sprig v2: a small lexer, parser, and tree-walking interpreter. Python 3.10+."""

import argparse
import math
import operator
import re
import sys
from collections import namedtuple
from pathlib import Path
from pprint import pprint


class SprigError(Exception):
    def __init__(self, line, message):
        super().__init__(f"Line {line}: {message}")


Token = namedtuple("Token", "kind text line")
Node = namedtuple("Node", "kind line args")
Function = namedtuple("Function", "params body closure")
KEYWORDS = set("let when otherwise end while repeat fn return true false nil and or not".split())
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
PATTERN = re.compile(
    r'(?P<space>[ \t]+|\#[^\r\n]*)|(?P<newline>\r\n|\r|\n)'
    r'|(?P<number>[0-9]+(?:\.[0-9]+)?)'
    r'|(?P<string>"(?:\\[^\r\n]|[^"\\\r\n])*")'
    r'|(?P<name>[A-Za-z_][A-Za-z_0-9]*)'
    r'|(?P<operator>==|!=|<=|>=|[+\-*/%()=:,<>])|(?P<bad>.)'
)
PRECEDENCE = {"or": 1, "and": 2, "==": 4, "!=": 4, "<": 4, "<=": 4,
              ">": 4, ">=": 4, "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}
OPERATIONS = {"+": operator.add, "-": operator.sub, "*": operator.mul,
              "/": operator.truediv, "%": operator.mod, "<": operator.lt,
              "<=": operator.le, ">": operator.gt, ">=": operator.ge}


def tokenize(source):
    """Keep newlines and line numbers; discard spaces and # comments."""
    tokens, line = [], 1
    for match in PATTERN.finditer(source):
        kind, text = match.lastgroup, match.group()
        if kind == "bad":
            message = "Unterminated string" if text == '"' else f"Unexpected character {text!r}"
            raise SprigError(line, message)
        if kind == "string":
            for escape in re.finditer(r"\\(.)", text):
                if escape[1] not in ESCAPES:
                    raise SprigError(line, f"Unknown escape \\{escape[1]}")
        if kind != "space":
            tokens.append(Token(kind, "\n" if kind == "newline" else text, line))
        if kind == "newline":
            line += 1
    if not tokens or tokens[-1].kind != "newline":
        tokens.append(Token("newline", "\n", line))
    return tokens + [Token("eof", "", line)]


class Parser:
    """Statements form blocks; precedence parsing builds small tuple AST nodes."""

    def __init__(self, tokens):
        self.tokens, self.pos, self.function_depth = tokens, 0, 0

    def peek(self):
        return self.tokens[self.pos]

    def take(self, text=None):
        token = self.peek()
        if text is not None and token.text != text:
            raise SprigError(token.line, f"Expected {text!r}, got {token.text or 'end of file'!r}")
        self.pos += 1
        return token

    def name(self):
        token = self.peek()
        if token.kind != "name" or token.text in KEYWORDS:
            raise SprigError(token.line, "Expected a name")
        return self.take().text

    def parse(self):
        return self.block(("",))

    def block(self, stops):
        body = []
        while self.peek().text not in stops:
            if self.peek().text == "":
                raise SprigError(self.peek().line, "Expected 'end'")
            if self.peek().text == "\n":
                self.take()
            else:
                body.append(self.statement())
        return body

    def suite(self, stops=("end",)):
        self.take(":")
        self.take("\n")
        return self.block(stops)

    def statement(self):
        token = self.peek()
        kind, line = token.text, token.line
        if kind == "let":
            self.take()
            name = self.name()
            self.take("=")
            node = Node("let", line, (name, self.expression()))
        elif kind in ("when", "while", "repeat"):
            self.take()
            condition = self.expression()
            body, other = self.suite(("otherwise", "end")), []
            if kind == "when" and self.peek().text == "otherwise":
                self.take()
                other = self.suite()
            self.take("end")
            node = Node(kind, line, (condition, body, other))
        elif kind == "fn":
            self.take()
            name, params = self.name(), []
            self.take("(")
            if self.peek().text != ")":
                while True:
                    param = self.name()
                    if param in params:
                        raise SprigError(line, f"Duplicate parameter {param!r}")
                    params.append(param)
                    if self.peek().text != ",":
                        break
                    self.take(",")
            self.take(")")
            self.function_depth += 1
            body = self.suite()
            self.function_depth -= 1
            self.take("end")
            node = Node("fn", line, (name, params, body))
        elif kind == "return":
            self.take()
            if not self.function_depth:
                raise SprigError(line, "Return is only allowed inside a function")
            value = Node("literal", line, (None,)) if self.peek().text == "\n" else self.expression()
            node = Node("return", line, (value,))
        else:
            value = self.expression()
            if self.peek().text == "=":
                if token.kind != "name" or value.kind != "name":
                    raise SprigError(line, "Assignment needs a variable name")
                self.take("=")
                node = Node("assign", line, (value.args[0], self.expression()))
            else:
                node = Node("expression", line, (value,))
        self.take("\n")
        return node

    def expression(self, minimum=0):
        token = self.take()
        text, line = token.text, token.line
        if text == "-" or (text == "not" and minimum <= 3):
            left = Node("unary", line, (text, self.expression(7 if text == "-" else 3)))
        elif text == "(":
            left = self.expression()
            self.take(")")
        elif token.kind == "number":
            try:
                value = float(text) if "." in text else int(text)
                if type(value) is float and not math.isfinite(value):
                    raise ValueError()
            except ValueError:
                raise SprigError(line, "Number is too large") from None
            left = Node("literal", line, (value,))
        elif token.kind == "string":
            value = re.sub(r"\\(.)", lambda m: ESCAPES[m[1]], text[1:-1])
            left = Node("literal", line, (value,))
        elif text in ("true", "false", "nil"):
            left = Node("literal", line, ({"true": True, "false": False, "nil": None}[text],))
        elif token.kind == "name" and text not in KEYWORDS:
            left = Node("name", line, (text,))
        else:
            raise SprigError(line, f"Expected an expression, got {text or 'end of file'!r}")
        compared = False
        while True:
            token = self.peek()
            if token.text == "(" and minimum <= 8:
                self.take()
                args = []
                if self.peek().text != ")":
                    while True:
                        args.append(self.expression())
                        if self.peek().text != ",":
                            break
                        self.take(",")
                self.take(")")
                left = Node("call", token.line, (left, args))
                continue
            level = PRECEDENCE.get(token.text, 0)
            if not level or level < minimum:
                break
            if level == 4:
                if compared:
                    raise SprigError(token.line, "Use 'and' between comparisons")
                compared = True
            self.take()
            left = Node("binary", token.line, (token.text, left, self.expression(level + 1)))
        return left


class Environment:
    """A function keeps its defining environment: lexical, rather than dynamic, scope."""

    def __init__(self, parent=None):
        self.values, self.parent = {}, parent

    def declare(self, name, value, line):
        if name in self.values:
            raise SprigError(line, f"Name {name!r} is already declared")
        self.values[name] = value

    def owner(self, name, line):
        if name in self.values:
            return self
        if self.parent is not None:
            return self.parent.owner(name, line)
        raise SprigError(line, f"Undefined name {name!r}")


class Return(Exception):
    def __init__(self, value):
        self.value = value


def display(value):
    if value is None:
        return "nil"
    if type(value) is bool:
        return "true" if value else "false"
    if isinstance(value, Function) or callable(value):
        return "<function>"
    return str(value)


class Interpreter:
    def __init__(self):
        builtins = Environment()
        builtins.values["print"] = lambda *args: print(*(display(arg) for arg in args))
        self.env, self.line = Environment(builtins), 1

    def run(self, source):
        self.line = 1
        try:
            return self.execute(Parser(tokenize(source)).parse(), self.env)
        except (ArithmeticError, ValueError, RecursionError) as error:
            message = "Too much recursion or nesting" if isinstance(error, RecursionError) else str(error)
            raise SprigError(self.line, message) from None

    @staticmethod
    def boolean(value, line):
        if type(value) is not bool:
            raise SprigError(line, "Expected a boolean (true or false)")
        return value

    def execute(self, body, env):
        result = None
        for node in body:
            self.line = node.line
            kind, args = node.kind, node.args
            result = None
            if kind in ("let", "assign"):
                name, expression = args
                value = self.evaluate(expression, env)
                if kind == "let":
                    env.declare(name, value, node.line)
                else:
                    env.owner(name, node.line).values[name] = value
            elif kind == "expression":
                result = self.evaluate(args[0], env)
            elif kind == "fn":
                name, params, statements = args
                env.declare(name, Function(params, statements, env), node.line)
            elif kind == "return":
                raise Return(self.evaluate(args[0], env))
            elif kind == "when":
                condition, yes, no = args
                self.execute(yes if self.boolean(self.evaluate(condition, env), node.line) else no, env)
            elif kind == "while":
                condition, statements, _ = args
                while self.boolean(self.evaluate(condition, env), node.line):
                    self.execute(statements, env)
            elif kind == "repeat":
                count, statements, _ = args
                count = self.evaluate(count, env)
                if type(count) is not int or count < 0:
                    raise SprigError(node.line, "Repeat needs a non-negative integer")
                for _ in range(count):
                    self.execute(statements, env)
        return result

    def evaluate(self, node, env):
        self.line = node.line
        kind, args = node.kind, node.args
        if kind == "literal":
            return args[0]
        if kind == "name":
            return env.owner(args[0], node.line).values[args[0]]
        if kind == "unary":
            op, expression = args
            value = self.evaluate(expression, env)
            if op == "not":
                return not self.boolean(value, node.line)
            if type(value) not in (int, float):
                raise SprigError(node.line, "Expected numbers")
            return -value
        if kind == "call":
            function, arguments = args
            function = self.evaluate(function, env)
            values = [self.evaluate(arg, env) for arg in arguments]
            if isinstance(function, Function):
                if len(values) != len(function.params):
                    raise SprigError(node.line, f"Expected {len(function.params)} arguments, got {len(values)}")
                local = Environment(function.closure)
                local.values.update(zip(function.params, values))
                try:
                    self.execute(function.body, local)
                except Return as returned:
                    return returned.value
                return None
            if callable(function):
                return function(*values)
            raise SprigError(node.line, "Value is not a function")
        op, left, right = args
        left = self.evaluate(left, env)
        if op in ("and", "or"):
            left = self.boolean(left, node.line)
            if (op == "and" and not left) or (op == "or" and left):
                return left
            return self.boolean(self.evaluate(right, env), node.line)
        right = self.evaluate(right, env)
        numeric = type(left) in (int, float) and type(right) in (int, float)
        if op in ("==", "!="):
            if isinstance(left, Function) or callable(left):
                equal = left is right
            else:
                equal = (numeric or type(left) is type(right)) and left == right
            return equal if op == "==" else not equal
        if not numeric and not (op == "+" and type(left) is str and type(right) is str):
            raise SprigError(node.line, "Expected numbers (or two strings for '+')")
        if op in ("/", "%") and right == 0:
            raise SprigError(node.line, "Division by zero")
        self.line = node.line
        value = OPERATIONS[op](left, right)
        if type(value) is float and not math.isfinite(value):
            raise SprigError(node.line, "Number is too large")
        return value


def repl():
    interpreter, buffer = Interpreter(), []
    print("Sprig 2.0 - :quit to exit, :reset to start over")
    while True:
        try:
            line = input("...> " if buffer else "sprig> ")
            if not buffer and line.strip() in (":quit", ":reset"):
                if line.strip() == ":quit":
                    return
                interpreter = Interpreter()
                continue
            buffer.append(line)
            source = "\n".join(buffer)
            tokens = tokenize(source)
            # Only keywords can open/close blocks; strings and comments cannot.
            depth = sum(t.text in ("fn", "when", "while", "repeat") for t in tokens)
            depth -= sum(t.text == "end" for t in tokens)
            if depth > 0:
                continue
            value = interpreter.run(source)
            if value is not None:
                print(display(value))
            buffer.clear()
        except SprigError as error:
            print(error, file=sys.stderr)
            buffer.clear()
        except KeyboardInterrupt:
            print()
            buffer.clear()
        except EOFError:
            if buffer:
                print("Unfinished block: expected 'end'", file=sys.stderr)
            return


def main():
    parser = argparse.ArgumentParser(description="Run a small Sprig 2 program.")
    parser.add_argument("--version", action="version", version="Sprig 2.0")
    parser.add_argument("--ast", action="store_true", help="show the syntax tree without running")
    parser.add_argument("file", nargs="?", help="a .sprig source file; omit for the interactive prompt")
    options = parser.parse_args()
    if not options.file:
        if options.ast:
            parser.error("--ast needs a .sprig file")
        repl()
        return 0
    try:
        path = Path(options.file)
        if path.suffix != ".sprig":
            raise SprigError(1, "Use a .sprig source file")
        source = path.read_text(encoding="utf-8")
        if options.ast:
            pprint(Parser(tokenize(source)).parse())
        else:
            Interpreter().run(source)
        return 0
    except (SprigError, OSError, UnicodeError, RecursionError) as error:
        message = "Too much recursion or nesting" if isinstance(error, RecursionError) else str(error)
        print(f"{options.file}: {message}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
