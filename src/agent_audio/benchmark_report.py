"""Offline, blind A/B listening report. No server or external assets required."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path


def _pairs(
    rows: list[dict],
    translations: dict[str, str] | None = None,
    *,
    run_id: str = "legacy",
) -> list[dict]:
    translations = translations or {}
    by_pair: dict[tuple[str, int], dict] = {}
    for row in rows:
        if not row.get("success"):
            continue
        key = (row["id"], row["duration_requested"])
        by_pair.setdefault(key, {})[row["model"]] = row
    result = []
    for (item_id, duration), models in by_pair.items():
        if set(models) != {"small-sfx", "medium"}:
            continue
        small, medium = models["small-sfx"], models["medium"]
        if small["seed"] != medium["seed"] or small["prompt"] != medium["prompt"]:
            raise ValueError(f"Mismatched pair: {item_id} {duration}")
        # Independent of the completed-pair set, including partial recovery.
        identity = json.dumps(
            [run_id, item_id, duration, small["seed"], small["prompt"]],
            ensure_ascii=False,
        )
        digest = hashlib.sha256(identity.encode()).hexdigest()
        swap = int(digest[-1], 16) % 2 == 1
        a, b = (medium, small) if swap else (small, medium)
        result.append(
            {
                "key": f"{item_id}_{duration}s",
                "rating_key": digest,
                "category": small["category"],
                "prompt": small["prompt"],
                "prompt_ko": translations.get(item_id, ""),
                "duration": duration,
                "seed": small["seed"],
                "A": {"model": a["model"], "url": f"audio/{a['case_id']}.wav"},
                "B": {"model": b["model"], "url": f"audio/{b['case_id']}.wav"},
            }
        )
    return result


def write_report(output: Path, *, replace: bool = False) -> Path:
    report = output / "report.html"
    if report.exists() and not replace:
        raise FileExistsError(f"Report exists: {report}")
    rows = [
        json.loads(line)
        for line in (output / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    translations_path = output / "prompt_translations_ko.json"
    translations = (
        json.loads(translations_path.read_text(encoding="utf-8"))
        if translations_path.exists()
        else {}
    )
    metadata_path = output / "run.json"
    metadata = (
        json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_path.exists()
        else {}
    )
    run_id = (
        metadata.get("run_id")
        or hashlib.sha256(
            (
                str(output.resolve())
                + json.dumps(
                    {
                        key: metadata.get(key)
                        for key in (
                            "manifest_sha256",
                            "runtime_revision",
                            "model_revision",
                            "backend",
                            "parameters",
                        )
                    },
                    sort_keys=True,
                )
            ).encode()
        ).hexdigest()
    )
    pairs = _pairs(rows, translations, run_id=run_id)
    retained = len(rows)
    planned = metadata.get("cases")
    pruned = (
        "completed_before_pruning" in metadata
        or "retained_cases" in metadata
        or "pruned" in str(metadata.get("status", ""))
    )
    scope = f"{retained} {'retained result rows' if pruned else 'attempted cases'}; {sum(bool(row.get('success')) for row in rows)} successful {'retained outputs' if pruned else 'outputs'}; {len(pairs)} complete listening pairs."
    if pruned:
        scope += " Results have been pruned; retained rows do not represent total historical attempts."
        if metadata.get("completed_before_pruning") is not None:
            scope += (
                f" Completed before pruning: {metadata['completed_before_pruning']}."
            )
        if metadata.get("retained_cases") is not None:
            scope += f" Metadata retained cases: {metadata['retained_cases']}."
        if metadata.get("retained_durations") is not None:
            scope += f" Retained durations (seconds): {metadata['retained_durations']}."
    if metadata.get("status"):
        scope += f" Run status: {metadata['status']}."
    if planned is not None:
        scope += f" Planned cases: {planned}."
    scope += " Smoke run." if metadata.get("smoke") else ""
    scope += " Only pairs with two successful outputs are shown. Single-seed results and browser ratings do not establish a general quality winner."
    data = json.dumps(pairs, ensure_ascii=False).replace("<", "\\u003c")
    document = TEMPLATE.replace("__PAIRS__", data).replace(
        "__TITLE__", html.escape(output.name)
    )
    document = document.replace(
        "__RUN_ID__", json.dumps(run_id).replace("<", "\\u003c")
    ).replace("__SCOPE__", html.escape(scope))
    report.write_text(document, encoding="utf-8")
    return report


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SFX A/B — __TITLE__</title>
<style>
:root{font-family:system-ui,sans-serif;color:#e9edf2;background:#111927}body{max-width:1100px;margin:auto;padding:24px}
h1{margin-bottom:6px}p{line-height:1.5;color:#b6c4d4}.bar,.samples,.rating{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}
button,select,input,textarea{background:#202d40;color:#fff;border:1px solid #60748a;border-radius:6px;padding:9px}
button{cursor:pointer}button:hover{background:#30435c}.card{flex:1;min-width:300px;background:#1b293a;padding:16px;border-radius:10px}
audio{width:100%}.rating label{display:block;margin:8px 0}.rating select{margin-left:6px}.pill{color:#8fd2dd}
textarea{width:95%;min-height:70px}.muted{color:#9bafc4}#identity{font-weight:bold;color:#f7c875}
</style></head><body>
<h1>SFX model comparison</h1><p>Blind A/B listening. Rate each sample before revealing its model. Ratings stay in this browser; export JSON to keep or share them.</p>
<p class="muted">__SCOPE__</p>
<div class="bar"><label>Category <select id="category"></select></label><label>Duration <select id="duration"><option value="all">All</option></select></label>
<button id="previous">Previous</button><button id="next">Next</button><label><input id="autoplay" type="checkbox"> Auto-play A on navigation</label></div>
<p id="position"></p><h2 id="key"></h2><p id="prompt"></p><p id="promptKo"></p><p class="pill" id="seed"></p>
<div class="samples"><section class="card"><h3>Sample A</h3><audio id="audioA" controls preload="none"></audio><div class="rating" id="ratingA"></div></section>
<section class="card"><h3>Sample B</h3><audio id="audioB" controls preload="none"></audio><div class="rating" id="ratingB"></div></section></div>
<p class="muted">Artifacts: 1 = severe audible artifacts, 5 = no audible artifacts. Other ratings: 1 = poor, 5 = excellent.</p>
<label>Overall preference <select id="preference"><option value="">Unrated</option><option>A</option><option>B</option><option>Tie</option></select></label>
<p><label>Notes<br><textarea id="notes"></textarea></label></p>
<div class="bar"><button id="reveal">Reveal model identities</button><span id="identity"></span><button id="export">Export ratings JSON</button></div>
<script>
const pairs=__PAIRS__, fields=[['alignment','Prompt alignment'],['fidelity','Audio fidelity / cleanliness'],['usefulness','Production SFX usefulness'],['artifacts','Audible artifacts']];
const runId=__RUN_ID__, storageKey='agent-audio-ab-v2-'+runId; let ratings={};try{ratings=JSON.parse(localStorage.getItem(storageKey)||'{}')}catch(e){}
let visible=[],index=0,revealed=false; const $=id=>document.getElementById(id);
for(const side of ['A','B']){for(const [field,label] of fields){const row=document.createElement('label');row.textContent=label+' ';
const select=document.createElement('select');select.id=side+'_'+field;select.innerHTML='<option value="">—</option>'+[1,2,3,4,5].map(n=>`<option>${n}</option>`).join('');
select.onchange=save;row.append(select);$('rating'+side).append(row)}}
const categories=['all',...new Set(pairs.map(p=>p.category))];for(const c of categories){const option=document.createElement('option');option.value=c;option.textContent=c==='all'?'All':c;$('category').append(option)}
for(const duration of [...new Set(pairs.map(p=>p.duration))].sort((a,b)=>a-b)){const option=document.createElement('option');option.value=String(duration);option.textContent=duration+' s';$('duration').append(option)}
function current(){return visible[index]}
function save(){const p=current();if(!p)return;let value={};for(const side of ['A','B']){value[side]={};for(const [field] of fields)value[side][field]=$(side+'_'+field).value}
value.identities_revealed=revealed||Boolean(ratings[p.rating_key]?.identities_revealed);value.preference=$('preference').value;value.notes=$('notes').value;ratings[p.rating_key]=value;try{localStorage.setItem(storageKey,JSON.stringify(ratings))}catch(e){$('identity').textContent='Browser storage unavailable: export ratings before closing.'}}
function filter(){const c=$('category').value,d=$('duration').value;visible=pairs.filter(p=>(c==='all'||p.category===c)&&(d==='all'||String(p.duration)===d));index=0;show()}
function show(){const p=current();$('position').textContent=p?`${index+1} / ${visible.length} matching pairs`:'No completed pairs match.';
if(!p){$('key').textContent='';$('prompt').textContent='';$('promptKo').textContent='';return}$('key').textContent=p.key;$('prompt').textContent=p.prompt;$('promptKo').textContent=p.prompt_ko||'';$('seed').textContent=`${p.category} · ${p.duration}s · seed ${p.seed}`;
for(const side of ['A','B']){$('audio'+side).src=p[side].url;for(const [field] of fields)$(side+'_'+field).value=ratings[p.rating_key]?.[side]?.[field]||''}
$('preference').value=ratings[p.rating_key]?.preference||'';$('notes').value=ratings[p.rating_key]?.notes||'';revealed=Boolean(ratings[p.rating_key]?.identities_revealed);$('identity').textContent=revealed?`Previously revealed: A: ${p.A.model} · B: ${p.B.model}`:'';
if($('autoplay').checked)$('audioA').play().catch(()=>{})}
$('category').onchange=filter;$('duration').onchange=filter;$('previous').onclick=()=>{if(visible.length){index=(index-1+visible.length)%visible.length;show()}};
$('next').onclick=()=>{if(visible.length){index=(index+1)%visible.length;show()}};$('preference').onchange=save;$('notes').oninput=save;
$('audioA').onended=()=>{if($('autoplay').checked)$('audioB').play().catch(()=>{})};
$('audioB').onended=()=>{if($('autoplay').checked&&visible.length){index=(index+1)%visible.length;show()}};
$('reveal').onclick=()=>{const p=current();if(!p)return;revealed=true;$('identity').textContent=`A: ${p.A.model} · B: ${p.B.model}`;save()};
$('export').onclick=()=>{const blob=new Blob([JSON.stringify({schema_version:2,run_id:runId,pairs:ratings,identities:pairs.map(p=>({key:p.key,rating_key:p.rating_key,A:p.A.model,B:p.B.model}))},null,2)],{type:'application/json'});
const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='sfx-ab-ratings.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
filter();
</script></body></html>"""
