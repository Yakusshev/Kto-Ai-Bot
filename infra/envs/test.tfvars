# Окружение test: тестовые боты, сюда выкладывается первым.
# cloud_id/folder_id по умолчанию берутся из активного профиля yc;
# раскомментируйте, если test живёт в отдельном каталоге.
# cloud_id  = "b1g..."
# folder_id = "b1g..."

subnet_cidr         = "10.10.0.0/24"
deletion_protection = false

# ID тестовой базы YDB (`yc ydb database get <name> --format json | jq -r .id`):
# SA VM получит ydb.editor только на неё, ключ YDB не нужен. Пусто — нужен ключ в Lockbox.
ydb_database_id = ""

# Несекретные переменные бота (секреты и всё остальное — в Lockbox).
bot_environment = {}

# Для отладки по SSH (пользователь yc-user):
# ssh_public_key = "ssh-ed25519 AAAA... you@host"
