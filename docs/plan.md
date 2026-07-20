<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I use Portfolio Performance to track my investment.  I need to build a manual scraper to pull in some prices.  eg. [Reports - Malta Stock Exchange](https://www.borzamalta.com.mt/reports/BOV)

Yes — you can build this as a **manual** price source for Portfolio Performance, and Malta Stock Exchange looks workable because it exposes downloadable market files as `.xls` alongside the report pages. Portfolio Performance supports both scraping a table from a webpage and importing from downloadable files when the quote source is not available natively.[^1_1][^1_2][^1_3]

## Best source

For MSE, the cleaner source is likely not the `/reports/BOV` page itself, because that page is mostly announcements for the security rather than a historical price table. The stronger candidate is the exchange’s published statistics/download area, which exposes files like `Daily_Market_Extract.xls` and annual trading statistics workbooks.[^1_4][^1_3][^1_1]

The exchange also has a Publications and Statistics area for daily “Prices \& Yields” and related price lists, which suggests there is structured end-of-day data you can reuse instead of scraping HTML visually. That is usually more stable than scraping a rendered page and is better for a manual workflow you need to maintain over time.[^1_5][^1_6][^1_7]

## Portfolio Performance fit

Portfolio Performance documents two relevant approaches: automatic scraping from a page URL when a table is directly accessible, and manual scraping when the site uses a layout that PP cannot ingest automatically. Its manual workflow is essentially copying the page source or data text into the import dialog, but it also points users toward CSV/JSON/file-based methods when those are available.[^1_2]

In your case, the practical order is:

1. Try the downloadable MSE extract or price-list file first.
2. If the file is awkward, transform it into CSV outside PP.
3. Use HTML scraping only as a fallback.[^1_3][^1_2]

## Practical approach

A robust manual scraper for BOV would usually do this:

- Download `Daily_Market_Extract.xls` or the daily price list from the MSE statistics area.[^1_6][^1_3]
- Filter rows for the instrument code, such as `BOV`, and capture at least date and close/last price.[^1_3]
- Convert the result into a simple CSV format that Portfolio Performance can map during import. Portfolio Performance explicitly supports file-based quote ingestion as one of the alternatives when direct feeds are unavailable.[^1_2]

If you must scrape HTML, use a page that actually contains price rows. The fetched `/reports/BOV` page content shown here does not expose quote history; it exposes announcement history, so it is the wrong target for price scraping.[^1_1]

## Recommendation

I’d recommend building this around the MSE downloadable extract, not the BOV reports page. That will give you a simpler, more supportable manual pipeline for Portfolio Performance, especially in a regulated environment where you probably want predictable inputs and fewer brittle selectors.[^1_1][^1_2][^1_3]

Would you like me to sketch the exact CSV schema Portfolio Performance expects and a small Python scraper/converter for BOV from the MSE daily extract?
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/table-website/

[^1_2]: https://help.portfolio-performance.info/en/how-to/

[^1_3]: https://cdn.borzamalta.com.mt/download/statistics/Daily_Market_Extract.xls

[^1_4]: https://cdn.borzamalta.com.mt/download/statistics/trading statistics 2026.xls

[^1_5]: https://www.borzamalta.com.mt/publications-and-statistics?category=14

[^1_6]: https://www.borzamalta.com.mt/publications-and-statistics?category=61

[^1_7]: https://www.borzamalta.com.mt/publications-and-statistics?category=46

[^1_8]: https://bourva.com/exchange/mtse/bov/

[^1_9]: https://www.investing.com/equities/bank-of-vallet

[^1_10]: https://www.borzamalta.com.mt/?handler=TradingBoard

[^1_11]: https://www.borzamalta.com.mt/publications-and-statistics

[^1_12]: https://www.borzamalta.com.mt/reports/BV30B

[^1_13]: https://www.borzamalta.com.mt/publications-and-statistics?category=24

[^1_14]: https://fr.investing.com/equities/bank-of-vallet

[^1_15]: https://www.borzamalta.com.mt/reports/AG35A

[^1_16]: https://www.marketscreener.com/quote/stock/BANK-OF-VALLETTA-P-L-C-64303144/quotes/

[^1_17]: https://borzamalta.com.mt/download-all-trades

[^1_18]: https://borzamalta.com.mt/

[^1_19]: https://www.borzamalta.com.mt/publications-and-statistics?category=39

[^1_20]: https://cdn.borzamalta.com.mt/download/statistics/ystats.xls

[^1_21]: https://www.borzamalta.com.mt/publications-and-statistics?category=11

[^1_22]: https://cdn.borzamalta.com.mt/download/Official_list/official_list.pdf

[^1_23]: https://cdn.borzamalta.com.mt/download/announcements/AXG78.pdf

[^1_24]: https://www.borzamalta.com.mt/reports/BV31A


---

# Does this have historical [Price List.xls](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fcdn.borzamalta.com.mt%2Fdownload%2Fstatistics%2FPrice_List%2FPrice%2520List.xls&wdOrigin=BROWSELINK)

No — that specific `Price List.xls` is a **daily snapshot**, not a full historical time series, but you can combine it with the exchange’s other statistics files to build history.[^2_1][^2_2][^2_3]

## What `Price List.xls` contains

- The file is described by MSE as: “Prices of securities which are admitted to trading. Issued daily. Extracts from our Price List issued daily.”[^2_1]
- The XLS itself holds instrument-level data (ISIN, amounts issued, price notes like ex-dividend), but there is **no date column** and no multi-day history; it’s meant to represent the current day’s official prices.[^2_2]

So if you download `Price List.xls` today, you get **today’s prices only**; tomorrow’s file overwrites those values, it doesn’t append a new row per date.[^2_2][^2_1]

## Where historical data lives

For history, the exchange exposes separate statistics workbooks, for example:

- Annual or multi-period **trading statistics** such as `trading statistics 2026.xls`, which include per‑instrument fields like open, close, high, low, change, volume, value, and trade date.[^2_3]
- Other statistics like `ystats.xls` and `extracts.xls`, which are used for additional historical reporting.[^2_4][^2_5]

A row from `trading statistics 2026.xls` shows the pattern: instrument code, last price data fields, and a specific date such as `05-Jan-2026`. That is exactly the kind of structure you need for historical quotes.[^2_3]

## How to use this for Portfolio Performance

For BOV or any other Malta-listed equity:

1. Use `trading statistics YYYY.xls` (or similar statistics files) to pull historical prices, since they **do** contain a date column and per-day data.[^2_5][^2_3]
2. Use `Price List.xls` only as a convenient **latest price snapshot**, if you want to top up your history with the most recent trading day; treat it as “today’s official list” rather than a timeseries.[^2_1][^2_2]
3. Convert the relevant rows (e.g., instrument code BOV) into a CSV with `date` and `close/last` columns, and import that into Portfolio Performance as historical quotes.[^2_6][^2_3]

If you’d like, I can outline a small Python script that takes `trading statistics YYYY.xls` plus today’s `Price List.xls` and emits a clean CSV just for BOV that you can drop straight into Portfolio Performance.
<span style="display:none">[^2_10][^2_11][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://www.borzamalta.com.mt/publications-and-statistics?category=14

[^2_2]: https://cdn.borzamalta.com.mt/download/statistics/Price_List/Price%20List.xls

[^2_3]: https://cdn.borzamalta.com.mt/download/statistics/trading statistics 2026.xls

[^2_4]: https://cdn.borzamalta.com.mt/download/statistics/extracts.xls

[^2_5]: https://cdn.borzamalta.com.mt/download/statistics/ystats.xls

[^2_6]: https://help.portfolio-performance.info/en/how-to/

[^2_7]: https://www.borzamalta.com.mt/publications-and-statistics

[^2_8]: https://cdn.borzamalta.com.mt/download/statistics/Price_List/Price%20List.pdf

[^2_9]: https://www.borzamalta.com.mt/publications-and-statistics?category=61

[^2_10]: https://www.borzamalta.com.mt/publications-and-statistics?category=11

[^2_11]: https://cdn.borzamalta.com.mt/download/statistics/CIS_price_list.xls


---

# [Publications and Statistics - Malta Stock Exchange](https://www.borzamalta.com.mt/publications-and-statistics?category=33)

Yes — **category 33 is the historical archive** you want. It is the “Daily Trading Summary - Yearly Archive” and lists downloadable yearly files from 2025 all the way back to 1992.[^3_1]

## What it gives you

This archive is much better for historical quote building than the daily `Price List.xls`, because it is explicitly organized by **yearly historical summaries** rather than a current-day snapshot. The page exposes one downloadable file per year, including 2025, 2024, 2023, and older years down to 1992.[^3_1]

That means you should be able to build a long price history for instruments like BOV by downloading the annual files and extracting the rows for the ticker you care about.[^3_1]

## Why this is useful

For Portfolio Performance, this is the right shape of source if each annual workbook contains daily rows with trade date and price fields. That is materially more useful than `Price List.xls`, which MSE describes as a daily issued list rather than a historical archive.[^3_2][^3_1]

A sensible workflow is:

- Use category 33 yearly archives for historical backfill.[^3_1]
- Use the current daily price list only for the latest day if needed.[^3_2]
- Merge both into one CSV for Portfolio Performance import.[^3_3]


## Recommendation

I’d treat category 33 as your **primary source of truth** for historical Malta Stock Exchange prices. The next practical step is to inspect one yearly download and confirm the exact columns for date, symbol, and closing or last traded price before you automate extraction.[^3_1]

Would you like me to inspect one of those yearly files and map the exact columns needed for a BOV importer?
<span style="display:none">[^3_10][^3_11][^3_4][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/table-website/

[^3_2]: https://www.borzamalta.com.mt/publications-and-statistics?category=14

[^3_3]: https://help.portfolio-performance.info/en/how-to/

[^3_4]: https://www.borzamalta.com.mt/publications-and-statistics

[^3_5]: https://www.borzamalta.com.mt/publications-and-statistics?category=46

[^3_6]: https://cc.com.mt/markets/

[^3_7]: https://www.borzamalta.com.mt/publications-and-statistics?category=12

[^3_8]: https://www.borzamalta.com.mt/reports/AX33A

[^3_9]: https://www.borzamalta.com.mt/

[^3_10]: https://masa.mt/statistics/

[^3_11]: https://cdn.borzamalta.com.mt/download/Official_list/official_list.pdf


---

# yes.. build me a BOV importer - should I use powershell or python?

Use **Python**, not PowerShell, for the importer. Given your workflow and comfort with Python plus CLI tooling, Python will be easier to test, extend, and reuse when you later add more Malta instruments or combine yearly archive files.

The MSE annual trading-statistics workbook already exposes the exact fields you need for BOV: `Symbol code`, `Close Price`, and `DATE`, with rows like `BOV | 1.920 | 05-Jan-2026`. That makes Python a natural fit because it can read XLS files, filter `Symbol code == BOV`, normalize dates, and emit a Portfolio Performance-friendly CSV with little friction. [^4_1]

## Recommendation

Pick Python if your goal is a maintainable importer with:

- yearly backfill from the MSE archive page, which lists annual “Daily Trading Summary” downloads from 2025 back to 1992,[^4_2]
- row filtering for `BOV`,[^4_1]
- CSV output for Portfolio Performance historical quotes, which supports file-based quote imports when direct feeds are unavailable.[^4_1]

PowerShell is acceptable if you want a Windows-only scheduled task and very tight Microsoft-native ops, but it is weaker for XLS parsing and data cleanup than Python. For this use case, PowerShell is better as a wrapper that schedules or launches the Python script, not as the main data-processing language.[^4_1]

## Why Python wins

Python gives you better libraries for spreadsheet parsing and transformation, which matters because the MSE files are classic `.xls` workbooks rather than a clean JSON API. The source structure is tabular and repetitive, so Python can turn it into a small, deterministic ETL job instead of a brittle screen scrape.[^4_1]

It also fits your preference for lightweight, structured tooling: one script, clear inputs, clear outputs, easy to review, and easy to evolve into “all Malta equities” later. That aligns with your stated preference for spec-driven but still lean development patterns.

## BOV importer shape

The importer should do four things:

1. Download one or more annual “Daily Trading Summary” files from the MSE archive.[^4_2]
2. Read the workbook and keep only rows where `Symbol code` is `BOV`.[^4_1]
3. Transform `DATE` into ISO format and map `Close Price` to `close`.[^4_1]
4. Write a CSV for Portfolio Performance import. Portfolio Performance documents file-based quote ingestion as a valid alternative to direct quote feeds.[^4_1]

A minimal output schema should be:

- `date`
- `close`

Example:

- `2026-01-05,1.920`
- `2026-01-06,1.910`[^4_1]


## Suggested architecture

I’d structure it like this:

- `config`: ticker `BOV`, start year, end year.
- `fetch`: pull the annual XLS files.
- `parse`: read workbook rows and normalize headers.
- `filter`: keep only `BOV`.
- `export`: write `bov_quotes.csv`.

That design keeps the script simple now, while making it easy to extend to APS, HSB, GO, or a full Malta watchlist later because the same workbook includes all those symbols in the same schema.[^4_1]

## Practical choice

So the short answer is: **Python for the importer, PowerShell only for automation around it**. The source archive is workbook-based and the actual data columns are already well suited to a Python ETL script.[^4_2][^4_1]

Would you like me to generate the actual Python importer script next, with a CSV output format tailored for Portfolio Performance?

<div align="center">⁂</div>

[^4_1]: https://help.portfolio-performance.info/en/how-to/

[^4_2]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/table-website/


---

# can you draft a prompt I can use in codex for this.. and also in claude code

Yes — below are two prompts you can paste directly, one tuned for **Codex** and one for **Claude Code**. I’ve aimed them at a lightweight, spec-driven build with Python as the implementation language, which fits both your working style and the MSE source format.[^5_1][^5_2]

## Codex prompt

Use this when you want Codex to generate the project in one go with clear acceptance criteria.

```text
Build a Python 3 command-line importer for Portfolio Performance that downloads historical prices for Bank of Valletta plc (ticker/symbol code: BOV) from the Malta Stock Exchange Daily Trading Summary yearly archive.

Context
- Source archive page: https://www.borzamalta.com.mt/publications-and-statistics?category=33
- The archive contains yearly “Daily Trading Summary” downloads.
- The yearly XLS data includes columns such as:
  - Symbol code
  - DATE
  - Close Price
- Example requirement: filter rows where Symbol code == BOV and export historical quotes for Portfolio Performance.
- Portfolio Performance historical quote CSV only needs:
  - date
  - quote
- Output date format should be ISO: YYYY-MM-DD
- Output quote should use decimal point, not comma

What I want
- Create a small, maintainable Python project.
- Use Python rather than PowerShell.
- Prefer simple dependencies; minimise complexity.
- The script should:
  1. Discover or accept yearly archive file URLs
  2. Download one or more yearly XLS files
  3. Parse the workbook(s)
  4. Filter rows for Symbol code = BOV
  5. Extract DATE and Close Price
  6. Normalise dates to YYYY-MM-DD
  7. Remove blank rows, duplicate dates, and invalid prices
  8. Sort ascending by date
  9. Write a CSV for Portfolio Performance with headers:
     date,quote
- Add command-line arguments:
  - --start-year
  - --end-year
  - --symbol (default BOV)
  - --output
- If the archive page structure is awkward, allow a fallback mode where I manually provide one or more XLS URLs.
- Include basic logging to console.
- Fail clearly if required columns are missing.

Project requirements
- Produce:
  - main Python script
  - requirements.txt
  - README.md
- Use pathlib and requests.
- Use pandas if helpful for XLS parsing; keep it pragmatic.
- Make the code easy to extend later for other Malta Stock Exchange symbols.
- Do not over-engineer.
- Keep functions small and clear.

Acceptance criteria
- Running the tool should produce a CSV compatible with Portfolio Performance historical quote import.
- CSV schema must be exactly:
  date,quote
- Rows must contain one quote per trading date for BOV.
- Duplicates by date should be resolved deterministically, keeping the last valid quote found.
- The script should work even if some yearly files have minor header inconsistencies; add a small header normalisation layer.
- README must include:
  - setup
  - install
  - example commands
  - how to import the CSV into Portfolio Performance

Please first output:
1. a short implementation plan,
2. the proposed project structure,
3. then the code files in full.
```


## Claude Code prompt

Use this when you want Claude Code to work more **surgically** and interact with the repo in steps rather than dumping everything blindly. That suits your usual Claude Code workflow better.[^5_3]

```text
I want you to build a small Python CLI importer in this repo.

Task
Create a maintainable Python 3 tool that downloads and converts Malta Stock Exchange historical prices for Bank of Valletta plc (symbol code BOV) into a CSV that I can import into Portfolio Performance as historical quotes.

Source context
- Archive page: https://www.borzamalta.com.mt/publications-and-statistics?category=33
- This is the Daily Trading Summary yearly archive.
- The yearly XLS files contain tabular rows with fields including:
  - Symbol code
  - DATE
  - Close Price
- Portfolio Performance historical quote CSV needs:
  - date
  - quote
- Output format:
  - date as YYYY-MM-DD
  - quote as decimal with dot separator
  - header row: date,quote

Implementation constraints
- Use Python, not PowerShell.
- Keep the solution lightweight and structured.
- Prefer a simple CLI script plus small helper functions.
- Use requests for download.
- Use pandas and any required Excel/XLS reader only if needed and justified.
- Make it easy to extend to other symbols later.
- Avoid over-engineering.

Functional requirements
1. Accept CLI arguments:
   - --start-year
   - --end-year
   - --symbol with default BOV
   - --output
   - optional --url for one or more manual XLS URLs
2. Download yearly XLS files from the MSE archive or use provided URLs.
3. Parse each file safely.
4. Normalise headers because yearly files may vary slightly.
5. Filter to rows where Symbol code matches the requested symbol.
6. Extract DATE and Close Price.
7. Clean the dataset:
   - drop empty dates
   - drop empty prices
   - coerce price to numeric
   - normalise date to YYYY-MM-DD
   - sort ascending
   - deduplicate by date, keeping the last valid row
8. Export CSV with exactly:
   date,quote
9. Print a short run summary:
   - files processed
   - rows matched
   - date range exported
   - output path

Engineering requirements
- Add:
  - requirements.txt
  - README.md
- README should contain:
  - setup instructions
  - install command
  - sample usage
  - how to import into Portfolio Performance
  - assumptions and known limitations

Working style
- First inspect the repo and tell me:
  1. what files you plan to create or change,
  2. your implementation plan,
  3. any dependency choices.
- Then implement.
- Keep edits surgical and focused.
- Do not introduce unrelated refactors.
- If you hit uncertainty on archive URL discovery, implement a clean fallback that accepts manual XLS URLs and document it.

Validation
- After coding, run the tool in a dry-run or test mode where possible.
- If live download is not feasible, at least validate parsing logic against the expected column names and explain any assumptions.
- Show me the exact command I should run for:
  - BOV for 2024-2026
  - a custom symbol
  - manual URLs fallback

Important
- Prioritise a working importer over elegance.
- Keep the code clear enough that I can later schedule it or wrap it in PowerShell/Task Scheduler if I want.
```


## Which to use where

Use the **Codex** prompt when you want a more self-contained “generate the artefacts” pass. It is more explicit about deliverables and acceptance criteria, which helps on a greenfield utility like this.

Use the **Claude Code** prompt when you already have a repo open and want disciplined, low-noise implementation with tighter control over scope and token usage. That lines up with your preference for short, focused Claude Code sessions and surgical edits.[^5_3]

## Small tweak

One useful addition to either prompt is this line:

- “If you can discover direct yearly download links from the archive page, do so; otherwise add a documented config file or manual URL list.”

That protects you from brittle archive-page parsing while still keeping the importer practical against the MSE yearly archive.[^5_1]

Would you like me to turn one of these into an even tighter **copy-paste build brief** with exact file names and a suggested repo structure?
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_4][^5_5][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^5_2]: https://help.portfolio-performance.info/en/how-to/

[^5_3]: https://www.perplexity.ai/search/ffc8f0a7-2434-4801-b17c-70f5613930bb

[^5_4]: https://help.portfolio-performance.info/en/reference/file/import/csv-import/

[^5_5]: https://www.youtube.com/watch?v=LolF7ees8X0

[^5_6]: https://forum.portfolio-performance.info/t/import-quotes-for-multiple-securities-from-single-csv-file/8060

[^5_7]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/csv-file/

[^5_8]: https://help.portfolio-performance.info/en/how-to/import-gbx/

[^5_9]: https://help.portfolio-performance.info/en/reference/file/import/

[^5_10]: https://help.portfolio-performance.info/en/getting-started/updating-portfolio/

[^5_11]: https://forum.portfolio-performance.info/t/import-open-high-low-close-and-volume-from-csv/28406

[^5_12]: https://forum.portfolio-performance.info/t/import-csv-file/17123

[^5_13]: https://www.borzamalta.com.mt/publications-and-statistics?category=23

[^5_14]: https://www.borzamalta.com.mt/publications-and-statistics

[^5_15]: https://forum.portfolio-performance.info/t/bulk-historical-quotes-csv-import-is-there-an-overwrite-mode-instead-of-add/37481

[^5_16]: https://www.youtube.com/watch?v=hANSRH_LTqY

[^5_17]: https://help.portfolio-performance.info/en/reference/file/export/


---

# the script import directly in peformance portfolio?

Not directly into Portfolio Performance in the sense of “push via API”. Portfolio Performance’s documented path is to **import historical quotes from a CSV file** through the app, or configure a quote feed provider such as a JSON/web source inside the security settings.[^6_1][^6_2][^6_3]

## What the script can do

Your script can absolutely automate **everything up to the final PP ingest step**:

- download MSE yearly files,
- extract BOV prices,
- generate `date,quote` CSV,
- optionally also generate JSON in a format PP can read via its JSON quote feed.[^6_3][^6_4][^6_5]

For plain CSV, the normal PP workflow is still manual: `File > Import > CSV Files`, then map the file as historical quotes. PP’s manual explicitly describes CSV import for historical prices this way.[^6_2][^6_1]

## Best two options

### Option 1: CSV import

This is the simplest and most reliable first version. The script writes a CSV, and you import it into Portfolio Performance when needed.[^6_1][^6_2]

### Option 2: JSON/web feed

If you want it to feel more “direct”, host the output as JSON and point PP’s **JSON Quote Feed Provider** at that URL. PP supports JSON feeds with paths such as `Path to Date = $[*].date` and `Path to Close = $[*].close`.[^6_6][^6_3]

That gives you a near-automatic setup:

- script fetches MSE data,
- script publishes `bov.json`,
- PP reads the JSON URL as its historical quote provider.[^6_6][^6_3]


## Important limitation

Portfolio Performance stores one historical price per day, and CSV import for historical quotes is limited to quote/date style data rather than a richer OHLCV import workflow. A forum discussion also notes there is no native “CSV as ongoing quote source” mode; CSV is for import, whereas ongoing updates are better handled through JSON or webpage-based quote feeds.[^6_7][^6_8]

## Recommendation

For your use case, I’d do this in two stages:

- start with **Python to CSV** so you can validate BOV history quickly,[^6_1]
- then upgrade the script to emit **JSON** and host it somewhere simple, so Portfolio Performance can refresh it as a quote feed with much less manual effort.[^6_3][^6_6]

If you want, I can draft a second prompt that tells Codex or Claude Code to build the **JSON-hosted version** instead of CSV-only.
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/csv-file/

[^6_2]: https://help.portfolio-performance.info/en/reference/file/import/

[^6_3]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/eodhd/

[^6_4]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^6_5]: https://help.portfolio-performance.info/en/how-to/

[^6_6]: https://github.com/havasd/pp-data

[^6_7]: https://forum.portfolio-performance.info/t/import-open-high-low-close-and-volume-from-csv/28406

[^6_8]: https://forum.portfolio-performance.info/t/bulk-historical-quotes-csv-import-is-there-an-overwrite-mode-instead-of-add/37481

[^6_9]: https://www.youtube.com/watch?v=LolF7ees8X0

[^6_10]: https://help.portfolio-performance.info/en/reference/file/import/csv-import/

[^6_11]: https://help.portfolio-performance.info/en/how-to/import-gbx/

[^6_12]: https://forum.portfolio-performance.info/t/import-quotes-for-multiple-securities-from-single-csv-file/8060

[^6_13]: https://forum.portfolio-performance.info/t/csv-import-not-recognising-dates-from-september/37356

[^6_14]: https://forum.portfolio-performance.info/t/historical-data-good-source-for-csv-imports-stooq/37973

[^6_15]: https://forum.portfolio-performance.info/t/export-import-securities/32753

[^6_16]: https://forum.portfolio-performance.info/t/import-data-from-http/25735

[^6_17]: https://github.com/portfolio-performance/portfolio/issues/676


---

# I need automation a much as possible

Then the best setup is **not CSV import** as your main path. For maximum automation, build a Python script that generates a **JSON historical price feed** for BOV, host that JSON at a stable URL, and point Portfolio Performance’s **JSON Quote Feed Provider** to it. PP supports JSON feeds directly and lets you map `date` and `close` fields with JSONPath.[^7_1][^7_2][^7_3]

## Best architecture

Use this pattern:

- Python job downloads Malta Stock Exchange yearly archive data.[^7_4]
- Python job filters BOV rows and writes `bov.json`.[^7_5]
- Host `bov.json` somewhere stable, for example GitHub Pages, a raw GitHub-backed CDN, or another simple HTTPS endpoint. A working community pattern is to host instrument JSON files in GitHub and point PP at them via a CDN-style URL.[^7_6]
- In Portfolio Performance, set the security’s historical quote provider to **JSON** and map:
    - `Path to Date = $[*].date`
    - `Path to Close = $[*].close`[^7_2][^7_6]

That gives you near-full automation because PP can refresh the historical quotes from the URL rather than requiring repeated CSV imports. A forum example also notes that if you maintain a historical quote feed provider, missing quotes get updated whenever you open PP or trigger a quote update.[^7_7]

## Why this is better

CSV import is good for first proof, but it remains a **manual import workflow** inside PP. The JSON provider is much closer to what you want because once configured, the ongoing refresh happens from the URL rather than from a file import wizard.[^7_8][^7_1]

This also matches your preference for lightweight but structured automation: one Python ETL job, one published artefact, one PP provider configuration. It is simpler to support than UI scraping and cleaner than trying to automate PP’s desktop UI.

## Practical setup

A minimal JSON payload should look like this:

```json
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]
```

Portfolio Performance documents JSON feeds with paths such as `$[*].date` for dates and `$[*].close` for prices, and similar examples are used for custom or API-based quote feeds.[^7_1][^7_2]

## Hosting choices

The easiest low-friction options are:

- GitHub repo + GitHub Pages or raw/CDN delivery,[^7_6]
- an Azure-hosted static file if you want it under your own governance model, which may suit your Microsoft-first bias better operationally,
- any HTTPS endpoint that serves plain JSON reliably.[^7_1]

For a single BOV feed, GitHub hosting is probably the fastest. For a broader Malta watchlist or internal reuse, Azure static hosting is more enterprise-friendly.[^7_6]

## Recommendation

If your goal is **as much automation as possible**, build:

- a Python script,
- scheduled daily,
- outputting `bov.json`,
- hosted at a stable URL,
- consumed by PP via the JSON quote provider.[^7_2][^7_7][^7_4]

That is the closest thing to a direct, maintainable integration without relying on an official PP write API, which PP does not document for this use case.[^7_9][^7_1]

Would you like me to draft the **exact Codex and Claude Code prompts for the JSON-hosted automated version** rather than the CSV-only version?
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16][^7_17][^7_18][^7_19]</span>

