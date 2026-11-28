#!/usr/bin/env python3
"""Builds this project's website (GitHub Pages, served from docs/) from
its own README.md, CHANGELOG.md and docs/adr/*.md, with the details in
site.toml. Run it after changing any of those; CI fails when docs/ is
out of date.

    python3 scripts/build-site.py           # write docs/
    python3 scripts/build-site.py --check   # exit 1 if docs/ would change

site.toml may name an interactive demo (demo = "site/try.html"): it is
copied to docs/try.html, and the nav and the hero link to it.

Standard library only. The same file lives in every repository of the
family (Vayu's tools): change it in one, copy it to all.
"""
import html
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")
GH = "https://github.com/Theyashsawarkar"
# Every tool's site has its own address: https://<tool>.theyashsawarkar.dev/
# (a CNAME record per tool, and docs/CNAME, which this writes).
DOMAIN = "theyashsawarkar.dev"


def home(n):
    return f"https://{n}.{DOMAIN}/"


# The family: every project with a site like this one.
FAMILY = [
    ("Desktop", [("vayu", "वायु", "the keyboard-driven Wayland desktop")]),
    ("Apps", [("kosha", "कोश", "package manager"), ("nada", "नाद", "music player"),
              ("drishya", "दृश्य", "video player"), ("darshan", "दर्शन", "document viewer"),
              ("sangam", "संगम", "pull requests in the terminal"),
              ("narada", "नारद", "mail and chat in the terminal"), ("pattan", "पत्तन", "ports and tunnels"),
              ("nauka", "नौका", "Docker in the terminal"), ("vaikhari", "वैखरी", "posts to X and LinkedIn"),
              ("dvarapala", "द्वारपाल", "commands for AI agents, approved"), ("pramana", "प्रमाण", "password prompts"),
              ("vesha", "वेष", "Claude Code accounts"), ("vishvakarma", "विश्वकर्मा", "skills for every AI agent"),
              ("sutradhar", "सूत्रधार", "browser hands for AI agents"),
              ("pranali", "प्रणाली", "one pipe from agents to tools"),
              ("ekatva", "एकत्व", "phone and laptop, linked"), ("vagdevi", "वाग्देवी", "book reader for Android"),
              ("varna", "वर्ण", "theme engine"), ("vinyasa", "विन्यास", "settings"),
              ("vyakarana", "व्याकरण", "key grammar")]),
    ("Vyom", [("vyom", "व्योम", "panels runtime")]),
    ("Vyom tools", [("dvara", "द्वार", "apps"), ("ganit", "गणित", "calculator"), ("smriti", "स्मृति", "clipboard"),
                    ("bhava", "भाव", "emoji"), ("tarang", "तरंग", "Wi‑Fi"), ("setu", "सेतु", "Bluetooth"),
                    ("doot", "दूत", "phone"), ("patra", "पात्र", "Docker"), ("akashvani", "आकाशवाणी", "notifications"),
                    ("raga", "राग", "YouTube"), ("mudra", "मुद्रा", "keybindings"), ("urja", "ऊर्जा", "battery"),
                    ("vishram", "विश्राम", "power menu"), ("kendra", "केन्द्र", "quick settings"),
                    ("darpana", "दर्पण", "phone, mirrored")]),
]
# Each tool's signature colour (site.toml "color"): Vayu's Spatial hues.
COLORS = {"rosewater": "#f6e1d8", "mauve": "#c9b6f2", "red": "#ff9389", "peach": "#f7b07d", "yellow": "#f3d47f",
          "green": "#8ee2a6", "teal": "#82ddd5", "sky": "#8fd6ec", "sapphire": "#7cc3ec", "blue": "#93c4ff", "lavender": "#b8c2ff",
          "pink": "#f4b4cc", "rose": "#f4b4cc"}


# ===================================================================== markdown
def slug(text):
    s = re.sub(r"<[^>]+>", "", text).lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.U)
    return re.sub(r"[\s]+", "-", s).strip("-")


def inline(text, link_map):
    """Inline markdown: code, images, links, bold, italics. HTML passes through."""
    codes = []

    def keep_code(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"
    t = re.sub(r"`([^`]+)`", keep_code, text)

    def img(m):
        return f'<img alt="{html.escape(m.group(1), quote=True)}" src="{link_map(m.group(2))}" loading="lazy">'
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", img, t)

    def link(m):
        return f'<a href="{link_map(m.group(2))}">{m.group(1)}</a>'
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\"'=/])(https?://[^\s<)]+[^\s<).,:;])", r'<a href="\1">\1</a>', t) if "<a " not in t else t
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], t)


