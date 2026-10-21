terraform {
  required_version = ">= 1.5.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.130.0, < 1.0.0"
    }
  }

  # Локальный state, отдельный файл на окружение: путь передаёт apply.sh
  # через `terraform init -backend-config=path=state/<env>.tfstate`.
  # Почему не S3-бакет — см. README.md, раздел «State».
  backend "local" {}
}

# Аутентификация: YC_TOKEN (apply.sh берёт его из `yc iam create-token`),
# cloud_id/folder_id — из переменных.
provider "yandex" {
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}
