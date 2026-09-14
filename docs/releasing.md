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

Releases are automatic. Push to `main` and `.github/workflows/build.yml` reads the
[Conventional Commits](https://www.conventionalcommits.org/) since the last tag:

| Commit prefix                       | Bump  |
| ----------------------------------- | ----- |
| `fix:`                              | patch |
| `feat:`                             | minor |
| `BREAKING CHANGE:` / `feat!:`       | major |
| anything else (`docs:`, `chore:` …) | none  |

When there is something to release the pipeline writes the new version into
`pyproject.toml` and `src/git_manager/__init__.py`, commits it as
`chore(release): X.Y.Z [skip ci]`, tags `vX.Y.Z`, builds on four runners (Linux x86_64,
Windows x86_64, macOS arm64, macOS x86_64), and attaches the four binaries to a GitHub
release. Do not bump the version by hand — the pipeline owns it.

`[skip ci]` on the release commit is what stops the push from re-triggering the workflow.

When no commit warrants a bump the binaries are still built as artifacts, but no tag and no
release are created.

`workflow_dispatch` is also enabled, so you can build the four binaries from the Actions tab.

## Signing

The binaries are unsigned. macOS users have to clear the quarantine flag on first run, which
[Installation](installation.md) documents. Signing needs an Apple Developer certificate and a
notarization step in CI; nobody has asked for it yet.
