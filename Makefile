# System-wide or packaged install:  make install [PREFIX=/usr/local] [DESTDIR=]
# Per-user, without make:            ./install.sh
PREFIX ?= /usr/local
BINDIR  = $(DESTDIR)$(PREFIX)/bin
SHARE   = $(DESTDIR)$(PREFIX)/share

.PHONY: install uninstall lint check

install:
	install -Dm755 bin/sangam $(BINDIR)/sangam
	install -Dm644 assets/icon.png $(SHARE)/sangam/icon.png
	install -Dm644 README.md $(SHARE)/doc/sangam/README.md
	install -Dm644 CHANGELOG.md $(SHARE)/doc/sangam/CHANGELOG.md
	install -Dm644 LICENSE $(SHARE)/licenses/sangam/LICENSE

uninstall:
	rm -f $(BINDIR)/sangam
	rm -rf $(SHARE)/sangam $(SHARE)/doc/sangam $(SHARE)/licenses/sangam

# What CI runs.
lint:
	shellcheck -S warning bin/sangam sangam.tmux install.sh

check: lint
	bash -n bin/sangam
	./bin/sangam --version
	./bin/sangam --help >/dev/null
