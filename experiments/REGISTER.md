# Experiment register

Every experiment CourtEdge runs is registered here before or as it is run,
with a hypothesis, its configuration, its metrics and a decision. This is
the single evidence trail referenced throughout the project — nothing is
promoted to the serving path without an entry here.

Numbering follows the planned experiment catalogue in the source
architecture document (section 14): experiments are grouped by theme, and
the leading digit(s) indicate the theme, not a strict run order.

- `EXP1`–`EXP9`: primitive baselines
- `EXP10`–`EXP19`: Markov analytic baseline
- `EXP20`–`EXP29`: learned (ML) probability models
- `EXP30`–`EXP39`: blending / fusion
- `EXP40`–`EXP49`: calibration
- `EXP50`+: optional / exploratory extensions

## Status legend

- **Planned** — registered, not yet run.
- **Running** — in progress.
- **Retained** — improved the agreed evidence; kept in the serving path or as a documented candidate.
- **Rejected** — run, and not promoted; code and results moved to [discarded/](../discarded) with the reason.

## Catalogue

| ID | Possibility considered | Role | Status |
|---|---|---|---|
| EXP1 | Always-50/50 probability | Primitive baseline | Planned |
| EXP2 | Current-score-leader heuristic | Primitive baseline | Planned |
| EXP10 | Constant tour-average serve rate Markov chain | Analytic baseline | Planned |
| EXP11 | Per-player overall serve-win rate | Baseline refinement | Planned |
| EXP12 | Surface-specific serve-win rate | Baseline tuning | Planned |
| EXP13 | Bayesian shrinkage for low-sample players | Robustness experiment | Planned |
| EXP14 | Non-i.i.d. Markov variant with a separate deuce-phase rate | Advanced analytic experiment | Planned |
| EXP20 | Logistic regression on score-state features only | Learned baseline | Planned |
| EXP21 | Logistic regression with player/context features added | Representation comparison | Planned |
| EXP22 | XGBoost/LightGBM classifier, state features only | Learned model | Planned |
| EXP23 | XGBoost/LightGBM classifier, state and context features | Learned model | Planned |
| EXP24 | XGBoost/LightGBM classifier, state, context and momentum features | Representation comparison | Planned |
| EXP30 | Markov-only probability | Analytic comparator | Planned |
| EXP31 | ML-only probability | Learned comparator | Planned |
| EXP32 | Fixed-weight blend of Markov and ML | Fusion baseline | Planned |
| EXP33 | Validation-tuned weighted blend | Fusion alternative | Planned |
| EXP34 | Stacked meta-model combining Markov output, ML output and features | Meta-learning candidate | Planned |
| EXP40 | No calibration (raw blended probability) | Calibration baseline | Planned |
| EXP41 | Platt scaling | Calibration candidate | Planned |
| EXP42 | Isotonic regression | Calibration candidate | Planned |
| EXP43 | Dynamic, phase-level calibration | Calibration candidate | Planned |
| EXP50 | Shot-level and rally momentum features | Optional representation experiment | Planned |
| EXP51 | Cross-sport Poisson extension (football goal model) | Optional generalisation experiment | Planned |

## Entry template

Each experiment gets its own file at `experiments/<ID>-<slug>.md` once it
runs, using this template:

```markdown
# EXP<n> — <title>

- Status: Running | Retained | Rejected
- Depends on: <other EXP IDs or work packages>
- Date: <yyyy-mm-dd>

## Hypothesis

## Configuration

## Metrics

## Decision

Retained/rejected and why, referencing the evidence rule: an experiment is
retained only if it solves a named problem, is reproducible, and improves
the agreed evidence without unacceptable latency, instability or ethical
risk.
```

## Negative-result policy

An experiment may be rejected because it lowers accuracy, worsens
calibration, increases latency, adds operational complexity, relies on weak
or sparse data, creates governance or ethical concerns, or duplicates a
simpler capability. The code and result remain in the evidence trail under
[discarded/](../discarded).

## Source

Derived from `docs/CourtEdge_Architecture_and_Task_Definition.docx`, section 14.
