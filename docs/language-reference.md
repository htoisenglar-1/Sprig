# Sprig 0.1 language reference

This document defines the intended language contract. The verification record is in `roadmap.md`.

## Source and statements

Source files use `.sprig` and UTF-8 encoding. Keywords and variable names are case-sensitive. Names use ASCII letters, digits, and underscores, with a letter or underscore first: `score`, `_total`, `item2`. Text inside strings can contain Unicode.

A newline ends a statement. The final simple statement may end at the end of the file. Blank lines and comments are allowed. A `#` outside a string starts a comment through the end of the line. LF and CRLF line endings are accepted. Semicolons and multiline expressions are not supported.

Indentation helps humans but does not determine blocks. A colon introduces a block, a newline starts its body, and `end` closes it. Nested blocks each need their own `end`. Empty bodies are allowed.

Reserved keywords:

```text
let when elif otherwise end while for in fn return
break continue true false nil and or not
```

Built-in names such as `print` are ordinary names, not keywords.

## Values

| Kind | Literals and behavior |
|---|---|
| Number | `42`, `3.5`; decimal integer or fractional form with digits on both sides of the dot |
| String | `"Hello"`; double quotes, one source line |
| Boolean | `true`, `false`; distinct from numbers |
| Nil | `nil`; the absence of a value |
| List | `[1, "two", false]`; mutable, ordered values |
| Function | A built-in or a function created with `fn` |

A negative number is a unary minus expression, not a separate literal form. Exponent notation, hexadecimal numbers, single-quoted strings, and trailing commas are not supported. Floats must be finite; invalid or overflowing numeric operations report a Sprig error. Decimal conversion is subject to Python's host digit limits, and recursive functions are subject to Python's recursion depth. Large integers still consume memory. No performance benchmark is claimed.

String escapes:

| Source spelling | Value |
|---|---|
| `\"` | Double quote |
| `\\` | Backslash |
| `\n` | Newline |
| `\t` | Tab |
| `\r` | Carriage return |

Unrecognized escapes and unclosed strings are errors.

## Variables and assignment

```text
let count = 1
count = count + 1
```

`let` creates a binding in the current environment. Repeating a declaration in the same environment is an error. Assignment updates the nearest existing binding, searching outward through enclosing environments. Reading or assigning an undefined name is an error.

Top-level variables live in the global environment. Conditions and loops share their surrounding environment. Each function call creates a local environment. A local `let` can shadow an outer name.

Built-in names live in a separate, enclosing environment. Assigning to an actual built-in binding is forbidden. A `let` in the program can shadow one, because the declaration belongs to a different environment. The initial global variable `args` is a list of script argument strings.

## Expressions and precedence

From weakest to strongest:

| Operators | Meaning |
|---|---|
| `or` | Short-circuit Boolean or |
| `and` | Short-circuit Boolean and |
| `not` | Boolean negation |
| `== != < <= > >=` | A single comparison |
| `+ -` | Addition/subtraction |
| `* / %` | Multiplication/division/modulo |
| unary `-` | Numeric negation |
| `f(...)`, `value[index]` | Function call and indexing |
| `(...)` | Explicit grouping |

Binary arithmetic operators group from left to right. `8 + 2 * 3` is `14`. `10 - 3 - 2` is `5`. `not 2 == 3` means `not (2 == 3)`.

Arithmetic requires numbers, with two additions: string + string joins text, and list + list makes a new list containing both sets of elements. Concatenation does not deep-copy nested values. A boolean does not count as a number. `"x" + 1` is an error.

`/` performs ordinary division: `5 / 2` is `2.5`. `%` gives the remainder using floor-division semantics: `-5 % 3` is `1`. Division and modulo by zero are errors. Numeric ordering requires numbers.

Equality is value-based and aware of kinds: `1 == 1.0` is `true`, `1 == true` is `false`, and `nil == nil` is `true`. Lists compare their elements recursively. Functions compare by identity. Cyclic lists do not cause endless printing or equality recursion.

Conditions and logical operators require booleans. There is no automatic truthiness. `and` and `or` skip their right operand when the left operand determines the answer:

```text
let safe = false and number("not a number") == 0
```

Comparisons cannot be chained. Write `1 < x and x < 10`, rather than `1 < x < 10`.

Assignment is a statement, not an expression. Its target must be a variable or an index. There is no `+=` shorthand initially.

## Conditions

```text
when score >= 90:
    print("excellent")
elif score >= 60:
    print("pass")
otherwise:
    print("practice")
end
```

The first true branch runs. `elif` and `otherwise` are optional. Conditions must be booleans. Each branch shares the surrounding environment.

## Loops

