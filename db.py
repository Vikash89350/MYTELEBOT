import aiosqlite

async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS accounts (user_id INTEGER, phone TEXT, session TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, link TEXT, channel TEXT, emoji TEXT, status TEXT)")
        await db.commit()

async def add_account(user_id, phone, session):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT INTO accounts VALUES (?, ?, ?)", (user_id, phone, session))
        await db.commit()

async def get_accounts(user_id):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT phone, session FROM accounts WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

async def delete_account(user_id, phone):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("DELETE FROM accounts WHERE user_id = ? AND phone = ?", (user_id, phone))
        await db.commit()

async def save_task(user_id, type, link, channel, emoji, status="Pending"):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT INTO tasks (user_id, type, link, channel, emoji, status) VALUES (?, ?, ?, ?, ?, ?)", 
                         (user_id, type, link, channel, emoji, status))
        await db.commit()

async def get_tasks(user_id):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT id, type, link, status FROM tasks WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()
