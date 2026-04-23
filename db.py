import os
import asyncpg

# Render ke environment variable se connection string uthayega
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Database se connect karega aur Tables banayega."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            print("✅ Database Connected Successfully!")
            await self.setup_tables()

    async def setup_tables(self):
        """Agar table nahi hai, toh create karega."""
        query = """
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            phone TEXT,
            session_string TEXT
        );
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query)

    # --- Account Operations ---
    async def save_account(self, user_id, phone, session_string):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO accounts (user_id, phone, session_string) VALUES ($1, $2, $3)",
                user_id, phone, session_string
            )

    async def get_accounts(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM accounts WHERE user_id = $1", user_id)

    async def delete_account(self, account_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM accounts WHERE id = $1", account_id)

# Bot mein import karne ke liye
db = Database()
