#!/usr/bin/env bash
# Выкладка образа на VM окружения: подменяет тег образа бота в metadata
# docker-compose (infra/README.md, «Контракт для CI»). COI сам пересоздаст
# контейнер: старый получит SIGTERM и до stop_grace_period на остановку.
#
#   .github/scripts/deploy-vm.sh <instance_id> <image_repository> <tag>
#
# Работает и локально (нужны yc и jq), например для ручного отката.
# В GitHub Actions пишет в $GITHUB_OUTPUT:
#   previous_tag — тег, который был на VM до выкладки (для отката);
#   changed      — true, если metadata изменилась (иначе COI ничего не перезапустит).
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Использование: $0 <instance_id> <image_repository> <tag>" >&2
  exit 2
fi
instance_id="$1"
repo="$2"
tag="$3"

output() {
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "$1=$2" >> "$GITHUB_OUTPUT"
  fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
compose="$work/compose.yaml"

get_compose() {
  yc compute instance get --id "$instance_id" --full --format json \
    | jq -r '.metadata["docker-compose"] // empty'
}

current_tag() {
  grep -oE "${repo}:[^\"[:space:]]+" "$1" | head -n 1 | sed "s#^${repo}:##" || true
}

get_compose > "$compose"
if [[ ! -s "$compose" ]]; then
  echo "::error::В metadata VM ${instance_id} нет ключа docker-compose" >&2
  exit 1
fi

previous="$(current_tag "$compose")"
if [[ -z "$previous" ]]; then
  echo "::error::В docker-compose на VM нет образа ${repo}:<tag>. Проверьте переменную YC_IMAGE_REPOSITORY" >&2
  exit 1
fi
output previous_tag "$previous"
echo "На VM сейчас: ${repo}:${previous}"

if [[ "$previous" == "$tag" ]]; then
  echo "Тег ${tag} уже выложен, metadata не меняю"
  output changed false
  exit 0
fi

sed -i -E "s#(${repo}):[^\"[:space:]]+#\\1:${tag}#" "$compose"
yc compute instance update --id "$instance_id" \
  --metadata-from-file docker-compose="$compose" >/dev/null

get_compose > "$work/applied.yaml"
applied="$(current_tag "$work/applied.yaml")"
if [[ "$applied" != "$tag" ]]; then
  echo "::error::После update на VM тег '${applied}', ожидался '${tag}'" >&2
  exit 1
fi
output changed true
echo "Выложено: ${repo}:${previous} → ${repo}:${tag}"
