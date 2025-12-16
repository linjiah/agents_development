#!/bin/bash

# Setup script for Google ADK Agent Development

echo "🤖 Setting up Google ADK Agent Development Environment"
echo "=================================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "   Consider activating: source ml_interview_env/bin/activate"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Google Gemini API Key
# Get your API key from: https://aistudio.google.com/
GEMINI_API_KEY=your_api_key_here

# Optional: Model configuration
GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: Project settings
PROJECT_NAME=interview_prep_agent
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env file. Please edit it and add your GEMINI_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p agents examples tools

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY from https://aistudio.google.com/"
echo "2. Try running: python examples/simple_agent.py"
echo "3. Or use ADK CLI: adk create --type=config my_agent"

