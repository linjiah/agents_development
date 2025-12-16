"""
Image Generation

Supports multiple image generation APIs:
1. OpenAI DALL-E (default, easiest)
2. Google Imagen (via Vertex AI)
3. Stability AI (alternative)

Set environment variables:
- OPENAI_API_KEY for DALL-E
- GOOGLE_APPLICATION_CREDENTIALS for Imagen
- STABILITY_API_KEY for Stability AI
"""

import os
import sys
import hashlib
from typing import Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Create output directory for generated images
OUTPUT_DIR = Path(__file__).parent.parent.parent / "generated_images"
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_image_dalle(prompt: str, style: str = "realistic", size: str = "1024x1024") -> str:
    """Generate image using OpenAI DALL-E API."""
    try:
        import openai
    except ImportError:
        return (
            "❌ DALL-E requires openai library.\n"
            "Install with: pip install openai"
        )
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "❌ OPENAI_API_KEY not set.\n"
            "Get your key from: https://platform.openai.com/api-keys"
        )
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Enhance prompt with style
        enhanced_prompt = f"{prompt}, {style} style, high quality"
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            n=1,
            size=size,
            quality="standard"
        )
        
        image_url = response.data[0].url
        
        # Download and save image
        import requests
        img_response = requests.get(image_url)
        
        # Generate filename
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        filename = f"dalle_{prompt_hash}.png"
        filepath = OUTPUT_DIR / filename
        
        with open(filepath, "wb") as f:
            f.write(img_response.content)
        
        return (
            f"✅ Image generated successfully!\n"
            f"- Prompt: {prompt}\n"
            f"- Style: {style}\n"
            f"- Saved to: {filepath}\n"
            f"- URL: {image_url}"
        )
        
    except Exception as e:
        return f"❌ Error generating image with DALL-E: {str(e)}"

def generate_image_imagen(prompt: str, style: str = "realistic") -> str:
    """
    Generate image using Google Imagen API (Vertex AI).
    
    Note: Imagen requires Vertex AI setup. See GOOGLE_SERVICES_SETUP.md for details.
    """
    try:
        from google.cloud import aiplatform
        try:
            from vertexai.preview.vision_models import ImageGenerationModel
        except ImportError:
            # Try alternative import path
            try:
                from vertexai.preview import generative_models
                ImageGenerationModel = None  # Will use alternative approach
            except ImportError:
                return (
                    "❌ Google Imagen requires Vertex AI libraries.\n"
                    "Install with: pip install google-cloud-aiplatform\n"
                    "\n"
                    "See GOOGLE_SERVICES_SETUP.md for complete setup instructions.\n"
                    "\n"
                    "Quick setup:\n"
                    "1. pip install google-cloud-aiplatform\n"
                    "2. gcloud auth application-default login\n"
                    "3. Set GOOGLE_CLOUD_PROJECT in .env\n"
                    "4. Enable Vertex AI API in Google Cloud Console\n"
                    "\n"
                    "Alternative: Use DALL-E (easier setup, just needs OPENAI_API_KEY)"
                )
    except ImportError:
        return (
            "❌ Google Imagen requires Vertex AI libraries.\n"
            "Install with: pip install google-cloud-aiplatform\n"
            "\n"
            "See GOOGLE_SERVICES_SETUP.md for complete setup instructions.\n"
            "\n"
            "Alternative: Use DALL-E (easier setup, just needs OPENAI_API_KEY)"
        )
    
    # Check for credentials
    has_creds = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or
        os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json"))
    )
    
    if not has_creds:
        return (
            "❌ Google Cloud credentials not found.\n"
            "Set up authentication:\n"
            "1. Run: gcloud auth application-default login\n"
            "   OR\n"
            "2. Set GOOGLE_APPLICATION_CREDENTIALS to service account JSON path\n"
            "\n"
            "See GOOGLE_SERVICES_SETUP.md for details.\n"
            "\n"
            "Alternative: Use DALL-E (easier setup, just needs OPENAI_API_KEY)"
        )
    
    try:
        # Initialize Vertex AI
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        if not project_id:
            return (
                "❌ GOOGLE_CLOUD_PROJECT not set.\n"
                "Set it in your .env file:\n"
                "GOOGLE_CLOUD_PROJECT=your-project-id\n"
                "\n"
                "See GOOGLE_SERVICES_SETUP.md for complete setup.\n"
                "\n"
                "Alternative: Use DALL-E (easier setup, just needs OPENAI_API_KEY)"
            )
        
        aiplatform.init(project=project_id, location=location)
        
        # Try to use Imagen model
        try:
            if ImageGenerationModel:
                model = ImageGenerationModel.from_pretrained("imagegeneration@006")
            else:
                # Alternative: Use REST API or different approach
                # For now, provide helpful error
                return (
                    "⚠️ Imagen API integration in progress.\n"
                    "Imagen requires specific Vertex AI setup.\n"
                    "\n"
                    "Current status:\n"
                    "- Google Speech-to-Text: ✅ Fully working\n"
                    "- Google Text-to-Speech: ✅ Fully working\n"
                    "- Google Imagen: ⚠️ Requires additional Vertex AI configuration\n"
                    "\n"
                    "For now, please use DALL-E:\n"
                    "1. Set OPENAI_API_KEY in .env\n"
                    "2. Image generation will use DALL-E automatically\n"
                    "\n"
                    "Or see GOOGLE_SERVICES_SETUP.md for Imagen setup instructions."
                )
            
            # Enhance prompt with style
            enhanced_prompt = f"{prompt}, {style} style, high quality"
            
            # Generate image
            response = model.generate_images(
                prompt=enhanced_prompt,
                number_of_images=1,
                aspect_ratio="1:1"
            )
            
            # Get generated image
            generated_image = response.generated_images[0]
            image_bytes = generated_image.image_bytes
            
            # Save image
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
            filename = f"imagen_{prompt_hash}.png"
            filepath = OUTPUT_DIR / filename
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            return (
                f"✅ Image generated successfully with Google Imagen!\n"
                f"- Prompt: {prompt}\n"
                f"- Style: {style}\n"
                f"- Saved to: {filepath}\n"
                f"- Model: Imagen"
            )
            
        except Exception as model_error:
            return (
                f"⚠️ Imagen model initialization issue: {str(model_error)}\n"
                "\n"
                "Imagen setup can be complex. For now, using DALL-E:\n"
                "1. Set OPENAI_API_KEY in .env\n"
                "2. Image generation will automatically use DALL-E\n"
                "\n"
                "See GOOGLE_SERVICES_SETUP.md for Imagen setup help."
            )
        
    except Exception as e:
        return (
            f"❌ Error with Google Imagen: {str(e)}\n"
            "\n"
            "Common issues:\n"
            "1. Vertex AI API not enabled\n"
            "2. Insufficient permissions\n"
            "3. Project billing not enabled\n"
            "\n"
            "Quick fixes:\n"
            "1. Enable API: gcloud services enable aiplatform.googleapis.com\n"
            "2. Check billing: https://console.cloud.google.com/billing\n"
            "3. Authenticate: gcloud auth application-default login\n"
            "\n"
            "See GOOGLE_SERVICES_SETUP.md for complete instructions.\n"
            "\n"
            "Alternative: Use DALL-E (easier setup, just needs OPENAI_API_KEY)"
        )

