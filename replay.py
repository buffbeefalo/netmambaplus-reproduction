"""Record strict native classifier inference and build a self-contained replay."""

import json
import math
import sys
from pathlib import Path

import evaluate
import repro


def metrics_from_predictions(labels, predictions, num_classes):
    if (type(num_classes) is not int or num_classes < 1 or not labels
            or len(labels) != len(predictions)):
        raise ValueError("A nonempty, paired prediction inventory is required")
    matrix = [[0] * num_classes for _ in range(num_classes)]
    for actual, predicted in zip(labels, predictions):
        if any(type(x) is not int or not 0 <= x < num_classes for x in (actual, predicted)):
            raise ValueError("Labels and predictions must be integer class indices")
        matrix[actual][predicted] += 1
    support = [sum(row) for row in matrix]
    predicted_count = [sum(row[c] for row in matrix) for c in range(num_classes)]
    precision = [matrix[c][c] / predicted_count[c] if predicted_count[c] else 0.0
                 for c in range(num_classes)]
    recall = [matrix[c][c] / support[c] if support[c] else 0.0 for c in range(num_classes)]
    f1 = [2 * p * r / (p + r) if p + r else 0.0 for p, r in zip(precision, recall)]
    result = {"confusion_matrix": matrix, "support": support,
              "accuracy": sum(matrix[c][c] for c in range(num_classes)) / len(labels),
              "precision_per_class": precision, "recall_per_class": recall, "f1_per_class": f1}
    for name, values in (("precision", precision), ("recall", recall), ("f1", f1)):
        result["macro_" + name] = sum(values) / num_classes
        result["weighted_" + name] = sum(v * n for v, n in zip(values, support)) / len(labels)
    return result


def probabilities(logits):
    if not logits or any(not math.isfinite(x) for x in logits):
        raise ValueError("Softmax requires nonempty finite logits")
    largest = max(logits)
    values = [math.exp(x - largest) for x in logits]
    total = sum(values)
    return [x / total for x in values]


