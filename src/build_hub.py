"""Builds the Field Notes home page (index.html) from src/guides.json."""
import base64, html, json, os, shutil
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); E = html.escape
f64 = lambda fn: base64.b64encode(open(os.path.join(H, "fonts", fn), "rb").read()).decode()
items = json.load(open(os.path.join(H, "guides.json"), encoding="utf-8"))
cards = "".join(
    f'<a class="card" href="{E(g["slug"])}/"><img src="{E(g["slug"])}/icon-192.png" alt="" width="72" height="72">'
    f'<div><h2>{E(g["title"])}</h2><p class="sub">{E(g["subtitle"])}</p><p>{E(g["blurb"])}</p>'
    f'<div class="tags">{"".join(f"<span>{E(t)}</span>" for t in g.get("tags", []))}</div></div></a>' for g in items)
page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#000000"><title>Field Notes</title>
<meta name="description" content="Personal collection of guides, checklists and notes.">
<link rel="icon" href="favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="Field Notes">
<style>
@font-face{{font-family:KBlack;src:url(data:font/woff2;base64,{f64('unifraktur-400-normal.woff2')}) format("woff2")}}
@font-face{{font-family:KHead;src:url(data:font/woff2;base64,{f64('bellefair-400-normal.woff2')}) format("woff2")}}
@font-face{{font-family:KBody;src:url(data:font/woff2;base64,{f64('alegreya-400-normal.woff2')}) format("woff2")}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:radial-gradient(ellipse 80% 50% at 50% 0%,#141418,#000 70%) fixed #000;color:#f1ecda;font:18px/1.6 KBody,Georgia,serif;-webkit-font-smoothing:antialiased}}
header{{text-align:center;padding:5rem 1.2rem 2.5rem}}h1{{font:400 clamp(3rem,10vw,5.5rem)/1 KBlack,serif;margin:0}}
header p{{font-family:KHead,serif;color:#fceb2d;font-size:1.35rem;margin:.9rem 0 0}}
main{{max-width:760px;margin:0 auto;padding:0 1.2rem 5rem;display:grid;gap:1.2rem}}
.card{{display:flex;gap:1.3rem;align-items:flex-start;padding:1.4rem;border:1px solid rgba(80,86,95,.5);border-radius:14px;background:rgba(10,10,11,.9);color:inherit;text-decoration:none;transition:border-color .2s,transform .2s}}
.card:hover{{border-color:#fceb2d;transform:translateY(-2px)}}.card img{{border-radius:16px;flex-shrink:0}}
h2{{font:400 1.7rem/1.15 KHead,serif;margin:0}}.sub{{font-family:KHead,serif;color:#fceb2d;margin:.2rem 0 .5rem}}.card p{{margin:.2rem 0;color:#b8b2a1}}
.tags{{display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.7rem}}.tags span{{font:400 .72rem KHead,serif;letter-spacing:.14em;text-transform:uppercase;border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:.25rem .7rem;color:#8a8476}}
footer{{text-align:center;color:#5d564b;font-size:.85rem;padding:0 1rem 3rem}}
@media(max-width:560px){{.card{{flex-direction:column}}}}
</style></head><body><header><h1>Field Notes</h1><p>Guides, checklists &amp; notes</p></header><main>{cards}</main>
<footer>{len(items)} {'entry' if len(items) == 1 else 'entries'}</footer></body></html>"""
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page)
for f in ("apple-touch-icon.png", "favicon-32.png", "icon-192.png", "icon-512.png"):
    shutil.copy(os.path.join(H, "hub", f), ROOT)
print("hub built:", len(items), "entries")
