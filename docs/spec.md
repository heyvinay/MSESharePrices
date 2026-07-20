# Spec: MSE → Portfolio Performance quote feed

## Purpose

Convert Malta Stock Exchange (MSE) end-of-day trading data into a static JSON historical-quote feed that
Portfolio Performance (PP) can consume via its JSON quote-feed provider, published over HTTPS via GitHub
Pages and refreshed automatically.

## Capabilities

1. **Discover or accept source files** — attempt to discover yearly "Daily Trading Summary" archive
   download links from the MSE publications-and-statistics page (category 33); accept one or more
   `--manual-url` values as a documented fallback when discovery is unreliable or blocked.
2. **Download** one or more yearly `.xls` workbooks.
3. **Parse** each workbook into rows, tolerating minor header naming variation between years
   (e.g. `Symbol code` vs `Symbol Code` vs `Ticker`; `DATE` vs `Trade Date`; `Close Price` vs `Close` vs
   `Last Price`).
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
project, so the yearly-archive HTML structure could not be verified live during development, and
`discover_urls()` finds zero downloadable links when GitHub Actions fetches the archive page (the page is
likely JS-rendered) — see `docs/architecture.md` § Risks.

**The parsing pipeline itself has been validated against a real MSE file** (`Daily_Market_Extract.xls`,
via GitHub Actions, which has normal internet access unlike the dev sandbox): the OLE2/xlrd routing, the
LibreOffice fallback for files xlrd can't parse, and header-row scanning all worked correctly and produced
genuinely readable MSE content. What's still unresolved is that the two candidate yearly-archive URLs
tried (`trading statistics 2025.xls` and `trading statistics 2026.xls`, both surfaced by AI research in
`docs/plan.md` and never confirmed by a human) consistently return garbled, content-free responses for
both years — most likely wrong/stale URLs, not a defect in this project. See `docs/qa.md`'s "Finding"
section and `docs/decision-log.md` for the full investigation.

**Before relying on unattended daily runs:** a human must browse
`https://www.borzamalta.com.mt/publications-and-statistics?category=33` directly, obtain a real, working
yearly-archive download URL, and confirm it via `--manual-url` (or the workflow's `manual_urls` dispatch
input) produces a sane `docs/json/BOV.json`.
