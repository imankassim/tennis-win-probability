# infrastructure

Containers and deployment config (Journey 20): `Dockerfile.backend`,
`Dockerfile.frontend`, `docker-compose.yml`.

## Status

Journey 20 is complete: containers, CI, monitoring (a container health
check plus Journey 19's ops dashboard) and rollback (the model registry,
`pricing/registry.py` + `pricing/rollback_model.py`).

**Honest limitation**: no Docker is available in the environment this
project was developed in (no local `docker` binary — verified, not
assumed). These Dockerfiles and the compose file were written correctly
by inspection and cross-referenced against the real project structure,
but were never built or run locally. The real verification is
`.github/workflows/ci.yml`'s `docker-build` job, which runs on GitHub's
hosted runners (which do have Docker) on every push to `main`: it builds
both images and smoke-tests the backend one (starts the container, polls
`/health` until it responds or the job fails). Check the Actions tab (or
`gh run list`) for the actual, current pass/fail state rather than
trusting this README alone.

## Structure

- `Dockerfile.backend` — the FastAPI app. Boots with the demo fixture
  out of the box; a real deployment mounts real ingested data and a
  promoted pipeline as volumes (see `docker-compose.yml`) rather than
  baking either into the image — matching
  [docs/architecture/charter.md](../docs/architecture/charter.md)'s "no
  automatic model promotion": an image that silently bundled whichever
  artefact happened to be on disk at build time would defeat the point
  of promotion being a deliberate, human-reviewed step.
- `Dockerfile.frontend` — the Next.js dashboard. Two-stage build using
  `next.config.ts`'s `output: "standalone"` (Next's own recommended
  Docker pattern) — the final image copies just the self-contained
  `.next/standalone` bundle plus `.next/static` and `public/`, not the
  full `node_modules` tree. An earlier hand-rolled non-standalone version
  failed CI's docker-build job without a clear enough error to diagnose
  which of several plausible causes it was (no local Docker to
  reproduce against — see the limitation noted above); switching to the
  well-tested standalone pattern was more productive than continuing to
  guess at the bespoke one.
- `docker-compose.yml` — wires both together for local use. No postgres
  service: despite [decision
  3](../docs/decisions/3-postgres-source-of-truth-duckdb-feature-store.md)
  naming PostgreSQL as the eventual source of truth,
  [database/README.md](../database/README.md) is explicit that nothing
  in this codebase executes SQL against a real database yet — adding an
  unused container would be ceremony, not a real dependency.

## Monitoring and rollback

**Monitoring**: `Dockerfile.backend`'s image is polled at `/health` by
the CI smoke test above; a real deployment would wire the same endpoint
into its orchestrator's health/liveness checks. Richer monitoring
(quality, latency, error rates) is Journey 19's `/ops/summary` and
`frontend/src/app/ops` — a dashboard, not a container-level probe, so it
lives in `backend/` and `frontend/` rather than here.

**Rollback**: `pricing/registry.py` records every promoted pipeline
(`pricing/promote_model.py` writes one entry per run, never overwriting
an earlier one), and `pricing/rollback_model.py` switches which promoted
version is active:

```bash
python -m pricing.rollback_model --list        # see every promoted version
python -m pricing.rollback_model <version>     # make one of them active again
```

Deliberately manual, like promotion itself — per
[docs/architecture/governance.md](../docs/architecture/governance.md)'s
"require review for model promotion," a rollback changes what's served
exactly the way a promotion does, so it gets the same deliberate,
human-run treatment, never an automatic trigger.

## Running locally (once Docker is available)

```bash
docker compose -f infrastructure/docker-compose.yml up --build
```

Backend on `http://localhost:8000`, frontend on `http://localhost:3000`.

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`,
sections 10 and 17 (the "courtedge/infrastructure/" line in the intended
repository layout).
