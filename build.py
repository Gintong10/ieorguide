#!/usr/bin/env python3
"""Build the static site in docs/ from the markdown in content/.  Usage: python3 build.py"""
import html, os, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(ROOT, 'content'), os.path.join(ROOT, 'docs')
SITE = 'Infernal Eclipse of Ragnarok'
SUB = 'Class Progression Guide'
REPO = 'https://github.com/Gintong10/ieorguide'

PAGES = [  # slug, nav title, kind
    ('overview', 'Overview', 'doc'), ('shared-gear', 'Shared gear', 'stages'), ('melee', 'Melee', 'stages'),
    ('ranged', 'Ranged', 'stages'), ('magic', 'Magic', 'stages'), ('summoner', 'Summoner', 'stages'),
    ('rogue', 'Rogue', 'stages'), ('healer', 'Healer', 'stages'), ('bard', 'Bard', 'stages'),
]
TITLES = {t: s for s, t, _ in PAGES}

MARK = {'\x00': ('*', 'Tedious to obtain at this stage'), '†': ('†', 'Risky or hard to get at this stage'),
        'C': ('C', 'Crowd control: strong in events and against worm bosses'), '+': ('+', 'Support or secondary pick'),
        '≤': ('≤', 'Has variants or upgrades worth using'), 'ν': ('ν', 'Needs the Void subclass (Secrets of the Shadows)'),
        'Ω': ('Ω', 'Meant to be used together; a number ties specific items to each other'),
        'Δ': ('Δ', 'Works differently in Calamity than in vanilla'), '≈': ('≈', 'Placed by rarity alone; can be a stage off')}
MARK_RE = re.compile(r'(?<=[\s>])(\x00|†|C|\+|≤|ν|Ω[¹²³⁴⁵⁶]?|Δ|≈)(?=$|[\s;,/)<])')
GROUPS = ['All-class', 'Permanent', 'Thorium Bosses Reworked', 'Thorium', 'Calamity Bard & Healer', 'Calamity Ranger Expansion',
          'Calamity Whip Addon', 'Calamity', 'Ragnarok', 'Infernal Arsenal', 'Infernal Eclipse', 'SOTS Bard & Healer',
          'Secrets of the Shadows', 'Catalyst', 'Clamity', 'Consolaria', 'Hunt of the Old God', 'Wrath of the Gods', 'Infernum']
GROUP_RE = re.compile(r'(?:^|(?<=\. ))(' + '|'.join(re.escape(g) for g in sorted(GROUPS, key=len, reverse=True)) + r'): ')


def inline(s, markers=False):
    s = s.replace('\\*', '\x00')
    s = re.sub(r'\*\*([^*]+)\*\*', '\x03\\1\x04', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', '\x01\\1\x02', s)
    s = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', '\x01\\1\x02', s)
    links = []
    def keep(m):
        links.append((m.group(1), m.group(2))); return f'\x05{len(links) - 1}\x06'
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', keep, s)
    s = html.escape(s, quote=False)
    s = s.replace('\x01', '<em>').replace('\x02', '</em>').replace('\x03', '<strong>').replace('\x04', '</strong>')
    if markers:
        s = MARK_RE.sub(lambda m: f'<abbr class="mk" title="{MARK[m.group(1)[0]][1]}">{MARK[m.group(1)[0]][0]}{m.group(1)[1:]}</abbr>', s)
        s = re.sub(r'\(([^()]*)\)', r'<small>(\1)</small>', s)
    s = s.replace('\x00', '*')
    s = re.sub(r'\x05(\d+)\x06', lambda m: f'<a href="{html.escape(links[int(m.group(1))][1])}">{html.escape(links[int(m.group(1))][0])}</a>', s)
    return s


def blocks(text):
    """Tiny markdown block parser: headings, tables, lists, paragraphs."""
    out, lines, i = [], text.split('\n'), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1; continue
        m = re.match(r'(#{1,3}) (.*)', ln)
        if m:
            out.append(('h', len(m.group(1)), m.group(2).strip())); i += 1; continue
        if ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r':?-+:?', c) for c in r)]
            out.append(('table', rows)); continue
        if re.match(r'[-*] ', ln):
            items = []
            while i < len(lines) and re.match(r'[-*] ', lines[i]):
                items.append(lines[i][2:].strip()); i += 1
            out.append(('list', items)); continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r'#{1,3} |\||[-*] ', lines[i]):
            para.append(lines[i].strip()); i += 1
        out.append(('p', ' '.join(para)))
    return out


