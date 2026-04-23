import asyncio
from aiogram import Bot, Dispatcher
import config
from database import get_pool
from keep_alive import keep_alive  # <--- Ye line add ki hai

# Bot aur Dispatcher setup
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

async def main():
    # Render ke liye dummy web server start karna (zaroori hai)
    keep_alive() 
    
    print("Bot is starting...")
    
    # Bot polling shuru
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Event loop run karna
    asyncio.run(main())
