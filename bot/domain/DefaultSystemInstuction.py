import os
from datetime import datetime
from zoneinfo import ZoneInfo

__NAME = '[NAME]'
__DATE_AND_TIME = '[DATE_AND_TIME]'

def anya_system_instruction(
    user_nickname: str,
):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(current_dir, '..', 'resource', 'string', 'default_system_instruction.txt')

    with (open(file_path, 'r', encoding='utf-8') as f):
        return f.read().strip()\
            .replace(__NAME, user_nickname)\
            .replace(__DATE_AND_TIME, get_simple_volgograd_time())


def get_simple_volgograd_time():
    volgograd_tz = ZoneInfo('Europe/Volgograd')
    current_time = datetime.now(volgograd_tz)

    time_readable = current_time.strftime("%Y-%m-%d %H:%M")

    print("time_readable ", time_readable)

    return time_readable
