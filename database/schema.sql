-- CourtEdge data foundation schema (Journey 4).
--
-- PostgreSQL is the transactional source of truth for matches, players,
-- points and outcome labels - see docs/architecture/data-architecture.md
-- and docs/decisions/3-postgres-source-of-truth-duckdb-feature-store.md.
-- The feature-and-replay store (DuckDB/Parquet) is a separate, rebuildable
-- copy derived from this schema, not defined here.
--
-- Quotes, quote events, experiments and model records are out of scope for
-- this schema - they belong to their own journeys (5, 9-11) and will get
-- their own migration when built.

CREATE TABLE players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hand TEXT,
    current_rank INTEGER,
    rank_points INTEGER
);

CREATE TABLE matches (
    match_id TEXT PRIMARY KEY,
    tournament TEXT NOT NULL,
    round TEXT NOT NULL,
    surface TEXT NOT NULL,
    best_of SMALLINT NOT NULL CHECK (best_of IN (3, 5)),
    match_date DATE NOT NULL,
    player_a_id TEXT NOT NULL REFERENCES players (player_id),
    player_b_id TEXT NOT NULL REFERENCES players (player_id),
    source TEXT NOT NULL
);

-- One row per point played, in sequence. Deliberately stores the raw score
-- state (sets/games won entering the point, and the point score string) as
-- recorded by the source, rather than a reinterpreted "games: '4-4'" view -
-- that interpretation is the match-state parser's job (Journey 6).
CREATE TABLE points (
    match_id TEXT NOT NULL REFERENCES matches (match_id),
    point_no INTEGER NOT NULL,
    set_no SMALLINT NOT NULL,
    game_no INTEGER NOT NULL,
    server TEXT NOT NULL CHECK (server IN ('player_a', 'player_b')),
    point_winner TEXT NOT NULL CHECK (point_winner IN ('player_a', 'player_b')),
    sets_won_a SMALLINT NOT NULL,
    sets_won_b SMALLINT NOT NULL,
    games_won_a SMALLINT NOT NULL,
    games_won_b SMALLINT NOT NULL,
    point_score TEXT NOT NULL,
    PRIMARY KEY (match_id, point_no)
);

-- The primary key above already enforces "unique and non-null match and
-- point identifiers" and "no duplicate point records". A true
-- monotonically-increasing check (no gaps, strictly sequential) is not
-- expressible as a plain constraint here - it's enforced at ingestion time
-- by database/quality_gates.py before rows ever reach this table.

CREATE TABLE outcome_labels (
    match_id TEXT PRIMARY KEY REFERENCES matches (match_id),
    actual_winner TEXT NOT NULL CHECK (actual_winner IN ('player_a', 'player_b')),
    final_score TEXT NOT NULL
);