def markdown(md, link_map=lambda u: u, toc=None, shift=0):
    """A small Markdown renderer: headings, paragraphs, lists (nested by
    indent), fenced code, tables, blockquotes, raw HTML blocks."""
    lines = md.splitlines()
    out, i = [], 0

    def para(buf):
        if buf:
            out.append("<p>" + inline(" ".join(x.strip() for x in buf), link_map) + "</p>")
    buf = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            para(buf), buf.clear()
            lang = line[3:].strip()
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(f'<pre class="code" data-lang="{html.escape(lang)}"><code>{html.escape(chr(10).join(code))}</code></pre>')
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            para(buf), buf.clear()
            level = min(6, len(m.group(1)) + shift)
            text = inline(m.group(2).strip(), link_map)
            sid = slug(m.group(2))
            if toc is not None and level in (2, 3):
                toc.append((level, sid, re.sub(r"<[^>]+>", "", text)))
            out.append(f'<h{level} id="{sid}"><a class="anchor" href="#{sid}">#</a>{text}</h{level}>')
            i += 1
            continue
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            para(buf), buf.clear()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = lambda r: [c.strip() for c in re.split(r"(?<!\\)\|", r.strip().strip("|"))]
            head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
            t = ['<div class="table"><table><thead><tr>'] + [f"<th>{inline(c, link_map)}</th>" for c in head] + ["</tr></thead><tbody>"]
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c.replace(chr(92) + '|', '|'), link_map)}</td>" for c in r) + "</tr>")
            out.append("".join(t) + "</tbody></table></div>")
            continue
        if line.startswith(">"):
            para(buf), buf.clear()
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i][1:].lstrip())
                i += 1
            out.append("<blockquote>" + markdown("\n".join(q), link_map) + "</blockquote>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            para(buf), buf.clear()
            items = []
            while i < len(lines) and (re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) or
                                      (lines[i].startswith("  ") and lines[i].strip() and items)):
                if re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    ordered = bool(re.match(r"^\s*\d+\.", lines[i]))
                    items.append([indent, ordered, re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i])])
                else:
                    items[-1][2] += " " + lines[i].strip()
                i += 1
            out.append(_list(items, link_map))
            continue
        if re.match(r"^\s*<(p|div|picture|table|details|img|br|hr|h\d)\b", line) or line.strip().startswith("<!--"):
            para(buf), buf.clear()
            block = []
            while i < len(lines) and lines[i].strip():
                block.append(lines[i])
                i += 1
            raw = "\n".join(block)
            raw = re.sub(r'(src|srcset|href)="(?!https?:|#|mailto:)([^"]+)"', lambda m: f'{m.group(1)}="{link_map(m.group(2))}"', raw)
            out.append(raw)
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            para(buf), buf.clear()
            out.append("<hr>")
            i += 1
            continue
        if not line.strip():
            para(buf), buf.clear()
        else:
            buf.append(line)
        i += 1
    para(buf)
    return "\n".join(out)


def _list(items, link_map, base=None):
    if not items:
        return ""
    base = items[0][0] if base is None else base
    tag = "ol" if items[0][1] else "ul"
    out, j = [f"<{tag}>"], 0
    while j < len(items):
        indent, _, text = items[j]
        sub = []
        k = j + 1
        while k < len(items) and items[k][0] > indent:
            sub.append(items[k])
            k += 1
        out.append("<li>" + inline(text, link_map) + (_list(sub, link_map) if sub else "") + "</li>")
        j = k
    out.append(f"</{tag}>")
    return "".join(out)


