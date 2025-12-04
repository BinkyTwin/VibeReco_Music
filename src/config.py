"""
Configuration module for the RecoLLM project.

This module loads environment variables from a .env file and provides
centralized access to API keys and configuration settings used throughout
the application.

Environment Variables:
    OPENAI_API_KEY: API key for OpenAI services (embeddings)
    TOKEN_GENIUS: Access token for Genius API (lyrics fetching)
    OPENROUTER_API_KEY: API key for OpenRouter AI services (analysis)
    CLIENT_ID_GENIUS: Genius API client ID
    CLIENT_SECRET_GENIUS: Genius API client secret

Constants:
    DATA_DIR: Directory path for storing data files (default: "data")
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOKEN_GENIUS = os.getenv("TOKEN_GENIUS")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CLIENT_ID_GENIUS = os.getenv("CLIENT_ID_GENIUS")
CLIENT_SECRET_GENIUS = os.getenv("CLIENT_SECRET_GENIUS")
DATA_DIR = "data"