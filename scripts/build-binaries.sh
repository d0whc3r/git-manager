#!/usr/bin/env bash
# Cross-compile the release binaries for every target into dist/.
#
# PyApp wraps our wheel and an embedded CPython in a Rust launcher, and cargo-zigbuild uses
# Zig as the cross-linker, so a single Linux host produces the macOS and Windows executables
# too. Zig ad-hoc signs the Mach-O output, which is what lets an unsigned arm64 binary start
# at all on Apple Silicon.
#
# Expects a wheel in dist/ and the cross toolchain already installed: see the release job in
# .github/workflows/build.yml.
set -euo pipefail

cd "$(dirname "$0")/.."

# v0.29.0 is pinned so a PyApp release cannot change what we ship without a commit.
: "${PYAPP_VERSION:=0.29.0}"
export PYAPP_PROJECT_NAME=git-manager
export PYAPP_EXEC_MODULE=git_manager
export PYAPP_PYTHON_VERSION=3.12
# Ship CPython inside the executable instead of fetching it on first run.
export PYAPP_DISTRIBUTION_EMBED=1
# Put the launcher's own path in $PYAPP instead of a bare "1", which is how
# `git-manager --upgrade` knows which file to replace.
export PYAPP_PASS_LOCATION=1

curl -fsSL "https://github.com/ofek/pyapp/releases/download/v$PYAPP_VERSION/source.tar.gz" \
  -o pyapp.tar.gz
mkdir -p pyapp && tar -xzf pyapp.tar.gz -C pyapp --strip-components=1
# PyApp only accepts an embedded wheel as a path relative to its own directory.
cp dist/*.whl pyapp/
cd pyapp
PYAPP_PROJECT_PATH="$(ls ./*.whl)"
PYAPP_PROJECT_VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' ../pyproject.toml | head -1)"
export PYAPP_PROJECT_PATH PYAPP_PROJECT_VERSION

# Windows cross-links against the gnu ABI: zig cannot compile zstd-sys for msvc.
for entry in \
  "x86_64-unknown-linux-gnu:pyapp:git-manager-linux-x86_64" \
  "x86_64-pc-windows-gnu:pyapp.exe:git-manager-windows-x86_64.exe" \
  "aarch64-apple-darwin:pyapp:git-manager-macos-arm64" \
  "x86_64-apple-darwin:pyapp:git-manager-macos-x86_64"
do
  target="${entry%%:*}"; rest="${entry#*:}"
  cargo zigbuild --release --target "$target"
  mv "target/$target/release/${rest%%:*}" "../dist/${rest#*:}"
done
