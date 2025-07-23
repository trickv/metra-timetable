#!/bin/bash

# Metra Timetable Bootstrap Script
# Creates virtual environment and installs required packages

set -e  # Exit on any error

echo "🚂 Metra Timetable Bootstrap Script"
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✅ Found Python $PYTHON_VERSION"

# Check if virtual environment already exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists at ./venv"
    read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf venv
    else
        echo "ℹ️  Using existing virtual environment"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📋 Installing packages from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Packages installed successfully"
else
    echo "⚠️  requirements.txt not found, installing basic packages..."
    pip install pandas jinja2
    echo "✅ Basic packages installed"
fi

echo ""
echo "🎉 Bootstrap complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To get started:"
echo "  1. ./get-schedule.sh          # Download GTFS data"
echo "  2. python render-all-lines.py # Generate schedule data"
echo "  3. python -m http.server 8000 # Start web server"
echo "  4. Open http://localhost:8000/metra-interactive.html"
echo ""
echo "Happy commuting! 🚂"