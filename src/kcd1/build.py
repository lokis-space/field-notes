import base64, html, json, os, re
from bs4 import BeautifulSoup

W = os.path.dirname(os.path.abspath(__file__))
E = html.escape
OUT = os.path.expanduser("~/Downloads")
D = json.load(open(f"{W}/data.json", encoding="utf-8"))
AN = json.load(open(f"{W}/analysis.json", encoding="utf-8"))
IMM = json.load(open(f"{W}/immersion.json", encoding="utf-8"))
APPX = open(f"{W}/appendix.html", encoding="utf-8").read()
_rq = f"{W}/reqs.json"
RQ = json.load(open(_rq, encoding="utf-8")) if os.path.exists(_rq) else {"quests": {}, "visits": {}, "acts": {}}
acts = D["acts"]

seen = set()
for a in acts:
    for v in a["visits"]:
        for e in v["entries"]:
            e["first"] = bool(e["url"]) and e["display"] not in seen
            if e["url"]:
                seen.add(e["display"])
NQ = sum(len(v["entries"]) for a in acts for v in a["visits"]) + 1
NV = sum(len(a["visits"]) for a in acts)
NQUEST = len(seen)


def font(fn):
    return base64.b64encode(open(f"{W}/../fonts/{fn}", "rb").read()).decode()


FONTS = f"""
@font-face{{font-family:"KBlack";src:url(data:font/woff2;base64,{font('unifraktur-400-normal.woff2')}) format("woff2");font-display:swap}}
@font-face{{font-family:"KHead";src:url(data:font/woff2;base64,{font('bellefair-400-normal.woff2')}) format("woff2");font-display:swap}}
@font-face{{font-family:"KBody";src:url(data:font/woff2;base64,{font('alegreya-400-normal.woff2')}) format("woff2");font-weight:400 800;font-display:swap}}
@font-face{{font-family:"KBody";font-style:italic;src:url(data:font/woff2;base64,{font('alegreya-400-italic.woff2')}) format("woff2");font-display:swap}}
"""

TYPE_CLS = {"MAIN": "t-main", "SIDE": "t-side", "ACTIVITY": "t-act"}
STATUS_CLS = {"Start": "s-start", "Progress": "s-prog", "Complete": "s-done", "Win": "s-done",
              "Refuse for now": "s-ref", "Bonus": "s-bonus", "Intended fail": "s-fail", "Never completed": "s-fail"}
NOTE_LBL = {"w": ("warn", "Warning"), "m": ("miss", "Missable"), "r": ("rp", "Role-play"), "i": ("info", "Note"),
            "c": ("choice", "Choice"), "a": ("alt", "Alternative")}
MD_ICON = {"w": "⚠", "m": "🔒", "r": "🎭", "i": "ℹ"}
VENG = "Added automatically after Homecoming; objectives complete by themselves through the main story; finishes at the Epilogue."
RING = '<svg class="ring" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.5"/><circle class="rf" cx="18" cy="18" r="15.5" pathLength="100"/></svg>'
DLCS = ["A Woman's Lot", "Band of Bastards", "From the Ashes", "The Amorous Adventures of Bold Sir Hans Capon"]


def tcls(b):
    return "t-dlc" if b.startswith("DLC") else TYPE_CLS.get(b, "t-obj")


def split_act(t):
    n, _, rest = t.partition(" — ")
    return n, rest or t


# ---------------- HTML ----------------
def analysis_html(e):
    a = AN.get(e["display"]) if e["first"] else None
    if not a:
        return ""
    cells = [(k, l) for k, l in (("outcome", "Outcome"), ("tip", "Tip"), ("immersion", "Immersion")) if a.get(k)]
    return ('<div class="an">' + "".join(f'<div class="an-{k}"><h5>{l}</h5><p>{E(a[k])}</p></div>' for k, l in cells) + "</div>")


def entry_html(e):
    name = (f'<a href="{E(e["url"])}" target="_blank" rel="noopener">{E(e["display"])}</a>' if e["url"] else E(e["display"]))
    h = [f'<article class="entry" id="{e["id"]}" data-type="{e["type"]}" data-dlc="{E(e["dlc"])}">',
         '<div class="ehead">',
         f'<label class="ckwrap"><input type="checkbox" class="ck" data-id="{e["id"]}" aria-label="Done: {E(e["display"])}"></label>',
         f'<h4 class="ename">{name}</h4>',
         f'<div class="tags"><span class="tag {tcls(e["badge"])}">{E(e["badge"])}</span>'
         f'<span class="st {STATUS_CLS.get(e["status"], "s-prog")}">{E(e["status"])}</span>'
         + ('<span class="tag t-added">Added</span>' if e["added"] else "") + "</div></div>",
         '<div class="ebody">']
    if e["first"] and e["where"]:
        h.append(f'<p class="where"><span class="lbl">Where to find</span>{E(e["where"])}</p>')
    rq = RQ["quests"].get(e["display"]) if e["first"] else None
    if rq and (rq.get("req") or rq.get("prep")):
        rows = [(k, l, rq.get(k)) for k, l in (("req", "Requires"), ("prep", "Bring")) if rq.get(k)]
        h.append('<div class="reqs">' + "".join(f'<div class="rq rq-{k}"><span class="lbl">{l}</span>' + "".join(f"<span class=\"chip\">{E(x)}</span>" for x in xs) + "</div>" for k, l, xs in rows) + "</div>")
    if e["steps"]:
        h.append('<ol class="steps">' + "".join(f"<li>{E(s)}</li>" for s in e["steps"]) + "</ol>")
    for k, t in e["notes"]:
        if k == "pc":
            h.append(f'<div class="note pc"><span class="lbl">PC only · console command</span><pre><code>{E(t)}</code></pre></div>')
        else:
            c, l = NOTE_LBL[k]
            h.append(f'<div class="note {c}"><span class="lbl">{l}</span>{E(t)}</div>')
    h.append(analysis_html(e))
    foot = []
    if e["reward"]:
        foot.append(f'<span class="reward"><span class="lbl">Reward</span>{E(e["reward"])}</span>')
    if e["cont"]:
        foot.append(f'<a class="cont" href="#v{e["cont"]}">Continues in Visit {e["cont"]} <span aria-hidden="true">→</span></a>')
    if foot:
        h.append('<div class="efoot">' + "".join(foot) + "</div>")
    if e["spoilers"]:
        h.append('<details class="spoiler"><summary>Reveal story outcome</summary>'
                 + "".join(f"<p>{E(s)}</p>" for s in e["spoilers"]) + "</details>")
    h.append("</div></article>")
    return "\n".join(h)


