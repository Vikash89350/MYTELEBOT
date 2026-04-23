import asyncio
from aiogram import Bot, Dispatcher
import config
from database import get_pool

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

async def main():
    # Database table create krne ka logic yahan daal sakte ho
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
