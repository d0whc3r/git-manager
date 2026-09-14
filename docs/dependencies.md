# Dependencies

`pyproject.toml` is the only place dependencies are declared:

```toml
[project]
dependencies = ["textual>=0.80"]   # needed at runtime, ships inside the binary

[dependency-groups]
dev = ["pyinstaller>=6.0", "ruff>=0.6"]   # build and check time only
```

`uv.lock` pins the exact resolved versions and is committed, so CI and every machine build the
same thing. Never edit it by hand.

## Common tasks

| Task | Command |
|------|---------|
| Add a runtime dependency | `uv add <package>` |
| Add a build-time dependency | `uv add --group dev <package>` |
| Remove one | `uv remove <package>` |
| Upgrade everything within the declared ranges | `make upgrade` |
| Upgrade a single package | `uv lock --upgrade-package <package>` |
| Recreate `.venv` from the lockfile | `make sync` |

`uv add`, `uv remove` and `uv lock` all rewrite `uv.lock`. Commit it alongside the change.

## When you need `make sync`

Rarely. `uv run` syncs the environment before every command, so `make run`, `make test`,
`make lint` and `make build` all work from a clean checkout with no setup step.

Run `make sync` when you want `.venv` to exist so your editor can point its interpreter at it.
