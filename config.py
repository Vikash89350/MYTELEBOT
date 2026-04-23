import os
from dotenv import load_dotenv

load_dotenv()

# Variables load karo
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
API_HASH = os.getenv("API_HASH")

# API_ID ko safely handle karo (Ye crash nahi karega)
raw_api_id = os.getenv("API_ID")
try:
    API_ID = int(raw_api_id) if raw_api_id else 0
except:
    API_ID = 0
    print("⚠️ ERROR: API_ID is not a valid number in Environment Variables!")

print(f"DEBUG: Config Loaded -> BOT_TOKEN={'Yes' if BOT_TOKEN else 'No'}, API_ID={API_ID}")
