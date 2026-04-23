import asyncio, config, db
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
login_data = {}

class FSM(StatesGroup):
    add_method = State()
    phone = State()
    otp = State()
    session_str = State()
    task_type = State()
    task_link = State()
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
    await msg.answer("Welcome! Select Option:", reply_markup=kb.as_markup())

# --- LOGIN FLOW ---
@dp.callback_query(F.data == "add_acc")
async def add_acc(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Phone + OTP", callback_data="type_phone")
    kb.button(text="Session String", callback_data="type_session")
    await call.message.answer("Choose Login Method:", reply_markup=kb.as_markup())
    await state.set_state(FSM.add_method)

@dp.callback_query(F.data == "type_phone")
async def ask_phone(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Enter Phone Number (e.g. +91xxxxxxxxx):")
    await state.set_state(FSM.phone)

@dp.message(FSM.phone)
async def process_phone(msg: types.Message, state: FSMContext):
    app = Client("temp_session", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
    await app.start()
    code = await app.send_code(msg.text)
    login_data[msg.from_user.id] = {"app": app, "phone": msg.text, "hash": code.phone_code_hash}
    await msg.answer("OTP Sent! Enter OTP:")
    await state.set_state(FSM.otp)

@dp.message(FSM.otp)
async def process_otp(msg: types.Message, state: FSMContext):
    data = login_data[msg.from_user.id]
    await data["app"].sign_in(data["phone"], data["hash"], msg.text)
    session = await data["app"].export_session_string()
    await db.add_account(msg.from_user.id, data["phone"], session)
    await msg.answer("✅ Account Added!")
    await data["app"].stop()
    await state.clear()

# --- TASK FLOW ---
@dp.callback_query(F.data == "add_task")
async def ask_task(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Vote", callback_data="task_vote")
    kb.button(text="Reaction", callback_data="task_react")
    await call.message.answer("Choose Task:", reply_markup=kb.as_markup())
    await state.set_state(FSM.task_type)

@dp.callback_query(F.data.startswith("task_"))
async def task_details(call: types.CallbackQuery, state: FSMContext):
    t_type = call.data.split("_")[1]
    await state.update_data(type=t_type)
    await call.message.answer("Send Post Link:")
    await state.set_state(FSM.task_link)

@dp.message(FSM.task_link)
async def get_link(msg: types.Message, state: FSMContext):
    await state.update_data(link=msg.text)
    await msg.answer("Send Channel Link (Private/Public):")
    await state.set_state(FSM.task_channel)

@dp.message(FSM.task_channel)
async def get_channel(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['type'] == "react":
        await msg.answer("Send Reaction Emoji:")
        await state.set_state(FSM.task_emoji)
    else:
        await db.save_task(msg.from_user.id, data['type'], data['link'], msg.text, None)
        await msg.answer("✅ Task Created! Executing...")
        await execute_task(msg.from_user.id, data['type'], data['link'], msg.text, None)
        await state.clear()

async def execute_task(user_id, t_type, post_link, channel_link, emoji):
    accounts = await db.get_accounts(user_id)
    for phone, session in accounts:
        try:
            async with Client(f"acc_{phone}", api_id=config.API_ID, api_hash=config.API_HASH, session_string=session) as app:
                chat = await app.join_chat(channel_link)
                # Logic for Vote/Reaction goes here using post_link ID
                # Simple example:
                if t_type == "react":
                    await app.send_reaction(chat.id, int(post_link.split('/')[-1]), emoji=emoji)
        except Exception as e:
            print(f"Error on {phone}: {e}")

async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
