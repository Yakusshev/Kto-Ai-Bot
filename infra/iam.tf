# -----------------------------------------------------------------------------
# SA виртуальной машины: pull образа, чтение Lockbox, запись логов, (опц.) YDB.
# Pull и Lockbox выданы на конкретный ресурс; logging.writer и ydb.editor —
# на каталог (у провайдера нет IAM-ресурсов уровнем ниже).
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

resource "yandex_resourcemanager_folder_iam_member" "vm_ydb" {
  count     = var.grant_ydb_editor ? 1 : 0
  folder_id = var.ydb_folder_id == "" ? var.folder_id : var.ydb_folder_id
  role      = "ydb.editor"
  member    = "serviceAccount:${yandex_iam_service_account.vm.id}"
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