# ===================================================================== pages
CSS = """
/* Vayu's Spatial look (the same as vayu.theyashsawarkar.dev): graphite
   glass floating over the tool's own screenshot, blurred far out of focus;
   very round; where you are is a near-white pill or brighter glass; no
   glows; colour only where it means something. The tool's own colour
   (--tool) is only its signature: the release dots. */
:root{--crust:#0e0f11;--mantle:#141518;--base:#1b1c20;--s0:#2a2c31;--s1:#3a3c42;--ov0:#6a6d74;--ov1:#80838a;
--sub0:#b3b5ba;--sub1:#cdcfd3;--text:#f2f2f0;--accent:#f4f4f2;--green:#8ee2a6;--peach:#f7b07d;--red:#ff9389;--blue:#93c4ff;--yellow:#f3d47f;
--glass:rgba(52,54,60,.44);--hi:rgba(255,255,255,.09);--rim:rgba(255,255,255,.13);--lit:inset 0 1px 0 rgba(255,255,255,.15);
--float:0 30px 70px -24px rgba(0,0,0,.7),0 2px 6px rgba(0,0,0,.25);--blur:blur(28px) saturate(160%);
--ui:"Inter","Adwaita Sans",system-ui,sans-serif;--mono:"JetBrains Mono","JetBrainsMono Nerd Font",ui-monospace,monospace;
--sa:"Tiro Devanagari Sanskrit","Noto Serif Devanagari",serif;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:96px}
body{margin:0;min-height:100vh;background:var(--crust);color:var(--text);font:16px/1.65 var(--ui);-webkit-font-smoothing:antialiased;font-feature-settings:"cv11","ss01"}
/* the backdrop: the tool's screenshot, out of focus, fading to graphite */
.backdrop{position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none}
.backdrop:before{content:"";position:absolute;inset:-12%;background:center/cover no-repeat;filter:blur(64px) saturate(1.25) brightness(.62);transform:translateZ(0)}
.backdrop:after{content:"";position:absolute;inset:0;background:linear-gradient(to bottom,rgba(14,15,17,.25),rgba(14,15,17,.8) 60%,var(--crust))}
.backdrop.none:before{background:radial-gradient(60% 50% at 50% 0%,color-mix(in srgb,var(--tool) 22%,transparent),transparent 70%);filter:none}
.sub .backdrop:after{background:linear-gradient(to bottom,rgba(14,15,17,.55),rgba(14,15,17,.93) 45%,var(--crust))}
a{color:var(--accent);text-decoration:underline;text-decoration-color:rgba(244,244,242,.3);text-underline-offset:3px}
a:hover{text-decoration-color:currentColor}
code{font:.86em var(--mono);background:rgba(255,255,255,.07);padding:.14em .45em;border-radius:7px;color:var(--sub1)}
kbd{display:inline-block;min-width:1.7em;padding:.05em .45em;font:500 .8em/1.6 var(--mono);text-align:center;color:var(--text);background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-bottom-width:2px;border-radius:8px}
img{max-width:100%;height:auto}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:10px}
.glass{background:var(--glass);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);border:1px solid var(--rim);box-shadow:var(--lit),var(--float)}
/* nav: a floating glass capsule; the page you're on is the near-white pill */
.top{position:sticky;top:0;z-index:20;padding:14px 24px 0}
.top .in{max-width:1180px;margin:0 auto;padding:6px 6px 6px 10px;display:flex;align-items:center;gap:18px;border-radius:999px;
background:rgba(30,31,35,.62);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);border:1px solid var(--rim);box-shadow:var(--lit),0 18px 40px -18px rgba(0,0,0,.7)}
.brand{display:flex;align-items:center;gap:10px;font-weight:650;font-size:16px;color:var(--text);text-decoration:none;padding:2px 6px 2px 2px;border-radius:999px}
.brand img{width:30px;height:30px;border-radius:10px}.brand small{font:400 14px var(--sa);color:var(--ov1)}
.top nav{display:flex;gap:2px;margin-left:auto}
.top nav a{color:var(--sub0);padding:7px 15px;border-radius:999px;font-size:14.5px;font-weight:500;text-decoration:none;white-space:nowrap;transition:background-color .15s,color .15s}
.top nav a:hover{background:rgba(255,255,255,.08);color:var(--text)}
.top nav a.on{background:var(--accent);color:var(--crust);font-weight:600}
.top nav a.gh{color:var(--text);background:rgba(255,255,255,.09);box-shadow:inset 0 1px 0 rgba(255,255,255,.1);margin-left:4px}.top nav a.gh:hover{background:rgba(255,255,255,.15)}
/* hero: the logo, the name, the verse, then the tool itself */
.hero{max-width:860px;margin:0 auto;padding:76px 24px 0;text-align:center}
.hero .logo{width:104px;height:104px;border-radius:28px;box-shadow:0 26px 50px -18px rgba(0,0,0,.8),0 0 0 1px rgba(255,255,255,.08)}
.hero h1{font-size:clamp(46px,7vw,76px);line-height:1;margin:26px 0 10px;letter-spacing:-.04em;font-weight:700}
.hero .sa{font-size:16px;color:var(--sub0)}.hero .sa b{font:400 21px var(--sa);color:var(--sub1);margin-right:6px}.hero .sa i{font-style:normal;color:var(--ov1)}
.hero p.lead{font-size:19.5px;line-height:1.55;color:var(--sub1);max-width:34em;margin:22px auto 0;text-wrap:pretty}
.hero .shloka{margin:34px auto 0;max-width:600px}
.hero .shloka p{margin:0;font:400 21px/1.55 var(--sa);color:var(--text)}
.hero .shloka figcaption{margin-top:10px;font-size:14.5px;color:var(--sub0);text-wrap:pretty}.hero .shloka cite{display:block;margin-top:2px;color:var(--ov1);font-style:normal;font-size:13px}
.cta{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:32px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 22px;border-radius:999px;font-weight:600;font-size:15px;color:var(--text);
background:rgba(255,255,255,.08);border:1px solid var(--rim);box-shadow:var(--lit);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);text-decoration:none;transition:background-color .15s}
.btn:hover{background:rgba(255,255,255,.14)}
.btn.primary{background:var(--accent);color:var(--crust);border-color:transparent;box-shadow:0 10px 30px -12px rgba(0,0,0,.6)}.btn.primary:hover{background:#fff}
.meta{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;margin-top:20px;font-size:13.5px;color:var(--ov1)}
.meta span{padding:4px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.09)}.meta b{color:var(--sub1);font-weight:600}
.shot{max-width:1180px;margin:56px auto 0;padding:0 24px;display:flex;gap:22px;justify-content:center;align-items:flex-start}
.shot img{display:block;border-radius:26px;border:1px solid var(--rim);background:var(--base);box-shadow:0 0 0 6px rgba(255,255,255,.04),0 50px 110px -30px rgba(0,0,0,.85)}
.shot.many img{flex:1 1 0;min-width:0;max-width:300px;border-radius:30px}
.shot figcaption{display:none}
/* layout: a glass "On this page" panel beside the article */
.wrap{max-width:1180px;margin:0 auto;padding:72px 24px 40px;display:grid;grid-template-columns:240px minmax(0,1fr);gap:56px}
.sub .wrap{padding-top:48px}
.wrap.solo{grid-template-columns:minmax(0,1fr);max-width:900px}.wrap.solo article{max-width:none}
.adrmeta+h2{border-top:0;padding-top:0;margin-top:10px;font-size:36px;letter-spacing:-.03em}
article>h2:first-child{font-size:36px;letter-spacing:-.03em}
.toc{position:sticky;top:92px;align-self:start;max-height:calc(100vh - 112px);overflow:auto;scrollbar-width:thin;scrollbar-color:rgba(255,255,255,.15) transparent;
padding:14px 8px 10px;border-radius:24px;background:rgba(30,31,35,.6);-webkit-backdrop-filter:var(--blur);backdrop-filter:var(--blur);border:1px solid var(--rim);box-shadow:var(--lit),0 24px 50px -24px rgba(0,0,0,.7)}
.toc:empty{display:none}
.toc b{display:block;font-size:13px;font-weight:600;color:var(--ov1);margin:0 12px 6px}
.toc a{display:block;color:var(--sub0);padding:6px 12px;border-radius:14px;font-size:13.5px;line-height:1.4;text-decoration:none;transition:background-color .15s,color .15s}
.toc a.l3{padding:4px 12px 4px 24px;font-size:12.5px;color:var(--ov1)}
.toc a:hover{color:var(--text);background:rgba(255,255,255,.06)}
.toc a.on{color:var(--text);background:rgba(255,255,255,.11);box-shadow:inset 0 1px 0 rgba(255,255,255,.12),inset 0 0 0 1px rgba(255,255,255,.08)}
article{min-width:0;max-width:820px}
article h2{font-size:28px;line-height:1.2;letter-spacing:-.022em;margin:64px 0 14px;padding-top:28px;border-top:1px solid rgba(255,255,255,.08);font-weight:650}
article>h2:first-child,article>section:first-child h2{margin-top:0;padding-top:0;border-top:0}
article h3{font-size:19px;margin:34px 0 10px;font-weight:600;letter-spacing:-.01em}article h4{font-size:16px;margin:24px 0 8px;color:var(--sub1)}
article p,article li{color:var(--sub1);overflow-wrap:anywhere}article strong{color:var(--text);font-weight:600}
article .anchor{opacity:0;margin-left:-22px;width:22px;display:inline-block;color:var(--ov0);text-decoration:none}
article h2:hover .anchor,article h3:hover .anchor{opacity:1}
article ul,article ol{padding-left:22px}article li{margin:5px 0}article li::marker{color:var(--ov0)}
article img{border-radius:22px;border:1px solid var(--rim);box-shadow:0 30px 70px -28px rgba(0,0,0,.85)}
article p[align=center]{text-align:center}article p[align=center] img{margin:6px 0}
article blockquote{margin:22px 0;padding:14px 20px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);box-shadow:inset 0 1px 0 rgba(255,255,255,.06);border-radius:20px}
article blockquote p{margin:.2em 0;color:var(--sub0)}
pre.code{position:relative;background:rgba(10,11,13,.6);border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:18px 20px;overflow:auto;font:13.5px/1.65 var(--mono);color:var(--sub1)}
pre.code code{background:none;padding:0;font-size:inherit;color:inherit}
pre.code .copy{position:absolute;top:10px;right:10px;font:600 12.5px var(--ui);padding:5px 13px;border-radius:999px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.08);color:var(--sub1);cursor:pointer;opacity:0;transition:opacity .15s,background-color .15s}
pre.code:hover .copy,pre.code .copy:focus-visible{opacity:1}pre.code .copy:hover{background:var(--accent);color:var(--crust)}
pre.code .copy.done{background:var(--green);color:var(--crust);border-color:transparent;opacity:1}
.table{overflow:auto;margin:18px 0 22px;border:1px solid rgba(255,255,255,.09);border-radius:20px;background:rgba(255,255,255,.035)}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th{text-align:left;color:var(--ov1);font-size:13px;font-weight:600;padding:12px 16px;border-bottom:1px solid rgba(255,255,255,.08);white-space:nowrap}
td{padding:11px 16px;border-top:1px solid rgba(255,255,255,.05);color:var(--sub1);vertical-align:top}tbody tr:first-child td{border-top:0}
td code{white-space:nowrap}
/* changelog: each release a glass card on a thread */
.release{position:relative;margin:0 0 18px 22px;padding:22px 26px 10px;border-radius:24px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);box-shadow:inset 0 1px 0 rgba(255,255,255,.07)}
.release:before{content:"";position:absolute;left:-23px;top:0;bottom:-18px;width:1px;background:rgba(255,255,255,.1)}
.release:after{content:"";position:absolute;left:-28px;top:30px;width:11px;height:11px;border-radius:50%;background:var(--tool);box-shadow:0 0 0 4px var(--crust)}
.release:last-child:before{bottom:auto;height:30px}
.release h2{margin:0 0 6px;padding:0;border:0;font-size:22px;display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 12px}
.release h2 .date{font:500 13.5px var(--mono);color:var(--ov1)}
.release .tag{font:600 12.5px var(--ui);padding:3px 11px;border-radius:999px;background:rgba(255,255,255,.08);color:var(--sub1);text-decoration:none;margin-left:auto}
.release .tag:hover{background:rgba(255,255,255,.14);color:var(--text)}
.release h3{font-size:15px;color:var(--sub0);margin:18px 0 6px}
/* decisions */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,100%),1fr));gap:14px;margin:22px 0}
.card{display:block;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);box-shadow:inset 0 1px 0 rgba(255,255,255,.07);border-radius:24px;padding:20px 22px;color:var(--text);text-decoration:none;transition:background-color .15s,border-color .15s}
.card:hover{background:var(--hi);border-color:rgba(255,255,255,.18)}
.card .n{font:500 12.5px var(--mono);color:var(--ov1);display:flex;gap:8px;align-items:center}.card h3{margin:10px 0 6px;font-size:17px;line-height:1.35}.card p{margin:0;color:var(--sub0);font-size:14px}
.status{display:inline-block;font:600 12px var(--ui);padding:2px 10px;border-radius:999px;background:rgba(142,226,166,.14);color:var(--green)}
.status.superseded,.status.deprecated{background:rgba(247,176,125,.14);color:var(--peach)}.status.proposed{background:rgba(147,196,255,.14);color:var(--blue)}
.adrmeta{display:flex;gap:10px;align-items:center;font:13px var(--mono);color:var(--ov1);margin:0 0 6px}
.back{display:flex;gap:10px;margin-top:44px}.back a{text-decoration:none}
/* footer: the family, in one glass panel */
footer{max-width:1180px;margin:60px auto 0;padding:0 24px 40px}
footer .in{display:grid;grid-template-columns:1fr 2.4fr 1fr 2fr;gap:28px;padding:30px 30px 26px;border-radius:28px}
footer h4{margin:0 0 10px;font-size:14px;font-weight:600;color:var(--text)}
footer .list{display:grid;gap:0 18px}footer .g2 .list{grid-template-columns:1fr 1fr}
footer a{display:flex;gap:8px;align-items:baseline;color:var(--sub0);font-size:14px;padding:3px 8px;margin:0 -8px;border-radius:10px;text-decoration:none;min-width:0}
footer a:hover{color:var(--text);background:rgba(255,255,255,.06)}footer a span{color:var(--ov0);font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
footer a.me{color:var(--crust);background:var(--accent);font-weight:600}footer a.me span{color:rgba(14,15,17,.6)}
footer .bottom{display:flex;flex-wrap:wrap;gap:6px 18px;padding:22px 6px 0;color:var(--ov1);font-size:13.5px}
footer .bottom a{display:inline;padding:0;margin:0;font-size:13.5px;color:var(--sub0);text-decoration:underline;text-decoration-color:rgba(255,255,255,.25)}footer .bottom a:hover{background:none}
@media(max-width:1000px){footer .in{grid-template-columns:1fr 1fr}}
@media(max-width:900px){.wrap{grid-template-columns:1fr;gap:28px}.toc{display:none}}
@media(max-width:640px){.top{padding:10px 10px 0}.top .in{gap:6px;padding-left:6px}.brand small,.brand span{display:none}
.top nav{overflow-x:auto;scrollbar-width:none}.top nav::-webkit-scrollbar{display:none}.top nav a{padding:7px 11px;font-size:14px}.top nav a.hide{display:none}
.hero{padding:44px 16px 0}.hero .logo{width:84px;height:84px;border-radius:23px}.hero p.lead{font-size:17px}.hero .shloka p{font-size:18.5px}
.shot{margin-top:36px;padding:0 16px;gap:10px}.shot img{border-radius:16px}.shot.many img{border-radius:18px}
.wrap{padding:52px 16px 32px}article h2{font-size:23px}.release{margin-left:14px;padding:18px 18px 8px}.release:before{left:-15px}.release:after{left:-20px}
footer{padding:0 16px 32px}footer .in{grid-template-columns:1fr;padding:22px 20px}footer .g2 .list{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
"""
JS = """
document.querySelectorAll('pre.code').forEach(p=>{const b=document.createElement('button');b.className='copy';b.type='button';b.textContent='Copy';
b.onclick=()=>{navigator.clipboard.writeText(p.querySelector('code').innerText).then(()=>{b.textContent='Copied';b.classList.add('done');setTimeout(()=>{b.textContent='Copy';b.classList.remove('done')},1400)})};p.appendChild(b)});
const links=[...document.querySelectorAll('.toc a')];if(links.length){const hs=links.map(a=>document.getElementById(a.hash.slice(1))).filter(Boolean);
const on=()=>{let cur=hs[0];for(const h of hs){if(h.getBoundingClientRect().top<120)cur=h}links.forEach(a=>a.classList.toggle('on',cur&&a.hash==='#'+cur.id))};
addEventListener('scroll',on,{passive:true});on()}
"""


