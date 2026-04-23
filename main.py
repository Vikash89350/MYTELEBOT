import asyncio
from aiogram import Bot, Dispatcher
import config
from keep_alive import keep_alive

# Bot setup
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

async def main():
    # Server start taaki Render port detect kar sake
    keep_alive()
    print("Bot is starting up...")
    
    # Polling start
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
