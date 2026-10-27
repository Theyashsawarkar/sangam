# Changelog

Newest first.

## v2.1.0 -- 2026-10-27

- **For AI agents**: `sangam mcp`, an MCP server, and `sangam call <tool>
  [json]`, the same tools as commands. Agents can list and search PRs (a
  query, one of your sections, or all of them), read a PR (checks, reviews,
  files, comments, inline review comments) and its diff, and see the counts
  (`pr_counts`, what a status bar shows). Commenting, reviewing and merging
  wait for your approval in a tmux popup (`y` approve, `n` decline, `e`
  edit the text first), or a desktop notification without tmux; no answer in
  10 minutes is a no. Other people's text reaches the agent inside
  `<untrusted>` blocks.
- Agents use the account you picked with `u` (the one sangam opens on),
  else gh's active one.
- **Tells a status bar when PRs change**: after a merge, review, comment,
  close or draft toggle (yours or an agent's) and whenever it reloads lists,
  sangam writes the time to `~/.cache/sangam/changed`, so a bar showing PR
  counts can recount at once instead of on its next poll.
- Temp files of fetches cut short (closing the popup mid-fetch) no longer
  pile up in the cache: sangam clears ones older than 10 minutes on start.

## v2.0.2 -- 2026-10-21

- **Follows your theme**: with [varna](https://github.com/Theyashsawarkar/varna)
  installed, sangam takes the current theme's colours (fzf's list and
  borders, the PR state badges, review states, section tabs, the commit line
  and the key sheet) instead of its fixed palette; without it, nothing
  changes. All colours now come from one place at the top of the script.

## v2.0.1 -- 2026-10-21

- A website (GitHub Pages, https://theyashsawarkar.github.io/sangam/): the README as a home page, the
  changelog, and architecture decision records (`docs/adr/`), built from these files by
  `scripts/build-site.py`; CI checks the site is up to date.

## v2.0.0 -- 2026-10-19

tmux-gh-pr is now **sangam**: a command-line tool first, a tmux popup
second.

- `sangam` runs in any terminal, inside tmux or not, like lazygit. Its
  layout runs on a private tmux server (own socket, `-f /dev/null`, so
  none of your tmux config applies) that goes away when you quit.
- New commands: `sangam doctor` (checks every dependency and its minimum
  version, the GitHub sign-in and the optional tools), `sangam -C <dir>`,
  `--help`, `--version`. Starting without a required tool or a gh sign-in
  says what's missing instead of failing later.
- Install it with a per-user installer (`install.sh`, curl | bash, no
  root), `make install`, or an Arch PKGBUILD (`packaging/arch`). The repo
  is still a TPM plugin: `sangam.tmux` binds the popup key.
- **Breaking:** tmux options are `@sangam-key`, `@sangam-width`,
  `@sangam-height`, `@sangam-title`, `@sangam-launcher` (were `@gh-pr-*`).
  The TPM line is `set -g @plugin 'Theyashsawarkar/sangam'`.
- Sections live in `~/.config/sangam/sections` and the cache in
  `~/.cache/sangam`; an existing `~/.config/gh-pr/sections` is copied
  over on first run.
- The popup's key closing it now works through the private server: it
  takes your tmux prefix and the configured key. The key sheet (`?`) shows
  the real combination (e.g. "or Ctrl+a G").
- Fixed: on a cold cache the preview could show "mv: cannot stat ..."
  when it and the background prefetch fetched the same PR at once (they
  shared one temp file). Every fetch now writes its own temp file.
- Notifications carry the sangam icon and app name; the editor falls back
  to `vi` (was `nvim`) when neither `VISUAL` nor `EDITOR` is set.
- A logo (two streams meeting: a sangam, a merge), a full README with
  install steps, requirements, every feature, key and option, and
  troubleshooting, and CI (ShellCheck, syntax, CLI, `make install`).

## v1.0.0 -- 2026-10-19 (as tmux-gh-pr)

- First release as its own plugin. It started as `gh-pr.sh` inside
  [Vayu](https://github.com/Theyashsawarkar/vayu)'s tmux config (its full
  history up to here is in Vayu's CHANGELOG, 2026-10-16) and moved out so
  it can be installed, tested and upgraded on its own.
- `gh-pr.tmux`: a TPM entry point that binds the key (`@gh-pr-key`,
  default `G`; the same key inside the popup closes it), with options for
  the popup's size, title and an optional launcher of your own.
- Works off Vayu: links are copied with whichever of wl-copy, xclip and
  pbcopy works (else tmux's buffer), notifications fall back to a tmux
  message without notify-send, and the key sheet shows the configured key.
