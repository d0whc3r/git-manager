# Releasing

## Building a binary locally

```sh
make build     # dist/git-manager
```

Under the hood:

```sh
uv run pyinstaller --onefile --name git-manager --collect-all textual \
    --paths src src/git_manager/__main__.py
```

Two things that are not optional:

- `--collect-all textual` — without it, Textual's `.tcss` data files are missing from the
  bundle and the binary fails at startup.
- Absolute imports in `src/git_manager/__main__.py`. PyInstaller runs the entry script as a
  top-level `__main__` rather than as part of its package, so a relative import there builds
  fine and then crashes at runtime with `attempted relative import with no known parent
  package`.

PyInstaller does not cross-compile. The binary targets the OS and architecture you build on.

## Cutting a release

```sh
git tag v0.1.0
git push origin v0.1.0
```

`.github/workflows/build.yml` then runs the lint and format checks and the self-check, builds
on four runners (Linux x86_64, Windows x86_64, macOS arm64, macOS x86_64), and attaches the
four binaries to a GitHub release.

Bump `version` in `pyproject.toml` and `__version__` in `src/git_manager/__init__.py` to match
the tag before pushing it.

`workflow_dispatch` is also enabled, so you can build the four binaries as artifacts from the
Actions tab without tagging anything.

## Signing

The binaries are unsigned. macOS users have to clear the quarantine flag on first run, which
[Installation](installation.md) documents. Signing needs an Apple Developer certificate and a
notarization step in CI; nobody has asked for it yet.
