# Используются CI (задача D3): см. README.md, раздел «Контракт для CI».

output "env" {
  value = var.env
}

output "registry_id" {
  description = "ID Container Registry."
  value       = yandex_container_registry.this.id
}

output "image_repository" {
  description = "Репозиторий образа бота без тега: cr.yandex/<registry_id>/kto-ai-bot."
  value       = local.image_repository
}

output "docker_compose" {
  description = "Актуальный compose по шаблону (тег image_tag). Применяет `apply.sh <env> compose`, сохраняя тег с VM."
  value       = local.docker_compose
}

output "instance_id" {
  value = yandex_compute_instance.bot.id
}

output "instance_name" {
  value = yandex_compute_instance.bot.name
}

output "instance_public_ip" {
  value = yandex_compute_instance.bot.network_interface[0].nat_ip_address
}

output "lockbox_secret_id" {
  value = yandex_lockbox_secret.bot.id
}

output "lockbox_secret_name" {
  value = yandex_lockbox_secret.bot.name
}

output "log_group_id" {
  value = yandex_logging_group.bot.id
}

output "vm_service_account_id" {
  value = yandex_iam_service_account.vm.id
}

output "ci_service_account_id" {
  description = "SA для CI. Ключ выпускается вручную (README.md)."
  value       = yandex_iam_service_account.ci.id
}
