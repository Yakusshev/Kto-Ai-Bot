variable "env" {
  description = "Окружение: test или prod. Входит в имена ресурсов kto-ai-bot-<env>."
  type        = string

  validation {
    condition     = contains(["test", "prod"], var.env)
    error_message = "env должен быть test или prod."
  }
}

variable "cloud_id" {
  description = "ID облака. apply.sh подставляет `yc config get cloud-id`, если не задано в envs/<env>.tfvars."
  type        = string
}

variable "folder_id" {
  description = "ID каталога, где создаются ресурсы окружения. apply.sh подставляет `yc config get folder-id`, если не задано."
  type        = string
}

variable "zone" {
  description = "Зона доступности VM и подсети."
  type        = string
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  description = "CIDR подсети окружения."
  type        = string
  default     = "10.10.0.0/24"
}

# --- VM ---

variable "platform_id" {
  description = "Платформа VM."
  type        = string
  default     = "standard-v3"
}

variable "cores" {
  description = "vCPU VM (минимум для standard-v3 — 2)."
  type        = number
  default     = 2
}

variable "core_fraction" {
  description = "Гарантированная доля vCPU, %. 20 — минимальная и самая дешёвая."
  type        = number
  default     = 20
}

variable "memory_gb" {
  description = "RAM VM, ГБ."
  type        = number
  default     = 1
}

variable "disk_size_gb" {
  description = "Желаемый размер загрузочного диска, ГБ (не меньше минимума образа COI)."
  type        = number
  default     = 30
}

variable "disk_type" {
  description = "Тип загрузочного диска."
  type        = string
  default     = "network-hdd"
}

variable "ssh_public_key" {
  description = "Публичный SSH-ключ для пользователя yc-user (для отладки). Пусто — SSH-доступа нет."
  type        = string
  default     = ""
}

variable "ssh_allowed_cidrs" {
  description = "Откуда разрешён SSH (только если задан ssh_public_key)."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# --- Контейнеры ---

variable "image_name" {
  description = "Имя репозитория образа бота в Container Registry."
  type        = string
  default     = "kto-ai-bot"
}

variable "image_tag" {
  description = "Тег образа только для первого создания VM. Дальше тег в metadata ведёт CI (см. README)."
  type        = string
  default     = "latest"
}

variable "bot_command" {
  description = "Команда запуска бота внутри образа (её exec'ает Lockbox-лаунчер)."
  type        = list(string)
  default     = ["python", "main.py"]
}

variable "stop_grace_period" {
  description = "Сколько docker ждёт после SIGTERM до SIGKILL. Должно покрывать самый долгий ответ LLM."
  type        = string
  default     = "60s"
}

variable "bot_environment" {
  description = "Несекретные переменные окружения бота. Записи Lockbox имеют приоритет."
  type        = map(string)
  default     = {}
}

variable "fluentbit_image" {
  description = "Образ Fluent Bit с плагином Yandex Cloud Logging."
  type        = string
  default     = "cr.yandex/yc/fluent-bit-plugin-yandex:v2.1.1-fluent-bit-2.1.7"
}

# --- Логи и доступы ---

variable "log_retention" {
  description = "Срок хранения логов в log group."
  type        = string
  default     = "168h"
}

variable "ydb_database_id" {
  description = "ID базы YDB этого окружения (`yc ydb database get <name>`). Если задан, SA VM получает ydb.editor только на эту базу и ходит в неё по metadata-токену без файла ключа. Пусто — роль не выдаётся, ключ обязателен (запись YDB_AUTHORIZED_KEY_JSON в Lockbox)."
  type        = string
  default     = ""
}

variable "deletion_protection" {
  description = "Защита Lockbox-секрета от удаления (рекомендуется для prod)."
  type        = bool
  default     = false
}
