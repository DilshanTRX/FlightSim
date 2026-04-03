"""
compliance_monitor.py
Monitors live flight data and waits until the pilot has reached
the assigned altitude, speed, and heading within tolerance.
"""

import time
from colorama import Fore, Style

from .atc_engine import ATCInstruction
from .sim_connector import FlightData


def _heading_diff(a: float, b: float) -> float:
    """Smallest angular difference between two headings (0–180)."""
    return abs((a - b + 540) % 360 - 180)


def _bar(current: float, target: float, tolerance: float, width: int = 12) -> str:
    """ASCII progress bar showing closeness to target."""
    diff = abs(current - target)
    ratio = max(0.0, 1.0 - diff / max(tolerance * 4, 1))
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    color = Fore.GREEN if diff <= tolerance else Fore.YELLOW
    return color + f"[{bar}]" + Style.RESET_ALL


def _is_compliant(data: FlightData, instruction: ATCInstruction, config: dict) -> bool:
    alt_ok = abs(data.altitude_ft - instruction.altitude_ft) <= config["altitude_tolerance_ft"]
    spd_ok = abs(data.speed_kts   - instruction.speed_kts)   <= config["speed_tolerance_kts"]
    hdg_ok = _heading_diff(data.heading_deg, instruction.heading_deg) <= config["heading_tolerance_deg"]
    return alt_ok and spd_ok and hdg_ok


def wait_for_compliance(
    sim,
    instruction: ATCInstruction,
    config: dict,
    poll_interval: float = 2.0,
) -> tuple[bool, float]:
    """
    Poll flight data until the aircraft reaches assigned values or timeout.

    Returns:
        (complied: bool, elapsed_sec: float)
    """
    timeout = config.get("compliance_timeout_sec", 120)
    start = time.time()

    # If mock simulator, tell it to start drifting toward targets
    if hasattr(sim, "set_targets"):
        sim.set_targets(instruction.altitude_ft, instruction.speed_kts, instruction.heading_deg)

    print(Fore.CYAN + "\n[MONITOR] Waiting for flight compliance..." + Style.RESET_ALL)
    print(
        f"  Target → ALT: {instruction.altitude_ft} ft | "
        f"SPD: {instruction.speed_kts} kts | "
        f"HDG: {instruction.heading_deg}°"
    )
    print(Style.DIM + "  (Adjust your aircraft to match the assigned values)" + Style.RESET_ALL)

    last_print_time = 0.0
    while True:
        elapsed = time.time() - start
        if elapsed >= timeout:
            print(Fore.RED + f"\n[MONITOR] Compliance timeout after {elapsed:.0f}s." + Style.RESET_ALL)
            return False, elapsed

        data = sim.get_flight_data()
        if data is None:
            time.sleep(poll_interval)
            continue

        if _is_compliant(data, instruction, config):
            elapsed = time.time() - start
            print(Fore.GREEN + f"\n[MONITOR] ✓ Compliance achieved in {elapsed:.0f}s." + Style.RESET_ALL)
            return True, elapsed

        # Print live progress every 3 seconds
        now = time.time()
        if now - last_print_time >= 3.0:
            alt_bar = _bar(data.altitude_ft,  instruction.altitude_ft,  config["altitude_tolerance_ft"])
            spd_bar = _bar(data.speed_kts,    instruction.speed_kts,    config["speed_tolerance_kts"])
            hdg_bar = _bar(data.heading_deg,  instruction.heading_deg,  config["heading_tolerance_deg"])
            remaining = int(timeout - elapsed)
            print(
                f"\r  ALT {alt_bar} {data.altitude_ft:6.0f}/{instruction.altitude_ft} ft  "
                f"SPD {spd_bar} {data.speed_kts:5.0f}/{instruction.speed_kts} kts  "
                f"HDG {hdg_bar} {data.heading_deg:5.0f}/{instruction.heading_deg}°  "
                f"⏱ {remaining}s",
                end="",
                flush=True,
            )
            last_print_time = now

        time.sleep(poll_interval)
