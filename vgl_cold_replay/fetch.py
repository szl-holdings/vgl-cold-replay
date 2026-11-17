"""Anonymous fetch helper. urllib only, fail-closed on HTTP errors."""
from __future__ import annotations
import json
import sys
import urllib.request

def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "vgl-cold-replay/1.0 (anonymous)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_text(url: str, timeout: int = 60) -> str:
    return fetch_bytes(url, timeout).decode("utf-8")

def fetch_json(url: str, timeout: int = 60):
    return json.loads(fetch_text(url, timeout))

def fetch_or_none(url: str, timeout: int = 60):
    """Fetch, returning None on any failure. A missing artifact is data, not an error."""
    try:
        return fetch_bytes(url, timeout)
    except Exception as e:  # noqa: BLE001 - deliberate: record, don't crash
        print(f"  fetch failed: {url} ({e})", file=sys.stderr)
        return None
