import asyncio, config, db
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
temp_data = {}

class Auth(StatesGroup):
    phone = State()
    otp = State()

@dp.message(CommandStart())
async def start(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Account", callback_data="add")
    kb.button(text="👤 My Accounts", callback_data="list")
    kb.adjust(1)
    await msg.answer("Welcome! Select an option:", reply_markup=kb.as_markup())

# --- LOGIN FLOW ---
@dp.callback_query(F.data == "add")
async def add_acc(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Enter Phone Number (with +91):")
    await state.set_state(Auth.phone)

@dp.message(Auth.phone)
async def get_phone(msg: types.Message, state: FSMContext):
    app = Client(f"user_{msg.from_user.id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    await app.start()
    code = await app.send_code(msg.text)
    temp_data[msg.from_user.id] = {"app": app, "phone": msg.text, "hash": code.phone_code_hash}
    await msg.answer("OTP Sent! Enter Code:")
    await state.set_state(Auth.otp)

@dp.message(Auth.otp)
async def get_otp(msg: types.Message, state: FSMContext):
    data = temp_data.get(msg.from_user.id)
    await data["app"].sign_in(data["phone"], data["hash"], msg.text)
    session = await data["app"].export_session_string()
    await db.add_account(msg.from_user.id, data["phone"], session)
    await data["app"].stop()
    await msg.answer("✅ Account Saved!")
    await state.clear()

@dp.callback_query(F.data == "list")
async def list_accs(call: types.CallbackQuery):
    accs = await db.get_accounts(call.from_user.id)
    if not accs: return await call.answer("No accounts found.")
    await call.message.answer(f"Accounts: {', '.join([a[0] for a in accs])}")

async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
