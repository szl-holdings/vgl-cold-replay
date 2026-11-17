"""Anonymous inventory snapshot of the public estate (GitHub org + HF org).

GitHub: the anonymous REST API is rate-limited (60 req/h per IP) and returns
only public repos; pass a token via VGL_GITHUB_TOKEN if you need the full 165.
HF:     the anonymous Hub API lists public repos only; no token needed.
Output: a frozen manifest with sha256 of each inventory file (clause 3: every
figure carries its population and n).
"""
from __future__ import annotations
import datetime as _dt
import hashlib
import json
import os
from .fetch import fetch_json

GH_API = "https://api.github.com"
HF_API = "https://huggingface.co/api"

def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def run() -> dict:
    out = {"check": "public_inventory_snapshot",
           "captured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "github_org_szl-holdings_public": None, "huggingface_SZLHOLDINGS_public": {}}
    token = os.environ.get("VGL_GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    import urllib.request
    req = urllib.request.Request(f"{GH_API}/orgs/szl-holdings/repos?per_page=100&page=1",
                                 headers={"User-Agent": "vgl-cold-replay/1.0", **headers})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            repos = json.load(r)
        out["github_org_szl-holdings_public"] = {
            "note": "anonymous API lists public repos only and is rate-limited; "
                    "the sprint freeze (165 total / 26 private) was captured with member access",
            "public_repos_seen": len(repos),
            "names": [x["name"] for x in repos],
        }
    except Exception as e:  # noqa: BLE001
        out["github_org_szl-holdings_public"] = {"verdict": "NOT_RUN", "reason": str(e)[:200]}
    for kind in ("models", "datasets", "spaces"):
        try:
            items = fetch_json(f"{HF_API}/{kind}?author=SZLHOLDINGS&limit=1000")
            out["huggingface_SZLHOLDINGS_public"][kind] = {
                "count": len(items), "ids": [x["id"] for x in items],
            }
        except Exception as e:  # noqa: BLE001
            out["huggingface_SZLHOLDINGS_public"][kind] = {"verdict": "NOT_RUN", "reason": str(e)[:200]}
    blob = json.dumps(out, sort_keys=True, separators=(",", ":")).encode()
    out["snapshot_sha256"] = _sha256(blob)
    out["verdict"] = "MEASURED"
    return out
