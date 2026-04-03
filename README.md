# ATC Training System – FSX Edition

An AI-based Air Traffic Control training system that connects live to **Microsoft Flight Simulator X (2006)**, issues realistic ATC instructions via text-to-speech, validates your voice readback, and monitors your flight compliance.

---

## Quick Start

### 1. Install Dependencies
```bash
python setup.py
```
> ⚠️ FSX requires **32-bit Python** for SimConnect. Download from [python.org](https://www.python.org/downloads/windows/) → *Windows x86 executable installer*

### 2. Start FSX
Load any flight before running the training system.

### 3. Run
```bash
# Live mode (connects to FSX)
python main.py

# Mock mode (no FSX needed — tests voice & TTS)
python main.py --mock
```

---

## How It Works

```
[FSX] → Flight Data → ATC Instruction Generated
                            ↓
                    [TTS speaks instruction]
                            ↓
                  [Microphone listens for readback]
                            ↓
               [Validates readback → "Readback correct" / "Say again"]
                            ↓
               [Monitors flight until values match]
                            ↓
                     [Next instruction]
```

---

## File Structure

```
FlightSim/
├── main.py                    # Entry point – training loop
├── setup.py                   # Install dependencies
├── config.json                # User-configurable settings
├── requirements.txt
├── atc_system/
│   ├── sim_connector.py       # FSX SimConnect bridge + MockSimulator
│   ├── atc_engine.py          # ATC instruction generator
│   ├── tts_engine.py          # Text-to-speech (pyttsx3)
│   ├── speech_recognizer.py   # Microphone → text (Google Web Speech)
│   ├── readback_validator.py  # Validates pilot readback
│   ├── compliance_monitor.py  # Flight compliance monitoring
│   └── number_words.py        # Aviation number ↔ word conversion
└── tests/
    ├── test_number_words.py
    ├── test_atc_engine.py
    └── test_readback_validator.py
```

---

## Configuration (`config.json`)

| Key | Default | Description |
|-----|---------|-------------|
| `callsign` | `"SriLankan 112"` | Your aircraft callsign |
| `station` | `"Colombo Tower"` | ATC station name |
| `altitude_range` | `[2000, 10000]` | Assigned altitude range (ft) |
| `speed_range` | `[200, 280]` | Assigned speed range (kts) |
| `heading_change_max` | `60` | Max heading change per instruction (°) |
| `altitude_tolerance_ft` | `200` | Compliance tolerance for altitude |
| `speed_tolerance_kts` | `10` | Compliance tolerance for speed |
| `heading_tolerance_deg` | `5` | Compliance tolerance for heading |
| `compliance_timeout_sec` | `120` | Timeout waiting for compliance |
| `max_readback_attempts` | `3` | Readback attempts before proceeding |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `SimConnect.dll` not found | Use 32-bit Python, or run with `--mock` |
| `pyaudio` install fails | Run: `pip install pipwin && pipwin install pyaudio` |
| No speech detected | Check microphone permissions in Windows Settings |
| Internet required? | Only for Google speech recognition. Vosk (offline) can be added |

---

## Contributors

- **[DilshanTRX](https://github.com/DilshanTRX)** - Creator & Maintainer