<div align="center">⁂</div>

[^7_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/json/

[^7_2]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/eodhd/

[^7_3]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/

[^7_4]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^7_5]: https://help.portfolio-performance.info/en/how-to/

[^7_6]: https://github.com/havasd/pp-data

[^7_7]: https://forum.portfolio-performance.info/t/adding-json-datafeed-stooq/31942

[^7_8]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/csv-file/

[^7_9]: https://help.portfolio-performance.info/en/reference/file/import/

[^7_10]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/portfolioperformance/

[^7_11]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/alpha-vantage/

[^7_12]: https://dimitristeiner.com/portfolio-performance-price-feed-for-securities/

[^7_13]: https://forum.portfolio-performance.info/t/last-quote-in-different-currency-to-historical/30843

[^7_14]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/morningstar/

[^7_15]: https://help.portfolio-performance.info/en/how-to/gold-prices/

[^7_16]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/table-website/

[^7_17]: https://github.com/portfolio-performance/portfolio/issues/1450

[^7_18]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/yahoo-finance/

[^7_19]: https://forum.portfolio-performance.info/t/format-of-table-for-quote-feed-table-on-web-site/7688


---

# I have a github account - I can create a new public repo for this..

Yes — that is a good fit. A **public GitHub repo + GitHub Pages + Python job** is probably the fastest way to get a mostly automated BOV feed into Portfolio Performance. GitHub Pages can serve static JSON over HTTPS, and Portfolio Performance can consume historical prices from a JSON quote feed using JSONPath mappings such as `$[*].date` and `$[*].close`.[^8_1][^8_2][^8_3][^8_4]

