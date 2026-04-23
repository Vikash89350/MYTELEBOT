import asyncio
import os
import config
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import db
from keep_alive import keep_alive

# States
class BotStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_otp = State()

# Bot Setup
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
login_clients = {}

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Account", callback_data="add_acc")
    builder.button(text="👤 My Accounts", callback_data="my_accs")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🚀 Bot Started! Options:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "add_acc")
async def start_add_acc(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter Phone Number (+91xxxxxxxxx):")
    await state.set_state(BotStates.waiting_for_phone)

@dp.message(BotStates.waiting_for_phone)
async def get_otp(message: types.Message, state: FSMContext):
    # LAZY IMPORT: Pyrogram yahan import hoga, main start par nahi
    from pyrogram import Client
    
    phone = message.text
    app = Client(f"session_{message.from_user.id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    
    await app.start()
    try:
        sent_code = await app.send_code(phone)
        login_clients[message.from_user.id] = {"app": app, "phone": phone, "hash": sent_code.phone_code_hash}
        await message.answer("✅ OTP sent! Enter OTP:")
        await state.set_state(BotStates.waiting_for_otp)
    except Exception as e:
        await app.stop()
        await message.answer(f"❌ Error: {e}")

@dp.message(BotStates.waiting_for_otp)
async def save_account(message: types.Message, state: FSMContext):
    # LAZY IMPORT: Yahan bhi
    from pyrogram import Client
    
    otp = message.text
    data = login_clients.get(message.from_user.id)
    if not data:
        await message.answer("Session expired. Start again.")
        return

    app = data["app"]
    try:
        await app.sign_in(data["phone"], data["hash"], otp)
        session_string = await app.export_session_string()
        await db.save_account(message.from_user.id, data["phone"], session_string)
        
        await message.answer("🎉 Account Saved Successfully!")
        await app.stop()
        del login_clients[message.from_user.id]
        await state.clear()
    except Exception as e:
        await app.stop()
        await message.answer(f"❌ Login Failed: {e}")
        await state.clear()

async def main():
    await db.connect()
    keep_alive() # Web server chalu
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
