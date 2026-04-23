import asyncio
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

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
login_clients = {}

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Account", callback_data="add_acc")
    builder.button(text="👤 My Account", callback_data="my_accs")
    builder.button(text="📝 Add Task", callback_data="add_task")
    builder.button(text="📋 My Tasks", callback_data="my_tasks")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    print("LOG: Start command received")
    await message.answer("🚀 Bot Menu:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "add_acc")
async def start_add_acc(callback: types.CallbackQuery, state: FSMContext):
    print("LOG: User clicked Add Account")
    await callback.message.answer("Enter Phone Number (with +91, e.g., +919876543210):")
    await state.set_state(BotStates.waiting_for_phone)

@dp.message(BotStates.waiting_for_phone)
async def get_otp(message: types.Message, state: FSMContext):
    print(f"LOG: Received phone number: {message.text}")
    from pyrogram import Client
    
    phone = message.text
    # Session name unique
    app = Client(f"session_{message.from_user.id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    
    try:
        print("LOG: Starting client...")
        await app.start()
        print("LOG: Client started. Sending code...")
        sent_code = await app.send_code(phone)
        
        login_clients[message.from_user.id] = {"app": app, "phone": phone, "hash": sent_code.phone_code_hash}
        await message.answer("✅ OTP sent! Enter OTP:")
        await state.set_state(BotStates.waiting_for_otp)
        print("LOG: OTP Sent success")
    except Exception as e:
        print(f"ERROR: {e}")
        await message.answer(f"❌ Error: {e}")

@dp.message(BotStates.waiting_for_otp)
async def save_account(message: types.Message, state: FSMContext):
    print(f"LOG: Received OTP: {message.text}")
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
        
        await message.answer("🎉 Account Logged In!")
        await app.stop()
        del login_clients[message.from_user.id]
        await state.clear()
        print("LOG: Account saved")
    except Exception as e:
        print(f"ERROR: {e}")
        await message.answer(f"❌ Login Failed: {e}")
        await state.clear()

async def main():
    await db.connect()
    keep_alive()
    print("Bot is fully running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
