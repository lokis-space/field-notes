"""Builds the Field Notes home page (index.html) from src/guides.json.

Each entry may ship a <slug>/meta.json with {"key", "total", "exclude", "labels", "stats"};
the home page then shows live progress read from that guide's localStorage.
"""
import base64, html, json, os, shutil
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); E = html.escape
f64 = lambda fn: base64.b64encode(open(os.path.join(H, "fonts", fn), "rb").read()).decode()
items = json.load(open(os.path.join(H, "guides.json"), encoding="utf-8"))
metas = {}
for g in items:
    mp = os.path.join(ROOT, g["slug"], "meta.json")
    if os.path.exists(mp):
        metas[g["slug"]] = json.load(open(mp, encoding="utf-8"))
tags = sorted({t for g in items for t in g.get("tags", [])})
RING = '<svg class="ring" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.5"/><circle class="rf" cx="18" cy="18" r="15.5" pathLength="100"/></svg>'

def card(g):
    m = metas.get(g["slug"])
    stats = f'<span class="meta">{E(m["stats"])}</span>' if m and m.get("stats") else ""
    prog = (f'<div class="prog">{RING}<div><b class="pct">0%</b><span class="cnt">Not started</span></div></div>' if m else "")
    return (f'<article class="card" data-slug="{E(g["slug"])}" data-tags="{E("|".join(g.get("tags", [])))}">'
            f'<a class="main" href="{E(g["slug"])}/"><img src="{E(g["slug"])}/icon-192.png" alt="" width="76" height="76">'
            f'<div class="txt"><h2>{E(g["title"])}</h2><p class="sub">{E(g["subtitle"])}</p><p class="blurb">{E(g["blurb"])}</p>'
            f'<div class="tags">{"".join(f"<span>{E(t)}</span>" for t in g.get("tags", []))}{stats}</div></div>{prog}</a>'
            f'<div class="foot" hidden><a class="resume" href="{E(g["slug"])}/"></a><span class="seen"></span></div></article>')

cards = "".join(card(g) for g in items)
tagbar = ("".join(f'<button class="tag" data-t="{E(t)}">{E(t)}</button>' for t in tags)) if len(items) > 3 else ""
tools = (f'<div class="tools"><input type="search" id="q" placeholder="Search {len(items)} entries…" aria-label="Search">'
         f'<div class="tagbar">{tagbar}</div></div>') if len(items) > 3 else ""
