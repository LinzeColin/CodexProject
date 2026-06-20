# Docker Infrastructure

Docker Compose service definitions and Dockerfiles live here. The root `docker-compose.yml` defines:

- `postgres`: local PostgreSQL system-of-record runtime for G1/G2 verification.
- `migrate`: one-shot schema migration container under the `worker` profile.
- `worker`: EEI background worker supervisor under the `worker` profile.

The default MVP process-manager binding for the worker is Docker Compose. It runs the same `apps.worker` supervisor used by the Makefile operator commands and waits for PostgreSQL health plus successful migrations before starting.

## PostgreSQL

```bash
make db-up
docker compose ps postgres
docker compose logs --tail=120 postgres
```

Stop local database services with:

```bash
make db-down
```

## Worker Supervisor

Start the production-style local worker binding:

```bash
docker compose --profile worker up -d worker
```

Inspect runtime state:

```bash
docker compose ps worker
docker compose logs --tail=200 worker
```

Stop only the worker:

```bash
docker compose --profile worker stop worker
```

The `migrate` service runs `scripts/migrate.py upgrade` before `worker`. The worker healthcheck runs `python -m apps.worker.app.main health` inside the container. The default database connection is:

```text
postgresql://eei:change-me-local-only@postgres:5432/eei
```

Override it with `EEI_DOCKER_DATABASE_URL` for non-local runtimes. Do not use the local default password outside local development.

## Validation And Rollback

Validate this binding without starting containers:

```bash
make validate-worker-deployment
```

Rollback this deployment binding by stopping the worker and reverting `docker-compose.yml`, `infra/docker/worker.Dockerfile` and the generated A206 evidence artifact, then regenerating release artifacts and rerunning `make verify`.

Acceptance IDs: A005, A206, A209
