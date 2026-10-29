"""Builds the KCD1 quest-order guide (HTML + Markdown).

Usage:  python src/kcd1/build.py <out_dir>     # site build (index.html, md, meta.json, PWA files)
        python src/kcd1/build.py               # standalone copy to ~/Downloads
"""
import base64, hashlib, html, json, os, re, shutil, sys
from bs4 import BeautifulSoup

W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
from route import SECTIONS, SOURCE_URL, SOURCE_AUTHOR, CHECKPOINTS  # noqa: E402
from style import CSS as BASE_CSS  # noqa: E402

E = html.escape
J = lambda f: json.load(open(os.path.join(W, f), encoding="utf-8"))
Q, AN, RQ, IMM = J("quests.json"), J("analysis.json"), J("reqs.json"), J("immersion.json")
OLD_APPX = BeautifulSoup(open(os.path.join(W, "appendix.html"), encoding="utf-8").read(), "html.parser")
KEY = "kcd1-guide-v2"
DLCS = ["A Woman's Lot", "Band of Bastards", "From the Ashes", "The Amorous Adventures of Bold Sir Hans Capon"]

# Old per-visit "prepare" lines and immersion banners, re-homed onto quests.
PREP_AT = {"20": "In God's Hands", "45": "Rattay Tourney", "46": "The Hunt Begins", "48": "On the Scent",
           "50": "Baptism of Fire", "57": "A Rock and a Hard Place", "60": "Talmberg Horse Race",
           "62": "At Your Service, My Lady", "72": "The King's Silver", "85": "All that Glisters", "87": "Interlopers",
           "93": "A Place to Call Home", "95": "Next to Godliness", "101": "If You Can't Beat 'em",
           "104": "Poverty, Chastity and Obedience", "106": "Payback", "107": "Night Raid",
           "110": "Revenge of the Cuman King", "111": "Cold Steel, Hot Blood"}
PREP = {q: RQ["visits"][v] for v, q in PREP_AT.items() if v in RQ["visits"]}
PREP["A Rock and a Hard Place"] = "The quarry wages heist runs on a five-day clock once the lads have a plan."
PREP["If You Can't Beat 'em"] = "Join the fight club through the Sasau tanner — Revenge of the Cuman King depends on it."
PREP["Poverty, Chastity and Obedience"] = ("Your belongings are confiscated at the gate; plan on Speech to get lockpicks from Cellarius. "
                                           "Shave and reset your hair first — most cutscenes from here on are pre-rendered.")
IMM_AT = {"2": "The Good Thief", "17": "Mightier than the Sword", "45": "Train Hard, Fight Easy", "50": "Baptism of Fire",
          "104": "In the Cloister", "112": "Epilogue"}
QIMM = {q: IMM["visits"][v][0] for v, q in IMM_AT.items() if IMM["visits"].get(v)}


def slug(n):
    return "q-" + re.sub(r"[^a-z0-9]+", "-", n.lower().replace("'", "")).strip("-")


# ---------- assemble ----------
secs, num = [], 0
for si, (title, summary, items) in enumerate(SECTIONS):
    qs = []
    for name, line, fl in items:
        num += 1
        q = dict(Q[name]); q.update(name=name, line=line, flags=fl, n=num, id=slug(name), sec=si)
        qs.append(q)
    secs.append({"title": title, "summary": summary, "quests": qs, "id": f"s{si+1}", "cp": CHECKPOINTS[si]})
ALLQ = [q for s in secs for q in s["quests"]]
NQ = len(ALLQ)
assert len({q["id"] for q in ALLQ}) == NQ
MIGRATE = {q["old_last"]: q["id"] for q in ALLQ if q.get("old_last")}


def short_name(n):
    return n.replace("The Madonna of Sasau — ", "Madonna · ")


def badge_cls(b):
    return "t-dlc" if b.startswith("DLC") else {"MAIN": "t-main", "SIDE": "t-side", "ACTIVITY": "t-act"}.get(b, "t-obj")


NOTE = {"w": ("warn", "Warning"), "m": ("miss", "Missable"), "r": ("rp", "Role-play"), "i": ("info", "Note"),
        "c": ("choice", "Recommended"), "a": ("alt", "Alternative")}
MD_ICON = {"w": "⚠", "m": "🔒", "r": "🎭", "i": "ℹ"}


# ---------- HTML ----------
def flag_tags(fl):
    t = []
    if fl.get("timed"):
        t.append(f'<span class="flag f-timed" title="{E(fl["timed"])}">Timed</span>')
    if fl.get("nr"):
        t.append('<span class="flag f-nr">No return</span>')
    if fl.get("excl"):
        t.append('<span class="flag f-excl">Exclusive</span>')
    if fl.get("moved"):
        t.append('<span class="flag f-moved">Moved</span>')
    if fl.get("added"):
        t.append('<span class="flag f-added">Added</span>')
    return "".join(t)


