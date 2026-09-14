# Installation

`git` must be on your `PATH`. That is the only external requirement.

## A release binary

Prebuilt, self-contained, no Python needed.

On Linux and macOS, one command picks the right file, drops it on your `PATH`, makes it
executable and clears the macOS quarantine flag:

```sh
curl -fsSL https://raw.githubusercontent.com/d0whc3r/git-manager/main/install.sh | sh
```

It lands in `~/.local/bin`, which has to be on your `PATH`. Set `BIN_DIR` to change that:

```sh
curl -fsSL https://raw.githubusercontent.com/d0whc3r/git-manager/main/install.sh | BIN_DIR=/usr/local/bin sh
```

Once it is installed, it upgrades itself:

```sh
git-manager --upgrade
```

That checks the latest release, and when it is newer, downloads it over the binary you are
running — wherever you put it. It is a no-op when you are already on the latest version.
Re-running the install command above does the same thing unconditionally.

Self-upgrade needs a release binary. A `uv tool` install is upgraded with `uv tool upgrade
git-manager`, and on Windows you download the new `.exe` by hand.

The files are attached to each [release](../../../releases) if you prefer to download by hand:

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

## With uv, onto your PATH

No clone, and it works on Windows too:

```sh
uv tool install git+https://github.com/d0whc3r/git-manager
uv tool upgrade git-manager
uv tool uninstall git-manager
```

To run it once without installing anything:

```sh
uvx --from git+https://github.com/d0whc3r/git-manager git-manager
```

From a working copy instead:

```sh
make install    # uv tool install --force .
make uninstall
```

Either way it lands in its own isolated environment, so it touches neither `.venv` nor any
other project.

## Command line

```
usage: git-manager [folder]

  -h, --help     show this message
  -V, --version  show the version
  --upgrade      replace the installed binary with the latest release
```

With no argument it scans the current folder.