def page(meta, title, body, depth=0, active="", toc=None, hero="", shot=""):
    up = "../" * depth
    name = meta["name"]
    tool = COLORS.get(meta.get("color", "mauve"), "#c9b6f2")
    nav = [("Overview", f"{up}index.html", "home"), ("Changelog", f"{up}changelog.html", "changelog"),
           ("Decisions", f"{up}adr/index.html", "adr")]
    if meta.get("demo"):  # an interactive demo: try it in the browser
        nav.insert(1, ("Try it", f"{up}try.html", "try"))
    navhtml = "".join(f'<a href="{h}" class="{"on" if k == active else ""}{" hide" if k == "adr" else ""}">{t}</a>' for t, h, k in nav)
    navhtml += f'<a class="gh" href="{GH}/{name}">GitHub</a>'
    tochtml = ""
    if toc:
        tochtml = '<aside class="toc"><b>On this page</b>' + "".join(
            f'<a class="l{lvl}" href="#{s}">{html.escape(t)}</a>' for lvl, s, t in toc) + "</aside>"
    fam = []
    for group, items in FAMILY:
        links = []
        for it in items:
            n, what = it[0], it[2]
            url = it[3] if len(it) > 3 else home(n)
            me, cur = ("me", ' aria-current="page"') if n == name else ("", "")
            links.append(f'<a href="{url}" class="{me}"{cur}>{n} <span>{what}</span></a>')
        cls = " g2" if len(items) > 8 else ""
        fam.append(f'<div class="{cls.strip()}"><h4>{group}</h4><div class="list">{"".join(links)}</div></div>')
    desc = html.escape(meta["tagline"], quote=True)
    # set here, in the page, so the address is relative to the page (a url() in a custom property resolves against site.css)
    shotvar = f'.backdrop:before{{background-image:url("{up}{shot}")}}' if shot else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{desc}">
