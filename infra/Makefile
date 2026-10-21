# Обёртка над apply.sh / push-secrets.sh.
#   make -C infra apply ENV=test
#   make -C infra plan ENV=prod
#   make -C infra secrets ENV=test FILE=../.env.test [YDB_KEY=../credentials/ydb_authorized_key.json]
#   make -C infra output ENV=test
#   make -C infra check        # fmt -check + validate, облако не нужно

ENV ?= test
ARGS ?=

.PHONY: apply plan destroy output secrets check

apply plan destroy output:
	./apply.sh $(ENV) $@ $(ARGS)

secrets:
	@test -n "$(FILE)" || (echo "Укажите FILE=<путь к .env>" >&2; exit 2)
	./push-secrets.sh $(ENV) $(FILE) $(YDB_KEY)

check:
	terraform fmt -check -recursive
	TF_DATA_DIR=.terraform/check terraform init -backend=false -input=false >/dev/null
	TF_DATA_DIR=.terraform/check terraform validate