def quest_html(q):
    fl = q["flags"]
    link = f'<a href="{E(q["url"])}" target="_blank" rel="noopener" title="Open on the wiki">{E(q["name"])}</a>'
    h = [f'<article class="q" id="{q["id"]}" data-type="{q["type"]}" data-dlc="{E(q["dlc"])}"'
         f' data-timed="{1 if fl.get("timed") else 0}">',
         f'<label class="ckwrap"><input type="checkbox" class="ck" data-id="{q["id"]}" aria-label="Done: {E(q["name"])}"></label>',
         '<details><summary>',
         f'<span class="qn">{q["n"]}</span><span class="qh"><h4 class="ename">{link}</h4>',
         f'<span class="tags"><span class="tag {badge_cls(q["badge"])}">{E(q["badge"])}</span>{flag_tags(fl)}</span>',
         f'<span class="ql">{E(q["line"])}</span></span><span class="chev" aria-hidden="true"></span></summary><div class="ebody">']
    for k in ("timed", "excl", "moved", "added"):
        if fl.get(k) and k != "timed":
            lab = {"excl": "Exclusive", "moved": "Moved", "added": "Added"}[k]
            h.append(f'<div class="note {"warn" if k == "excl" else "info"}"><span class="lbl">{lab}</span>{E(fl[k])}</div>')
    if fl.get("timed"):
        h.append(f'<div class="note warn"><span class="lbl">Timed</span>{E(fl["timed"][0].upper() + fl["timed"][1:])}.</div>')
    if fl.get("nr"):
        h.append('<div class="note miss"><span class="lbl">Point of no return</span>Entering Vranik locks out several side quests. Finish what you want first.</div>')
    if q.get("where"):
        h.append(f'<p class="where"><span class="lbl">Where to find</span>{E(q["where"])}</p>')
    rq = RQ["quests"].get(q["name"])
    if rq and (rq.get("req") or rq.get("prep")):
        rows = [(k, l, rq[k]) for k, l in (("req", "Requires"), ("prep", "Bring")) if rq.get(k)]
        h.append('<div class="reqs">' + "".join(f'<div class="rq rq-{k}"><span class="lbl">{l}</span>'
                 + "".join(f'<span class="chip">{E(x)}</span>' for x in xs) + "</div>" for k, l, xs in rows) + "</div>")
    if PREP.get(q["name"]):
        h.append(f'<div class="note prep"><span class="lbl">Prepare</span>{E(PREP[q["name"]])}</div>')
    if q["steps"]:
        h.append('<ol class="steps">' + "".join(f"<li>{E(s)}</li>" for s in q["steps"]) + "</ol>")
    for k, t in q["notes"]:
        if k == "pc":
            h.append(f'<div class="note pc"><span class="lbl">PC only · console command</span><pre><code>{E(t)}</code></pre></div>')
        else:
            c, l = NOTE[k]
            h.append(f'<div class="note {c}"><span class="lbl">{l}</span>{E(t)}</div>')
    if QIMM.get(q["name"]):
        h.append(f'<div class="note rp"><span class="lbl">Immersion</span>{E(QIMM[q["name"]])}</div>')
    a = AN.get(q["name"])
    if a:
        cells = [(k, l) for k, l in (("outcome", "Outcome"), ("tip", "Tip"), ("immersion", "Immersion")) if a.get(k)]
        if cells:
            h.append('<div class="an">' + "".join(f'<div class="an-{k}"><h5>{l}</h5><p>{E(a[k])}</p></div>' for k, l in cells) + "</div>")
    if q.get("reward"):
        h.append(f'<div class="efoot"><span class="reward"><span class="lbl">Reward</span>{E(q["reward"])}</span></div>')
    if q["spoilers"]:
        h.append('<details class="spoiler"><summary>Reveal story outcome</summary>' + "".join(f"<p>{E(s)}</p>" for s in q["spoilers"]) + "</details>")
    h.append("</div></details></article>")
    return "".join(h)


RING = '<svg class="ring" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.5"/><circle class="rf" cx="18" cy="18" r="15.5" pathLength="100"/></svg>'


def section_html(i, s):
    n = len(s["quests"])
    return (f'<section class="act" id="{s["id"]}"><header class="band"><div class="actno">Part {i+1}</div>'
            f'<h2>{E(s["title"])}</h2><p>{E(s["summary"])}</p>'
            f'<div class="actprog" data-act="{s["id"]}">{RING}<span>0 / {n} done</span></div></header>'
            f'<div class="qlist">{"".join(quest_html(q) for q in s["quests"])}</div>'
            f'<aside class="checkpoint"><span class="lbl">Checkpoint · end of Part {i+1}</span><p>{E(s["cp"])}</p></aside></section>')


