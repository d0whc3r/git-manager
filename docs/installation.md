# Installation

`git` must be on your `PATH`. That is the only external requirement.

## A release binary

Prebuilt, self-contained, no Python needed. Attached to each [release](../../../releases):

| File | Platform |
|------|----------|
| `git-manager-linux-x86_64` | Linux x86_64 |
| `git-manager-windows-x86_64.exe` | Windows x86_64 |
| `git-manager-macos-arm64` | macOS Apple Silicon |
| `git-manager-macos-x86_64` | macOS Intel |

On Linux and macOS, make it executable:

```sh
chmod +x ./git-manager-*
```

The binaries are unsigned. macOS will refuse to run one until you clear the quarantine flag:

```sh
xattr -d com.apple.quarantine ./git-manager-macos-arm64
```

## From source, without installing

[uv](https://docs.astral.sh/uv/) creates the environment and installs dependencies on first run:

```sh
uv run git-manager            # scan the current folder
uv run git-manager ~/projects # scan another folder
```

## From source, onto your PATH

```sh
make install    # uv tool install --force .
make uninstall
```

This installs from the working copy into its own isolated environment, so it touches neither
`.venv` nor any other project.

## Command line

```
usage: git-manager [folder]

  -h, --help     show this message
  -V, --version  show the version
```

With no argument it scans the current folder.
