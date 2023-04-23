from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor
from config import token
from db import Database
import asyncio
from config import host, user, password, db_name, port

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


connection = Database(
    host=host,
    user=user,
    password=password,
    database=db_name,
    port=port
)


async def main():
    groups = connection.get_groups()
    while True:
        for group in groups:
            await connection.sniper_bot(group[0])
        await asyncio.sleep(100)


if __name__ == '__main__':
    from handlers import dp
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    executor.start_polling(dp, skip_updates=True)