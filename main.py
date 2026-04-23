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
    session_str = State()
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
    kb.adjust(2)
    await msg.answer("✅ Main Menu:", reply_markup=kb.as_markup())

# --- LOGIN FLOW ---
@dp.callback_query(F.data == "add_acc")
async def add_acc_method(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Phone+OTP", callback_data="login_phone")
    kb.button(text="Session String", callback_data="login_session")
    await call.message.answer("Select Method:", reply_markup=kb.as_markup())
    await state.set_state(States.add_method)

@dp.callback_query(F.data == "login_phone")
async def ask_phone(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Send Phone (+91...):")
    await state.set_state(States.phone)

@dp.message(States.phone)
async def process_phone(msg: types.Message, state: FSMContext):
    app = Client("temp_login", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
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

# --- TASK FLOW ---
@dp.callback_query(F.data == "add_task")
async def add_task(call: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Vote", callback_data="task_vote")
    kb.button(text="Reaction", callback_data="task_react")
    await call.message.answer("Select Task:", reply_markup=kb.as_markup())
    await state.set_state(States.task_type)

@dp.callback_query(F.data.startswith("task_"))
async def task_steps(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(type=call.data.split("_")[1])
    await call.message.answer("Send Post Link:")
    await state.set_state(States.task_post)

@dp.message(States.task_post)
async def get_link(msg: types.Message, state: FSMContext):
    await state.update_data(post=msg.text)
    await msg.answer("Send Channel/Group Link:")
    await state.set_state(States.task_channel)

@dp.message(States.task_channel)
async def get_channel(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if data['type'] == 'react':
        await msg.answer("Send Emoji:")
        await state.set_state(States.task_emoji)
        await state.update_data(channel=msg.text)
    else:
        await execute(msg.from_user.id, data['type'], data['post'], msg.text, None)
        await msg.answer("✅ Task Executed!")
        await state.clear()

@dp.message(States.task_emoji)
async def final_react(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    await execute(msg.from_user.id, data['type'], data['post'], data['channel'], msg.text)
    await msg.answer("✅ Task Executed!")
    await state.clear()

async def execute(uid, t_type, link, chan, emoji):
    accounts = await db.get_accounts(uid)
    for phone, session in accounts:
        async with Client(f"acc_{phone}", api_id=config.API_ID, api_hash=config.API_HASH, session_string=session) as app:
            await app.join_chat(chan)
            # Yahan logic hai execution ka
            msg_id = int(link.split('/')[-1])
            if t_type == 'react':
                await app.send_reaction(chan, msg_id, emoji=emoji)

async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
