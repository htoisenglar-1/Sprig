# Working on Sprig

Use Python 3.10 or newer. The source runner and tests need only the standard library.

```sh
cd ~/Desktop/sprig
python3 -m unittest discover -v
python3 -m sprig examples/hello.sprig
```

For a language change, write down a small source example and expected behavior first.
Update tokens/lexer for new spelling, AST/parser for new structure, interpreter or
built-ins for new behavior, and the reference/tutorial to explain the rule.
Add tests that exercise behavior and error cases. Run the whole suite before sharing.
Keep source positions attached to nodes so diagnostics stay useful.

The pipeline is source → lexer → tokens → parser → AST → interpreter. Never delegate
Sprig source execution to Python eval, exec, compile, or another host source runner.

## Preparing a GitHub repository

This folder is organized for a repository, but no remote repository has been created.
Before publishing, choose a license and confirm the working project name. From this
folder, initialize Git if desired, review the files, then commit:

```sh
git init
git status
git add README.md CONTRIBUTING.md pyproject.toml MANIFEST.in .gitignore sprig tests examples docs
git diff --cached
git commit -m "Build the initial Sprig interpreter"
```

Do not commit virtual environments, build output, cache files, or credentials.
Remote repository creation, package-index publication, and hosted CI are later steps;
local tests do not establish that every Python version or operating system is verified.
