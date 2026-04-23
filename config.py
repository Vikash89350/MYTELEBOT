import os
from dotenv import load_dotenv

load_dotenv()

# Safely get variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
API_HASH = os.getenv("API_HASH")

# API_ID ko safely handle karo
raw_api_id = os.getenv("API_ID")
if raw_api_id:
    API_ID = int(raw_api_id)
else:
    API_ID = 0  # Default value
    print("⚠️ WARNING: API_ID not found in Environment Variables!")

print(f"DEBUG: Loaded API_ID = {API_ID}") # Isse log mein dikh jayega kya load hua
