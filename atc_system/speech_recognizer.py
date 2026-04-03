"""
speech_recognizer.py
Listens to pilot readback via microphone and returns a transcription string.
Uses Google Web Speech API by default (free, requires internet).
"""

import time
from colorama import Fore, Style


class SpeechRecognizer:
    def __init__(self, timeout_sec: int = 15):
        self._timeout = timeout_sec
        self._recognizer = None
        self._microphone = None
        self._init()

    def _init(self) -> None:
        try:
            import speech_recognition as sr  # type: ignore
            self._sr = sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 1.0   # seconds of silence before phrase ends
            print(Fore.GREEN + "[MIC] Speech recognizer ready." + Style.RESET_ALL)
        except ImportError:
            print(Fore.YELLOW + "[MIC] SpeechRecognition not installed. Manual text input mode." + Style.RESET_ALL)
            self._recognizer = None

    def listen(self) -> str | None:
        """
        Listen for pilot speech until pause or timeout.
        Returns transcription string, or None on failure.
        """
        if self._recognizer is None:
            # Fallback: keyboard input
            print(Fore.YELLOW + "[MIC] Type your readback and press Enter:" + Style.RESET_ALL, end=" ")
            try:
                return input().strip()
            except (EOFError, KeyboardInterrupt):
                return None

        sr = self._sr
        print(Fore.CYAN + f"\n[MIC] Listening... (timeout: {self._timeout}s)" + Style.RESET_ALL)

        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = self._recognizer.listen(
                        source,
                        timeout=self._timeout,
                        phrase_time_limit=20,
                    )
                except sr.WaitTimeoutError:
                    print(Fore.YELLOW + "[MIC] No speech detected within timeout." + Style.RESET_ALL)
                    return None

            print(Fore.CYAN + "[MIC] Recognizing..." + Style.RESET_ALL)
            text = self._recognizer.recognize_google(audio)
            print(Fore.WHITE + f"[PILOT] '{text}'" + Style.RESET_ALL)
            return text

        except sr.UnknownValueError:
            print(Fore.YELLOW + "[MIC] Could not understand audio. Please try again." + Style.RESET_ALL)
            return None
        except sr.RequestError as exc:
            print(Fore.RED + f"[MIC] Speech API error: {exc}" + Style.RESET_ALL)
            return None
        except OSError as exc:
            print(
                Fore.RED
                + f"[MIC] Microphone error: {exc}\n"
                + "      Ensure a microphone is connected. Falling back to text input."
                + Style.RESET_ALL
            )
            # Fallback to keyboard
            print(Fore.YELLOW + "Type your readback and press Enter:" + Style.RESET_ALL, end=" ")
            try:
                return input().strip()
            except (EOFError, KeyboardInterrupt):
                return None
