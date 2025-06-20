#!/bin/bash

# STPA Tool Launch Script
# This script launches the STPA Tool GUI application

echo "🚀 Launching STPA Tool..."

# Navigate to the project directory
cd "/media/netrisk/Maxwell/STPA Tool"

# Activate the virtual environment
echo "📦 Activating virtual environment..."
source stpa_tool_env/bin/activate

# Check if activation was successful
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Launch the application
echo "🖥️  Starting STPA Tool GUI..."
python main.py

echo "👋 STPA Tool closed"