def visit_html(v):
    n = len(v["entries"])
    h = [f'<details class="visit" id="v{v["no"]}" open><summary>'
         f'<span class="vno"><small>Visit</small>{v["no"]}</span>'
         f'<span class="vtitle"><span class="vlabel">{E(v["label"])}</span><span class="vsum">{E(v["summary"])}</span></span>'
         f'<span class="vcount" data-v="v{v["no"]}">0/{n}</span><span class="chev" aria-hidden="true"></span></summary><div class="vbody">']
    for k, t in v["banners"]:
        h.append(f'<div class="banner {"warn" if k == "w" else "info"}"><span class="lbl">{"Warning" if k == "w" else "Note"}</span>{E(t)}</div>')
    if RQ["visits"].get(str(v["no"])):
        h.append(f'<div class="banner prep"><span class="lbl">Prepare</span>{E(RQ["visits"][str(v["no"])])}</div>')
    for t in IMM.get("visits", {}).get(str(v["no"]), []):
        h.append(f'<div class="banner imm"><span class="lbl">Immersion</span>{E(t)}</div>')
    h += [entry_html(e) for e in v["entries"]]
    h.append("</div></details>")
    return "\n".join(h)


def vengeance_html():
    return ('<div class="frame tracker"><article class="entry" id="vengeance" data-type="MAIN" data-dlc="">'
            '<div class="ehead"><label class="ckwrap"><input type="checkbox" class="ck" data-id="vengeance" aria-label="Done: Vengeance"></label>'
            '<h4 class="ename"><span class="pre">Tracker</span><a href="https://kingdomcomedeliverance.wiki.gg/wiki/Vengeance" target="_blank" rel="noopener">Vengeance</a></h4>'
            '<div class="tags"><span class="tag t-main">MAIN</span><span class="st s-prog">Background</span></div></div>'
            f'<div class="ebody"><p class="where">{E(VENG)}</p>'
            '<div class="note info"><span class="lbl">Wiki note</span>Vengeance actually stays open when the credits roll. Tick it off at the Epilogue.</div></div></article></div>')


def mainstory_html():
    rows, seen_m = [], {}
    for a in acts:
        for v in a["visits"]:
            for e in v["entries"]:
                if e["type"] == "MAIN" and e["url"]:
                    seen_m.setdefault(e["display"], []).append((v["no"], v["label"], e["id"], e["status"]))
    for name, aps in seen_m.items():
        first = aps[0]
        rng = f"Visit {aps[0][0]}" + (f"–{aps[-1][0]}" if aps[-1][0] != aps[0][0] else "")
        ids = " ".join(x[2] for x in aps)
        rows.append(f'<li data-ids="{ids}"><a href="#{first[2]}"><span class="mn">{E(name)}</span><span class="mv">{rng} · {E(first[1])}</span></a></li>')
    return ('<details class="frame mainstory" id="mainstory"><summary><span class="lbl">Main story</span>'
            f'<span class="mst">{len(seen_m)} quests in order</span><span class="msp">0/{len(seen_m)}</span><span class="chev" aria-hidden="true"></span></summary>'
            '<p class="msnote">This route deliberately delays the story: after the prologue, Awakening doesn\'t come until Visit 45. Visits 2–44 are Henry earning his keep. '
            'The Vengeance tracker at the top of Act II runs in the background.</p><ol class="mslist">' + "".join(rows) + "</ol></details>")


def charter_html():
    h = ['<section class="frame charter" id="immersion"><div class="orn" aria-hidden="true">✠</div>',
         '<h2>The Immersion Charter</h2>', f'<p class="lead">{E(IMM["intro"])}</p><div class="cgrid">']
    for g in IMM["groups"]:
        h.append(f'<div><h3>{E(g["title"])}</h3><ul>' + "".join(f"<li>{E(x)}</li>" for x in g["rules"]) + "</ul></div>")
    h.append(f'</div><p class="src">{E(IMM["source"])}</p></section>')
    return "\n".join(h)


def sidebar_html():
    h = ['<nav id="sidebar" aria-label="Contents"><div class="navhead">Contents</div>',
         '<a class="nimm" href="#mainstory">Main story</a><a class="nimm" href="#immersion">Immersion Charter</a><ol class="nacts">']
    for i, a in enumerate(acts):
        n, t = split_act(a["title"])
        h.append(f'<li><a class="nact" href="#act{i+1}" data-act="act{i+1}">{RING}<span>{E(n)}</span>{E(t)}</a><ol>')
        h += [f'<li><a href="#v{v["no"]}"><span>{v["no"]}</span>{E(v["label"])}</a></li>' for v in a["visits"]]
        h.append("</ol></li>")
    h.append('<li><a class="nact" href="#appendix"><span>Appendix</span>Reference</a></li></ol></nav>')
    return "\n".join(h)


NOISE = ("data:image/svg+xml;utf8," + "%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E"
         "%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1  0 0 0 0 .95  0 0 0 0 .85  0 0 0 .55 0'/%3E"
         "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")