def sidebar_html():
    h = ['<nav id="sidebar" aria-label="Contents"><div class="navhead">Contents</div><a class="nimm" href="#immersion">Immersion Charter</a><ol class="nacts">']
    for i, s in enumerate(secs):
        h.append(f'<li><a class="nact" href="#{s["id"]}" data-act="{s["id"]}">{RING}<span>Part {i+1}</span>{E(s["title"])}</a><ol>')
        h += [f'<li><a href="#{q["id"]}"><span>{q["n"]}</span>{E(short_name(q["name"]))}</a></li>' for q in s["quests"]]
        h.append("</ol></li>")
    h.append('<li><a class="nact" href="#appendix"><span>Appendix</span>Reference</a></li></ol></nav>')
    return "".join(h)


def charter_html():
    h = ['<details class="frame charter" id="immersion"><summary><div class="orn" aria-hidden="true">✠</div>',
         '<h2>The Immersion Charter</h2>', f'<p class="lead">{E(IMM["intro"])}</p><span class="open">Show the rules</span></summary><div class="cgrid">']
    for g in IMM["groups"]:
        h.append(f'<div><h3>{E(g["title"])}</h3><ul>' + "".join(f"<li>{E(x)}</li>" for x in g["rules"]) + "</ul></div>")
    h.append(f'</div><p class="src">{E(IMM["source"])}</p></details>')
    return "".join(h)


def qa(name):
    return f'<a href="#{slug(name)}">{E(short_name(name))}</a>'


def appendix_html():
    moved = [q for q in ALLQ if q["flags"].get("moved") or q["flags"].get("added")]
    h = ['<section class="appendix" id="appendix"><h2>Appendices</h2>',
         '<h3>1. Source &amp; changes</h3>',
         f'<p>Quest order follows <a href="{E(SOURCE_URL)}" target="_blank" rel="noopener">{E(SOURCE_AUTHOR)}\'s list of all quests in the order to start them</a> '
         '(r/kingdomcome). It groups quests by location to cut travel. It lists when to <b>start</b> each quest; many run side by side, so finish them when convenient. '
         'Summaries, steps and analysis are written for this guide and checked against the KCD Wiki.</p><ul>']
    h += [f'<li>{qa(q["name"])} — <b>{"Moved" if q["flags"].get("moved") else "Added"}.</b> {E(q["flags"].get("moved") or q["flags"].get("added"))}</li>' for q in moved]
    h.append(f'<li>Grouped entries in the post are split into their individual quests: A Woman\'s Lot, the Madonna of Sasau chapters, Band of Bastards, the monastery side quests and the Pribyslavitz rebuild.</li>'
             f'<li>{qa("Hare Hunt")} and {qa("Sheep in Wolf\'s Clothing")} are mutually exclusive; the guide follows the poachers so {qa("Emergency Supply")} stays available.</li></ul>')
    counts = {}
    for q in ALLQ:
        counts[q["badge"]] = counts.get(q["badge"], 0) + 1
    h.append('<h3>2. Coverage</h3><table><tr><th>Type</th><th>Quests</th></tr>'
             + "".join(f"<tr><td>{E(b)}</td><td>{c}</td></tr>" for b, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])))
             + f'<tr><td><b>Total</b></td><td><b>{NQ}</b></td></tr></table>'
             '<p>Treasures of the Past (five treasure maps) has no quest entry — see below.</p>')
    h.append('<h3>3. Activities &amp; collectibles</h3><ul>'
             '<li><b><a href="https://kingdomcomedeliverance.wiki.gg/wiki/Treasures_of_the_Past" target="_blank" rel="noopener">Treasures of the Past</a></b> — five ancient maps turn up as loot; each leads to a buried chest with a piece of the Warhorse armour. Nothing is missable.</li>'
             f'<li><b>Tourneys</b> — {qa("Rattay Tourney")} runs weekly; bet on yourself in {qa("Who Do You Like")} and fight for Capon in {qa("Capon\'s Champion")}.</li>'
             f'<li><b>Races &amp; archery</b> — {qa("Talmberg Horse Race")} and {qa("Chumps on the River")}.</li>'
             f'<li><b>Fist fights</b> — {qa("Do Me a Favour - Punch Me!")}, {qa("Fishy Business in Uzhitz")}, the Sasau fight club in {qa("If You Can\'t Beat \'em")}, then {qa("Revenge of the Cuman King")} (Unarmed 8).</li>'
             f'<li><b>Open-ended jobs</b> — {qa("The Queen of Sheba\'s Sword")}, {qa("Fat Profits")}, {qa("Green-Eyed Monster")}, {qa("Skin")}: finish at your own pace.</li></ul>')
    rec = OLD_APPX.find(lambda t: t.name == "h3" and "Pribyslavitz" in t.get_text())
    if rec:
        tbl = rec.find_next("table")
        for c in tbl.select("input"):
            c["data-id"] = c["data-id"]
        h.append("<h3>4. Pribyslavitz recruit checklist</h3>" + str(tbl))
    h.append('<h3>5. Timed quests &amp; points of no return</h3><ol>')
    for q in ALLQ:
        fl = q["flags"]
        if fl.get("timed"):
            h.append(f'<li>{qa(q["name"])} — timed: {E(fl["timed"])}.</li>')
        if fl.get("nr"):
            h.append(f'<li>{qa(q["name"])} — <b>point of no return</b>: Vranik locks out remaining side quests.</li>')
        if fl.get("excl"):
            h.append(f'<li>{qa(q["name"])} — {E(fl["excl"])}.</li>')
    h.append('</ol><h3>6. Good to know</h3><ul>'
             '<li>Quest links go to kingdomcomedeliverance.wiki.gg; all were checked.</li>'
             '<li>Vengeance stays open on the wiki after the credits; tick it off at the end here.</li>'
             '<li>The Family Silver has very little wiki detail, so its steps are general.</li>'
             '<li>The ~10,800 groschen for Pribyslavitz is an estimate; "Speech above 17" for Marius works around a known bug.</li>'
             '<li>Your ticks from the previous version of this guide are carried over automatically where a quest\'s final step was ticked.</li>'
             '</ul></section>')
    return "".join(h)


