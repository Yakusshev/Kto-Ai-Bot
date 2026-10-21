locals {
  name = "kto-ai-bot-${var.env}"

  labels = {
    project = "kto-ai-bot"
    env     = var.env
  }

  image_repository = "cr.yandex/${yandex_container_registry.this.id}/${var.image_name}"
  bot_image        = "${local.image_repository}:${var.image_tag}"

  # Лаунчер передаётся через `python -c`, то есть целиком живёт в metadata
  # (никаких файлов на хосте). `$` экранируем от интерполяции docker-compose.
  launcher_source = replace(file("${path.module}/templates/lockbox_launcher.py"), "$", "$$")

  docker_compose = templatefile("${path.module}/templates/docker-compose.yaml.tftpl", {
    bot_image = local.bot_image
    bot_environment = jsonencode(merge(var.bot_environment, {
      LOCKBOX_SECRET_ID = yandex_lockbox_secret.bot.id
      BOT_ENV           = var.env
    }))
    bot_entrypoint  = jsonencode(concat(["python", "-c", local.launcher_source], var.bot_command))
    fluentbit_image = var.fluentbit_image
    fluentbit_command = jsonencode([
      "-i", "forward",
      "-p", "listen=0.0.0.0",
      "-p", "port=24224",
      "-o", "yc-logging",
      "-m", "*",
      "-p", "group_id=${yandex_logging_group.bot.id}",
      "-p", "message_key=log",
      "-p", "default_level=INFO",
      "-p", "resource_type=kto-ai-bot",
      "-p", "resource_id=${local.name}",
      "-p", "authorization=instance-service-account",
      "-f", "1",
    ])
  })
}
