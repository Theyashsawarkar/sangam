#!/usr/bin/env bash
# Install sangam for the current user, no root needed:
#
#   curl -fsSL https://raw.githubusercontent.com/Theyashsawarkar/sangam/main/install.sh | bash
#
# Clones (or updates) sangam into ~/.local/share/sangam and links
# ~/.local/bin/sangam to it, then runs `sangam doctor`. Run it again to
# update.
#
#   install.sh [--bin-dir DIR] [--dir DIR] [--ref BRANCH|TAG] [--uninstall]
set -euo pipefail

REPO=https://github.com/Theyashsawarkar/sangam.git
DIR=${XDG_DATA_HOME:-$HOME/.local/share}/sangam
BIN_DIR=$HOME/.local/bin
REF=main
UNINSTALL=0

while [ $# -gt 0 ]; do
  case $1 in
    --bin-dir) BIN_DIR=$2; shift 2 ;;
    --dir) DIR=$2; shift 2 ;;
    --ref) REF=$2; shift 2 ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h | --help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "install.sh: unknown option $1" >&2; exit 2 ;;
  esac
done

say() { printf '\033[1;38;2;203;166;247m==>\033[0m %s\n' "$*"; }

if [ "$UNINSTALL" = 1 ]; then
  rm -f "$BIN_DIR/sangam"
  rm -rf "$DIR"
  say "Removed sangam ($BIN_DIR/sangam, $DIR)."
  say "Your sections (~/.config/sangam) and cache (~/.cache/sangam) are kept; delete them by hand if you like."
  exit 0
fi

command -v git >/dev/null || { echo "install.sh: git is needed to install sangam" >&2; exit 1; }

if [ -d "$DIR/.git" ]; then
  say "Updating $DIR"
  git -C "$DIR" fetch --quiet --tags origin
  git -C "$DIR" checkout --quiet "$REF"
  git -C "$DIR" pull --quiet --ff-only origin "$REF" 2>/dev/null || true   # a tag has nothing to pull
else
  say "Cloning sangam into $DIR"
  mkdir -p "$(dirname "$DIR")"
  git clone --quiet "$REPO" "$DIR"
  git -C "$DIR" checkout --quiet "$REF"
fi

mkdir -p "$BIN_DIR"
ln -sf "$DIR/bin/sangam" "$BIN_DIR/sangam"
say "Linked $BIN_DIR/sangam -> $DIR/bin/sangam"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) say "$BIN_DIR isn't on your PATH yet. Add this to your shell's rc file:"
     printf '      export PATH="%s:$PATH"\n' "$BIN_DIR" ;;
esac

say "Checking the dependencies (sangam doctor):"
"$DIR/bin/sangam" doctor || say "Fix what's marked ✗ above, then run: sangam"
