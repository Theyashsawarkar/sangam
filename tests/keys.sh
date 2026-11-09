#!/usr/bin/env bash
# The vim keys: what `sangam --key` (fzf's transform for every key but the
# moving ones) answers for each key and pending prefix. No fzf, gh or tmux:
# it only reads and writes $STATE/pending.
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
STATE=$(mktemp -d); export STATE
trap 'rm -rf "$STATE"' EXIT
fails=0
fail() { echo "FAIL: $1"; fails=$((fails + 1)); }
press() { FZF_KEY=$1 FZF_COLUMNS=180 bash "$here/bin/sangam" --key | sed 's/\x1b\[[0-9;]*m//g'; }
pending() { cat "$STATE/pending" 2>/dev/null; }
has() { grep -qF -- "$2" <<<"$1" || fail "$3: want '$2' in: $1"; }
hasnt() { grep -qF -- "$2" <<<"$1" && fail "$3: didn't want '$2' in: $1"; }

# Space opens the leader: moving keys unbound, which-key in the footer.
o=$(press space); has "$o" "unbind(j,k" space; has "$o" "change-footer:Space ›" space; has "$o" "p PR…" space
[ "$(pending)" = space ] || fail "space: pending is '$(pending)'"
o=$(press p); has "$o" "Space p ›" "space p"; has "$o" "m merge" "space p"
o=$(press m); has "$o" "rebind(j,k" "space p m"; has "$o" "--action merge {1}" "space p m"
[ -z "$(pending)" ] || fail "space p m: still pending '$(pending)'"

# Esc cancels a pending key and gives the moving keys back; with nothing
# pending it quits; in the filter it goes back to normal mode.
press space >/dev/null; o=$(press esc); has "$o" "rebind(j,k" "esc pending"; hasnt "$o" abort "esc pending"
o=$(press esc); has "$o" abort "esc"
o=$(FZF_INPUT_STATE=enabled press esc); has "$o" "hide-input+rebind(" "esc in filter"

# gg, and a stray key after g does nothing.
press g >/dev/null; o=$(press g); has "$o" "+first" gg
press g >/dev/null; o=$(press m); hasnt "$o" "moved" "g m"; [ -z "$(pending)" ] || fail "g m: still pending"

# Every leader leaf.
leaf() { local want=$1; shift; local k o=""; for k in "$@"; do o=$(press "$k"); done; has "$o" "$want" "$*"; }
leaf "--action approve" space p a; leaf "--action request" space p r; leaf "--action comment" space p c
leaf "--action close" space p x; leaf "--action draft" space p d; leaf "--action checkout" space g b
leaf "--next-acct" space g a; leaf "show-input+unbind(" space f f; leaf "--next-state" space f s
leaf "--toggle-all" space f a; leaf "--search" space f g; leaf "--clear-search" space f c
leaf "--section-to 3" space t 3; leaf "--copy {1}" space y y; leaf "--web {1}" space o b
leaf "--sections-menu" space , s; leaf "--edit" space , e; leaf "--reload" space r; leaf abort space q
leaf "--show-keys" space '?'; leaf "--palette)+transform(" space space

# Direct keys, and the ones that moved say where.
leaf "--section -1" H; leaf "--section 1" L; leaf "--section 1" l; leaf "--reload" r; leaf "--web {1}" o
leaf "moved: merge → Space p m" m; leaf "moved: account → Space g a" u; leaf "--mode diff" 2

# A palette pick is replayed as keys.
echo "Space p a" >"$STATE/replay"
o=$(bash "$here/bin/sangam" --replay | sed 's/\x1b\[[0-9;]*m//g'); has "$o" "--action approve" replay
[ -z "$(pending)" ] || fail "replay: still pending"

# Regressions: a second action() (the approval popup's chips) once replaced
# the PR actions, so Space p m and the rest did nothing; and a section with
# an empty account lost its search ("a | | q" read as account q).
dups=$(grep -oE '^[a-z_]+\(\) ?\{' "$here/bin/sangam" | sed 's/(.*//' | sort | uniq -d)
[ -z "$dups" ] || fail "functions defined twice: $dups"
mkdir -p "$STATE/cfg/sangam" "$STATE/bin"; printf 'Mine | | author:@me\nWork | bob | org:x\n' >"$STATE/cfg/sangam/sections"
printf '#!/bin/sh\nexit 1\n' >"$STATE/bin/gh"; chmod +x "$STATE/bin/gh"; echo bob >"$STATE/accounts"
mkdir -p "$STATE/cache/sangam"; PATH="$STATE/bin:$PATH" XDG_CONFIG_HOME=$STATE/cfg XDG_CACHE_HOME=$STATE/cache HERE="" bash "$here/bin/sangam" --next-acct
printf 'Mine\tbob\tauthor:@me\n' | cmp -s - <(cut -f1-3 "$STATE/sections" | head -1) || fail "empty account: $(head -1 "$STATE/sections")"

((fails)) && { echo "$fails failed"; exit 1; }
echo "keys: ok"
