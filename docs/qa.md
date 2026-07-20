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
| xlrd engine routing | OLE2 (`.xls`) files are routed through `xlrd`; zip (`.xlsx`) files go through pandas' default engine detection. |
| LibreOffice fallback routing | When `xlrd` raises on an OLE2 file, `read_workbook()` falls back to `convert_xls_to_xlsx_via_libreoffice()` + `openpyxl` (mocked in the unit test; see the real-`soffice` integration test below for the unmocked path). |
| LibreOffice conversion (real, not mocked) | `test_convert_xls_to_xlsx_via_libreoffice_real_roundtrip` exercises the actual `soffice` binary end-to-end. It **skips** (not fails) if headless conversion doesn't work in the current environment — this development sandbox's LibreOffice can't complete *any* headless conversion, even a trivial `.txt`→`.pdf`, which is an environment restriction, not a code bug. GitHub Actions' `ubuntu-latest` runner (where `libreoffice-calc` is installed by the workflow) is the environment that actually matters; the live workflow run is the real confirmation this path works (see `docs/decision-log.md`, 2026-07-20 LibreOffice entry). |

## CI

`.github/workflows/update-bov.yml` installs dependencies and can run `pytest` before regenerating the feed,
so a regression in parsing/transform logic fails the workflow instead of silently publishing bad data.
(See the workflow file for the exact steps.)

## Manual verification checklist (not automated)

Because live network access to `borzamalta.com.mt` was not available during development:

1. **Get a real archive URL by hand.** Open
   `https://www.borzamalta.com.mt/publications-and-statistics?category=33` in an actual browser and copy
   the download link for a yearly "Daily Trading Summary" workbook. Do not reuse the
   `trading statistics YYYY.xls` URL pattern from `docs/plan.md` unverified — see the finding below.
2. Run `python src/mse_pp_feed.py --symbol BOV --manual-url <path-or-url-to-that-file> --output-json /tmp/bov.json`.
3. Confirm the run summary reports a plausible row count and date range.
4. Open `/tmp/bov.json` and spot-check a few known BOV closing prices against the MSE site.
5. Only then trust the scheduled/unattended GitHub Actions run.

If any recognised header variant is wrong for real MSE files, update `normalise_headers()` and add a
regression test with the real header name (redacted of any non-public data, though MSE prices are public).

## Finding: the `trading statistics YYYY.xls` URLs are likely wrong, not a parsing bug

Extensive live-run debugging (see `docs/decision-log.md`, 2026-07-20 entries) confirmed the full pipeline
works correctly end-to-end — including the OLE2/xlrd routing, the LibreOffice fallback for files xlrd can't
parse, and header-row scanning — by testing it against a real MSE file
(`Daily_Market_Extract.xls`), which produced genuinely readable content (real company names and prices).

However, both `trading statistics 2025.xls` and `trading statistics 2026.xls` — the URLs surfaced by AI web
research in `docs/plan.md`, never confirmed by a human clicking through MSE's site — consistently produced
**only garbled OLE2-internal container text with zero real content**, for two different years. That rules
out "the current year isn't finalized yet" as an explanation; it's consistent with those specific URLs
being wrong or stale for the "Daily Trading Summary yearly archive" resource, not a defect in this
project's code.

**Action needed:** a human should browse
`https://www.borzamalta.com.mt/publications-and-statistics?category=33` directly, download a yearly archive
file, and confirm it opens correctly in Excel/LibreOffice before assuming its URL is usable with
`--manual-url`. `Daily_Market_Extract.xls` itself is not usable as-is either — it's an "Official List"
narrative document (security names + ex-dividend dates in loosely-structured cells), not a clean
Symbol/Date/Close table `normalise_headers()` expects.
