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

Run for BOV against MSE's real yearly archive URL (page discovery doesn't work — see Known limitations —
so `--manual-url` is the recommended path; the tool also extracts `.xls`/`.xlsx` files from a `.zip`
archive automatically):

```bash
python src/mse_pp_feed.py --symbol BOV \
  --manual-url "https://cdn.borzamalta.com.mt/download/archives/Trading-Statistics/Trading-Statistics2025.zip" \
  --output-json docs/json/BOV.json
```

Run for a different MSE symbol:

```bash
python src/mse_pp_feed.py --symbol APS \
  --manual-url "https://cdn.borzamalta.com.mt/download/archives/Trading-Statistics/Trading-Statistics2025.zip" \
  --output-json docs/json/APS.json
```

Run against one or more manually-provided local files (also supported, e.g. for a pre-downloaded file or
one of MSE's other statistics files):

```bash
python src/mse_pp_feed.py --symbol BOV \
  --manual-url /path/to/Trading-Statistics2025.zip \
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
- **Archive page discovery doesn't work from this environment** — `discover_urls()` finds zero downloadable
  links when fetched by an automated client (the page is likely JS-rendered). The real, confirmed-working
  source is a direct download URL instead:
  ```
  https://cdn.borzamalta.com.mt/download/archives/Trading-Statistics/Trading-Statistics<YYYY>.zip
  ```
  The workflow's default scheduled run targets this URL for the current year automatically; `--manual-url`
  (or the workflow's `manual_urls` dispatch input) can override it.
- **MSE's real `.xls` exports (authored by Crystal Reports) trip a real defect in `xlrd`'s own
  directory-stream navigation** — a genuinely cyclic sector chain that Microsoft Excel tolerates but `xlrd`
  does not. `read_workbook()` recovers via `read_xls_via_olefile_bypass()`, which extracts the raw
  `Workbook` BIFF stream using the `olefile` library (which, like Excel, doesn't depend on that broken
  navigation step) and feeds it directly to `xlrd`'s own BIFF parser. Verified against real MSE files (see
  `tests/fixtures/trading_statistics_2026_sample.xls` and [`docs/decision-log.md`](docs/decision-log.md)'s
  2026-07-20 "RESOLVED" entry) — 132 real BOV rows, correct dates and prices, matching what the file shows
  when opened directly in Excel. LibreOffice conversion remains as a last-resort fallback for anything that
  defeats both `xlrd` and the olefile bypass, but should rarely trigger now.
- MSE's yearly archive is served as a `.zip` wrapper around the `.xls` workbook, not the workbook directly —
  `process_workbook()` extracts `.xls`/`.xlsx` members from zip archives automatically.
- Only closing price is captured (no open/high/low/volume) — that's all Portfolio Performance's JSON
  historical-quote provider needs.
- Requires a system-level LibreOffice install (`libreoffice-calc`, added via apt in the workflow) purely as
  a last-resort fallback converter — it should rarely actually run now that the real root cause (above) is
  fixed, but the apt-get install step still costs time on every scheduled run.

## Troubleshooting

- **"Could not find a column for 'X'"** — the source workbook doesn't use any of the recognised header
  spellings for that field. Open the workbook, note its real header, and add it to `HEADER_ALIASES` in
  `src/mse_pp_feed.py` (with a matching test in `tests/test_mse_pp_feed.py`).
- **"no source files found or provided"** — page discovery failed (site down, structure changed, or
  blocked). Use `--manual-url` with a directly-downloaded file as a workaround.
- **GitHub Pages 404** — confirm Pages is enabled and pointed at `/docs` on the correct branch, and that
  the workflow has run at least once to create `docs/json/BOV.json`.
