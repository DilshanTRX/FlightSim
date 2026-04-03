"""
tests/test_readback_validator.py
Unit tests for the pilot readback validator.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from atc_system.atc_engine import ATCInstruction
from atc_system.readback_validator import validate_readback

CONFIG = {
    "altitude_tolerance_ft": 200,
    "speed_tolerance_kts": 10,
    "heading_tolerance_deg": 5,
}

INSTRUCTION = ATCInstruction(
    altitude_ft=6000,
    speed_kts=240,
    heading_deg=180,
    phrase="SriLankan one one two, Colombo Tower, climb and maintain six thousand feet, "
           "maintain two four zero knots, turn heading one eight zero.",
)

CALLSIGN = "SriLankan 112"


def test_correct_spoken_readback():
    result = validate_readback(
        "SriLankan one one two, climbing to six thousand feet, "
        "maintain two four zero knots, heading one eight zero",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert result.is_correct


def test_correct_numeric_readback():
    result = validate_readback(
        "SriLankan 112 climb maintain 6000 feet 240 knots heading 180",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert result.is_correct


def test_missing_altitude():
    result = validate_readback(
        "SriLankan 112 maintain two four zero knots heading one eight zero",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert not result.is_correct
    assert any("altitude" in item for item in result.missing_items)


def test_missing_speed():
    result = validate_readback(
        "SriLankan 112 climbing six thousand feet heading one eight zero",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert not result.is_correct
    assert any("speed" in item for item in result.missing_items)


def test_missing_heading():
    result = validate_readback(
        "SriLankan 112 climbing six thousand feet maintain two four zero knots",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert not result.is_correct
    assert any("heading" in item for item in result.missing_items)


def test_empty_readback():
    result = validate_readback("", INSTRUCTION, CALLSIGN, CONFIG)
    assert not result.is_correct


def test_none_readback():
    result = validate_readback(None, INSTRUCTION, CALLSIGN, CONFIG)
    assert not result.is_correct


def test_wrong_altitude():
    result = validate_readback(
        "SriLankan 112 climb to three thousand feet two four zero knots heading one eight zero",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert not result.is_correct
    assert any("altitude" in item for item in result.missing_items)


def test_heading_tolerance():
    # 182 is within 5 degrees of 180 — should pass
    result = validate_readback(
        "SriLankan 112 six thousand feet two four zero knots heading one eight two",
        INSTRUCTION, CALLSIGN, CONFIG,
    )
    assert result.is_correct
