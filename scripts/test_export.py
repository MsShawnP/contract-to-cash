"""Tests for export_json utility functions."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from export_json import num_to_word


class TestNumToWord:
    def test_zero(self):
        assert num_to_word(0) == "Zero"

    def test_single_digits(self):
        assert num_to_word(1) == "One"
        assert num_to_word(9) == "Nine"

    def test_teens(self):
        assert num_to_word(10) == "Ten"
        assert num_to_word(13) == "Thirteen"
        assert num_to_word(19) == "Nineteen"

    def test_tens(self):
        assert num_to_word(20) == "Twenty"
        assert num_to_word(30) == "Thirty"
        assert num_to_word(90) == "Ninety"

    def test_compound(self):
        assert num_to_word(21) == "Twenty-One"
        assert num_to_word(59) == "Fifty-Nine"
        assert num_to_word(86) == "Eighty-Six"
        assert num_to_word(99) == "Ninety-Nine"

    def test_hundred_falls_back_to_digit(self):
        assert num_to_word(100) == "100"

    def test_large_number_falls_back(self):
        assert num_to_word(255) == "255"
