# Voice Input/Output Features

## 🎤 Voice Input (Speech-to-Text)

The agent now supports **voice input** using your microphone!

### How to Use

1. **Click "🎤 Start Voice Input"** button in the chat panel
2. **Allow microphone access** when prompted by your browser
3. **Speak your question** - you'll see "Recording... Speak now!"
4. **Click "⏹️ Stop Recording"** when done
5. The agent will:
   - Transcribe your speech to text
   - Process your question
   - Respond with both text and audio

### Features

- ✅ Real-time microphone recording
- ✅ Automatic transcription using Whisper/Google STT
- ✅ Visual recording indicator
- ✅ Automatic processing after recording stops

### Browser Requirements

- **Chrome/Edge**: Full support ✅
- **Firefox**: Full support ✅
- **Safari**: May require HTTPS (works on localhost)
- **Mobile**: Works on mobile browsers

### Privacy

- Audio is processed on the server
- Not stored permanently (only for transcription)
- You control when to record

---

## 🔊 Voice Output (Text-to-Speech)

The agent can respond with **both text and speech**!

### Auto-Play Audio Responses

1. **Enable "🔊 Auto-play audio responses"** checkbox
2. All agent responses will automatically:
   - Display text
   - Generate speech audio
   - Play automatically

### Manual Audio Playback

- Voice conversations automatically include audio
- Regular text conversations can have audio added
- Click the audio player to replay

### Voice Options

Currently using OpenAI TTS voices:
- **alloy** (default) - Balanced, neutral
- **echo** - Clear, confident
- **fable** - Expressive, warm
- **onyx** - Deep, authoritative
- **nova** - Bright, energetic
- **shimmer** - Soft, gentle

---

## 🎯 Complete Voice Conversation Flow

### Example Usage:

1. **Click "🎤 Start Voice Input"**
2. **Speak**: "What's the weather like today?"
3. **Click "⏹️ Stop Recording"**
4. **Agent will**:
   - Show your transcribed text: "🎤 What's the weather like today?"
   - Process and respond with text
   - Generate and play audio response
   - Show audio player for replay

### What You'll See:

```
You: 🎤 What's the weather like today?

Agent: [Text response about weather]

🔊 Audio Response:
[Audio player with play button]
```

---

## 🔧 Technical Details

### Backend Endpoint

**`POST /api/chat-with-voice`**
- Accepts audio file (WebM format from browser)
- Returns: transcript, response, audio_url
- Automatically generates TTS if requested

### Frontend Implementation

- Uses **Web Audio API** for microphone access
- Uses **MediaRecorder API** for audio recording
- Records in **WebM format** (browser native)
- Sends to backend for processing

### Audio Formats

- **Input**: WebM (from browser microphone)
- **Output**: MP3 (from TTS service)
- **Compatibility**: Works in all modern browsers

---

## 🐛 Troubleshooting

### "Microphone access denied"

**Solution**:
1. Check browser permissions
2. Click the lock icon in address bar
3. Allow microphone access
4. Refresh the page

### "No audio playback"

**Check**:
- Browser audio is not muted
- System volume is up
- Auto-play is enabled (or click play button)

### "Recording doesn't stop"

**Solution**:
- Click "⏹️ Stop Recording" button
- Or refresh the page

### "Transcription failed"

**Possible causes**:
- Audio too short (< 1 second)
- Background noise too loud
- Microphone not working
- API key not set (for OpenAI Whisper)

**Solution**:
- Speak clearly
- Use a quiet environment
- Check microphone in system settings
- Verify API keys in `.env`

---

## 💡 Tips

1. **Speak clearly** - Better audio = better transcription
2. **Use quiet environment** - Reduces background noise
3. **Speak at normal pace** - Not too fast or slow
4. **Check microphone** - Test in system settings first
5. **Enable auto-TTS** - For hands-free conversation

---

## 🎉 Features Summary

✅ **Voice Input**: Speak instead of typing  
✅ **Voice Output**: Listen to responses  
✅ **Auto-Play**: Automatic audio playback  
✅ **Visual Feedback**: Recording indicators  
✅ **Text + Audio**: Both formats available  
✅ **Replay**: Audio players for all responses  

---

**Your agent now supports full voice conversation!** 🎤🔊

