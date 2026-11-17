"""Cold verification of the A1 fixture package (protocol B2/B2.2 perimeter).

Manifest: frontier-54-runs collaboration/fixture-package-hashes.json (31 files).
Files:   szl-holdings/szl-forge @ tag protocol-prep-2026-11-12 (raw.githubusercontent).
Every file fetched anonymously and SHA-256-compared. 0 mismatch expected.
"""
from __future__ import annotations
import hashlib
from .fetch import fetch_json, fetch_or_none

MANIFEST_URL = ("https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs/"
                "resolve/main/collaboration/fixture-package-hashes.json")
RAW_BASE = "https://raw.githubusercontent.com/szl-holdings/szl-forge/protocol-prep-2026-11-12/"

def run() -> dict:
    manifest = fetch_json(MANIFEST_URL)
    files: dict[str, str] = manifest["files"] if isinstance(manifest, dict) else manifest
    passed, mismatched, missing = [], [], []
    for path, expected in files.items():
        data = fetch_or_none(RAW_BASE + path)
        if data is None:
            missing.append(path)
        elif hashlib.sha256(data).hexdigest() == expected:
            passed.append(path)
        else:
            mismatched.append(path)
    n = len(files)
    ok = (not mismatched and not missing and len(passed) == n)
    verdict = "PASS" if ok else ("FAIL" if (mismatched or missing) else "PARTIAL")
    return {
        "check": "fixture_package_cold_verification",
        "manifest": MANIFEST_URL,
        "source": RAW_BASE,
        "files": n, "passed": len(passed),
        "mismatched": mismatched, "missing": missing,
        "verdict": verdict,
        "claim": f"{len(passed)}/{n} fixture files byte-exact SHA-256 vs the published manifest, anonymous fetch",
    }
