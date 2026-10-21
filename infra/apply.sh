#!/usr/bin/env bash
# Одна команда для инфраструктуры окружения.
#
#   infra/apply.sh <test|prod> [apply|plan|destroy|output|compose] [доп. аргументы terraform]
#
# По умолчанию — apply. State: infra/state/<env>.tfstate (см. README.md).
# compose — выложить на VM изменённый шаблон docker-compose с текущим тегом образа.
set -euo pipefail

ENV_NAME="${1:-}"
ACTION="${2:-apply}"
if [[ $# -gt 0 ]]; then shift; fi
if [[ $# -gt 0 ]]; then shift; fi

case "$ENV_NAME" in
  test|prod) ;;
  *)
    echo "Использование: $0 <test|prod> [apply|plan|destroy|output|compose] [аргументы terraform]" >&2
    exit 2
    ;;
esac

INFRA_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$INFRA_DIR"

for tool in terraform yc; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Не найден $tool — см. «Предпосылки» в infra/README.md" >&2
    exit 1
  fi
done

# Авторизация провайдера: IAM-токен текущего профиля yc (живёт до 12 часов)
if [[ -z "${YC_TOKEN:-}" ]]; then
  YC_TOKEN="$(yc iam create-token)"
  export YC_TOKEN
fi

# cloud_id/folder_id: envs/<env>.tfvars > TF_VAR_* > активный профиль yc
if [[ -z "${TF_VAR_cloud_id:-}" ]]; then
  TF_VAR_cloud_id="$(yc config get cloud-id 2>/dev/null || true)"
  export TF_VAR_cloud_id
fi
if [[ -z "${TF_VAR_folder_id:-}" ]]; then
  TF_VAR_folder_id="$(yc config get folder-id 2>/dev/null || true)"
  export TF_VAR_folder_id
fi

VAR_FILE="envs/${ENV_NAME}.tfvars"
export TF_VAR_env="$ENV_NAME"
# Отдельный .terraform на окружение, чтобы test и prod не путали backend
export TF_DATA_DIR="${INFRA_DIR}/.terraform/${ENV_NAME}"
mkdir -p state "$TF_DATA_DIR"

terraform init -input=false -reconfigure \
  -backend-config="path=${INFRA_DIR}/state/${ENV_NAME}.tfstate" >/dev/null

case "$ACTION" in
  apply|plan|destroy)
    terraform "$ACTION" -var-file="$VAR_FILE" "$@"
    ;;
  output)
    terraform output "$@"
    ;;
  compose)
    # Доставить изменения шаблона compose на VM, сохранив тег образа,
    # который туда выложил CI. Перед этим нужен `apply`, чтобы обновился output.
    instance_id="$(terraform output -raw instance_id)"
    repo="$(terraform output -raw image_repository)"
    compose_file="$(mktemp)"
    trap 'rm -f "$compose_file"' EXIT
    terraform output -raw docker_compose >"$compose_file"
    # Тег можно передать явно: apply.sh <env> compose <tag> (например после -replace VM)
    current_tag="${1:-}"
    [[ -n "$current_tag" ]] || current_tag="$(
      yc compute instance get --id "$instance_id" --full --format json \
        | python3 -I -c 'import json, sys; print(json.load(sys.stdin)["metadata"].get("docker-compose", ""))' \
        | grep -oE "${repo}:[^\"[:space:]]+" | head -n 1 | sed "s#^${repo}:##" || true
    )"
    if [[ -n "$current_tag" ]]; then
      sed -i -E "s#(${repo}):[^\"[:space:]]+#\\1:${current_tag}#" "$compose_file"
      echo "Сохраняю тег образа с VM: ${current_tag}" >&2
    fi
    yc compute instance update --id "$instance_id" \
      --metadata-from-file docker-compose="$compose_file" >/dev/null
    echo "docker-compose обновлён на ${instance_id}" >&2
    ;;
  *)
    echo "Неизвестное действие: $ACTION (apply|plan|destroy|output|compose)" >&2
    exit 2
    ;;
esac
