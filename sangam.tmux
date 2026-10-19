#!/usr/bin/env bash
# sangam as a tmux popup: TPM entry point (also works with a plain
# `run-shell` on this file). Binds prefix + @sangam-key to open sangam in a
# popup; the same key inside the popup closes it.
#
# Options (set them before TPM's `run` line):
#   @sangam-key       key after the prefix (default G; "none" binds nothing)
#   @sangam-width     popup width  (default 90%)
#   @sangam-height    popup height (default 88%)
#   @sangam-title     popup title  (default " sangam ")
#   @sangam-launcher  your own popup command instead of display-popup: it is
#                     run with display-popup's arguments appended (-E -d DIR
#                     -T TITLE CMD), tmux formats expanded, e.g.
#                     "~/.tmux/scripts/popup.sh '#{client_name}'"

dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
sangam="$dir/bin/sangam"

opt() { local v; v=$(tmux show-option -gqv "$1"); printf '%s' "${v:-$2}"; }
key=$(opt @sangam-key G)
[ "$key" = none ] && exit 0
width=$(opt @sangam-width 90%)
height=$(opt @sangam-height 88%)
title=$(opt @sangam-title ' sangam ')
launcher=$(opt @sangam-launcher '')

cmd="'$sangam' --popup '$key'"
if [ -n "$launcher" ]; then
  open="run -b \"$launcher -E -d '#{pane_current_path}' -T '$title' $cmd\""
else
  open="display-popup -E -w '$width' -h '$height' -d '#{pane_current_path}' -T '$title' \"$cmd\""
fi

tmux bind-key -N "Open sangam pull requests popup (review, merge; prefix $key again closes)" "$key" "$open"
