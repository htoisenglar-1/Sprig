# Sprig: design decisions

Sprig is a working language name; uniqueness and publication availability have not been checked. `.sprig` is its source extension. Its purpose is to teach language implementation while providing a small, readable general-purpose core.

## A real interpreter implemented in Python

The lexer reads characters, the parser builds a Sprig AST, and the interpreter executes that AST. Python is the tool used to implement those components. Sprig source is never delegated to Python `eval`, `exec`, `ast`, or `tokenize`.

This gives us control over syntax and semantics. For example, Sprig rejects numbers as conditions and distinguishes booleans from numbers even though Python's own type relationships differ.

## Readability with explicit block endings

The initial example uses familiar arithmetic and function calls:

```text
let score = 8 + 2 * 3
when score >= 10:
    print("Goal reached!")
otherwise:
    print("Keep practicing!")
end
```

`let` distinguishes declaration from reassignment. `when` and `otherwise` introduce readable branches. A colon introduces a block and `end` closes it. Indentation is encouraged but insignificant, so our first lexer needs no indentation stack. Newlines terminate statements; multiline expressions are deliberately postponed.

## A small set of runtime rules

Numbers, strings, booleans, nil, lists, and functions are enough to write useful examples. Dynamic typing means the value's kind is checked during execution, rather than requiring type declarations on variables.

Arithmetic checks kinds instead of silently converting values. `print` accepts multiple arguments, and `str` makes conversion explicit. Lists are mutable; numeric values and strings are treated as immutable. Negative integer indexing is convenient but fractional and Boolean indices are errors.

Strict Boolean conditions make common mistakes visible. Short-circuit `and` and `or` still support guards. Chained comparisons are postponed to keep parsing and evaluation unambiguous in the first version.

## Explicit scope behavior

Top-level declarations are global. Blocks share their surrounding environment. Function calls create local environments, and functions retain their defining environment. Lookup and assignment search outward; `let` declares locally. These rules support recursion, local shadowing, and closures.

A `for` loop creates or updates its iteration variable locally. It visits a snapshot of list element references, making mutation of the original list's length predictable. Nested list values remain shared.

Built-ins occupy a protected parent environment. Programs can declare a local name that shadows a built-in, but cannot overwrite the actual built-in binding through assignment.

## Build the straightforward evaluator first

A tree walker is easy to inspect: one AST node maps to a small piece of interpreter behavior. A bytecode compiler and VM might later improve some workloads, but introduce extra representations and debugging work. Version 0.1 prioritizes clarity and tests.

## Deliberate limits

We avoid host imports and attribute access. This keeps the language core small; it does not create a security sandbox. Eager `range` is capped at 100,000 elements. Optional evaluation steps help catch accidental infinite loops, but memory, string/list growth, and expensive operations still require judgment.

Modules, dictionaries, classes, package management, a broad standard library, a debugger, and bytecode are deferred. The reference is authoritative for current syntax; proposed future examples must be labeled as proposals.
