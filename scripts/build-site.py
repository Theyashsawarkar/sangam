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
/* Vayu's Spatial look: graphite glass that floats, very round, colour only
   where it means something. The near-white accent is where you act (links,
   the main button); the tool's own colour (--tool) is only its signature:
   the logo's glow, the shloka's line, the release dots. */
:root{--crust:#0e0f11;--mantle:#141518;--base:#1b1c20;--s0:#2a2c31;--s1:#3a3c42;--ov0:#6a6d74;--ov1:#80838a;
--sub0:#b3b5ba;--sub1:#cdcfd3;--text:#f2f2f0;--accent:#f4f4f2;--green:#8ee2a6;--peach:#f7b07d;--red:#ff9389;--blue:#93c4ff;
--glass:rgba(255,255,255,.045);--rim:rgba(255,255,255,.10);--lit:inset 0 1px 0 rgba(255,255,255,.08);
--ui:"Inter","Segoe UI",system-ui,sans-serif;--mono:"JetBrains Mono","JetBrainsMono Nerd Font",ui-monospace,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:96px}
body{margin:0;background:var(--crust);color:var(--text);font:16px/1.65 var(--ui);-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:underline;text-decoration-color:rgba(244,244,242,.28);text-underline-offset:3px}
a:hover{text-decoration-color:var(--accent)}
code{font:.86em var(--mono);background:rgba(255,255,255,.07);padding:.14em .45em;border-radius:7px;color:var(--sub1)}
img{max-width:100%;height:auto}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:8px}
/* nav: a floating glass pill */
.top{position:sticky;top:12px;z-index:20;padding:0 16px}
.top .in{max-width:1240px;margin:0 auto;padding:8px 10px 8px 16px;display:flex;align-items:center;gap:22px;
border-radius:999px;background:rgba(27,28,32,.62);border:1px solid var(--rim);box-shadow:var(--lit),0 18px 40px rgba(0,0,0,.35);
backdrop-filter:blur(24px) saturate(1.5);-webkit-backdrop-filter:blur(24px) saturate(1.5)}
.brand{display:flex;align-items:center;gap:10px;font-weight:650;font-size:16.5px;color:var(--text);text-decoration:none}
.brand img{width:28px;height:28px;border-radius:9px}.brand small{font-weight:500;color:var(--ov1);font-size:13px}
.top nav{display:flex;gap:4px;margin-left:auto;flex-wrap:wrap}
.top nav a{color:var(--sub0);padding:6px 14px;border-radius:999px;font-size:14.5px;text-decoration:none}
.top nav a:hover{background:rgba(255,255,255,.07);color:var(--text)}
.top nav a.on{background:rgba(255,255,255,.14);color:var(--text);box-shadow:var(--lit)}
.top nav a.gh{background:var(--accent);color:var(--crust);font-weight:600}.top nav a.gh:hover{background:#fff}
/* hero: the tool's light in a dark room */
.hero{position:relative;overflow:hidden;margin-top:-64px;padding-top:64px}
.hero:before{content:"";position:absolute;inset:-30% -10% auto;height:720px;
background:radial-gradient(640px 340px at 18% 32%,var(--glow),transparent 70%),radial-gradient(520px 300px at 86% 8%,rgba(255,255,255,.06),transparent 70%);pointer-events:none}
.hero .in{position:relative;max-width:1240px;margin:0 auto;padding:84px 24px 60px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:48px;align-items:center}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font:500 13.5px var(--ui);color:var(--sub1);padding:5px 13px 5px 11px;border-radius:999px;
background:var(--glass);border:1px solid var(--rim);box-shadow:var(--lit)}
.eyebrow:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--tool)}
.hero h1{font-size:clamp(42px,6vw,68px);line-height:1.02;margin:18px 0 8px;letter-spacing:-.035em;font-weight:700}
.hero .sa{font-size:22px;color:var(--sub1);margin-bottom:22px}.hero .sa span{color:var(--ov1)}
.hero .shloka{margin:0 0 28px;padding:16px 20px;border-radius:22px;background:var(--glass);border:1px solid var(--rim);box-shadow:var(--lit),inset 3px 0 0 var(--tool);max-width:720px}
.hero .shloka p{margin:0 0 6px;font-size:18px;line-height:1.6;color:var(--text)}.hero .shloka figcaption{font-size:14px;color:var(--sub0)}.hero .shloka cite{color:var(--ov1);font-style:normal;white-space:nowrap}
.hero p.lead{font-size:19px;color:var(--sub0);max-width:680px;margin:0 0 28px}
.cta{display:flex;gap:10px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:11px 20px;border-radius:999px;font-weight:600;font-size:15px;color:var(--text);
background:rgba(255,255,255,.07);border:1px solid var(--rim);box-shadow:var(--lit);text-decoration:none}
.btn:hover{background:rgba(255,255,255,.12)}
.btn.primary{background:var(--accent);color:var(--crust);border-color:transparent;box-shadow:none}.btn.primary:hover{background:#fff}
.hero .logo{width:184px;height:184px;filter:drop-shadow(0 28px 56px var(--glow))}
.meta{display:flex;gap:18px;flex-wrap:wrap;margin-top:24px;color:var(--ov1);font-size:14px}.meta b{color:var(--sub1);font-weight:600}
/* layout */
.wrap{max-width:1240px;margin:0 auto;padding:44px 24px 88px;display:grid;grid-template-columns:230px minmax(0,1fr);gap:52px}
.toc{position:sticky;top:96px;align-self:start;max-height:calc(100vh - 116px);overflow:auto;font-size:14px;padding-right:6px}
.toc b{display:block;font-size:13px;font-weight:600;color:var(--ov1);margin:0 0 10px 12px}
.toc a{display:block;color:var(--sub0);padding:5px 12px;border-radius:12px;text-decoration:none}
.toc a.l3{padding-left:24px;font-size:13px;color:var(--ov1)}
.toc a:hover{color:var(--text);background:rgba(255,255,255,.04)}
.toc a.on{color:var(--text);background:rgba(255,255,255,.09);box-shadow:var(--lit)}
article{min-width:0}
article h2{font-size:30px;letter-spacing:-.02em;margin:60px 0 14px;padding-top:6px;font-weight:650}
article h2:first-child{margin-top:0}
article h3{font-size:20px;margin:34px 0 10px;font-weight:600}article h4{font-size:16px;margin:24px 0 8px;color:var(--sub1)}
article p,article li{color:var(--sub1)}
article .anchor{opacity:0;margin-left:-22px;width:22px;display:inline-block;color:var(--ov0);text-decoration:none}
article h2:hover .anchor,article h3:hover .anchor{opacity:1}
article ul,article ol{padding-left:22px}article li{margin:5px 0}
article img{border-radius:22px;border:1px solid var(--rim);box-shadow:0 24px 60px rgba(0,0,0,.35)}
article p[align=center]{text-align:center}article p[align=center] img{margin:6px 0}
article blockquote{margin:22px 0;padding:16px 22px;background:var(--glass);border:1px solid var(--rim);box-shadow:var(--lit);border-radius:22px}
article blockquote p{margin:0;color:var(--sub0)}
pre.code{position:relative;background:rgba(0,0,0,.28);border:1px solid var(--rim);box-shadow:var(--lit);border-radius:20px;padding:18px 20px;overflow:auto;font:13.5px/1.65 var(--mono);color:var(--sub1)}
pre.code code{background:none;padding:0;font-size:inherit;color:inherit}
pre.code .copy{position:absolute;top:10px;right:10px;font:600 12px var(--ui);padding:5px 12px;border-radius:999px;border:0;background:rgba(255,255,255,.1);color:var(--text);cursor:pointer;opacity:0;transition:opacity .15s}
pre.code:hover .copy,pre.code .copy:focus-visible{opacity:1}
.table{overflow:auto;margin:16px 0;border:1px solid var(--rim);border-radius:20px;background:var(--glass);box-shadow:var(--lit)}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th{text-align:left;color:var(--sub1);font-weight:600;padding:11px 16px;border-bottom:1px solid var(--rim);background:rgba(255,255,255,.03)}
td{padding:10px 16px;border-bottom:1px solid rgba(255,255,255,.06);color:var(--sub1);vertical-align:top}tr:last-child td{border-bottom:0}
td code{white-space:nowrap}
/* changelog */
.release{position:relative;padding:0 0 10px 30px;border-left:1px solid var(--s1);margin-left:6px}
.release:before{content:"";position:absolute;left:-6px;top:11px;width:11px;height:11px;border-radius:50%;background:var(--tool);box-shadow:0 0 0 4px var(--crust)}
.release h2{margin-top:0;font-size:24px}.release h2 .date{font:500 14px var(--mono);color:var(--ov1);margin-left:10px}
.release .tag{font:600 12px var(--mono);padding:2px 10px;border-radius:999px;background:rgba(255,255,255,.08);color:var(--text);margin-left:8px;vertical-align:3px}
/* adr */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:18px 0}
.card{display:block;background:var(--glass);border:1px solid var(--rim);box-shadow:var(--lit);border-radius:24px;padding:20px 22px;color:var(--text);text-decoration:none;transition:background .15s,border-color .15s}
.card:hover{background:rgba(255,255,255,.075);border-color:rgba(255,255,255,.2)}
.card .n{font:600 12px var(--mono);color:var(--ov1)}.card h3{margin:6px 0 6px;font-size:17px}.card p{margin:0;color:var(--sub0);font-size:14px}
.status{display:inline-block;font:600 12px var(--ui);padding:2px 10px;border-radius:999px;background:rgba(142,226,166,.14);color:var(--green)}
.status.superseded,.status.deprecated{background:rgba(247,176,125,.14);color:var(--peach)}.status.proposed{background:rgba(147,196,255,.14);color:var(--blue)}
/* footer */
footer{border-top:1px solid rgba(255,255,255,.06);background:var(--mantle)}
footer .in{max-width:1240px;margin:0 auto;padding:48px 24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:28px}
footer h4{margin:0 0 10px;font-size:13.5px;font-weight:600;color:var(--sub0)}
footer a{display:flex;gap:8px;align-items:baseline;color:var(--sub0);font-size:14px;padding:2px 0;text-decoration:none}footer a:hover{color:var(--text)}footer a span{color:var(--ov0);font-size:12.5px}
footer a.me{color:var(--text);font-weight:600}
footer .bottom{max-width:1240px;margin:0 auto;padding:0 24px 32px;color:var(--ov0);font-size:13px}
footer .bottom a{display:inline;padding:0;font-size:13px;text-decoration:underline}
@media(max-width:900px){.wrap{grid-template-columns:1fr}.toc{display:none}.hero .in{grid-template-columns:1fr}.hero .logo{width:112px;height:112px;order:-1}
.top nav a:not(.gh){padding:6px 9px}}
@media(max-width:560px){.top{padding:0 10px}.top .in{gap:10px;padding-left:12px}.brand small{display:none}.top nav a.hide{display:none}.hero .in{padding:52px 16px 36px}.wrap{padding:28px 16px 64px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
"""
JS = """
document.querySelectorAll('pre.code').forEach(p=>{const b=document.createElement('button');b.className='copy';b.textContent='Copy';
b.onclick=()=>{navigator.clipboard.writeText(p.innerText.replace(/^Copy/,'')).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1200)})};p.appendChild(b)});
const links=[...document.querySelectorAll('.toc a')];if(links.length){const hs=links.map(a=>document.getElementById(a.hash.slice(1))).filter(Boolean);
const on=()=>{let cur=hs[0];for(const h of hs){if(h.getBoundingClientRect().top<120)cur=h}links.forEach(a=>a.classList.toggle('on',cur&&a.hash==='#'+cur.id))};
addEventListener('scroll',on,{passive:true});on()}
"""


def page(meta, title, body, depth=0, active="", toc=None, hero=""):
    up = "../" * depth
    name = meta["name"]
    tool = COLORS.get(meta.get("color", "mauve"), "#c9b6f2")
    nav = [("Overview", f"{up}index.html", "home"), ("Changelog", f"{up}changelog.html", "changelog"),
           ("Decisions", f"{up}adr/index.html", "adr")]
    if meta.get("demo"):  # an interactive demo: try it in the browser
        nav.insert(1, ("Try it", f"{up}try.html", "try"))
    navhtml = "".join(f'<a href="{h}" class="{"on" if k == active else ""}{" hide" if k == "adr" else ""}">{t}</a>' for t, h, k in nav)
    navhtml += f'<a class="gh" href="{GH}/{name}">GitHub ↗</a>'
    tochtml = ""
    if toc:
        tochtml = '<aside class="toc"><b>On this page</b>' + "".join(
            f'<a class="l{lvl}" href="#{s}">{html.escape(t)}</a>' for lvl, s, t in toc) + "</aside>"
    fam = []
    for group, items in FAMILY:
        links = []
        for it in items:
            n, sa, what = it[0], it[1], it[2]
            url = it[3] if len(it) > 3 else home(n)
            links.append(f'<a href="{url}" class="{"me" if n == name else ""}">{n} <span>{sa} · {what}</span></a>')
        fam.append(f"<div><h4>{group}</h4>{''.join(links)}</div>")
    desc = html.escape(meta["tagline"], quote=True)
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/site.css">
<style>:root{{--tool:{tool};--glow:{tool}2e}}</style>
</head>
<body>
<header class="top"><div class="in">
<a class="brand" href="{up}index.html"><img src="{up}assets/logo.svg" alt=""><span>{name} <small>{meta.get("sanskrit", "")}</small></span></a>
<nav>{navhtml}</nav></div></header>
{hero}
<div class="wrap">{tochtml or '<aside class="toc"></aside>'}<article>
{body}
</article></div>
<footer><div class="in">{''.join(fam)}</div>
<div class="bottom">{name} is free software under the MIT license · <a href="{GH}/{name}">source</a> · <a href="{GH}/{name}/issues">issues</a> · <a href="{up}changelog.html">changelog</a> · part of <a href="{home('vayu')}">Vayu</a></div></footer>
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
    # keep the first screenshot block for the page body if it was among the stripped ones
    shots = [m for m in re.findall(r'(?s)<p align="center">\s*<img[^>]+assets/screenshots/[^>]+>.*?</p>', readme.split("\n## ")[0])
             if m not in stripped]
    body_md = ("\n\n".join(shots) + "\n\n" + stripped) if shots else stripped
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
    hero = f"""<section class="hero"><div class="in"><div>
