"""CLI for anonymous public evidence replay with immutable local receipt custody.

No private credentials, new provider effects, automatic remediation or model training.
Each replay gets an exclusive, fsynced, byte-verified output. Existing historical
evidence/replay.json is a baseline, never an output target.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

from . import __version__
from . import battery_determinism, fixture_verify, independent_digest_check, inventory_freeze


def _status(overall: str, *, reason: str | None = None, **extra: object) -> None:
    payload: dict[str, object] = {"overall": overall}
    if reason is not None:
        payload["reason"] = reason
    payload.update(extra)
    print(json.dumps(payload, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vgl-cold-replay")
    ap.add_argument(
        "--out",
        default=None,
        help="a NEW exclusive receipt filename; default creates a unique evidence/replay-*.json",
    )
    ap.add_argument(
        "--skip-inventory", action="store_true",
        help="skip the GitHub/HF inventory snapshot (other anonymous checks still fetch)",
    )
    args = ap.parse_args(argv)
    observed_at = dt.datetime.now(dt.timezone.utc)
    receipt: dict[str, object] = {
        "kind": "vgl.cold-replay/v1",
        "tool_version": __version__,
        "ran_at": observed_at.isoformat(timespec="seconds"),
        "access": "anonymous public only; neither authentication nor training proven",
        "checks": [],
        "signature_verified": False,
    }
    checks = [fixture_verify, battery_determinism, independent_digest_check]
    if not args.skip_inventory:
        checks.append(inventory_freeze)
    for module in checks:
        try:
            result = module.run()
            if not isinstance(result, dict):
                result = {"check": module.__name__, "verdict": "ERROR",
                          "reason": "CHECK_RETURN_TYPE_INVALID"}
        except Exception as exc:
            # Never disclose arbitrary exception text; it can contain URLs,
            # local paths or identifiers even in an anonymous public tool.
            result = {"check": module.__name__, "verdict": "ERROR",
                      "reason": "CHECK_EXCEPTION_" + type(exc).__name__}
        receipt["checks"].append(result)

    verdicts = [row.get("verdict") for row in receipt["checks"]]
    overall = (
        "PASS" if all(v in ("PASS", "MEASURED", "REPRODUCED") for v in verdicts)
        else "REVIEW"
    )
    receipt["overall"] = overall
    try:
        data = (
            json.dumps(receipt, ensure_ascii=True, sort_keys=True,
                       indent=1, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        _status("ERROR", reason="NONFINITE_OR_INVALID_CHECK_RESULT")
        return 3

    if args.out is None:
        root = Path("evidence")
        if root.is_symlink():
            _status("BLOCKED", reason="OUTPUT_PARENT_SYMLINK")
            return 2
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            _status("ERROR", reason="OUTPUT_PARENT_UNAVAILABLE")
            return 3
        target = root / (
            "replay-" + observed_at.strftime("%Y%m%dT%H%M%S%fZ")
            + "-" + uuid.uuid4().hex + ".json"
        )
    else:
        target = Path(args.out)

    try:
        # Exclusive create MUST precede any write. No overwrite, truncate or
        # fallback on a collision; fsync and exact readback before reporting.
        with target.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if target.read_bytes() != data:
            _status("ERROR", reason="RECEIPT_READBACK_MISMATCH")
            return 3
    except FileExistsError:
        _status("BLOCKED", reason="DESTINATION_ALREADY_EXISTS")
        return 2
    except OSError:
        _status("ERROR", reason="OUTPUT_WRITE_UNAVAILABLE")
        return 3

    _status(overall, receipt_sha256=hashlib.sha256(data).hexdigest(),
            check_count=len(checks), bytes=len(data), exclusive_create=True,
            signature_verified=False, path_disclosed=False)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
