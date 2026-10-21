# Окружение prod: боевые боты.
# cloud_id/folder_id по умолчанию берутся из активного профиля yc;
# раскомментируйте, если prod живёт в отдельном каталоге.
# cloud_id  = "b1g..."
# folder_id = "b1g..."

subnet_cidr         = "10.20.0.0/24"
deletion_protection = true

# ID боевой базы YDB: ydb.editor только на неё. Пусто — нужен ключ в Lockbox.
ydb_database_id = ""

# Несекретные переменные бота (секреты и всё остальное — в Lockbox).
bot_environment = {}

# ssh_public_key = "ssh-ed25519 AAAA... you@host"
