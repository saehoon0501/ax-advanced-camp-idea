#!/bin/bash
# Test Project - Development Setup Script
# A simple hello world CLI application

echo "=== Test Project Development Setup ==="
echo "Setting up development environment for CLI hello world application..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install development dependencies (when requirements.txt is created)
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "ℹ No requirements.txt found - will be created during development"
fi

# Make main CLI executable (when created)
if [ -f "main.py" ]; then
    chmod +x main.py
    echo "✓ Made main.py executable"
fi

echo ""
echo "=== Development Environment Ready ==="
echo "Next steps:"
echo "1. Implement feature-001: Create basic CLI application entry point"
echo "2. Implement feature-002: Display 'Hello, World!' message"
echo "3. Run tests as features are implemented"
echo ""
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
echo ""
echo "To run the CLI (once implemented):"
echo "  python3 main.py"
echo "  or ./main.py"