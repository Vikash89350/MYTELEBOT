import asyncio
import config
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import db  # Database import kiya
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

# --- Handlers ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🚀 AUTO DYNAMO Bot Pro\nSelect an option:", reply_markup=get_main_menu())

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
    data = await state.get_data()
    # Yahan DB mein save kar rahe hain
    await db.save_account(message.from_user.id, data['phone'], "dummy_session_string")
    await message.answer("✅ Account Saved Successfully!", reply_markup=get_main_menu())
    await state.clear()

# 2. MY ACCOUNTS & REMOVE
@dp.callback_query(F.data == "my_accs")
async def show_accounts(callback: types.CallbackQuery):
    accounts = await db.get_accounts(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    
    if not accounts:
        await callback.message.edit_text("No accounts saved.", reply_markup=get_main_menu())
        return

    for acc in accounts:
        builder.button(text=f"❌ {acc['phone']}", callback_data=f"del_{acc['id']}")
    
    builder.button(text="🔙 Back", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text("👤 Your Accounts:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("del_"))
async def delete_account(callback: types.CallbackQuery):
    acc_id = int(callback.data.split("_")[1])
    await db.delete_account(acc_id)
    await callback.answer("Account Removed!")
    await show_accounts(callback) # List refresh karo

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🚀 Main Menu:", reply_markup=get_main_menu())

# 3. ADD TASK FLOW
@dp.callback_query(F.data == "add_task")
async def start_task(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗳 Vote", callback_data="task_vote")
    builder.button(text="❤️ Reaction", callback_data="task_react")
    await callback.message.answer("Task type chunein:", reply_markup=builder.as_markup())
    await state.set_state(BotStates.waiting_for_task_type)

# [... baaki task handlers waise hi rehne do ...]

async def startup():
    await db.connect() # Database connect ho raha hai
    print("Database connected!")

async def main():
    await startup() # Yahan startup call kiya
    keep_alive()
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
