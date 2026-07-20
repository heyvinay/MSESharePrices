# MSESharePrices

## Project identity

**Mission:** Publish a stable, automated historical-quote feed for Malta Stock Exchange (MSE) listed
securities, in a format Portfolio Performance can consume directly via its JSON quote-feed provider.

**Primary user:** a single investor using [Portfolio Performance](https://www.portfolio-performance.info/)
to track a portfolio that includes MSE-listed securities not covered by PP's built-in quote providers.

**Deployment model:** public GitHub repo. A Python script converts MSE's published yearly trading-summary
workbooks into JSON, publishes it to `docs/json/<SYMBOL>.json`, and GitHub Pages serves it over HTTPS.
GitHub Actions refreshes the feed on a schedule.

**Non-goals:**
- Not a general-purpose market-data API or a redistribution service for MSE data beyond personal use.
- Not a real-time feed — MSE publishes end-of-day data, so refresh cadence is daily at most.
- Not a UI/dashboard — the deliverable is a static JSON file.
- No OHLCV richness beyond what Portfolio Performance's JSON provider needs (`date`, `close`).

## Core principles

- **Source before scrape** — prefer MSE's structured workbook downloads (yearly trading-summary archive)
  over scraping rendered HTML pages, which are brittle and not built for machine consumption.
- **Stable contracts over cleverness** — the published JSON schema must not change without a deliberate,
  documented decision, since Portfolio Performance depends on it.
- **Testability over convenience** — parsing, normalisation, and transformation logic lives in small pure
  functions that are easy to unit test.
- **Automation by default** — the feed should refresh itself; manual CSV import is a fallback, not the
  primary workflow.
- **Public-repo-safe design** — no secrets, no credentials, no non-public data. Everything handled here is
  already public MSE market data.
- **Docs and code change together** — any behavioural change updates the relevant doc (`docs/spec.md`,
  `docs/architecture.md`, `docs/qa.md`, `docs/decision-log.md`) in the same change set.

## Invariants

- Output JSON schema is exactly `[{"date": "YYYY-MM-DD", "close": <number>}, ...]`, sorted ascending by date.
- Dates are always ISO `YYYY-MM-DD`.
- `close` is always numeric (float), never a string.
- Duplicate dates are resolved deterministically: the last valid row encountered wins.
- Missing required source columns (`Symbol code` / `Date` / `Close Price`, allowing header variation) cause
  a clear failure, not a silent skip.
- No secrets or credentials are ever committed to this repo.

## Working rules for coding agents

- Keep edits surgical; do not refactor unrelated code.
- Prefer small, pure, independently-testable functions (`discover_urls`, `download_file`, `read_workbook`,
  `normalise_headers`, `extract_quotes`, `write_json`).
- Write or update tests alongside any change to parsing/transform logic.
- Update `docs/decision-log.md` when an architectural decision changes (e.g. hosting path, schema, source
  format).

## Repo map

- `src/mse_pp_feed.py` — CLI importer/feed generator.
- `tests/` — pytest suite.
- `docs/spec.md` — capabilities, non-goals, acceptance criteria.
- `docs/architecture.md` — slim arc42-style architecture notes.
- `docs/qa.md` — test strategy.
- `docs/decision-log.md` — ADR-style log of key decisions.
- `docs/plan.md` — original research/planning conversation this project was scoped from.
- `docs/index.html` — landing page for the published feed (served via GitHub Pages).
- `docs/json/<SYMBOL>.json` — published quote feed(s).
- `.github/workflows/update-bov.yml` — scheduled refresh.

## Optional: Matt Pocock skills

This repo is small enough not to require any external skill framework, but if you have
[Matt Pocock's skills](https://github.com/mattpocock/skills) installed (`npx skills@latest add mattpocock/skills`),
they map well onto this workflow:

- `/grill-me` — pressure-test the spec before implementing.
- `/to-prd` — refine a feature into a concrete brief.
- `/tdd` — red-green-refactor loop for parser/transform logic.
- `/diagnose` — investigate parsing or workflow failures.
- `/improve-codebase-architecture` — periodic architecture review as the project grows to more symbols.
