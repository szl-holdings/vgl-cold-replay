"""Network-free negative controls for immutable VGL cold-replay receipts."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from vgl_cold_replay import replay


@contextmanager
def isolated_cwd():
    previous = Path.cwd()
    with tempfile.TemporaryDirectory() as folder:
        try:
            os.chdir(folder)
            yield Path(folder)
        finally:
            os.chdir(previous)


@contextmanager
def synthetic_checks(*, failing=False, malformed=False):
    def fixture():
        if failing:
            raise RuntimeError("Bearer SYNTHETIC_PRIVATE_DO_NOT_ECHO")
        if malformed:
            return {"check": "synthetic", "verdict": "PASS", "value": float("nan")}
        return {"check": "fixture", "verdict": "PASS"}

    with patch.object(replay.fixture_verify, "run", side_effect=fixture), (
        patch.object(replay.battery_determinism, "run",
                     return_value={"check": "battery", "verdict": "PASS"})
    ), patch.object(
        replay.independent_digest_check, "run",
        return_value={"check": "digest", "verdict": "REPRODUCED"}
    ), patch.object(
        replay.inventory_freeze, "run",
        side_effect=AssertionError("INVENTORY_MUST_NOT_BE_FETCHED")
    ):
        yield


class ReceiptPreservationTests(unittest.TestCase):
    def test_default_keeps_baseline_and_creates_two_distinct_receipts(self):
        with isolated_cwd() as root, synthetic_checks():
            old = root / "evidence" / "replay.json"
            old.parent.mkdir()
            old.write_bytes(b"historical-baseline-never-overwrite")
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(replay.main(["--skip-inventory"]), 0)
                self.assertEqual(replay.main(["--skip-inventory"]), 0)
            self.assertEqual(old.read_bytes(), b"historical-baseline-never-overwrite")
            files = list(old.parent.glob("replay-*.json"))
            self.assertEqual(len(files), 2)
            self.assertNotEqual(files[0].name, files[1].name)
            for path in files:
                result = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(result["overall"], "PASS")
                self.assertEqual(len(result["checks"]), 3)
                self.assertFalse(result["signature_verified"])
            self.assertNotIn(str(root), stdout.getvalue())

    def test_explicit_destination_cannot_overwrite_earlier_receipt(self):
        with isolated_cwd() as root, synthetic_checks():
            destination = root / "output.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(replay.main(["--skip-inventory", "--out", str(destination)]), 0)
            original = destination.read_bytes()
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(replay.main(["--skip-inventory", "--out", str(destination)]), 2)
            self.assertEqual(destination.read_bytes(), original)
            self.assertIn("DESTINATION_ALREADY_EXISTS", stdout.getvalue())
            self.assertNotIn(str(destination), stdout.getvalue())

    def test_check_exception_becomes_review_without_echoing_details(self):
        with isolated_cwd() as root, synthetic_checks(failing=True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(replay.main(["--skip-inventory"]), 1)
            saved = list((root / "evidence").glob("replay-*.json"))
            self.assertEqual(len(saved), 1)
            result = json.loads(saved[0].read_text(encoding="utf-8"))
            self.assertEqual(result["overall"], "REVIEW")
            self.assertEqual(result["checks"][0]["reason"], "CHECK_EXCEPTION_RuntimeError")
            self.assertNotIn("SYNTHETIC_PRIVATE_DO_NOT_ECHO", str(result))
            self.assertNotIn("SYNTHETIC_PRIVATE_DO_NOT_ECHO", stdout.getvalue())

    def test_nonfinite_check_result_does_not_create_receipt(self):
        with isolated_cwd() as root, synthetic_checks(malformed=True):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(replay.main(["--skip-inventory"]), 3)
            self.assertIn("NONFINITE_OR_INVALID_CHECK_RESULT", stdout.getvalue())
            self.assertFalse((root / "evidence").exists())

    def test_missing_explicit_parent_fails_without_creating_new_directories(self):
        with isolated_cwd() as root, synthetic_checks():
            destination = root / "nonexistent" / "output.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(replay.main(["--skip-inventory", "--out", str(destination)]), 3)
            self.assertEqual(json.loads(stdout.getvalue())["reason"],
                             "OUTPUT_WRITE_UNAVAILABLE")
            self.assertFalse(destination.parent.exists())

    def test_skipped_inventory_never_calls_an_external_inventory(self):
        with isolated_cwd(), synthetic_checks():
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(replay.main(["--skip-inventory"]), 0)
            output = json.loads(stdout.getvalue())
            self.assertEqual(output["check_count"], 3)
            self.assertEqual(len(output["receipt_sha256"]), 64)
            self.assertTrue(output["exclusive_create"])
            self.assertFalse(output["signature_verified"])
            self.assertFalse(output["path_disclosed"])


if __name__ == "__main__":
    unittest.main()