## Best setup

I’d use this structure:

- Public GitHub repo for the code and published data.[^8_2][^8_5]
- Python script that downloads the Malta Stock Exchange yearly archive and produces `docs/bov.json`. The MSE archive page exposes the Daily Trading Summary yearly archive you need.[^8_6][^8_7]
- GitHub Pages enabled from the `docs/` folder or the main branch, so the JSON is reachable by URL. GitHub Pages can expose files directly by path under your site URL.[^8_8][^8_5]
- Portfolio Performance configured to use that JSON URL as the historical quote feed.[^8_4][^8_1]

That gets you close to “set and forget” once the repo and Pages site are live.[^8_1][^8_2]

## Repo layout

A simple layout would be:

- `src/` for the Python script
- `docs/bov.json` for the published feed
- `requirements.txt`
- `README.md`
- optional `.github/workflows/update-bov.yml` for scheduled automation

The key point is that the published JSON must end up at a stable public HTTPS URL, because PP’s JSON feed provider reads from a URL, not from a GitHub repository object directly.[^8_3][^8_4][^8_1]

## Automation level

To maximise automation, add a **GitHub Actions** workflow that runs daily or on demand, regenerates `bov.json`, and commits the updated file back to the repo. That way the feed URL stays constant while the contents refresh automatically. GitHub-hosted static JSON plus scheduled updates is a common pattern for lightweight public data feeds.[^8_2][^8_8]

Compared with repeated CSV imports, this removes the recurring manual step inside Portfolio Performance and leaves only the one-time PP configuration. PP’s JSON quote feed provider is the important piece that makes this worthwhile.[^8_9][^8_1]

## Practical cautions

Because the repo is public, avoid putting secrets in it. If the script only downloads public Malta Stock Exchange files and writes public JSON, a public repo is perfectly reasonable for this use case.[^8_7][^8_2]

Also, GitHub Pages is ideal for **read-only static data**, which matches this problem well. You are not building an API server; you are publishing a static JSON artefact that PP can read.[^8_10][^8_3]

## Recommendation

Your cleanest path is:

1. Create a new public repo.
2. Build the Python importer to output `docs/bov.json`.
3. Enable GitHub Pages.
4. Point Portfolio Performance at the Pages URL with:
    - `Path to Date = $[*].date`
    - `Path to Close = $[*].close`[^8_4][^8_1]
5. Add GitHub Actions later for daily refresh.

That gives you a lightweight, low-cost, highly automated solution with tooling you already use comfortably.[^8_11]

A good repo name would be `mse-pp-feed` or `malta-stock-pp-quotes`. Would you like me to draft the **exact repo structure, GitHub Actions workflow, and Codex/Claude prompts** for this GitHub-hosted version?
<span style="display:none">[^8_12][^8_13][^8_14][^8_15][^8_16][^8_17][^8_18]</span>

<div align="center">⁂</div>

[^8_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/json/

[^8_2]: https://www.youtube.com/watch?v=KfZZDRIb5wE

[^8_3]: https://stackoverflow.com/questions/39199042/serve-json-data-from-github-pages

[^8_4]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/eodhd/

[^8_5]: https://til.simonwillison.net/github/github-pages

[^8_6]: https://www.borzamalta.com.mt/publications-and-statistics?category=23

[^8_7]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^8_8]: https://medium.com/@sourav.ahmed5654/static-json-provider-using-github-page-da971e5f50a2

[^8_9]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/csv-file/

