# Camera Features

## 📷 Camera Functionality

The agent now supports **full camera integration** with live preview, photo capture, and video recording!

## Features

### ✅ Live Camera Feed
- Real-time camera preview in the UI
- Front-facing camera (MacBook/iPad camera)
- High-quality video stream (1280x720 ideal)
- Automatic camera access request

### ✅ Photo Capture
- Take instant photos from camera feed
- Automatic upload to server
- Preview captured photos
- Send photos directly to agent for analysis
- High-quality JPEG format

### ✅ Video Recording
- Record videos from camera
- WebM format (VP9/VP8 codecs)
- Automatic download when recording stops
- Video preview in UI
- Compatible with all modern browsers

## How to Use

### Starting the Camera

1. **Click "📷 Start Camera"** button
2. **Allow camera access** when prompted by your browser
3. Camera feed will appear in the UI
4. You'll see live video from your camera

### Taking Photos

1. **Start the camera** (see above)
2. **Click "📸 Take Photo"** button
3. Photo is automatically:
   - Captured from camera feed
   - Uploaded to server
   - Displayed in preview
4. **Options**:
   - **"Send to Agent"**: Send photo to agent for analysis
   - **"Clear"**: Remove preview

### Recording Videos

1. **Start the camera** (see above)
2. **Click "🎥 Start Recording"** button
3. **Speak or show what you want to record**
4. **Click "⏹️ Stop Recording"** when done
5. Video is automatically:
   - Saved as WebM file
   - Downloaded to your computer
   - Displayed in preview

### Stopping the Camera

- Click **"⏹️ Stop Camera"** button
- Camera feed stops
- All resources are released

## Browser Requirements

### Supported Browsers
- **Chrome/Edge**: Full support ✅
- **Firefox**: Full support ✅
- **Safari**: Full support ✅ (iOS 11+)
- **Opera**: Full support ✅

### Requirements
- **HTTPS or localhost**: Required for camera access
- **Modern browser**: WebRTC support needed
- **Camera permissions**: Must allow camera access

## Privacy & Security

### Camera Access
- Camera only activates when you click "Start Camera"
- Camera feed is **not** recorded or stored automatically
- Photos/videos are only saved when you explicitly capture them
- You control when to start/stop camera

### Data Handling
- **Photos**: Uploaded to server, can be sent to agent
- **Videos**: Saved locally, not uploaded automatically
- **Camera feed**: Only displayed in browser, not transmitted

## Technical Details

### Camera API
- Uses **MediaDevices.getUserMedia()** API
- Requests front-facing camera (`facingMode: 'user'`)
- Ideal resolution: 1280x720
- No audio in camera feed (video only)

### Photo Capture
- Uses **Canvas API** to capture video frame
- Converts to JPEG (95% quality)
- Uploads via FormData to `/api/upload/image`
- Can be sent to agent for analysis

### Video Recording
- Uses **MediaRecorder API**
- Codec priority: VP9 → VP8 → WebM → MP4
- Automatically selects best supported codec
- Records in WebM format
- Downloads as `.webm` file

## Use Cases

### 1. Visual Analysis
- Take photo of object/document
- Send to agent for analysis
- Get detailed description or answer questions

### 2. Document Scanning
- Capture documents
- Send to agent for text extraction
- Get summaries or answers

### 3. Live Demonstrations
- Show agent what you're working on
- Get real-time assistance
- Record tutorials or explanations

### 4. Visual Q&A
- Point camera at something
- Ask agent questions about it
- Get instant visual analysis

## Troubleshooting

### "Camera access denied"

**Solution**:
1. Check browser permissions
2. Click lock icon in address bar
3. Allow camera access
4. Refresh page and try again

### "Camera not found"

**Possible causes**:
- No camera connected
- Camera in use by another app
- Browser doesn't support camera API

**Solution**:
- Check if camera works in other apps
- Close other apps using camera
- Try different browser

### "Photo upload failed"

**Check**:
- Internet connection
- Server is running
- File size limits

**Solution**:
- Check network connection
- Verify server is running on port 8000
- Try smaller photo resolution

### "Video recording not working"

**Possible causes**:
- Codec not supported
- Browser limitations
- Insufficient permissions

**Solution**:
- Try different browser
- Check browser console for errors
- Ensure camera permissions are granted

## Tips

1. **Good lighting**: Better lighting = better photos/videos
2. **Stable camera**: Hold device steady for clear captures
3. **High resolution**: Camera uses 1280x720 for best quality
4. **Privacy**: Always stop camera when not in use
5. **Storage**: Videos are saved locally, manage disk space

## Integration with Agent

### Sending Photos to Agent

When you capture a photo:
1. Photo is uploaded to server
2. Click "Send to Agent" button
3. Agent receives photo with message "Please analyze this image"
4. Agent uses Gemini Vision to analyze
5. You get detailed response about the image

### Example Workflow

```
1. Start Camera
2. Take Photo of document
3. Click "Send to Agent"
4. Agent: "I can see a document with text about..."
5. Ask follow-up questions
6. Agent provides detailed analysis
```

---

**Your agent now has full camera capabilities!** 📷🎥

