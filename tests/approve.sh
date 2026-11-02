#!/usr/bin/env bash
# The approval popup, on a throwaway tmux server with a request made by hand
# (no gh, nothing real): what it shows, that it fits any size, that it stays
# still while the countdown runs, and what each key answers.
set -u
here=$(cd "$(dirname "$0")/.." && pwd)
sock=sangam-test-$$
t() { tmux -L "$sock" -f /dev/null "$@"; }
tmp=$(mktemp -d)
trap 't kill-server 2>/dev/null; rm -rf "$tmp"' EXIT
fails=0
fail() { echo "FAIL: $1"; fails=$((fails + 1)); }

request() {  # request <name>: a merge request in $tmp/<name>
  local d=$tmp/$1; mkdir -p "$d"
  printf 'Claude Code' >"$d/who"; printf 'merge the checkout fix' >"$d/why"; date +%s >"$d/since"
  printf 'Merge' >"$d/kind"; printf 'acme/shop#142' >"$d/ref"; printf 'danger' >"$d/tone"
  printf 'squash and merge into' >"$d/say"; printf 'main' >"$d/target"; printf '' >"$d/after"
  printf 'Merge into main' >"$d/action"; printf 'Fix rounding in the checkout total' >"$d/title"
  printf 'bad\tlands on main\nplain\tundo is a revert\n' >"$d/chips"
  printf 'H\tReady to merge\nF\t✓\tChecks: 14 of 14 passed\nF\tFrom\tfix/rounding\nF\tInto\tmain\n' >"$d/facts"
  seq -f 'commit line %g' 1 60 >"$d/frame"
  printf 'https://example.com/pr' >"$d/url"; printf '' >"$d/log"
  printf 'diff --git a b\n' >"$d/diff"
}
stop() { t kill-server 2>/dev/null; while t has-session 2>/dev/null; do sleep .1; done; sleep .2; }
open() {  # open <name> <w> <h>
  stop
  t new -d -s o -x "$2" -y "$3" "env -u TMUX SANGAM_ASK='$tmp/$1' bash '$here/bin/sangam' --approve-ui; sleep 30"
  sleep 1.2
}
screen() { t capture-pane -p -t o; }

request show; open show 150 40
s=$(screen)
for want in "sangam · approve a merge" "acme/shop#142" "Claude Code wants to squash and merge into main" 'You asked: "merge the checkout fix"' \
    "lands on main" "Ready to merge" "✓ Checks: 14 of 14 passed" "Fix rounding in the checkout total" "commit line 1" "Merge into main" "Decline" "is a no"; do
  grep -qF "$want" <<<"$s" || fail "missing: $want"
done

# stays still: after the first draw only the countdown is written
t pipe-pane -t o -o "cat >>'$tmp/raw'"; sleep 3.5; t pipe-pane -t o
if grep -qaF $'\e[2J' "$tmp/raw"; then fail "it cleared the screen while waiting (flicker)"; fi
n=$(wc -c <"$tmp/raw"); [ "$n" -lt 400 ] || fail "wrote $n bytes in 3.5s while waiting, should be just the countdown"

# j scrolls the frame, without clearing either
: >"$tmp/raw"; t pipe-pane -t o -o "cat >>'$tmp/raw'"; t send-keys -t o j j j; sleep .5; t pipe-pane -t o
grep -qaF $'\e[2J' "$tmp/raw" && fail "scrolling cleared the screen"
grep -qF "commit line 4" <<<"$(screen)" || fail "j didn't scroll"

# any size: nothing past the edge, no error, the answers still there at a sane size
for size in "200 60" "120 30" "90 24" "70 20" "50 16" "30 10"; do
  set -- $size; request "s$1"; open "s$1" "$1" "$2"; s=$(screen)
  grep -q "syntax error\|bad substitution\|command not found\|unbound" <<<"$s" && fail "$size: an error on screen"
  [ "$(wc -l <<<"$s")" -le "$2" ] || fail "$size: too tall"
  [ "$1" -ge 50 ] && { grep -qF "Decline" <<<"$s" || fail "$size: no Decline"; }
done

# resize: redraws at the new size
request rz; open rz 120 30; t resize-window -t o -x 150 -y 40; sleep 1.4
grep -qF "Merge into main" <<<"$(screen)" || fail "resize lost the answers"