def chips(seg):
    seg = seg.strip()
    items = [x.strip() for x in seg.split('; ') if x.strip()]
    if len(items) == 1 and (len(seg) > 70 or seg[:1].islower() or re.search(r'\. [A-Z]', seg)):
        return f'<span class="prose">{inline(seg, True)}</span>'
    return '<ul class="chips">' + ''.join(f'<li>{inline(x, True)}</li>' for x in items) + '</ul>'


def row_body(content):
    parts = GROUP_RE.split(content)
    out = []
    pre = parts[0].strip()
    if len(parts) > 1 and pre.endswith('.'): pre = pre[:-1]
    if pre: out.append(chips(pre))
    for k in range(1, len(parts), 2):
        seg = parts[k + 1].strip()
        if k + 2 < len(parts) and seg.endswith('.'): seg = seg[:-1]
        out.append(f'<div class="grp"><span class="g">{html.escape(parts[k])}</span>{chips(seg)}</div>')
    return ''.join(out)


def render_list(items):
    rows = []
    for it in items:
        m = re.match(r'\*\*(.+?):\*\*\s*(.*)', it)
        if m:
            rows.append(f'<div class="row"><dt>{inline(m.group(1))}</dt><dd>{row_body(m.group(2))}</dd></div>')
        else:
            rows.append(f'<div class="row full"><dd><span class="prose">{inline(it, True)}</span></dd></div>')
    return '<dl class="rows">' + ''.join(rows) + '</dl>'


def table_html(rows, link_cells=False, prefix=''):
    def cell(c, tag):
        t = inline(c, True)
        if link_cells and c in TITLES and tag == 'td':
            t = f'<a href="{prefix}{TITLES[c]}/">{t} loadouts</a>'
        return f'<{tag}>{t}</{tag}>'
    head = '<tr>' + ''.join(cell(c, 'th') for c in rows[0]) + '</tr>'
    body = ''.join('<tr>' + ''.join(cell(c, 'td') for c in r) + '</tr>' for r in rows[1:])
    return f'<div class="tw"><table><thead>{head}</thead><tbody>{body}</tbody></table></div>'


ERA = {'Pre-Hardmode': 'pre', 'Hardmode': 'hm', 'Post-Moon Lord': 'post'}