def render_html(record):
    payload = json.dumps(record, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")
    return HTML.replace("__RECORDED_DATA__", payload)


def run_replay(prepared):
    args, native, manifest = prepared["args"], prepared["native"], prepared["manifest"]
    if manifest["checkpoint_provenance"]["class_order"] != "hash_bound":
        raise repro.ReproError("Replay requires a checkpoint with a hash-bound class mapping")
    manifest["argv"] = [sys.executable, str(Path(__file__).resolve()), *repro.execution_options(args)]
    manifest["replay_sha256"] = repro.sha256_file(__file__)
    manifest["evaluation_entrypoint"] = "replay.py"
    runtime = evaluate.load_runtime(args.upstream)
    device = runtime.torch.device(native.device)
    model = runtime.classifier(native)
    checkpoint = runtime.torch.load(str(prepared["checkpoint"]), map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.to(device)
    loader, mapping = runtime.loader(native, str(Path(args.data).resolve() / "data-test.json"))
    evaluate.check_loader_mapping(mapping, manifest["class_mapping"],
                                  prepared["report"]["splits"]["test"]["class_counts"])
    raw = runtime.engine(loader, model, device, native, return_logits=True)
    measured, nonfinite = evaluate.serialize_metrics(raw)
    if nonfinite:
        raise repro.ReproError(f"Nonfinite inference outputs: {nonfinite}")
    logits, labels = measured.pop("logits"), measured.pop("labels")
    predictions = runtime.torch.tensor(logits, device=device).topk(1, dim=1).indices.flatten().tolist()
    independent = metrics_from_predictions(labels, predictions, len(manifest["class_mapping"]))
    if independent["confusion_matrix"] != measured["cm"]:
        raise repro.ReproError("Independent and native confusion matrices disagree")
    for our_key, native_key in (("accuracy", "acc"), ("weighted_precision", "weighted_pre"),
                                ("weighted_recall", "weighted_rec"), ("weighted_f1", "weighted_f1")):
        if not math.isclose(independent[our_key], measured[native_key], abs_tol=1e-10, rel_tol=1e-10):
            raise repro.ReproError(f"Independent metric disagreement: {our_key}")
    record = {"schema_version": 1, "kind": "recorded_native_test_inference",
              "scope": "Recorded inference replay; not live packet capture or an intrusion prevention system.",
              "created_at": repro.timestamp(), "class_mapping": manifest["class_mapping"],
              "checkpoint_sha256": manifest["input_checkpoint"]["sha256"],
              "test_sha256": repro.sha256_file(Path(args.data) / "data-test.json"),
              "source_commit": manifest["configuration"]["upstream"]["commit"],
              "independent_metrics": independent, "native_metrics": measured,
              "confidence_interpretation": "Uncalibrated softmax score, not probability of a real attack",
              "predictions": [{"row": i, "label": label, "prediction": prediction,
                               "logits": values, "scores": probabilities(values)}
                              for i, (label, prediction, values) in enumerate(zip(labels, predictions, logits))]}
    output = Path(args.output)
    repro.atomic_json(output / "predictions.json", record, overwrite=False)
    with (output / "index.html").open("x", encoding="utf-8") as stream:
        stream.write(render_html(record))
    return {"metrics": measured, "independent_metrics": independent,
            "nonfinite_metric_paths": [], "checkpoint_sha256": record["checkpoint_sha256"],
            "class_mapping": record["class_mapping"],
            "predictions_sha256": repro.sha256_file(output / "predictions.json"),
            "replay_sha256": repro.sha256_file(output / "index.html"),
            "evaluation_behavior": "Unmodified engine_mm.evaluate(return_logits=True), internal CUDA autocast"}


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NetMamba+ | Recorded inference replay</title>
<style>
:root{color-scheme:dark;--bg:#0b1520;--panel:#14232f;--ink:#edf2ef;--muted:#afbec6;--line:#324652;--teal:#77e4cd;--amber:#ffc785}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Trebuchet MS",sans-serif}
main{max-width:1240px;margin:auto;padding:36px 36px 60px}header{display:flex;justify-content:space-between;gap:36px;border-bottom:1px solid var(--line);padding-bottom:28px}
.eyebrow{font:12px/1.5 "Courier New",monospace;letter-spacing:.15em;text-transform:uppercase;color:var(--teal)}h1{font:normal clamp(34px,5vw,60px)/1.08 Georgia,serif;margin:14px 0 18px;max-width:750px}h2{font:normal 25px Georgia,serif;margin:0 0 14px}p{margin:8px 0}.muted{color:var(--muted)}.intro{max-width:650px}.scope{border-left:3px solid var(--amber);padding-left:18px;max-width:295px;align-self:center}
.pipeline{display:flex;flex-wrap:wrap;gap:14px;margin:24px 0;color:var(--muted);font-size:14px}.pipeline strong{color:var(--ink)}.arrow{color:var(--teal)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);margin:20px 0 26px}.stat{padding:20px;border-right:1px solid var(--line)}.stat:last-child{border:0}.stat b{display:block;font:32px Georgia,serif;color:var(--teal)}.stat span{font-size:13px;color:var(--muted)}
.controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:16px 0}.controls label{font-size:14px}.controls select{margin-left:7px}button,select{background:var(--panel);border:1px solid #67818c;color:var(--ink);border-radius:3px;padding:10px 15px;font:inherit;cursor:pointer}button.primary{background:var(--teal);border-color:var(--teal);color:var(--bg);font-weight:bold}button:focus-visible,select:focus-visible{outline:3px solid var(--amber);outline-offset:3px}button:hover{border-color:var(--teal)}
progress{width:100%;height:6px;accent-color:var(--teal);display:block;margin:20px 0}.grid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px}.panel{min-width:0;background:var(--panel);padding:22px;border:1px solid var(--line)}.table-wrap{overflow:auto;max-height:475px}table{border-collapse:collapse;width:100%;font-size:14px;text-align:left}th{position:sticky;top:0;background:var(--panel);font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:13px 8px}td{padding:13px 8px;border-top:1px solid var(--line)}.correct{color:var(--teal)}.wrong{color:var(--amber)}.tag{font-size:11px;border:1px solid var(--amber);color:var(--amber);padding:2px 5px;margin-left:7px;white-space:nowrap}.score{font-family:"Courier New",monospace}.key{font-size:13px;color:var(--muted)}.key li{margin-bottom:12px}.hash{overflow-wrap:anywhere;font:11px/1.6 "Courier New",monospace;color:var(--muted)}footer{margin-top:30px;border-top:1px solid var(--line);padding-top:20px;font-size:13px;color:var(--muted)}
@media(max-width:800px){main{padding:20px}header{display:block}.scope{max-width:none;margin-top:24px}.grid{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.stat{border-bottom:1px solid var(--line)}}
</style></head><body><main>
<header><div><div class="eyebrow">NetMamba+ / measured system walkthrough</div><h1>Recorded inference replay</h1><p class="intro muted">Follow a saved classifier as it labels held-out CICIoT2022 flows. Every row below comes from a real GPU inference run.</p></div><div class="scope"><strong>Offline demonstration</strong><p class="muted">This is not live packet capture. Playback speed controls the display, not the model. No traffic is blocked.</p></div></header>
<div class="pipeline"><span><strong>Input</strong> · bytes + sizes + timing</span><span class="arrow">→</span><span><strong>NetMamba+</strong> · 443 tokens / flow</span><span class="arrow">→</span><span><strong>Output</strong> · six class scores</span></div>
<div class="stats"><div class="stat"><b id="count">0</b><span>flows displayed</span></div><div class="stat"><b id="accuracy">—</b><span>full test accuracy</span></div><div class="stat"><b id="macro">—</b><span>full test macro F1</span></div><div class="stat"><b id="alerts">0</b><span>displayed attack-class predictions</span></div></div>
<div class="controls"><button class="primary" id="play">Play replay</button><button id="reset">Reset</button><button id="all">Show all</button><label>Display pace<select id="pace"><option value="150">Fast · 150 ms / row</option><option value="600">Talk-through · 600 ms / row</option></select></label><label>Rows<select id="filter"><option value="all">All displayed flows</option><option value="errors">Prediction errors</option><option value="alerts">Attack-class predictions</option></select></label></div>
<progress id="progress" value="0" max="1" aria-label="Replay progress"></progress>
<div class="grid"><section class="panel"><h2>Predictions and benchmark truth</h2><p class="muted" id="status" role="status" aria-live="polite">Ready. Press Play replay or Show all.</p><div class="table-wrap"><table><thead><tr><th>Row</th><th>Model prediction</th><th>Score</th><th>Dataset label</th><th>Match</th></tr></thead><tbody id="rows"></tbody></table></div></section>
<aside class="panel"><h2>How to read this</h2><ul class="key"><li><strong>Prediction</strong> is the class with the largest model logit.</li><li><strong>Score</strong> is uncalibrated softmax confidence; it is not a measured probability of malicious traffic.</li><li><strong>Dataset label</strong> is benchmark truth used for evaluation. It is not a model input.</li><li><strong>Attack-class</strong> means Flood or RTSP Brute Force in this six-class benchmark. Other attacks are not covered.</li><li><strong>Errors</strong> are retained. Official splits contain a small number of exact raw-input overlaps.</li></ul><p class="eyebrow">Classifier fingerprint</p><p class="hash" id="hash"></p></aside></div>
<footer>Measured replay of an experimental classifier. This page contains predictions only, with no raw packet payloads. <a style="color:var(--teal)" href="https://github.com/buffbeefalo/netmambaplus-reproduction/tree/main/docs/customer">Open the customer package for commands, hashes, limits and paper comparisons.</a></footer>
</main><script id="record" type="application/json">__RECORDED_DATA__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('record').textContent), records=data.predictions, byId=Object.fromEntries(Object.entries(data.class_mapping).map(([name,id])=>[id,name]));
const attackIds=new Set(Object.entries(data.class_mapping).filter(([name])=>['6-Attacks-1-Flood','6-Attacks-2-RTSP Brute Force'].includes(name)).map(([,id])=>id));
const el=id=>document.getElementById(id);let shown=0,timer=null;
const shortName=id=>(byId[id]||String(id)).replace(/^6-Attacks-\d-/,'').replace(/^1-Power-/,'');
const percent=value=>typeof value==='number'?(100*value).toFixed(2)+'%':'—';
el('accuracy').textContent=percent(data.independent_metrics?.accuracy);el('macro').textContent=percent(data.independent_metrics?.macro_f1);el('hash').textContent=data.checkpoint_sha256||'No classifier hash recorded';el('progress').max=Math.max(1,records.length);
function pause(){clearInterval(timer);timer=null;el('play').textContent='Play replay';}
function render(){const visible=records.slice(0,shown),filter=el('filter').value;el('count').textContent=shown.toLocaleString()+' / '+records.length.toLocaleString();el('alerts').textContent=visible.filter(r=>attackIds.has(r.prediction)).length.toLocaleString();el('progress').value=shown;el('rows').replaceChildren();const selected=visible.filter(r=>filter==='all'||(filter==='errors'&&r.prediction!==r.label)||(filter==='alerts'&&attackIds.has(r.prediction))).slice().reverse();for(const r of selected){const tr=document.createElement('tr');const values=[String(r.row+1).padStart(4,'0'),shortName(r.prediction),percent(r.scores[r.prediction]),shortName(r.label),r.prediction===r.label?'Correct':'Error'];values.forEach((value,i)=>{const td=document.createElement('td');td.textContent=value;if(i===1&&attackIds.has(r.prediction)){const tag=document.createElement('span');tag.className='tag';tag.textContent='Attack-class';td.append(tag);}if(i===2)td.className='score';if(i===4)td.className=r.prediction===r.label?'correct':'wrong';tr.append(td);});el('rows').append(tr);}el('status').textContent=shown===records.length?'Replay complete · '+selected.length+' rows match the selected filter.':shown+' flows displayed · '+selected.length+' rows match the selected filter.';}
function play(){if(timer){pause();return;}if(shown===records.length)shown=0;el('play').textContent='Pause replay';timer=setInterval(()=>{shown=Math.min(shown+1,records.length);render();if(shown===records.length)pause();},Number(el('pace').value));}
el('play').onclick=play;el('reset').onclick=()=>{pause();shown=0;render();};el('all').onclick=()=>{pause();shown=records.length;render();};el('filter').onchange=render;el('pace').onchange=()=>{if(timer){pause();play();}};
</script></body></html>'''


def main(argv=None):
    args = repro.cli_parser().parse_args(["evaluate", *(sys.argv[1:] if argv is None else argv)])
    return repro.run_stage(args, evaluation_fn=run_replay)


if __name__ == "__main__":
    raise SystemExit(main())
