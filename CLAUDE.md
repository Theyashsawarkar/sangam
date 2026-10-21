# sangam -- notes for agents

A terminal UI for GitHub pull requests: one Bash script (`bin/sangam`)
over gh, fzf and tmux. Usable three ways, all from this repo: the `sangam`
command (install.sh, make install, packaging/arch), and a TPM plugin
(`sangam.tmux` binds a popup key). It is pulled into Vayu
(github.com/Theyashsawarkar/vayu) as a tmux plugin, but must work on any
Linux setup without Vayu: no hardcoded paths, Vayu-specific behaviour only
through the `@sangam-*` options.

- `bin/sangam` calls itself for every part (`--strip`, `--main`,
  `--preview`, `--action`...); the internal flags are dispatched in the
  first `case` near the end, the CLI (`doctor`, `-C`, `--popup`...) after
  it. The layout runs on a private tmux server (`$STATE/tmux.sock`).
- Every key has a `# keybind: Tmux/sangam | <keys> | <Verb> ...` line in
  the script header (Vayu's keybinding search reads them). Add, change or
  remove that line with the key, and update the README's key tables and
  the `?` key sheet (`keysheet()`).
- The README documents every feature, key, option and dependency: a
  change to any of them updates it. Every change gets a CHANGELOG.md
  entry; releases are tags (`vX.Y.Z`) with `VERSION` in bin/sangam and
  `pkgver` in packaging/arch/PKGBUILD bumped to match.
- `make check` must pass (ShellCheck at warning level, syntax, CLI).
- Test on throwaway tmux servers, never the user's live one. Standalone:
  `tmux -L t -f /dev/null new -d -s o -x 180 -y 44 "env -u TMUX bin/sangam"`,
  then `tmux -L t send-keys -t o ...` / `capture-pane -p -t o`. Popup:
  an outer server running `tmux -L inner -f /dev/null`, then
  `tmux -L inner run-shell $PWD/sangam.tmux` and `send-keys C-b G`.
  Quitting must leave no `$XDG_RUNTIME_DIR/sangam.*` dir and no server.
- Theyashsawarkar/pr-playground is a public test repo with one PR per
  merge situation. Screenshots (assets/screenshots) are taken with a
  sections file that only searches it, so no private PRs leak into them.
- The website (docs/, GitHub Pages) is generated: after changing README.md, CHANGELOG.md or docs/adr/, run `python3 scripts/build-site.py` and commit docs/ (CI checks it). A significant design decision gets a new ADR in docs/adr/ (next number; supersede, never rewrite).
