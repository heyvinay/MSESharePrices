# Decision log

Short ADR-style entries. Newest first.

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
