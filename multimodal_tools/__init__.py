"""
Multimodal Tools Package

This package contains implementations for:
- Image generation and analysis
- Audio processing (speech-to-text, text-to-speech)
- Figure and diagram generation
"""

from .image.generation import generate_image
from .image.analysis import analyze_image
from .audio.speech_to_text import speech_to_text
from .audio.text_to_speech import text_to_speech
from .figures.generator import generate_figure

__all__ = [
    "generate_image",
    "analyze_image",
    "speech_to_text",
    "text_to_speech",
    "generate_figure",
]

