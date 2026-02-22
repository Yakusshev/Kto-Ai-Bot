import os
import ydb

from bot.domain.const.env_const import YDB_AUTH_KEY_FILE, YDB_ENDPOINT, YDB_PATH


def create_ydb_driver():

    # Выбираем способ авторизации
    if YDB_AUTH_KEY_FILE and os.path.exists(YDB_AUTH_KEY_FILE):
        # Локальная разработка: используем файл ключа
        print(f"YDB: Использую авторизацию через файл {YDB_AUTH_KEY_FILE}")
        credentials = ydb.iam.ServiceAccountCredentials.from_file(YDB_AUTH_KEY_FILE)
    else:
        # В облаке: используем автоматические метаданные сервисного аккаунта
        print("YDB: Файл ключа не найден, использую MetadataUrlCredentials")
        credentials = ydb.iam.MetadataUrlCredentials()

    driver_config = ydb.DriverConfig(
        endpoint=YDB_ENDPOINT,
        database=YDB_PATH,
        credentials=credentials,
    )

    driver = ydb.Driver(driver_config)

    # Ожидаем готовности драйвера (таймаут 5 секунд)
    try:
        driver.wait(fail_fast=True, timeout=5)
        print("YDB: Драйвер успешно инициализирован")
    except TimeoutError:
        print("YDB: Ошибка инициализации драйвера (timeout)")
        raise

    return driver
