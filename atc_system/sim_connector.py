"""
sim_connector.py
Connects to FSX via SimConnect and exposes live flight data.
Falls back to a MockSimulator when --mock flag is used.

Architecture note:
  FSX is a 32-bit app; SimConnect.dll is 32-bit.
  This module checks Python bitness at import time and warns the user.
"""

import struct
import sys
import time
import platform

from colorama import Fore, Style


# ---------------------------------------------------------------------------
# Architecture check
# ---------------------------------------------------------------------------

def _check_architecture() -> None:
    bits = struct.calcsize("P") * 8
    if bits != 32:
        print(
            Fore.YELLOW
            + f"[WARNING] Running {bits}-bit Python. FSX SimConnect requires 32-bit Python.\n"
            + "          If connection fails, install the 32-bit Python interpreter from python.org\n"
            + "          and re-run. Alternatively, use '--mock' mode to test without FSX."
            + Style.RESET_ALL
        )


# ---------------------------------------------------------------------------
# FlightData dataclass
# ---------------------------------------------------------------------------

class FlightData:
    __slots__ = ("altitude_ft", "speed_kts", "heading_deg")

    def __init__(self, altitude_ft: float, speed_kts: float, heading_deg: float):
        self.altitude_ft = altitude_ft
        self.speed_kts   = speed_kts
        self.heading_deg = heading_deg

    def __repr__(self) -> str:
        return (
            f"FlightData(alt={self.altitude_ft:.0f}ft, "
            f"spd={self.speed_kts:.0f}kts, "
            f"hdg={self.heading_deg:.0f}°)"
        )


# ---------------------------------------------------------------------------
# FSX SimConnect connector
# ---------------------------------------------------------------------------

class FSXSimConnector:
    """
    Connects to FSX via the SimConnect Python library.
    Reads INDICATED_ALTITUDE, AIRSPEED_INDICATED, and PLANE_HEADING_DEGREES_MAGNETIC.
    """

    def __init__(self):
        _check_architecture()
        self._aq = None
        self._sm = None
        self._connected = False

    def connect(self) -> bool:
        """Attempt connection to FSX. Returns True on success."""
        try:
            from SimConnect import SimConnect, AircraftRequests  # type: ignore
            self._sm = SimConnect()
            self._aq = AircraftRequests(self._sm, _time=0)
            self._connected = True
            print(Fore.GREEN + "[SIM] Connected to FSX via SimConnect." + Style.RESET_ALL)
            return True
        except Exception as exc:
            print(
                Fore.RED
                + f"[SIM] Failed to connect to FSX: {exc}\n"
                + "      Ensure FSX is running and SimConnect.dll is accessible.\n"
                + "      Use '--mock' mode to run without FSX."
                + Style.RESET_ALL
            )
            self._connected = False
            return False

    def get_flight_data(self) -> FlightData | None:
        """Poll current altitude, airspeed, and heading from FSX."""
        if not self._connected:
            return None
        try:
            alt = self._aq.get("INDICATED_ALTITUDE")
            spd = self._aq.get("AIRSPEED_INDICATED")
            hdg = self._aq.get("PLANE_HEADING_DEGREES_MAGNETIC")

            # SimConnect sometimes returns None while sim is loading
            if None in (alt, spd, hdg):
                return None

            return FlightData(
                altitude_ft=float(alt),
                speed_kts=float(spd),
                heading_deg=float(hdg) % 360,
            )
        except Exception as exc:
            print(Fore.RED + f"[SIM] Read error: {exc}" + Style.RESET_ALL)
            self._connected = False
            return None

    def disconnect(self) -> None:
        if self._sm:
            try:
                self._sm.exit()
            except Exception:
                pass
        self._connected = False
        print(Fore.YELLOW + "[SIM] Disconnected from FSX." + Style.RESET_ALL)

    @property
    def is_connected(self) -> bool:
        return self._connected


# ---------------------------------------------------------------------------
# Mock simulator (no FSX needed)
# ---------------------------------------------------------------------------

class MockSimConnector:
    """
    Simulates an aircraft for testing without FSX.
    Aircraft starts at fixed state and slowly drifts toward assigned targets.
    """

    def __init__(self):
        self._alt = 5000.0
        self._spd = 240.0
        self._hdg = 090.0
        self._target_alt = 5000.0
        self._target_spd = 240.0
        self._target_hdg = 090.0
        self._connected = True
        print(Fore.CYAN + "[SIM] Mock simulator active (no FSX connection)." + Style.RESET_ALL)

    def connect(self) -> bool:
        return True

    def set_targets(self, alt: float, spd: float, hdg: float) -> None:
        """Called by compliance monitor so the mock aircraft can drift toward targets."""
        self._target_alt = alt
        self._target_spd = spd
        self._target_hdg = hdg

    def _drift(self, current: float, target: float, rate: float) -> float:
        diff = target - current
        step = min(abs(diff), rate) * (1 if diff >= 0 else -1)
        return current + step

    def get_flight_data(self) -> FlightData:
        # Slowly move toward targets (simulates pilot flying to new values)
        self._alt = self._drift(self._alt, self._target_alt, 50)   # 50 ft/poll
        self._spd = self._drift(self._spd, self._target_spd, 2)    # 2 kts/poll
        # Heading wrap-around handled simply
        hdg_diff = (self._target_hdg - self._hdg + 540) % 360 - 180
        self._hdg = (self._hdg + min(abs(hdg_diff), 1) * (1 if hdg_diff >= 0 else -1)) % 360
        return FlightData(self._alt, self._spd, self._hdg)

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_connector(mock: bool = False):
    """Return the appropriate simulator connector."""
    if mock:
        return MockSimConnector()
    return FSXSimConnector()
