# tmux-gh-pr

A pull request popup for tmux: read, review, merge and close GitHub pull
requests without leaving the terminal or opening the browser, from any
folder.

`prefix G` opens it; `prefix G` again (or `q`) closes it.

- **Sections, like gh-dash.** Each is a GitHub search across all repos,
  run as one of your `gh` accounts, so work and personal PRs sit side by
  side. Opened inside a GitHub repo, a tab for that repo is added too.
- **Everything in one place.** An overview of each PR (checks, reviews,
  labels, files, description, activity), the diff, the checks (failed
  logs full screen) and the comments.
- **Act on it.** Merge through a panel that knows what the PR needs
  (squash with an editable title, update the branch, auto-merge, admin
  merge, mark ready), approve, request changes, comment, close/reopen,
  check out, toggle draft, copy the link.
- **Vim-style keys.** It opens in normal mode: `j`/`k` move, `h`/`l`
  switch sections, `/` filters, `?` shows every key.

Part of [Vayu](https://github.com/Theyashsawarkar/vayu), a keyboard-driven
Arch Linux desktop, but it works on any tmux setup on its own.

## Requirements

- tmux 3.3+ (popups with titles)
- [`gh`](https://cli.github.com/), signed in (`gh auth login`; sign in
  to several accounts to switch between them with `u`)
- [`fzf`](https://github.com/junegunn/fzf) 0.63+
- `jq`, bash 4+
- Optional: `notify-send` for notifications (else tmux messages);
  `wl-copy`, `xclip` or `pbcopy` for copying links (else tmux's buffer)

## Install

### With [TPM](https://github.com/tmux-plugins/tpm)

Add to `~/.tmux.conf` (or `~/.config/tmux/tmux.conf`), above TPM's `run`
line:

```tmux
set -g @plugin 'Theyashsawarkar/tmux-gh-pr'
```

then `prefix I` to install.

### Manually

```sh
git clone https://github.com/Theyashsawarkar/tmux-gh-pr ~/.tmux/plugins/tmux-gh-pr
```

and add to your tmux config:

```tmux
run-shell ~/.tmux/plugins/tmux-gh-pr/gh-pr.tmux
```

Reload tmux (`tmux source-file ~/.tmux.conf`).

## Options

Set them before TPM's `run` line (or the `run-shell` above).

| Option | Default | What it does |
|---|---|---|
| `@gh-pr-key` | `G` | Key after the prefix that opens and closes the popup; `none` binds nothing |
| `@gh-pr-width` | `90%` | Popup width |
| `@gh-pr-height` | `88%` | Popup height |
| `@gh-pr-title` | ` pull requests ` | Popup title |
| `@gh-pr-launcher` | (unset) | Your own popup command instead of `display-popup`; it gets display-popup's arguments appended (`-E -d DIR -T TITLE CMD`), tmux formats expanded |

Example, a custom key and a popup helper of your own:

```tmux
set -g @gh-pr-key 'P'
set -g @gh-pr-launcher "~/.tmux/scripts/popup.sh '#{client_name}'"
```

## Sections

Sections live in `~/.config/gh-pr/sections`, one per line:

```
name | account | GitHub search
Review requested |                 | review-requested:@me
My PRs           |                 | author:@me
Work repo        | my-work-account | repo:acme/api
```

- `account` is a `gh` account (`gh auth status`); empty means the active
  one.
- The search is anything GitHub search takes; `is:pr` and the
  open/merged/closed state are added for you. Several `repo:` filters in
  one search are OR'ed.
- On first run the file is created with three sections: Review
  requested, My PRs and Involved.
  Edit it with `E`, or add / edit / delete / move sections from the popup
  with `S`.

## Keys

| Key | Action |
|---|---|
| `j` / `k`, `g` / `G` | Next / previous PR, first / last |
| `h` / `l` | Previous / next section |
| `1` `2` `3` `4`, `Tab` | Overview, diff, checks, comments; cycle them |
| `J` / `K`, `Ctrl+d` / `Ctrl+u` | Scroll the preview |
| `Enter` | Current view full screen (failed check logs in checks) |
| `/` | Filter the list (`Enter` or `Esc` back to normal mode) |
| `s` | Search GitHub within the section (`author:x label:y`...) |
| `f` / `F` | Cycle open / merged / closed / all; toggle open ↔ all |
| `u` | Switch account (all, then each signed-in account) |
| `R` | Reload from GitHub |
| `S` / `E` | Manage sections / edit the sections file |
| `m` | Merge panel |
| `a` / `r` / `c` | Approve / request changes / comment |
| `x` | Close (or reopen) |
| `o` | Check out the PR's branch (inside a clone of its repo) |
| `d` | Toggle draft / ready for review |
| `y` / `b` | Copy the link / open in the browser |
| `?` | Show every key |
| `q`, `Esc`, `prefix G` | Close the popup |

The script's header has every key as a `# keybind:` line, which Vayu's
keybinding search reads.

## How it works

The popup runs its own small tmux session (`gh-prs-<pid>`) with a
3-line strip of section tabs on top and fzf below, so the tabs can span
both the list and the preview. Pressing the popup's key inside it kills
that session, which closes the popup. Each section is one GraphQL search
(CI and review state included), fetched in the background and cached in
`~/.cache/gh-pr`, so switching sections is instant.

## License

MIT