<meta name="theme-color" content="#0e0f11">
<link rel="icon" href="{up}assets/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Tiro+Devanagari+Sanskrit&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/site.css">
<style>:root{{--tool:{tool}}}{shotvar}</style>
</head>
<body class="{"home" if active == "home" else "sub"}">
<div class="backdrop{"" if shot else " none"}" aria-hidden="true"></div>
<header class="top"><div class="in">
<a class="brand" href="{up}index.html"><img src="{up}assets/logo.svg" alt=""><span>{name} <small>{meta.get("sanskrit", "")}</small></span></a>
<nav>{navhtml}</nav></div></header>
{hero}
<div class="wrap{"" if tochtml else " solo"}">{tochtml}<article>
{body}
</article></div>
<footer><div class="in glass">{''.join(fam)}</div>
<div class="bottom"><span>{name} is free software under the MIT license.</span><a href="{GH}/{name}">Source</a><a href="{GH}/{name}/issues">Report a problem</a><a href="{up}changelog.html">Changelog</a><span>Part of <a href="{home('vayu')}">Vayu</a>.</span></div></footer>
<script>{JS}</script>
</body>
</html>
"""


def versions(changelog):
    """[(version, date, body_md)] from a Keep-a-Changelog style file."""
    out = []
    parts = re.split(r"(?m)^## ", changelog)
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        m = re.match(r"\s*(v?[\d.]+|Unreleased)\s*(?:--|—|-)?\s*(.*)$", head.strip())
        ver, date = (m.group(1), m.group(2).strip()) if m else (head.strip(), "")
        out.append((ver, date, body.strip()))
    return out


def adr_meta(md):
    title = re.search(r"(?m)^#\s+(.+)$", md)
    status = re.search(r"(?mi)^\*\*Status:?\*\*:?\s*(.+)$", md) or re.search(r"(?mi)^Status:\s*(.+)$", md)
    date = re.search(r"(?mi)^\*\*Date:?\*\*:?\s*(.+)$", md)
    ctx = re.search(r"(?ms)^## Context\s*\n+(.+?)(\n\n|\Z)", md)
    return (title.group(1).strip() if title else "Decision", status.group(1).strip() if status else "Accepted",
            date.group(1).strip() if date else "", re.sub(r"\s+", " ", ctx.group(1)).strip() if ctx else "")


def build():
    meta = tomllib.load(open(os.path.join(ROOT, "site.toml"), "rb"))
    name = meta["name"]
    files = {}

    def link_map(u):
        if u.startswith(("http://", "https://", "#", "mailto:")):
            return u
        if u.startswith("assets/"):
            return u
        if u.endswith(".md") and not u.startswith("docs/adr"):
            if u == "CHANGELOG.md":
                return "changelog.html"
            return f"{GH}/{name}/blob/main/{u}"
        if u.startswith("docs/adr/") and u.endswith(".md"):
            return "adr/" + os.path.basename(u)[:-3] + ".html"
        return f"{GH}/{name}/blob/main/{u}"

    # ---- assets: logo, banners, screenshots referenced by the README
    readme = open(os.path.join(ROOT, "README.md")).read()
    logo = meta.get("logo", "assets/logo.svg")
    files["assets/logo.svg"] = open(os.path.join(ROOT, logo), "rb").read()
    copies = set()
    copies |= set(re.findall(r'(?:src|srcset)="(assets/[^"]+)"', readme)) | set(re.findall(r"\]\((assets/[^)]+)\)", readme))
    for rel in sorted(copies):
        src = os.path.join(ROOT, rel)
        if os.path.exists(src):
            files[os.path.join("assets", rel[len("assets/"):])] = open(src, "rb").read()
    files["assets/site.css"] = CSS.strip().encode()
    # GitHub Pages serves the site at its own address (a CNAME record points it there).
    files["CNAME"] = f"{name}.{DOMAIN}\n".encode()

    # ---- home: the README without its banner/badges block (the hero has the shloka)
    readme = re.sub(r"(?s)<!-- identity -->.*?<!-- /identity -->\s*", "", readme)
    body_md = readme
    stripped = re.sub(r"(?s)^(\s*<p align=\"center\">.*?</p>\s*)+", "", readme)
    # The first block of screenshots above the first section is the hero's
    # picture (and, blurred, the page's backdrop); the rest stay in the page.
    blocks = re.findall(r'(?s)<p align="center">(?:(?!</p>).)*?assets/screenshots/.*?</p>', readme.split("\n## ")[0])
    hero_imgs = re.findall(r'<img[^>]*>', blocks[0]) if blocks else []
    hero_imgs = [i for i in hero_imgs if "assets/screenshots/" in i]
    rest = [b for b in blocks[1:] if b not in stripped]
    if blocks and blocks[0] in stripped:
        stripped = stripped.replace(blocks[0], "", 1)
    body_md = ("\n\n".join(rest) + "\n\n" + stripped) if rest else stripped
    body_md = re.sub(r"(?ms)^## Contents\s*\n.*?(?=^## )", "", body_md)
    toc = []
    body = markdown(body_md, link_map, toc)
    vers = versions(open(os.path.join(ROOT, "CHANGELOG.md")).read()) if os.path.exists(os.path.join(ROOT, "CHANGELOG.md")) else []
    latest = next((v for v, _, _ in vers if v[0].isdigit() or v.startswith("v")), "")
    latest = latest if latest.startswith("v") or not latest else "v" + latest
    adrs = sorted(f for f in os.listdir(os.path.join(ROOT, "docs", "adr")) if re.match(r"\d{4}-.+\.md$", f)) \
        if os.path.isdir(os.path.join(ROOT, "docs", "adr")) else []
    shloka = ""
    if meta.get("shloka"):
        verse = html.escape(meta["shloka"]).replace("\n", "<br>")
        shloka = (f'<figure class="shloka"><p lang="sa">{verse}</p><figcaption>{html.escape(meta.get("shloka_meaning", ""))} '
                  f'<cite>{html.escape(meta.get("shloka_source", ""))}</cite></figcaption></figure>\n')
    def attr(tag, a):
        m = re.search(a + r'="([^"]*)"', tag)
        return m.group(1) if m else ""
    shot_src = attr(hero_imgs[0], "src") if hero_imgs else ""
    shot_html = ""
    if hero_imgs:
        first, rest = ' fetchpriority="high"', ' loading="lazy"'
        imgs = "".join(f'<img src="{attr(t, "src")}" alt="{attr(t, "alt")}"{first if k == 0 else rest}>'
                       for k, t in enumerate(hero_imgs))
        shot_html = f'<figure class="shot{" many" if len(hero_imgs) > 1 else ""}">{imgs}</figure>'
    releases = len([v for v in vers if v[0] != 'Unreleased'])
    meta_row = [f"<span><b>{latest}</b> latest</span>" if latest else "<span>not released yet</span>"]
    if releases:
        meta_row.append(f"<span><b>{releases}</b> release{'s' if releases != 1 else ''}</span>")
    if adrs:
        meta_row.append(f"<span><b>{len(adrs)}</b> decision{'s' if len(adrs) != 1 else ''} recorded</span>")
    meta_row.append("<span><b>MIT</b> license</span>")
    hero = f"""<header class="hero">
