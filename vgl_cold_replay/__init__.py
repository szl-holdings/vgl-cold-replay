"""vgl-cold-replay: reproduce the 2026-11-17 sprint evidence from public artifacts alone.

Everything here runs anonymous: no member access, no tokens, no secrets.
Standard library only. Fail closed: a check that cannot run is NOT_RUN,
never silently passed. Protocol alignment: v1.1 clauses A1, A9, A10, B2,
B2.1, 10.4 (negative verdicts carry their own search).
"""
__version__ = "1.0.0"
