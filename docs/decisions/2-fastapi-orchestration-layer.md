# 2. Use FastAPI as the backend orchestration layer

- Status: Accepted
- Date: 2026-09-08

## Context

The system needs a controlled API boundary exposing `/probability`,
`/price`, `/replay` and `/health`, validating inputs and orchestrating the
match-state parser, player-context service, match-catalogue service, the
Markov and ML estimators, the blend, calibration and trading-rules layers
(logical architecture, section 6). The wider modelling stack (Markov, ML
via XGBoost/LightGBM, calibration) is Python-native, so the orchestration
layer should be too, to avoid a cross-language boundary in the hot request
path.

## Decision

Use Python with FastAPI for the application layer.

## Consequences

- FastAPI's request/response typing gives the response contract (request
  ID, model version, fallback/suspended flags) enforceable structure,
  supporting the API contract tests in the testing matrix.
- Keeps the Markov, ML, blend, calibration and trading-rules code in the
  same language and process family as the API that serves them, avoiding a
  serialisation boundary between modelling and orchestration.
- Async support gives a path to computing the Markov and ML estimates in
  parallel later, addressing the "latency growth as layers are added" risk.