[^8_10]: https://testfairy.com/blog/utilize-github-pages-as-json-api/

[^8_11]: https://www.perplexity.ai/search/9bf3d45d-2cf0-40d9-bd36-1f5179054c05

[^8_12]: https://www.borzamalta.com.mt/publications-and-statistics

[^8_13]: https://www.youtube.com/watch?v=8JvW6AgX09s

[^8_14]: https://medium.com/@peternjuguna76/hosting-a-json-file-on-github-pages-a-step-by-step-guide-52105a5a393a

[^8_15]: https://mahmudul-razib.medium.com/global-static-json-api-on-github-pages-96557d5cabf3

[^8_16]: https://forum.portfolio-performance.info/t/json-from-alpha-vantage/26875

[^8_17]: https://stackoverflow.com/questions/56420630/correct-json-api-format-on-github-pages

[^8_18]: https://cdn.borzamalta.com.mt/download/statistics/Daily_Market_Extract.xls


---

# write a prompt for codex and claude code

Yes — here are two **copy-paste prompts** for the GitHub-hosted, highly automated version. They are aimed at a Python script that builds a static JSON feed from the Malta Stock Exchange yearly archive, publishes it via GitHub Pages, and lets Portfolio Performance consume it through the JSON quote provider. PP supports JSON feeds with JSONPath mappings such as `$[*].date` and `$[*].close`, and MSE category 33 is the Daily Trading Summary yearly archive.[^9_1][^9_2][^9_3]

## Codex prompt

```text
Build a small Python project that creates an automated Portfolio Performance historical quote feed for Bank of Valletta plc (BOV) using Malta Stock Exchange data and GitHub Pages.

Goal
I want a public GitHub repository that:
1. downloads Malta Stock Exchange historical daily trading data for BOV,
2. converts it into a static JSON feed,
3. publishes that JSON via GitHub Pages,
4. allows Portfolio Performance to consume it via the JSON Quote Feed Provider.

Source data
- Malta Stock Exchange archive page:
  https://www.borzamalta.com.mt/publications-and-statistics?category=33
- This page is the Daily Trading Summary yearly archive.
- The yearly XLS files contain tabular rows with fields including:
  - Symbol code
  - DATE
  - Close Price

Portfolio Performance target
- Portfolio Performance supports JSON historical quote feeds.
- JSON must be shaped so that PP can use:
  - Path to Date = $[*].date
  - Path to Close = $[*].close

Desired JSON output
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]

What I want built
Create a lightweight Python 3 project with:
- a CLI script that downloads one or more yearly XLS files,
- parsing and header normalisation,
- filtering by symbol code (default BOV),
- extraction of DATE and Close Price,
- cleaning and deduplication,
- output to JSON for GitHub Pages,
- optional CSV output for local validation,
- a GitHub Actions workflow that refreshes the JSON daily and on manual dispatch,
- repo files and documentation needed for quick setup.

Project requirements
- Keep it simple and maintainable.
- Use Python, not PowerShell.
- Use requests.
- Use pandas if needed for old XLS parsing.
- Make the code easy to extend later for more Malta Stock Exchange symbols.
- Do not over-engineer.
- Fail clearly if required columns are missing.
- Log useful progress to console.

Functional requirements
1. The script must support CLI arguments:
   - --symbol (default BOV)
   - --start-year
   - --end-year
   - --output-json
   - --output-csv
   - --manual-url (repeatable, optional)
2. The script should try to discover yearly archive file URLs from the category 33 page.
3. If discovery is unreliable, support manual URLs as fallback.
4. Normalise headers because workbook column names may vary slightly.
5. Filter rows where Symbol code matches the requested symbol.
6. Extract DATE and Close Price.
7. Convert dates to YYYY-MM-DD.
8. Coerce prices to numeric.
9. Remove invalid rows.
10. Deduplicate by date, keeping the last valid quote.
11. Sort ascending by date.
12. Write JSON using this exact schema:
    [
      { "date": "YYYY-MM-DD", "close": 1.234 }
    ]
13. Optionally write CSV with:
    date,quote

Repository structure
Please create something close to this:
- src/
  - mse_pp_feed.py
- docs/
  - bov.json
  - index.html
- .github/workflows/
  - update-bov.yml
- requirements.txt
- README.md

GitHub Pages requirements
- The JSON should be published from docs/ so it is reachable over GitHub Pages.
- Include a minimal docs/index.html that explains the feed and links to the JSON file.
- Assume the final URL pattern will be:
  https://<github-username>.github.io/<repo-name>/bov.json
  or
  https://<github-username>.github.io/<repo-name>/docs/bov.json
  depending on the Pages setup; document the expected path clearly.

GitHub Actions workflow
- Add a scheduled workflow that runs daily.
- Also allow workflow_dispatch for manual runs.
- The workflow should:
  1. set up Python,
  2. install dependencies,
  3. run the script,
  4. commit updated docs/bov.json if changed.

README requirements
- Setup steps
- Local run command examples
- GitHub Pages setup steps
- GitHub Actions setup notes
- Portfolio Performance configuration steps:
  - Provider: JSON
  - Feed URL: published bov.json URL
  - Path to Date: $[*].date
  - Path to Close: $[*].close
- Troubleshooting section
- Known limitations

Acceptance criteria
- Running the script locally generates a valid bov.json feed.
- The feed schema is compatible with Portfolio Performance JSON quote provider.
- The repository includes an automated daily refresh workflow.
- The repo can be used as a template for other Malta-listed symbols later.
- The result should prioritise working automation over elegance.

Please first output:
1. a short implementation plan,
2. the exact project structure,
3. any assumptions,
4. then all files in full.
```


## Claude Code prompt

```text
I want you to build a lightweight Python automation project in this repository.

Mission
Create an automated historical quote feed for Portfolio Performance using Malta Stock Exchange archive data for Bank of Valletta plc (symbol code BOV), published via GitHub Pages as static JSON.

Business outcome
I want as much automation as possible.
The end state should be:
- Python script updates BOV historical prices from MSE archive data,
- GitHub Actions runs it daily,
- docs/bov.json is published via GitHub Pages,
- Portfolio Performance reads it via JSON quote feed,
- I do not want recurring manual CSV imports.

Source context
- Malta Stock Exchange yearly archive:
  https://www.borzamalta.com.mt/publications-and-statistics?category=33
- This is the Daily Trading Summary yearly archive.
- The yearly XLS files contain fields such as:
  - Symbol code
  - DATE
  - Close Price

Portfolio Performance target format
- Historical quote provider: JSON
- JSONPath mappings:
  - Path to Date = $[*].date
  - Path to Close = $[*].close

Target JSON shape
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]

Constraints
- Use Python, not PowerShell.
- Keep the solution lightweight and structured.
- Use requests for downloads.
- Use pandas and required XLS reader only if justified.
- Make it easy to extend later to other MSE symbols.
- Avoid unrelated refactors.
- Prioritise a working automated feed over cleverness.

Build requirements
1. Create a Python CLI script.
2. Discover yearly XLS download links from the MSE archive page where feasible.
3. Add a clean fallback to accept one or more manual XLS URLs if discovery is unreliable.
4. Parse workbook data safely.
5. Normalise headers to handle minor yearly variations.
6. Filter rows where Symbol code == requested symbol, default BOV.
7. Extract DATE and Close Price.
8. Clean data:
   - drop blank rows
   - coerce prices to numeric
   - normalise dates to YYYY-MM-DD
   - sort ascending
   - deduplicate by date, keeping the last valid row
9. Write:
   - docs/bov.json in this format:
     [
       { "date": "YYYY-MM-DD", "close": 1.234 }
     ]
   - optional CSV validation output with:
     date,quote
10. Create a minimal docs/index.html describing the feed and linking to bov.json.
11. Add a GitHub Actions workflow that:
   - runs daily,
   - supports manual dispatch,
   - installs dependencies,
   - runs the script,
   - commits updated feed files if changed.
12. Add README.md with:
   - setup
   - local usage
   - GitHub Pages setup
   - GitHub Actions notes
   - Portfolio Performance configuration
   - assumptions and limitations

Expected file structure
- src/mse_pp_feed.py
- docs/bov.json
- docs/index.html
- .github/workflows/update-bov.yml
- requirements.txt
- README.md

Portfolio Performance setup that this project should support
- Provider = JSON
- Feed URL = published GitHub Pages URL to bov.json
- Path to Date = $[*].date
- Path to Close = $[*].close

Working style
- First inspect the repo and tell me:
  1. what files you will create or change,
  2. your implementation plan,
  3. dependency choices,
  4. assumptions or risks about MSE archive link discovery.
- Then implement.
- Keep edits surgical and focused.
- Do not change unrelated files.
- If live download is partially blocked, still implement the full project and document assumptions clearly.

Validation
- Validate the JSON structure.
- Validate that dates are ISO formatted.
- Validate that records are sorted ascending.
- Validate that duplicate dates are removed.
- Show me the exact commands to:
  - run locally for BOV,
  - run for another symbol,
  - run using manual XLS URLs,
  - test the generated JSON URL in Portfolio Performance.

Please provide:
1. implementation plan,
2. then code changes,
3. then a short usage section with exact commands.
```


## Small tweak

If you want to make either prompt even stronger, add this line near the top:

- “Prefer publishing JSON under `docs/json/bov.json` if that keeps the repo tidy, but document the final GitHub Pages URL exactly.”

That helps keep room for later expansion to multiple Malta symbols while still matching PP’s JSON provider pattern. GitHub-hosted static quote feeds are already used in the wild for Portfolio Performance, and the PP JSON provider works with simple arrays of objects keyed by date and close.[^9_2][^9_4][^9_5]

## Best choice

Use the **Claude Code** prompt if you want tighter stepwise control inside a repo. That matches your preference for structured, focused implementation work.[^9_6]

Use the **Codex** prompt if you want a more one-shot repo scaffold with workflow files and docs generated in one pass. That fits your interest in using Codex for automation-oriented pilots and measurable output.
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_16][^9_7][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/json/

[^9_2]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/eodhd/

[^9_3]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^9_4]: https://github.com/havasd/pp-data

[^9_5]: https://github.com/enrichman/portfolio-performance/blob/main/README.md

[^9_6]: https://www.perplexity.ai/search/7a0d7369-2c44-404f-87b7-8dba52c29317

[^9_7]: https://medium.com/@peternjuguna76/hosting-a-json-file-on-github-pages-a-step-by-step-guide-52105a5a393a

[^9_8]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/alpha-vantage/

[^9_9]: https://forum.portfolio-performance.info/t/add-custom-quote-provider/28741

[^9_10]: https://www.borzamalta.com.mt/publications-and-statistics?category=15

[^9_11]: https://www.borzamalta.com.mt/publications-and-statistics

[^9_12]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/portfolioperformance/

[^9_13]: https://medium.com/@sourav.ahmed5654/static-json-provider-using-github-page-da971e5f50a2

[^9_14]: https://www.borzamalta.com.mt/publications-and-statistics?category=23