EXTRA_CSS = r"""
.qlist{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:1rem 0}
.q{display:grid;grid-template-columns:auto 1fr;column-gap:.85rem;padding:0 1.2rem;border-top:1px solid var(--line);scroll-margin-top:calc(var(--hh) + 12px)}
.q:first-child{border-top:0}
.q .ckwrap{padding-top:1.12rem}
.q>details>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:2.1rem 1fr auto;column-gap:.6rem;align-items:start;padding:.95rem 0}
.qn{font-family:var(--head);color:var(--y);font-size:1.05rem;text-align:right;padding-top:.2rem;font-variant-numeric:tabular-nums}
.qh{min-width:0}
.q .ename{font-size:1.35rem;display:inline}
.q .tags{display:inline-flex;margin:0 0 0 .55rem;vertical-align:.18em;gap:.3rem}
.ql{display:block;color:var(--muted);font-size:.97rem;line-height:1.45;margin-top:.15rem}
.q .chev{margin-top:.55rem}
.q details[open]>summary{border-bottom:0}
.q .ebody{margin-left:2.7rem;padding-bottom:1.1rem}
.q.cur{box-shadow:inset 2px 0 0 var(--y)}
.q.done{opacity:.42}.q.done .ename a{text-decoration:line-through;text-decoration-thickness:1px}
.flag{font-family:var(--head);font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;line-height:1;padding:.3rem .55rem .24rem;border-radius:999px}
.f-timed{background:rgba(241,191,59,.14);color:var(--warn)}.f-nr{background:rgba(239,90,76,.16);color:var(--miss)}
.f-excl{background:rgba(194,148,232,.14);color:var(--dlc)}.f-moved{background:rgba(134,175,227,.14);color:var(--side)}.f-added{background:var(--y);color:#000}
.note.prep{border-left-color:var(--act)}.note.prep .lbl{color:var(--act)}
.charter{padding:0}
.charter>summary{list-style:none;cursor:pointer;padding:2rem 2rem 1.4rem;text-align:center}
.charter .open{font-family:var(--head);font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);border-bottom:1px dashed var(--faint)}
.charter[open] .open{display:none}
.charter .lead{margin-bottom:.8rem}
.charter .cgrid,.charter .src{padding:0 2rem}.charter .src{padding-bottom:1.6rem}
.an{grid-template-columns:none;grid-auto-flow:column;grid-auto-columns:1fr}
#timedonly.on,#mainonly.on{border-color:var(--y);color:var(--y)}
@media (max-width:860px){.q{padding:0 .8rem}.q>details>summary{grid-template-columns:1.6rem 1fr auto}.q .ebody{margin-left:0}.q .ename{font-size:1.2rem}.an{grid-auto-flow:row}.q .tags{display:flex;margin:.3rem 0 0}}
@media print{.q details>*{display:block}}
"""

