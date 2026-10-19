#!/usr/bin/env bash
# tmux-gh-pr: TPM entry point (also works with a plain `run-shell` on this
# file). Binds prefix + @gh-pr-key to the pull request popup; the same key
# inside the popup closes it.
#
# Options (set them before TPM's `run` line):
#   @gh-pr-key       key after the prefix (default G; "none" binds nothing)
#   @gh-pr-width     popup width  (default 90%)
#   @gh-pr-height    popup height (default 88%)
#   @gh-pr-title     popup title  (default " pull requests ")
#   @gh-pr-launcher  your own popup command instead of display-popup: it is
#                    run with display-popup's arguments appended (-E -d DIR
#                    -T TITLE CMD), tmux formats expanded, e.g.
#                    "~/.tmux/scripts/popup.sh '#{client_name}'"

dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
script="$dir/scripts/gh-pr.sh"

opt() { local v; v=$(tmux show-option -gqv "$1"); printf '%s' "${v:-$2}"; }
key=$(opt @gh-pr-key G)
[ "$key" = none ] && exit 0
width=$(opt @gh-pr-width 90%)
height=$(opt @gh-pr-height 88%)
title=$(opt @gh-pr-title ' pull requests ')
launcher=$(opt @gh-pr-launcher '')

if [ -n "$launcher" ]; then
  open="run -b \"$launcher -E -d '#{pane_current_path}' -T '$title' '$script' --session\""
else
  open="display-popup -E -w '$width' -h '$height' -d '#{pane_current_path}' -T '$title' \"'$script' --session\""
fi

# The popup runs its own gh-prs-<pid> session; killing it closes the popup.
tmux bind-key -N "Open pull requests popup (sections, accounts, search; prefix $key again closes)" "$key" \
  if-shell -F "#{m:gh-prs-*,#{session_name}}" "kill-session" "$open"
