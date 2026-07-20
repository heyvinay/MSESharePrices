# Architecture (slim arc42-style)

## 1. Context

```
 MSE (borzamalta.com.mt)          GitHub repo: MSESharePrices              Portfolio Performance
 ┌───────────────────────┐        ┌──────────────────────────────┐        ┌───────────────────────┐
 │ publications-and-     │  xls   │ src/mse_pp_feed.py           │  json  │ JSON quote feed        │
 │ statistics?category=33│ ─────► │  (GitHub Actions, daily)     │ ─────► │ provider               │
 │ yearly archive files  │        │  → docs/json/BOV.json        │        │ $[*].date / $[*].close │
 └───────────────────────┘        └──────────────────────────────┘        └───────────────────────┘
                                          │
                                          ▼
                                   GitHub Pages
                                (serves docs/ over HTTPS)
```

## 2. External dependencies

- **MSE publications-and-statistics page** — source of yearly `.xls` "Daily Trading Summary" workbooks.
  Unauthenticated, public, but structure/availability is outside this project's control.
- **GitHub Pages** — static hosting for the published JSON feed. Requires Pages enabled on the repo,
  serving from `docs/` (or the configured source).
- **GitHub Actions** — scheduled compute for the daily refresh.
- **Portfolio Performance** — the consumer. Not integrated with directly; it polls the published JSON URL
  on its own schedule using the JSON quote-feed provider.

## 3. Components / modules

All logic lives in `src/mse_pp_feed.py`, organised as small, independently testable functions:

| Function | Responsibility |
|---|---|
| `discover_urls(page_html)` | Extract candidate yearly `.xls` URLs from the archive page's HTML. |
| `download_file(url)` | Fetch a single workbook (via `requests`), return raw bytes. |
| `read_workbook(bytes_or_path)` | Load a workbook into a list of row dicts (via `pandas`/`xlrd`/`openpyxl`). |
| `normalise_headers(rows)` | Map varying source column names onto canonical `symbol`, `date`, `close`. |
| `extract_quotes(rows, symbol)` | Filter to the requested symbol, coerce/clean each row. |
| `dedupe_and_sort(quotes)` | Resolve duplicate dates (last valid wins), sort ascending. |
| `write_json(quotes, path)` | Serialise to the PP-compatible schema. |
| `write_csv(quotes, path)` | Optional local-validation CSV (`date,quote`). |
| `main()` | CLI wiring: argument parsing, orchestration, run summary, exit codes. |

## 4. Data flow

1. CLI args parsed (`--symbol`, `--start-year`, `--end-year`, `--manual-url`, `--output-json`,
   `--output-csv`).
2. Source URLs resolved: either from `--manual-url` (if given) or by attempting `discover_urls()` against
   the archive page for the requested year range.
3. Each workbook downloaded and parsed independently; a failure on one year is reported but does not abort
   processing of other years (best-effort backfill).
4. Rows from all years are merged, normalised, filtered to the target symbol, cleaned, deduplicated, and
   sorted.
5. Result written to JSON (required) and CSV (optional).
6. Summary printed: files processed, rows matched, date range, output path.

## 5. Interfaces / contracts

- **Input contract (per workbook row, after header normalisation):** `symbol` (str), `date` (parseable to a
  calendar date), `close` (parseable to a positive float).
- **Output contract (JSON):** `[{"date": "YYYY-MM-DD", "close": <float>}, ...]`, ascending by date, no
  duplicate dates, no trailing/leading whitespace, valid UTF-8 JSON.
- **Output contract (CSV, optional):** header `date,quote`, same ordering/dedup rules as JSON.
- **CLI contract:** non-zero exit code and a message naming the missing/invalid column when required data
  can't be found; zero exit code and a printed summary on success (including the case of zero matched rows
  for a given symbol/year, which is a valid — if unhelpful — outcome, not an error).

## 6. Error handling approach

- Network/download failures for one yearly file: log and continue with the rest (partial backfill is
  better than total failure), but exit non-zero overall if **no** file could be processed at all.
- Missing required column after header normalisation: raise a clear, named exception — never silently
  produce an empty or partial feed.
- Non-numeric close price / unparseable date: drop the row, do not fail the whole run, but count it in the
  summary so silent data loss is visible.

## 7. Design decisions

See `docs/decision-log.md` for the running ADR-style log. Headline decisions:

- JSON (not CSV-only) is the primary output, because PP's JSON quote-feed provider allows unattended
  refresh; CSV is kept only as an optional local-validation artifact.
- GitHub Pages + Actions (not a third-party host) because it needs no new infrastructure and matches "no
  secrets, public data only."
- Yearly-archive workbooks (not the daily `Price_List.xls` snapshot) are the source of truth, because the
  daily list has no date column / is overwritten daily and cannot build history.

## 8. Risks and assumptions

- **Verification gap (see `docs/spec.md`):** MSE's site blocked automated requests from the development
  sandbox (HTTP 403), so the exact archive page HTML and workbook column names are based on the research
  in `docs/plan.md`, not a live-verified sample. `normalise_headers()` must tolerate the plausible variants
  documented there and fail loudly if none match. Confirm against a real download before trusting
  unattended runs.
- **Archive page structure may change.** `discover_urls()` is inherently coupled to today's page markup;
  the `--manual-url` fallback exists specifically to de-risk this.
- **Workbook format may vary by year** (old `.xls` vs newer `.xlsx`); the reader should tolerate both where
  feasible, and fail with a clear message otherwise.
