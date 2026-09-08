# Architecture decision records

One file per decision, named `<n>-<slug>.md` using plain sequential numbers
(`1-`, `2-`, `3-` ...). Each ADR uses this shape:

```markdown
# <n>. <Title>

- Status: Proposed | Accepted | Superseded by <n>
- Date: <yyyy-mm-dd>

## Context

## Decision

## Consequences
```

An ADR is never edited to reverse a decision — a later decision that changes
course adds a new ADR and marks the old one superseded, so the history stays
intact.
