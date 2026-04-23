import asyncpg
import os

async def get_pool():
    return await asyncpg.create_pool(os.getenv("DATABASE_URL"))
