"""CLI orchestrator: run the full cold replay and emit a receipt.

    python -m vgl_cold_replay.replay [--out evidence/replay.json]

Exit codes follow estate convention: 0 PASS, 1 REVIEW (a check failed or was
NOT_RUN), 2 BLOCKED, 3 ERROR. A NOT_REPRODUCED negative finding is REVIEW, not
ERROR: the tool did its job by reporting it.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import sys
from . import __version__
from . import battery_determinism, fixture_verify, independent_digest_check, inventory_freeze

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="vgl-cold-replay")
    ap.add_argument("--out", default="evidence/replay.json")
    ap.add_argument("--skip-inventory", action="store_true",
                    help="skip the GitHub/HF snapshot (avoids API rate limits)")
    args = ap.parse_args(argv)

    receipt = {
        "kind": "vgl.cold-replay/v1",
        "tool_version": __version__,
        "ran_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "access": "anonymous only - no member access, no tokens, no secrets",
        "checks": [],
    }
    checks = [fixture_verify, battery_determinism, independent_digest_check]
    if not args.skip_inventory:
        checks.append(inventory_freeze)
    for mod in checks:
        try:
            receipt["checks"].append(mod.run())
        except Exception as e:  # noqa: BLE001 - fail closed, record the failure
            receipt["checks"].append({"check": mod.__name__, "verdict": "ERROR", "reason": str(e)[:300]})

    verdicts = [c.get("verdict") for c in receipt["checks"]]
    receipt["overall"] = ("PASS" if all(v in ("PASS", "MEASURED", "REPRODUCED") for v in verdicts)
                          else "REVIEW")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=1, sort_keys=False)
    print(json.dumps({"overall": receipt["overall"], "verdicts": verdicts,
                      "written": args.out}, indent=1))
    return 0 if receipt["overall"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
