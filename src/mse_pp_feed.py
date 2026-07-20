#!/usr/bin/env python3
"""Malta Stock Exchange -> Portfolio Performance historical quote feed generator.

Downloads MSE "Daily Trading Summary" yearly archive workbooks, extracts closing
prices for a given symbol, and writes a JSON feed Portfolio Performance can read
via its JSON quote-feed provider (Path to Date = $[*].date, Path to Close = $[*].close).

See docs/spec.md, docs/architecture.md, and docs/qa.md for the full design and
the documented live-verification gap (MSE blocked automated requests from the
development sandbox, so header names below are based on research, not a
confirmed live sample -- use --manual-url with a real downloaded file to verify).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests

ARCHIVE_PAGE_URL = "https://www.borzamalta.com.mt/publications-and-statistics?category=33"
ARCHIVE_BASE_URL = "https://www.borzamalta.com.mt"
USER_AGENT = "Mozilla/5.0 (compatible; MSESharePrices/1.0; +https://github.com/heyvinay/MSESharePrices)"
REQUEST_TIMEOUT_SECONDS = 30
LIBREOFFICE_TIMEOUT_SECONDS = 60

# Recognised header aliases per canonical field. Header matching is case-insensitive
# and ignores surrounding whitespace. Extend this list if a real MSE workbook uses a
# spelling not covered here (see docs/decision-log.md, 2026-07-20 entry).
HEADER_ALIASES = {
    "symbol": ["symbol code", "symbol", "ticker", "instrument code"],
    "date": ["date", "trade date", "value date"],
    "close": ["close price", "close", "last price", "last traded price"],
}


class MissingColumnError(Exception):
    """Raised when a workbook is missing a required column (no alias matched)."""


@dataclass
class ExtractResult:
    quotes: list[dict]
    rows_dropped_invalid: int = 0


@dataclass
class RunStats:
    files_processed: int = 0
    files_failed: int = 0
    rows_matched: int = 0
    rows_dropped_invalid: int = 0
    failures: list[str] = field(default_factory=list)


def discover_urls(page_html: str, start_year: int | None = None, end_year: int | None = None) -> list[str]:
    """Extract candidate yearly workbook URLs from the archive page's HTML.

    Looks for href attributes pointing at .xls/.xlsx files and resolves them
    against the MSE base URL. If start_year/end_year are given, only URLs whose
    href contains a 4-digit year within that inclusive range are kept; URLs with
    no discernible year are always kept (better to include than silently drop).
    """
    hrefs = re.findall(r'href=["\']([^"\']+\.xlsx?)["\']', page_html, flags=re.IGNORECASE)
    urls = [urljoin(ARCHIVE_BASE_URL, href) for href in hrefs]

    if start_year is None and end_year is None:
        return urls

    lo = start_year if start_year is not None else 0
    hi = end_year if end_year is not None else 9999

    filtered = []
    for url in urls:
        years_in_url = [int(y) for y in re.findall(r"(?:19|20)\d{2}", url)]
        if not years_in_url:
            filtered.append(url)
            continue
        if any(lo <= y <= hi for y in years_in_url):
            filtered.append(url)
    return filtered


def download_file(url: str) -> bytes:
    """Download a single file (workbook or the archive page) and return raw bytes."""
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    print(
        f"INFO: downloaded {url} -> {len(response.content)} bytes, "
        f"Content-Type: {response.headers.get('Content-Type')}",
        file=sys.stderr,
    )
    return response.content


OLE2_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")


class WorkbookConversionError(Exception):
    """Raised when a legacy .xls file can't be parsed by xlrd or converted via LibreOffice."""