CSS = r"""
:root{--bg:#000;--card:rgba(10,10,11,.92);--card2:#111113;--ink:#f1ecda;--muted:#b8b2a1;--faint:#8a8476;
--line:rgba(80,86,95,.5);--line2:rgba(255,255,255,.14);--y:#fceb2d;--ydim:rgba(252,235,45,.55);--gold:#d8bb63;
--navy1:#0f1b31;--navy2:#060a13;--main:#e5584c;--side:#86afe3;--dlc:#c294e8;--act:#a9cb73;--obj:#a29c90;--warn:#f1bf3b;--miss:#ef5a4c;
--head:"KHead",Georgia,serif;--body:"KBody",Georgia,"Times New Roman",serif;--black:"KBlack","KHead",serif;--hh:64px}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 18px/1.62 var(--body);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
body::before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;background:radial-gradient(ellipse 80% 50% at 50% 0%,#141418 0%,#000 70%)}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:url("__NOISE__");opacity:.035}
a{color:var(--y);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}
::selection{background:var(--y);color:#000}
h1,h2,h3,h4,h5{font-family:var(--head);font-weight:400;margin:0}
.lbl{font-family:var(--head);font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;margin-right:.6rem;white-space:nowrap}
/* hero */
.hero{text-align:center;padding:4.2rem 1.2rem 2.4rem;position:relative;border-bottom:1px solid transparent;border-image:linear-gradient(90deg,transparent,var(--gold),transparent) 1}
.hero .home{position:absolute;left:1.2rem;top:1rem;font-family:var(--head);font-size:.85rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faint)}
.hero .home:hover{color:var(--y);text-decoration:none}
.hero .crest{font-size:2rem;color:var(--y);line-height:1}
.hero h1{font-family:var(--black);font-size:clamp(2.8rem,8vw,5.4rem);line-height:.95;color:var(--ink);letter-spacing:.01em;margin-top:.4rem}
.hero h1 span{display:block;font-size:.58em;margin-top:.05em}
.hero .sub{font-family:var(--head);color:var(--y);font-size:clamp(1.25rem,3vw,1.9rem);letter-spacing:-.01em;margin:1rem 0 .4rem}
.hero .intro{max-width:620px;margin:0 auto;color:var(--muted);font-size:1.02rem}
.stats{display:flex;justify-content:center;gap:2.4rem;margin-top:1.6rem;flex-wrap:wrap}
.stats div{font-family:var(--head);color:var(--faint);font-size:.78rem;letter-spacing:.14em;text-transform:uppercase}
.stats b{display:block;font-weight:400;font-size:2rem;color:var(--ink);letter-spacing:0;line-height:1.1}
/* sticky bar */
.bar{position:sticky;top:0;z-index:30;background:rgba(0,0,0,.86);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.barrow{display:flex;align-items:center;gap:.7rem;padding:.6rem 1.2rem;max-width:1360px;margin:0 auto}
.brand{font-family:var(--black);font-size:1.35rem;color:var(--ink);white-space:nowrap}
.search{flex:1;max-width:460px;position:relative}
.search input{width:100%;background:#0b0b0c;border:1px solid var(--line);border-radius:999px;color:var(--ink);font:inherit;font-size:.95rem;padding:.45rem 1rem .45rem 2.2rem;outline:none;transition:border-color .2s}
.search input:focus{border-color:var(--y)}
.search::before{content:"⚲";position:absolute;left:.85rem;top:50%;transform:translateY(-52%) rotate(-45deg);color:var(--faint)}
.btn{font-family:var(--head);font-size:.88rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink);background:transparent;border:1px solid var(--line2);border-radius:999px;padding:.42rem 1rem;cursor:pointer;white-space:nowrap;transition:all .2s}
.btn:hover,.btn[aria-expanded=true]{border-color:var(--y);color:var(--y)}
.prog{display:flex;align-items:center;gap:.7rem;margin-left:auto;min-width:180px}
.track{flex:1;height:2px;background:var(--line);position:relative}
.track i{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--y);box-shadow:0 0 8px var(--y);transition:width .4s}
#progtxt{font-family:var(--head);font-size:.95rem;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
#hamb{display:none}
.filters{display:none;border-top:1px solid var(--line);padding:.8rem 1.2rem;max-width:1360px;margin:0 auto;flex-wrap:wrap;gap:.5rem;align-items:center}
.filters.open{display:flex}
.filters .grp{font-family:var(--head);font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin:0 .3rem 0 .6rem}
.filters .grp:first-child{margin-left:0}
.pill{position:relative;cursor:pointer}
.pill input{position:absolute;opacity:0;pointer-events:none}
.pill span{display:inline-block;font-family:var(--head);font-size:.95rem;padding:.25rem .85rem;border:1px solid var(--line2);border-radius:999px;color:var(--faint);transition:all .2s}
.pill input:checked+span{border-color:var(--ydim);color:var(--y)}
.pill input:focus-visible+span{outline:1px solid var(--y);outline-offset:2px}
.filters select{background:#0b0b0c;color:var(--ink);border:1px solid var(--line2);border-radius:999px;padding:.3rem .8rem;font:inherit;font-size:.9rem}
/* layout */
.layout{display:flex;max-width:1360px;margin:0 auto}
#sidebar{position:sticky;top:var(--hh);align-self:flex-start;width:280px;flex-shrink:0;max-height:calc(100vh - var(--hh));overflow:auto;padding:1.8rem 1rem 3rem 1.4rem;scrollbar-width:thin;scrollbar-color:#2a2a2e transparent}
.navhead{font-family:var(--head);font-size:.8rem;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);margin-bottom:.6rem}
.nimm{display:block;font-family:var(--head);font-size:1.05rem;color:var(--y);padding:.15rem 0 .35rem}
.mainstory{padding:0;background:var(--card)}
.mainstory>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:1rem;padding:1rem 1.3rem}
.mainstory>summary .lbl{color:var(--main);font-size:.9rem}
.mst{flex:1;font-family:var(--head);font-size:1.25rem}
.msp{font-family:var(--head);color:var(--faint);font-variant-numeric:tabular-nums}
.msnote{margin:0 1.3rem .6rem;color:var(--muted);font-size:.93rem;font-style:italic}
.mslist{list-style:none;counter-reset:m;margin:0;padding:0 1.3rem 1rem;columns:2 300px;column-gap:2rem}
.mslist li{counter-increment:m;break-inside:avoid;border-top:1px solid var(--line)}
.mslist a{display:grid;grid-template-columns:2rem 1fr;padding:.45rem 0;color:var(--ink)}
.mslist a::before{content:counter(m);grid-row:1/3;font-family:var(--head);color:var(--main);font-variant-numeric:tabular-nums}
.mslist a:hover{text-decoration:none}.mslist a:hover .mn{color:var(--y)}
.mn{font-family:var(--head);font-size:1.08rem;line-height:1.25}
.mv{font-size:.82rem;color:var(--faint)}
.mslist li.ok .mn{color:var(--faint);text-decoration:line-through}
.mslist li.ok a::before{content:"✓";color:var(--act)}
#mainonly.on{border-color:var(--main);color:var(--main)}
#sidebar ol{list-style:none;margin:0;padding:0}
.nact{display:block;font-family:var(--head);font-size:1.08rem;color:var(--ink);line-height:1.25;margin:1.1rem 0 .35rem}
.nact span{display:block;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)}
#sidebar ol ol a{display:flex;gap:.6rem;padding:.12rem .5rem;margin-left:-.5rem;border-left:2px solid transparent;color:var(--faint);font-size:.92rem}
#sidebar ol ol a span{min-width:1.6em;text-align:right;font-family:var(--head);font-variant-numeric:tabular-nums}
#sidebar ol ol a:hover{color:var(--ink);text-decoration:none}
#sidebar ol ol a.on{color:var(--ink);border-left-color:var(--y)}
#sidebar ol ol a.on span{color:var(--y)}
main{flex:1;min-width:0;max-width:900px;padding:2rem 1.6rem 6rem}
/* frames */
.frame{position:relative;border:1px solid rgba(216,187,99,.35);outline:1px solid rgba(216,187,99,.14);outline-offset:6px;border-radius:2px;margin:1.2rem 6px 2.4rem;background:linear-gradient(180deg,var(--navy1),var(--navy2))}
.frame::before,.frame::after{content:"✦";position:absolute;top:-.85rem;color:var(--gold);font-size:1rem;background:#000;padding:0 .3rem;line-height:1.6}
.frame::before{left:-1.05rem}.frame::after{right:-1.05rem}
.charter{padding:2.2rem 2rem 1.6rem;text-align:left}
.charter .orn{text-align:center;color:var(--y);font-size:1.4rem;line-height:1}
.charter h2{text-align:center;font-size:2.4rem;letter-spacing:-.02em;margin:.3rem 0 .2rem}
.charter .lead{text-align:center;color:var(--y);font-family:var(--head);font-size:1.25rem;margin:0 auto 1.4rem;max-width:560px}
.cgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.2rem 2rem}
.cgrid h3{font-size:1.2rem;color:var(--gold);border-bottom:1px solid var(--line);padding-bottom:.25rem;margin-bottom:.4rem}
.cgrid ul{margin:0;padding-left:1.05rem;font-size:.95rem;color:var(--muted)}
.cgrid li{margin:.35rem 0}
.cgrid li::marker{color:var(--gold)}
.src{font-size:.8rem;color:var(--faint);font-style:italic;margin:1.4rem 0 0;text-align:center}
.tracker{padding:1rem 1.3rem}
.tracker .entry{border:0;padding:0}
.pre{font-size:.75rem;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);display:block}
/* acts */
.act{scroll-margin-top:var(--hh)}
.band{position:relative;text-align:center;margin:4rem -1.6rem 1.6rem;padding:2.4rem 1.6rem 2rem;background:linear-gradient(180deg,var(--navy1),var(--navy2));border-top:1px solid transparent;border-bottom:1px solid transparent;border-image:linear-gradient(90deg,transparent,rgba(216,187,99,.7),transparent) 1}
.band .actno{font-family:var(--head);font-size:.85rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold)}
.band h2{font-size:clamp(2rem,4.5vw,3rem);letter-spacing:-.025em;line-height:1.05;margin:.35rem 0 .6rem;color:var(--ink)}
.band p{margin:0 auto;max-width:600px;color:var(--y);font-family:var(--head);font-size:1.18rem;line-height:1.4}
/* visits */
details.visit{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:1rem 0;scroll-margin-top:calc(var(--hh) + 12px);transition:border-color .25s,box-shadow .25s}
details.visit:hover{border-color:rgba(252,235,45,.3)}
details.visit.cur,details.visit:target{border-color:var(--y);box-shadow:0 0 0 1px rgba(252,235,45,.12),0 8px 30px rgba(0,0,0,.6)}
details.visit>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:1.1rem;padding:1.05rem 1.3rem}
details>summary::-webkit-details-marker{display:none}
.vno{font-family:var(--head);color:var(--y);font-size:1.9rem;line-height:1;text-align:center;min-width:2.6rem;font-variant-numeric:tabular-nums}
.vno small{display:block;font-size:.58rem;letter-spacing:.2em;text-transform:uppercase;color:var(--faint);margin-bottom:.2rem}
.vtitle{flex:1;min-width:0}
.vlabel{display:block;font-family:var(--head);font-size:1.6rem;line-height:1.15;letter-spacing:-.015em}
.vsum{display:block;color:var(--muted);font-style:italic;font-size:.98rem;line-height:1.4;margin-top:.15rem}
.vcount{font-family:var(--head);color:var(--faint);font-size:1rem;font-variant-numeric:tabular-nums}
.vcount.full{color:var(--act)}
.chev{width:.6rem;height:.6rem;border-right:1.5px solid var(--faint);border-bottom:1.5px solid var(--faint);transform:rotate(45deg);transition:transform .2s;margin:0 .2rem .25rem}
details[open] .chev{transform:rotate(225deg);margin-bottom:-.2rem}
.vbody{padding:0 1.3rem 1rem;border-top:1px solid var(--line)}
.banner{margin:1rem 0 .2rem;padding:.65rem .9rem;border:1px solid var(--line2);border-left:2px solid;font-size:.95rem}
.banner.warn{border-left-color:var(--warn)}.banner.warn .lbl{color:var(--warn)}
.banner.info{border-left-color:var(--side)}.banner.info .lbl{color:var(--side)}
.banner.prep{border-left-color:var(--act)}.banner.prep .lbl{color:var(--act)}
.reqs{display:grid;gap:.35rem;margin:.55rem 0 .2rem}
.rq{display:flex;flex-wrap:wrap;align-items:center;gap:.35rem}
.rq .lbl{min-width:5.6rem}
.rq-req .lbl{color:var(--main)}.rq-prep .lbl{color:var(--side)}
.chip{font-size:.86rem;line-height:1.3;padding:.18rem .6rem;border-radius:6px;background:#141416;border:1px solid var(--line);color:var(--ink)}
.rq-req .chip{border-color:rgba(229,88,76,.35)}
.checkpoint{margin:1.6rem 0 .4rem;padding:1rem 1.2rem;border:1px dashed rgba(216,187,99,.45);border-radius:10px;text-align:center}
.checkpoint .lbl{color:var(--gold)}
.checkpoint p{margin:.35rem 0 0;font-family:var(--head);font-size:1.15rem;color:var(--ink)}
.banner.imm{border-left-color:var(--gold);font-style:italic;color:var(--muted)}.banner.imm .lbl{color:var(--gold);font-style:normal}
/* entries */
.entry{padding:1.3rem 0 1.1rem;border-top:1px solid var(--line)}
.vbody>.entry:first-child,.banner+.entry{border-top:0}
.ehead{display:grid;grid-template-columns:auto 1fr;column-gap:.85rem;align-items:start}
.ckwrap{grid-row:1/3;padding-top:.32rem;cursor:pointer}
.ck{appearance:none;-webkit-appearance:none;width:1.2rem;height:1.2rem;margin:0;border:1px solid var(--faint);border-radius:3px;background:transparent;cursor:pointer;display:grid;place-content:center;transition:all .15s}
.ck:hover{border-color:var(--y)}
.ck:checked{background:var(--y);border-color:var(--y)}
.ck:checked::after{content:"";width:.3rem;height:.6rem;border:solid #000;border-width:0 2px 2px 0;transform:rotate(45deg) translate(-1px,-1px)}
.ck:focus-visible{outline:1px solid var(--y);outline-offset:3px}
.ename{font-size:1.5rem;line-height:1.2;letter-spacing:-.01em}
.ename a{color:var(--ink)}
.ename a:hover{color:var(--y);text-decoration:none}
.tags{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.4rem;align-items:center}
.tag,.st{font-family:var(--head);font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;line-height:1;padding:.32rem .65rem .26rem;border-radius:999px}
.tag{border:1px solid currentColor}
.t-main{color:var(--main)}.t-side{color:var(--side)}.t-dlc{color:var(--dlc)}.t-act{color:var(--act)}.t-obj{color:var(--obj)}.t-added{color:#000;background:var(--y);border-color:var(--y)}
.st{padding-left:.15rem}
.st::before{content:"";display:inline-block;width:.42rem;height:.42rem;border-radius:50%;background:currentColor;margin-right:.45rem;vertical-align:.05em}
.s-start{color:var(--side)}.s-prog{color:var(--faint)}.s-done{color:var(--act)}.s-ref{color:var(--warn)}.s-bonus{color:var(--y)}.s-fail{color:var(--miss)}
.ebody{margin-left:2.05rem}
.where{margin:.75rem 0 .3rem;color:var(--muted);font-size:.98rem}
.where .lbl,.reward .lbl{color:var(--gold)}
.steps{list-style:none;counter-reset:s;padding:0;margin:.6rem 0 .4rem}
.steps li{counter-increment:s;position:relative;padding-left:2rem;margin:.32rem 0}
.steps li::before{content:counter(s,upper-roman) ".";position:absolute;left:0;width:1.5rem;text-align:right;font-family:var(--head);color:var(--y);font-size:.95rem;top:.08em}
.note{margin:.6rem 0;padding:.6rem .9rem;border:1px solid var(--line2);border-left:2px solid;font-size:.96rem;line-height:1.55}
.note.warn{border-left-color:var(--warn)}.note.warn .lbl{color:var(--warn)}
.note.miss{border-left-color:var(--miss);background:rgba(239,90,76,.06)}.note.miss .lbl{color:var(--miss)}
.note.rp{border-left-color:var(--gold);font-style:italic;color:var(--muted)}.note.rp .lbl{color:var(--gold);font-style:normal}
.note.info{border-left-color:var(--side)}.note.info .lbl{color:var(--side)}
.note.choice{border-left-color:var(--act)}.note.choice .lbl{color:var(--act)}
.note.alt{border-left-color:var(--faint);color:var(--muted)}.note.alt .lbl{color:var(--faint)}
.note.pc{border-left-color:var(--ink)}.note.pc .lbl{color:var(--ink)}
.note pre{margin:.45rem 0 0;padding:.6rem .8rem;background:#050505;border:1px solid var(--line);overflow-x:auto;font:.86rem/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--y)}
.an{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin:1rem 0 .4rem;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.an>div{padding:.8rem 1rem .7rem 0}
.an>div+div{padding-left:1rem;border-left:1px solid var(--line)}
.an h5{font-size:.78rem;letter-spacing:.16em;text-transform:uppercase;margin-bottom:.25rem}
.an-outcome h5{color:var(--act)}.an-tip h5{color:var(--side)}.an-immersion h5{color:var(--gold)}
.an p{margin:0;font-size:.93rem;line-height:1.5;color:var(--muted)}
.efoot{display:flex;flex-wrap:wrap;gap:.4rem 1.6rem;align-items:baseline;margin-top:.6rem;font-size:.95rem;color:var(--muted)}
.cont{font-family:var(--head);font-size:1rem;color:var(--y)}
.spoiler{margin-top:.6rem}
.spoiler summary{display:inline-block;cursor:pointer;font-family:var(--head);font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);border-bottom:1px dashed var(--faint)}
.spoiler summary:hover{color:var(--y);border-color:var(--y)}
.spoiler p{margin:.45rem 0 0;color:var(--muted);font-style:italic}
.entry.done{opacity:.42}
.entry.done .ename a{text-decoration:line-through;text-decoration-thickness:1px}
/* appendix */
.appendix{margin-top:4rem}
.appendix>h2{text-align:center;font-size:clamp(2rem,4.5vw,3rem);letter-spacing:-.025em;padding:2.4rem 1rem 2rem;margin:0 -1.6rem 1.4rem;background:linear-gradient(180deg,var(--navy1),var(--navy2));border-top:1px solid transparent;border-bottom:1px solid transparent;border-image:linear-gradient(90deg,transparent,rgba(216,187,99,.7),transparent) 1}
.appendix h3{font-size:1.6rem;color:var(--y);margin:2.4rem 0 .8rem;letter-spacing:-.01em}
.appendix table{width:100%;border-collapse:collapse;font-size:.95rem}
.appendix th{font-family:var(--head);font-weight:400;font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);text-align:left;padding:.5rem .7rem;border-bottom:1px solid var(--ydim)}
.appendix td{padding:.6rem .7rem;border-bottom:1px solid var(--line);vertical-align:top;color:var(--muted)}
.appendix td:nth-child(2){color:var(--ink)}
.appendix ul,.appendix ol{padding-left:1.2rem;color:var(--muted)}
.appendix li{margin:.5rem 0}
.appendix li::marker{color:var(--gold)}
.appendix b{color:var(--ink);font-weight:700}
.appendix p{color:var(--muted)}
footer{text-align:center;color:var(--faint);font-size:.85rem;padding:2rem 1rem 3rem;border-top:1px solid var(--line)}
footer .crest{color:var(--y);font-size:1.2rem}
.hidden{display:none!important}
#totop{position:fixed;right:1.2rem;bottom:1.2rem;z-index:20;width:2.8rem;height:2.8rem;padding:0;border-radius:50%;background:#000;opacity:0;pointer-events:none;transition:opacity .25s}
#totop.show{opacity:1;pointer-events:auto}

.legend{display:flex;flex-wrap:wrap;justify-content:center;gap:.45rem;margin-top:1.4rem;align-items:center}
.legend i{width:1px;height:1rem;background:var(--line2);margin:0 .4rem}
.ring{width:1.15rem;height:1.15rem;transform:rotate(-90deg);flex-shrink:0}
.ring circle{fill:none;stroke:var(--line);stroke-width:3.2}
.ring .rf{stroke:var(--y);stroke-dasharray:0 100;stroke-linecap:round;transition:stroke-dasharray .4s}
.ring.full .rf{stroke:var(--act)}
.nact{position:relative;padding-right:1.6rem}
.nact .ring{position:absolute;right:0;top:.15rem}
.actprog{display:inline-flex;align-items:center;gap:.55rem;margin-top:1rem;font-family:var(--head);color:var(--muted);font-size:1rem;font-variant-numeric:tabular-nums}
.actprog .ring{width:1.6rem;height:1.6rem}
.toast{position:fixed;left:50%;transform:translateX(-50%);bottom:1.2rem;z-index:60;display:flex;align-items:center;gap:.2rem;background:#0b0b0c;border:1px solid var(--ydim);border-radius:999px;padding:.25rem .3rem .25rem .4rem;box-shadow:0 10px 40px rgba(0,0,0,.8);max-width:calc(100% - 2rem)}
.toast[hidden]{display:none}
.toast button{background:none;border:0;color:var(--ink);font:inherit;cursor:pointer;padding:.4rem .8rem;border-radius:999px}
.toast .rgo{font-family:var(--head);font-size:1rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toast .rgo b{color:var(--y);font-weight:400}
.toast .rgo:hover{background:#17171a}
.toast .rx{color:var(--faint)}
.toast.msg{padding:.6rem 1.2rem;font-family:var(--head);color:var(--y)}
.entry.flash{animation:flash 1.6s ease-out}
@keyframes flash{0%{background:rgba(252,235,45,.14)}100%{background:transparent}}
@media (max-width:860px){#nexttodo{padding:.42rem .7rem}}
@media print{.toast,.legend,.actprog{display:none!important}}
@media (max-width:1080px){#sidebar{width:230px}}
@media (max-width:860px){
 body{font-size:17px}
 #hamb{display:inline-block}
 .brand{display:none}
 .prog{min-width:0;flex:0 0 auto}.track{display:none}
 #sidebar{position:fixed;left:0;top:0;bottom:0;max-height:none;z-index:50;width:84%;max-width:330px;background:#050506;border-right:1px solid var(--line);transform:translateX(-102%);transition:transform .25s}
 #sidebar.open{transform:none;box-shadow:20px 0 60px rgba(0,0,0,.8)}
 main{padding:1.2rem .8rem 5rem}
 .band,.appendix>h2{margin-left:-.8rem;margin-right:-.8rem}
 details.visit>summary{padding:.9rem 1rem;gap:.8rem}
 .vlabel{font-size:1.35rem}.vno{font-size:1.5rem;min-width:2rem}
 .vbody{padding:0 1rem .9rem}
 .ebody{margin-left:0}
 .ename{font-size:1.32rem}
 .an{grid-template-columns:1fr}.an>div+div{padding-left:0;border-left:0;border-top:1px solid var(--line)}
 .charter{padding:1.8rem 1.1rem 1.3rem}
 .hero{padding-top:3rem}
}
@media print{
 :root{--ink:#000;--muted:#222;--faint:#555;--line:#bbb;--line2:#ccc;--y:#7a5d00;--gold:#7a5d00}
 body{background:#fff}body::before,body::after{display:none}
 .bar,#sidebar,#totop,.chev{display:none!important}
 .band,.frame,.appendix>h2{background:none}
 details.visit{background:none;break-inside:auto}
 .hidden{display:revert!important}
 .entry.done{opacity:1}
}
""".replace("__NOISE__", NOISE)

