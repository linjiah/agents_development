# Super Personal Agent

A modern web application for your personal AI assistant, built with FastAPI backend and vanilla JavaScript frontend. This is your personal multimodal agent with chat, image, and audio capabilities.

## Features

- 💬 **Chat Interface**: Interactive chat with the multimodal agent
- 🖼️ **Image Analysis**: Upload and analyze images
- 🎨 **Image Generation**: Generate images using DALL-E or Imagen
- 🎤 **Audio Transcription**: Upload audio files and get text transcripts
- 🔊 **Text-to-Speech**: Convert text to speech audio
- 📱 **Responsive Design**: Works on desktop and mobile

## Architecture

```
super_personal_agent/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   └── index.html           # Web UI (HTML/CSS/JS)
└── uploads/                 # Auto-created for uploaded files
    ├── images/
    └── audio/
```

## Setup

### 1. Install Backend Dependencies

```bash
cd super_personal_agent/backend
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
cd super_personal_agent/backend
python main.py
```

Or using uvicorn directly:

```bash
cd super_personal_agent/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 3. Open the Frontend

Simply open `super_personal_agent/frontend/index.html` in your browser, or serve it with a simple HTTP server:

```bash
# Python 3
cd super_personal_agent/frontend
python -m http.server 8080

# Then open: http://localhost:8080
```

Or use any web server you prefer.

## API Endpoints

### Chat
- `POST /api/chat` - Send text message (with optional image)
- `POST /api/upload/image` - Upload image file
- `POST /api/upload/audio` - Upload audio file

### Image Generation
- `POST /api/generate-image` - Generate image from prompt

### Audio Processing
- `POST /api/transcribe-audio` - Transcribe audio to text
- `POST /api/text-to-speech` - Convert text to speech

### File Serving
- `GET /api/files/{path}` - Serve generated files
- `GET /api/files/uploads/{path}` - Serve uploaded files

### Health Check
- `GET /api/health` - Check API and agent status

## Usage

1. **Start the backend**: `python super_personal_agent/backend/main.py`
2. **Open the frontend**: Open `super_personal_agent/frontend/index.html` in your browser
3. **Start chatting**: Type messages and interact with your personal agent!

## Configuration

Make sure your `.env` file is set up in the project root with:
- `GEMINI_API_KEY` - For image analysis
- `OPENAI_API_KEY` - For image generation and audio (optional)

## Development

### Backend Development

The FastAPI backend includes:
- Automatic API documentation at `http://localhost:8000/docs`
- CORS enabled for frontend connections
- File upload handling
- Error handling and validation

### Frontend Development

The frontend is a single-page application with:
- Modern, responsive design
- Real-time chat interface
- File upload support
- Image and audio display

## Future Enhancements

- [ ] WebSocket support for real-time streaming
- [ ] User authentication
- [ ] Conversation history persistence
- [ ] Multiple agent selection
- [ ] Advanced image editing
- [ ] Video support

## Troubleshooting

### Backend won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify `.env` file exists with API keys
- Check port 8000 is not in use

### Frontend can't connect
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify API_BASE URL in `index.html` matches your backend URL

### File upload fails
- Check `super_personal_agent/uploads/` directory exists and is writable
- Verify file size limits (adjust in FastAPI if needed)

---

**Enjoy your super personal agent!** 🎉

