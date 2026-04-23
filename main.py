import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from keep_alive import keep_alive

# --- States ---
class BotStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_otp = State()
    waiting_for_task_type = State()
    waiting_for_post_link = State()
    waiting_for_channel_link = State()
    waiting_for_delay = State()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Menu Design ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Account", callback_data="add_acc")
    builder.button(text="👤 My Accounts", callback_data="my_accs")
    builder.button(text="📝 Add Task", callback_data="add_task")
    builder.button(text="📋 My Tasks", callback_data="my_tasks")
    builder.adjust(2)
    return builder.as_markup()

# --- HANDLERS ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🚀 Qutomatic Bot Pro\nSelect an option:", reply_markup=get_main_menu())

# 1. ADD ACCOUNT FLOW
@dp.callback_query(F.data == "add_acc")
async def start_add_acc(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Enter Phone Number (+91xxxxxxxxx):")
    await state.set_state(BotStates.waiting_for_phone)

@dp.message(BotStates.waiting_for_phone)
async def get_otp(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("OTP mangwa raha hoon... OTP bhejein:")
    await state.set_state(BotStates.waiting_for_otp)

@dp.message(BotStates.waiting_for_otp)
async def save_account(message: types.Message, state: FSMContext):
    # Yahan Pyrogram login aur DB save ka logic aayega
    await message.answer("✅ Account Saved Successfully!", reply_markup=get_main_menu())
    await state.clear()

# 2. MY ACCOUNTS & REMOVE
@dp.callback_query(F.data == "my_accs")
async def show_accounts(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    # Yahan DB se accounts loop karke buttons banao
    builder.button(text="❌ Remove (Dummy)", callback_data="del_1")
    builder.button(text="🔙 Back", callback_data="main_menu")
    await callback.message.edit_text("Your Accounts:", reply_markup=builder.as_markup())

# 3. ADD TASK FLOW (Professional)
@dp.callback_query(F.data == "add_task")
async def start_task(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗳 Vote", callback_data="task_vote")
    builder.button(text="❤️ Reaction", callback_data="task_react")
    await callback.message.answer("Task type chunein:", reply_markup=builder.as_markup())
    await state.set_state(BotStates.waiting_for_task_type)

@dp.callback_query(F.data.startswith("task_"))
async def get_link(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(task_type=callback.data)
    await callback.message.answer("Post ki Link bhejein:")
    await state.set_state(BotStates.waiting_for_post_link)

@dp.message(BotStates.waiting_for_post_link)
async def get_channel(message: types.Message, state: FSMContext):
    await state.update_data(post_link=message.text)
    await message.answer("Channel/Group link bhejein:")
    await state.set_state(BotStates.waiting_for_channel_link)

@dp.message(BotStates.waiting_for_channel_link)
async def get_delay(message: types.Message, state: FSMContext):
    await state.update_data(channel=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="1 Sec", callback_data="delay_1")
    builder.button(text="5 Sec", callback_data="delay_5")
    await message.answer("Delay chunein:", reply_markup=builder.as_markup())
    await state.set_state(BotStates.waiting_for_delay)

@dp.callback_query(F.data.startswith("delay_"))
async def finalize_task(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✅ Task Processing Start ho gayi hai!")
    await state.clear()

async def main():
    keep_alive()
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