# the answers
answer() {  # answer <name> <keys...> -> the answer file
  local n=$1; shift; request "$n"; open "$n" 120 30; t send-keys -t o "$@"; sleep .5; cat "$tmp/$n/answer" 2>/dev/null
}
[ "$(answer a1 y)" = yes ] || fail "y didn't approve"
[ "$(answer a2 n)" = no ] || fail "n didn't decline"
[ "$(answer a3 Escape)" = no ] || fail "Esc didn't decline"
[ -z "$(answer a4 Enter)" ] || fail "Enter answered"
[ -z "$(answer a5 x)" ] || fail "x answered"

# a key pressed as it opens (you were typing) doesn't answer
request early; stop
t new -d -s o -x 120 -y 30 "env -u TMUX SANGAM_ASK='$tmp/early' bash '$here/bin/sangam' --approve-ui; sleep 30"
sleep .15; t send-keys -t o y; sleep 1
[ -z "$(cat "$tmp/early/answer" 2>/dev/null)" ] || fail "a key typed as it opened answered"

# with text: the edit is marked, u undoes it
request ed; printf 'hello there' >"$tmp/ed/text"; cp "$tmp/ed/text" "$tmp/ed/orig"; rm -f "$tmp/ed/frame"
printf '#!/bin/sh\nprintf "my words" >"$1"\n' >"$tmp/ed.sh"; chmod +x "$tmp/ed.sh"
stop
t new -d -s o -x 120 -y 30 "env -u TMUX EDITOR='$tmp/ed.sh' SANGAM_ASK='$tmp/ed' bash '$here/bin/sangam' --approve-ui; sleep 30"
sleep 1.2; t send-keys -t o e; sleep 1
s=$(screen); grep -qF "edited by you" <<<"$s" || fail "no sign of the edit"
grep -qF "my words" <<<"$s" || fail "the edit isn't shown"
grep -qF "Undo my edit" <<<"$s" || fail "no undo offered"
t send-keys -t o u; sleep .6
s=$(screen); grep -qF "hello there" <<<"$s" || fail "u didn't undo"
grep -qF "edited by you" <<<"$s" && fail "u left the label"

# A request from an older sangam still running shows everything it has.
old=$tmp/old; mkdir -p "$old"; printf 'Claude Code' >"$old/who"; printf 'merge (squash) acme/shop#7' >"$old/what"
printf 'Fix the thing\nas sam\n' >"$old/details"; printf 'lands on main' >"$old/risk"; printf 'commits that land:\n  a1f3c09 Fix\n' >"$old/extra"; : >"$old/why"; date +%s >"$old/since"
stop; t new -d -s o -x 150 -y 40 "env -u TMUX SANGAM_ASK='$old' bash '$here/bin/sangam' --approve-ui 2>'$tmp/old-err'; sleep 30"; sleep 1.2
s=$(screen)
for want in "Claude Code wants to merge (squash) acme/shop#7" "lands on main" "Fix the thing" "as sam" "a1f3c09" "Approve" "Decline"; do
  grep -qF "$want" <<<"$s" || fail "old request: missing $want"
done
[ ! -s "$tmp/old-err" ] || fail "old request: errors: $(cat "$tmp/old-err")"
stop
# ... and with text, which stays the text you can edit
printf 'hello team' >"$old/text"; rm -f "$old/kind"; date +%s >"$old/since"
t new -d -s o -x 150 -y 40 "env -u TMUX SANGAM_ASK='$old' bash '$here/bin/sangam' --approve-ui; sleep 30"; sleep 1.2
s=$(screen)
for want in "Fix the thing" "hello team" "Edit"; do grep -qF "$want" <<<"$s" || fail "old request with text: missing $want"; done
grep -qF "edited by you" <<<"$s" && fail "old request with text: shown as edited"
stop

