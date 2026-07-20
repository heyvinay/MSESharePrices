# QA strategy

## Approach

TDD on the transformation contracts, not on plumbing. Network I/O (`download_file`, `discover_urls`
against the live site) is not exercised by the automated suite — it's tested indirectly via fixtures and
manually validated per `docs/spec.md`'s documented verification gap.

## Test matrix (`tests/`)

| Area | What's verified |
|---|---|
| Header normalisation | Recognised header variants (`Symbol code`/`Symbol Code`/`Ticker`, `DATE`/`Trade Date`, `Close Price`/`Close`/`Last Price`) all map to canonical `symbol`/`date`/`close`. |
| Missing-column failure | A workbook missing all recognised variants of a required column raises a clear, named error — not a silent empty result. |
| Symbol filtering | Only rows matching the requested symbol (case-sensitive exact match) survive; other symbols in the same workbook are excluded. |
| Date normalisation | Multiple plausible input date formats (`05-Jan-2026`, `2026-01-05`, Excel serial dates) normalise to `YYYY-MM-DD`. |
| Price coercion | Numeric strings, comma-formatted numbers, and blank/invalid prices are handled (valid → float, invalid → row dropped and counted). |
| Deduplication | Two rows for the same date resolve to the last valid one encountered, not the first. |
| Sort order | Output is strictly ascending by date regardless of input order. |
| JSON schema | Output is a list of `{"date": ..., "close": ...}` objects; `close` is numeric (not a string); no extra keys. |
| CSV schema (optional output) | Header is exactly `date,quote`; row count and ordering match the JSON output. |
| End-to-end (fixture-based) | A small synthetic in-memory workbook (multiple symbols, one duplicate date, one invalid row) produces the exact expected JSON. |

## CI

`.github/workflows/update-bov.yml` installs dependencies and can run `pytest` before regenerating the feed,
so a regression in parsing/transform logic fails the workflow instead of silently publishing bad data.
(See the workflow file for the exact steps.)

## Manual verification checklist (not automated)

Because live network access to `borzamalta.com.mt` was not available during development:

1. Download one real yearly workbook by hand from
   `https://www.borzamalta.com.mt/publications-and-statistics?category=33`.
2. Run `python src/mse_pp_feed.py --symbol BOV --manual-url <path-or-url-to-that-file> --output-json /tmp/bov.json`.
3. Confirm the run summary reports a plausible row count and date range.
4. Open `/tmp/bov.json` and spot-check a few known BOV closing prices against the MSE site.
5. Only then trust the scheduled/unattended GitHub Actions run.

If any recognised header variant is wrong for real MSE files, update `normalise_headers()` and add a
regression test with the real header name (redacted of any non-public data, though MSE prices are public).
