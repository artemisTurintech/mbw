#!/usr/bin/env python3
"""
Benchmark runner for mbw (Memory Bandwidth Benchmark).

One unit of work: a single execution of the mbw binary measuring all three
copy methods (MEMCPY, DUMB, MCBLOCK) over ARRAY_SIZE_MIB of memory.
Metrics reported: memory bandwidth in MiB/s per method, and wall-clock
execution time per run in milliseconds.
"""

import json
import math
import os
import re
import subprocess
import sys
import timeit

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUMBER = 1          # mbw executions per trial
REPEAT = 10         # number of trials
ARRAY_SIZE_MIB = 512

# ---------------------------------------------------------------------------
# Locate the binary
# ---------------------------------------------------------------------------
_candidates = ["./mbw.exe", "./mbw"]
MBW_BINARY = next((c for c in _candidates if os.path.isfile(c)), None)
if MBW_BINARY is None:
    sys.exit("mbw binary not found — run: gcc -O2 -o mbw mbw.c")

_CMD = [MBW_BINARY, "-q", "-n", "1", str(ARRAY_SIZE_MIB)]

# ---------------------------------------------------------------------------
# Setup: verify binary is functional (excluded from timing)
# ---------------------------------------------------------------------------
try:
    subprocess.run(_CMD, capture_output=True, text=True, check=True)
except subprocess.CalledProcessError as exc:
    sys.exit(f"mbw failed during setup:\n{exc.stderr}")

# ---------------------------------------------------------------------------
# Per-trial collector
# ---------------------------------------------------------------------------
_trial_results: list[dict[str, float]] = []

def _run() -> None:
    proc = subprocess.run(_CMD, capture_output=True, text=True, check=True)
    bw: dict[str, float] = {}
    for line in proc.stdout.splitlines():
        # Individual run lines start with a digit (e.g. "0\tMethod: ...")
        if line and line[0].isdigit():
            m = re.search(r"Method: (\w+)", line)
            b = re.search(r"Copy: ([\d.]+) MiB/s", line)
            if m and b:
                bw[m.group(1)] = float(b.group(1))
    _trial_results.append(bw)

# ---------------------------------------------------------------------------
# Warm-up (excluded from measurement)
# ---------------------------------------------------------------------------
_run()
_trial_results.clear()

# ---------------------------------------------------------------------------
# Timed runs
# ---------------------------------------------------------------------------
raw_times = timeit.repeat(stmt=_run, number=NUMBER, repeat=REPEAT)

# raw_times[i] is wall-clock seconds for NUMBER calls; normalise to per-call
times_s = [t / NUMBER for t in raw_times]

# ---------------------------------------------------------------------------
# Statistics helpers (stdlib only)
# ---------------------------------------------------------------------------
def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)

def _stdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

# ---------------------------------------------------------------------------
# Build per-trial rows
# ---------------------------------------------------------------------------
rows = []
for i, (trial_bw, t_s) in enumerate(zip(_trial_results, times_s)):
    row: dict = {"number": NUMBER, "repeat": REPEAT}
    for method, bw in sorted(trial_bw.items()):
        row[f"{method.lower()}_mibs"] = round(bw, 3)
    row["run_time_ms"] = round(t_s * 1000, 3)
    rows.append(row)

# ---------------------------------------------------------------------------
# Stdout summary (mean ± stdev per metric)
# ---------------------------------------------------------------------------
all_keys = [k for k in rows[0] if k not in ("number", "repeat")]
print(f"{'metric':<25} {'mean':>12}  {'stdev':>12}")
print("-" * 52)
for key in all_keys:
    values = [r[key] for r in rows]
    print(f"{key:<25} {_mean(values):>12.3f}  {_stdev(values):>12.3f}")

# ---------------------------------------------------------------------------
# Write JSON
# ---------------------------------------------------------------------------
output_path = "artemis_results.json"
with open(output_path, "w") as fh:
    json.dump(rows, fh, indent=2)

print(f"\nResults written to {output_path}")
