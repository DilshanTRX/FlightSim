"""
tts_engine.py
Text-to-speech engine wrapping pyttsx3 for offline ATC voice output.
"""

import sys
from colorama import Fore, Style


class TTSEngine:
    def __init__(self, rate: int = 150, voice_preference: str = "auto"):
        self._engine = None
        self._rate = rate
        self._voice_preference = voice_preference
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3  # type: ignore
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)

            # Try to select a suitable voice
            voices = self._engine.getProperty("voices")
            if voices:
                selected = voices[0]  # default
                if self._voice_preference == "auto":
                    # Prefer a male voice for ATC realism
                    for v in voices:
                        if "male" in v.name.lower() or "david" in v.name.lower():
                            selected = v
                            break
                self._engine.setProperty("voice", selected.id)
                print(Fore.GREEN + f"[TTS] Voice: {selected.name}" + Style.RESET_ALL)

        except ImportError:
            print(Fore.YELLOW + "[TTS] pyttsx3 not installed. Output will be text-only." + Style.RESET_ALL)
            self._engine = None
        except Exception as exc:
            print(Fore.YELLOW + f"[TTS] Init failed ({exc}). Text-only mode." + Style.RESET_ALL)
            self._engine = None

    def speak(self, text: str) -> None:
        """Speak text aloud (blocking). Falls back to console print on failure."""
        if self._engine:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                return
            except Exception as exc:
                print(Fore.YELLOW + f"[TTS] Speak error: {exc}" + Style.RESET_ALL)
        # Fallback: print for manual reading
        print(Fore.CYAN + f"\n[ATC INSTRUCTION] {text}\n" + Style.RESET_ALL)
