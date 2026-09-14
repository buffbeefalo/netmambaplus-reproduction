"""Render verified joint-model packet predictions as a standalone offline page."""

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_study as study


def source_view(source, records):
    if source not in ('cic', 'unsw'):
        raise ValueError('Expected a registered packet source')
    metrics = study.evaluate_records(records)
    predictions = []
    for item in records:
        logits = item['logits']
        selected = int(logits[1] > logits[0])
        weights = [math.exp(value - max(logits)) for value in logits]
        predictions.append({'id': item['id'], 'counts': item['counts'],
                            'logits': logits, 'prediction': selected,
                            'probability': weights[selected] / sum(weights)})
    return {'source': source, 'groups': len(records), 'rows': metrics['rows'],
            'conflicting_groups': sum(all(row['counts']) for row in predictions),
            'disagreement_groups': sum(row['counts'][1 - row['prediction']] > 0 for row in predictions),
            'incorrect_rows': sum(row['counts'][1 - row['prediction']] for row in predictions),
            'metrics': metrics, 'predictions': predictions}


def script_json(document):
    return (json.dumps(document, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e'))


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NetMamba+ · Packet evidence</title>
<style>
:root{--ink:#172c32;--paper:#f6f3eb;--line:#cad2cd;--muted:#425960;--green:#185943;--rust:#8c351d;--gold:#eadbb0}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 "Trebuchet MS",Verdana,sans-serif}
main{max-width:1240px;margin:auto;padding:30px 38px 48px}a{color:var(--green);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}
.eyebrow{font:700 12px/1.4 "Courier New",monospace;letter-spacing:.12em;text-transform:uppercase}.mast{display:flex;justify-content:space-between;gap:16px;padding-bottom:20px;border-bottom:2px solid var(--ink)}
.stamp{color:var(--green)}h1{font:400 clamp(36px,5.5vw,64px)/1.04 Georgia,serif;letter-spacing:-.035em;margin:24px 0 18px;max-width:740px}
h2{font:400 29px/1.15 Georgia,serif;margin:0 0 10px}p{margin:8px 0 16px}.intro{display:grid;grid-template-columns:1.5fr 1fr;gap:36px;margin:26px 0}.lede{font-size:18px;max-width:750px}
.process{background:var(--ink);color:white;padding:24px 26px;border-radius:3px}.process ol{padding-left:22px;margin:15px 0 0}.process li{padding-left:5px;margin:13px 0}.process small{display:block;color:#d9e3dc}
.note{border-left:4px solid var(--rust);padding:10px 15px;background:#efe7da;font-size:14px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:25px 0}
.metric{padding:18px;background:var(--paper)}.metric strong{display:block;font:400 34px/1.2 Georgia,serif;margin:7px 0}.metric small{display:block;color:var(--muted);font-size:12px}
.toolbar{display:flex;flex-wrap:wrap;gap:18px;align-items:end;padding:18px 0;border-top:1px solid var(--line)}label{display:grid;gap:5px;font-size:13px;font-weight:700}
select{min-width:0;max-width:100%}select,input,button{font:inherit;color:var(--ink);border:1px solid #72877f;border-radius:3px;padding:9px 12px;background:#fffdf7}input{max-width:220px}button{cursor:pointer}button:disabled{opacity:.48;cursor:default}button:hover:enabled{background:var(--gold)}
:focus-visible{outline:3px solid #9c4b00;outline-offset:3px}.status{font-size:14px;color:var(--muted)}.table-wrap{overflow:auto;border-top:2px solid var(--ink);border-bottom:1px solid var(--line)}
table{width:100%;border-collapse:collapse;text-align:left;font-size:14px}caption{text-align:left;padding:12px 0;font-size:13px;color:var(--muted)}th{font-size:12px;white-space:nowrap;background:#e6e8dd}th,td{padding:11px 12px;border-bottom:1px solid var(--line)}
td:first-child{font-family:"Courier New",monospace}.pill{display:inline-block;padding:2px 8px;border-radius:2px;font-size:12px;font-weight:bold}.benign{background:#dce9df;color:#19442f}.attack{background:#f2dfd4;color:#742813}.conflict{color:var(--rust)}.hash-button{font:inherit;padding:3px 5px;border:0;background:transparent;text-decoration:underline;text-underline-offset:3px}
.pager{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:16px 0 28px}.pager div{display:flex;gap:9px}.detail{padding:18px;background:#e6e8dd;overflow-wrap:anywhere;margin-bottom:24px}.detail pre{white-space:pre-wrap;font-size:12px}
.notes{display:grid;grid-template-columns:1fr 1fr;gap:30px;border-top:2px solid var(--ink);padding-top:25px;font-size:14px}.notes h2{font-size:24px}footer{overflow-wrap:anywhere;margin-top:26px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
@media(max-width:740px){main{padding:20px 17px}.mast{display:block}.mast span{display:block}.mast .stamp{margin-top:7px}.mast a{display:inline-block;margin-top:10px}.intro,.notes{grid-template-columns:1fr;gap:16px}.metrics{grid-template-columns:1fr 1fr}.metric{padding:14px}.metric strong{font-size:29px}.toolbar{gap:12px}label{flex:1;min-width:140px}input{max-width:100%;width:100%}.pager{align-items:start}.lede{font-size:16px}}
</style></head><body><main>
<div class="mast"><span class="eyebrow">NetMamba+ / packet evidence</span><span class="stamp">Recorded GPU predictions · offline viewer</span></div>
<section class="intro"><div><h1>Two CSVs.<br>One packet classifier.</h1><p class="lede">Explore the joint pretrained model's held-out predictions from CICIDS2017 and UNSW. Both sources supplied training groups; this page shows their separate test groups.</p><p class="note">This browser displays saved evidence. It does not run new inference, capture traffic or block packets. Scores are uncalibrated.</p></div>
<aside class="process"><span class="eyebrow">The tested input path</span><ol><li>Validate both packet CSVs<small>1,500 stored payload bytes per row; globally grouped to keep identical inputs in one split.</small></li><li>Train the native packet encoder<small>378 tokens, four Mamba blocks, a two-class head. Joint batches use both sources.</small></li><li>Classify unlabeled packet bytes<small>Two logits and a benign/attack prediction, with an input/checkpoint receipt.</small></li></ol></aside></section>
<div class="toolbar"><label>Test source<select id="source"><option value="cic">CICIDS2017</option><option value="unsw">UNSW</option></select></label><label>Show groups<select id="filter"><option value="all">All groups</option><option value="disagreement">Any label disagreement</option><option value="conflict">Conflicting supplied labels</option></select></label><label>Predicted class<select id="class-filter"><option value="all">Both classes</option><option value="0">Benign</option><option value="1">Attack</option></select></label><label>Payload hash prefix<input id="search" type="search" placeholder="e.g. 0000b8" maxlength="64" autocomplete="off"></label></div>
<section class="metrics" aria-label="Complete selected test set metrics"><div class="metric"><span>Balanced accuracy</span><strong id="balanced"></strong><small>Group weighting · complete source test</small></div><div class="metric"><span>Distinct payload groups</span><strong id="groups"></strong><small id="represented"></small></div><div class="metric"><span>Label disagreement</span><strong id="disagreements"></strong><small>Groups with at least one mismatched label</small></div><div class="metric"><span>Conflicting labels</span><strong id="conflicts"></strong><small>Same bytes labeled both benign and attack</small></div></section>
<h2>Inspect the evidence</h2><p id="status" class="status" aria-live="polite"></p>
<div class="table-wrap"><table><caption>Each row below is one distinct payload group. Label counts are original CSV rows, not model scores. Select a hash to inspect logits.</caption><thead><tr><th scope="col">Payload hash</th><th scope="col">Prediction</th><th scope="col">Model score</th><th scope="col">Benign labels</th><th scope="col">Attack labels</th><th scope="col">Mismatched rows</th></tr></thead><tbody id="rows"></tbody></table></div>
<div class="pager"><span id="page-info" class="status"></span><div><button id="previous" type="button">Previous</button><button id="next" type="button">Next</button></div></div>
<section id="detail" class="detail" hidden><h2>Selected payload group</h2><pre id="detail-text"></pre><button id="close-detail" type="button">Close details</button></section>
<section class="notes"><div><h2>Read the result correctly</h2><p>The joint pretrained model scored <strong>97.56% on CIC and 94.29% on UNSW</strong> in group-weighted balanced accuracy. The selected test sets contain 20,000 and 5,930 groups. Filters change this table; the four headline cards continue to describe the complete selected source test.</p><p>Balanced accuracy averages benign and attack recall. Duplicate groups with contradictory labels retain both counts. A prediction can therefore disagree with some labels even within one group. Supplied labels have not been independently adjudicated.</p><p>The UNSW-only metadata control scored 99.34% there, above the neural models. This is one seed with capped subsets, limited attack-subtype support and unknown prior pretrained exposure.</p></div><div><h2>Evidence, not a deployment claim</h2><p>This packet adaptation uses the NetMamba+ encoder with a new input layout and binary head. Its results are separate from the paper's original flow benchmark.</p><p>All 25,930 classes agreed in the original saved-model inference check. Two strict logit comparisons failed; a later capped client check retained 76 score-comparison failures across 128 rows despite class agreement. Those separate scopes remain in the records.</p><p><a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md">Understand the complete project</a> · <a href="https://github.com/buffbeefalo/netmambaplus-client">Client code and setup</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md">All models and controls</a></p></div></section>
<footer id="provenance"></footer><noscript>This viewer needs browser JavaScript to display its bundled predictions. No network connection is needed. The JSON evidence is also available in the repository.</noscript>
</main><script id="evidence" type="application/json">__EVIDENCE__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('evidence').textContent);
const byId=id=>document.getElementById(id), format=n=>n.toLocaleString('en-US');
let page=0, filtered=[];const size=40;
function cell(row,value){const c=document.createElement('td');c.textContent=value;row.append(c);return c;}
function selected(){return data.sources[byId('source').value];}
function inspect(item){byId('detail').hidden=false;byId('detail-text').textContent=JSON.stringify(item,null,2);byId('close-detail').focus();}
function draw(){
 const view=selected(), mode=byId('filter').value, target=byId('class-filter').value, query=byId('search').value.trim().toLowerCase();
 filtered=view.predictions.filter(r=>(target==='all'||r.prediction===Number(target))&&r.id.startsWith(query)&&(mode==='all'||(mode==='conflict'?r.counts[0]>0&&r.counts[1]>0:r.counts[1-r.prediction]>0)));
 const pages=Math.max(1,Math.ceil(filtered.length/size));page=Math.min(page,pages-1);
 byId('balanced').textContent=(100*view.metrics.group_weighted.balanced_accuracy).toFixed(2)+'%';byId('groups').textContent=format(view.groups);
 byId('represented').textContent=format(view.rows)+' original rows represented';byId('disagreements').textContent=format(view.disagreement_groups);byId('conflicts').textContent=format(view.conflicting_groups);
 byId('status').textContent=format(filtered.length)+' matching groups from '+format(view.groups)+' in '+(view.source==='cic'?'CICIDS2017':'UNSW')+'. '+format(view.incorrect_rows)+' original rows disagree with the model across this complete source test.';
 const body=byId('rows');body.replaceChildren();for(const item of filtered.slice(page*size,(page+1)*size)){
  const row=document.createElement('tr'), id=cell(row,''), button=document.createElement('button');button.type='button';button.className='hash-button';button.textContent=item.id.slice(0,14)+'…';button.setAttribute('aria-label','Inspect payload '+item.id);button.onclick=()=>inspect(item);id.append(button);
  const predicted=cell(row,''), badge=document.createElement('span');badge.className='pill '+(item.prediction?'attack':'benign');badge.textContent=item.prediction?'Attack':'Benign';predicted.append(badge);
  cell(row,(100*item.probability).toFixed(2)+'%');cell(row,format(item.counts[0]));cell(row,format(item.counts[1]));const wrong=item.counts[1-item.prediction], last=cell(row,format(wrong));if(wrong)last.className='conflict';body.append(row);
 }
 if(!filtered.length){const row=document.createElement('tr'), value=cell(row,'No matching groups. Change the filters or hash prefix.');value.colSpan=6;body.append(row);}
 byId('page-info').textContent='Page '+(page+1)+' of '+pages+' · up to '+size+' groups per page';byId('previous').disabled=page===0;byId('next').disabled=page===pages-1;
}
for(const id of ['source','filter','class-filter','search'])byId(id).addEventListener(id==='search'?'input':'change',()=>{page=0;byId('detail').hidden=true;draw();});
byId('previous').onclick=()=>{page--;draw();};byId('next').onclick=()=>{page++;draw();};byId('close-detail').onclick=()=>{byId('detail').hidden=true;byId('source').focus();};
byId('provenance').textContent='Recorded model: joint_pretrained · protocol SHA-256 '+data.protocol_sha256+' · '+format(data.total_groups)+' groups across both test sources. The generated receipt binds this page to its evidence inputs.';draw();
</script></body></html>'''


def build(evidence, output):
    evidence, output = Path(evidence).resolve(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError('Choose a fresh packet demo output directory')
    from tools.review_packet_study import verify
    verification = verify(evidence)
    results = study.read_json(evidence / 'results.json')
    joint = next(item for item in results['results'] if item['arm']['name'] == 'joint_pretrained')
    sources, inputs = {}, {}
    for source in ('cic', 'unsw'):
        reference = joint['tests'][source]['predictions']
        path = study.verify_artifact(evidence, reference)
        sources[source] = source_view(source, list(study.prediction_records(path)))
        inputs[source] = reference
    document = {'sources': sources, 'protocol_sha256': results['protocol_sha256'],
                'total_groups': sum(source['groups'] for source in sources.values())}
    html = PAGE.replace('__EVIDENCE__', script_json(document))
    output.mkdir(parents=True, exist_ok=False)
    page = output / 'index.html'
    page.write_text(html, encoding='utf-8', newline='\n')
    receipt = {'status': 'rendered', 'scope': 'Recorded joint packet predictions; no new inference',
               'protocol_sha256': document['protocol_sha256'], 'predictions': inputs,
               'checkpoint': joint['selected_checkpoint'], 'total_groups': document['total_groups'],
               'evidence_index_sha256': study.sha256(evidence / 'index.json'),
               'renderer_sha256': study.sha256(Path(__file__)), 'verification': verification,
               'page': study.artifact(output, page)}
    study.write_json(output / 'receipt.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/customer/evidence/packet-study')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.evidence, args.output)
    print(json.dumps({'status': result['status'], 'groups': result['total_groups'], 'page': result['page']}))


if __name__ == '__main__':
    main()
