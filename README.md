# MSESharePrices

Automated historical-quote feed for Malta Stock Exchange (MSE) listed securities, published as static
JSON so [Portfolio Performance](https://www.portfolio-performance.info/) can consume it directly via its
JSON quote-feed provider — no recurring manual CSV import.

Currently ships one feed: **Bank of Valletta plc (`BOV`)**. The design is symbol-agnostic; see
[Adding another symbol](#adding-another-symbol) below.

See [`docs/spec.md`](docs/spec.md), [`docs/architecture.md`](docs/architecture.md),
[`docs/qa.md`](docs/qa.md), and [`docs/decision-log.md`](docs/decision-log.md) for the full design
rationale, and [`docs/plan.md`](docs/plan.md) for the original research conversation this project was
scoped from.

## How it works

```
MSE yearly "Daily Trading Summary" archive  →  src/mse_pp_feed.py  →  docs/json/BOV.json  →  GitHub Pages  →  Portfolio Performance
                                                  (GitHub Actions, daily)
```

## Setup

```bash
pip install -r requirements.txt
```

## Local usage

Run for BOV, letting the tool discover archive URLs itself:

```bash
python src/mse_pp_feed.py --symbol BOV --start-year 2024 --end-year 2026
```

Run for a different MSE symbol:

```bash
python src/mse_pp_feed.py --symbol APS --output-json docs/json/APS.json
```

Run against one or more manually-provided workbook files or URLs (bypasses page discovery entirely —
use this if the MSE archive page structure changes or is unreachable):

```bash
python src/mse_pp_feed.py --symbol BOV \
  --manual-url /path/to/trading_statistics_2025.xls \
  --manual-url /path/to/trading_statistics_2026.xls \
  --output-json docs/json/BOV.json \
  --output-csv /tmp/BOV.csv
```

Run the test suite:

```bash
pytest tests/
```

## GitHub Pages setup

1. In the repo's **Settings → Pages**, set the source to the `main` (or default) branch, folder `/docs`.
2. Once enabled, the feed is served at:
   ```
   https://heyvinay.github.io/MSESharePrices/json/BOV.json
   ```
3. The landing page at `docs/index.html` links to all published feeds.

## GitHub Actions

[`update-bov.yml`](.github/workflows/update-bov.yml) runs on a weekday schedule and on manual dispatch
(**Actions → Update BOV quote feed → Run workflow**). It installs dependencies, runs the test suite,
regenerates `docs/json/BOV.json`, and commits the file only if its content actually changed.

## Portfolio Performance configuration

On the security's **Historical Quotes** tab:

| Field | Value |
|---|---|
| Provider | `JSON` |
| Feed URL | `https://heyvinay.github.io/MSESharePrices/json/BOV.json` |
| Path to Date | `$[*].date` |
| Path to Close | `$[*].close` |

## Adding another symbol

1. Run the script with `--symbol <CODE> --output-json docs/json/<CODE>.json`.
2. Add a link to `docs/json/<CODE>.json` in `docs/index.html`.
3. Optionally duplicate `.github/workflows/update-bov.yml` for the new symbol (or generalise it to accept
   a symbol as a workflow input — not done yet, kept simple for one symbol for now).

## Known limitations

- **MSE data is end-of-day only.** This is not, and cannot be, a real-time feed.
- **Live-verification gap:** during development, `borzamalta.com.mt` returned HTTP 403 to automated
  requests from the sandbox this project was built in, so the exact archive page HTML and workbook column
  names could not be confirmed against a real live sample. The parser (`normalise_headers` in
  `src/mse_pp_feed.py`) accepts several plausible header spellings and fails with a clear, named error if
  none match — but **run it once against a real downloaded workbook (via `--manual-url`) before trusting
  the scheduled Action**, and see [`docs/qa.md`](docs/qa.md)'s manual verification checklist.
- **Archive page structure may change** — `discover_urls()` is coupled to today's page markup;
  `--manual-url` is the documented fallback.
- Only closing price is captured (no open/high/low/volume) — that's all Portfolio Performance's JSON
  historical-quote provider needs.

## Troubleshooting

- **"Could not find a column for 'X'"** — the source workbook doesn't use any of the recognised header
  spellings for that field. Open the workbook, note its real header, and add it to `HEADER_ALIASES` in
  `src/mse_pp_feed.py` (with a matching test in `tests/test_mse_pp_feed.py`).
- **"no source files found or provided"** — page discovery failed (site down, structure changed, or
  blocked). Use `--manual-url` with a directly-downloaded file as a workaround.
- **GitHub Pages 404** — confirm Pages is enabled and pointed at `/docs` on the correct branch, and that
  the workflow has run at least once to create `docs/json/BOV.json`.
