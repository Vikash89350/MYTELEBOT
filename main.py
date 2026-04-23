import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from keep_alive import keep_alive

# States (Bot ki yaaddasht)
class BotStates(StatesGroup):
    waiting_for_account = State()
    waiting_for_task = State()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Buttons Generator ---
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add Account", callback_data="add_acc")
    builder.button(text="➖ Remove Account", callback_data="rem_acc")
    builder.button(text="📝 Add Task", callback_data="add_task")
    builder.button(text="📋 My Tasks", callback_data="my_tasks")
    builder.adjust(2) # 2 columns
    return builder.as_markup()

# --- Handlers ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("👋 Swagat hai! Main aapka task manager hoon.\nNiche diye gaye menu se choose karein:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "add_acc")
async def add_account(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Account ka naam ya details bhejein:")
    await state.set_state(BotStates.waiting_for_account)
    await callback.answer()

@dp.callback_query(F.data == "add_task")
async def add_task(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Task ka description bhejein:")
    await state.set_state(BotStates.waiting_for_task)
    await callback.answer()

# --- Input Handling ---
@dp.message(BotStates.waiting_for_account)
async def save_account(message: types.Message, state: FSMContext):
    # Yahan DB mein save karne ka code aayega
    await message.answer(f"✅ Account '{message.text}' add ho gaya!", reply_markup=get_main_menu())
    await state.clear()

@dp.message(BotStates.waiting_for_task)
async def save_task(message: types.Message, state: FSMContext):
    # Yahan DB mein save karne ka code aayega
    await message.answer(f"✅ Task '{message.text}' list mein add ho gaya!", reply_markup=get_main_menu())
    await state.clear()

# --- Simple Handlers for other buttons ---
@dp.callback_query(F.data == "my_tasks")
async def show_tasks(callback: types.CallbackQuery):
    await callback.message.answer("📋 Aapke Tasks:\n1. Link posting\n2. OTP check", reply_markup=get_main_menu())
    await callback.answer()

async def main():
    keep_alive()
    print("Bot is ready and professional!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
