<!-- szl:header v1 -->
# vgl-cold-replay

**Fully Python. Standard library only. Anonymous access only.**

A cold-replay kit for the SZL Holdings x Vidal-Gadea Lab protocol: everything
the 2026-11-17 evidence sprint verified can be re-verified by anyone —
including the Vidal-Gadea Lab as the independent outside party for protocol
clause B1 — from public artifacts alone, with no member access, no tokens, and
no secrets. Fail closed: a check that cannot run is NOT_RUN, never passed.

## Run it

```bash
python3 -m vgl_cold_replay.replay --skip-inventory   # core checks, ~1 min, anonymous
python3 -m vgl_cold_replay.replay                    # + public inventory snapshot
```

Exit codes follow the estate convention: 0 PASS, 1 REVIEW, 2 BLOCKED, 3 ERROR.
The replay **never overwrites** the committed historical `evidence/replay.json`
baseline. Each default invocation exclusively creates a fresh
`evidence/replay-<UTC>-<random>.json` receipt, fsyncs and reads back the exact
bytes, and prints only the SHA-256 checksum (**not a digital signature**).
Use `--out NEW_UNWRITTEN_PATH.json` to select an explicit *new* destination:
an existing file or symlink returns BLOCKED without changing any old bytes.
Unexpected check exception strings are redacted to fixed exception-type reasons;
local output paths and credentials are never printed.

## What it verifies (all against live public artifacts)

| Check | Protocol clause | Result on 2026-11-17 |
|---|---|---|
| Fixture package cold verification — 31 files fetched anonymously from `szl-forge @ protocol-prep-2026-11-12`, SHA-256 compared against the published manifest | A1, B2, B2.1, B2.2 | **31/31 byte-exact, PASS** |
| Battery v2.1 determinism — the two held-out receipts (03:14Z, 07:38Z) compared field by field | A2, A9 | **Identical on every measured value; only run metadata differs; PASS. c2/c5 pass, c3/c4 fail (trippable, tripped), `battery_admissible: false` as coded** |
| Independent digest recomputation — the Lean receipts' embedded `receipt_sha256` recomputed by code that shares nothing with the estate emitters | A6, 10.2, 10.4 | **3/3 REPRODUCED — recipe: SHA-256 over the receipt minus the digest field, canonicalized sort_keys=True with default separators. The recipe is undeclared in the receipt bodies, so the tool searches for it; future receipts should declare canon profile + algorithm** |
| Public inventory snapshot — GitHub org public repos + HF org public models/datasets/spaces | C1 (population freeze) | MEASURED, with snapshot sha256 |

## Honest corrections, on the record (clause 10.2: supersede, never edit)

- The sprint's independent-replay receipt of 17 Nov (wink-observatory-data
  `receipts/sprint-20261117-independent-replay.json`, commit `1f1a02ed`)
  reported the Lean digest check as **NOT_REPRODUCED**. That finding is
  **superseded**: this kit's recipe search — larger than the original pass's —
  reproduces all three digests. The original search space omitted the
  sorted-keys + default-separator combination. The supersession is published on
  the observatory. The residual, correct finding is narrower: the digests
  recompute, but their recipe is not declared, so a verifier must search for
  it.
- `battery_admissible: false` is reported as coded, never as a pass. The broken
  control failed 0 rules against a pre-declared must-fail.

## Scope and non-claims

Nothing here establishes model quality, honesty, or biological validity
(protocol section 2). The 16x figure elsewhere in the estate is a measured
21.9% capture rate versus a stated floor — not training speed and not a
model-quality improvement. Statuses used: theorem/proved, conjecture, measured,
experimental, runtime, production. This repo is Apache-2.0; the synthetic
fixture licence proposal for protocol item 9 is Apache-2.0 for the same reason.

## Layout

```
vgl_cold_replay/          stdlib-only Python package (fetch, verify, compare, replay)
receipts/                 the sprint's published receipts, mirrored from the observatory:
                          sprint-20261117-inventory-freeze.json (commit 48b65a63),
                          sprint-20261117-independent-replay.json (commit 1f1a02ed, contains
                          the superseded NOT_REPRODUCED finding, kept unedited per 10.2), and
                          sprint-20261117-digest-finding-supersession.json (commit be4d2485,
                          the supersession)
evidence/replay.json      output of the passing run committed as the baseline receipt
```

## A3 operator-2

Protocol clause A3 requires two operators; operator-2 must come from outside
the measurement path and is named before freeze. No freeze is asserted by
either party, so nothing here blocks on it — but this kit exists so that any
operator-2 can be productive on day one.