<img class="logo" src="assets/logo.svg" alt="{name} logo" width="104" height="104">
<h1>{name}</h1>
<div class="sa"><b lang="sa">{meta.get("sanskrit", "")}</b> <i>“{html.escape(meta.get("meaning", ""))}”</i> · {html.escape(meta.get("kind", "open source"))}</div>
<p class="lead">{html.escape(meta["tagline"])}</p>
{shloka}<div class="cta">{'<a class="btn primary" href="try.html">Try it in your browser</a>' if meta.get("demo") else ""}<a class="btn{"" if meta.get("demo") else " primary"}" href="#install">Install</a><a class="btn" href="{GH}/{name}">Source on GitHub</a><a class="btn" href="changelog.html">What's new{(' in ' + latest) if latest else ''}</a></div>
<div class="meta">{"".join(meta_row)}</div>
</header>
{shot_html}"""
    if "install" not in {s for _, s, _ in toc}:
        hero = hero.replace('href="#install"', f'href="{GH}/{name}#install"')
    files["index.html"] = page(meta, f"{name} · {meta['tagline']}", body, 0, "home", toc, hero, shot_src).encode()

    # ---- changelog
    items = []
    ctoc = []
    for v, date, md in vers:
        sid = slug(v)
        tag = f'<a class="tag" href="{GH}/{name}/releases/tag/{v if v.startswith("v") else "v" + v}">Release notes</a>' if v != "Unreleased" else ""
        items.append(f'<section class="release"><h2 id="{sid}">{html.escape(v)}<span class="date">{html.escape(date)}</span>{tag}</h2>'
                     f"{markdown(md, lambda u: link_map(u).replace('changelog.html', '#'), None, 1)}</section>")
        ctoc.append((2, sid, v))
    intro = (f"<h2>Changelog</h2><p>Every change to {name}, newest first. Releases are git tags "
             f"(<a href=\"{GH}/{name}/tags\">all tags</a>, <a href=\"{GH}/{name}/releases\">GitHub releases</a>); "
             f"the source of this page is <a href=\"{GH}/{name}/blob/main/CHANGELOG.md\">CHANGELOG.md</a>.</p>")
    files["changelog.html"] = page(meta, f"Changelog · {name}", intro + "".join(items), 0, "changelog", ctoc, "", shot_src).encode()

    # ---- ADRs
    cards = []
    for f in adrs:
        md = open(os.path.join(ROOT, "docs", "adr", f)).read()
        title, status, date, ctx = adr_meta(md)
        num = f[:4]
        st = status.split()[0].lower().strip(".,")
        out_name = f[:-3] + ".html"
        md = re.sub(r"(?mi)^\*\*(Status|Date):?\*\*.*\n?", "", md)   # shown as the badge instead
        adr_body = markdown(md, lambda u: "../" + link_map(u) if not u.startswith(("http", "#")) and not u.endswith(".md") else
                            (os.path.basename(u)[:-3] + ".html" if re.match(r"\d{4}-", os.path.basename(u)) else link_map(u)), None)
        adr_body = adr_body.replace("<h1 ", f'<p class="adrmeta"><span class="status {st}">{html.escape(status)}</span> '
                                    f'<span>ADR {num}{" · " + html.escape(date) if date else ""}</span></p><h2 ', 1).replace("</h1>", "</h2>", 1)
        nav = f'<p class="back"><a class="btn" href="index.html">All decisions</a><a class="btn" href="{GH}/{name}/blob/main/docs/adr/{f}">Source</a></p>'
        files[os.path.join("adr", out_name)] = page(meta, f"ADR {num}: {title} · {name}", adr_body + nav, 1, "adr", None, "", shot_src).encode()
        card_title = re.sub(r"^\d+\.\s*", "", title)
        card_text = re.sub(r"[`*]", "", ctx)
        card_text = card_text[:180] + ("…" if len(card_text) > 180 else "")
        cards.append(f'<a class="card" href="{out_name}"><div class="n">ADR {num} · <span class="status {st}">{html.escape(status)}</span></div>'
                     f"<h3>{html.escape(card_title)}</h3><p>{html.escape(card_text)}</p></a>")
    adr_intro = (f"<h2>Architecture decisions</h2><p>Why {name} is built the way it is: each significant decision as a short "
                 "record (context, the decision, its consequences), in the "
                 "<a href=\"https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions\">ADR</a> format. "
                 "A decision is never edited away: a later one supersedes it. Sources: "
                 f"<a href=\"{GH}/{name}/tree/main/docs/adr\">docs/adr</a>.</p>")
    files[os.path.join("adr", "index.html")] = page(meta, f"Decisions · {name}", adr_intro + f'<div class="cards">{"".join(cards)}</div>', 1, "adr", None, "", shot_src).encode()
    # ---- the demo: a page of its own (site.toml demo = "path"), copied as is
    if meta.get("demo"):
        files["try.html"] = open(os.path.join(ROOT, meta["demo"]), "rb").read()
    files[".nojekyll"] = b""
    return files


def main():
    files = build()
    check = "--check" in sys.argv
    stale = []
    keep_md = {os.path.join("adr", f) for f in os.listdir(os.path.join(OUT, "adr"))} if os.path.isdir(os.path.join(OUT, "adr")) else set()
    for rel, data in files.items():
        path = os.path.join(OUT, rel)
        old = open(path, "rb").read() if os.path.exists(path) else None
        if old != data:
            stale.append(rel)
            if not check:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, "wb").write(data)
    # generated files that no longer exist (an ADR's html, an old screenshot)
    for dirpath, _, names in os.walk(OUT):
        for n in names:
            rel = os.path.relpath(os.path.join(dirpath, n), OUT)
            if rel not in files and not rel.endswith(".md") and rel not in keep_md - {r for r in keep_md if r.endswith(".html")}:
                stale.append(rel + " (remove)")
                if not check:
                    os.remove(os.path.join(dirpath, n))
    if check:
        if stale:
            print("docs/ is out of date; run python3 scripts/build-site.py:\n  " + "\n  ".join(stale))
            return 1
        print("docs/ is up to date")
        return 0
    print(f"docs/: {len(files)} files, {len(stale)} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
