import logging

from bot.core.domain.const.env_const import DEBUG_MODE_TYPING, DEBUG_MODE_LOGGING

CLASS_NAME = 'class_name'

def get_logger(
    class_name: str,
):
    base_logger = logging.getLogger(__name__)
    # Оборачиваем адаптером, который добавляет поле class_name
    logger = logging.LoggerAdapter(
        base_logger, {CLASS_NAME: class_name},
    )

    return logger


def get_logging_config():
    logging_level = logging.DEBUG if DEBUG_MODE_LOGGING else logging.INFO

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(levelname)s - %(name)s :: %(message)s',
            },
            'bot_format': {
                'format': f'%(asctime)s - %(levelname)s - %({CLASS_NAME})s :: %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'default',
                'stream': 'ext://sys.stdout',
            },
            'bot_console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'bot_format',  # свой формат
                'stream': 'ext://sys.stdout',
            },
        },
        'root': {  # корневой логгер
            'level': 'INFO',
            'handlers': ['console'],
        },
        'loggers': {
            'bot': {  # замените на имя вашего пакета/модуля
                'level': logging_level,
                'handlers': ['bot_console'],
                'propagate': False,
            },
        },
    }
