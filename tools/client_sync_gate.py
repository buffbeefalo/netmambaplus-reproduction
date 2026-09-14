"""Admit only successful canonical push verification at the current source main."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

REPOSITORY = "buffbeefalo/netmambaplus-reproduction"


def eligible(*, event_name, event, repository, ref, remote_sha, run):
    if repository != REPOSITORY or ref != "refs/heads/main" or not re.fullmatch(r"[0-9a-f]{40}", remote_sha):
        return False
    if (run.get("path") != ".github/workflows/ci.yml" or run.get("name") != "CPU verification" or
            run.get("event") != "push" or run.get("status") != "completed" or
            run.get("conclusion") != "success" or run.get("head_branch") != "main" or
            run.get("head_repository", {}).get("full_name") != REPOSITORY or run.get("head_sha") != remote_sha):
        return False
    if event_name == "workflow_run":
        original = event.get("workflow_run", {})
        return original.get("id") == run.get("id") and original.get("head_sha") == remote_sha
    return event_name == "workflow_dispatch"


def api(suffix):
    request = urllib.request.Request("https://api.github.com/repos/" + REPOSITORY + suffix,
                                     headers={"Accept": "application/vnd.github+json",
                                              "Authorization": "Bearer " + os.environ["GH_TOKEN"],
                                              "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        event_name = os.environ["GITHUB_EVENT_NAME"]
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        remote_sha = api("/git/ref/heads/main")["object"]["sha"]
        if event_name == "workflow_run":
            run_id = event.get("workflow_run", {}).get("id")
            if not isinstance(run_id, int) or run_id <= 0:
                raise ValueError("Invalid workflow run identity")
            run = api(f"/actions/runs/{run_id}")
        elif event_name == "workflow_dispatch":
            runs = api("/actions/workflows/ci.yml/runs?branch=main&event=push&per_page=100")["workflow_runs"]
            run = next((r for r in runs if r.get("head_sha") == remote_sha), {})
        else:
            raise ValueError("Unsupported publication event")
        admitted = eligible(event_name=event_name, event=event, repository=os.environ["GITHUB_REPOSITORY"],
                            ref=os.environ["GITHUB_REF"], remote_sha=remote_sha, run=run)
        with args.output.open("a", encoding="utf-8") as stream:
            stream.write(f"eligible={'true' if admitted else 'false'}\n")
            if admitted:
                stream.write(f"source_sha={remote_sha}\n")
        print(json.dumps({"eligible": admitted, "source_sha": remote_sha,
                          "verification_run": run.get("id"),
                          "reason": "verified current main" if admitted else "unverified, stale or ineligible event"}))
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(f"Client publication gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
