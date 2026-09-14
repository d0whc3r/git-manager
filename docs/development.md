# Development

```sh
make help    # list every target
```

| Target | What it does |
|--------|--------------|
| `sync` | Create `.venv` and install dependencies from `uv.lock` |
| `run` | Run the TUI (`DIR=<path>` to scan another folder) |
| `lint` | Check lint rules and formatting, changing nothing |
| `fmt` | Apply lint fixes and format the code |
| `test` | Run the self-check |
| `build` | Build a standalone binary into `dist/` |
| `install` | Install `git-manager` on your `PATH` |
| `uninstall` | Remove it from your `PATH` |
| `upgrade` | Upgrade locked dependencies to their latest allowed versions |
| `clean` | Remove build artifacts |

On Windows there is no `make` by default — run the commands from the `Makefile` directly.

## Layout

```
src/git_manager/
  git.py        # domain: shells out to git, returns plain data. No UI, no state.
  ui.py         # Textual app and modal. No subprocess calls.
  __main__.py   # argument handling and entry point
tests/
  test_git.py   # self-check for the domain layer
```

The split is the point. `git.py` is importable and testable without a terminal, and `ui.py`
never calls `subprocess` itself.

Every mutating operation — `update_default`, `merge_default`, `discard` — lives in `git.py` and
returns `(ok, message)`. The UI just renders the message, which is why all three actions share
one `_run(repo, op, label)` worker.

Adding an action means writing one function in `git.py` that returns `(ok, message)`, then a
binding and a two-line worker in `ui.py`.

## Threads

Git calls block, so every action runs on a Textual thread worker (`@work(thread=True)`).
Anything touching widgets from a worker goes through `call_from_thread`. The helpers make the
rule visible: `_write` and `_fill` run on the main thread, `say` and `_rescan` are the
worker-side wrappers.

Reading the cursor position happens in the action method, on the main thread, before the worker
starts — never inside it.

## Linting and formatting

Both are [ruff](https://docs.astral.sh/ruff/):

```sh
make lint   # reports, changes nothing
make fmt    # rewrites
```

CI runs both checks and fails on any difference, so run `make fmt` before pushing.

Rules live under `[tool.ruff.lint]` in `pyproject.toml`, each line commented with what it buys.
The ones worth knowing about:

| Set | Catches |
|-----|---------|
| `B` | Mutable default arguments, loop-variable capture, and similar real bugs |
| `S` | Security footguns — `subprocess` misuse, `assert` in shipped code, hardcoded secrets |
| `SIM`, `RET`, `PERF`, `FURB` | Code that can be shorter, flatter, or faster |
| `PTH` | `os.path` calls that should be `pathlib` |
| `T20` | Stray `print()` left behind from debugging |
| `SLF` | Reaching into another object's private members |
| `C90` | Functions over complexity 10 |
| `PGH` | Blanket `# noqa` with no rule code |

`PGH` is the one that keeps the rest honest: every suppression has to name the rule it silences,
so nothing gets muted by accident. There are three in the codebase, all in `git.py`, all with a
comment above them explaining why shelling out to `git` from `PATH` is the intended design.

Deliberately not enabled: `ANN` (type annotations) and `D` (docstrings on every public symbol).
Together they flag 60-odd sites in a 300-line project, most of them Textual lifecycle methods
whose signatures the framework already defines. Turn them on if the project grows enough to
need them.

Per-file exceptions live under `[tool.ruff.lint.per-file-ignores]`: the self-check may use
`assert`, shell out to `git`, and `print`; `__main__.py` may `print`.

## Tests

```sh
make test
```

`tests/test_git.py` is a plain script of asserts — no framework. It creates throwaway
repositories in a temp folder, clones one, moves the upstream ahead, dirties the working tree,
and asserts that discovery, default branch detection, and the `state`, `behind` and `ahead`
columns are all correct. It touches nothing outside that temp folder.

It covers `git.py` only. The UI is exercised by hand, or headlessly with Textual's
`App.run_test()`.
