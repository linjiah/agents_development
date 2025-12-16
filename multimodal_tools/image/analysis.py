"""
Image Analysis using Gemini Vision

Uses Gemini's native vision capabilities to analyze images.
No additional API keys needed - uses the same GEMINI_API_KEY.
"""

import os
import sys
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import google.generativeai as genai
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def analyze_image(image_path: str, question: Optional[str] = None) -> str:
    """
    Analyze an image using Gemini's vision capabilities.
    
    Args:
        image_path: Path to the image file (local file path or URL)
        question: Optional question about the image. If None, provides general description.
    
    Returns:
        Analysis result as text string
    
    Examples:
        >>> analyze_image("photo.jpg")
        "This image shows..."
        
        >>> analyze_image("photo.jpg", "What objects are in this image?")
        "The image contains..."
    """
    if not HAS_PIL:
        return (
            "❌ Image analysis requires PIL/Pillow library.\n"
            "Install with: pip install Pillow"
        )
    
    # Check if image exists
    if not os.path.exists(image_path) and not image_path.startswith(("http://", "https://")):
        return f"❌ Error: Image file not found: {image_path}"
    
    try:
        # Load image
        if image_path.startswith(("http://", "https://")):
            import requests
            from io import BytesIO
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(image_path)
        
        # Create prompt
        if question:
            prompt = question
        else:
            prompt = "Describe this image in detail. Include objects, people, text, colors, and any other relevant information."
        
        # Use Gemini's vision model
        # Try gemini-1.5-pro first (best vision), fallback to gemini-pro-vision
        vision_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro-vision"]
        
        last_error = None
        for model_name in vision_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([prompt, img])
                
                if hasattr(response, 'text') and response.text:
                    return response.text
                else:
                    return str(response)
            except Exception as e:
                last_error = e
                continue
        
        # If all models fail, return error
        return f"❌ Error analyzing image: {last_error}"
        
    except Exception as e:
        return f"❌ Error processing image: {str(e)}"

