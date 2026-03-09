import asyncio
import random

from bot.core.domain.const.env_const import DEBUG_MODE_TYPING


async def wait_to_see_message():
    if not DEBUG_MODE_TYPING:
        await asyncio.sleep(random.uniform(a = 10, b = 30))


async def wait_to_start_typing(
    message: str,
):
    if not DEBUG_MODE_TYPING:
        read_time = max(2.0, len(message.split()) / 1.5)
        await asyncio.sleep(read_time)


async def wait_to_write_message(text: str):
    if not DEBUG_MODE_TYPING:
        write_time = len(text) / random.uniform(a = 2, b = 6)
        await asyncio.sleep(write_time)
