"""
atc_engine.py
Generates realistic ATC instructions within configured ranges,
formats them into proper aviation phraseology.
"""

import random
from dataclasses import dataclass

from .number_words import to_spoken_altitude, to_spoken_speed, to_spoken_heading
from .sim_connector import FlightData


@dataclass
class ATCInstruction:
    altitude_ft:  int
    speed_kts:    int
    heading_deg:  int
    phrase:       str    # full spoken ATC phrase


def _snap(value: float, step: int) -> int:
    """Round value to nearest multiple of step."""
    return int(round(value / step) * step)


def _wrap_heading(h: float) -> int:
    """Wrap heading to 1–360 (ATC never says 000, uses 360)."""
    h = int(h) % 360
    return h if h != 0 else 360


def generate_instruction(
    current: FlightData,
    config: dict,
    last_instruction: "ATCInstruction | None" = None,
) -> ATCInstruction:
    """
    Generate a new ATC instruction that:
    - Differs meaningfully from the last instruction
    - Stays within configured altitude / speed ranges
    - Limits heading changes to heading_change_max degrees
    """
    alt_min, alt_max = config["altitude_range"]
    spd_min, spd_max = config["speed_range"]
    hdg_delta_max    = config["heading_change_max"]

    # Generate new altitude (snapped to nearest 1000 ft, different from current)
    alt_candidates = list(range(alt_min, alt_max + 1, 1000))
    if last_instruction:
        alt_candidates = [a for a in alt_candidates if a != last_instruction.altitude_ft]
    new_alt = _snap(random.choice(alt_candidates), 1000)

    # Generate new speed (snapped to nearest 10 kts, different from current)
    spd_candidates = list(range(spd_min, spd_max + 1, 10))
    if last_instruction:
        spd_candidates = [s for s in spd_candidates if s != last_instruction.speed_kts]
    new_spd = _snap(random.choice(spd_candidates), 10)

    # Generate new heading (current ± delta, wrapped, different from last)
    current_hdg = current.heading_deg
    delta = random.randint(15, hdg_delta_max) * random.choice([-1, 1])
    new_hdg = _wrap_heading(current_hdg + delta)
    # Snap to nearest 10 degrees for realism
    new_hdg = _wrap_heading(_snap(new_hdg, 10))
    if last_instruction and new_hdg == last_instruction.heading_deg:
        new_hdg = _wrap_heading(new_hdg + 10)

    phrase = _format_phrase(
        callsign=config["callsign"],
        station=config["station"],
        altitude_ft=new_alt,
        speed_kts=new_spd,
        heading_deg=new_hdg,
        current_alt=current.altitude_ft,
    )

    return ATCInstruction(
        altitude_ft=new_alt,
        speed_kts=new_spd,
        heading_deg=new_hdg,
        phrase=phrase,
    )


def _format_callsign(callsign: str) -> str:
    """
    'SriLankan 112' → 'SriLankan one one two'
    """
    parts = callsign.split()
    airline = " ".join(p for p in parts if not p.isdigit())
    number_parts = [p for p in parts if p.isdigit()]
    if number_parts:
        from .number_words import ONES
        spoken_num = " ".join(ONES[int(d)] for d in number_parts[0])
        return f"{airline} {spoken_num}"
    return callsign


def _format_phrase(
    callsign: str,
    station: str,
    altitude_ft: int,
    speed_kts: int,
    heading_deg: int,
    current_alt: float,
) -> str:
    """
    Build the full ATC phraseology string.
    Example:
      'SriLankan one one two, Colombo Tower,
       climb and maintain six thousand feet,
       maintain two four zero knots,
       turn heading one eight zero.'
    """
    spoken_callsign = _format_callsign(callsign)
    spoken_alt      = to_spoken_altitude(altitude_ft)
    spoken_spd      = to_spoken_speed(speed_kts)
    spoken_hdg      = to_spoken_heading(heading_deg)

    # Climb vs descend vs maintain
    if altitude_ft > current_alt + 100:
        alt_action = f"climb and maintain {spoken_alt} feet"
    elif altitude_ft < current_alt - 100:
        alt_action = f"descend and maintain {spoken_alt} feet"
    else:
        alt_action = f"maintain {spoken_alt} feet"

    return (
        f"{spoken_callsign}, {station}, "
        f"{alt_action}, "
        f"maintain {spoken_spd} knots, "
        f"turn heading {spoken_hdg}."
    )
