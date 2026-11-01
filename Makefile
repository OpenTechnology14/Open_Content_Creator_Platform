# Open Content Creator Platform — convenience targets.
# Run `make help` for the list.

.PHONY: help up up-with-graphics up-with-automation down logs ps build clean \
        backup healthcheck migrate test test-acceptance test-obs deploy-do lint verify proposal-report

help:
	@echo "Common targets:"
	@echo "  make up                  # bring up core stack (postgres, redis, minio, fastapi, prom/loki/grafana)"
	@echo "  make up-with-graphics    # core + NodeCG"
	@echo "  make up-with-automation  # core + n8n"
	@echo "  make down                # stop everything"
	@echo "  make logs                # tail all logs"
	@echo "  make ps                  # show container status"
	@echo "  make build               # rebuild local images"
	@echo "  make migrate             # run Postgres migrations"
	@echo "  make test                # run the offline test suite"
	@echo "  make verify ARGS=--list   # inspect CI-derived local gates and not-run checks"
	@echo "  make proposal-report     # JSON queue counts, model assignments and lane coverage"
	@echo "  python3 scripts/testing/generate_docs.py --check  # generated policy/registry gate"
	@echo "  make test-acceptance     # run the acceptance harness (needs Docker; P-016)"
	@echo "  make test-obs            # verify OBS WebSocket connectivity"
	@echo "  make healthcheck         # smoke-test running services"
	@echo "  make backup              # run the backup script"
	@echo "  make deploy-do DROPLET=  # deploy to DigitalOcean droplet"
	@echo "  make lint                # ruff lint Python"

up:
	docker compose up -d

up-with-graphics:
	docker compose --profile graphics up -d

up-with-automation:
	docker compose --profile automation up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

build:
	docker compose build

migrate:
	@./scripts/setup/postgres_migrate.sh

test:
	@python3 -m pytest -q

verify:
	@python3 scripts/testing/verify.py $(ARGS)

proposal-report:
	@python3 scripts/testing/proposal_report.py $(ARGS)

test-acceptance:
	@python3 -m pytest -m live -q

test-obs:
	@python3 scripts/setup/test_obs_websocket.py

healthcheck:
	@./scripts/maintenance/healthcheck.sh

backup:
	@./scripts/maintenance/backup.sh

deploy-do:
	@test -n "$(DROPLET)" || (echo "usage: make deploy-do DROPLET=<host>" && exit 1)
	@DROPLET=$(DROPLET) ./scripts/deploy/deploy-do.sh

lint:
	@ruff check modules/ scripts/

clean:
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