def convert_xls_to_xlsx_via_libreoffice(data: bytes) -> bytes:
    """Convert legacy .xls bytes to .xlsx bytes using headless LibreOffice.

    Some real MSE workbooks are valid OLE2 compound documents that Excel and
    LibreOffice open fine, but trip xlrd's directory-chain "seen" check in a
    way xlrd's own ignore_workbook_corruption flag does not cover (that flag
    only guards a different, unrelated code path -- see docs/decision-log.md,
    2026-07-20 entry). LibreOffice's OLE2 parser is far more tolerant of
    real-world exporter quirks, so this is used as a fallback, not the primary
    path, to avoid the cost of shelling out for well-formed files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "workbook.xls"
        src.write_bytes(data)
        try:
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "xlsx", "--outdir", tmpdir, str(src)],
                check=True,
                capture_output=True,
                timeout=LIBREOFFICE_TIMEOUT_SECONDS,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            raise WorkbookConversionError(f"LibreOffice conversion failed: {exc}") from exc

        converted = Path(tmpdir) / "workbook.xlsx"
        if not converted.exists():
            raise WorkbookConversionError("LibreOffice did not produce workbook.xlsx")
        return converted.read_bytes()


HEADER_SCAN_MAX_ROWS = 15


def _looks_like_header_row(values: list) -> bool:
    lowered = [str(v).strip().lower() for v in values]
    return all(any(alias in lowered for alias in aliases) for aliases in HEADER_ALIASES.values())


def _promote_header_row(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Find the real header row within the first HEADER_SCAN_MAX_ROWS rows and promote it.

    Real MSE exports (confirmed against a live archive file) have a banner/title
    row above the actual column headers, so the header is not reliably row 0.
    Falls back to returning raw_df unchanged (pandas' default row-0-as-header
    behaviour) if no row in the scan window matches -- normalise_headers() will
    then raise its own clear MissingColumnError.
    """
    limit = min(HEADER_SCAN_MAX_ROWS, len(raw_df))
    for row_idx in range(limit):
        values = raw_df.iloc[row_idx].tolist()
        if _looks_like_header_row(values):
            promoted = raw_df.iloc[row_idx + 1:].copy()
            promoted.columns = [str(v) for v in values]
            promoted.reset_index(drop=True, inplace=True)
            return promoted

    print(f"DEBUG: no header row found in first {limit} rows; dumping for diagnosis:", file=sys.stderr)
    for row_idx in range(limit):
        print(f"DEBUG: row {row_idx}: {raw_df.iloc[row_idx].tolist()!r}", file=sys.stderr)
    return raw_df


def read_workbook(data: bytes) -> pd.DataFrame:
    """Parse workbook bytes (.xls or .xlsx) into a DataFrame of raw rows.

    For legacy .xls (OLE2) files, tries xlrd first (fast, no subprocess), then
    falls back to a LibreOffice-based conversion if xlrd rejects a file that is
    nonetheless a genuine workbook (confirmed against a real MSE archive file:
    Content-Type application/vnd.ms-excel, correct OLE2 magic bytes, clean
    sector-aligned size -- xlrd was simply wrong to reject it). Reads without
    assuming row 0 is the header, since real MSE exports have a banner row
    above the actual column headers (also confirmed against a real file).
    """
    if data[:8] == OLE2_MAGIC:
        try:
            raw = pd.read_excel(io.BytesIO(data), header=None, engine="xlrd",
                                 engine_kwargs={"ignore_workbook_corruption": True})
        except Exception:  # noqa: BLE001 - xlrd raises assorted error types for bad files
            xlsx_data = convert_xls_to_xlsx_via_libreoffice(data)
            raw = pd.read_excel(io.BytesIO(xlsx_data), header=None, engine="openpyxl")
    else:
        raw = pd.read_excel(io.BytesIO(data), header=None)
    return _promote_header_row(raw)


