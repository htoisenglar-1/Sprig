"""Lexical scopes: names live in a mapping linked to an enclosing mapping."""

from .errors import RuntimeFault


class Environment:
    def __init__(self, parent=None, *, readonly=False):
        self.parent = parent
        self.values = {}
        self.readonly = readonly

    def define(self, name, value, token):
        if name in self.values:
            raise RuntimeFault(f"Name '{name}' is already declared in this scope.", token.line, token.column)
        self.values[name] = value

    def get(self, name, token):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name, token)
        raise RuntimeFault(f"Undefined variable '{name}'.", token.line, token.column)

    def assign(self, name, value, token):
        if name in self.values:
            if self.readonly:
                raise RuntimeFault(f"Cannot assign to built-in '{name}'.", token.line, token.column)
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value, token)
            return
        raise RuntimeFault(f"Cannot assign to undeclared variable '{name}'. Use 'let' first.", token.line, token.column)