page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#000000"><title>Field Notes</title>
<meta name="description" content="Personal collection of guides, checklists and notes.">
<link rel="icon" href="favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black"><meta name="apple-mobile-web-app-title" content="Field Notes">
<style>
@font-face{{font-family:KBlack;src:url(data:font/woff2;base64,{f64('unifraktur-400-normal.woff2')}) format("woff2")}}
@font-face{{font-family:KHead;src:url(data:font/woff2;base64,{f64('bellefair-400-normal.woff2')}) format("woff2")}}
@font-face{{font-family:KBody;src:url(data:font/woff2;base64,{f64('alegreya-400-normal.woff2')}) format("woff2")}}
:root{{--y:#fceb2d;--gold:#d8bb63;--ink:#f1ecda;--muted:#b8b2a1;--faint:#8a8476;--line:rgba(80,86,95,.5);--green:#a9cb73}}
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;background:radial-gradient(ellipse 80% 50% at 50% 0%,#141418,#000 70%) fixed #000;color:var(--ink);font:18px/1.6 KBody,Georgia,serif;-webkit-font-smoothing:antialiased;padding:env(safe-area-inset-top) env(safe-area-inset-right) 0 env(safe-area-inset-left)}}
a{{color:inherit;text-decoration:none}}
header{{text-align:center;padding:4.5rem 1.2rem 2.2rem}}
h1{{font:400 clamp(3rem,10vw,5.5rem)/1 KBlack,serif;margin:0}}
header p{{font-family:KHead,serif;color:var(--y);font-size:1.35rem;margin:.9rem 0 0}}
.rule{{width:180px;height:1px;margin:1.6rem auto 0;background:linear-gradient(90deg,transparent,var(--gold),transparent)}}
main{{max-width:780px;margin:0 auto;padding:0 1.2rem 5rem;display:grid;gap:1.2rem}}
.tools{{display:grid;gap:.7rem;margin-bottom:.4rem}}
.tools input{{width:100%;background:#0b0b0c;border:1px solid var(--line);border-radius:999px;color:var(--ink);font:inherit;font-size:1rem;padding:.55rem 1.1rem;outline:none}}
.tools input:focus{{border-color:var(--y)}}
.tagbar{{display:flex;flex-wrap:wrap;gap:.4rem}}
.tag{{font:400 .75rem KHead,serif;letter-spacing:.14em;text-transform:uppercase;background:none;border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:.3rem .8rem;color:var(--faint);cursor:pointer}}
.tag.on{{border-color:var(--y);color:var(--y)}}
.card{{border:1px solid var(--line);border-radius:16px;background:rgba(10,10,11,.92);transition:border-color .2s,transform .2s,box-shadow .2s;overflow:hidden}}
.card:hover{{border-color:var(--y);transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,0,0,.6)}}
.main{{display:flex;gap:1.3rem;align-items:flex-start;padding:1.4rem}}
.main img{{border-radius:18px;flex-shrink:0}}
.txt{{flex:1;min-width:0}}
h2{{font:400 1.7rem/1.15 KHead,serif;margin:0}}
.sub{{font-family:KHead,serif;color:var(--y);margin:.2rem 0 .5rem}}
.blurb{{margin:.2rem 0;color:var(--muted)}}
.tags{{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;margin-top:.7rem}}
.tags span{{font:400 .72rem KHead,serif;letter-spacing:.14em;text-transform:uppercase;border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:.25rem .7rem;color:var(--faint)}}
.tags .meta{{border:0;padding-left:.2rem;color:var(--faint)}}
.prog{{display:flex;flex-direction:column;align-items:center;gap:.3rem;min-width:84px;text-align:center}}
.prog b{{display:block;font:400 1.15rem KHead,serif;color:var(--ink)}}
.prog .cnt{{display:block;font:400 .66rem KHead,serif;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}}
.ring{{width:58px;height:58px;transform:rotate(-90deg)}}
.ring circle{{fill:none;stroke:rgba(80,86,95,.55);stroke-width:2.6}}
.ring .rf{{stroke:var(--y);stroke-linecap:round;stroke-dasharray:0 100;transition:stroke-dasharray .8s ease}}
.card.full .ring .rf{{stroke:var(--green)}}
.foot{{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.75rem 1.4rem;border-top:1px solid var(--line);font-size:.92rem}}
.foot[hidden]{{display:none}}
.resume{{font-family:KHead,serif;color:var(--y);font-size:1.05rem}}
.resume:hover{{text-decoration:underline;text-underline-offset:3px}}
.seen{{color:var(--faint);font-style:italic}}
.empty{{text-align:center;color:var(--faint);padding:2rem}}
footer{{text-align:center;color:#5d564b;font-size:.85rem;padding:0 1rem 3rem}}
@media(max-width:600px){{.main{{flex-wrap:wrap}}.main img{{width:60px;height:60px}}.txt{{flex-basis:calc(100% - 80px)}}.prog{{flex-direction:row;min-width:0;width:100%;justify-content:flex-start;gap:.8rem;padding-top:.4rem;border-top:1px solid var(--line);text-align:left}}.ring{{width:40px;height:40px}}.foot{{flex-direction:column;align-items:flex-start;gap:.2rem}}}}
</style></head><body><header><h1>Field Notes</h1><p>Guides, checklists &amp; notes</p><div class="rule"></div></header>
<main>{tools}{cards}<p class="empty" hidden>Nothing matches.</p></main>
<footer>{len(items)} {'entry' if len(items) == 1 else 'entries'}</footer>
<script>
var META={json.dumps({k: {x: v[x] for x in ("key", "total", "exclude", "labels")} for k, v in metas.items()}, ensure_ascii=False)};
function ago(t){{var s=(Date.now()-t)/1000;if(s<60)return 'just now';var u=[[86400*365,'year'],[86400*30,'month'],[86400*7,'week'],[86400,'day'],[3600,'hour'],[60,'minute']];
  for(var i=0;i<u.length;i++){{var n=Math.floor(s/u[i][0]);if(n>=1)return n+' '+u[i][1]+(n>1?'s':'')+' ago';}}}}
document.querySelectorAll('.card').forEach(function(c){{
  var m=META[c.dataset.slug];if(!m)return;var st={{}};try{{st=JSON.parse(localStorage.getItem(m.key)||'{{}}')}}catch(e){{}}
  var n=Object.keys(st).filter(function(k){{return st[k]&&(!m.exclude||k.indexOf(m.exclude)!==0)}}).length,p=Math.min(100,100*n/m.total);
  c.querySelector('.rf').style.strokeDasharray=p+' 100';c.querySelector('.pct').textContent=(p>0&&p<1?'<1':Math.round(p))+'%';
  c.querySelector('.cnt').textContent=n?n+' / '+m.total:'Not started';c.classList.toggle('full',n>=m.total);
  var last=localStorage.getItem(m.key+'-last'),opened=+localStorage.getItem(m.key+'-opened'),f=c.querySelector('.foot');
  if(last&&m.labels[last]){{var r=f.querySelector('.resume');r.href=c.dataset.slug+'/#'+last;r.textContent='Continue · Visit '+last.slice(1)+' — '+m.labels[last]+' →';f.hidden=false;}}
  if(opened){{f.querySelector('.seen').textContent='Opened '+ago(opened);f.hidden=false;}}
}});
var q=document.getElementById('q'),on=null;
function filt(){{var t=q?q.value.trim().toLowerCase():'',vis=0;document.querySelectorAll('.card').forEach(function(c){{
  var ok=(!t||c.textContent.toLowerCase().indexOf(t)>=0)&&(!on||c.dataset.tags.split('|').indexOf(on)>=0);c.hidden=!ok;if(ok)vis++;}});
  document.querySelector('.empty').hidden=vis>0;}}
if(q){{q.addEventListener('input',filt);document.querySelectorAll('.tagbar .tag').forEach(function(b){{b.onclick=function(){{
  on=on===b.dataset.t?null:b.dataset.t;document.querySelectorAll('.tagbar .tag').forEach(function(x){{x.classList.toggle('on',x.dataset.t===on)}});filt();}}}});}}
</script></body></html>"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page)
for f in ("apple-touch-icon.png", "favicon-32.png", "icon-192.png", "icon-512.png"):
    shutil.copy(os.path.join(H, "hub", f), ROOT)
json.dump({"name": "Field Notes", "short_name": "Field Notes", "start_url": "./", "scope": "./", "display": "standalone",
           "background_color": "#000000", "theme_color": "#000000",
           "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(os.path.join(ROOT, "manifest.webmanifest"), "w"), indent=1)
print("hub built:", len(items), "entries")
