"""Render the video watch page, chapter controls and accessible transcript."""

import argparse
import html
from pathlib import Path

from build_course import ROOT, read
from build_course_video import DESTINATION, MEDIA_NAME, WEBM_NAME, timecode


def render():
    manifest = read(DESTINATION / "media-manifest.json")
    chapters, sections = [], []
    for index, chapter in enumerate(manifest["chapters"], 1):
        stamp = timecode(chapter["start"])[3:8]
        title = html.escape(chapter["title"])
        chapters.append(f'<li><a class="chapter" data-start="{chapter["start"]}" href="{MEDIA_NAME}#t={chapter["start"]}"><span>{stamp}</span>{title}</a></li>')
        scenes = []
        for scene in [s for s in manifest["scenes"] if s["chapter"] == index]:
            text = scene["narration"] or f'Practice for {scene["seconds"]} seconds: ' + ' '.join(scene["bullets"])
            references = []
            for key in scene["references"]:
                path = manifest["references"][key]["path"]
                references.append(f'<a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/{html.escape(path)}">{html.escape(key)}</a>')
            scenes.append(f'<h4>{timecode(scene["start"])[3:8]} · {html.escape(scene["title"])}</h4><p>{html.escape(text)}</p><p class="evidence">Evidence: {", ".join(references)}</p>')
        sections.append(f'<section id="transcript-{chapter["id"]}"><h3>{stamp} · {title}</h3>{"".join(scenes)}</section>')
    size = manifest["artifacts"][MEDIA_NAME]["bytes"] / 1048576
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A narrated 30-minute course on the actual NetMamba+ experiments, input data, training, inference and remaining work.">
<title>NetMamba+ · Watch the 30-minute course</title>
<style>
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#f8f6ef;color:#172c3a;font:18px/1.65 system-ui,sans-serif}}a{{color:#09635c;text-underline-offset:.18em}}a:focus-visible,button:focus-visible,video:focus-visible{{outline:3px solid #b14c36;outline-offset:5px}}.skip{{position:absolute;top:-100px}}.skip:focus{{top:12px;background:white;z-index:3}}header,main,footer{{max-width:1240px;margin:auto;padding:28px}}header{{border-top:8px solid #126e68}}.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-size:.8rem;color:#126e68;font-weight:750}}h1{{font:700 clamp(2.2rem,5vw,4.5rem)/1.1 Georgia,serif;margin:.3em 0}}h2{{font:700 2rem/1.2 Georgia,serif}}h3{{margin-top:2.5em}}h4{{font-size:1.1rem;margin-bottom:.5em}}.lede{{max-width:850px;font-size:1.15rem}}video{{display:block;width:100%;aspect-ratio:16/9;background:#172c3a;border-radius:12px}}.downloads{{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}}.downloads a{{padding:10px 17px;border:1px solid #126e68;border-radius:7px;text-decoration:none;font-weight:650;min-height:46px}}.downloads a:first-child{{background:#126e68;color:white}}.small,.evidence{{font-size:.9rem;color:#465a63}}.chapters{{display:grid;grid-template-columns:1fr 1fr;gap:8px;list-style:none;padding:0}}.chapter{{display:flex;gap:16px;align-items:baseline;padding:13px 16px;background:white;border:1px solid #d9e9ed;border-radius:7px;text-decoration:none;min-height:48px}}.chapter span{{font:600 1rem ui-monospace,monospace;white-space:nowrap}}.chapter:hover{{background:#e2eeeb}}.transcript{{max-width:850px}}.transcript section{{border-top:1px solid #b8cbd0;margin-top:28px}}.status{{padding:12px 18px;background:#e2eeeb;border-left:4px solid #126e68}}footer{{border-top:1px solid #b8cbd0;margin-top:30px}}@media(max-width:650px){{header,main,footer{{padding:20px}}.chapters{{grid-template-columns:1fr}}.downloads a{{flex:1;text-align:center;min-width:150px}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}@media print{{video,.chapters,.downloads,header nav{{display:none}}body{{font-size:12pt}}header,main{{padding:0}}a{{color:inherit}}}}
</style></head><body><a class="skip" href="#player">Skip to video</a>
<header><nav><a href="../">Recorded IDS demo</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction">Repository</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md">Every file explained</a></nav>
<p class="eyebrow">The reproduction lab · video course</p><h1>Understand what you built.</h1>
<p class="lede">Start with no networking or machine-learning background. This thirty-minute lesson explains the paper, your two CSVs, the data actually used, what this repository adds, and how to explain the measured results to someone else.</p></header>
<main><video id="player" controls playsinline preload="metadata" aria-label="NetMamba+ 30-minute narrated course" poster="poster.png"><source src="{WEBM_NAME}" type="video/webm"><source src="{MEDIA_NAME}" type="video/mp4"><track kind="captions" src="captions.vtt" srclang="en" label="English">Your browser cannot play this video. <a href="{MEDIA_NAME}">Download the MP4</a>.</video>
<div class="downloads"><a href="{MEDIA_NAME}" download>Download MP4 · {size:.1f} MiB</a><a href="transcript.md" download>Download transcript</a><a href="captions.vtt" download>Download captions</a><a href="#transcript">Read along</a></div>
<p class="small">One continuous 30:00 video · 1080p · local synthetic voice · captions included in the picture. Optional English text captions are also available in the player. Three minutes are labeled practice pauses, including a 90-second teach-back; pause longer whenever you need.</p>
<p class="small">Review copy: automated media and playback checks are recorded. A complete human watch-through and detailed caption-timing review remain pending. <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/video-verification.md">Read the exact review status.</a></p>
<p class="status">Actual three-run mean: <strong>86.65%</strong>. The paper’s <strong>97.50%</strong> was not reproduced. The demo replays saved predictions; live IDS and NPU/SmartNIC deployment remain future work.</p>
<h2>Jump to a chapter</h2><ol class="chapters">{"".join(chapters)}</ol><p id="play-status" class="small" role="status" aria-live="polite">Choose a chapter, then press Play.</p>
<div class="transcript" id="transcript"><h2>Read the complete narration</h2><p>This transcript reflows for smaller screens. Evidence links lead to the saved records. The course explains earlier experiments; playing it does not rerun training.</p>{"".join(sections)}</div></main>
<footer><a href="https://github.com/buffbeefalo/netmambaplus-reproduction/releases/tag/course-video-v1">Versioned video release</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/video-verification.md">Media checks and remaining review</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md">Every file and download explained</a></footer>
<script>
const player=document.getElementById('player');
document.querySelectorAll('.chapter').forEach(link=>link.addEventListener('click',event=>{{
 event.preventDefault(); const seek=()=>{{player.currentTime=Number(link.dataset.start);player.focus();document.getElementById('play-status').textContent='Selected '+link.textContent+'. Press Play to continue.';}};
 if(player.readyState>=1)seek();else{{player.addEventListener('loadedmetadata',seek,{{once:true}});player.load();}}
}}));
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = DESTINATION / "index.html"
    expected = render()
    if args.check:
        if not path.is_file() or path.read_text() != expected:
            raise SystemExit("Video watch page is stale")
        print("Video watch page matches the measured media manifest.")
    else:
        path.write_text(expected)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