[^9_15]: https://dimitristeiner.com/portfolio-performance-price-feed-for-securities/

[^9_16]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/


---

# this is the github repo - update your prompts [https://github.com/heyvinay/MSESharePrices](https://github.com/heyvinay/MSESharePrices)

Yes — here are **updated prompts** tailored to your actual repo: `heyvinay/MSESharePrices`. The design assumes you will use that public repository to generate and publish a JSON feed for Portfolio Performance, which supports JSON historical quote feeds with `Path to Date = $[*].date` and `Path to Close = $[*].close`. The Malta Stock Exchange source remains the Daily Trading Summary yearly archive.[^10_1][^10_2][^10_3][^10_4]

## Codex prompt

```text
Work in this existing GitHub repository:

https://github.com/heyvinay/MSESharePrices

I want you to build the project directly for this repo.

Goal
Turn this repository into a lightweight automation project that publishes Malta Stock Exchange historical prices for Bank of Valletta plc (symbol code BOV) in a Portfolio Performance-compatible JSON feed.

End state
- The repo generates a static JSON file for BOV historical quotes.
- The JSON is published through GitHub Pages from this repository.
- Portfolio Performance can use the JSON Quote Feed Provider with:
  - Path to Date = $[*].date
  - Path to Close = $[*].close
- The repo includes GitHub Actions automation so the feed refreshes daily.

Data source
- Malta Stock Exchange Daily Trading Summary yearly archive:
  https://www.borzamalta.com.mt/publications-and-statistics?category=33
- The archive exposes yearly trading summary files.
- The yearly XLS data contains fields including:
  - Symbol code
  - DATE
  - Close Price

Target JSON format
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]

What to build
Create or update the repo with:
- a Python 3 CLI script to fetch and transform MSE archive data,
- support for symbol selection, defaulting to BOV,
- JSON output for GitHub Pages,
- optional CSV output for validation,
- a minimal docs/index.html page,
- a GitHub Actions workflow to update the feed daily,
- clear README instructions for local use, GitHub Pages setup, and Portfolio Performance configuration.

Implementation requirements
- Use Python, not PowerShell.
- Keep the implementation lightweight and maintainable.
- Use requests for downloading.
- Use pandas if needed for legacy XLS parsing.
- Make the script easy to extend later to other MSE symbols.
- Do not over-engineer the project.
- Log progress to the console.
- Fail clearly if required columns are missing.

Functional requirements
1. Support CLI arguments:
   - --symbol (default BOV)
   - --start-year
   - --end-year
   - --output-json
   - --output-csv
   - --manual-url (repeatable, optional)
2. Discover yearly XLS links from the MSE archive page if possible.
3. If discovery is unreliable, support manual URLs as fallback.
4. Normalise headers because yearly files may vary slightly.
5. Filter rows where Symbol code matches the selected symbol.
6. Extract DATE and Close Price.
7. Convert date values to YYYY-MM-DD.
8. Coerce prices to numeric.
9. Remove invalid rows.
10. Deduplicate by date, keeping the last valid quote.
11. Sort ascending by date.
12. Write JSON using exactly:
    [
      { "date": "YYYY-MM-DD", "close": 1.234 }
    ]
13. Optionally write CSV with:
    date,quote

Repository-specific expectations
- Work with the repo name MSESharePrices.
- Prefer publishing the JSON at:
  docs/json/BOV.json
- Also create a simple landing page at:
  docs/index.html
- Document the expected GitHub Pages URL pattern for this repo, for example:
  https://heyvinay.github.io/MSESharePrices/json/BOV.json
  if Pages is configured from docs/.

Recommended file structure
- src/mse_pp_feed.py
- docs/index.html
- docs/json/BOV.json
- .github/workflows/update-bov.yml
- requirements.txt
- README.md

GitHub Actions requirements
- Add a scheduled workflow that runs daily.
- Also support workflow_dispatch.
- The workflow should:
  1. set up Python,
  2. install dependencies,
  3. run the script,
  4. update docs/json/BOV.json,
  5. commit changes only when the generated feed has changed.

README requirements
- Project purpose
- Setup
- Local run commands
- GitHub Pages configuration for this exact repo
- GitHub Actions notes
- Portfolio Performance configuration using this repo’s published JSON URL
- Troubleshooting
- Known limitations
- Notes on how to add more MSE symbols later

Acceptance criteria
- Running the script locally produces a valid JSON feed for BOV.
- The feed schema works with Portfolio Performance JSON quote provider.
- The repository can publish the JSON via GitHub Pages.
- The GitHub Actions workflow refreshes the JSON automatically.
- The design is simple enough to extend to APS, GO, HSB, or other MSE symbols later.

Please first output:
1. a short implementation plan,
2. the proposed file changes for this repo,
3. assumptions and risks,
4. then the full code and file contents.
```


## Claude Code prompt

```text
You are working in this existing repository:

https://github.com/heyvinay/MSESharePrices

I want you to turn this repo into an automated Portfolio Performance quote feed project for Malta Stock Exchange prices.

Mission
Build a lightweight Python automation flow that generates and publishes a historical JSON quote feed for Bank of Valletta plc (symbol code BOV) from the Malta Stock Exchange archive, using this repository’s GitHub Pages site.

Business outcome
I want as much automation as possible.
The finished repo should:
- fetch Malta Stock Exchange archive data,
- build a clean BOV historical JSON file,
- publish it via GitHub Pages from this repo,
- refresh it daily via GitHub Actions,
- allow Portfolio Performance to consume it using its JSON Quote Feed Provider.

Source context
- Malta Stock Exchange archive page:
  https://www.borzamalta.com.mt/publications-and-statistics?category=33
- This is the Daily Trading Summary yearly archive.
- Archive files contain fields such as:
  - Symbol code
  - DATE
  - Close Price

Portfolio Performance target
- Provider: JSON
- Feed URL: published JSON from this repository
- Path to Date = $[*].date
- Path to Close = $[*].close

Target JSON shape
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]

Repository-specific target layout
- src/mse_pp_feed.py
- docs/index.html
- docs/json/BOV.json
- .github/workflows/update-bov.yml
- requirements.txt
- README.md

Constraints
- Use Python, not PowerShell.
- Keep the solution lightweight and structured.
- Use requests for downloads.
- Use pandas plus any required XLS engine only if needed.
- Make the solution easy to extend later to other MSE symbols.
- Avoid unrelated refactors.
- Prioritise working automation over cleverness.

Functional requirements
1. Create a Python CLI script.
2. Discover yearly XLS download links from the MSE archive page where feasible.
3. Add a documented fallback to accept one or more manual XLS URLs.
4. Parse workbook data safely.
5. Normalise headers because MSE files may vary slightly.
6. Filter rows where Symbol code equals the requested symbol, default BOV.
7. Extract DATE and Close Price.
8. Clean data:
   - drop blank rows,
   - coerce prices to numeric,
   - normalise dates to YYYY-MM-DD,
   - sort ascending,
   - deduplicate by date, keeping the last valid row.
9. Write:
   - docs/json/BOV.json using:
     [
       { "date": "YYYY-MM-DD", "close": 1.234 }
     ]
   - optional CSV output with:
     date,quote
10. Create docs/index.html with a short explanation and a link to the JSON file.
11. Add a GitHub Actions workflow that:
   - runs daily,
   - supports manual dispatch,
   - installs dependencies,
   - runs the script,
   - commits updated feed files only if they changed.
12. Update README.md so it includes:
   - project purpose,
   - setup,
   - local usage,
   - GitHub Pages setup for this exact repo,
   - GitHub Actions notes,
   - Portfolio Performance setup using this repo’s Pages URL,
   - assumptions and limitations,
   - how to add more MSE symbols later.

Expected GitHub Pages result
Assume this repository will publish the JSON at something like:
https://heyvinay.github.io/MSESharePrices/json/BOV.json
if Pages is configured from docs/.
Document the final expected URL clearly in the README.

Working style
- First inspect the repo and tell me:
  1. what files already exist,
  2. what files you plan to create or change,
  3. your implementation plan,
  4. your dependency choices,
  5. any risks with MSE archive link discovery.
- Then implement.
- Keep edits surgical and focused.
- Do not change unrelated files.
- If anything is missing in the repo, create the minimum necessary structure cleanly.

Validation
- Validate the JSON structure.
- Validate that dates are ISO formatted.
- Validate that records are sorted ascending.
- Validate that duplicate dates are removed.
- Show me exact commands to:
  - run locally for BOV,
  - run for another symbol,
  - run with manual XLS URLs,
  - verify the resulting GitHub Pages URL for Portfolio Performance.

Important
- Optimise for maintainability and automation.
- This is a public repo.
- Avoid secrets and avoid unnecessary complexity.
- Make the repo useful as a template for future Malta Stock Exchange symbols too.

Please provide:
1. implementation plan,
2. repo change plan,
3. then the code changes,
4. then a short usage section with exact commands.
```


## Repo-specific note

I’ve now baked the repo name into the prompts and aligned the likely GitHub Pages path to `heyvinay/MSESharePrices`. That matters because Portfolio Performance’s JSON provider wants a stable published URL, and the JSON structure should stay in the simple array-of-objects form that PP documents and that other PP quote-feed repos also use.[^10_4][^10_5][^10_6][^10_1]

## One extra line

Add this single line to either prompt if you want stronger control over repo hygiene:

- “If the repo is empty or nearly empty, create the minimal structure cleanly rather than introducing a large framework.”

That fits your preference for lightweight, structured builds over bulky scaffolding.[^10_7]

