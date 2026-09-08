# CourtEdge

CourtEdge is an original in-play tennis probability and pricing research
prototype, inspired by the type of real-time pricing systems used by sports
betting companies. It is not a copy of any real bookmaker's product, brand
or proprietary pricing feed, and it is **not** a real-money trading system —
see [Prototype boundary](#prototype-boundary).

## Research question

> To what extent does a machine-learned in-play win-probability model,
> blended with a transparent point-based Markov chain baseline and refined
> by a learned calibration step, improve probabilistic accuracy and
> calibration compared with the Markov baseline alone and with observed
> historical market prices?

The project starts from a working but deliberately simple replay dashboard,
then builds a searchable match/point catalogue, an API, event
instrumentation and a labelled outcome set. Only once those foundations
exist does it introduce a Markov chain analytic baseline, a machine-learned
probability model, a blended combination, learned calibration, trading
rules, and a bounded, research-only market-comparison layer.

## Scope

**Being built:** a replay and pricing dashboard; a match/point/player
catalogue from permitted public data; a Next.js front end and FastAPI back
end; a PostgreSQL source of truth plus a DuckDB/Parquet feature-and-replay
store; a transparent Markov chain baseline; an ML win-probability model
(XGBoost/LightGBM); a validated blend and learned meta-model; a calibration
layer; a trading-rules layer (margin, price bounds, suspension, staleness);
a bounded, clearly labelled research-only market-comparison layer; and an
evaluation/monitoring layer.

**Not being built:** real-money wagering, payments or settlement; any copy
of a real bookmaker's branding or proprietary feed; a production identity/KYC
platform; unrestricted LLM control of prices or trading rules; an advanced
shot-level/biometric model without sufficient data; automatic retraining or
model promotion without review; ingestion of a paid or restricted-licence
feed; or any output presented as betting advice.

## Architecture

The request path recomputes a probability and indicative price after every
point, through independent analytic and learned estimates that are blended,
calibrated, and finally checked against hard trading rules before anything
is returned:

```mermaid
flowchart TD
    A["Next.js dashboard\nmatch selector - probability chart - price ticker"]
    B["FastAPI application layer\n/probability - /price - /replay - /health"]
    B1["Match state parser"]
    B2["Player context service"]
    B3["Match catalogue service"]
    C["Probability estimation\nMarkov chain (analytic) + ML model (learned),\ncomputed independently"]
    D["Blend\nweighted combination or learned meta-model"]
    E["Calibration\nPlatt scaling / isotonic regression"]
    F["Trading rules & risk controls\nmargin - price bounds - suspension - staleness\n(hard constraints — cannot be overridden)"]
    G["API response\nrequest ID - probability - price - model version - suspended flag"]

    A --> B
    B --> B1 & B2 & B3
    B1 & B2 & B3 --> C
    C --> D --> E --> F --> G --> A
```

A failure in any advanced layer degrades to a simpler, honest method rather
than a fabricated price — e.g. if the ML model is unavailable, the system
serves the Markov-only probability and marks `ml_fallback: true`; if trading
rules themselves fail, pricing is suspended entirely. See
[docs/architecture/deployment.md](docs/architecture/deployment.md) for the
full fallback table.

Data flows through two stores with distinct jobs: **PostgreSQL** is the
transactional source of truth for matches, players, points and outcome
labels; a **DuckDB/Parquet feature-and-replay store**, rebuilt from
PostgreSQL, supports fast point-in-time feature computation. Model training
and calibration fitting run entirely offline, on match-level (never
point-level) splits, and serving loads only versioned artefacts from a model
registry — training never happens inside a live request.

For the full set of views (system context, data architecture, offline
training pipeline, deployment roles, security/governance) see
[docs/architecture/](docs/architecture/).

## Repository structure

```
courtedge/
├── frontend/            # Next.js replay and pricing dashboard
├── backend/             # FastAPI routes and orchestration
├── database/            # schemas, migrations and seeds
├── pricing/
│   ├── baselines/       # primitive 50/50 and score-leader heuristics
│   ├── markov/          # analytic point/game/set/match model
│   ├── ml/               # feature engineering and learned models
│   ├── blend/             # fusion and meta-model
│   └── calibration/       # Platt, isotonic and dynamic calibration
├── trading_rules/        # margin, suspension, staleness, value-flagging
├── experiments/           # reproducible investigations (see REGISTER.md)
├── discarded/              # clean rejected approaches + reasons
├── evaluation/              # outcome labels, metrics and reports
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── scenario_regression/
│   └── data_quality/
├── infrastructure/          # containers and deployment config
└── docs/
    ├── architecture/        # system context, logical, data, offline, deployment, governance
    ├── decisions/            # architecture decision records (ADR 1, 2, 3 ...)
    ├── model_cards/
    ├── data_sheets/          # data provenance, permitted-data rules
    └── ethics/
```

## Documentation

| Document | Purpose |
|---|---|
| [docs/architecture/charter.md](docs/architecture/charter.md) | Full project charter: research question, in/out-of-scope, requirements, success measures. |
| [docs/architecture/](docs/architecture/) | System context, logical, data, offline-training, deployment and governance architectures. |
| [docs/decisions/](docs/decisions/) | Architecture decision records (ADR 1, 2, 3 ...; plain numbering, never zero-padded). |
| [docs/data_sheets/data_provenance.md](docs/data_sheets/data_provenance.md) | Approved data sources, licences and permitted-data rules. |
| [experiments/REGISTER.md](experiments/REGISTER.md) | The full planned experiment catalogue (EXP1, EXP2, ... EXP51; plain numbering) with status. |
| [docs/architecture/risk_register.md](docs/architecture/risk_register.md) | Known risks, assumptions and mitigations. |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Journey roadmap, work packages, stage decision gates, testing matrix. |
| [docs/REFERENCES.md](docs/REFERENCES.md) | Academic and technical sources behind the modelling approach. |
| [docs/CourtEdge_Architecture_and_Task_Definition.docx](docs/CourtEdge_Architecture_and_Task_Definition.docx) | The original, full source specification this repository implements. |

## Running it locally

The scenario library (`/`) works standalone on scripted mock data:

```bash
cd frontend
npm install
npm run dev
```

To also browse real matches (`/matches`), run the backend alongside it:

```bash
python -m uvicorn backend.main:app --reload
```

The backend serves a small synthetic demo match out of the box; point it
at real ingested data with `COURTEDGE_DATA_DIR` — see
[backend/README.md](backend/README.md) and
[database/README.md](database/README.md).

## Project status

**Journeys 1–6 are complete, in order.** Journey 10 (context features) was
then built ahead of schedule by mistake — corrected here rather than
hidden; the work itself is real and tested, just out of sequence. Journeys
7-9 (instrumentation, evaluation, Markov baseline) are being filled in now
before continuing past 10.

Done so far:

- Repository scaffold, project charter, all architecture views, the
  decision records, the experiment register, data provenance rules and the
  risk register.
- A static Next.js replay dashboard (`frontend/`) running on two scripted
  mock matches, with all four target page states reachable: loading,
  success, error (unknown match), and a suspended quote mid-replay.
- The primitive baselines — always-50/50 and the current-score-leader
  heuristic (`EXP1`, `EXP2`, in `pricing/baselines/`) — as the weak,
  measurable floor every later component must clear.
- The data foundation (`database/`): a PostgreSQL schema for matches,
  players, points and outcome labels, and an ingestion pipeline for the
  [Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject)
  (the originally-named data source had been removed from GitHub — see
  [decision 9](docs/decisions/9-match-charting-project-data-source.md)),
  run against real data: 183 confirmed match outcomes, 7 incomplete charts
  correctly quarantined instead of guessed at.
- A FastAPI backend (`backend/`) exposing `/health`, `GET /matches`,
  `/replay/{match_id}` and `/probability`, matching the documented
  response contract exactly, plus a real match-state parser for
  break-point detection. Uses the score-leader heuristic as a stand-in
  estimator until the Markov chain exists.
- The frontend is wired to it: `/matches` browses and filters real
  ingested matches, replayed through the same components as the scenario
  library, which stays separate (mock data) since it demonstrates page
  states — suspension — a completed match archive can't produce.

- **(Journey 10, early)** Deterministic context features
  (`backend/context_features.py`): recent form, surface record and
  head-to-head, computed entirely from our own ingested match archive with
  a strict no-look-ahead cutoff. Player ranking remains unsourced —
  deferred until the ML feature set needs it.

Next: **Journey 7 — instrumentation** (quote event logging; request IDs
and model version are already in the `/probability` response), then
**Journey 8 — evaluation** (Brier score, log-loss, latency measurement)
and **Journey 9 — the Markov baseline**, before returning to Journey 10's
remaining scope (ranking) and Journey 11 onward.

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full 21-journey plan and the
stage decision gates each journey must pass before the next begins.

## Prototype boundary

This is a technical learning and portfolio project. It does not constitute
a compliant real-money betting system, and no part of it should be deployed
against real markets or real customers without full legal, regulatory and
responsible-gambling review.