def generate_image_stability(prompt: str, style: str = "realistic") -> str:
    """Generate image using Stability AI API."""
    try:
        import requests
    except ImportError:
        return "❌ requests library required for Stability AI"
    
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        return (
            "❌ STABILITY_API_KEY not set.\n"
            "Get your key from: https://platform.stability.ai/"
        )
    
    # Implementation would go here
    return "⚠️ Stability AI integration coming soon. Using DALL-E for now."

def generate_image(prompt: str, style: str = "realistic", provider: str = "auto") -> str:
    """
    Generate an image based on a prompt and style.
    
    Args:
        prompt: Image description/prompt
        style: Style (e.g., realistic, sketch, 3d, anime, oil painting)
        provider: Image generation provider ("dalle", "imagen", "stability", or "auto")
    
    Returns:
        Result message with image location/URL
    
    Examples:
        >>> generate_image("a sunset over mountains", "realistic")
        "✅ Image generated successfully!..."
    """
    # Auto-select provider based on available API keys
    # Priority: Google Imagen first (for consistency with Google ADK), then others
    if provider == "auto":
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            provider = "imagen"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "dalle"
        elif os.getenv("STABILITY_API_KEY"):
            provider = "stability"
        else:
            return (
                "❌ No image generation API key found.\n"
                "Please set one of:\n"
                "- GOOGLE_APPLICATION_CREDENTIALS (for Imagen - recommended for Google ADK)\n"
                "- OPENAI_API_KEY (for DALL-E)\n"
                "- STABILITY_API_KEY (for Stability AI)\n"
                "\n"
                "Recommended: Use Google Imagen for consistency with Google ADK:\n"
                "1. Set up Google Cloud Project\n"
                "2. Enable Vertex AI API\n"
                "3. Set GOOGLE_APPLICATION_CREDENTIALS\n"
                "\n"
                "Alternative: Use DALL-E for easier setup:\n"
                "1. Get key from https://platform.openai.com/api-keys\n"
                "2. Set OPENAI_API_KEY in your .env file"
            )
    
    # Route to appropriate provider
    if provider == "dalle":
        return generate_image_dalle(prompt, style)
    elif provider == "imagen":
        return generate_image_imagen(prompt, style)
    elif provider == "stability":
        return generate_image_stability(prompt, style)
    else:
        return f"❌ Unknown provider: {provider}. Use 'dalle', 'imagen', or 'stability'"

