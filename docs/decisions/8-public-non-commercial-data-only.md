# 8. Restrict data sources to public, non-commercial-licensed data; market odds are a benchmark only

- Status: Accepted
- Date: 2026-09-08

## Context

CourtEdge is a portfolio/research prototype, not a licensed product. Using
a paid or restricted-licence feed (e.g. a live regulated odds feed) would
create legal and licensing exposure disproportionate to a learning project,
and would blur the line between "research prototype" and "something that
looks like it's plugged into a real market" — a framing risk flagged
explicitly in the governance architecture.

## Decision

Ingest only data with confirmed, recorded provenance and a non-commercial
licence: the Sackmann point-by-point/ATP/WTA repositories (CC BY-NC-SA) and
tennis-data.co.uk historical odds. Market odds are used exclusively as an
offline evaluation benchmark and for the bounded, research-only
value-detection layer — never as a live serving-time feature, and never
treated as ground truth of the "true" probability.

## Consequences

- No live ingestion of a paid or restricted-licence feed is possible
  without a separate decision and recorded licence confirmation (charter:
  "what will not be built initially").
- Every dataset must be registered in
  [docs/data_sheets/data_provenance.md](../data_sheets/data_provenance.md)
  with its source and licence terms before ingestion.
- Historical market-price comparisons must be de-vigged and explicitly
  framed as research validation, addressing the "naive beat-the-market
  claims may mislead" risk.
- Limits CourtEdge to match years and tours where Sackmann's archives have
  good coverage; sparse or poorly covered years are excluded rather than
  supplemented with an unlicensed source.
