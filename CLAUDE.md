# tmux-gh-pr -- notes for agents

A standalone tmux plugin (TPM), pulled into Vayu
(github.com/Theyashsawarkar/vayu) by its tmux.conf. Keep it working on a
stock tmux without Vayu: no hardcoded paths, Vayu-specific behaviour only
through options (`@gh-pr-*`, see gh-pr.tmux and the README).

- `gh-pr.tmux` binds the key; `scripts/gh-pr.sh` is everything else (it
  calls itself with `--strip`, `--main`, `--preview`... for each part).
- Every key inside the popup has a `# keybind: Tmux/PR popup | <keys> |
  <Verb> ...` line in the script header: Vayu's keybinding search reads
  them. Add, change or remove that line with the key, and update the
  README's key table and the `?` key sheet (`keysheet()`).
- Every change gets a CHANGELOG.md entry; releases are tags (`vX.Y.Z`).
- Test on an isolated tmux server, never the live one: a bare one
  (`tmux -L t -f /dev/null`, then `run-shell .../gh-pr.tmux`) and Vayu's
  config. Drive it from an outer server so the popup has a client:
  `tmux -L outer -f /dev/null new -d -s o -x 200 -y 50 "env -u TMUX tmux -L inner -f /dev/null new -A -s main"`,
  `tmux -L inner run-shell $PWD/gh-pr.tmux`, `tmux -L outer send-keys -t o C-b G`,
  `tmux -L outer capture-pane -p -t o`.
- Theyashsawarkar/pr-playground is a test repo with one PR per merge
  situation (clean, conflicting, behind, failing CI, draft, needs review).