JS = r"""
(function(){
var KEY='kcd1-guide-v1',st={};
try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
var boxes=$$('.ck'),quest=boxes.filter(function(b){return !b.classList.contains('ck-extra')});
function refresh(){
  var d=quest.filter(function(b){return b.checked}).length;
  $('#progtxt').textContent=d+' / '+quest.length;
  $('.track i').style.width=(100*d/quest.length)+'%';
  $$('.vcount').forEach(function(c){var bs=$$('.ck',document.getElementById(c.dataset.v)),n=bs.filter(function(b){return b.checked}).length;
    c.textContent=n+'/'+bs.length;c.classList.toggle('full',n===bs.length);});
  filter();
}
boxes.forEach(function(b){
  b.checked=!!st[b.dataset.id];var ent=b.closest('.entry');if(ent)ent.classList.toggle('done',b.checked);
  b.addEventListener('change',function(){if(b.checked)st[b.dataset.id]=true;else delete st[b.dataset.id];
    if(ent)ent.classList.toggle('done',b.checked);save();refresh();});
});
var q=$('#search'),hide=$('#hidedone'),dlc=$('#dlcsel'),types=$$('.tf');
function filter(){
  var term=q.value.trim().toLowerCase(),on={};types.forEach(function(t){on[t.value]=t.checked});
  var dv=dlc.value,any=!!(term||dv||hide.checked||types.some(function(t){return !t.checked}));
  $$('main .entry').forEach(function(e){
    var ok=on[e.dataset.type];
    if(dv)ok=ok&&e.dataset.dlc===dv;
    if(hide.checked&&e.classList.contains('done'))ok=false;
    if(term&&e.textContent.toLowerCase().indexOf(term)<0)ok=false;
    e.classList.toggle('hidden',!ok);
  });
  $$('details.visit').forEach(function(v){var n=$$('.entry:not(.hidden)',v).length;v.classList.toggle('hidden',any&&n===0);if(any&&n)v.open=true;});
  $$('.act').forEach(function(a){a.classList.toggle('hidden',any&&$$('details.visit:not(.hidden),.tracker .entry:not(.hidden)',a).length===0)});
  var t=$('.tracker');if(t)t.classList.toggle('hidden',!!$('#vengeance.hidden'));
  $('#charter-wrap').classList.toggle('hidden',any);
}
[q,hide,dlc].concat(types).forEach(function(el){el.addEventListener('input',filter);el.addEventListener('change',filter)});
var fb=$('#ftog'),fp=$('.filters');
fb.onclick=function(){var o=fp.classList.toggle('open');fb.setAttribute('aria-expanded',o);hh()};
$('#expand').onclick=function(){$$('details.visit').forEach(function(d){d.open=true})};
$('#collapse').onclick=function(){$$('details.visit').forEach(function(d){d.open=false})};
$('#reset').onclick=function(){if(confirm('Clear every tick?')){st={};save();boxes.forEach(function(b){b.checked=false;var e=b.closest('.entry');if(e)e.classList.remove('done')});refresh();}};
var sb=$('#sidebar');
$('#hamb').onclick=function(e){e.stopPropagation();sb.classList.toggle('open')};
document.addEventListener('click',function(e){if(sb.classList.contains('open')&&!sb.contains(e.target))sb.classList.remove('open')});
$$('a[href^="#"]').forEach(function(a){a.addEventListener('click',function(){
  sb.classList.remove('open');var t=document.querySelector(a.getAttribute('href'));if(t&&t.tagName==='DETAILS')t.open=true;})});
function hh(){document.documentElement.style.setProperty('--hh',$('.bar').offsetHeight+'px')}
window.addEventListener('resize',hh);hh();
var tt=$('#totop');tt.onclick=function(){window.scrollTo({top:0})};
var links={};$$('#sidebar ol ol a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a});
if('IntersectionObserver' in window){var cur,cv;var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){
  if(cur)cur.classList.remove('on');if(cv)cv.classList.remove('cur');cv=en.target;cv.classList.add('cur');
  cur=links[en.target.id];if(cur){cur.classList.add('on');var r=cur.getBoundingClientRect(),s=sb.getBoundingClientRect();if(r.top<s.top+40||r.bottom>s.bottom-40)sb.scrollTop+=r.top-s.top-s.height/2;}}})},{rootMargin:'-35% 0px -60% 0px'});
  $$('details.visit').forEach(function(v){io.observe(v)});}
window.addEventListener('scroll',function(){tt.classList.toggle('show',window.scrollY>1200)},{passive:true});
window.addEventListener('beforeprint',function(){$$('details').forEach(function(d){d.dataset.w=d.open;d.open=true})});
window.addEventListener('afterprint',function(){$$('details').forEach(function(d){d.open=d.dataset.w==='true'})});

function actProg(){$$('.act').forEach(function(a){var bs=$$('.ck',a),n=bs.filter(function(b){return b.checked}).length,p=bs.length?100*n/bs.length:0;
  $$('[data-act="'+a.id+'"]').forEach(function(x){var r=$('.ring',x);$('.rf',r).style.strokeDasharray=p+' 100';r.classList.toggle('full',n===bs.length);var sp=$('span:last-child',x);if(x.classList.contains('actprog'))sp.textContent=n+' / '+bs.length+' done';});});}
var _r=refresh;refresh=function(){_r();actProg();};
function toast(t){var m=$('#msg');m.textContent=t;m.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(function(){m.hidden=true},2600);}
function go(el,flash){var v=el.closest('details.visit');if(v)v.open=true;var y=el.getBoundingClientRect().top+scrollY-$('.bar').offsetHeight-14;window.scrollTo({top:y});
  if(flash){el.classList.remove('flash');void el.offsetWidth;el.classList.add('flash');}}
function msProg(){var n=0,ls=$$('.mslist li');ls.forEach(function(li){var ok=li.dataset.ids.split(' ').every(function(id){return st[id]});li.classList.toggle('ok',ok);if(ok)n++});$('.msp').textContent=n+'/'+ls.length;}
var _r2=refresh;refresh=function(){_r2();msProg();};
var mo=$('#mainonly');mo.onclick=function(){var on=!mo.classList.contains('on');mo.classList.toggle('on',on);
  types.forEach(function(t){t.checked=on?t.value==='MAIN':true});filter();};
types.forEach(function(t){t.addEventListener('change',function(){mo.classList.toggle('on',types.every(function(x){return x.checked===(x.value==='MAIN')}))})});
$$('.mslist a').forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();var t=document.getElementById(a.getAttribute('href').slice(1));if(t){if(t.classList.contains('hidden')){mo.classList.remove('on');types.forEach(function(x){x.checked=true});q.value='';filter();}go(t,true);}})});
$('#nexttodo').onclick=function(){var b=quest.filter(function(b){return !b.checked&&!b.closest('.hidden')})[0];
  if(!b){toast('Everything visible is ticked off. Well done, Henry.');return;}go(b.closest('.entry'),true);};
$('#export').onclick=function(){var d=new Date().toISOString().slice(0,10);
  var blob=new Blob([JSON.stringify({app:'kcd1-quest-guide',version:1,exported:new Date().toISOString(),ticks:st,last:localStorage.getItem(KEY+'-last')},null,1)],{type:'application/json'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='kcd1-progress-'+d+'.json';document.body.appendChild(a);a.click();a.remove();
  toast('Exported '+Object.keys(st).length+' ticks');};
$('#import').onclick=function(){$('#importf').click()};
$('#importf').onchange=function(){var f=this.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){
  try{var j=JSON.parse(rd.result),t=j.ticks||j;if(typeof t!=='object')throw 0;
    if(Object.keys(st).length&&!confirm('Replace your current '+Object.keys(st).length+' ticks with '+Object.keys(t).length+' from the file?'))return;
    st={};Object.keys(t).forEach(function(k){if(t[k])st[k]=true});save();if(j.last)localStorage.setItem(KEY+'-last',j.last);
    boxes.forEach(function(b){b.checked=!!st[b.dataset.id];var e=b.closest('.entry');if(e)e.classList.toggle('done',b.checked)});refresh();toast('Imported '+Object.keys(st).length+' ticks');
  }catch(e){alert('That file is not a KCD1 guide progress export.')}};rd.readAsText(f);this.value='';};
try{localStorage.setItem(KEY+'-opened',Date.now())}catch(e){}
var LK=KEY+'-last',lastT;
window.addEventListener('scroll',function(){clearTimeout(lastT);lastT=setTimeout(function(){var c=$('details.visit.cur');if(c&&scrollY>400)try{localStorage.setItem(LK,c.id)}catch(e){}},500)},{passive:true});
(function(){var l=localStorage.getItem(LK),el=l&&document.getElementById(l);if(!el||location.hash||l==='v1')return;
  var r=$('#resume'),lab=$('.vlabel',el).textContent;$('.rgo',r).innerHTML='Resume at <b>Visit '+l.slice(1)+'</b> · '+lab;r.hidden=false;
  $('.rgo',r).onclick=function(){r.hidden=true;go(el)};$('.rx',r).onclick=function(){r.hidden=true};setTimeout(function(){r.hidden=true},15000);})();
refresh();
})();
"""

