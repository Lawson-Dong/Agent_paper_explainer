import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("Warning: DEEPSEEK_API_KEY not found. Please set it in a .env file for the app to work.")