"""
readback_validator.py
Validates the pilot's readback against the assigned ATC instruction.
Checks that the callsign, altitude, speed, and heading are correctly repeated.
"""

from dataclasses import dataclass
from .atc_engine import ATCInstruction
from .number_words import extract_numbers_from_text


@dataclass
class ValidationResult:
    is_correct:    bool
    missing_items: list[str]
    message:       str


def _numbers_match(assigned: int, found_numbers: list[int], tolerance: int) -> bool:
    """Check if any number in found_numbers is within tolerance of assigned."""
    return any(abs(n - assigned) <= tolerance for n in found_numbers)


def _heading_match(assigned: int, found_numbers: list[int], tolerance: int = 5) -> bool:
    """Heading wrap-aware match (e.g. 358 ≈ 002)."""
    for n in found_numbers:
        diff = abs((assigned - n + 540) % 360 - 180)
        if diff <= tolerance:
            return True
    return False


def validate_readback(
    transcription: str,
    instruction: ATCInstruction,
    callsign: str,
    config: dict,
) -> ValidationResult:
    """
    Validate pilot readback against the given ATC instruction.
    Returns a ValidationResult with is_correct, missing_items, and a message.
    """
    if not transcription or not transcription.strip():
        return ValidationResult(
            is_correct=False,
            missing_items=["readback (nothing heard)"],
            message="No readback detected. Please read back the instruction.",
        )

    text_lower = transcription.lower()
    missing = []

    # 1. Callsign check (at least the flight number part)
    callsign_parts = callsign.lower().split()
    callsign_found = any(part in text_lower for part in callsign_parts)
    if not callsign_found:
        missing.append("callsign")

    # 2. Extract all numbers from the transcription
    numbers = extract_numbers_from_text(transcription)

    # 3. Altitude check (±200 ft tolerance)
    alt_tol = config.get("altitude_tolerance_ft", 200)
    if not _numbers_match(instruction.altitude_ft, numbers, alt_tol):
        missing.append(f"altitude ({instruction.altitude_ft} ft)")

    # 4. Speed check (±10 kts tolerance)
    spd_tol = config.get("speed_tolerance_kts", 10)
    if not _numbers_match(instruction.speed_kts, numbers, spd_tol):
        missing.append(f"speed ({instruction.speed_kts} kts)")

    # 5. Heading check (±5 deg tolerance, wrap-aware)
    hdg_tol = config.get("heading_tolerance_deg", 5)
    if not _heading_match(instruction.heading_deg, numbers, hdg_tol):
        missing.append(f"heading ({instruction.heading_deg}°)")

    if not missing:
        return ValidationResult(
            is_correct=True,
            missing_items=[],
            message="Readback correct.",
        )

    missing_str = ", ".join(missing)
    return ValidationResult(
        is_correct=False,
        missing_items=missing,
        message=f"Readback incomplete. Missing: {missing_str}. Say again.",
    )
