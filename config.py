"""
Configuration settings for the Weather LLM MCP project
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Weather API Configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MCP Server Configuration
MCP_SERVER_NAME = "weather-server"
MCP_SERVER_VERSION = "1.0.0"

# Default settings
DEFAULT_UNITS = "metric"  # metric, imperial, or kelvin
DEFAULT_LANGUAGE = "en"

# Validation
def validate_config():
    """Validate required configuration"""
    if not OPENWEATHER_API_KEY:
        raise ValueError(
            "OPENWEATHER_API_KEY is required. "
            "Get your free API key from https://openweathermap.org/api "
            "and set it in your .env file"
        )
    
    return True
