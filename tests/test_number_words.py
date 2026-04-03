"""
tests/test_number_words.py
Unit tests for the number_words module.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from atc_system.number_words import (
    to_spoken_altitude,
    to_spoken_speed,
    to_spoken_heading,
    parse_spoken_number,
    extract_numbers_from_text,
)


class TestSpokenAltitude:
    def test_six_thousand(self):
        assert to_spoken_altitude(6000) == "six thousand"

    def test_three_thousand(self):
        assert to_spoken_altitude(3000) == "three thousand"

    def test_ten_thousand(self):
        assert to_spoken_altitude(10000) == "ten thousand"

    def test_two_thousand(self):
        assert to_spoken_altitude(2000) == "two thousand"

    def test_snaps_to_nearest_100(self):
        # 5950 → 6000
        assert "six thousand" in to_spoken_altitude(5950)

    def test_three_thousand_five_hundred(self):
        assert to_spoken_altitude(3500) == "three thousand five hundred"


class TestSpokenSpeed:
    def test_two_four_zero(self):
        assert to_spoken_speed(240) == "two four zero"

    def test_two_zero_zero(self):
        assert to_spoken_speed(200) == "two zero zero"

    def test_two_eight_zero(self):
        assert to_spoken_speed(280) == "two eight zero"


class TestSpokenHeading:
    def test_one_eight_zero(self):
        assert to_spoken_heading(180) == "one eight zero"

    def test_zero_zero_five(self):
        assert to_spoken_heading(5) == "zero zero five"

    def test_three_six_zero(self):
        assert to_spoken_heading(360) == "three six zero"

    def test_zero_nine_zero(self):
        assert to_spoken_heading(90) == "zero nine zero"


class TestParseSpokenNumber:
    def test_digit_sequence(self):
        assert parse_spoken_number("two four zero") == 240

    def test_altitude_phrase(self):
        assert parse_spoken_number("six thousand") == 6000

    def test_bare_integer(self):
        assert parse_spoken_number("6000") == 6000

    def test_one_eight_zero(self):
        assert parse_spoken_number("one eight zero") == 180

    def test_niner_alias(self):
        assert parse_spoken_number("two niner zero") == 290


class TestExtractNumbers:
    def test_finds_altitude_and_heading(self):
        text = "SriLankan 112 climb and maintain six thousand feet heading one eight zero"
        numbers = extract_numbers_from_text(text)
        assert 6000 in numbers
        assert 180 in numbers

    def test_finds_bare_numbers(self):
        text = "maintain 240 knots"
        numbers = extract_numbers_from_text(text)
        assert 240 in numbers

    def test_callsign_number(self):
        text = "SriLankan 112 climbing to six thousand"
        numbers = extract_numbers_from_text(text)
        assert 6000 in numbers