# The tools build the request from what gh says. Fake gh, tmux and
# notify-send: nothing reaches GitHub or your tmux.
bin=$tmp/bin; mkdir -p "$bin"
cat >"$tmp/pr.json" <<'JSON'
{"title":"Fix search","state":"OPEN","isDraft":false,"mergeable":"MERGEABLE","mergeStateStatus":"BLOCKED","reviewDecision":"REVIEW_REQUIRED",
 "statusCheckRollup":[{"name":"e2e","conclusion":"FAILURE","status":"COMPLETED","detailsUrl":"https://example.com/log"},{"name":"unit","conclusion":"SUCCESS","status":"COMPLETED"}],
 "headRefName":"fix/search","baseRefName":"main","author":{"login":"priya"},"additions":12,"deletions":3,"changedFiles":2,"url":"https://example.com/pr/9",
 "commits":[{"oid":"a1f3c09aaaa","messageHeadline":"Rank exact matches first"}]}
JSON
cat >"$bin/gh" <<EOF
#!/bin/sh
case "\$1 \$2" in
  "auth status") echo "  Logged in to github.com account sam (keyring)"; echo "  - Active account: true" ;;
  "auth token") echo tok ;;
  "api "*) echo 9 ;;
  "pr view") cat "$tmp/pr.json" ;;
  "pr list") printf '#10' ;;
  "pr diff") echo "diff --git a/x b/x" ;;
  "pr merge"|"pr comment"|"pr review") echo "\$*" >>"$tmp/gh-writes" ;;
esac
EOF
cat >"$bin/tmux" <<EOF
#!/usr/bin/env bash
case "\$1" in
  list-clients) echo "1 /dev/pts/9" ;;
  display-popup)
    a="\$*"; d=\${a##*SANGAM_ASK=\'}; d=\${d%%\'*}
    rm -rf "$tmp/seen"; cp -r "\$d" "$tmp/seen"
    echo "\$*" >"$tmp/popup-args"
    cat "$tmp/say" >"\$d/answer" ;;
esac
EOF
printf '#!/bin/sh\nexit 0\n' >"$bin/notify-send"; chmod +x "$bin/"*
call() {  # call <tool> <json>
  env -u TMUX -u TMUX_PANE PATH="$bin:$PATH" XDG_STATE_HOME="$tmp/state" XDG_CACHE_HOME="$tmp/cache" XDG_CONFIG_HOME="$tmp/conf" "$here/bin/sangam" call "$1" "$2" 2>&1
}
seen() { grep -qF "$1" "$tmp/seen/$2" || fail "$2 lacks: $1"; }

echo no >"$tmp/say"
out=$(call pr_merge '{"pr":"acme/shop#9","auto":true,"delete_branch":true,"why":"get it merged"}')
grep -q "declined" <<<"$out" || fail "a no is not reported as declined: $out"
[ ! -e "$tmp/gh-writes" ] || fail "merged after a no"
grep -q -- " -B " "$tmp/popup-args" || fail "the popup keeps tmux's border"
seen "Auto-merge" kind; seen danger tone; seen "merge into" say; seen main target; seen "Turn on auto-merge" action
seen "not ready: Checks: 1 failed, 1 passed" chips; seen "merges later" chips; seen "lands on main" chips; seen "deletes the branch" chips; seen "moves #10" chips
seen "Not ready yet" facts; seen "✗"$'\t'"Checks: 1 failed" facts; seen "○"$'\t'"Review: needs an approval" facts; seen "fix/search" facts
seen "a1f3c09" frame; seen "✗ e2e" frame; seen "If you approve" frame; seen "https://example.com/log" log; seen "https://example.com/pr/9" url; seen "diff --git" diff

echo yes >"$tmp/say"
out=$(call pr_merge '{"pr":"acme/shop#9","method":"rebase"}')
grep -q "Merged" <<<"$out" || fail "merge: $out"; grep -q -- "--rebase" "$tmp/gh-writes" || fail "not a rebase"
seen "rebase and merge into" say; seen "Merge into main" action

out=$(call pr_comment '{"pr":"acme/shop#9","body":"Looks good"}')
grep -q "Posted" <<<"$out" || fail "comment: $out"
seen Comment kind; seen "Post the comment" action; seen "public on the PR" chips; seen "Looks good" text; seen "Fix search" facts

out=$(call pr_review '{"pr":"acme/shop#9","event":"request_changes","body":"Please fix"}')
grep -q "Review submitted" <<<"$out" || fail "review: $out"
seen "request changes" say; seen "blocks the merge" chips; seen "diff --git" diff

[ "$fails" -eq 0 ] && echo "approve popup: ok"
exit "$fails"
