# 1. Use Next.js for the replay and pricing dashboard

- Status: Accepted
- Date: 2026-09-08

## Context

CourtEdge needs a front end for match replay, a live win-probability chart,
a price ticker and scenario browsing (charter FR-01, FR-02). It must serve
static content well for demo/portfolio purposes, support component-based
UI development, and reach a reasonable feature-per-effort ratio for a
prototype built primarily by one developer.

## Decision

Use Next.js (React) for the dashboard, starting with a static replay route
before any live API is connected (journey 2).

## Consequences

- The frontend can be developed and reviewed (page states: loading,
  success, error, suspended) before the backend exists, satisfying gate G1.
- React's component model maps directly onto the dashboard's named parts:
  match selector, point ticker, probability chart, price ticker,
  model-version badge.
- Introduces a Node.js toolchain alongside the Python backend; accepted as
  the standard pairing for this kind of app and consistent with the
  deployment architecture's "Web" layer.
