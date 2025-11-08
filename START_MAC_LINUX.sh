#!/bin/bash

echo "========================================"
echo " Wallet Tracker - Starting..."
echo "========================================"
echo ""

# Activate virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3.11 -m venv venv"
    echo "Then run: source venv/bin/activate"
    echo "Then run: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "Starting Flask server..."
echo ""

# Run the application
python run_local.py

