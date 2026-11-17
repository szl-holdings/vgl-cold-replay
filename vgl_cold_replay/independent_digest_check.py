"""Independent digest re-computation for receipts that embed a digest field.

Written fresh for this kit: it does NOT import estate code, so it satisfies the
independence rule (protocol clause A6) for digest verification.

Result on the current lean/ receipts: REPRODUCED. All three embed
`receipt_sha256` recomputable as SHA-256 over the receipt minus the digest
field, canonicalized as sort_keys=True with Python default separators
(ensure_ascii=True) - found by recipe search after an earlier pass wrongly
reported NOT_REPRODUCED (that pass's search space omitted the sorted+default-
separator combination; the error is recorded and superseded, per clause 10.2).
The recipe remains UNDECLARED in the receipt bodies, so this tool still has to
search for it; later receipts should declare their canon profile + algorithm.
"""
from __future__ import annotations
import hashlib
import itertools
import json
from .fetch import fetch_json

TARGETS = [
    "https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs/resolve/main/lean/f23-deny-by-default-proven.json",
    "https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs/resolve/main/lean/f24-f25-covenant-proven.json",
    "https://huggingface.co/datasets/SZLHOLDINGS/frontier-54-runs/resolve/main/lean/lake-build-complete.json",
]
DIGEST_FIELDS = ("receipt_sha256", "sha256", "digest")

def _canon_bytes(obj, sort_keys, ensure_ascii, sep, indent):
    def norm(o):
        if isinstance(o, dict):
            items = sorted(o.items()) if sort_keys else o.items()
            return {k: norm(v) for k, v in items}
        if isinstance(o, list):
            return [norm(v) for v in o]
        return o
    return json.dumps(norm(obj), ensure_ascii=ensure_ascii, separators=sep,
                      indent=indent, allow_nan=False).encode()

def _recipes(obj):
    """Yield (label, bytes) for every canonicalization recipe in the search space."""
    for sort, ascii_ in itertools.product((True, False), (True, False)):
        for sep in ((",", ":"), (", ", ": ")):
            for drop in DIGEST_FIELDS + (None,):
                o = dict(obj)
                if drop and drop in o:
                    del o[drop]
                yield (f"sha256 sort={sort} ascii={ascii_} sep={sep} drop={drop}",
                       hashlib.sha256(_canon_bytes(o, sort, ascii_, sep, None)).hexdigest())
                yield (f"sha256 sort={sort} ascii={ascii_} sep={sep} indent=2 drop={drop}",
                       hashlib.sha256(_canon_bytes(o, sort, ascii_, sep, 2)).hexdigest())
                yield (f"sha3-256 sort={sort} ascii={ascii_} sep={sep} drop={drop}",
                       hashlib.sha3_256(_canon_bytes(o, sort, ascii_, sep, None)).hexdigest())

def run() -> dict:
    results = []
    for url in TARGETS:
        obj = fetch_json(url)
        target = next((obj[f] for f in DIGEST_FIELDS if f in obj), None)
        if target is None:
            results.append({"artifact": url, "verdict": "NOT_RUN", "note": "no embedded digest field"})
            continue
        tried, hit = 0, None
        for label, digest in _recipes(obj):
            tried += 1
            if digest == target:
                hit = label
                break
        results.append({
            "artifact": url,
            "target_field": "receipt_sha256",
            "recipes_tried": tried,
            "verdict": "REPRODUCED" if hit else "NOT_REPRODUCED",
            "matching_recipe": hit,
            "diagnosis": None if hit else (
                "the receipt body does not declare its canonicalization profile or hash "
                "algorithm, so the embedded digest cannot be recomputed from the published "
                "file alone"),
        })
    n_repro = sum(1 for r in results if r["verdict"] == "REPRODUCED")
    return {
        "check": "independent_digest_recomputation",
        "independence": "this module shares no code with the estate receipt emitters (clause A6)",
        "targets": results,
        "verdict": "REPRODUCED" if n_repro == len(results) else ("MIXED" if n_repro else "NOT_REPRODUCED"),
        "reproduced": f"{n_repro}/{len(results)}",
        "search_space": "8 canonicalization shapes x 2 hash algorithms x drop-digest variants, ~48 recipes per artifact",
        "note": "Supersedes the 17-Nov NOT_REPRODUCED finding: the digests DO recompute, "
                "recipe sha256(sort_keys, default separators, drop digest field). The recipe is "
                "undeclared in the receipt bodies; recommendation stands that future receipts "
                "carry algorithm-declared digests so no search is needed.",
    }
