# Decision log

Short ADR-style entries. Newest first.

## 2026-07-20 — Fix: git diff --quiet misses a brand-new untracked file

**Context:** The first genuinely successful run (after the olefile-bypass fix landed) generated
`docs/json/BOV.json` correctly, but the "Commit updated feed if changed" step logged "No changes ...;
nothing to commit." and never pushed the file. `docs/json/BOV.json` didn't exist in the repo before this
run — `git diff --quiet -- <path>` only detects changes to already-tracked files; it doesn't consider an
untracked new file a "diff" at all, so the guard silently (and incorrectly) skipped the commit.

**Decision:** Stage the file first (`git add`), then check `git diff --cached --quiet` (the staged diff)
instead of the working-tree diff. A staged new file does show up as a diff against `HEAD`, so this
correctly covers both "brand new file" and "changed existing file" cases.

**Consequence:** This bug was independent of, and unrelated to, every `.xls`/OLE2 parsing issue
investigated earlier — the feed generation itself was correct on the run that exposed this; only the
commit step's change-detection was wrong, and only on the very first run (once the file exists and is
tracked, the original `git diff --quiet` form would have worked correctly for all subsequent runs).

## 2026-07-20 — RESOLVED: real archive URL found, real root cause fixed, real data confirmed

**Context:** The user found the real, correct download URL by browsing MSE's site
directly: `https://cdn.borzamalta.com.mt/download/archives/Trading-Statistics/Trading-StatisticsYYYY.zip`
(a `.zip`, not a bare `.xls` as every previously-guessed URL assumed). This superseded
the "guessed URLs are likely wrong" entry below — that entry was right that the
guessed URLs were bad, but its "the file is probably corrupted" hypothesis for
the *real* URL turned out to be wrong once tested against the actual source.

**What the zip needed:** `process_workbook()` now detects a zip that isn't
itself a valid xlsx and extracts `.xls`/`.xlsx` members from inside it (see
the zip-handling entry below).

**The real root cause, found via user-uploaded real files:** the extracted
`.xls` (authored by **Crystal Reports**, per its own OLE2 metadata — a known
source of non-standard-but-valid `.xls` exports) makes `xlrd`'s own
directory-stream navigation trip over a **genuinely cyclic sector chain**.
This was confirmed two ways:
- Naively bypassing xlrd's "seen sector" cycle-detection (thinking it was a
  false-positive corruption check, per the earlier `ignore_workbook_corruption`
  investigation) caused a real infinite loop that consumed **11.6GB of RAM**
  in this sandbox before being killed. The check is real cycle-detection, not
  just an overzealous corruption flag.
- The user opened the exact same file in real Microsoft Excel and it rendered
  perfectly — a clean table with real headers (`Symbol code`, `Daily High`,
  `Daily  Low`, `Open Price`, `Close Price`, `CHANGE  in cents`, `TWAP`,
  `DEALS`, `VOLUME`, `VALUE`, `MARKET CODE *`, `DATE`) and real data (`BOV`,
  `1.720`, ..., `03-Jan-2025`). Excel tolerates this defect; `xlrd` and
  LibreOffice's headless conversion (independently, in different ways) do not.

**The fix:** `read_xls_via_olefile_bypass()` (in `src/mse_pp_feed.py`) uses the
`olefile` library — which, like Excel, does not depend on walking the same
directory-stream chain to locate named streams — to extract the raw
`"Workbook"` BIFF stream bytes directly, then feeds those bytes straight into
`xlrd`'s own (well-tested) `Book` object, bypassing only the one broken
compound-document-navigation step. `read_workbook()`'s fallback order is now:
(1) `xlrd`'s normal entrypoint, fast path for well-formed files; (2) the
`olefile` bypass, the fix for this real defect; (3) the LibreOffice conversion,
kept only as a last resort for whatever might defeat both of the above.

**Verified against the real files** (`tests/fixtures/trading_statistics_2026_sample.xls`,
committed as a regression fixture — MSE market data is public): the full
pipeline (`process_workbook` → `dedupe_and_sort` → JSON) correctly recovers
132 real BOV closing-price rows spanning 2026-01-05 through 2026-07-20, prices
€1.91–€2.13, matching the range visible in the user's own Excel screenshot.

