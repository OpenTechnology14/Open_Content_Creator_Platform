# infrastructure — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

Automated for deployment and maintenance; networking is manual by nature.

**Desktop users start with the [app launch guide](desktop-setup.md).** The commands below are
for selected infrastructure features; Docker/WSL and `make up` are not prerequisites to open
Stream Extend or Creator Extend. Defer container blockers while using the local setup panel.

## Commands

```bash
make up          # local core stack
make deploy-do DROPLET=<host>    # scripts/deploy/deploy-do.sh
make backup                      # scripts/maintenance/backup.sh
make healthcheck                 # scripts/maintenance/healthcheck.sh
make down                        # stop everything
```

For optional Windows module prerequisites after app launch, source-checkout users can run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -InstallDesktopApps
```

This bootstraps Python, optionally installs OBS/FFmpeg, installs an explicit module preset and
records dependency plus capture-device diagnostics. `-InstallDesktopApps` means OBS/FFmpeg;
it does not install or open either Extend app, install Docker, or configure cloud infrastructure,
accounts, game clients, vendor-specific drivers or OBS scenes.

## DigitalOcean

The cloud overlay is additive:

```bash
docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml up -d
```

It removes local Postgres/Redis containers in favour of managed services, adds droplet-appropriate
resource limits, and sets `unless-stopped` restart policies.

## Not automated

- **Tailscale.** Installing and authenticating each node is manual — see [manual.md](manual.md).
  Auth keys are ephemeral and regenerated per node, so this is not scriptable in a committed file.
- **Droplet provisioning.** `deploy-do.sh` deploys to a droplet you have already created.
- **Kubernetes.** Explicitly out of scope. See [manual.md](manual.md).

> **Status caveat.** `docs/AUDIT.md` lists open P0 gates on this module's surface: weak fallback
> secrets, broad CORS, public database/cache port mappings, and six Compose-referenced values
> missing from `.env.example`. Do not run the cloud overlay on a public droplet until those are closed.

## CI/CD

Workflows belong in `.github/workflows/`:

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | every PR | Lint (ruff, prettier), run `tests/`, validate compose files |
| `build-images.yml` | tagged release | Build per-module images, push to GHCR or DOCR |
| `deploy-do.yml` | push to `main` | Roll the droplet — pull images and `docker compose up -d` |

GitHub secrets required: `DOCR_TOKEN` (or `GHCR_TOKEN`), `DO_SSH_KEY`, `DO_DROPLET_IP`,
`TAILSCALE_AUTHKEY` (ephemeral, scoped).

> **Current state, per `docs/AUDIT.md`:** CI is a placeholder — "Ruff is allowed to fail and pytest
> only prints a placeholder message", and `tests/` has no automated suite. `ci.yml` therefore
> gates nothing today. Closing that is P0 gate #2.

**Do not deploy from `main`** until the workflow has been tested on a separate branch against a
non-production droplet.

## Kubernetes — the deferral test

The roadmap lists Kubernetes as later-stage. Defer until **all four** are true:

1. More than one GPU worker, needing scheduled placement.
2. Services with genuinely different scaling needs (a burst-render pool scaling independently of FastAPI).
3. A second person who must deploy without learning your bespoke Compose setup.
4. Downtime during deploys is no longer acceptable.

If even one is false, stay on Compose. The complexity tax is real and it is paid every day.

When the test does pass: DigitalOcean **DOKS** is the easiest entry, Helm charts per module
(skeleton at `digitalocean/helm/`, deferred), Argo CD for GitOps (deferred). Record the decision in
[`docs/architecture/k8s-decision.md`](../../../docs/architecture/k8s-decision.md).

## Backups

```bash
make backup    # scripts/maintenance/backup.sh
```

Covers **Postgres + MinIO**. Extend it to cover the state that is not in either:

- Grafana dashboard JSON export
- Prometheus rule files (in git, but back up the active state)
- n8n workflow export
- OBS profile + scene collection — periodic re-export from the workstation

The runbook is [`docs/architecture/disaster-recovery.md`](../../../docs/architecture/disaster-recovery.md).

**Test recovery quarterly.** A backup you have never restored is a hope, not a backup.


Use [à la carte module setup](module-selection.md) to list modules, preview dependencies and install selected Python requirements on Mac/Windows. Service, driver and application installation remains separate.
