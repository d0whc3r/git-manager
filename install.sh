#!/bin/sh
# Install the latest git-manager release binary.
#
#   curl -fsSL https://raw.githubusercontent.com/d0whc3r/git-manager/main/install.sh | sh
#
# BIN_DIR overrides where it lands. Default: ~/.local/bin
set -eu

REPO="${REPO:-d0whc3r/git-manager}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"

case "$(uname -s)" in
  Linux) os=linux ;;
  Darwin) os=macos ;;
  *)
    echo "install: no build for $(uname -s)." >&2
    echo "On Windows, download the .exe from https://github.com/$REPO/releases/latest" >&2
    exit 1
    ;;
esac

case "$(uname -m)" in
  x86_64 | amd64) arch=x86_64 ;;
  arm64 | aarch64) arch=arm64 ;;
  *)
    echo "install: no build for $(uname -m)." >&2
    exit 1
    ;;
esac

# Only macOS ships an arm64 build.
if [ "$os" = linux ] && [ "$arch" = arm64 ]; then
  echo "install: no Linux arm64 build. Use: uv tool install git+https://github.com/$REPO" >&2
  exit 1
fi

asset="git-manager-$os-$arch"
url="https://github.com/$REPO/releases/latest/download/$asset"

mkdir -p "$BIN_DIR"
# Download beside the target so the final move is atomic: a failed download can
# never leave a half-written binary where a working one used to be.
tmp="$(mktemp "$BIN_DIR/.git-manager.XXXXXX")"
trap 'rm -f "$tmp"' EXIT INT TERM

echo "Downloading $asset..."
if ! curl -fsSL "$url" -o "$tmp"; then
  echo "install: download failed: $url" >&2
  exit 1
fi

chmod 755 "$tmp"
mv -f "$tmp" "$BIN_DIR/git-manager"
trap - EXIT INT TERM

# The binaries are unsigned, so macOS refuses to run one that carries the flag.
if [ "$os" = macos ]; then
  xattr -d com.apple.quarantine "$BIN_DIR/git-manager" 2>/dev/null || true
fi

echo "Installed $BIN_DIR/git-manager"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Add $BIN_DIR to your PATH to run it as 'git-manager'." ;;
esac
