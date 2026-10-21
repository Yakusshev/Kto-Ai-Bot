# --- Container Registry -------------------------------------------------------

resource "yandex_container_registry" "this" {
  name   = local.name
  labels = local.labels
}

# --- Lockbox ------------------------------------------------------------------
# Только «контейнер» секрета. Значения заливаются вне Terraform
# (infra/push-secrets.sh или `yc lockbox secret add-version`) и в state не попадают.

resource "yandex_lockbox_secret" "bot" {
  name                = local.name
  description         = "Переменные окружения бота ${local.name}. Значения вне репозитория и state."
  labels              = local.labels
  deletion_protection = var.deletion_protection
}

# --- Cloud Logging ------------------------------------------------------------

resource "yandex_logging_group" "bot" {
  name             = local.name
  folder_id        = var.folder_id
  retention_period = var.log_retention
  labels           = local.labels
}

# --- Сеть ---------------------------------------------------------------------

resource "yandex_vpc_network" "this" {
  name   = local.name
  labels = local.labels
}

resource "yandex_vpc_subnet" "this" {
  name           = local.name
  zone           = var.zone
  network_id     = yandex_vpc_network.this.id
  v4_cidr_blocks = [var.subnet_cidr]
  labels         = local.labels
}

# Боту (long polling) нужен только исходящий трафик. Входящий — лишь SSH,
# и только если задан ssh_public_key.
resource "yandex_vpc_security_group" "bot" {
  name       = local.name
  network_id = yandex_vpc_network.this.id
  labels     = local.labels

  egress {
    description    = "Исходящий: Telegram, LLM API, YDB, Lockbox, Logging, Registry"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.ssh_public_key == "" ? [] : [1]
    content {
      description    = "SSH для отладки"
      protocol       = "TCP"
      port           = 22
      v4_cidr_blocks = var.ssh_allowed_cidrs
    }
  }
}
