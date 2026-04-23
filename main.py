import asyncio
import config
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client # <--- Pyrogram Import kiya
from db import db
from keep_alive import keep_alive

# States
class BotStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_otp = State()

# Temporary store for login
login_clients = {}

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Menu ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Account", callback_data="add_acc")
    builder.button(text="👤 My Accounts", callback_data="my_accs")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🚀 Bot Started! Options:", reply_markup=get_main_menu())

# --- LOGIN FLOW ---
@dp.callback_query(F.data == "add_acc")
async def start_add_acc(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter Phone Number (+91xxxxxxxxx):")
    await state.set_state(BotStates.waiting_for_phone)

@dp.message(BotStates.waiting_for_phone)
async def get_otp(message: types.Message, state: FSMContext):
    phone = message.text
    # Pyrogram Client banaya
    app = Client(f"session_{message.from_user.id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    await app.connect()
    
    try:
        sent_code = await app.send_code(phone)
        login_clients[message.from_user.id] = {"app": app, "phone": phone, "hash": sent_code.phone_code_hash}
        await message.answer("✅ OTP sent! Enter OTP:")
        await state.set_state(BotStates.waiting_for_otp)
    except Exception as e:
        await message.answer(f"❌ Error: {e}")
        await app.disconnect()

@dp.message(BotStates.waiting_for_otp)
async def save_account(message: types.Message, state: FSMContext):
    otp = message.text
    user_data = login_clients.get(message.from_user.id)
    
    if not user_data:
        await message.answer("Session expired. Start again.")
        return

    app = user_data["app"]
    try:
        await app.sign_in(user_data["phone"], user_data["hash"], otp)
        session_string = await app.export_session_string()
        
        # Database mein save karo
        await db.save_account(message.from_user.id, user_data["phone"], session_string)
        
        await message.answer("🎉 Account Saved Successfully!")
        await app.disconnect()
        del login_clients[message.from_user.id]
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Login Failed: {e}")
        await app.disconnect()
        await state.clear()

# --- Run ---
async def main():
    await db.connect()
    keep_alive()
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
