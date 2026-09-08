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
| [EXP1](EXP1-always-fifty-fifty.md) | Always-50/50 probability | Primitive baseline | Retained |
| [EXP2](EXP2-score-leader-heuristic.md) | Current-score-leader heuristic | Primitive baseline | Retained |
| [EXP10](EXP10-tour-average-markov.md) | Constant tour-average serve rate Markov chain | Analytic baseline | Retained |
| [EXP11](EXP11-per-player-serve-rate.md) | Per-player overall serve-win rate | Baseline refinement | Retained (data-volume limited — see write-up) |
| EXP12 | Surface-specific serve-win rate | Baseline tuning | Planned |
| [EXP13](EXP13-bayesian-shrinkage.md) | Bayesian shrinkage for low-sample players | Robustness experiment | Retained |
| EXP14 | Non-i.i.d. Markov variant with a separate deuce-phase rate | Advanced analytic experiment | Planned |
| [EXP20](EXP20-logistic-state-only.md) | Logistic regression on score-state features only | Learned baseline | Retained |
| [EXP21](EXP21-logistic-state-context.md) | Logistic regression with player/context features added | Representation comparison | Retained |
| [EXP22](EXP22-lightgbm-state-only.md) | XGBoost/LightGBM classifier, state features only | Learned model | Retained |
| [EXP23](EXP23-lightgbm-state-context.md) | XGBoost/LightGBM classifier, state and context features | Learned model | Retained |
| [EXP24](EXP24-lightgbm-state-context-momentum.md) | XGBoost/LightGBM classifier, state, context and momentum features | Representation comparison | **Retained — leading ML candidate** |
| [EXP30](EXP30-EXP31-markov-and-ml-only.md) | Markov-only probability | Analytic comparator | Retained (comparator) |
| [EXP31](EXP30-EXP31-markov-and-ml-only.md) | ML-only probability | Learned comparator | Retained (comparator) |
| [EXP32](EXP32-EXP33-blend.md) | Fixed-weight blend of Markov and ML | Fusion baseline | Rejected — worse than ML alone (retained as evidence) |
| [EXP33](EXP32-EXP33-blend.md) | Validation-tuned weighted blend | Fusion alternative | **Retained — leading configuration** |
| EXP34 | Stacked meta-model combining Markov output, ML output and features | Meta-learning candidate | Planned |
| [EXP40](EXP40-EXP43-calibration.md) | No calibration (raw blended probability) | Calibration baseline | Retained (comparator) |
| [EXP41](EXP40-EXP43-calibration.md) | Platt scaling | Calibration candidate | Rejected — worse than no calibration on every metric (retained as evidence) |
| [EXP42](EXP40-EXP43-calibration.md) | Isotonic regression | Calibration candidate | Retained |
| [EXP43](EXP40-EXP43-calibration.md) | Dynamic, phase-level calibration | Calibration candidate | **Retained — leading configuration** |
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
