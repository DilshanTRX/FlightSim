# ATC Training System Dependencies
# ---------------------------------
# Run this script FIRST to install everything:
#   python setup.py
# Or install manually:
#   pip install -r requirements.txt

import subprocess
import sys
import struct
import platform

def main():
    bits = struct.calcsize("P") * 8
    print(f"Python: {sys.version}")
    print(f"Architecture: {bits}-bit")
    print(f"Platform: {platform.platform()}")

    if bits != 32:
        print(
            "\n[WARNING] FSX uses a 32-bit SimConnect.dll.\n"
            "  For best results, use a 32-bit Python interpreter.\n"
            "  Download: https://www.python.org/downloads/windows/ → 'Windows x86 executable installer'\n"
            "  If you continue with 64-bit Python, use '--mock' mode to test voice/TTS features,\n"
            "  or if SimConnect still works on your system, it will connect fine.\n"
        )
        answer = input("Continue installation anyway? [y/N]: ").strip().lower()
        if answer != "y":
            print("Installation cancelled.")
            return

    print("\nInstalling dependencies from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        check=False,
    )
    if result.returncode != 0:
        print("\n[ERROR] Some packages failed to install.")
        print("  Common issue: 'pyaudio' requires build tools on Windows.")
        print("  Fix: pip install pipwin && pipwin install pyaudio")
    else:
        print("\n[OK] All dependencies installed successfully.")
        print("\nTo start training:")
        print("  python main.py          # Connect to FSX")
        print("  python main.py --mock   # Test without FSX")
        print("\nTo run tests:")
        print("  python -m pytest tests/ -v")

if __name__ == "__main__":
    main()
