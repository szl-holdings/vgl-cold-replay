"""Field-level determinism comparison of the v2.1 battery receipts (clause A2/A9).

The two receipts (03:14Z and 07:38Z) must be identical on every measured value.
Wall-clock and energy fields are run metadata, not measurements, and are
reported separately - never pooled with the measurements.
"""
from __future__ import annotations
from .fetch import fetch_json

URLS = [
    ("run_1_0314Z", "https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs/resolve/main/collaboration/vgl-criteria-v2/salad-v5-heldout-v2-20261117T031434.json"),
    ("run_2_0738Z", "https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs/resolve/main/collaboration/vgl-criteria-v2/salad-v5-heldout-v2-20261117T073800.json"),
]
RUN_METADATA_FIELDS = {"started_utc", "completed_utc", "wall_seconds", "energy_j"}

def _diff(a, b, prefix=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += _diff(a.get(k), b.get(k), f"{prefix}{k}.")
    elif a != b:
        out.append((prefix.rstrip("."), a, b))
    return out

def run() -> dict:
    (n1, u1), (n2, u2) = URLS
    r1, r2 = fetch_json(u1), fetch_json(u2)
    diffs = _diff(r1, r2)
    measurements = [d for d in diffs if d[0] not in RUN_METADATA_FIELDS]
    metadata = [d for d in diffs if d[0] in RUN_METADATA_FIELDS]
    cv = r1.get("criteria_v2", [])
    if isinstance(cv, dict):
        cv = list(cv.values())
    criteria = [
        {"rule": c.get("rule"), "observed": {k: v for k, v in c.items() if k != "rule"}, "pass": c.get("pass")}
        for c in cv if isinstance(c, dict)
    ]
    return {
        "check": "battery_v2_1_determinism",
        "artifacts": {n1: u1, n2: u2},
        "fields_differing": [{"field": d[0], "run1": d[1], "run2": d[2]} for d in diffs],
        "measurement_fields_differing": [d[0] for d in measurements],
        "run_metadata_fields_differing": [d[0] for d in metadata],
        "criteria_run1": criteria,
        "battery_admissible_run1": r1.get("battery_admissible"),
        "verdict": "PASS" if not measurements else "FAIL",
        "claim": ("IDENTICAL on every measured value; differences are run metadata only"
                  if not measurements else f"MEASUREMENT DIVERGENCE in {len(measurements)} fields"),
    }