PWA_HEAD = """
<link rel="manifest" href="manifest.webmanifest"><link rel="icon" href="favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black"><meta name="apple-mobile-web-app-title" content="KCD Guide">
<meta name="description" content="Chronological role-play quest guide for Kingdom Come: Deliverance (2018) with all story DLCs.">"""
PWA_JS = """
if('serviceWorker' in navigator&&location.protocol==='https:'){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js')})}
"""


def build_html(pwa=False):
    body = []
    for i, a in enumerate(acts):
        n, t = split_act(a["title"])
        body.append(f'<section class="act" id="act{i+1}"><header class="band"><div class="actno">{E(n)}</div>'
                    f'<h2>{E(t)}</h2><p>{E(a["summary"])}</p><div class="actprog" data-act="act{i+1}">{RING}<span>0 / 0</span></div></header>')
        if a["vengeance"]:
            body.append(vengeance_html())
        body += [visit_html(v) for v in a["visits"]]
        cp = RQ["acts"].get(str(i + 1))
        if cp:
            body.append(f'<aside class="checkpoint"><span class="lbl">Checkpoint · end of {E(n)}</span><p>{E(cp)}</p></aside>')
        body.append("</section>")
    tf = "".join(f'<label class="pill"><input type="checkbox" class="tf" value="{v}" checked><span>{l}</span></label>'
                 for v, l in [("MAIN", "Main"), ("SIDE", "Side"), ("DLC", "DLC"), ("ACTIVITY", "Activity"), ("OBJ", "Objective / RP")])
    dopts = '<option value="">All content</option>' + "".join(f'<option value="{E(d)}">{E(d)}</option>' for d in DLCS)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#000000">
