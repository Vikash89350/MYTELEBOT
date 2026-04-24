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
temp_storage = {}

# FSM States
class AddAccState(StatesGroup):
    phone = State()
    otp = State()

class AddTaskState(StatesGroup):
    t_type = State()
    link = State()
    channel = State()
    emoji = State()

# --- START MENU ---
@dp.message(CommandStart())
async def start_cmd(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Account", callback_data="add_acc")
    kb.button(text="👤 My Accounts", callback_data="my_accs")
    kb.button(text="📝 Add Task", callback_data="add_task")
    kb.button(text="📋 My Tasks", callback_data="my_tasks")
    kb.adjust(2)
    await msg.answer("🚀 Menu:", reply_markup=kb.as_markup())

# --- 1. ADD ACCOUNT FLOW ---
@dp.callback_query(F.data == "add_acc")
async def start_add_acc(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Enter Phone Number (with +91):")
    await state.set_state(AddAccState.phone)

@dp.message(AddAccState.phone)
async def get_phone(msg: types.Message, state: FSMContext):
    app = Client(f"session_{msg.from_user.id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    await app.start()
    code = await app.send_code(msg.text)
    temp_storage[msg.from_user.id] = {"app": app, "phone": msg.text, "hash": code.phone_code_hash}
    await msg.answer("OTP Sent! Enter OTP:")
    await state.set_state(AddAccState.otp)

@dp.message(AddAccState.otp)
async def get_otp(msg: types.Message, state: FSMContext):
    data = temp_storage.get(msg.from_user.id)
    await data["app"].sign_in(data["phone"], data["hash"], msg.text)
    session = await data["app"].export_session_string()
    await db.add_account(msg.from_user.id, data["phone"], session)
    await data["app"].stop()
    await msg.answer("✅ Account Saved!")
    await state.clear()

# --- 2. LIST ACCOUNTS ---
@dp.callback_query(F.data == "my_accs")
async def list_accs(call: types.CallbackQuery):
    accs = await db.get_accounts(call.from_user.id)
    if not accs: return await call.message.answer("No accounts found.")
    await call.message.answer("📱 Your Accounts:\n" + "\n".join([a[0] for a in accs]))

# --- 3. ADD TASK FLOW ---
@dp.callback_query(F.data == "add_task")
async def start_task(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Vote", callback_data="type_vote")
    kb.button(text="Reaction", callback_data="type_react")
    await call.message.answer("Select Task Type:", reply_markup=kb.as_markup())
    await state.set_state(AddTaskState.t_type)

@dp.callback_query(F.data.startswith("type_"))
async def get_type(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(t_type=call.data.split("_")[1])
    await call.message.answer("Send Post Link:")
    await state.set_state(AddTaskState.link)

@dp.message(AddTaskState.link)
async def get_link(msg: types.Message, state: FSMContext):
    await state.update_data(link=msg.text)
    await msg.answer("Send Channel Link:")
    await state.set_state(AddTaskState.channel)

@dp.message(AddTaskState.channel)
async def get_channel(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['t_type'] == 'react':
        await state.update_data(channel=msg.text)
        await msg.answer("Send Emoji:")
        await state.set_state(AddTaskState.emoji)
    else:
        await db.save_task(msg.from_user.id, data['t_type'], data['link'], msg.text, None)
        await msg.answer("✅ Task Saved!")
        await state.clear()

@dp.message(AddTaskState.emoji)
async def get_emoji(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.save_task(msg.from_user.id, data['t_type'], data['link'], data['channel'], msg.text)
    await msg.answer("✅ Task Saved!")
    await state.clear()

# --- 4. MY TASKS ---
@dp.callback_query(F.data == "my_tasks")
async def list_tasks(call: types.CallbackQuery):
    tasks = await db.get_user_tasks(call.from_user.id)
    if not tasks: return await call.message.answer("No tasks.")
    await call.message.answer("📋 Your Tasks:\n" + "\n".join([f"{t[1]} - {t[2]}" for t in tasks]))

async def main():
    await db.init_db()
    print("Bot is polling...")
    await dp.start_polling(bot)

# SABSE NEECHE KA BLOCK
if __name__ == "__main__":
    print("DEBUG: SCRIPT START HO RAHI HAI...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"DEBUG CRITICAL ERROR: {e}")
