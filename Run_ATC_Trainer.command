#!/bin/bash
clear
echo "Starting ATC Training System..."
echo "Note: If running on Mac without a simulator, use Mock Mode."
echo "-------------------------------------------------------------"

# Traverse to the directory where this script is located
cd "$(dirname "$0")"

# Run the python script in Mock mode (since FSX isn't on Mac)
python3 main.py --mock

echo
echo "-------------------------------------------------------------"
echo "Session ended. You can close this terminal window now."