Would you like a third prompt variant specifically for **Codex in agent mode**, with shorter instructions and tighter acceptance tests?
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_16][^10_8][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/json/

[^10_2]: https://www.borzamalta.com.mt/publications-and-statistics?category=24

[^10_3]: https://www.borzamalta.com.mt/publications-and-statistics

[^10_4]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/eodhd/

[^10_5]: https://github.com/havasd/pp-data

[^10_6]: https://github.com/enrichman/portfolio-performance/blob/main/README.md

[^10_7]: https://www.perplexity.ai/search/22919c1f-9263-4d81-a291-f197fba7c0a1

[^10_8]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/alpha-vantage/

[^10_9]: https://dimitristeiner.com/portfolio-performance-price-feed-for-securities/

[^10_10]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/

[^10_11]: https://forum.portfolio-performance.info/t/import-fund-data-from-morningstar/14516

[^10_12]: https://forum.portfolio-performance.info/t/dynamic-price-url/27099/6

[^10_13]: https://forum.portfolio-performance.info/t/adding-json-datafeed-stooq/31942

[^10_14]: https://forum.portfolio-performance.info/t/dynamic-price-url/27099

[^10_15]: https://cdn.borzamalta.com.mt/download/statistics/Daily_Market_Extract.xls

[^10_16]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/portfolioperformance/


---

# do I need to download and install any specific skills for this projet - to ensure I draft good specs, use TDD and any other good software develpment practises and architecture.

No — you do **not** need to install a lot of extra “skills” to do this project well. For this repo, the best setup is a **lightweight spec-first workflow** with Python, pytest, GitHub Actions, and a small amount of repo guidance such as `CLAUDE.md`; BMAD is relevant if you want structure, while spec-kitty is more useful when you need stronger work-package governance and review gates across agent work.[^11_1][^11_2]

## What you need

For this specific project, I’d keep the toolset small:

- **Python** for the importer and feed generator.[^11_3]
- **pytest** for TDD and regression checks around parsing, date normalisation, deduplication, and JSON output. Pytest is a standard fit for TDD-style Python work.[^11_4][^11_5][^11_6]
- **GitHub Actions** for scheduled refresh and test execution in the repo.[^11_7]
- **CLAUDE.md** in the repo root to define mission, architecture boundaries, coding rules, test rules, and git workflow. Repo-anchored instructions are a strong way to keep Claude Code aligned across sessions.[^11_8][^11_9]

That is enough to get good specs, tests, and maintainable structure without turning a small automation utility into process theatre. That matches your preference for lightweight but structured development.[^11_10]

## What I’d add

I would add these repo artefacts:

- `CLAUDE.md`
- `docs/spec.md`
- `docs/architecture.md`
- `tests/`
- `.github/workflows/update-bov.yml`

A small spec and architecture note will help Codex or Claude Code stay disciplined: source of truth, failure modes, JSON contract, test boundaries, and non-goals. That is usually more valuable than installing a large framework for a compact project like this.[^11_11]

## BMAD vs spec-kitty

If you want **good specs and architecture**, BMAD is the better conceptual fit. BMAD is explicitly a structured agile AI-driven development method, while spec-kitty focuses more on repeatable work packages, reviewable specs, execution boundaries, and visible delivery control.[^11_1][^11_2][^11_12]

For your case:

- **BMAD mindset**: yes, useful for thinking and repo structure.[^11_2]
- **spec-kitty install**: probably not necessary for this small project unless you want formalised mission lanes, work packages, and stronger governance records.[^11_12][^11_1]
- **Full framework install**: optional, not required.

Given that you previously found spec-kitty too manual for your preferred approach, I would not make it a prerequisite here.

## TDD and architecture

For TDD, keep it practical:

- write tests first for header normalisation,
- parsing of workbook rows,
- filtering `Symbol code == BOV`,
- duplicate-date handling,
- JSON schema output,
- resilience when a required column is missing.[^11_6][^11_4]

Architecturally, keep the code split into small pure functions:

- `discover_urls()`
- `download_file()`
- `read_workbook()`
- `normalise_headers()`
- `extract_quotes()`
- `write_json()`

That style makes TDD much easier and reduces the risk of fragile scraper logic. It also fits your preference for maintainability and structured debugging over speed alone.

## Recommended stack

My recommendation for this repo is:

- **Install**: Python, pytest, requests, pandas, and whichever XLS reader the implementation needs.[^11_13][^11_4]
- **Create**: `CLAUDE.md`, `docs/spec.md`, `docs/architecture.md`, `tests/`.[^11_9][^11_8]
- **Use**: BMAD principles lightly, not necessarily the full installed framework.[^11_10][^11_2]
- **Skip for now**: spec-kitty, unless you want heavier governance and explicit work-package control.[^11_1]

A good one-line rule for this repo would be: **spec first, tests first, automation first, minimal framework overhead**.

## Practical answer

So the short answer is:

- **No special skills are mandatory.**
- **Yes, add lightweight repo guidance and tests.**[^11_4][^11_8]
- **Use pytest for TDD.**[^11_5][^11_6]
- **Use BMAD ideas lightly if you want discipline.**[^11_2][^11_10]
- **Do not bother installing spec-kitty unless you want heavier process control.**[^11_1]

Would you like me to draft a **starter `CLAUDE.md`, `spec.md`, and `architecture.md`** for `MSESharePrices` so your repo is ready before you hand it to Codex or Claude Code?
<span style="display:none">[^11_14][^11_15][^11_16][^11_17][^11_18][^11_19][^11_20][^11_21][^11_22]</span>

<div align="center">⁂</div>

[^11_1]: https://github.com/Priivacy-ai/spec-kitty

[^11_2]: https://github.com/bmad-code-org/bmad-method

[^11_3]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^11_4]: https://pytest-with-eric.com/tdd/pytest-tdd/

[^11_5]: https://www.thedigitalcatonline.com/blog/2020/09/10/tdd-in-python-with-pytest-part-1/

[^11_6]: https://testdriven.io/blog/modern-tdd/

[^11_7]: https://github.com/havasd/pp-data

[^11_8]: https://www.perplexity.ai/search/c61fe530-c551-4746-9b77-e057c57fd6e9

[^11_9]: https://www.perplexity.ai/search/fb287191-8b36-4c17-b0f9-61d9c611d1c7

[^11_10]: https://www.perplexity.ai/search/1daa919e-7720-4728-92cf-652357d8bbbd

[^11_11]: https://www.perplexity.ai/search/cfc3d9be-3ed5-4c04-9a14-9aec26068bb5

[^11_12]: https://spec-kitty.ai/

[^11_13]: https://help.portfolio-performance.info/en/how-to/

[^11_14]: https://github.com/oimiragieo/BMAD-SPEC-KIT

[^11_15]: https://www.slideshare.net/slideshow/tdd-in-python-with-pytest-43671276/43671276?nway-=

[^11_16]: https://github.com/bmad-code-org/BMAD-METHOD/issues/279

[^11_17]: https://github.com/Priivacy-ai/spec-kitty/blob/main/spec-driven.md

[^11_18]: https://mikulskibartosz.name/tdd-with-pytest

[^11_19]: https://github.com/FBorowiec/tdd_with_python

[^11_20]: https://codefellows.github.io/sea-python-401d4/lectures/tdd_with_pytest.html

[^11_21]: https://newreleases.io/project/github/Priivacy-ai/spec-kitty/release/v2.0.1

[^11_22]: https://medium.com/@visrow/a-tale-of-two-frameworks-bmad-method-vs-github-spec-kit-c021ab0ad037


---

# Defining your project identity

Choosing your core principles
Setting up initial capabilities
Configuring invariants
Design interfaces, create architecture docs
Plan implementation
QA and verify
Keep documentation accurate

Yes — that is a **good checklist**, and for this project I’d treat it as the operating model for the repo. It lines up well with a lightweight spec-driven approach, pragmatic architecture documentation such as arc42, and Python TDD with pytest.[^12_1][^12_2][^12_3]

## Operating model

Your list maps cleanly to a small but disciplined workflow:

- Define the project identity and core principles first, so the repo has a clear mission and decision criteria. arc42 explicitly starts with introduction, goals, constraints, stakeholders, and quality goals, which makes it a good fit for this kind of small but maintainable utility.[^12_1][^12_4]
- Set capabilities, invariants, and interfaces before implementation, so the importer has stable contracts around inputs, outputs, JSON schema, and error handling. arc42’s structure also covers solution strategy, building blocks, runtime views, cross-cutting concepts, risks, and architectural decisions.[^12_2][^12_5][^12_1]


## What to create

For `MSESharePrices`, I would create these docs:

- `CLAUDE.md` — repo mission, working rules, git workflow, coding standards, TDD rule, invariants.
- `docs/spec.md` — purpose, capabilities, non-goals, acceptance criteria.
- `docs/architecture.md` — context, components, data flow, interfaces, decisions, risks.
- `docs/qa.md` — test strategy, fixtures, smoke checks, CI expectations.
- `docs/decision-log.md` — short ADR-style decisions for parser approach, JSON schema, hosting path, scheduling.
- `tests/` — executable verification of the spec.[^12_6][^12_7][^12_1]

This is enough documentation to stay accurate without becoming heavy. arc42 is explicitly designed to be pragmatic and “painless” rather than bloated.[^12_5][^12_2]

## Suggested mapping

Your headings can become concrete repo sections like this:


| Your heading | Repo artefact |
| :-- | :-- |
| Defining your project identity | `CLAUDE.md` mission + `docs/spec.md` overview [^12_7][^12_4] |
| Choosing your core principles | `CLAUDE.md` principles/invariants |
| Setting up initial capabilities | `docs/spec.md` capabilities and non-goals |
| Configuring invariants | `CLAUDE.md` + `docs/architecture.md` contracts and rules [^12_1] |
| Design interfaces, create architecture docs | `docs/architecture.md` using a slim arc42 structure [^12_1][^12_2] |
| Plan implementation | `docs/spec.md` implementation slices and acceptance criteria |
| QA and verify | `docs/qa.md` + `tests/` + CI workflow [^12_8] |
| Keep documentation accurate | “docs updated in same PR as behaviour change” rule in `CLAUDE.md` |

## TDD approach

For this project, TDD should focus on the **contracts**, not on every line of plumbing. Good first tests are:

- header normalisation from messy workbook columns,
- symbol filtering for `BOV`,
- date parsing to `YYYY-MM-DD`,
- duplicate-date resolution,
- JSON feed schema,
- behaviour when required columns are missing.[^12_3][^12_9][^12_10]

That style keeps tests high-value and stable. It also supports your preference for structured QA and measurable outcomes rather than vague “best effort” testing.

## Practical principles

I’d use these core principles for the repo:

- Source before scrape — prefer structured MSE workbook data over brittle HTML scraping.[^12_11]
- Contracts first — keep JSON output stable for Portfolio Performance.[^12_12]
- Pure functions where possible — easier testing and maintenance.[^12_3]
- Automation by default — scheduled GitHub Action plus test run in CI.[^12_8]
- Docs and code change together — no silent drift between behaviour and documentation.[^12_2]


## Recommendation

So yes — your list is strong, and I would formalise it into the repo rather than hunting for more external “skills”. For this utility, the best combination is **lightweight spec docs + arc42-style architecture note + pytest TDD + CI + repo invariants in `CLAUDE.md`**.[^12_1][^12_8]

Would you like me to turn your checklist into a **ready-to-paste repo starter pack** with:

- `CLAUDE.md`
- `docs/spec.md`
- `docs/architecture.md`
- `docs/qa.md`
- `docs/decision-log.md`
<span style="display:none">[^12_13][^12_14][^12_15][^12_16][^12_17][^12_18][^12_19]</span>

<div align="center">⁂</div>

[^12_1]: https://arc42.org/overview

[^12_2]: https://arc42.org/documentation/

[^12_3]: https://pytest-with-eric.com/tdd/pytest-tdd/

[^12_4]: https://docs.arc42.org/section-1/

[^12_5]: https://arc42.org/

[^12_6]: https://www.perplexity.ai/search/c61fe530-c551-4746-9b77-e057c57fd6e9

[^12_7]: https://www.perplexity.ai/search/fb287191-8b36-4c17-b0f9-61d9c611d1c7

[^12_8]: https://github.com/actions/starter-workflows/blob/main/ci/python-app.yml

[^12_9]: https://www.thedigitalcatonline.com/blog/2020/09/10/tdd-in-python-with-pytest-part-1/

