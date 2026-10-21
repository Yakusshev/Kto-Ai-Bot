data "yandex_compute_image" "coi" {
  family = "container-optimized-image"
}

resource "yandex_compute_instance" "bot" {
  name        = local.name
  hostname    = local.name
  description = "Telegram-бот ${local.name}: COI, docker-compose из metadata"
  platform_id = var.platform_id
  zone        = var.zone
  labels      = local.labels

  service_account_id        = yandex_iam_service_account.vm.id
  allow_stopping_for_update = true

  resources {
    cores         = var.cores
    core_fraction = var.core_fraction
    memory        = var.memory_gb
  }

  # Бот должен работать постоянно: прерываемая VM не подходит
  scheduling_policy {
    preemptible = false
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.coi.id
      type     = var.disk_type
      size     = max(var.disk_size_gb, data.yandex_compute_image.coi.min_disk_size)
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.this.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.bot.id]
  }

  metadata = merge(
    {
      docker-compose     = local.docker_compose
      serial-port-enable = "0"
    },
    var.ssh_public_key == "" ? {} : {
      user-data = templatefile("${path.module}/templates/user-data.yaml.tftpl", {
        ssh_public_key = var.ssh_public_key
      })
    },
  )

  # Без прав на pull/Lockbox/Logging контейнеры стартуют с ошибками
  depends_on = [
    yandex_container_registry_iam_binding.vm_puller,
    yandex_lockbox_secret_iam_binding.vm_payload_viewer,
    yandex_resourcemanager_folder_iam_member.vm_log_writer,
    yandex_resourcemanager_folder_iam_member.vm_ydb,
  ]
}
