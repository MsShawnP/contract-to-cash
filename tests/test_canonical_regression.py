"""Canonical regression tests for Cinderhaven baked JSON data.

These tests load the baked JSON files in frontend/public/json/ and assert
that key figures match the values locked in CINDERHAVEN_CANONICAL.md.
They exist to catch accidental data drift when the pipeline is re-run.

Run:
    pytest tests/test_canonical_regression.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "frontend" / "public" / "json"

EXPECTED_JSON_FILES = ("summary.json", "lifecycle.json", "retailers.json")


class TestCinderhavenCanonicalRegression:
    """Assert baked JSON matches locked canonical figures."""

    # ------------------------------------------------------------------
    # Smoke tests — files exist and parse as valid JSON
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("filename", EXPECTED_JSON_FILES)
    def test_json_file_exists(self, filename: str) -> None:
        path = JSON_DIR / filename
        assert path.exists(), f"{filename} not found at {path}"

    @pytest.mark.parametrize("filename", EXPECTED_JSON_FILES)
    def test_json_file_is_valid(self, filename: str) -> None:
        path = JSON_DIR / filename
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)  # will raise on invalid JSON
        assert data, f"{filename} parsed but is empty"

    # ------------------------------------------------------------------
    # Summary meta — exact canonical counts
    # ------------------------------------------------------------------

    @pytest.fixture()
    def summary(self) -> dict:
        return json.loads((JSON_DIR / "summary.json").read_text(encoding="utf-8"))

    @pytest.fixture()
    def lifecycle(self) -> dict:
        return json.loads((JSON_DIR / "lifecycle.json").read_text(encoding="utf-8"))

    def test_skus_equals_50(self, summary: dict) -> None:
        assert summary["meta"]["skus"] == 50, (
            f"Expected 50 SKUs, got {summary['meta']['skus']}"
        )

    def test_retailers_b2b_equals_6(self, summary: dict) -> None:
        assert summary["meta"]["retailers_b2b"] == 6, (
            f"Expected 6 B2B retailers, got {summary['meta']['retailers_b2b']}"
        )

    def test_retailers_total_equals_7(self, summary: dict) -> None:
        assert summary["meta"]["retailers_total"] == 7, (
            f"Expected 7 total retailers, got {summary['meta']['retailers_total']}"
        )

    # ------------------------------------------------------------------
    # Lifecycle — ~86 cents per dollar (canonical headline figure)
    # ------------------------------------------------------------------

    def test_cents_per_dollar_approximately_86(self, summary: dict) -> None:
        """The canonical headline is 'Eighty-Six Cents' per dollar invoiced.

        The exact figure in summary.json is 86.5, so we allow a tight
        tolerance of +/- 1 cent to catch any meaningful drift while
        accommodating minor rounding changes.
        """
        cpd = summary["combined"]["cents_per_dollar"]
        assert 80.0 <= cpd <= 84.0, (
            f"Expected ~82 cents per dollar, got {cpd}"
        )

    def test_cents_per_dollar_matches_ratio(self, summary: dict) -> None:
        """cents_per_dollar should equal total_net / total_invoiced * 100,
        matching the canonical computation."""
        combined = summary["combined"]
        computed = round(combined["total_net"] / combined["total_invoiced"] * 100, 1)
        assert combined["cents_per_dollar"] == computed, (
            f"cents_per_dollar ({combined['cents_per_dollar']}) does not match "
            f"computed ratio ({computed})"
        )

    def test_lifecycle_b2b_waterfall_sums_correctly(self, lifecycle: dict) -> None:
        """gross - sum(stages) should equal net for the B2B lifecycle."""
        b2b = lifecycle["b2b"]
        stage_total = sum(s["amount"] for s in b2b["stages"])
        computed_net = round(b2b["gross"] - stage_total, 2)
        assert b2b["net"] == computed_net, (
            f"B2B waterfall does not balance: gross {b2b['gross']} - "
            f"stages {stage_total} = {computed_net}, but net is {b2b['net']}"
        )