[^12_10]: https://testdriven.io/blog/modern-tdd/

[^12_11]: https://www.borzamalta.com.mt/publications-and-statistics?category=33

[^12_12]: https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/json/

[^12_13]: https://x-as-code.useblocks.com/how-to-guides/arc42/index.html

[^12_14]: https://github.com/github/docs/blob/main/content/actions/use-cases-and-examples/building-and-testing/building-and-testing-python.md

[^12_15]: https://www.slideshare.net/slideshow/tdd-in-python-with-pytest-43671276/43671276?nway-=

[^12_16]: https://www.innoq.com/en/blog/2022/08/brief-introduction-to-arc42/

[^12_17]: https://blog.hompus.nl/2026/02/01/arc42-practical-series/

[^12_18]: https://www.youtube.com/watch?v=qnq8TLoB5Qo

[^12_19]: https://www.open200.com/post/how-to-kick-off-software-architecture-documentation-with-the-arc42-canvas


---

# how about [https://github.com/mattpocock](https://github.com/mattpocock) or  [https://github.com/obra/superpowers](https://github.com/obra/superpowers)

Both are **relevant**, but they serve different purposes. For your `MSESharePrices` repo, Matt Pocock’s skills are the better fit if your goal is sharper specs, TDD loops, and disciplined solo implementation, while `obra/superpowers` is better if you want a broader agentic workflow framework with planning, debugging, collaboration, and plugin-style skill installation.[^13_1][^13_2][^13_3]

## Matt Pocock

Matt Pocock’s `skills` repo is essentially a public set of reusable Claude Code skills and behaviours, installed via `npx skills@latest add mattpocock/skills`. The active skill set highlighted in coverage includes items like `tdd`, `diagnose`, `to-prd`, `to-issues`, and `grill-me`, which map very well to your needs around defining specs, pressure-testing plans, and keeping implementation tight.[^13_4][^13_3][^13_5]

For this BOV/MSE project, the most useful parts are:

- `to-prd` for a crisp project brief,[^13_4]
- `grill-me` for challenging assumptions before coding,[^13_6]
- `tdd` for test-first loops,[^13_6][^13_4]
- `diagnose` for parser/download failures once the script is running.[^13_4]

That is a strong fit for a **small, repo-centric, solo engineering workflow**.[^13_5]

## obra/superpowers

`obra/superpowers` is positioned as an “agentic skills framework \& software development methodology,” and the marketplace description says it includes core skills for TDD, debugging, collaboration patterns, session-start context injection, and discovery tooling. It is installable as a plugin from the Superpowers marketplace, with the marketplace recommending `/plugin install superpowers@superpowers-marketplace`.[^13_2][^13_1]

This gives you a more opinionated framework around:

- planning,
- git worktrees,
- test-driven development,
- code review,
- parallel agents,
- branch finishing.[^13_7]

That is attractive if you want a **fuller operating system for AI coding**, but it is also heavier than you likely need for one small Python feed project.[^13_1][^13_7]

## Best fit here

For `MSESharePrices`, I would choose **Matt Pocock’s skills first**. They are lighter, more composable, and more directly aligned to the problems you actually have right now: good spec drafting, TDD, issue breakdown, and failure diagnosis.[^13_5][^13_6][^13_4]

I would only add `superpowers` if you later decide you want:

- a bigger plugin-based workflow,
- more formal multi-agent collaboration,
- or a standardised repeatable pattern across several repos.[^13_2][^13_1]

That recommendation also fits your stated preference for lightweight but structured development rather than overly manual or heavy frameworks.

## Practical recommendation

Use this combination:

- **Keep your own repo docs** as the real source of truth: `CLAUDE.md`, `spec.md`, `architecture.md`, `qa.md`.
- **Install Matt Pocock skills** for working habits and prompts around PRDs, TDD, diagnosis, and issue slicing.[^13_3][^13_4]
- **Skip superpowers for now**, unless you want to experiment with a wider plugin ecosystem and more agentic workflow control.[^13_1][^13_2]

So the short answer is: **Matt Pocock = yes, likely useful now. Superpowers = interesting, but probably optional for this repo.**[^13_1][^13_4]

Would you like me to suggest the **exact Matt Pocock skills I’d enable for this repo** and how I’d reflect them inside `CLAUDE.md`?
<span style="display:none">[^13_10][^13_11][^13_12][^13_13][^13_14][^13_8][^13_9]</span>

<div align="center">⁂</div>

[^13_1]: https://github.com/obra/superpowers-marketplace/blob/main/README.md

[^13_2]: https://github.com/obra/superpowers/blob/main/README.md

[^13_3]: https://github.com/mattpocock/skills/blob/main/CONTEXT.md

[^13_4]: https://www.implicator.ai/matt-pocock-skills-repo-jumps-past-45k-stars-with-reusable-ai-instructions/

[^13_5]: https://app.daily.dev/posts/x3nupj92r

[^13_6]: https://www.youtube.com/watch?v=z0y1nuiXdoc

[^13_7]: https://www.c-sharpcorner.com/article/superpowers-by-obra-what-it-is-and-how-to-use-it-to-improve-ai-coding/

[^13_8]: https://x.com/AlphaSignalAI/status/2048809516993556845

[^13_9]: https://github.com/obra/superpowers/releases

[^13_10]: https://github.com/mattpocock/sandcastle

[^13_11]: https://github.com/obra/superpowers-chrome/blob/main/mcp/README.md

[^13_12]: https://www.developersdigest.tech/blog/github-trending-skills-2026-05-13

[^13_13]: https://www.youtube.com/watch?v=LTO43rpjYVg

[^13_14]: https://github.com/obra/superpowers/blob/main/docs/README.opencode.md


---

# update both prompts to ensure if covers: Defining your project identity

Choosing your core principles
Setting up initial capabilities
Configuring invariants
Design interfaces, create architecture docs
Plan implementation
QA and verify
Keep documentation accurate

and the installation and use of the Matt Pocock skills.

Yes — below are **updated prompts for both Codex and Claude Code** that explicitly cover your lifecycle checklist and the installation/use of Matt Pocock’s skills. Matt Pocock’s repo documents the installer command `npx skills@latest add mattpocock/skills`, and guidance around running `/setup-matt-pocock-skills` once per repo appears in secondary coverage of the skills workflow.[^14_1][^14_2]

## Codex prompt

```text
Work in this existing GitHub repository:

https://github.com/heyvinay/MSESharePrices

I want you to build this repo as a lightweight, well-structured, automation-first project for Portfolio Performance historical quote feeds from the Malta Stock Exchange.

Project goal
Turn this repository into a maintainable Python project that:
- fetches Malta Stock Exchange Daily Trading Summary archive data,
- extracts historical prices for Bank of Valletta plc (symbol code BOV),
- publishes a static JSON feed via GitHub Pages,
- refreshes the feed automatically via GitHub Actions,
- supports Portfolio Performance JSON quote feed configuration.

Portfolio Performance target
- Historical quote provider: JSON
- Feed URL: published JSON from this repository
- Path to Date = $[*].date
- Path to Close = $[*].close

Data source
- Malta Stock Exchange archive page:
  https://www.borzamalta.com.mt/publications-and-statistics?category=33
- This is the Daily Trading Summary yearly archive.
- The yearly XLS files contain fields such as:
  - Symbol code
  - DATE
  - Close Price

Target JSON output
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]

Important working style
This repo must be built using a lightweight spec-driven approach, TDD, clear architecture notes, and accurate documentation.
Do not jump straight into code.
You must explicitly cover the following areas in the repo and in your planning output:
1. Defining project identity
2. Choosing core principles
3. Setting up initial capabilities
4. Configuring invariants
5. Designing interfaces and architecture docs
6. Planning implementation
7. QA and verification
8. Keeping documentation accurate

Matt Pocock skills
Assume I want to use Matt Pocock’s skills in this repository.
Please incorporate this into the repo guidance and setup documentation.

Relevant installation details
- Install command:
  npx skills@latest add mattpocock/skills
- I will likely use skills such as:
  /setup-matt-pocock-skills
  /grill-me
  /to-prd
  /tdd
  /diagnose
  /improve-codebase-architecture

What I want you to create
Build or update this repository with:
- Python implementation
- tests
- GitHub Actions workflow
- GitHub Pages output
- spec and architecture documents
- repo guidance for Claude Code / Codex style work
- Matt Pocock skills installation and usage notes

Repository outputs
Please create or update at least these files:
- CLAUDE.md
- docs/spec.md
- docs/architecture.md
- docs/qa.md
- docs/decision-log.md
- src/mse_pp_feed.py
- tests/
- docs/index.html
- docs/json/BOV.json
- .github/workflows/update-bov.yml
- requirements.txt
- README.md

Required content by section

A. Defining project identity
Create a clear project identity section in CLAUDE.md and docs/spec.md covering:
- mission
- business outcome
- intended user
- source systems
- deployment model
- non-goals

B. Choosing core principles
Document core principles such as:
- source before scrape
- stable contracts over cleverness
- testability over convenience
- automation by default
- public-repo-safe design
- docs and code change together

C. Setting up initial capabilities
Define initial capabilities in docs/spec.md, for example:
- discover or accept MSE archive URLs
- download yearly files
- parse and normalise workbook data
- filter by symbol
- produce JSON for Portfolio Performance
- optional CSV validation export
- scheduled refresh via GitHub Actions

D. Configuring invariants
Document invariants in CLAUDE.md and architecture docs, such as:
- output JSON schema is stable
- date format must be YYYY-MM-DD
- close price must be numeric
- rows sorted ascending
- duplicate dates resolved deterministically
- no secrets in repo
- all behaviour changes must update docs and tests

E. Design interfaces and architecture docs
Create architecture documentation using a slim pragmatic structure inspired by arc42.
Include:
- system context
- external dependencies
- components/modules
- data flow
- interfaces and contracts
- error handling approach
- design decisions and trade-offs
- risks and assumptions

F. Plan implementation
Create an implementation plan section in docs/spec.md or docs/qa.md.
Break work into small steps:
- repo scaffolding
- docs and invariants
- archive discovery
- parsing
- transformation
- JSON output
- tests
- CI workflow
- Pages publishing

G. QA and verify
Use TDD and create tests first or alongside implementation where practical.
Test at minimum:
- header normalisation
- symbol filtering
- date conversion
- duplicate handling
- missing-column failure
- JSON output structure
- sorted output
Add CI to run tests automatically.

H. Keep documentation accurate
Create an explicit repo rule:
- documentation must be updated in the same change set as behaviour changes
- README, spec, architecture, and QA docs must not drift
- decision-log updated when architectural decisions change

Functional requirements for the Python tool
1. Support CLI arguments:
   - --symbol (default BOV)
   - --start-year
   - --end-year
   - --output-json
   - --output-csv
   - --manual-url (repeatable, optional)
2. Discover yearly XLS links from the MSE archive page if possible.
3. If discovery is unreliable, support manual URLs as fallback.
4. Normalise headers because yearly files may vary slightly.
5. Filter rows where Symbol code matches the selected symbol.
6. Extract DATE and Close Price.
7. Convert dates to YYYY-MM-DD.
8. Coerce prices to numeric.
9. Remove invalid rows.
10. Deduplicate by date, keeping the last valid quote.
11. Sort ascending by date.
12. Write JSON using exactly:
    [
      { "date": "YYYY-MM-DD", "close": 1.234 }
    ]
13. Optionally write CSV with:
    date,quote

Repository-specific expectations
- Work with repo name MSESharePrices
- Prefer publishing JSON at:
  docs/json/BOV.json
- Create docs/index.html linking to the JSON file
- Document expected GitHub Pages URL for this exact repo
- Keep the project extensible to additional MSE symbols later

README requirements
README.md must include:
- project purpose
- local setup
- Python install/use
- GitHub Pages setup
- GitHub Actions notes
- Portfolio Performance configuration
- Matt Pocock skills installation
- which Matt Pocock skills to use and when
- troubleshooting
- known limitations
- how to add more symbols later

Matt Pocock skills section
Document in README and/or CLAUDE.md:
- install with:
  npx skills@latest add mattpocock/skills
- run repo setup via:
  /setup-matt-pocock-skills
- use /grill-me to pressure-test the spec
- use /to-prd to refine project brief
- use /tdd for red-green-refactor loops
- use /diagnose for bugs or parsing failures
- use /improve-codebase-architecture for periodic design review

Acceptance criteria
- The repo contains clear identity, principles, capabilities, invariants, architecture docs, QA docs, and accurate README guidance.
- The Python script generates a valid Portfolio Performance JSON feed for BOV.
- Tests cover core invariants.
- GitHub Actions refreshes the JSON automatically.
- GitHub Pages can serve the resulting JSON.
- The repo is suitable for disciplined future extension to more Malta symbols.

Please first output:
1. project identity
2. core principles
3. capabilities
4. invariants
5. architecture/documentation plan
6. implementation plan
7. QA plan
8. Matt Pocock skills usage plan
9. then all file contents in full
```