def stage_page(slug, title, bl):
    lead, body, nav, era, open_stage = [], [], [], '', False
    i = 0
    if bl and bl[0][0] == 'h': i = 1
    while i < len(bl) and bl[i][0] != 'h':
        b = bl[i]
        if b[0] == 'p':
            cls = 'legend' if b[1].startswith('Markers:') else 'lead'
            lead.append(f'<p class="{cls}">{inline(b[1])}</p>')
        i += 1
    def close():
        nonlocal open_stage
        if open_stage: body.append('</section>'); open_stage = False
    for b in bl[i:]:
        if b[0] == 'h' and b[1] == 2:
            close()
            era = ERA.get(b[2], 'pre')
            body.append(f'<h2 class="era era-{era}" id="{era}">{html.escape(b[2])}</h2>')
            nav.append(('era', era, b[2]))
        elif b[0] == 'h' and b[1] == 3:
            close()
            nums = re.findall(r'(\d+)\.\s', b[2])
            sid = f'stage-{nums[0]}' if nums else 'x-' + re.sub(r'\W+', '-', b[2].lower()).strip('-')
            extra = ''.join(f'<span class="anchor" id="stage-{n}"></span>' for n in nums[1:])
            label = re.sub(r'(\d+)\.\s', r'<span class="num">\1</span> ', html.escape(b[2]))
            body.append(f'<section class="stage era-{era}" id="{sid}">{extra}<h3>{label}</h3>')
            open_stage = True
            short = re.sub(r'(\d+)\.\s', '', b[2])
            nav.append(('stage', sid, ('–'.join(nums) if nums else '·'), short))
        elif b[0] == 'list':
            body.append(render_list(b[1]))
        elif b[0] == 'p':
            body.append(f'<p class="note">{inline(b[1], True)}</p>')
        elif b[0] == 'table':
            body.append(table_html(b[1]))
    close()
    side = []
    for n in nav:
        if n[0] == 'era': side.append(f'<a class="s-era era-{n[1]}" href="#{n[1]}">{html.escape(n[2])}</a>')
        else: side.append(f'<a class="s-stage" href="#{n[1]}"><b>{n[2]}</b> {html.escape(n[3])}</a>')
    opts = ''.join(f'<option value="{n[1]}">{n[2]} · {html.escape(n[3])}</option>' for n in nav if n[0] == 'stage')
    tools = ('<div class="tools"><input id="q" type="search" placeholder="Filter items, e.g. Daedalus or Lich" aria-label="Filter items">'
             f'<select id="jump" aria-label="Jump to stage"><option value="">Jump to stage…</option>{opts}</select>'
             '<span id="count" aria-live="polite"></span></div>')
    return (f'<div class="layout"><aside class="side" aria-label="Stages">{"".join(side)}</aside><main>'
            f'<h1>{html.escape(title)}</h1>{"".join(lead)}{tools}{"".join(body)}'
            '<p id="none" hidden>No item on this page matches that filter.</p></main></div>')


CLASS_BLURB = {}


def doc_page(bl):
    out, hero_done = [], False
    for b in bl:
        if b[0] == 'h' and b[1] == 1:
            continue
        if b[0] == 'p' and not hero_done and b[1].startswith('Updated'):
            hero_done = True
            cards = ''.join(f'<a class="card c-{s}" href="{s}/"><b>{t}</b><span>{CLASS_BLURB.get(t, "")}</span></a>' for s, t, k in PAGES[1:])
            out.append(f'<header class="hero"><p class="kicker">Terraria modpack · unofficial fan guide</p><h1>{SITE}</h1>'
                       f'<p class="sub">{SUB}: weapons, armor and accessories for all seven classes across 22 stages.</p>'
                       f'<p class="date">{html.escape(b[1])}</p></header><nav class="cards" aria-label="Class pages">{cards}</nav>')
            continue
        if b[0] == 'h':
            hid = re.sub(r'\W+', '-', b[2].lower()).strip('-')
            out.append(f'<h{b[1]} id="{hid}">{html.escape(b[2])}</h{b[1]}>')
        elif b[0] == 'p':
            t = inline(b[1], True).replace('are in Shared gear.', 'are on the <a href="shared-gear/">Shared gear</a> page.')
            out.append(f'<p>{t}</p>')
        elif b[0] == 'list':
            out.append('<ul class="plain">' + ''.join(f'<li>{inline(x, True)}</li>' for x in b[1]) + '</ul>')
        elif b[0] == 'table':
            out.append(table_html(b[1], link_cells=True))
    return '<main class="doc">' + ''.join(out) + '</main>'


def shell(slug, title, inner, prefix):
    nav = ''.join(
        f'<a href="{prefix}{"" if s == "overview" else s + "/"}" data-base="{prefix}{"" if s == "overview" else s + "/"}"'
        f'{" data-stages" if k == "stages" else ""}{" aria-current=page" if s == slug else ""}>{t}</a>' for s, t, k in PAGES)
    page_title = f'{SITE}: {SUB}' if slug == 'overview' else f'{title} · {SITE} guide'
    icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%23ff7a3d'/%3E%3Ccircle cx='19' cy='13' r='11' fill='%23121014'/%3E%3C/svg%3E"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page_title)}</title>
