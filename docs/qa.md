# QA strategy

## Approach

TDD on the transformation contracts, not on plumbing, plus a real-file regression fixture (see below) since
the transform bugs this project actually hit only surfaced against genuine MSE exports. Network I/O
(`download_file`, `discover_urls` against the live site) is not exercised by the automated suite — it's
tested indirectly via fixtures.

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
| End-to-end (synthetic fixture) | A small synthetic in-memory workbook (multiple symbols, one duplicate date, one invalid row) produces the exact expected JSON. |
| xlrd engine routing | OLE2 (`.xls`) files try `xlrd`'s normal entrypoint first; zip (`.xlsx`) files go through pandas' default engine detection. |
| olefile bypass routing | When `xlrd` raises on an OLE2 file, `read_workbook()` uses `read_xls_via_olefile_bypass()` — this is the real, proven fix (see `docs/decision-log.md`, 2026-07-20 RESOLVED entry) for the actual defect MSE's real exports have. |
| LibreOffice last-resort fallback | If the olefile bypass *also* fails, `read_workbook()` falls back to `convert_xls_to_xlsx_via_libreoffice()` + `openpyxl` as a final attempt (mocked in the unit test; see the real-`soffice` integration test below for the unmocked path). In practice this should rarely trigger now that the real root cause is fixed. |
| LibreOffice conversion (real, not mocked) | `test_convert_xls_to_xlsx_via_libreoffice_real_roundtrip` exercises the actual `soffice` binary end-to-end. It **skips** (not fails) if headless conversion doesn't work in the current environment — this development sandbox's LibreOffice can't complete *any* headless conversion, even a trivial `.txt`→`.pdf`, which is an environment restriction, not a code bug. |
| Zip archive extraction | `process_workbook()` detects a zip that isn't itself a valid xlsx and extracts `.xls`/`.xlsx` members from inside it (MSE's real yearly archive URL is a `.zip` wrapper, not a bare workbook) — covered for single-member, multi-member (merged), non-workbook-junk-ignored, and no-workbook-members-found cases. |
| **Real MSE file (end-to-end, not mocked)** | `test_process_workbook_extracts_real_bov_data_from_a_real_mse_export` and `test_read_xls_via_olefile_bypass_matches_the_known_real_header_row` run against `tests/fixtures/trading_statistics_2026_sample.xls` — an actual MSE "Daily Trading Summary" export (public market data), authored by Crystal Reports per its OLE2 metadata. This is the real file class that exposed every bug this project hit with real `.xls` parsing. Confirms 132 real BOV rows, Jan–Jul 2026, prices in a sane €1.91–€2.13 range, zero dropped rows. |

## CI

`.github/workflows/update-bov.yml` installs dependencies and can run `pytest` before regenerating the feed,
so a regression in parsing/transform logic fails the workflow instead of silently publishing bad data.
(See the workflow file for the exact steps.)

## Manual verification checklist (not automated)

1. Run `python src/mse_pp_feed.py --symbol BOV --manual-url <path-or-url-to-a-real-archive-file> --output-json /tmp/bov.json`.
2. Confirm the run summary reports a plausible row count and date range.
3. Open `/tmp/bov.json` and spot-check a few known BOV closing prices against the MSE site.
4. Only then trust the scheduled/unattended GitHub Actions run.

If any recognised header variant is wrong for real MSE files, update `normalise_headers()` and add a
regression test with the real header name (redacted of any non-public data, though MSE prices are public).

## RESOLVED: the real archive URL, and the real root cause

The earlier "guessed archive URLs are likely wrong" finding was half right and half wrong. It correctly
identified that the `trading statistics YYYY.xls` URLs (guessed from unverified AI research in
`docs/plan.md`) were bad. But its "the file must be corrupted" hypothesis, tested against the *actual*
correct URL, turned out to be wrong.

**The real, confirmed-working archive URL** (found by the user browsing MSE's site directly):

```
https://cdn.borzamalta.com.mt/download/archives/Trading-Statistics/Trading-Statistics<YYYY>.zip
```

It's a `.zip` wrapper containing the real `.xls` workbook — see `process_workbook()`'s zip-extraction
support.

**The real root cause** of every "garbled OLE2 internals" symptom seen throughout this project's
development: the extracted `.xls` (authored by Crystal Reports) makes `xlrd`'s own compound-document
directory navigation trip over a genuinely cyclic sector chain. Confirmed two ways: (1) naively bypassing
`xlrd`'s cycle-detection there is a real infinite loop, not a false-positive check — it consumed 11.6GB of
RAM in the dev sandbox before being killed; (2) the user opened the same file in real Microsoft Excel and
it rendered perfectly, proving the underlying data was never actually damaged — Excel just doesn't rely on
that same directory-stream chain to locate named streams, and neither does the Python `olefile` library.

`read_xls_via_olefile_bypass()` is the fix: extract the raw `"Workbook"` BIFF stream via `olefile`, then
feed those bytes directly into `xlrd`'s own well-tested BIFF parser, skipping only the one broken
navigation step. See `docs/decision-log.md`, 2026-07-20 "RESOLVED" entry, for the full investigation.