## Claude Code prompt

```text
You are working in this existing repository:

https://github.com/heyvinay/MSESharePrices

I want you to turn this repo into a lightweight, automation-first, well-documented Python project that publishes Malta Stock Exchange historical prices for Portfolio Performance.

Mission
Build an automated historical quote feed for Bank of Valletta plc (symbol code BOV) using Malta Stock Exchange yearly archive data, publish the result through this repo’s GitHub Pages site, and keep the project maintainable through specs, invariants, architecture notes, TDD, and accurate documentation.

Portfolio Performance target
- Provider: JSON
- Feed URL: published JSON from this repository
- Path to Date = $[*].date
- Path to Close = $[*].close

Source context
- Malta Stock Exchange archive page:
  https://www.borzamalta.com.mt/publications-and-statistics?category=33
- This is the Daily Trading Summary yearly archive.
- Archive files contain fields such as:
  - Symbol code
  - DATE
  - Close Price

Target JSON shape
[
  { "date": "2026-01-05", "close": 1.920 },
  { "date": "2026-01-06", "close": 1.910 }
]

Non-negotiable working model
Do not start by writing code blindly.
Use a lightweight spec-driven workflow and explicitly cover these eight areas in the repo:

1. Defining project identity
2. Choosing core principles
3. Setting up initial capabilities
4. Configuring invariants
5. Designing interfaces and creating architecture docs
6. Planning implementation
7. QA and verification
8. Keeping documentation accurate

Matt Pocock skills
Assume I want to use Matt Pocock’s skills in this repo.
Please include repo guidance and documentation for installing and using them.

Known install/use details
- Install with:
  npx skills@latest add mattpocock/skills
- Include guidance for:
  /setup-matt-pocock-skills
  /grill-me
  /to-prd
  /tdd
  /diagnose
  /improve-codebase-architecture

Repository outputs expected
Create or update:
- CLAUDE.md
- docs/spec.md
- docs/architecture.md
- docs/qa.md
- docs/decision-log.md
- src/mse_pp_feed.py
- tests/
- docs/index.html
- docs/json/BOV.json
- .github/workflows/update-bov.yml
- requirements.txt
- README.md

Repository expectations by topic

A. Defining project identity
Create a clear project identity in CLAUDE.md and docs/spec.md:
- mission
- intended use
- expected business outcome
- primary user
- deployment model
- non-goals

B. Choosing core principles
Document core engineering principles such as:
- structured source data over brittle scraping
- explicit contracts over implicit behaviour
- testability over convenience
- automation by default
- public-repo-safe design
- documentation and code evolve together

C. Setting up initial capabilities
Define initial capabilities:
- archive URL discovery or manual URL fallback
- download yearly XLS files
- normalise workbook headers
- filter symbol rows
- produce Portfolio Performance JSON
- optional CSV export
- automated refresh via GitHub Actions

D. Configuring invariants
Document and enforce invariants:
- JSON schema must remain stable
- dates must be YYYY-MM-DD
- close prices must be numeric
- records must be sorted ascending
- duplicate dates must be resolved deterministically
- missing required columns must fail clearly
- no secrets in repo
- any behaviour change must update tests and docs

E. Design interfaces and architecture docs
Create pragmatic architecture docs inspired by a slim arc42 approach:
- context
- external systems
- internal modules
- data flow
- interfaces/contracts
- failure handling
- design decisions
- risks and assumptions

F. Plan implementation
Write an implementation plan that breaks work into small reviewable steps.

G. QA and verify
Use TDD where practical.
Create tests for:
- header normalisation
- symbol filtering
- date conversion
- duplicate resolution
- missing-column failure
- JSON schema/output
- sorted output
Set up CI to run tests automatically.

H. Keep documentation accurate
Create repo rules that:
- documentation updates happen in the same change as behaviour changes
- README, spec, architecture, QA docs, and decision log stay aligned
- decision log is updated when architecture decisions change

Functional requirements for the Python tool
1. Support CLI arguments:
   - --symbol (default BOV)
   - --start-year
   - --end-year
   - --output-json
   - --output-csv
   - --manual-url (repeatable, optional)
2. Discover yearly XLS links from the MSE archive page where feasible.
3. Support manual URLs if discovery is unreliable.
4. Normalise headers because yearly workbook headers may vary slightly.
5. Filter rows where Symbol code matches the selected symbol.
6. Extract DATE and Close Price.
7. Convert dates to YYYY-MM-DD.
8. Coerce prices to numeric.
9. Remove invalid rows.
10. Deduplicate by date, keeping the last valid quote.
11. Sort ascending by date.
12. Write JSON using:
    [
      { "date": "YYYY-MM-DD", "close": 1.234 }
    ]
13. Optionally write CSV with:
    date,quote

Repository-specific publishing target
- Use repo name MSESharePrices
- Prefer output path:
  docs/json/BOV.json
- Create docs/index.html linking to the JSON feed
- Document the expected Pages URL for this repo clearly

Matt Pocock skills documentation requirements
In README.md and/or CLAUDE.md:
- explain installation:
  npx skills@latest add mattpocock/skills
- recommend running /setup-matt-pocock-skills once in this repo
- explain when to use:
  /grill-me for clarifying requirements
  /to-prd for refining the project brief
  /tdd for red-green-refactor implementation loops
  /diagnose for parsing or runtime failures
  /improve-codebase-architecture for periodic design review

Working style
- First inspect the repo.
- Tell me:
  1. what files already exist,
  2. what files you will create or change,
  3. your project identity proposal,
  4. your core principles,
  5. your capabilities,
  6. your invariants,
  7. your architecture/doc plan,
  8. your implementation plan,
  9. your QA plan,
  10. your Matt Pocock skills plan.
- Then implement.
- Keep edits surgical and focused.
- Do not introduce unrelated refactors.

Validation
- Validate JSON shape.
- Validate date format.
- Validate sorted output.
- Validate duplicate handling.
- Validate tests run cleanly.
- Show the exact commands to:
  - run locally for BOV,
  - run for another symbol,
  - run with manual XLS URLs,
  - install Matt Pocock skills,
  - run the key Matt Pocock skills in this repo,
  - verify the GitHub Pages URL for Portfolio Performance.

Important
- Optimise for maintainability and automation.
- This is a public repo.
- Avoid secrets.
- Keep the solution light but disciplined.
- Make the repo extensible to future Malta symbols.

Please provide:
1. repo inspection summary,
2. project identity,
3. core principles,
4. capabilities,
5. invariants,
6. architecture and documentation plan,
7. implementation plan,
8. QA plan,
9. Matt Pocock skills usage plan,
10. then the code and file changes,
11. then a short usage section with exact commands.
```


## Suggested skill set

For this repo, I would explicitly tell the agent to use these Matt Pocock skills in practice:

- `/setup-matt-pocock-skills` once per repo,[^14_2]
- `/grill-me` before finalising the spec,[^14_3][^14_4]
- `/to-prd` to harden the project brief,[^14_3]
- `/tdd` during parser and transformer implementation,[^14_4][^14_3]
- `/diagnose` for workbook-format or CI failures,[^14_4][^14_3]
- `/improve-codebase-architecture` after the first working version, as a lightweight architecture review.[^14_3]


## Practical note

The key improvement here is that the prompts no longer only ask for code. They now require the agent to produce **identity, principles, capabilities, invariants, architecture, implementation plan, QA plan, and documentation discipline** before building, while also wiring in the Matt Pocock skills workflow and installation command. That should fit your preference for structured but lightweight development very well.
<span style="display:none">[^14_10][^14_11][^14_12][^14_13][^14_14][^14_15][^14_5][^14_6][^14_7][^14_8][^14_9]</span>

<div align="center">⁂</div>

[^14_1]: https://github.com/mattpocock/skills

[^14_2]: https://explainx.ai/blog/matt-pocock-agent-skills-real-engineers

[^14_3]: https://pmlifestyle.jp/resources/mattpocock-skills

[^14_4]: https://www.youtube.com/watch?v=z0y1nuiXdoc

[^14_5]: https://mcp.directory/blog/matt-pocock-skills-the-npm-moment-explained-2026

[^14_6]: https://gitcode.csdn.net/6a0e705e662f9a54cb7606c6.html

[^14_7]: https://www.aihero.dev/learn-anything-with-my-teach-skill

[^14_8]: https://www.aihero.dev/skills-catalog

[^14_9]: https://llmbase.ai/skills/mattpocock/setup-matt-pocock-skills/

[^14_10]: https://lobehub.com/pl/skills/mattpocock-ai-hero-cli-what-to-test

[^14_11]: https://note.com/shali_note/n/ne7849aa13605?hl=en

[^14_12]: https://gitcode.csdn.net/6a253c04662f9a54cb7af27a.html

[^14_13]: https://www.youtube.com/watch?v=M6mYodf0dJM

[^14_14]: https://www.youtube.com/watch?v=qTvD9TNGMKo

[^14_15]: https://www.claudepluginhub.com/plugins/hgxszhj-mattpocock-skills

