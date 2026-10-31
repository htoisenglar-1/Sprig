# Sprig

Sprig is a small interpreted programming language, built in Python to make the inside of a language understandable. It has its own syntax, lexer, parser, abstract syntax tree, scope rules, and evaluator. It does not execute Sprig source with Python's `eval()` or `exec()`.

```text
fn square(value):
    return value * value
end

for value in range(1, 4):
    print(value, square(value))
end
```

Intended output:

```text
1 1
2 4
3 9
```

The project targets Python 3.10 or newer and uses only the Python standard library at runtime. Build and validation status is recorded in `docs/roadmap.md`.

## Start here

Open Terminal and enter:

```sh
cd ~/Desktop/sprig
python3 --version
python3 -m sprig examples/hello.sprig
```

Start an interactive prompt:

```sh
python3 -m sprig
```

Enter statements one at a time. Type `:help` for commands, `:reset` for a fresh environment, or `:quit` to leave. Close blocks with `end`; expressions and strings must fit on one line.

Run the automated tests:

```sh
python3 -m unittest discover -s tests -v
```

Inspect how a program is read without executing it:

```sh
python3 -m sprig --tokens examples/arithmetic.sprig
python3 -m sprig --ast examples/arithmetic.sprig
```

Pass arguments to a program:

```sh
python3 -m sprig examples/arguments.sprig Ada 3
```

An optional step budget helps catch accidental infinite loops:

```sh
python3 -m sprig --max-steps 10000 examples/loops.sprig
```

Steps count evaluated expressions, executed statements, and `for` iterations. It is a learning/debugging aid, not a security boundary or a wall-clock timeout.

## Optional command installation

Running `python3 -m sprig` from this folder needs no package installation. To add the `sprig` command inside a virtual environment:

```sh
cd ~/Desktop/sprig
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --no-deps -e .
sprig examples/hello.sprig
```

The editable install uses the setuptools build backend. Pip may need network access to obtain build tooling. The interpreter itself has no third-party runtime dependencies. Keep using `python3 -m sprig` if installation is unavailable.

## Learn the project

- `docs/tutorial.md`: stages 1–9, with examples, commands, debugging advice, and exercises; stage 10 is a future study plan.
- `docs/language-reference.md`: the syntax and runtime rules in one place.
- `docs/language-design.md`: why we made the main design choices.
- `docs/architecture.md`: each module's responsibility and the execution pipeline.
- `docs/roadmap.md`: milestone and verification status.
- `examples/`: small programs to read, change, and run.
- `tests/`: executable checks for the implementation.

## Scope of version 0.1

The core includes variables, numbers, strings, booleans, `nil`, conditions, loops, functions, lexical closures, mutable lists, built-in functions, source-position errors, a file runner, and a persistent REPL.

Modules, dictionaries, classes, a standard-library ecosystem, a package manager, a debugger, and a bytecode VM are future work. Sprig programs can consume CPU and memory; run programs you trust.

This is a learning implementation. The name is a working name, and the project has not been published to a package index or a remote GitHub repository.
