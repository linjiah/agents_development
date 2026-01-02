# API Keys Setup Guide

This agent requires **two API keys** to work:

1. **Google Gemini API Key** - For the LLM (language model)
2. **OpenWeatherMap API Key** - For weather data

## Quick Setup

### Option 1: Using Environment Variables (Recommended)

Export the keys in your terminal before running:

```bash
export GOOGLE_GEMINI_API_KEY="your-gemini-api-key-here"
export OPENWEATHERMAP_API_KEY="your-openweathermap-api-key-here"
```

Then run the agent:
```bash
python mcp_client.py
```

### Option 2: Using a `.env` File

1. Create a `.env` file in the `agent_with_mcp` directory:

```bash
cd agents/agent_with_mcp
cat > .env << EOF
GOOGLE_GEMINI_API_KEY=your-gemini-api-key-here
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key-here
EOF
```

2. Install `python-dotenv` to load the `.env` file:
```bash
pip install python-dotenv
```

3. Update the code to load from `.env` (see below)

---

## Getting the API Keys

### 1. Google Gemini API Key

**Steps:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

**Note:** The free tier is generous for testing. You'll need to enable billing for higher usage.

**Environment Variable Name:** `GOOGLE_GEMINI_API_KEY`

---

### 2. OpenWeatherMap API Key

**Steps:**
1. Go to https://openweathermap.org/api
2. Click "Sign Up" (top right)
3. Create a free account
4. After signing up, go to https://home.openweathermap.org/api_keys
5. Click "Generate" to create a new API key
6. Copy the key (it may take a few minutes to activate)

**Note:** Free tier includes:
- 60 calls/minute
- 1,000,000 calls/month
- Current weather data
- 5-day/3-hour forecast

**Environment Variable Name:** `OPENWEATHERMAP_API_KEY`

---

## Verifying Your Keys

### Test Google Gemini Key

```bash
export GOOGLE_GEMINI_API_KEY="your-key"
python -c "import google.generativeai as genai; genai.configure(api_key='$GOOGLE_GEMINI_API_KEY'); print('✅ Gemini key works!')"
```

### Test OpenWeatherMap Key

```bash
export OPENWEATHERMAP_API_KEY="your-key"
curl "http://api.openweathermap.org/data/2.5/weather?q=London&appid=$OPENWEATHERMAP_API_KEY"
```

If you see JSON weather data, your key works! ✅

---

## Using .env File (Optional)

If you want to use a `.env` file instead of exporting variables:

1. **Install python-dotenv:**
```bash
pip install python-dotenv
```

2. **Create `.env` file:**
```bash
GOOGLE_GEMINI_API_KEY=your-actual-key-here
OPENWEATHERMAP_API_KEY=your-actual-key-here
```

3. **Update `mcp_client.py`** to load from `.env`:
```python
from dotenv import load_dotenv
load_dotenv()  # Add this at the top, after imports
```

4. **Update `weather_server.py`** similarly:
```python
from dotenv import load_dotenv
load_dotenv()  # Add this at the top, after imports
```

---

## Security Notes

⚠️ **Important:**
- **Never commit API keys to git!**
- Add `.env` to your `.gitignore` file
- Don't share your keys publicly
- Rotate keys if they're accidentally exposed

**Example `.gitignore`:**
```
.env
*.env
.env.local
```

---

## Troubleshooting

### Error: "GOOGLE_GEMINI_API_KEY environment variable is not set"
- Make sure you exported the variable: `export GOOGLE_GEMINI_API_KEY="your-key"`
- Or create a `.env` file and load it with `python-dotenv`

### Error: "OpenWeatherMap API key is not configured"
- The weather server runs as a separate process, so it needs the environment variable too
- Make sure `OPENWEATHERMAP_API_KEY` is exported before running `mcp_client.py`
- The MCP server inherits environment variables from the parent process

### Error: "Authentication failed" (OpenWeatherMap)
- Your API key might not be activated yet (wait 5-10 minutes after creation)
- Check that you copied the key correctly
- Verify at https://home.openweathermap.org/api_keys

### Error: "Invalid API key" (Gemini)
- Make sure you're using the correct key from https://aistudio.google.com/app/apikey
- Check that billing is enabled if you've exceeded free tier

---

## Quick Test

Once both keys are set, test the agent:

```bash
# Set keys
export GOOGLE_GEMINI_API_KEY="your-key"
export OPENWEATHERMAP_API_KEY="your-key"

# Run agent
python mcp_client.py

# Try asking:
# "What's the weather in San Francisco?"
```

If everything works, you should see the agent respond with weather information! 🌤️

