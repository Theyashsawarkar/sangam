# Changelog

Newest first.

## v2.3.1 -- 2026-11-03

- Fixed: an agent's `sangam mcp` started before 2.3 and still running opened the
  new popup with almost nothing on it. It now shows everything the request has.

## v2.3.0 -- 2026-11-02

- **A new approval popup**: one sentence says who wants what, then what you
  asked, then labels for what's at stake. The details sit beside the exact
  text, or for a merge what's ready and what isn't, the commits that land and
  what follows. The action says what it does ("Merge into main"). The border
  turns red for a merge, and it says plainly when a PR isn't ready.
- **Fixed: the popup flickered.** It cleared and redrew everything each second
  for the countdown. Now it draws once and rewrites only the countdown; a test
  fails if it ever clears the screen while waiting.
- New keys: `d` views the diff, `l` opens a failed check's log, `b` opens the
  PR, `u` undoes your edit, `j`/`k` scroll. Your edit is marked.
- A key pressed as the popup opens (you were typing elsewhere) can't answer it.
- `make check` runs the popup on a throwaway tmux server (`tests/approve.sh`),
  with a fake gh: nothing reaches GitHub.

## v2.2.0 -- 2026-11-02

- **A clearer approval popup**: who asks (the agent's name from MCP), what
  it wants as one sentence, what's at stake, the agent's reason (a new
  optional `why` on `pr_comment`, `pr_review` and `pr_merge`), and for a
  merge the commits that land and what follows. A countdown shows when no
  answer becomes a no.
- **The merge screen** says first whether the PR is ready to merge, and
  shows what follows a merge (branch deletion, stacked PRs moving to the
  base).
- Fixed: an agent's merge with the merge-commit method was shown as
  "merge-merge".

## v2.1.1 -- 2026-10-27

- ShellCheck clean again (the merge tool builds its gh flags as an array).

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
