#!/bin/bash
# Quick setup script for API keys

echo "🔑 MCP Agent API Keys Setup"
echo "=========================="
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

echo ""
echo "📝 Please enter your API keys:"
echo ""

# Get Gemini API key
read -p "Google Gemini API Key (get from https://aistudio.google.com/app/apikey): " GEMINI_KEY
if [ -z "$GEMINI_KEY" ]; then
    echo "❌ Gemini API key is required!"
    exit 1
fi

# Get OpenWeatherMap API key
read -p "OpenWeatherMap API Key (get from https://openweathermap.org/api): " WEATHER_KEY
if [ -z "$WEATHER_KEY" ]; then
    echo "❌ OpenWeatherMap API key is required!"
    exit 1
fi

# Create .env file
cat > .env << EOF
# API Keys for MCP Agent
# DO NOT COMMIT THIS FILE TO GIT!

GOOGLE_GEMINI_API_KEY=$GEMINI_KEY
OPENWEATHERMAP_API_KEY=$WEATHER_KEY
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Install python-dotenv: pip install python-dotenv"
echo "2. Update mcp_client.py and weather_server.py to load .env (see SETUP.md)"
echo "3. Or export the variables:"
echo "   export GOOGLE_GEMINI_API_KEY=\"$GEMINI_KEY\""
echo "   export OPENWEATHERMAP_API_KEY=\"$WEATHER_KEY\""
echo ""
echo "🚀 Then run: python mcp_client.py"

