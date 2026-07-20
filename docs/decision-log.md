# Decision log

Short ADR-style entries. Newest first.

## 2026-07-20 — Scan for the real header row instead of assuming row 0

**Context:** With the LibreOffice fallback in place, the live workflow run
progressed past the xlrd failure and actually parsed the real MSE workbook —
but `normalise_headers()` then failed with column 0 containing garbled binary
text and 11 "Unnamed" columns. This is the classic signature of a banner/title
row sitting above the real header row, which pandas' default `header=0`
doesn't account for.

**Decision:** `read_workbook()` now reads with `header=None` (every row as
plain data) and a new `_promote_header_row()` scans the first
`HEADER_SCAN_MAX_ROWS` (15) rows for the one that actually matches all three
required canonical fields via `HEADER_ALIASES`, promotes that row to the
column headers, and drops everything above and including it. If no matching
row is found in the scan window, the raw frame is returned unchanged so
`normalise_headers()` still raises its existing clear `MissingColumnError`.

**Consequence:** `normalise_headers()` itself is unchanged and still expects a
DataFrame with real column names — the header-row search is a preprocessing
step, not a change to that function's contract, so existing tests for it
needed no changes. This is the third fix needed to parse a real MSE file,
after (1) the OLE2/xlrd routing and (2) the LibreOffice fallback — each prior
fix was necessary but not sufficient on its own; this one was only visible
once the first two were in place and parsing progressed far enough to reach
real column data.

## 2026-07-20 — Fall back to LibreOffice when xlrd rejects a genuine .xls file

**Context:** The `ignore_workbook_corruption` fix (below) did not resolve the
real failure — reading xlrd's own source (`compdoc.py`) showed that flag only
guards a check in `_locate_stream`, not the `_get_stream` directory-chain check
that MSE's real file actually trips (`directory corruption: seen[0] == 2`).
There is no xlrd-level escape hatch for this specific check; it's a hard
limitation of xlrd's compound-document parser, which is unmaintained.

**Decision:** Try xlrd first (fast, no subprocess) for OLE2 files; if it raises
any exception, fall back to converting the file to `.xlsx` via headless
LibreOffice (`soffice --headless --convert-to xlsx`) and reading that with
openpyxl instead. LibreOffice's own OLE2 parser is materially more tolerant of
real-world exporter quirks. The GitHub Actions workflow now installs
`libreoffice-calc` via apt before running the script.

**Consequence:** Adds a system-level dependency (LibreOffice) and a subprocess
call, only exercised as a fallback (well-formed files never pay this cost).
`soffice` can exit 0 while still failing to convert ("source file could not be
loaded" printed to stdout) — `convert_xls_to_xlsx_via_libreoffice()` explicitly
checks the expected output file exists rather than trusting the exit code
alone. The real end-to-end LibreOffice conversion path could not be verified
in the development sandbox (headless `soffice` fails there entirely, even for
a trivial .txt→.pdf conversion — an environment restriction, not a code bug);
it is verified against GitHub Actions' standard ubuntu-latest runner instead
(see `docs/qa.md`).

## 2026-07-20 — Route OLE2 .xls files through xlrd with ignore_workbook_corruption (superseded)

**Context:** First live GitHub Actions run against a real MSE archive URL
(`https://cdn.borzamalta.com.mt/download/statistics/trading%20statistics%202026.xls`,
surfaced during the original research in `docs/plan.md`) downloaded successfully
(`Content-Type: application/vnd.ms-excel`, correct OLE2 magic bytes, 1,662,976
bytes = exactly 406 × 4096) but `xlrd` raised `directory corruption: seen[0] == 2`
while parsing it.

**Decision:** This is a known xlrd strictness issue with compound-document
directory chains in some real-world exported `.xls` files, not evidence the
file itself is broken. `read_workbook()` now detects the OLE2 magic number and
explicitly passes `engine="xlrd", engine_kwargs={"ignore_workbook_corruption": True}`
for those files, leaving `.xlsx` (zip-based) files to pandas' normal engine
auto-detection.

**Consequence:** Superseded the same day by the entry above — a second live run
showed this specific error is not covered by `ignore_workbook_corruption` at
all (see above). Left in the log for the record of what was tried and why it
didn't fully work; the code still attempts this fast path first before falling
back to LibreOffice, since it does help for the corruption classes it actually
guards.

## 2026-07-20 — Document the live-verification gap instead of guessing silently

**Context:** Development sandbox network policy returns HTTP 403 for all requests to
`borzamalta.com.mt` (and its CDN), so the archive page HTML and real workbook column names could not be
fetched or inspected while building this project.

**Decision:** Build `normalise_headers()` to accept several plausible header spellings (sourced from
`docs/plan.md`'s research) and fail loudly, with a named missing-column error, if none match — rather than
assume one exact spelling. Document the gap explicitly in `docs/spec.md` and `docs/qa.md`'s manual
verification checklist, instead of presenting untested assumptions as confirmed behaviour.

**Consequence:** The first real run (locally, or the first scheduled Action run) is the actual verification
of the header-mapping assumptions. If it fails, the fix is to extend the header-variant list and add a
regression test — not to relax the "fail loudly" invariant.

## 2026-07-20 — JSON (GitHub Pages) as primary output, CSV as secondary

**Context:** Portfolio Performance supports both a manual CSV import and an automatically-polled JSON
quote-feed provider (`$[*].date`, `$[*].close`).

**Decision:** Make JSON via GitHub Pages the primary, automated path. Keep CSV as an optional output only,
for local validation — not as a first-class integration target.

**Consequence:** All schema-stability guarantees (`docs/architecture.md` § invariants) apply primarily to
the JSON contract. CSV output must stay consistent with it but is not independently versioned.

## 2026-07-20 — Yearly archive workbooks as the source of truth, not the daily Price List

**Context:** MSE publishes `Price_List.xls` as a daily snapshot (no date column, overwritten daily) and
separate yearly "Daily Trading Summary" archive workbooks (category 33) that do contain a date column.

**Decision:** Use the yearly archive as the sole source of historical data. `Price_List.xls` is out of
scope entirely (not even used for "today's price" top-up), to keep the source-of-truth simple and avoid
maintaining two parsing paths for one project.

**Consequence:** The feed's data freshness is bounded by how promptly MSE publishes the current year's
archive file, not by daily price-list availability.

## 2026-07-20 — GitHub Pages + Actions, no third-party hosting

**Context:** The project needs a stable public HTTPS URL and a way to refresh it on a schedule, with no
budget for and no need for a dedicated server.

**Decision:** Publish from `docs/` in this repo via GitHub Pages; refresh via a scheduled GitHub Actions
workflow that commits only when the generated feed content changed.

**Consequence:** The published URL is tied to this repo's name and Pages configuration
(`https://heyvinay.github.io/MSESharePrices/json/BOV.json`, assuming Pages is configured to serve from
`docs/` on the default branch). Changing the repo name or Pages source later requires updating the PP
configuration and this doc.
