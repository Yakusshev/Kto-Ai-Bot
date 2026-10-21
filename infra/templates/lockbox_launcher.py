# Лаунчер контейнера бота: читает Lockbox-секрет от имени сервисного
# аккаунта VM, кладёт его записи в окружение и exec'ает команду бота.
#
# Запускается как `python -c "<этот файл>" <команда бота...>` из
# docker-compose (см. docker-compose.yaml.tftpl), поэтому:
#   - только стандартная библиотека (работает в любом python-образе);
#   - значения секретов не пишутся в логи и на диск хоста;
#   - запись YDB_AUTHORIZED_KEY_JSON (если есть) сохраняется в файл внутри
#     контейнера, а путь к нему передаётся боту в YDB_AUTH_KEY_FILE.
import base64
import json
import os
import signal
import sys
import time
import urllib.request

METADATA_TOKEN_URL = os.environ.get(
    "LOCKBOX_METADATA_TOKEN_URL",
    "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
)
PAYLOAD_URL_TEMPLATE = os.environ.get(
    "LOCKBOX_PAYLOAD_URL_TEMPLATE",
    "https://payload.lockbox.api.cloud.yandex.net/lockbox/v1/secrets/{secret_id}/payload",
)
YDB_KEY_ENTRY = "YDB_AUTHORIZED_KEY_JSON"
YDB_KEY_PATH = "/tmp/ydb_authorized_key.json"
MAX_ATTEMPTS = 30
SERVICE_KEYS = (
    "LOCKBOX_SECRET_ID",
    "LOCKBOX_METADATA_TOKEN_URL",
    "LOCKBOX_PAYLOAD_URL_TEMPLATE",
)


def log(message):
    print("lockbox-launcher: " + message, file = sys.stderr, flush = True)


def get_json(url, headers):
    request = urllib.request.Request(url, headers = headers)
    with urllib.request.urlopen(request, timeout = 10) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_payload(secret_id):
    token = get_json(
        METADATA_TOKEN_URL,
        {"Metadata-Flavor": "Google"},
    )["access_token"]
    return get_json(
        PAYLOAD_URL_TEMPLATE.format(secret_id = secret_id),
        {"Authorization": "Bearer " + token},
    )


def fetch_with_retry(secret_id):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fetch_payload(secret_id)
        except Exception as error:
            log("attempt {0}/{1} failed: {2!r}".format(attempt, MAX_ATTEMPTS, error))
            time.sleep(min(2 * attempt, 30))
    log("giving up, container will be restarted by docker")
    sys.exit(1)


def entry_value(entry):
    if "textValue" in entry:
        return entry["textValue"]
    return base64.b64decode(entry.get("binaryValue", "")).decode("utf-8")


def stop_on_signal(signum, frame):
    log("got signal {0} before bot start, exiting".format(signum))
    sys.exit(128 + signum)


def main():
    # Пока лаунчер — PID 1, ядро не применяет к нему действие SIGTERM по
    # умолчанию: без обработчика `docker stop` во время ретраев ждал бы SIGKILL.
    signal.signal(signal.SIGTERM, stop_on_signal)
    signal.signal(signal.SIGINT, stop_on_signal)

    if len(sys.argv) < 2:
        log("usage: python -c <launcher> <command> [args...]")
        sys.exit(2)

    secret_id = os.environ.get("LOCKBOX_SECRET_ID", "").strip()
    if not secret_id:
        log("LOCKBOX_SECRET_ID is not set")
        sys.exit(2)

    payload = fetch_with_retry(secret_id)
    env = {key: value for key, value in os.environ.items() if key not in SERVICE_KEYS}
    loaded_keys = []
    for entry in payload.get("entries", []):
        key = entry["key"]
        value = entry_value(entry)
        if key == YDB_KEY_ENTRY:
            with open(YDB_KEY_PATH, "w", encoding = "utf-8") as key_file:
                key_file.write(value)
            os.chmod(YDB_KEY_PATH, 0o600)
            env["YDB_AUTH_KEY_FILE"] = YDB_KEY_PATH
        else:
            env[key] = value
        loaded_keys.append(key)

    log(
        "loaded secret version {0}, keys: {1}".format(
            payload.get("versionId", "?"),
            ", ".join(sorted(loaded_keys)) or "<none>",
        ),
    )
    # exec заменяет процесс: python бота остаётся PID 1 и сам получает SIGTERM
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.execvpe(sys.argv[1], sys.argv[1:], env)


main()
