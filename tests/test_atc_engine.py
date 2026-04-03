"""
tests/test_atc_engine.py
Unit tests for ATC instruction generation.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from atc_system.sim_connector import FlightData
from atc_system.atc_engine import generate_instruction, ATCInstruction

CONFIG = {
    "callsign": "SriLankan 112",
    "station": "Colombo Tower",
    "altitude_range": [2000, 10000],
    "speed_range": [200, 280],
    "heading_change_max": 60,
}

FLIGHT = FlightData(altitude_ft=5000, speed_kts=240, heading_deg=90)


def test_altitude_in_range():
    for _ in range(20):
        inst = generate_instruction(FLIGHT, CONFIG)
        assert CONFIG["altitude_range"][0] <= inst.altitude_ft <= CONFIG["altitude_range"][1]


def test_speed_in_range():
    for _ in range(20):
        inst = generate_instruction(FLIGHT, CONFIG)
        assert CONFIG["speed_range"][0] <= inst.speed_kts <= CONFIG["speed_range"][1]


def test_heading_change_within_limit():
    for _ in range(20):
        inst = generate_instruction(FLIGHT, CONFIG, last_instruction=None)
        current_hdg = FLIGHT.heading_deg
        diff = abs((inst.heading_deg - current_hdg + 540) % 360 - 180)
        assert diff <= CONFIG["heading_change_max"] + 10  # +10 for snap rounding


def test_altitude_snapped_to_1000():
    for _ in range(20):
        inst = generate_instruction(FLIGHT, CONFIG)
        assert inst.altitude_ft % 1000 == 0


def test_speed_snapped_to_10():
    for _ in range(20):
        inst = generate_instruction(FLIGHT, CONFIG)
        assert inst.speed_kts % 10 == 0


def test_phrase_contains_callsign():
    inst = generate_instruction(FLIGHT, CONFIG)
    assert "sri" in inst.phrase.lower() or "lankan" in inst.phrase.lower()


def test_phrase_contains_station():
    inst = generate_instruction(FLIGHT, CONFIG)
    assert "colombo" in inst.phrase.lower()


def test_phrase_ends_with_period():
    inst = generate_instruction(FLIGHT, CONFIG)
    assert inst.phrase.strip().endswith(".")


def test_different_from_last_instruction():
    last = ATCInstruction(altitude_ft=5000, speed_kts=240, heading_deg=90, phrase="")
    for _ in range(20):
        inst = generate_instruction(FLIGHT, CONFIG, last_instruction=last)
        # At least one of the three should differ
        assert (
            inst.altitude_ft != last.altitude_ft
            or inst.speed_kts != last.speed_kts
            or inst.heading_deg != last.heading_deg
        )
