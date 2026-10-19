import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Project Root & Directory Paths
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
OUTPUT_DIR = BASE_DIR / "carousels"

# API & Model Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = "gemini-2.5-flash"

# Canvas Dimensions (4:5 Instagram Portrait)
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350

# Card Framing & Geometry
PADDING = 36                                  # Outer black border frame width
CARD_PADDING = PADDING                         # Alias for compatibility
CORNER_RADIUS = 140                           # Deep rounded corner curve
CARD_CORNER_RADIUS = CORNER_RADIUS             # Alias for compatibility

CARD_WIDTH = CANVAS_WIDTH - (PADDING * 2)     # 1008 px
CARD_HEIGHT = CANVAS_HEIGHT - (PADDING * 2)   # 1278 px

# Vignette & Film Grain FX Settings
VIGNETTE_INSET = 8                            # Inset depth for the inner shadow ring
VIGNETTE_BLUR_RADIUS = 14                     # Soft gradient blur bleeding inward
GRAIN_INTENSITY = 18                          # Film grain intensity (0-100)

# Color Palette
COLOR_BG = "#0A0A0A"                          # Dark background canvas
COLOR_TEXT = "#000000"                        # Dark text overlay
COLOR_FALLBACK = "#1A1D24"                    # Fallback solid card color
OUTER_CANVAS_COLOR = (10, 10, 10, 255)        # RGBA representation of COLOR_BG

# Brand Branding
BRAND_HANDLE = "@unmasked.thoughts"

# Typography Paths
FONT_REGULAR_PATH = FONTS_DIR / "georgia.ttf"
FONT_BOLD_PATH = FONTS_DIR / "georgia_bold.ttf"
FONT_ITALIC_PATH = FONTS_DIR / "georgia_italic.ttf"
