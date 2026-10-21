#!/usr/bin/env bash
# Одна команда для инфраструктуры окружения.
#
#   infra/apply.sh <test|prod> [apply|plan|destroy|output] [доп. аргументы terraform]
#
# По умолчанию — apply. State: infra/state/<env>.tfstate (см. README.md).
set -euo pipefail

ENV_NAME="${1:-}"
ACTION="${2:-apply}"
if [[ $# -gt 0 ]]; then shift; fi
if [[ $# -gt 0 ]]; then shift; fi

case "$ENV_NAME" in
  test|prod) ;;
  *)
    echo "Использование: $0 <test|prod> [apply|plan|destroy|output] [аргументы terraform]" >&2
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
  *)
    echo "Неизвестное действие: $ACTION (apply|plan|destroy|output)" >&2
    exit 2
    ;;
esac