JS = r"""
(function(){
var KEY='__KEY__',st={};
try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
(function(){if(Object.keys(st).length)return;var M=__MIGRATE__,o;try{o=JSON.parse(localStorage.getItem('kcd1-guide-v1')||'{}')}catch(e){return}
  var n=0;Object.keys(o).forEach(function(k){if(o[k]&&(M[k]||k.indexOf('rec-')===0)){st[M[k]||k]=true;n++}});if(n)localStorage.setItem(KEY,JSON.stringify(st));})();
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
var $=function(s,r){return (r||document).querySelector(s)},$$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
var boxes=$$('.ck'),quest=boxes.filter(function(b){return !b.classList.contains('ck-extra')});
function refresh(){
  var d=quest.filter(function(b){return b.checked}).length;
  $('#progtxt').textContent=d+' / '+quest.length;$('.track i').style.width=(100*d/quest.length)+'%';
  $$('.act').forEach(function(a){var bs=$$('.q .ck',a),n=bs.filter(function(b){return b.checked}).length,p=bs.length?100*n/bs.length:0;
    $$('[data-act="'+a.id+'"]').forEach(function(x){var r=$('.ring',x);$('.rf',r).style.strokeDasharray=p+' 100';r.classList.toggle('full',n===bs.length);
      if(x.classList.contains('actprog'))$('span:last-child',x).textContent=n+' / '+bs.length+' done';});});
  filter();
}
boxes.forEach(function(b){
  b.checked=!!st[b.dataset.id];var q=b.closest('.q');if(q)q.classList.toggle('done',b.checked);
  b.addEventListener('change',function(){if(b.checked)st[b.dataset.id]=true;else delete st[b.dataset.id];if(q)q.classList.toggle('done',b.checked);save();refresh();});
});
var s=$('#search'),hide=$('#hidedone'),dlc=$('#dlcsel'),types=$$('.tf'),to=$('#timedonly'),mo=$('#mainonly');
function filter(){
  var term=s.value.trim().toLowerCase(),on={};types.forEach(function(t){on[t.value]=t.checked});
  var dv=dlc.value,tim=to.classList.contains('on'),any=!!(term||dv||tim||hide.checked||types.some(function(t){return !t.checked}));
  $$('.q').forEach(function(e){var ok=on[e.dataset.type];if(dv)ok=ok&&e.dataset.dlc===dv;if(tim)ok=ok&&e.dataset.timed==='1';
    if(hide.checked&&e.classList.contains('done'))ok=false;if(term&&e.textContent.toLowerCase().indexOf(term)<0)ok=false;
    e.classList.toggle('hidden',!ok);if(term&&ok)$('details',e).open=true;});
  $$('.act').forEach(function(a){a.classList.toggle('hidden',any&&$$('.q:not(.hidden)',a).length===0)});
  $('#immersion').classList.toggle('hidden',any);
}
[s,hide,dlc].concat(types).forEach(function(el){el.addEventListener('input',filter);el.addEventListener('change',filter)});
mo.onclick=function(){var on=!mo.classList.contains('on');mo.classList.toggle('on',on);types.forEach(function(t){t.checked=on?t.value==='MAIN':true});filter();};
types.forEach(function(t){t.addEventListener('change',function(){mo.classList.toggle('on',types.every(function(x){return x.checked===(x.value==='MAIN')}))})});
to.onclick=function(){to.classList.toggle('on');filter();};
var fb=$('#ftog'),fp=$('.filters');fb.onclick=function(){var o=fp.classList.toggle('open');fb.setAttribute('aria-expanded',o);hh()};
$('#expand').onclick=function(){$$('.q details:not(.spoiler)').forEach(function(d){d.open=true})};
$('#collapse').onclick=function(){$$('.q details').forEach(function(d){d.open=false})};
$('#reset').onclick=function(){if(confirm('Clear every tick?')){st={};save();boxes.forEach(function(b){b.checked=false;var q=b.closest('.q');if(q)q.classList.remove('done')});refresh();}};
function toast(t){var m=$('#msg');m.textContent=t;m.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(function(){m.hidden=true},2600);}
function go(el,flash){var d=$('details',el);if(d)d.open=true;window.scrollTo({top:el.getBoundingClientRect().top+scrollY-$('.bar').offsetHeight-14});
  if(flash){el.classList.remove('flash');void el.offsetWidth;el.classList.add('flash');}}
$('#nexttodo').onclick=function(){var b=quest.filter(function(b){return !b.checked&&!b.closest('.hidden')})[0];if(!b){toast('Everything visible is ticked off. Well done, Henry.');return;}go(b.closest('.q'),true);};
$('#export').onclick=function(){var blob=new Blob([JSON.stringify({app:'kcd1-quest-guide',version:2,exported:new Date().toISOString(),ticks:st,last:localStorage.getItem(KEY+'-last')},null,1)],{type:'application/json'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='kcd1-progress-'+new Date().toISOString().slice(0,10)+'.json';document.body.appendChild(a);a.click();a.remove();toast('Exported '+Object.keys(st).length+' ticks');};
$('#import').onclick=function(){$('#importf').click()};
$('#importf').onchange=function(){var f=this.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){try{var j=JSON.parse(rd.result),t=j.ticks||j,M=__MIGRATE__;if(typeof t!=='object')throw 0;
  if(Object.keys(st).length&&!confirm('Replace your current '+Object.keys(st).length+' ticks with the ones in this file?'))return;
  st={};Object.keys(t).forEach(function(k){if(t[k])st[M[k]||k]=true});save();boxes.forEach(function(b){b.checked=!!st[b.dataset.id];var q=b.closest('.q');if(q)q.classList.toggle('done',b.checked)});refresh();toast('Imported '+Object.keys(st).length+' ticks');
  }catch(e){alert('That file is not a KCD1 guide progress export.')}};rd.readAsText(f);this.value='';};
var sb=$('#sidebar');$('#hamb').onclick=function(e){e.stopPropagation();sb.classList.toggle('open')};
document.addEventListener('click',function(e){if(sb.classList.contains('open')&&!sb.contains(e.target))sb.classList.remove('open')});
$$('a[href^="#q-"]').forEach(function(a){a.addEventListener('click',function(ev){var t=document.getElementById(a.getAttribute('href').slice(1));if(!t)return;ev.preventDefault();sb.classList.remove('open');
  if(t.classList.contains('hidden')){types.forEach(function(x){x.checked=true});mo.classList.remove('on');to.classList.remove('on');s.value='';dlc.value='';hide.checked=false;filter();}go(t,true);history.replaceState(null,'','#'+t.id);})});
$$('#sidebar a[href^="#s"],#sidebar a[href="#appendix"],#sidebar a[href="#immersion"]').forEach(function(a){a.addEventListener('click',function(){sb.classList.remove('open')})});
function hh(){document.documentElement.style.setProperty('--hh',$('.bar').offsetHeight+'px')}window.addEventListener('resize',hh);hh();
var tt=$('#totop');tt.onclick=function(){window.scrollTo({top:0})};
try{localStorage.setItem(KEY+'-opened',Date.now())}catch(e){}
var links={};$$('#sidebar ol ol a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a});
var LK=KEY+'-last',cur,cv,lastT;
if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){if(!en.isIntersecting)return;
  if(cur)cur.classList.remove('on');if(cv)cv.classList.remove('cur');cv=en.target;cv.classList.add('cur');cur=links[cv.id];
  if(cur){cur.classList.add('on');var r=cur.getBoundingClientRect(),b=sb.getBoundingClientRect();if(r.top<b.top+40||r.bottom>b.bottom-40)sb.scrollTop+=r.top-b.top-b.height/2;}})},{rootMargin:'-35% 0px -60% 0px'});
  $$('.q').forEach(function(q){io.observe(q)});}
window.addEventListener('scroll',function(){tt.classList.toggle('show',scrollY>1200);clearTimeout(lastT);lastT=setTimeout(function(){if(cv&&scrollY>400)try{localStorage.setItem(LK,cv.id)}catch(e){}},500)},{passive:true});
(function(){var h=location.hash.slice(1),el=h&&document.getElementById(h);if(el&&el.classList.contains('q')){setTimeout(function(){go(el,true)},50);return;}
  var l=localStorage.getItem(LK),q=l&&document.getElementById(l);if(!q||h)return;var r=$('#resume');
  $('.rgo',r).innerHTML='Resume at <b>#'+$('.qn',q).textContent+'</b> · '+$('.ename',q).textContent;r.hidden=false;
  $('.rgo',r).onclick=function(){r.hidden=true;go(q)};$('.rx',r).onclick=function(){r.hidden=true};setTimeout(function(){r.hidden=true},15000);})();
window.addEventListener('beforeprint',function(){$$('details').forEach(function(d){d.dataset.w=d.open;d.open=true})});
window.addEventListener('afterprint',function(){$$('details').forEach(function(d){d.open=d.dataset.w==='true'})});
refresh();
})();
"""


