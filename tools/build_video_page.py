"""Render the video watch page, chapter controls and accessible transcript."""

import argparse
from contextlib import nullcontext
import html
import os
from pathlib import Path
from urllib.parse import quote

from build_course import ROOT, read
from build_course_video import (DESTINATION, LEGACY_DESTINATION, check_source_binding,
                                display_time, production_credit, publication)
from narrate_course_video import SOURCE, digest

WATCH_PAGE = LEGACY_DESTINATION / "index.html"


def render(manifest=None, *, media_dir=None, output=None):
    if manifest is None:
        manifest = read((media_dir or DESTINATION) / "media-manifest.json")
    metadata = publication(manifest)
    media_name, webm_name = metadata["media_name"], metadata["webm_name"]
    duration, practice = manifest["scheduled_seconds"], manifest["practice_seconds"]
    # Preserve the published v2 page when rendering its original metadata-free manifest.
    legacy = ("media_name" not in manifest and "title" not in manifest and duration == 1800 and practice == 180)
    version = metadata['release_tag'].removeprefix('course-video-')
    media_dir = Path(media_dir or (LEGACY_DESTINATION if legacy else LEGACY_DESTINATION / version)).resolve()
    output = Path(output or WATCH_PAGE).resolve()
    prefix = Path(os.path.relpath(media_dir, output.parent)).as_posix()
    prefix = "" if prefix == "." else quote(prefix, safe="/") + "/"
    media_url, webm_url = prefix + media_name, prefix + webm_name
    review_path = "docs/customer/video-verification.md" if legacy else f"docs/customer/video-verification-{version}.md"
    if legacy:
        description = "A narrated 30-minute course on the actual NetMamba+ experiments, input data, training, inference and remaining work."
        title = "NetMamba+ · Watch the 30-minute course"
        heading = "Understand what you built."
        lede = "Start with no networking or machine-learning background. This thirty-minute lesson explains the paper, your two CSVs, the data actually used, what this repository adds, and how to explain the measured results to someone else."
        aria_label = "NetMamba+ 30-minute narrated course"
        runtime = "One continuous 30:00 video · 1080p · local synthetic voice · captions included in the picture. Optional English text captions are also available in the player. Three minutes are labeled practice pauses, including a 90-second teach-back; pause longer whenever you need."
    else:
        title = heading = metadata["title"]
        description = f"{title}. A narrated course on the actual NetMamba+ experiments, input data, training, inference and remaining work."
        lede = "Follow the evidence from input data through training, saved predictions and the remaining work. Chapter controls and the complete transcript let you learn at your own pace."
        aria_label = metadata["title"] + " — narrated course"
        runtime = (f"One continuous {display_time(duration)} video · {len(manifest['chapters'])} chapters · 1080p · synthetic voice · captions included in the picture. "
                   f"Optional English text captions are also available in the player. Labeled practice pauses total {display_time(practice)}; pause longer whenever you need.")
    page_title = title
    credit = '\n<p class="small">' + html.escape(production_credit(metadata)) + '</p>' if metadata["production"] else ""
    chapters, sections = [], []
    for index, chapter in enumerate(manifest["chapters"], 1):
        stamp = display_time(chapter["start"])
        title = html.escape(chapter["title"])
        chapters.append(f'<li><a class="chapter" data-start="{chapter["start"]}" href="{media_url}#t={chapter["start"]}"><span>{stamp}</span>{title}</a></li>')
        scenes = []
        for scene in [s for s in manifest["scenes"] if s["chapter"] == index]:
            text = scene["narration"] or f'Practice for {scene["seconds"]} seconds: ' + ' '.join(scene["bullets"])
            references = []
            for key in scene["references"]:
                path = manifest["references"][key]["path"]
                references.append(f'<a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/{html.escape(path)}">{html.escape(key)}</a>')
            scenes.append(f'<h4>{display_time(scene["start"])} · {html.escape(scene["title"])}</h4><p>{html.escape(text)}</p><p class="evidence">Evidence: {", ".join(references)}</p>')
        sections.append(f'<section id="transcript-{chapter["id"]}"><h3>{stamp} · {title}</h3>{"".join(scenes)}</section>')
    size = manifest["artifacts"][media_name]["bytes"] / 1048576
    companion_links = ""
    if not legacy:
        for name, label in [("NetMambaPlus-course-slides.pptx", "PowerPoint + speaker notes"),
                            ("NetMambaPlus-course-handbook.pdf", "PDF handbook + file guide"),
                            ("NetMambaPlus-course-slides.pdf", "PDF slides")]:
            if name in manifest["artifacts"]:
                companion_links += f'<a href="{prefix}{name}" download>{label}</a>'
    packet_notice = ""
    if version == 'v4':
        packet_notice = ('<aside class="status" aria-label="Later packet study">'
            '<strong>Later addition: both uploaded CSVs now train a packet model.</strong> '
            'This preserved v4 video explains the original flow experiment and confidence calibration. '
            'Read the <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md">packet study and measured results</a> '
            'and send the <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-addendum/NetMambaPlus-packet-addendum.pdf">PDF</a> '
            'and <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-addendum/NetMambaPlus-packet-addendum.pptx">PowerPoint addendum</a> '
            'with this video. Its new CSV training is not covered by this recording.</aside>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(description)}">
<title>{html.escape(page_title)}</title>
<style>
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#f8f6ef;color:#172c3a;font:18px/1.65 system-ui,sans-serif}}a{{color:#09635c;text-underline-offset:.18em}}a:focus-visible,button:focus-visible,video:focus-visible{{outline:3px solid #b14c36;outline-offset:5px}}.skip{{position:absolute;top:-100px}}.skip:focus{{top:12px;background:white;z-index:3}}header,main,footer{{max-width:1240px;margin:auto;padding:28px}}header{{border-top:8px solid #126e68}}.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-size:.8rem;color:#126e68;font-weight:750}}h1{{font:700 clamp(2.2rem,5vw,4.5rem)/1.1 Georgia,serif;margin:.3em 0}}h2{{font:700 2rem/1.2 Georgia,serif}}h3{{margin-top:2.5em}}h4{{font-size:1.1rem;margin-bottom:.5em}}.lede{{max-width:850px;font-size:1.15rem}}video{{display:block;width:100%;aspect-ratio:16/9;background:#172c3a;border-radius:12px}}.downloads{{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}}.downloads a{{padding:10px 17px;border:1px solid #126e68;border-radius:7px;text-decoration:none;font-weight:650;min-height:46px}}.downloads a:first-child{{background:#126e68;color:white}}.small,.evidence{{font-size:.9rem;color:#465a63}}.chapters{{display:grid;grid-template-columns:1fr 1fr;gap:8px;list-style:none;padding:0}}.chapter{{display:flex;gap:16px;align-items:baseline;padding:13px 16px;background:white;border:1px solid #d9e9ed;border-radius:7px;text-decoration:none;min-height:48px}}.chapter span{{font:600 1rem ui-monospace,monospace;white-space:nowrap}}.chapter:hover{{background:#e2eeeb}}.transcript{{max-width:850px}}.transcript section{{border-top:1px solid #b8cbd0;margin-top:28px}}.status{{padding:12px 18px;background:#e2eeeb;border-left:4px solid #126e68}}footer{{border-top:1px solid #b8cbd0;margin-top:30px}}@media(max-width:650px){{header,main,footer{{padding:20px}}.chapters{{grid-template-columns:1fr}}.downloads a{{flex:1;text-align:center;min-width:150px}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}@media print{{video,.chapters,.downloads,header nav{{display:none}}body{{font-size:12pt}}header,main{{padding:0}}a{{color:inherit}}}}
</style></head><body><a class="skip" href="#player">Skip to video</a>
<header><nav><a href="../">Recorded IDS demo</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction">Repository</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md">Every file explained</a></nav>
<p class="eyebrow">The reproduction lab · video course</p><h1>{html.escape(heading)}</h1>
<p class="lede">{html.escape(lede)}</p>{packet_notice}</header>
<main><video id="player" controls playsinline preload="metadata" aria-label="{html.escape(aria_label)}" poster="{prefix}poster.png"><source src="{webm_url}" type="video/webm"><source src="{media_url}" type="video/mp4"><track kind="captions" src="{prefix}captions.vtt" srclang="en" label="English">Your browser cannot play this video. <a href="{media_url}">Download the MP4</a>.</video>
<div class="downloads"><a href="{media_url}" download>Download MP4 · {size:.1f} MiB</a><a href="{prefix}transcript.md" download>Download transcript</a><a href="{prefix}captions.vtt" download>Download captions</a>{companion_links}<a href="#transcript">Read along</a></div>
<p class="small">{html.escape(runtime)}</p>{credit}
<p class="small">Review copy: automated media and playback checks are recorded. A complete human watch-through and detailed caption-timing review remain pending. <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/{review_path}">Read the exact review status.</a></p>
<p class="status">Actual three-run mean: <strong>86.65%</strong>. The paper’s <strong>97.50%</strong> was not reproduced. The demo replays saved predictions; live IDS and NPU/SmartNIC deployment remain future work.</p>
<h2>Jump to a chapter</h2><ol class="chapters">{"".join(chapters)}</ol><p id="play-status" class="small" role="status" aria-live="polite">Choose a chapter, then press Play.</p>
<div class="transcript" id="transcript"><h2>Read the complete narration</h2><p>This transcript reflows for smaller screens. Evidence links lead to the saved records. The course explains earlier experiments; playing it does not rerun training.</p>{"".join(sections)}</div></main>
<footer><a href="https://github.com/buffbeefalo/netmambaplus-reproduction/releases/tag/{metadata['release_tag']}">Versioned video release</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/{review_path}">Media checks and remaining review</a> · <a href="https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md">Every file and download explained</a></footer>
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
    parser.add_argument("--media-dir", type=Path, help="Directory containing the selected version's media manifest")
    parser.add_argument("--source", type=Path, default=SOURCE, help="Source whose identity and references must match the selected media")
    parser.add_argument("--output", type=Path, help="Watch page path; defaults to the one active video/index.html")
    parser.add_argument("--legacy", action="store_true", help="Render the preserved v2 manifest to a separate explicit output")
    args = parser.parse_args()
    repository_root = ROOT.resolve()
    if args.legacy and args.output is None:
        parser.error("--legacy requires --output; the active watch page is reserved for v4")
    path = (args.output or WATCH_PAGE).resolve()
    if args.legacy and not args.check and path == WATCH_PAGE.resolve():
        parser.error("Legacy HTML cannot replace the active watch page")
    media_dir = (args.media_dir or (LEGACY_DESTINATION if args.legacy else DESTINATION)).resolve()
    manifest_path = media_dir / "media-manifest.json"
    manifest_hash = digest(manifest_path)
    manifest = read(manifest_path)
    if publication(manifest)["release_tag"] == "course-video-v2" and not args.legacy:
        parser.error("Use --legacy and --output to render historical HTML")
    if not args.legacy:
        if publication(manifest)["release_tag"] != "course-video-v4" and path == WATCH_PAGE.resolve():
            parser.error("Historical HTML requires a separate --output; the active watch page is reserved for v4")
    version = publication(manifest)['release_tag'].removeprefix('course-video-v')
    archived = (not args.legacy and version in ('3', '4')
                and media_dir == (repository_root / f'docs/customer/demo/video/v{version}').resolve())
    if archived:
        from verify_video_course_v3 import historical_snapshot
        binding = historical_snapshot(repository_root, version=int(version))
    else:
        binding = nullcontext((repository_root, None))
    with binding as (binding_root, _):
        if not args.legacy:
            source = binding_root / args.source.resolve().relative_to(repository_root)
            recorded_manifest = binding_root / f'docs/customer/demo/video/v{version}/media-manifest.json'
            if archived and digest(recorded_manifest) != manifest_hash:
                raise ValueError('Watch page requires the exact published historical media manifest')
            check_source_binding(manifest, source, root=binding_root)
        expected = render(manifest, media_dir=media_dir, output=path)
        if not args.legacy:
            check_source_binding(manifest, source, root=binding_root)
    if digest(manifest_path) != manifest_hash:
        raise ValueError("Media manifest changed while rendering the watch page")
    if args.check:
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            raise SystemExit("Video watch page is stale")
        print("Video watch page matches the measured media manifest.")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8", newline="\n")
        print(path.relative_to(repository_root) if path.is_relative_to(repository_root) else path)


if __name__ == "__main__":
    main()
