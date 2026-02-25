import asyncio
import random

from bot.domain.const.env_const import DEBUG_MODE


async def wait_to_see_message():
    if not DEBUG_MODE:
        await asyncio.sleep(random.uniform(a = 1, b = 10))


async def wait_to_read_message(
    message: str,
):
    if not DEBUG_MODE:
        read_time = max(2.0, len(message.split()) / 2.5)
        await asyncio.sleep(read_time)


async def wait_to_write_message(text: str):
    if not DEBUG_MODE:
        write_time = len(text) / random.uniform(a = 3, b = 10)
        await asyncio.sleep(write_time)
