# Changelog

Newest first.

## v1.0.0 -- 2026-10-19

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