def normalise_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to canonical names (symbol/date/close) using HEADER_ALIASES.

    Raises MissingColumnError naming the missing field if no alias is found for
    a required canonical column.
    """
    lookup = {str(col).strip().lower(): col for col in df.columns}

    rename_map = {}
    for canonical, aliases in HEADER_ALIASES.items():
        match = next((lookup[alias] for alias in aliases if alias in lookup), None)
        if match is None:
            raise MissingColumnError(
                f"Could not find a column for '{canonical}' among columns "
                f"{list(df.columns)}. Recognised aliases: {aliases}. "
                "See docs/qa.md manual verification checklist."
            )
        rename_map[match] = canonical

    return df.rename(columns=rename_map)[list(HEADER_ALIASES.keys())]


def extract_quotes(df: pd.DataFrame, symbol: str) -> ExtractResult:
    """Filter to `symbol`, clean/coerce, return quotes plus a count of dropped rows."""
    matched = df[df["symbol"].astype(str).str.strip() == symbol].copy()

    # Parsed element-by-element (not as a vectorised batch): MSE workbooks can mix
    # date formats across years, and pandas infers a single format for a whole
    # batch, silently turning non-conforming values into NaT.
    parsed_dates = matched["date"].apply(lambda v: pd.to_datetime(v, errors="coerce"))
    parsed_close = pd.to_numeric(
        matched["close"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )

    valid_mask = parsed_dates.notna() & parsed_close.notna()
    dropped = int((~valid_mask).sum())

    quotes = [
        {"date": d.strftime("%Y-%m-%d"), "close": float(c)}
        for d, c in zip(parsed_dates[valid_mask], parsed_close[valid_mask])
    ]
    return ExtractResult(quotes=quotes, rows_dropped_invalid=dropped)


def dedupe_and_sort(quotes: list[dict]) -> list[dict]:
    """Resolve duplicate dates (last valid row wins) and sort ascending by date."""
    by_date: dict[str, dict] = {}
    for quote in quotes:
        by_date[quote["date"]] = quote
    return [by_date[d] for d in sorted(by_date.keys())]


def write_json(quotes: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(quotes, indent=2) + "\n", encoding="utf-8")


def write_csv(quotes: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "quote"])
        for quote in quotes:
            writer.writerow([quote["date"], quote["close"]])


def process_workbook(data: bytes, symbol: str) -> ExtractResult:
    df = read_workbook(data)
    df = normalise_headers(df)
    return extract_quotes(df, symbol)


def resolve_source_urls(manual_urls: list[str], start_year: int | None, end_year: int | None) -> list[str]:
    if manual_urls:
        return manual_urls
    page_html = download_file(ARCHIVE_PAGE_URL).decode("utf-8", errors="replace")
    return discover_urls(page_html, start_year, end_year)


def run(
    symbol: str,
    start_year: int | None,
    end_year: int | None,
    manual_urls: list[str],
    output_json: Path,
    output_csv: Path | None,
) -> tuple[int, RunStats, list[dict]]:
    stats = RunStats()

    try:
        urls = resolve_source_urls(manual_urls, start_year, end_year)
    except Exception as exc:  # noqa: BLE001 - top-level discovery failure is reported, not swallowed
        print(f"ERROR: could not discover source files ({exc}). "
              f"Pass --manual-url to bypass discovery.", file=sys.stderr)
        return 1, stats, []

    if not urls:
        print("ERROR: no source files found or provided. Pass --manual-url to bypass discovery.",
              file=sys.stderr)
        return 1, stats, []

    all_quotes: list[dict] = []
    for url in urls:
        try:
            data = download_file(url) if url.startswith("http") else Path(url).read_bytes()
        except Exception as exc:  # noqa: BLE001 - one bad year shouldn't abort the whole run
            stats.files_failed += 1
            stats.failures.append(f"{url}: {exc}")
            print(f"WARNING: failed to download {url}: {exc}", file=sys.stderr)
            continue

        try:
            result = process_workbook(data, symbol)
        except Exception as exc:  # noqa: BLE001 - one bad year shouldn't abort the whole run
            stats.files_failed += 1
            stats.failures.append(f"{url}: {exc}")
            print(
                f"WARNING: failed to process {url}: {exc} "
                f"(downloaded {len(data)} bytes, first 16 bytes: {data[:16].hex()})",
                file=sys.stderr,
            )
            continue
        stats.files_processed += 1
        stats.rows_matched += len(result.quotes)
        stats.rows_dropped_invalid += result.rows_dropped_invalid
        all_quotes.extend(result.quotes)

    if stats.files_processed == 0:
        print("ERROR: no source file could be processed successfully.", file=sys.stderr)
        return 1, stats, []

    final_quotes = dedupe_and_sort(all_quotes)
    write_json(final_quotes, output_json)
    if output_csv is not None:
        write_csv(final_quotes, output_csv)

    return 0, stats, final_quotes


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Portfolio Performance JSON quote feed from MSE archive data."
    )
    parser.add_argument("--symbol", default="BOV", help="MSE symbol code to extract (default: BOV)")
    parser.add_argument("--start-year", type=int, default=None, help="Earliest year to include")
    parser.add_argument("--end-year", type=int, default=None, help="Latest year to include")
    parser.add_argument(
        "--manual-url",
        action="append",
        default=[],
        dest="manual_urls",
        help="Explicit workbook URL or local file path (repeatable). Bypasses page discovery.",
    )
    parser.add_argument("--output-json", type=Path, default=None,
                         help="Output JSON path (default: docs/json/<SYMBOL>.json)")
    parser.add_argument("--output-csv", type=Path, default=None,
                         help="Optional CSV output path (date,quote)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    output_json = args.output_json or Path("docs/json") / f"{args.symbol}.json"

    exit_code, stats, final_quotes = run(
        symbol=args.symbol,
        start_year=args.start_year,
        end_year=args.end_year,
        manual_urls=args.manual_urls,
        output_json=output_json,
        output_csv=args.output_csv,
    )

    if exit_code == 0:
        date_range = f"{final_quotes[0]['date']} to {final_quotes[-1]['date']}" if final_quotes else "n/a"
        print(
            f"Done. files_processed={stats.files_processed} files_failed={stats.files_failed} "
            f"rows_matched={stats.rows_matched} rows_dropped_invalid={stats.rows_dropped_invalid} "
            f"date_range={date_range} output={output_json}"
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