```text
let count = 0
while count < 3:
    print(count)
    count = count + 1
end

for item in ["a", "b"]:
    print(item)
end
```

`while` checks its Boolean condition before each iteration. `for` accepts a list or string. For a list it iterates a snapshot of the element references, so appending to the original list does not extend that loop. String iteration yields one-character strings.

The `for` variable belongs to the current environment. It is created on first assignment if absent locally; an existing local binding is updated. Its final value remains after a nonempty loop. An empty iterable does not introduce a new loop variable. Because loop blocks share scope, repeatedly executing `let x = ...` in a loop body can cause a redeclaration error: declare reusable variables before the loop and assign inside it.

`break` ends the nearest loop. `continue` skips to its next iteration. Both are syntax errors outside a loop. A function declared inside a loop cannot use `break` or `continue` to control the enclosing function's loop.

## Functions and closures

```text
fn add(left, right):
    return left + right
end

print(add(2, 3))
```

A function requires exactly its declared number of arguments. Arguments are evaluated left to right. `return expression` exits the current function with a value; bare `return`, or reaching the end, returns `nil`. A return outside a function is a syntax error. Function names are declared in the surrounding environment, so recursion is possible.

Functions retain the environment where they were defined. This is lexical scope:

```text
fn make_counter():
    let count = 0
    fn next():
        count = count + 1
        return count
    end
    return next
end

let counter = make_counter()
print(counter())
print(counter())
```

The intended output is `1` then `2`. Assignment can update an enclosing variable. Use `let` to create a distinct local binding. Lists passed to functions remain shared, so mutating a list parameter affects that same list in the caller.

No anonymous functions, default arguments, variadic user functions, decorators, classes, or modules are included yet.

## Lists and indexing

```text
let tasks = ["read", "code"]
append(tasks, "test")
tasks[0] = "study"
print(tasks[-1])
```

Indices are integers, starting at zero. Negative indices count from the end. Booleans and fractional numbers are invalid indices, even `1.0`. Out-of-range access is an error. Lists support indexed assignment; strings support reading by index but are immutable. Slices are not supported.

## Built-in functions

| Function | Behavior |
|---|---|
| `print(...)` | Print zero or more values separated by spaces, then newline; return `nil` |
| `input()` / `input(prompt)` | Read one line, removing its line ending; return a string; input EOF is an error |
| `len(value)` | Length of a string or list |
| `append(items, value)` | Add to a list; return `nil` |
| `pop(items)` | Remove and return the final list element; empty list is an error |
| `range(stop)` | List from zero up to, excluding, stop |
| `range(start, stop)` | List from start up to, excluding, stop |
| `range(start, stop, step)` | As above, using nonzero integer step; negative step permitted |
| `str(value)` | The display form of a value as a string |
| `number(value)` | Convert a numeric string or number into a finite number; booleans are invalid |
| `type(value)` | Kind name: `number`, `string`, `boolean`, `nil`, `list`, or `function` |

`range` accepts integers, excluding booleans. It eagerly builds a list and is capped at 100,000 elements. Use a `while` loop when you do not want to allocate a range list.

Printing spells booleans `true`/`false` and the empty value `nil`. String arguments print without surrounding quotes; string elements inside displayed lists are quoted. Recursive list references are represented safely. No built-in exposes Python attributes, imports, or host file operations. Sprig is not a security sandbox.

## Command line

From the project folder:

```sh
python3 -m sprig --help
python3 -m sprig --version
python3 -m sprig examples/hello.sprig
python3 -m sprig examples/arguments.sprig Ada 3
python3 -m sprig --tokens examples/hello.sprig
python3 -m sprig --ast examples/hello.sprig
python3 -m sprig --max-steps 10000 examples/loops.sprig
```

Interpreter options go before the file. Words after the file become `args`. `--tokens` and `--ast` inspect without running the program and are mutually exclusive. File execution requires the `.sprig` extension. With no file, the persistent REPL starts.

File execution returns 0 for success, 1 for a Sprig/file/decoding error, and 130 for interruption. Command usage errors return 2. A REPL session returns 0 when it ends normally, even if earlier submissions failed. A displayed error contains the filename, line, column, source excerpt, and caret. Completed side effects before an error are not rolled back.

## Interactive prompt

Run `python3 -m sprig`. At `sprig>` enter a statement; unfinished blocks use `...>` until `end`. The same environment persists across entries. Use `print(...)` to display results. Commands at a fresh prompt:

- `:help`: show commands.
- `:reset`: start a fresh global environment.
- `:quit`: exit.

EOF exits. EOF during an unfinished block reports an error. Ctrl-C cancels the current buffer and keeps the REPL alive. Runtime errors leave earlier successful mutations in place. Code remembered by a function retains its definition source for diagnostics.
