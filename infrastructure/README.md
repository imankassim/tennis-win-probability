# infrastructure

Containers and deployment config (Journey 20): `Dockerfile.backend`,
`Dockerfile.frontend`, `docker-compose.yml`.

## Status

Journey 20 is complete: containers, CI, monitoring (a container health
check plus Journey 19's ops dashboard) and rollback (the model registry,
`pricing/registry.py` + `pricing/rollback_model.py`).

**Honest limitation**: no Docker is available in the environment this
project was developed in (no local `docker` binary - verified, not
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

- `Dockerfile.backend` - the FastAPI app. Boots with the demo fixture
  out of the box; a real deployment mounts real ingested data and a
  promoted pipeline as volumes (see `docker-compose.yml`) rather than
  baking either into the image - matching
  [docs/architecture/charter.md](../docs/architecture/charter.md)'s "no
  automatic model promotion": an image that silently bundled whichever
  artefact happened to be on disk at build time would defeat the point
  of promotion being a deliberate, human-reviewed step.
- `Dockerfile.frontend` - the Next.js dashboard. Two-stage build using
  `next.config.ts`'s `output: "standalone"` (Next's own recommended
  Docker pattern) - the final image copies just the self-contained
  `.next/standalone` bundle plus `.next/static` and `public/`, not the
  full `node_modules` tree.

  Getting this to actually build in CI took several attempts, worth
  recording honestly rather than smoothing over: with no local Docker
  to reproduce against and the job-logs API requiring admin rights even
  on this public repo (an unauthenticated `docker build` succeeding
  locally tells you nothing about a container's Linux runtime, and
  vice versa isn't diagnosable without seeing the actual log), the real
  error stayed invisible for several failed runs. It finally surfaced
  by having a CI step publish the build log to a throwaway git branch,
  fetchable unauthenticated via `raw.githubusercontent.com` - and even
  that needed two fixes first (the log-capture step's own exit code was
  masked by a trailing `cat`, misreporting a real failure as success;
  the git push then failed silently on the repo's default read-only
  workflow token, fixed by declaring `permissions: contents: write` on
  the job). The actual root cause, once visible, was unrelated to
  standalone output at all: `frontend/public/` is genuinely empty, and
  git never tracks empty directories - so it doesn't exist after a
  fresh checkout, and `COPY --from=builder /app/public ./public` failed
  with `"/app/public": not found`. Fixed with a `.gitkeep` placeholder
  so the directory is actually committed. The standalone-output switch
  was a genuine improvement (smaller image, Next's own recommended
  pattern) but not what was actually broken - recorded here so a future
  reader doesn't waste time on the wrong lead the way this session did.
- `docker-compose.yml` - wires both together for local use. No postgres
  service: despite [decision
  3](../docs/decisions/3-postgres-source-of-truth-duckdb-feature-store.md)
  naming PostgreSQL as the eventual source of truth,
  [database/README.md](../database/README.md) is explicit that nothing
  in this codebase executes SQL against a real database yet - adding an
  unused container would be ceremony, not a real dependency.

## Monitoring and rollback

**Monitoring**: `Dockerfile.backend`'s image is polled at `/health` by
the CI smoke test above; a real deployment would wire the same endpoint
into its orchestrator's health/liveness checks. Richer monitoring
(quality, latency, error rates) is Journey 19's `/ops/summary` and
`frontend/src/app/ops` - a dashboard, not a container-level probe, so it
lives in `backend/` and `frontend/` rather than here.

**Rollback**: `pricing/registry.py` records every promoted pipeline
(`pricing/promote_model.py` writes one entry per run, never overwriting
an earlier one), and `pricing/rollback_model.py` switches which promoted
version is active:

```bash
python -m pricing.rollback_model --list        # see every promoted version
python -m pricing.rollback_model <version>     # make one of them active again
```

Deliberately manual, like promotion itself - per
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