**Consequence:** The live-verification gap that shaped much of this project's
early development (`docs/spec.md`'s original "MSE blocked automated requests"
caveat) is closed. The workflow's default (non-`manual_urls`) scheduled run
now targets `Trading-Statistics<current-year>.zip` directly, since
`discover_urls()` against the live HTML page still returns nothing (the page
is likely JS-rendered) and this is the only proven-working source.

## 2026-07-20 — Conclusion: the guessed archive URLs are likely wrong, not a parsing bug

**Context:** After confirming the OLE2/xlrd routing, the LibreOffice fallback, and
header-row scanning all work correctly, `trading statistics 2026.xls` still
produced only garbled OLE2-internal text (`Root Entry`/`Workbook`/
`SummaryInformation`/`MsoDataStore`) with zero real content anywhere in the
first 15 rows. Two differential tests were run to isolate the cause:

1. **`trading statistics 2025.xls`** (a fully-closed prior year, ruling out
   "2026 is still being written"): same 100% garbage, zero real content.
2. **`Daily_Market_Extract.xls`** (a different real MSE file): rows 0-5 show
   the same OLE2 garbage, but **rows 6-14 contain genuine, readable MSE
   content** — real company names and prices (`BMIT Technologies p.l.c. Ord
   € 0.10`, `Harvest Technology p.l.c. Ord € 0.50`, `RS2 plc Pref € 0.06`,
   `LifeStar Insurance p.l.c.`, `APS Bank plc Ordinary Shares € 0.25`, `MIDI
   plc Secured €... 2026`, etc.) — it's an "Official List" narrative document
   (security names + ex-dividend dates), not a Symbol/Date/Close price table,
   but it proves the full pipeline (download → OLE2 detection → LibreOffice
   conversion → row scanning) genuinely works end-to-end against a real file.

**Decision:** The pipeline is not the problem. The two `trading statistics
YYYY.xls` URLs — surfaced by AI web research in `docs/plan.md`, never
confirmed by a human actually clicking through MSE's site — are almost
certainly wrong or stale for **both** tested years, which rules out "current
year not finalized" as an explanation (a genuinely wrong/dead URL would
plausibly serve the same placeholder/generic OLE2 document regardless of the
year in the filename). Continuing to guess more candidate URLs blindly was not
productive and this was stopped in favour of documenting the finding clearly.

**Consequence:** Getting real historical daily-close data requires a
human-confirmed download URL from MSE's actual archive page
(https://www.borzamalta.com.mt/publications-and-statistics?category=33),
which this sandbox and the GitHub Actions runner's automated request to that
HTML page could not extract (see the discover_urls entry in
`docs/architecture.md` § risks — the page returns zero `<a href>` `.xls`
links to an automated fetch, consistent with a JS-rendered page). The
`--manual-url` CLI flag and the workflow's `manual_urls` dispatch input exist
specifically for this: once a human obtains the correct URL by browsing the
archive page directly, the exact same pipeline validated in this session
should work against it unchanged.

## 2026-07-20 — Remove ignore_workbook_corruption: it caused silent data corruption

**Context:** After the header-row-scan fix (below), the live workflow still
failed, but with a new and much more serious symptom: the row dump showed
literal OLE2 container internals — the strings `Root Entry`, `Workbook`,
`SummaryInformation`, `MsoDataStore` — appearing as cell *values*. Those are
OLE2 compound-document stream/directory names, not spreadsheet content. This
meant `read_workbook()`'s `xlrd` attempt was **succeeding** (no exception, so
the LibreOffice fallback never ran) while silently returning garbage.

**Decision:** `ignore_workbook_corruption=True` does not fix the directory-chain
issue this file triggers — it only suppresses xlrd's own safety check, letting
it proceed with a broken understanding of the compound file's structure and
return corrupted data instead of raising. Removed that flag entirely; `xlrd` is
now called in its default strict mode, which correctly raises on this file
every time, which is what triggers the (actually correct) LibreOffice fallback.

**Consequence:** A loud, deterministic failure from `xlrd` is the desired
outcome for this file — silence would be far worse than an exception here,
since it would publish wrong closing prices into a feed a real portfolio
depends on. This is the fourth fix in this chain (after: 1. OLE2/xlrd routing,
2. the ignore_workbook_corruption attempt — now reverted, 3. LibreOffice
fallback, 4. header-row scanning) — each prior one was necessary infrastructure
even where a later fix corrected a mistake, since the LibreOffice fallback and
header-row scan are still both needed regardless of this correction.

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
