"""Profile uploaded packet CSV metadata without publishing packet contents."""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repro


def profile(path):
    with path.open(newline="") as stream:
        columns = next(csv.reader(stream))
    expected = [f"payload_byte_{i}" for i in range(1, 1501)] + ["ttl", "total_len", "protocol", "t_delta", "label"]
    if columns != expected:
        raise ValueError(f"Unexpected packet CSV schema: {path.name}")
    quoted = "'" + str(path.resolve()).replace("'", "''") + "'"
    query = f"""SET threads=2; SET memory_limit='1GB';
    SELECT label, count(*) AS rows,
           min(try_cast(ttl AS DOUBLE)) AS min_ttl, max(try_cast(ttl AS DOUBLE)) AS max_ttl,
           min(try_cast(total_len AS DOUBLE)) AS min_total_len,
           max(try_cast(total_len AS DOUBLE)) AS max_total_len,
           min(try_cast(t_delta AS DOUBLE)) AS min_t_delta,
           max(try_cast(t_delta AS DOUBLE)) AS max_t_delta,
           count(*) FILTER (WHERE try_cast(t_delta AS DOUBLE) IS NULL) AS invalid_t_delta,
           histogram(protocol) AS protocol_counts
    FROM read_csv({quoted}, header=true, all_varchar=true, strict_mode=true, ignore_errors=false)
    GROUP BY label ORDER BY rows DESC, label;"""
    result = subprocess.run(["duckdb", "-json", "-c", query], capture_output=True, text=True, check=True)
    groups = json.loads(result.stdout)
    return {"file": path.name.split("-Payload_data_")[-1] if "-Payload_data_" in path.name else path.name,
            "sha256": repro.sha256_file(path), "bytes": path.stat().st_size,
            "columns": len(columns), "payload_byte_columns": 1500,
            "remaining_columns": columns[1500:], "rows": sum(group["rows"] for group in groups),
            "labels": groups,
            "scope": "Full CSV scan for row counts and metadata aggregates; payload values were not exhaustively numerically validated or used for model training.",
            "missing_flow_context": ["source address", "destination address", "source port", "destination port",
                                     "flow identifier", "established packet order within a flow"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output file")
    reports = []
    for path in args.csv:
        reports.append(profile(path))
        print(f"Profiled {path.name}: {reports[-1]['rows']} rows", flush=True)
    repro.atomic_json(args.output, {"created_at": repro.timestamp(), "tool_sha256": repro.sha256_file(__file__),
                                  "duckdb_version": subprocess.check_output(["duckdb", "--version"], text=True).strip(),
                                  "files": reports}, overwrite=False)


if __name__ == "__main__":
    main()
