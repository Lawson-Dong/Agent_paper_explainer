import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("Warning: DEEPSEEK_API_KEY not found. Please set it in a .env file for the app to work.")

# Grammarly API Configuration
GRAMMARLY_CLIENT_ID = os.getenv("GRAMMARLY_CLIENT_ID")
GRAMMARLY_CLIENT_SECRET = os.getenv("GRAMMARLY_CLIENT_SECRET")

if not GRAMMARLY_CLIENT_ID or not GRAMMARLY_CLIENT_SECRET:
    GRAMMARLY_AVAILABLE = False
else:
    GRAMMARLY_AVAILABLE = True