<meta name="description" content="Stage-by-stage gear for every class in the Infernal Eclipse of Ragnarok Terraria modpack: Melee, Ranged, Magic, Summoner, Rogue, Healer and Bard.">
<link rel="icon" href="{icon}">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body class="p-{slug}">
<header class="top"><a class="brand" href="{prefix}"><span class="eclipse" aria-hidden="true"></span>IEoR <span>Class Guide</span></a><nav class="nav" aria-label="Pages">{nav}</nav></header>
{inner}
<footer><p>Unofficial fan guide. Item lists draw on the <a href="https://terrariamods.wiki.gg/wiki/Infernal_Eclipse_of_Ragnarok">Infernal Eclipse of Ragnarok</a>, <a href="https://calamitymod.wiki.gg/wiki/Guide:Class_setups">Calamity</a> and <a href="https://thoriummod.wiki.gg/wiki/Guide:Class_setups">Thorium</a> wikis and on the mods' own files. Terraria and every mod named here belong to their creators.</p><p><a href="{REPO}">Source on GitHub</a></p></footer>
<script src="{prefix}assets/app.js" defer></script>
</body>
</html>
'''


CSS = r''':root{--bg:#f6f3ee;--surface:#fff;--ink:#1d1a17;--muted:#6b635a;--line:#e2dbd0;--accent:#c2410c;--accent2:#6d28d9;--chip:#f3eee6;--chipline:#e3dbce;--hit:#ffe2a8;--pre:#2f8f55;--hm:#c97a12;--post:#7c4ddb;--shadow:0 1px 2px rgba(40,30,20,.06),0 6px 20px rgba(40,30,20,.05)}
@media (prefers-color-scheme:dark){:root{--bg:#121014;--surface:#1b181f;--ink:#ece7e1;--muted:#a39a90;--line:#2e2934;--accent:#ff7a3d;--accent2:#b79cff;--chip:#25212b;--chipline:#37313f;--hit:#6b4a12;--pre:#5fc587;--hm:#f0a640;--post:#a98bff;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.25)}}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:76px}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-text-size-adjust:100%}
a{color:var(--accent);text-underline-offset:2px}a:hover{text-decoration-thickness:2px}
.top{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:20px;padding:10px 20px;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;color:var(--ink);text-decoration:none;white-space:nowrap}.brand span:last-child{font-weight:400;color:var(--muted)}
.eclipse{width:20px;height:20px;border-radius:50%;background:radial-gradient(circle at 62% 38%,var(--bg) 0 58%,transparent 60%),var(--accent)}
.nav{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;margin-left:auto}.nav::-webkit-scrollbar{display:none}
.nav a{padding:6px 12px;border-radius:999px;color:var(--muted);text-decoration:none;font-size:14px;white-space:nowrap}
.nav a:hover{color:var(--ink);background:var(--chip)}.nav a[aria-current]{color:var(--bg);background:var(--ink);font-weight:600}
h1{font-size:clamp(28px,4vw,40px);line-height:1.15;margin:0 0 12px;letter-spacing:-.02em}
.doc{max-width:980px;margin:0 auto;padding:16px 20px 60px}
.doc h2{font-size:24px;margin:48px 0 10px;letter-spacing:-.01em}.doc p{max-width:72ch}
.hero{padding:56px 0 20px}.kicker{margin:0 0 10px;color:var(--accent);font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}
.hero h1{font-size:clamp(34px,6vw,60px);background:linear-gradient(100deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{font-size:19px;color:var(--muted);max-width:60ch;margin:0}.date{font-size:13px;color:var(--muted);margin:14px 0 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin:18px 0 8px}
.card{display:flex;flex-direction:column;gap:4px;padding:14px 16px;background:var(--surface);border:1px solid var(--line);border-radius:12px;text-decoration:none;color:var(--ink);box-shadow:var(--shadow);border-top:3px solid var(--k,var(--accent));transition:transform .12s}
.card:hover{transform:translateY(-2px)}.card b{font-size:17px}.card span{font-size:13px;color:var(--muted);line-height:1.4}
.c-shared-gear{--k:#8a8178}.c-melee{--k:#d9534f}.c-ranged{--k:#3f9d5b}.c-magic{--k:#3b82f6}.c-summoner{--k:#14b8a6}.c-rogue{--k:#e05a9c}.c-healer{--k:#d4a514}.c-bard{--k:#8b5cf6}
ul.plain{padding-left:20px;max-width:76ch}ul.plain li{margin:6px 0}
.tw{overflow-x:auto;margin:14px 0;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14.5px}th,td{padding:9px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);white-space:nowrap;background:color-mix(in srgb,var(--chip) 60%,transparent)}tr:last-child td{border-bottom:0}td:first-child{font-weight:600;white-space:nowrap}
.layout{display:grid;grid-template-columns:230px minmax(0,1fr);gap:36px;max-width:1240px;margin:0 auto;padding:28px 20px 60px}
.side{position:sticky;top:68px;align-self:start;max-height:calc(100vh - 84px);overflow-y:auto;display:flex;flex-direction:column;gap:1px;font-size:13.5px;padding-right:6px}
.side a{text-decoration:none;color:var(--muted);padding:4px 10px;border-radius:7px;border-left:2px solid transparent}
.side a:hover{color:var(--ink);background:var(--chip)}.side a.on{color:var(--ink);background:var(--chip);border-left-color:var(--accent)}
.side .s-era{margin-top:12px;font-size:11.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase}.side .s-era:first-child{margin-top:0}
.side .s-stage{display:grid;grid-template-columns:2.4em 1fr;line-height:1.35}.side b{color:var(--ink);font-variant-numeric:tabular-nums}
.era-pre{--e:var(--pre)}.era-hm{--e:var(--hm)}.era-post{--e:var(--post)}.s-era{color:var(--e)!important}
.lead{font-size:18px;color:var(--muted);max-width:70ch;margin:0 0 10px}.legend{font-size:13px;color:var(--muted);max-width:none;margin:10px 0 0}
.tools{position:sticky;top:53px;z-index:5;display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:18px -8px 0;padding:10px 8px;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(8px)}
.tools input,.tools select{font:inherit;font-size:15px;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:8px 12px;min-width:0}
.tools input{flex:1 1 240px}.tools select{flex:0 1 250px;display:none}.tools input:focus,.tools select:focus{outline:2px solid var(--accent);outline-offset:1px}#count{font-size:13px;color:var(--muted)}
h2.era{margin:44px 0 6px;font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--e);display:flex;align-items:center;gap:12px}h2.era::after{content:"";flex:1;height:1px;background:var(--line)}
.stage{position:relative;background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--e);border-radius:12px;padding:16px 20px 8px;margin:14px 0;box-shadow:var(--shadow)}
.stage h3{margin:0 0 8px;font-size:19px;letter-spacing:-.01em}.num{display:inline-block;min-width:1.9em;padding:1px 7px;margin-right:4px;border-radius:7px;background:var(--e);color:var(--surface);font-size:14px;text-align:center;font-variant-numeric:tabular-nums;vertical-align:2px}
.anchor{position:absolute;top:0}
.rows{margin:0}.row{display:grid;grid-template-columns:150px minmax(0,1fr);gap:4px 16px;padding:9px 0;border-top:1px solid var(--line)}.row.full{grid-template-columns:1fr}
dt{font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);padding-top:4px}dd{margin:0}
.chips{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:5px}.chips li{padding:2px 9px;background:var(--chip);border:1px solid var(--chipline);border-radius:8px;font-size:14px;line-height:1.5}
.chips li.hit{background:var(--hit);border-color:var(--accent)}.chips small{color:var(--muted);font-size:12.5px}
.grp{display:flex;flex-wrap:wrap;gap:5px 8px;align-items:baseline;margin-top:6px}.grp:first-child{margin-top:0}.g{font-size:12px;font-weight:600;color:var(--accent2);white-space:nowrap}
.grp .chips{flex:1 1 60%}.prose{font-size:14.5px;color:var(--muted)}.note{font-size:14.5px;color:var(--muted);max-width:76ch;margin:8px 0}
.mk{text-decoration:none;color:var(--accent);font-weight:700;cursor:help;margin-left:1px}em{font-style:italic}
[hidden]{display:none!important}#none{color:var(--muted);padding:30px 0}
footer{border-top:1px solid var(--line);padding:26px 20px 40px;color:var(--muted);font-size:13px;text-align:center}footer p{max-width:80ch;margin:6px auto}
main{min-width:0}.chips li,.prose,.note{overflow-wrap:anywhere}
@media (max-width:940px){.layout{grid-template-columns:minmax(0,1fr);padding-top:18px}.side{display:none}.tools select{display:block}.row{grid-template-columns:1fr}dt{padding-top:0}.top{padding:8px 14px;gap:12px}.brand span:last-child{display:none}}
@media (max-width:520px){.doc,.layout{padding-left:16px;padding-right:16px}.stage{padding:14px 14px 6px}.tools{top:49px}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card{transition:none}}
'''

JS = r'''(() => {
  const q = document.getElementById('q'), jump = document.getElementById('jump'), count = document.getElementById('count'), none = document.getElementById('none');
  const stages = [...document.querySelectorAll('.stage')];
  if (q) {
    const run = () => {
      const t = q.value.trim().toLowerCase(); let shown = 0, hits = 0;
      for (const s of stages) {
        let any = !t;
        for (const li of s.querySelectorAll('.chips li')) { const h = !!t && li.textContent.toLowerCase().includes(t); li.classList.toggle('hit', h); if (h) { any = true; hits++; } }
        if (t && !any) any = [...s.querySelectorAll('.prose, h3')].some(e => e.textContent.toLowerCase().includes(t));
        s.hidden = !any; if (any) shown++;
      }
      for (const h of document.querySelectorAll('h2.era')) { let n = h.nextElementSibling, vis = false; while (n && !n.matches('h2.era')) { if (n.matches('.stage') && !n.hidden) vis = true; n = n.nextElementSibling; } h.hidden = !vis; }
      count.textContent = t ? `${hits} item${hits === 1 ? '' : 's'} in ${shown} stage${shown === 1 ? '' : 's'}` : '';
      none.hidden = !!shown;
    };
    q.addEventListener('input', run);
    const p = new URLSearchParams(location.search).get('q'); if (p) { q.value = p; run(); }
  }
  if (jump) jump.addEventListener('change', () => { if (jump.value) { location.hash = jump.value; jump.value = ''; } });
  const links = [...document.querySelectorAll('.side a.s-stage')];
  if (links.length && 'IntersectionObserver' in window) {
    const byId = Object.fromEntries(links.map(a => [a.hash.slice(1), a]));
    const io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) { links.forEach(a => a.classList.remove('on')); const a = byId[e.target.id]; if (a) { a.classList.add('on'); a.scrollIntoView({ block: 'nearest' }); } } }, { rootMargin: '-80px 0px -70% 0px' });
    stages.forEach(s => io.observe(s));
  }
  const carry = () => { const h = /^#stage-\d+$/.test(location.hash) ? location.hash : ''; for (const a of document.querySelectorAll('.nav a[data-stages]')) a.href = a.dataset.base + h; };
  if (stages.length) { addEventListener('hashchange', carry); carry(); }
})();
'''


def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'assets'))
    open(os.path.join(OUT, 'assets', 'style.css'), 'w', encoding='utf-8').write(CSS)
    open(os.path.join(OUT, 'assets', 'app.js'), 'w', encoding='utf-8').write(JS)
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    parsed = {s: blocks(open(os.path.join(SRC, s + '.md'), encoding='utf-8').read()) for s, _, _ in PAGES}
    CLASS_BLURB['Shared gear'] = 'Accessories, potions and permanent upgrades that suit any class.'
    for b in parsed['overview']:
        if b[0] == 'table' and b[1][0][:2] == ['Class', 'From']:
            for r in b[1][1:]: CLASS_BLURB[r[0]] = r[3]
    for slug, title, kind in PAGES:
        if kind == 'doc':
            page, path, prefix = doc_page(parsed[slug]), os.path.join(OUT, 'index.html'), ''
        else:
            page, path, prefix = stage_page(slug, title, parsed[slug]), os.path.join(OUT, slug, 'index.html'), '../'
            os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8').write(shell(slug, title, page, prefix))
        print(f'{slug:12} {os.path.getsize(path):7} bytes')


if __name__ == '__main__':
    main()
