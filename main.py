import asyncio, config, db
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
login_store = {}

class States(StatesGroup):
    add_method = State()
    phone = State()
    otp = State()
    task_type = State()
    task_post = State()
    task_channel = State()
    task_emoji = State()

@dp.message(F.text == "/start")
async def start(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Account", callback_data="add_acc")
    kb.button(text="👤 My Accounts", callback_data="my_accs")
    kb.button(text="📝 Add Task", callback_data="add_task")
    kb.button(text="📋 My Tasks", callback_data="my_tasks")
    kb.adjust(2)
    await msg.answer("🚀 Menu:", reply_markup=kb.as_markup())

# --- LOGIN FLOW ---
@dp.callback_query(F.data == "add_acc")
async def add_acc(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Enter Phone Number:")
    await state.set_state(States.phone)

@dp.message(States.phone)
async def process_phone(msg: types.Message, state: FSMContext):
    app = Client(f"tmp_{msg.from_user.id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    await app.start()
    code = await app.send_code(msg.text)
    login_store[msg.from_user.id] = {"app": app, "phone": msg.text, "hash": code.phone_code_hash}
    await msg.answer("OTP Sent! Enter OTP:")
    await state.set_state(States.otp)

@dp.message(States.otp)
async def process_otp(msg: types.Message, state: FSMContext):
    data = login_store.get(msg.from_user.id)
    await data["app"].sign_in(data["phone"], data["hash"], msg.text)
    session = await data["app"].export_session_string()
    await db.add_account(msg.from_user.id, data["phone"], session)
    await msg.answer("✅ Account Saved!")
    await data["app"].stop()
    await state.clear()

# --- MY ACCOUNTS ---
@dp.callback_query(F.data == "my_accs")
async def show_accs(call: types.CallbackQuery):
    accs = await db.get_accounts(call.from_user.id)
    if not accs: return await call.message.answer("No accounts.")
    for p, s in accs:
        await call.message.answer(f"📱 {p}")

# --- TASK FLOW ---
@dp.callback_query(F.data == "add_task")
async def ask_task(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Vote", callback_data="task_vote")
    kb.button(text="Reaction", callback_data="task_react")
    await call.message.answer("Select:", reply_markup=kb.as_markup())
    await state.set_state(States.task_type)

@dp.callback_query(F.data.startswith("task_"))
async def get_task_info(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(type=call.data.split("_")[1])
    await call.message.answer("Send Post Link:")
    await state.set_state(States.task_post)

@dp.message(States.task_post)
async def get_link(msg: types.Message, state: FSMContext):
    await state.update_data(link=msg.text)
    await msg.answer("Send Channel Link:")
    await state.set_state(States.task_channel)

@dp.message(States.task_channel)
async def get_channel(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['type'] == 'react':
        await msg.answer("Send Emoji:")
        await state.set_state(States.task_emoji)
        await state.update_data(chan=msg.text)
    else:
        await db.save_task(msg.from_user.id, data['type'], data['link'], msg.text, None)
        await msg.answer("✅ Task Saved!")
        await state.clear()

@dp.message(States.task_emoji)
async def final_emoji(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.save_task(msg.from_user.id, data['type'], data['link'], data['chan'], msg.text)
    await msg.answer("✅ Task Saved!")
    await state.clear()

async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
