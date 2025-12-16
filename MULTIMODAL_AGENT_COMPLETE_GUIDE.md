# Multimodal Agent - Complete Guide

A comprehensive guide to the multimodal agent with image, audio, and speech capabilities.

---

## Table of Contents

1. [Overview](#overview)
2. [Current State & Analysis](#current-state--analysis)
3. [What Was Implemented](#what-was-implemented)
4. [Setup Options](#setup-options)
5. [Installation Instructions](#installation-instructions)
6. [Usage Examples](#usage-examples)
7. [How It Works](#how-it-works)
8. [Provider Comparison](#provider-comparison)
9. [Troubleshooting](#troubleshooting)
10. [Technical Details](#technical-details)

---

## Overview

The multimodal agent is a fully functional personal assistant with:

- ✅ **Text**: Normal Q&A, explanations, summaries
- ✅ **Image Analysis**: Analyze uploaded images using Gemini vision
- ✅ **Image Generation**: Generate images using DALL-E or Google Imagen
- ✅ **Speech-to-Text**: Transcribe audio files using Whisper or Google STT
- ✅ **Text-to-Speech**: Generate speech audio using OpenAI TTS or Google TTS
- ✅ **Diagrams**: Generate Mermaid flowcharts and diagrams

### Key Features

- **Real implementations** (no placeholders!)
- **Auto-selection**: Prioritizes Google services, falls back to OpenAI
- **Multimodal input**: Text + image together
- **Interactive uploads**: Image and audio file support
- **Modular design**: Easy to extend and customize

---

## Current State & Analysis

### ✅ What's Working Well

1. **Basic Structure**
   - Clean class-based design with `MultimodalAgent`
   - Proper model fallback logic
   - Good error handling for model initialization
   - Conversation history management

2. **Function Calling Framework**
   - Correct implementation of function calling pattern
   - Proper handling of function calls and responses
   - Default parameter handling for tools

3. **Tool Definitions**
   - Well-structured tool schemas
   - Clear parameter definitions
   - Good separation between tool definitions and implementations

### 📁 File Structure

```
agents_adk/
├── multimodal_tools/
│   ├── __init__.py
│   ├── image/
│   │   ├── __init__.py
│   │   ├── analysis.py      # Gemini vision
│   │   └── generation.py    # DALL-E / Imagen
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── speech_to_text.py  # Whisper / Google STT
│   │   └── text_to_speech.py  # OpenAI TTS / Google TTS
│   └── figures/
│       ├── __init__.py
│       └── generator.py     # Mermaid diagrams
├── examples/
│   └── multimodal_agent.py  # Main agent
├── generated_images/         # Auto-created for image outputs
└── generated_audio/          # Auto-created for audio outputs
```

---

## What Was Implemented

### 1. Real Image Analysis (Gemini Vision)
- ✅ Uses Gemini's native vision capabilities
- ✅ No additional API keys needed (uses GEMINI_API_KEY)
- ✅ Can analyze uploaded images
- ✅ Supports questions about images
- ✅ OCR (text extraction from images)

### 2. Real Image Generation (Google Imagen / DALL-E)
- ✅ Generates actual images using **Google Imagen** (prioritized) or DALL-E
- ✅ Auto-selects Google Imagen first (for consistency with Google ADK)
- ✅ Falls back to DALL-E if Google not available
- ✅ Saves images to `generated_images/` directory
- ✅ Supports multiple styles (realistic, sketch, 3d, anime, etc.)

### 3. Real Speech-to-Text (Google STT / Whisper)
- ✅ Transcribes audio using **Google Speech-to-Text** (prioritized) or Whisper
- ✅ Auto-selects Google STT first (for consistency with Google ADK)
- ✅ Falls back to Whisper if Google not available
- ✅ Supports multiple languages
- ✅ High accuracy transcription

### 4. Real Text-to-Speech (Google TTS / OpenAI TTS)
- ✅ Generates speech audio using **Google TTS** (prioritized) or OpenAI TTS
- ✅ Auto-selects Google TTS first (for consistency with Google ADK)
- ✅ Falls back to OpenAI TTS if Google not available
- ✅ Multiple voice options
- ✅ Saves audio to `generated_audio/` directory

### 5. Enhanced Figure Generation
- ✅ Multiple diagram types (flowchart, sequence, class)
- ✅ Mermaid format support
- ✅ ASCII art option

### 6. Interactive Features
- ✅ Image upload support (`image: <path>`)
- ✅ Audio upload support (`audio: <path>`)
- ✅ Multimodal input (text + image together)

---

## Setup Options

### Why Google vs OpenAI?

Since we're using **Google ADK** and **Gemini**, it makes sense to use **Google's services** for consistency:

✅ **Unified ecosystem** - All services from Google  
✅ **Better integration** - Works seamlessly with Google ADK  
✅ **Single authentication** - Same credentials for all services  
✅ **Cost efficiency** - May be more cost-effective if using Google Cloud  
✅ **Consistency** - All services follow Google's patterns

However, **OpenAI setup is much easier** (just API key), so the code supports both!

### Auto-Selection Priority

The code **prioritizes Google services** when available:

```python
# Auto-selection logic:
if GOOGLE_APPLICATION_CREDENTIALS exists:
    use_google_services()  # ✅ Prioritized
elif OPENAI_API_KEY exists:
    use_openai_services()  # ⬇️ Fallback
else:
    show_setup_instructions()
```

**Priority Order:**
1. **Image Generation**: Google Imagen → DALL-E
2. **Speech-to-Text**: Google STT → Whisper
3. **Text-to-Speech**: Google TTS → OpenAI TTS

---

## Installation Instructions

### Option 1: OpenAI Setup (Easiest - Recommended for Quick Start)

This is the **easiest way** to get multimodal capabilities working. No Google Cloud setup needed!

#### Step 1: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Go to [API Keys](https://platform.openai.com/api-keys)
4. Click **Create new secret key**
5. Copy the key (you won't see it again!)

#### Step 2: Install Dependencies

```bash
# Make sure you're in the project directory
cd /Users/linjia/cursor_ai_space/interview_preparation/ai_ml_interviews/machine_learning/agents_adk

# Install required libraries
pip install Pillow openai
```

#### Step 3: Set API Keys

Add to your `.env` file (in the `agents_adk` directory):

```bash
# Required for Gemini (image analysis)
GEMINI_API_KEY=your_gemini_key_here

# Required for OpenAI services (image generation, audio)
OPENAI_API_KEY=your_openai_key_here
```

#### Step 4: Run the Agent

```bash
python examples/multimodal_agent.py
```

**That's it!** 🎉

**What Works:**
- ✅ Image Analysis: Gemini vision (uses GEMINI_API_KEY)
- ✅ Image Generation: DALL-E 3 (uses OPENAI_API_KEY)
- ✅ Speech-to-Text: Whisper (uses OPENAI_API_KEY)
- ✅ Text-to-Speech: OpenAI TTS (uses OPENAI_API_KEY)
- ✅ Diagrams: Mermaid diagrams (no API needed)

---

### Option 2: Google Services Setup (Recommended for Google ADK)

Since we're using Google ADK, using Google services provides better integration and consistency.

#### Quick Start: Service Account Method (No gcloud Needed!)

**You don't need to install `gcloud`!** Use a service account JSON file instead.

##### Step 1: Create Service Account (Web Console)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Go to **IAM & Admin** → **Service Accounts**
4. Click **Create Service Account**
5. Name it (e.g., "multimodal-agent")
6. Click **Create and Continue**
7. Grant these roles:
   - **Vertex AI User** (for Imagen)
   - **Cloud Speech Client** (for Speech-to-Text)
   - **Cloud Text-to-Speech API User** (for TTS)
8. Click **Done**
9. Click on the service account → **Keys** tab
10. Click **Add Key** → **Create new key** → **JSON**
11. Download the JSON file (save it somewhere safe!)

##### Step 2: Enable APIs (Web Console)

Enable these APIs via [API Library](https://console.cloud.google.com/apis/library):
- [Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com) (for Imagen)
- [Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com)
- [Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)

##### Step 3: Install Python Libraries

```bash
pip install google-cloud-aiplatform google-cloud-speech google-cloud-texttospeech
```

##### Step 4: Set Environment Variables

Add to your `.env` file:

```bash
# Required
GEMINI_API_KEY=your_gemini_key_here

# Google Cloud (using service account - no gcloud needed!)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/downloaded/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # Optional, defaults to us-central1
```

**That's it!** No `gcloud` installation needed. 🎉

---

#### Alternative: Using gcloud (If You Want CLI Tools)

If you prefer using `gcloud` command-line tools:

##### 1. Install Google Cloud SDK

**macOS (Homebrew)**:
```bash
brew install google-cloud-sdk
```

**Or download from**: https://cloud.google.com/sdk/docs/install

##### 2. Authenticate

```bash
gcloud auth login
gcloud auth application-default login
```

##### 3. Create/Select Project

```bash
# List projects
gcloud projects list

# Create new project (optional)
gcloud projects create your-project-id

# Set current project
gcloud config set project your-project-id
```

##### 4. Enable APIs

```bash
# Enable Vertex AI API (for Imagen)
gcloud services enable aiplatform.googleapis.com

# Enable Speech-to-Text API
gcloud services enable speech.googleapis.com

# Enable Text-to-Speech API
gcloud services enable texttospeech.googleapis.com
```

##### 5. Set Environment Variables

If using `gcloud auth`, you only need:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_APPLICATION_CREDENTIALS not needed if using gcloud auth
```

---

### Option 3: Mixed Setup (Hybrid)

Set up both Google and OpenAI:

```bash
# In .env file
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
OPENAI_API_KEY=your_openai_key_here
```

**Result**: Uses Google services first, falls back to OpenAI if Google fails.

---

## Usage Examples

### Text Queries (Normal)
```
You: What is machine learning?
Agent: [Explains machine learning...]
```

### Image Analysis
```
You: image: photo.jpg
Question about image: What objects are in this image?
Agent: [Analyzes image using Gemini vision...]
```

### Image Generation
```
You: Generate an image of a sunset over mountains
Agent: ✅ Image generated successfully!
- Prompt: a sunset over mountains
- Style: realistic
- Saved to: generated_images/dalle_abc123.png
- URL: https://...
```

### Audio Transcription
```
You: audio: recording.mp3
Agent: 📝 Audio Transcript: [transcription text]
What would you like to do with this transcript?
You: Summarize the key points
Agent: [Summarizes transcript...]
```

### Text-to-Speech
```
You: Convert this text to speech: "Hello, how are you?"
Agent: ✅ Audio generated successfully!
- Text: Hello, how are you?
- Voice: alloy
- Saved to: generated_audio/tts_abc123_alloy.mp3
```

### Diagram Generation
```
You: Create a flowchart for user login process
Agent: [Generates Mermaid diagram...]
```

### Multimodal Input (Text + Image)
The agent automatically handles this when you use `image: <path>` command.

---

## How It Works

### Image Analysis Flow
1. User provides image path
2. Agent loads image using PIL
3. Sends image + question to Gemini vision model
4. Gemini analyzes and returns description
5. Agent presents results

### Image Generation Flow
1. User requests image generation
2. Agent calls `generate_image()` tool
3. Tool auto-selects provider (Imagen or DALL-E)
4. API generates image
5. Image downloaded and saved to `generated_images/`
6. Agent returns file path and URL

### Audio Processing Flow
1. User provides audio file path
2. Agent calls `speech_to_text()` tool
3. Tool auto-selects provider (Google STT or Whisper)
4. API transcribes audio
5. Agent returns transcript

### Text-to-Speech Flow
1. User requests text-to-speech
2. Agent calls `text_to_speech()` tool
3. Tool auto-selects provider (Google TTS or OpenAI TTS)
4. API generates audio
5. Audio saved to `generated_audio/`
6. Agent returns file path

---

## Provider Comparison

### Google vs OpenAI

| Feature | Google | OpenAI |
|---------|--------|--------|
| **Setup Time** | ~15-30 min | ~2 min |
| **Requirements** | Google Cloud account, billing, APIs | Just API key |
| **Authentication** | gcloud auth or service account | API key only |
| **Image Generation** | Imagen 3.0 (high quality) | DALL-E 3 (high quality) |
| **Speech-to-Text** | 120+ languages, very accurate | Whisper (99 languages, very accurate) |
| **Text-to-Speech** | 100+ voices, many languages | 6 voices, English-focused |
| **Cost** | Pay-per-use, free tier available | Pay-per-use, pricing varies |

### When to Use Each

**Use Google Services If:**
- ✅ You're already using Google Cloud
- ✅ You want unified ecosystem
- ✅ You need many languages/voices
- ✅ You want better integration with Google ADK

**Use OpenAI Services If:**
- ✅ You want quickest setup
- ✅ You don't have Google Cloud account
- ✅ You prefer simpler authentication
- ✅ You're just experimenting

---

## Troubleshooting

### "OPENAI_API_KEY not set"
- Make sure you added it to `.env` file
- Restart your terminal/IDE after adding to `.env`

### "GOOGLE_APPLICATION_CREDENTIALS not set"
- If using service account: Set path to JSON file in `.env`
- If using gcloud: Run `gcloud auth application-default login`

### "Module 'openai' not found"
```bash
pip install openai
```

### "PIL/Pillow not found"
```bash
pip install Pillow
```

### "Could not import multimodal tools"
- Make sure you're in the correct directory
- Check that `multimodal_tools/` directory exists

### "Image file not found"
- Check file path is correct
- Use absolute path if relative path doesn't work

### "Image generation fails"
- Check your API account has credits
- Verify API key is correct
- Check service status (OpenAI: https://status.openai.com/)

### "gcloud is not found"
- You don't need gcloud! Use service account method instead (see Option 2 above)
- Or install: `brew install google-cloud-sdk` (macOS)

### Google Cloud Setup Issues

**"Vertex AI API not enabled"**
- Enable via web console: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
- Or via gcloud: `gcloud services enable aiplatform.googleapis.com`

**"Insufficient permissions"**
- Make sure service account has correct roles:
  - Vertex AI User
  - Cloud Speech Client
  - Cloud Text-to-Speech API User

**"Project billing not enabled"**
- Enable billing: https://console.cloud.google.com/billing

---

## Technical Details

### Tool Functions

#### `analyze_image(image_path, question=None)`
- Analyzes images using Gemini vision
- Returns detailed description or answers questions
- **API**: Gemini (uses GEMINI_API_KEY)

#### `generate_image(prompt, style="realistic", provider="auto")`
- Generates images using DALL-E or Imagen
- Auto-selects provider based on available credentials
- Returns file path and URL
- **APIs**: Google Imagen (prioritized) or DALL-E

#### `speech_to_text(audio_path, provider="auto", language=None)`
- Transcribes audio using Whisper or Google STT
- Auto-selects provider based on available credentials
- Returns text transcript
- **APIs**: Google Speech-to-Text (prioritized) or Whisper

#### `text_to_speech(text, voice="default", provider="auto")`
- Generates speech audio
- Auto-selects provider based on available credentials
- Returns file path
- **APIs**: Google TTS (prioritized) or OpenAI TTS

#### `generate_figure(description, format="mermaid", diagram_type="flowchart")`
- Generates diagrams
- Returns Mermaid code or ASCII art
- **No API needed**

### Performance Notes

- **Image Analysis**: Fast (Gemini vision is efficient)
- **Image Generation**: ~10-20 seconds (DALL-E/Imagen API)
- **Speech-to-Text**: Depends on audio length (~1-2x audio duration)
- **Text-to-Speech**: Fast (~1-2 seconds)

### Cost Notes

**OpenAI pricing (as of 2024):**
- **DALL-E 3**: ~$0.04 per image
- **Whisper**: ~$0.006 per minute
- **TTS**: ~$0.015 per 1000 characters

**Google pricing:**
- Pay-per-use, free tier available
- Check current pricing: https://cloud.google.com/pricing

**Note**: You get some free credits when you sign up for OpenAI!

### Security & Privacy

- Generated images/audio saved locally
- API keys stored in `.env` (not committed)
- No data sent to unauthorized services
- User controls what files are processed

### Fallback Behavior

The agent gracefully handles missing dependencies:

- **If multimodal_tools not available**: Falls back to placeholder implementations
- **If OPENAI_API_KEY not set**: Image generation and audio features show helpful error messages
- **If GOOGLE_APPLICATION_CREDENTIALS not set**: Falls back to OpenAI services
- **If Pillow not installed**: Image analysis shows installation instructions

---

## Summary

The multimodal agent is now **fully functional** with:

- ✅ Real image analysis (Gemini vision)
- ✅ Real image generation (DALL-E / Imagen)
- ✅ Real audio processing (Whisper / Google STT + TTS)
- ✅ Enhanced diagram generation
- ✅ Interactive upload support
- ✅ Multimodal input handling
- ✅ Auto-selection of best provider
- ✅ Graceful fallbacks

**Quick Start**: Just set `OPENAI_API_KEY` in `.env` and you're ready to go! 🚀

**For Google ADK consistency**: Set up Google Cloud services for unified ecosystem.

---

**Last Updated**: December 2025  
**Status**: ✅ Complete and Ready to Use