def fonts_css():
    f = lambda fn: base64.b64encode(open(os.path.join(W, "..", "fonts", fn), "rb").read()).decode()
    return (f'@font-face{{font-family:"KBlack";src:url(data:font/woff2;base64,{f("unifraktur-400-normal.woff2")}) format("woff2");font-display:swap}}'
            f'@font-face{{font-family:"KHead";src:url(data:font/woff2;base64,{f("bellefair-400-normal.woff2")}) format("woff2");font-display:swap}}'
            f'@font-face{{font-family:"KBody";src:url(data:font/woff2;base64,{f("alegreya-400-normal.woff2")}) format("woff2");font-weight:400 800;font-display:swap}}'
            f'@font-face{{font-family:"KBody";font-style:italic;src:url(data:font/woff2;base64,{f("alegreya-400-italic.woff2")}) format("woff2");font-display:swap}}')


PWA_HEAD = ('<link rel="manifest" href="manifest.webmanifest"><link rel="icon" href="favicon-32.png" type="image/png" sizes="32x32">'
            '<link rel="apple-touch-icon" href="apple-touch-icon.png"><meta name="apple-mobile-web-app-capable" content="yes">'
            '<meta name="apple-mobile-web-app-status-bar-style" content="black"><meta name="apple-mobile-web-app-title" content="KCD Guide">')
