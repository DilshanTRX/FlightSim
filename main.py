"""
main.py
ATC Training System – Main Entry Point

Usage:
  python main.py            # Connect to FSX via SimConnect
  python main.py --mock     # Run without FSX (mock aircraft)
"""

import json
import sys
import time
import argparse
from pathlib import Path

from colorama import init as colorama_init, Fore, Style

from atc_system.sim_connector  import create_connector
from atc_system.atc_engine     import generate_instruction
from atc_system.tts_engine     import TTSEngine
from atc_system.speech_recognizer  import SpeechRecognizer
from atc_system.readback_validator import validate_readback
from atc_system.compliance_monitor import wait_for_compliance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BANNER = r"""
  _  _____ ____   _____           _       _
 / \|_   _/ ___| |_   _| __ __ _(_)_ __ (_)_ __   __ _
/ _ \ | || |       | || '__/ _` | | '_ \| | '_ \ / _` |
/ ___ \| || |___    | || | | (_| | | | | | | | | | (_| |
/_/   \_\_| \____|   |_||_|  \__,_|_|_| |_|_|_| |_|\__, |
                                                      |___/
  ATC Training System  |  FSX Edition
"""

DIVIDER = Fore.BLUE + "─" * 65 + Style.RESET_ALL


def load_config(path: str = "config.json") -> dict:
    with open(path) as f:
        return json.load(f)


def print_banner(config: dict) -> None:
    print(Fore.CYAN + BANNER + Style.RESET_ALL)
    print(DIVIDER)
    print(f"  Callsign : {Fore.WHITE}{config['callsign']}{Style.RESET_ALL}")
    print(f"  Station  : {Fore.WHITE}{config['station']}{Style.RESET_ALL}")
    print(f"  Alt range: {config['altitude_range'][0]}–{config['altitude_range'][1]} ft")
    print(f"  Spd range: {config['speed_range'][0]}–{config['speed_range'][1]} kts")
    print(DIVIDER)


def connect_with_retry(sim, max_attempts: int = 10, delay: float = 5.0) -> bool:
    for attempt in range(1, max_attempts + 1):
        print(f"\r[SIM] Connecting to FSX... attempt {attempt}/{max_attempts}", end="", flush=True)
        if sim.connect():
            print()
            return True
        time.sleep(delay)
    print()
    return False


# ---------------------------------------------------------------------------
# Core training loop
# ---------------------------------------------------------------------------

def training_loop(sim, tts: TTSEngine, mic: SpeechRecognizer, config: dict) -> None:
    callsign    = config["callsign"]
    max_attempts = config.get("max_readback_attempts", 3)
    instruction_count = 0

    last_instruction = None

    while True:
        print(f"\n{DIVIDER}")
        instruction_count += 1
        print(Fore.BLUE + f"  Instruction #{instruction_count}" + Style.RESET_ALL)

        # 1. Read current flight state
        flight_data = None
        while flight_data is None:
            flight_data = sim.get_flight_data()
            if flight_data is None:
                print(Fore.YELLOW + "[SIM] Waiting for valid flight data..." + Style.RESET_ALL)
                time.sleep(2)

        print(
            f"  ✈  Current state → "
            f"ALT: {flight_data.altitude_ft:.0f} ft | "
            f"SPD: {flight_data.speed_kts:.0f} kts | "
            f"HDG: {flight_data.heading_deg:.0f}°"
        )

        # 2. Generate ATC instruction
        instruction = generate_instruction(flight_data, config, last_instruction)
        last_instruction = instruction

        print(DIVIDER)
        print(Fore.YELLOW + f"\n[ATC] '{instruction.phrase}'\n" + Style.RESET_ALL)

        # 3. Speak instruction aloud
        tts.speak(instruction.phrase)

        # 4. Readback loop
        readback_ok = False
        for attempt in range(1, max_attempts + 1):
            print(Fore.CYAN + f"\n[ATC] Awaiting readback (attempt {attempt}/{max_attempts})..." + Style.RESET_ALL)

            transcription = mic.listen()

            if transcription is None:
                print(Fore.YELLOW + "[ATC] No response. Repeating instruction." + Style.RESET_ALL)
                tts.speak(instruction.phrase)
                continue

            result = validate_readback(transcription, instruction, callsign, config)

            if result.is_correct:
                print(Fore.GREEN + f"\n[ATC] {result.message}" + Style.RESET_ALL)
                tts.speak(result.message)
                readback_ok = True
                break
            else:
                print(Fore.RED + f"\n[ATC] {result.message}" + Style.RESET_ALL)
                tts.speak(result.message)
                # Re-speak the instruction
                time.sleep(0.5)
                tts.speak(instruction.phrase)

        if not readback_ok:
            msg = f"{callsign}, unable to verify readback. Proceeding with instruction."
            print(Fore.YELLOW + f"[ATC] {msg}" + Style.RESET_ALL)
            tts.speak(msg)

        # 5. Monitor flight compliance
        complied, elapsed = wait_for_compliance(sim, instruction, config)

        if complied:
            msg = f"{callsign}, roger. Standby for next instruction."
        else:
            msg = (
                f"{callsign}, you did not reach the assigned values within "
                f"{config['compliance_timeout_sec']} seconds. Continuing."
            )
            print(Fore.RED + f"\n[MONITOR] {msg}" + Style.RESET_ALL)

        tts.speak(msg)

        # Brief pause before next instruction
        time.sleep(2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    colorama_init()

    parser = argparse.ArgumentParser(description="ATC Training System – FSX Edition")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run without FSX (mock aircraft for voice/TTS testing)",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file (default: config.json)",
    )
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(Fore.RED + f"[ERROR] Config file not found: {config_path}" + Style.RESET_ALL)
        sys.exit(1)
    config = load_config(str(config_path))

    print_banner(config)

    # Initialise subsystems
    tts = TTSEngine(rate=config.get("tts_rate", 150), voice_preference=config.get("tts_voice", "auto"))
    mic = SpeechRecognizer(timeout_sec=config.get("listen_timeout_sec", 15))

    # Simulator connector
    sim = create_connector(mock=args.mock)
    if not args.mock:
        if not connect_with_retry(sim):
            print(
                Fore.RED
                + "\n[ERROR] Could not connect to FSX after multiple attempts.\n"
                + "  • Make sure FSX is running before launching this script.\n"
                + "  • Use '--mock' to test without FSX."
                + Style.RESET_ALL
            )
            sys.exit(1)
    else:
        sim.connect()

    print(Fore.GREEN + "\n[SYSTEM] All systems ready. Starting training loop.\n" + Style.RESET_ALL)
    tts.speak(f"ATC training system active. {config['callsign']}, {config['station']} is online.")

    try:
        training_loop(sim, tts, mic, config)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n[SYSTEM] Training session ended by user." + Style.RESET_ALL)
        tts.speak("Training session complete. Good flight.")
    finally:
        sim.disconnect()


if __name__ == "__main__":
    main()
