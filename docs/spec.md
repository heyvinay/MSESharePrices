# Spec: MSE → Portfolio Performance quote feed

## Purpose

Convert Malta Stock Exchange (MSE) end-of-day trading data into a static JSON historical-quote feed that
Portfolio Performance (PP) can consume via its JSON quote-feed provider, published over HTTPS via GitHub
Pages and refreshed automatically.

## Capabilities

1. **Discover or accept source files** — attempt to discover yearly "Daily Trading Summary" archive
   download links from the MSE publications-and-statistics page (category 33); accept one or more
   `--manual-url` values as the primary, confirmed-working path (page discovery does not currently work —
   see Known limitation below).
2. **Download** one or more yearly archive files — MSE's real archive URL is a `.zip` wrapper containing
   an `.xls` workbook, not a bare `.xls`; `process_workbook()` extracts workbook members from zip archives
   automatically.
3. **Parse** each workbook into rows, tolerating minor header naming variation between years
   (e.g. `Symbol code` vs `Symbol Code` vs `Ticker`; `DATE` vs `Trade Date`; `Close Price` vs `Close` vs
   `Last Price`), and recovering from a real OLE2 sector-chain defect real MSE exports have (see
   `read_xls_via_olefile_bypass()` and `docs/decision-log.md`).
4. **Filter** rows to the requested symbol (default `BOV`).
5. **Clean and transform**:
   - normalise dates to ISO `YYYY-MM-DD`,
   - coerce close price to numeric,
   - drop rows with blank/invalid date or price,
   - deduplicate by date (last valid row wins),
   - sort ascending by date.
6. **Export**:
   - `docs/json/<SYMBOL>.json` in the schema `[{"date": "YYYY-MM-DD", "close": <number>}, ...]`,
   - optional `date,quote` CSV for local validation.
7. **Report** a short run summary: files processed, rows matched, date range exported, output path.
8. **Automate** refresh via a scheduled GitHub Actions workflow that commits the feed only when it changed.

## Non-goals

- Real-time or intraday quotes.
- OHLCV richness beyond close price (PP's JSON provider only needs date + close for historical quotes).
- A general market-data API/service for third parties.
- Automated push of data into Portfolio Performance itself — PP pulls from the published URL; this project
  does not talk to PP directly.
- Handling MSE instruments other than the ones explicitly requested via `--symbol` in a given run (the
  design is symbol-agnostic, but each run targets one symbol at a time).

## Acceptance criteria

- Running `python src/mse_pp_feed.py --symbol BOV --start-year <Y> --end-year <Y>` produces a valid
  `docs/json/BOV.json` matching the schema above.
- The output is valid JSON, sorted ascending by date, with no duplicate dates.
- If none of the recognised header variants are present in a source file, the tool fails with a clear
  error naming the missing column — it never silently skips or emits an empty/incorrect feed.
- `docs/index.html` links to the published JSON and explains how to use it with Portfolio Performance.
- `.github/workflows/update-bov.yml` runs on a daily schedule and via manual dispatch, and only commits
  when the generated feed content changed.
- The design supports adding another MSE symbol by passing a different `--symbol` value, without code
  changes.

## Known limitation (documented, not hidden)

MSE's site returned HTTP 403 to automated requests from the development sandbox used to build this
project, and `discover_urls()` finds zero downloadable links when GitHub Actions fetches the archive page
(the page is likely JS-rendered) — see `docs/architecture.md` § Risks. Automated page discovery is
therefore not currently a working path.

**This is resolved for the data pipeline itself.** The real, confirmed-working archive URL (found by the
user browsing MSE's site directly) is:

```
https://cdn.borzamalta.com.mt/download/archives/Trading-Statistics/Trading-Statistics<YYYY>.zip
```

The full pipeline — zip extraction, OLE2 parsing (via `read_xls_via_olefile_bypass()`, which fixes a real
sector-chain defect Crystal-Reports-authored MSE exports have), and header-row scanning — has been
validated against real MSE files (see `tests/fixtures/trading_statistics_2026_sample.xls` and
`docs/decision-log.md`'s 2026-07-20 "RESOLVED" entry), producing genuine BOV historical prices matching
what the user confirmed by opening the same file in Microsoft Excel.

The workflow's default (non-`manual_urls`) scheduled run now targets this URL pattern for the current year
directly, since page discovery doesn't work. `--manual-url` (or the workflow's `manual_urls` dispatch
input) remains available to override with a specific file if needed.
