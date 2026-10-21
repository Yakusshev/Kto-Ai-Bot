# -----------------------------------------------------------------------------
# SA виртуальной машины: pull образа, чтение Lockbox, запись логов, (опц.) YDB.
# Pull, Lockbox и YDB выданы на конкретный ресурс; logging.writer — на каталог
# (у провайдера нет IAM-ресурса на уровне log group).
# -----------------------------------------------------------------------------
resource "yandex_iam_service_account" "vm" {
  name        = "${local.name}-vm"
  description = "VM ${local.name}: pull из registry, чтение Lockbox, запись в Cloud Logging"
}

resource "yandex_container_registry_iam_binding" "vm_puller" {
  registry_id = yandex_container_registry.this.id
  role        = "container-registry.images.puller"
  members     = ["serviceAccount:${yandex_iam_service_account.vm.id}"]
}

resource "yandex_lockbox_secret_iam_binding" "vm_payload_viewer" {
  secret_id = yandex_lockbox_secret.bot.id
  role      = "lockbox.payloadViewer"
  members   = ["serviceAccount:${yandex_iam_service_account.vm.id}"]
}

# У провайдера нет IAM-ресурса на уровне log group, поэтому роль на каталог.
# logging.writer даёт только запись логов, читать или удалять их SA не может.
resource "yandex_resourcemanager_folder_iam_member" "vm_log_writer" {
  folder_id = var.folder_id
  role      = "logging.writer"
  member    = "serviceAccount:${yandex_iam_service_account.vm.id}"
}

# Роль только на базу своего окружения: test-VM не должна видеть prod-YDB,
# даже если оба окружения в одном каталоге.
resource "yandex_ydb_database_iam_member" "vm_ydb" {
  count       = var.ydb_database_id == "" ? 0 : 1
  database_id = var.ydb_database_id
  role        = "ydb.editor"
  member      = "serviceAccount:${yandex_iam_service_account.vm.id}"
}

# -----------------------------------------------------------------------------
# SA для CI-деплоя (задача D3): push образа и обновление metadata VM.
# Ключ этого SA Terraform НЕ создаёт (чтобы он не попал в state) —
# выпуск описан в README.md.
# -----------------------------------------------------------------------------
resource "yandex_iam_service_account" "ci" {
  name        = "${local.name}-ci"
  description = "CI-деплой ${local.name}: push в registry и обновление VM"
}

resource "yandex_container_registry_iam_binding" "ci_pusher" {
  registry_id = yandex_container_registry.this.id
  role        = "container-registry.images.pusher"
  members     = ["serviceAccount:${yandex_iam_service_account.ci.id}"]
}

# compute.editor только на одну VM, а не на каталог
resource "yandex_compute_instance_iam_binding" "ci_editor" {
  instance_id = yandex_compute_instance.bot.id
  role        = "compute.editor"
  members     = ["serviceAccount:${yandex_iam_service_account.ci.id}"]
}

# Изменение VM с привязанным SA требует права «использовать» этот SA
resource "yandex_iam_service_account_iam_binding" "ci_uses_vm_sa" {
  service_account_id = yandex_iam_service_account.vm.id
  role               = "iam.serviceAccounts.user"
  members            = ["serviceAccount:${yandex_iam_service_account.ci.id}"]
}

# Проверка после выкладки читает логи контейнера (.github/scripts/verify-deploy.sh).
# Роль только на log group окружения: в логах переписка, и ключ test-CI не должен
# читать prod, даже если оба окружения в одном каталоге. В провайдере нет IAM-ресурса
# для log group, а в платформе он есть, поэтому выдаём через yc (apply.sh его требует).
resource "terraform_data" "ci_log_reader" {
  input = {
    log_group_id = yandex_logging_group.bot.id
    sa_id        = yandex_iam_service_account.ci.id
  }

  provisioner "local-exec" {
    command = "yc logging group add-access-binding --id ${self.input.log_group_id} --role logging.reader --service-account-id ${self.input.sa_id}"
  }

  provisioner "local-exec" {
    when       = destroy
    on_failure = continue
    command    = "yc logging group remove-access-binding --id ${self.input.log_group_id} --role logging.reader --service-account-id ${self.input.sa_id}"
  }
}

# Только prod: CI берёт из test-registry образ с тегом tested-<sha> (тот же digest,
# что прошёл тестовых ботов) и копирует его к себе. Нужен pull из чужого registry.
# Ресурс в state prod, а registry принадлежит state test, поэтому не authoritative
# binding (он затёр бы puller у SA VM test), а точечный access binding через yc.
resource "terraform_data" "ci_promote_puller" {
  count = var.promote_from_registry_id == "" ? 0 : 1

  input = {
    registry_id = var.promote_from_registry_id
    sa_id       = yandex_iam_service_account.ci.id
  }

  provisioner "local-exec" {
    command = "yc container registry add-access-binding --id ${self.input.registry_id} --role container-registry.images.puller --service-account-id ${self.input.sa_id}"
  }

  provisioner "local-exec" {
    when       = destroy
    on_failure = continue
    command    = "yc container registry remove-access-binding --id ${self.input.registry_id} --role container-registry.images.puller --service-account-id ${self.input.sa_id}"
  }
}