PWA_JS = "if('serviceWorker' in navigator&&location.protocol==='https:'){window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js')})}"


def build_html(pwa=False):
    ntimed = sum(1 for q in ALLQ if q["flags"].get("timed"))
    tf = "".join(f'<label class="pill"><input type="checkbox" class="tf" value="{v}" checked><span>{l}</span></label>'
                 for v, l in [("MAIN", "Main"), ("SIDE", "Side"), ("DLC", "DLC"), ("ACTIVITY", "Activity")])
    dopts = '<option value="">All content</option>' + "".join(f'<option value="{E(d)}">{E(d)}</option>' for d in DLCS)
    js = JS.replace("__KEY__", KEY).replace("__MIGRATE__", json.dumps(MIGRATE))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#000000">
<meta name="description" content="Every Kingdom Come: Deliverance quest and DLC in the order to start them, with steps, requirements and tips.">
<title>Kingdom Come: Deliverance — Quest Order Guide</title>{PWA_HEAD if pwa else ""}
<style>{fonts_css()}{BASE_CSS}{EXTRA_CSS}</style></head>
<body>
<header class="hero" id="top">
{'<a class="home" href="../">← Field Notes</a>' if pwa else ''}<div class="crest" aria-hidden="true">♛</div>
<h1>Kingdom Come<span>Deliverance</span></h1>
<p class="sub">Every Quest, in the Order to Start It</p>
<p class="intro">A completionist route grouped by location so you cross the map as little as possible — based on <a href="{E(SOURCE_URL)}" target="_blank" rel="noopener">{E(SOURCE_AUTHOR)}'s list</a>, expanded with steps, requirements and tips for every quest.</p>
<div class="legend" aria-label="Legend"><span class="tag t-main">Main</span><span class="tag t-side">Side</span><span class="tag t-dlc">DLC</span><span class="tag t-act">Activity</span><i></i><span class="flag f-timed">Timed</span><span class="flag f-nr">No return</span><span class="flag f-excl">Exclusive</span><span class="flag f-moved">Moved</span></div>
<div class="stats"><div><b>{NQ}</b>Quests</div><div><b>{len(secs)}</b>Parts</div><div><b>{ntimed}</b>Timed</div><div><b>4</b>Story DLCs</div></div>
</header>
<div class="bar"><div class="barrow">
<button class="btn" id="hamb" aria-label="Contents">☰</button><a class="brand" href="#top">Kingdom Come</a>
<div class="search"><input type="search" id="search" placeholder="Search quests, people, places…" aria-label="Search"></div>
<button class="btn" id="nexttodo" title="Jump to the next unticked quest">Next</button><button class="btn" id="ftog" aria-expanded="false">Filters</button>
<div class="prog"><div class="track"><i></i></div><span id="progtxt">0 / {NQ}</span></div></div>
<div class="filters">
<span class="grp">Show</span><button class="btn" id="mainonly">Main only</button><button class="btn" id="timedonly">Timed only</button>{tf}
<span class="grp">Content</span><select id="dlcsel" aria-label="DLC filter">{dopts}</select>
<label class="pill"><input type="checkbox" id="hidedone"><span>Hide done</span></label>
<span class="grp">View</span><button class="btn" id="expand">Expand all</button><button class="btn" id="collapse">Collapse all</button>
<span class="grp">Progress</span><button class="btn" id="export">Export</button><button class="btn" id="import">Import</button><input type="file" id="importf" accept="application/json,.json" hidden><button class="btn" id="reset">Reset</button>
</div></div>
<div class="layout">{sidebar_html()}<main>
{charter_html()}
{''.join(section_html(i, s) for i, s in enumerate(secs))}
{appendix_html()}
</main></div>
<footer><div class="crest">✠</div>Quest order after {E(SOURCE_AUTHOR)} on r/kingdomcome · quest links to kingdomcomedeliverance.wiki.gg · ticks are saved in this browser (Filters → Export to back them up). Fonts: Bellefair, Alegreya, UnifrakturMaguntia (SIL OFL).</footer>
<button class="btn" id="totop" aria-label="Back to top">↑</button>
<div id="resume" class="toast" hidden><button class="rgo"></button><button class="rx" aria-label="Dismiss">✕</button></div>
<div id="msg" class="toast msg" hidden></div>
<script>{js}{PWA_JS if pwa else ""}</script>
</body></html>"""


# ---------- Markdown ----------
def build_md():
    o = ["# Kingdom Come: Deliverance — Every Quest, in the Order to Start It", "",
         f"Completionist route grouped by location, based on [{SOURCE_AUTHOR}'s list]({SOURCE_URL}). {NQ} quests in {len(secs)} parts. Links go to kingdomcomedeliverance.wiki.gg.", "",
         "**Flags:** ⏳ timed · ⛔ point of no return · ⚖ mutually exclusive · ↪ moved from the post's position · ➕ added", ""]
    for i, s in enumerate(secs):
        o += [f"## Part {i+1} — {s['title']}", "", f"*{s['summary']}*", ""]
        for q in s["quests"]:
            fl = q["flags"]
            marks = "".join(m for k, m in (("timed", " ⏳"), ("nr", " ⛔"), ("excl", " ⚖"), ("moved", " ↪"), ("added", " ➕")) if fl.get(k))
            o.append(f"- [ ] **{q['n']}. [{q['name']}]({q['url']})** — `{q['badge']}`{marks} — {q['line']}")
            for k, lab in (("timed", "Timed"), ("excl", "Exclusive"), ("moved", "Moved"), ("added", "Added")):
                if fl.get(k):
                    o.append(f"  - *{lab}:* {fl[k]}")
            if q.get("where"):
                o.append(f"  - *Where:* {q['where']}")
            rq = RQ["quests"].get(q["name"])
            if rq and rq.get("req"):
                o.append("  - **Requires:** " + " · ".join(rq["req"]))
            if rq and rq.get("prep"):
                o.append("  - **Bring:** " + " · ".join(rq["prep"]))
            if PREP.get(q["name"]):
                o.append(f"  - 🎒 **Prepare:** {PREP[q['name']]}")
            o += [f"  {j}. {x}" for j, x in enumerate(q["steps"], 1)]
            for k, t in q["notes"]:
                if k == "pc":
                    o += ["  - 💻 **PC only:**", "    ```", f"    {t}", "    ```"]
                elif k in ("c", "a"):
                    o.append(f"  - **{'Recommended' if k == 'c' else 'Alternative'}:** {t}")
                else:
                    o.append(f"  - {MD_ICON[k]} {t}")
            if QIMM.get(q["name"]):
                o.append(f"  - 🕯 {QIMM[q['name']]}")
            a = AN.get(q["name"]) or {}
            for k, lab in (("outcome", "Outcome"), ("tip", "Tip"), ("immersion", "Immersion")):
                if a.get(k):
                    o.append(f"  - **{lab}:** {a[k]}")
            if q.get("reward"):
                o.append(f"  - 🪙 {q['reward']}")
            if q["spoilers"]:
                o.append("  - <details><summary>Story spoiler</summary>" + " ".join(q["spoilers"]) + "</details>")
        o += ["", f"> 🏁 **Checkpoint — end of Part {i+1}:** {s['cp']}", ""]
    ap = BeautifulSoup(appendix_html(), "html.parser")
    o += ["## Appendices", ""]
    for el in ap.section.children:
        if el.name == "h3":
            o += [f"### {el.get_text()}", ""]
        elif el.name == "p":
            o += [el.get_text(), ""]
        elif el.name in ("ul", "ol"):
            o += [("- " if el.name == "ul" else f"{j}. ") + li.get_text().strip() for j, li in enumerate(el.find_all("li", recursive=False), 1)] + [""]
        elif el.name == "table":
            for j, r in enumerate(el.find_all("tr")):
                cells = [("☐" if c.find("input") else c.get_text().strip().replace("|", "\\|")) or "✓" for c in r.find_all(["th", "td"])]
                o.append("| " + " | ".join(cells) + " |")
                if j == 0:
                    o.append("|" + "---|" * len(cells))
            o.append("")
    return "\n".join(o) + "\n"


def build_site(dest):
    os.makedirs(dest, exist_ok=True)
    open(os.path.join(dest, "index.html"), "w", encoding="utf-8").write(build_html(pwa=True))
    open(os.path.join(dest, "KCD1_Quest_Guide.md"), "w", encoding="utf-8").write(build_md())
    json.dump({"key": KEY, "total": NQ, "exclude": "rec-", "labels": {q["id"]: f"#{q['n']} {short_name(q['name'])}" for q in ALLQ},
               "stats": f"{NQ} quests · {len(secs)} parts"}, open(os.path.join(dest, "meta.json"), "w"), ensure_ascii=False)
    for f in ("manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png", "favicon-32.png"):
        shutil.copy(os.path.join(W, "pwa", f), dest)
    ver = hashlib.sha1(open(os.path.join(dest, "index.html"), "rb").read()).hexdigest()[:10]
    p = os.path.join(dest, "sw.js")
    txt = open(p).read().replace("__VER__", ver)
    open(p, "w").write(txt)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_site(sys.argv[1])
        print(f"site built in {sys.argv[1]}: {NQ} quests, {len(secs)} parts")
    else:
        out = os.path.expanduser("~/Downloads")
        open(os.path.join(out, "KCD1_Quest_Guide.html"), "w", encoding="utf-8").write(build_html())
        open(os.path.join(out, "KCD1_Quest_Guide.md"), "w", encoding="utf-8").write(build_md())
        print("standalone copy written to", out)