<title>Kingdom Come: Deliverance — Chronological Role-Play Quest Guide</title>{PWA_HEAD if pwa else ""}
<style>{FONTS}{CSS}</style></head>
<body>
<header class="hero" id="top">
{'<a class="home" href="../">← Field Notes</a>' if pwa else ''}<div class="crest" aria-hidden="true">♛</div>
<h1>Kingdom Come<span>Deliverance</span></h1>
<p class="sub">A Chronological Role-Play Quest Guide</p>
<p class="intro">Henry's whole journey, from the last morning in Skalitz to the road out of Neuhof — every quest and every DLC, in the order a role-playing Henry would live them.</p>
<div class="legend" aria-label="Legend"><span class="tag t-main">Main</span><span class="tag t-side">Side</span><span class="tag t-dlc">DLC</span><span class="tag t-act">Activity</span><span class="tag t-obj">Objective / RP</span><i></i><span class="st s-start">Start</span><span class="st s-prog">Progress</span><span class="st s-done">Complete</span><span class="st s-fail">Fail</span></div>
<div class="stats"><div><b>{NV}</b>Visits</div><div><b>{NQUEST}</b>Quests</div><div><b>{NQ}</b>Checkpoints</div><div><b>4</b>Story DLCs</div></div>
</header>
<div class="bar">
<div class="barrow">
<button class="btn" id="hamb" aria-label="Contents">☰</button>
<a class="brand" href="#top">Kingdom Come</a>
<div class="search"><input type="search" id="search" placeholder="Search quests, people, places…" aria-label="Search"></div>
<button class="btn" id="nexttodo" title="Jump to the next unticked quest">Next</button><button class="btn" id="ftog" aria-expanded="false">Filters</button>
<div class="prog"><div class="track"><i></i></div><span id="progtxt">0 / {NQ}</span></div>
</div>
<div class="filters">
<span class="grp">Type</span><button class="btn" id="mainonly">Main only</button>{tf}
<span class="grp">Content</span><select id="dlcsel" aria-label="DLC filter">{dopts}</select>
<label class="pill"><input type="checkbox" id="hidedone"><span>Hide done</span></label>
<span class="grp">View</span><button class="btn" id="expand">Expand</button><button class="btn" id="collapse">Collapse</button><span class="grp">Progress</span><button class="btn" id="export">Export</button><button class="btn" id="import">Import</button><input type="file" id="importf" accept="application/json,.json" hidden><button class="btn" id="reset">Reset ticks</button>
</div>
</div>
<div class="layout">
{sidebar_html()}
<main>
{mainstory_html()}<div id="charter-wrap">{charter_html()}</div>
{''.join(body)}
{APPX}
</main></div>
<footer><div class="crest">✠</div>Quest names link to kingdomcomedeliverance.wiki.gg. Ticks are saved in this browser — use Filters → Export to back them up or move them to another device. Fonts: Bellefair, Alegreya, UnifrakturMaguntia (SIL Open Font License).</footer>
<button class="btn" id="totop" aria-label="Back to top">↑</button>
<div id="resume" class="toast" hidden><button class="rgo"></button><button class="rx" aria-label="Dismiss">✕</button></div>
<div id="msg" class="toast msg" hidden></div>
<script>{JS}{PWA_JS if pwa else ""}</script>
</body></html>"""


# ---------------- Markdown ----------------
def md_entry(e):
    nm = f"[{e['display']}]({e['url']})" if e["url"] else e["display"]
    L = [f"- [ ] **{nm}** — `{e['badge']}` · **{e['status']}**" + (" · **[Added]**" if e["added"] else "")]
    if e["first"] and e["where"]:
        L.append(f"  - *Where:* {e['where']}")
    rq = RQ["quests"].get(e["display"]) if e["first"] else None
    if rq:
        if rq.get("req"):
            L.append("  - **Requires:** " + " · ".join(rq["req"]))
        if rq.get("prep"):
            L.append("  - **Bring:** " + " · ".join(rq["prep"]))
    L += [f"  {i}. {s}" for i, s in enumerate(e["steps"], 1)]
    for k, t in e["notes"]:
        if k == "pc":
            L += ["  - 💻 **PC only:**", "    ```", f"    {t}", "    ```"]
        elif k == "c":
            L.append(f"  - **Choice:** {t}")
        elif k == "a":
            L.append(f"  - *Alternative:* {t}")
        else:
            L.append(f"  - {MD_ICON[k]} {t}")
    a = AN.get(e["display"]) if e["first"] else None
    if a:
        for k, l in (("outcome", "Outcome"), ("tip", "Tip"), ("immersion", "Immersion")):
            if a.get(k):
                L.append(f"  - **{l}:** {a[k]}")
    if e["reward"]:
        L.append(f"  - 🪙 {e['reward']}")
    if e["cont"]:
        L.append(f"  - ↪ Continues in [Visit {e['cont']}](#visit-{e['cont']})")
    if e["spoilers"]:
        L.append("  - <details><summary>Story spoiler</summary>" + " ".join(e["spoilers"]) + "</details>")
    return "\n".join(L)


def md_appendix():
    s = BeautifulSoup(APPX, "html.parser")
    o = ["## Appendices", ""]
    for el in s.section.children:
        if not getattr(el, "name", None) or el.name == "h2":
            continue
        if el.name == "h3":
            o += [f"### {el.get_text()}", ""]
        elif el.name == "p":
            o += [el.get_text(), ""]
        elif el.name in ("ul", "ol"):
            o += [("- " if el.name == "ul" else f"{i}. ") + li.get_text().strip() for i, li in enumerate(el.find_all("li", recursive=False), 1)] + [""]
        elif el.name == "table":
            for j, r in enumerate(el.find_all("tr")):
                cells = [("☐" if c.find("input") else c.get_text().strip().replace("|", "\\|")) for c in r.find_all(["th", "td"])]
                if j == 0 and cells and cells[0] == "":
                    cells[0] = "✓"
                o.append("| " + " | ".join(cells) + " |")
                if j == 0:
                    o.append("|" + "---|" * len(cells))
            o.append("")
    return o


def build_md():
    o = ["# Kingdom Come: Deliverance — Chronological Role-Play Quest Guide", "",
         f"KCD1 (2018) with all four story DLCs, in the order of the Reddit role-play timeline. {NV} visits, {NQUEST} quests, {NQ} checkpoints. Links go to kingdomcomedeliverance.wiki.gg.", "",
         "**Legend:** ⚠ warning/timed · 🔒 missable · 🎭 role-play note · 🕯 immersion · 💻 PC only · ℹ info · 🪙 reward", "",
         "## 🕯 The Immersion Charter", "", f"*{IMM['intro']}*", ""]
    for g in IMM["groups"]:
        o += [f"**{g['title']}**", ""] + [f"- {x}" for x in g["rules"]] + [""]
    o += [f"*{IMM['source']}*", ""]
    for a in acts:
        o += [f"## {a['title']}", "", f"*{a['summary']}*", ""]
        if a["vengeance"]:
            o += ["> - [ ] **Tracker: [Vengeance](https://kingdomcomedeliverance.wiki.gg/wiki/Vengeance)** — `MAIN` · Background",
                  f"> {VENG}", "> ℹ Wiki note: Vengeance actually stays open when the credits roll. Tick it off at the Epilogue.", ""]
        for v in a["visits"]:
            o += [f'<a id="visit-{v["no"]}"></a>', f"### Visit {v['no']} — {v['label']}", "", f"*{v['summary']}*", ""]
            bl = [f"> {'⚠' if k == 'w' else 'ℹ'} **{t}**" for k, t in v["banners"]]
            if RQ["visits"].get(str(v["no"])):
                bl.append(f"> 🎒 **Prepare:** {RQ['visits'][str(v['no'])]}")
            bl += [f"> 🕯 *{t}*" for t in IMM.get("visits", {}).get(str(v["no"]), [])]
            o += bl + ([""] if bl else [])
            o += [md_entry(e) for e in v["entries"]] + [""]
        cp = RQ["acts"].get(str(acts.index(a) + 1))
        if cp:
            o += [f"> 🏁 **Checkpoint — end of {split_act(a['title'])[0]}:** {cp}", ""]
    return "\n".join(o + md_appendix()) + "\n"


def build_site(dest):
    import shutil
    os.makedirs(dest, exist_ok=True)
    open(os.path.join(dest, "index.html"), "w", encoding="utf-8").write(build_html(pwa=True))
    open(os.path.join(dest, "KCD1_Quest_Guide.md"), "w", encoding="utf-8").write(build_md())
    labels = {f"v{v['no']}": v["label"] for a in acts for v in a["visits"]}
    json.dump({"key": "kcd1-guide-v1", "total": NQ, "exclude": "rec-", "labels": labels,
               "stats": f"{NV} visits · {NQUEST} quests"}, open(os.path.join(dest, "meta.json"), "w"), ensure_ascii=False)
    for f in ("manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "favicon-32.png"):
        shutil.copy(os.path.join(W, "pwa", f), dest)
    import hashlib
    ver = hashlib.sha1(open(os.path.join(dest, "index.html"), "rb").read()).hexdigest()[:10]
    p = os.path.join(dest, "sw.js")
    txt = open(p).read().replace("__VER__", ver)
    open(p, "w").write(txt)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        build_site(sys.argv[1])
        print("site built in", sys.argv[1])
        sys.exit()
    open(os.path.join(OUT, "KCD1_Quest_Guide.html"), "w", encoding="utf-8").write(build_html())
    open(os.path.join(OUT, "KCD1_Quest_Guide.md"), "w", encoding="utf-8").write(build_md())
    print("visits", NV, "quests", NQUEST, "entries", NQ, "analysis", sum(1 for n in seen if n in AN))