<div class="eyebrow">{html.escape(meta.get("kind", "open source"))}</div>
<h1>{name}</h1>
<div class="sa">{meta.get("sanskrit", "")} <span>· “{html.escape(meta.get("meaning", ""))}”</span></div>
<p class="lead">{html.escape(meta["tagline"])}</p>
{shloka}<div class="cta">{'<a class="btn primary" href="try.html">Try it in your browser</a>' if meta.get("demo") else ""}<a class="btn{"" if meta.get("demo") else " primary"}" href="#install">Install</a><a class="btn" href="{GH}/{name}">GitHub ↗</a>
<a class="btn" href="changelog.html">What's new{(' in ' + latest) if latest else ''}</a></div>
<div class="meta"><span><b>{latest or 'unreleased'}</b> latest</span><span><b>{len([v for v in vers if v[0] != 'Unreleased'])}</b> releases</span><span><b>{len(adrs)}</b> decisions recorded</span><span><b>MIT</b> license</span></div>
</div><img class="logo" src="assets/logo.svg" alt="{name} logo"></div></section>"""
    if "install" not in {s for _, s, _ in toc}:
        hero = hero.replace('href="#install"', f'href="{GH}/{name}#install"')
    files["index.html"] = page(meta, f"{name} · {meta['tagline']}", body, 0, "home", toc, hero).encode()

    # ---- changelog
    items = []
    ctoc = []
    for v, date, md in vers:
        sid = slug(v)
        tag = f'<a class="tag" href="{GH}/{name}/releases/tag/{v if v.startswith("v") else "v" + v}">release ↗</a>' if v != "Unreleased" else ""
        items.append(f'<section class="release"><h2 id="{sid}">{html.escape(v)}<span class="date">{html.escape(date)}</span>{tag}</h2>'
                     f"{markdown(md, lambda u: link_map(u).replace('changelog.html', '#'), None, 1)}</section>")
        ctoc.append((2, sid, v))
    intro = (f"<h2>Changelog</h2><p>Every change to {name}, newest first. Releases are git tags "
             f"(<a href=\"{GH}/{name}/tags\">all tags</a>, <a href=\"{GH}/{name}/releases\">GitHub releases</a>); "
             f"the source of this page is <a href=\"{GH}/{name}/blob/main/CHANGELOG.md\">CHANGELOG.md</a>.</p>")
    files["changelog.html"] = page(meta, f"Changelog · {name}", intro + "".join(items), 0, "changelog", ctoc).encode()

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
        adr_body = adr_body.replace("<h1 ", f'<p class="n"><span class="status {st}">{html.escape(status)}</span> '
                                    f'<span style="color:var(--ov1);font:13px var(--mono)">ADR {num}{" · " + html.escape(date) if date else ""}</span></p><h2 ', 1).replace("</h1>", "</h2>", 1)
        nav = f'<p style="margin-top:40px"><a href="index.html">← All decisions</a> · <a href="{GH}/{name}/blob/main/docs/adr/{f}">source</a></p>'
        files[os.path.join("adr", out_name)] = page(meta, f"ADR {num}: {title} · {name}", adr_body + nav, 1, "adr").encode()
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
    files[os.path.join("adr", "index.html")] = page(meta, f"Decisions · {name}", adr_intro + f'<div class="cards">{"".join(cards)}</div>', 1, "adr").encode()
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
