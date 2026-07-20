import io
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest

import mse_pp_feed as feed


def make_workbook_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


# ---- header normalisation -------------------------------------------------

@pytest.mark.parametrize(
    "columns",
    [
        ["Symbol code", "DATE", "Close Price"],
        ["Symbol Code", "Trade Date", "Close"],
        ["Ticker", "Date", "Last Price"],
    ],
)
def test_normalise_headers_accepts_known_aliases(columns):
    df = pd.DataFrame([[  "BOV", "2026-01-05", 1.92 ]], columns=columns)
    normalised = feed.normalise_headers(df)
    assert list(normalised.columns) == ["symbol", "date", "close"]
    assert normalised.iloc[0]["symbol"] == "BOV"


def test_normalise_headers_raises_missing_column_error():
    df = pd.DataFrame([["BOV", "2026-01-05"]], columns=["Symbol code", "DATE"])
    with pytest.raises(feed.MissingColumnError, match="close"):
        feed.normalise_headers(df)


# ---- symbol filtering ------------------------------------------------------

def test_extract_quotes_filters_by_symbol():
    df = pd.DataFrame(
        {
            "symbol": ["BOV", "APS", "BOV"],
            "date": ["2026-01-05", "2026-01-05", "2026-01-06"],
            "close": [1.92, 0.55, 1.91],
        }
    )
    result = feed.extract_quotes(df, "BOV")
    assert [q["date"] for q in result.quotes] == ["2026-01-05", "2026-01-06"]
    assert result.rows_dropped_invalid == 0


# ---- date normalisation -----------------------------------------------------

def test_extract_quotes_normalises_various_date_formats():
    df = pd.DataFrame(
        {
            "symbol": ["BOV", "BOV"],
            "date": ["05-Jan-2026", "2026-01-06"],
            "close": [1.92, 1.91],
        }
    )
    result = feed.extract_quotes(df, "BOV")
    dates = sorted(q["date"] for q in result.quotes)
    assert dates == ["2026-01-05", "2026-01-06"]


# ---- price coercion ----------------------------------------------------------

def test_extract_quotes_coerces_comma_formatted_and_drops_invalid_prices():
    df = pd.DataFrame(
        {
            "symbol": ["BOV", "BOV", "BOV"],
            "date": ["2026-01-05", "2026-01-06", "2026-01-07"],
            "close": ["1,920", "not-a-number", 1.90],
        }
    )
    result = feed.extract_quotes(df, "BOV")
    assert result.rows_dropped_invalid == 1
    values = {q["date"]: q["close"] for q in result.quotes}
    assert values["2026-01-05"] == 1920.0
    assert values["2026-01-07"] == 1.90
    assert "2026-01-06" not in values


def test_extract_quotes_drops_blank_date_or_price():
    df = pd.DataFrame(
        {
            "symbol": ["BOV", "BOV"],
            "date": ["2026-01-05", None],
            "close": [1.92, 1.90],
        }
    )
    result = feed.extract_quotes(df, "BOV")
    assert result.rows_dropped_invalid == 1
    assert len(result.quotes) == 1


# ---- dedupe and sort ----------------------------------------------------------

def test_dedupe_and_sort_keeps_last_valid_and_sorts_ascending():
    quotes = [
        {"date": "2026-01-06", "close": 1.91},
        {"date": "2026-01-05", "close": 1.92},
        {"date": "2026-01-05", "close": 1.925},  # later occurrence should win
    ]
    result = feed.dedupe_and_sort(quotes)
    assert [q["date"] for q in result] == ["2026-01-05", "2026-01-06"]
    assert result[0]["close"] == 1.925


# ---- JSON / CSV output schema --------------------------------------------------

def test_write_json_schema(tmp_path):
    quotes = [{"date": "2026-01-05", "close": 1.92}, {"date": "2026-01-06", "close": 1.91}]
    out = tmp_path / "BOV.json"
    feed.write_json(quotes, out)
    loaded = json.loads(out.read_text())
    assert loaded == quotes
    assert all(isinstance(q["close"], float) for q in loaded)


def test_write_csv_schema(tmp_path):
    quotes = [{"date": "2026-01-05", "close": 1.92}, {"date": "2026-01-06", "close": 1.91}]
    out = tmp_path / "BOV.csv"
    feed.write_csv(quotes, out)
    lines = out.read_text().strip().splitlines()
    assert lines[0] == "date,quote"
    assert lines[1] == "2026-01-05,1.92"
    assert lines[2] == "2026-01-06,1.91"


# ---- end-to-end via process_workbook (fixture-based, no network) -------------

def test_process_workbook_end_to_end():
    df = pd.DataFrame(
        {
            "Symbol code": ["BOV", "APS", "BOV", "BOV"],
            "DATE": ["05-Jan-2026", "05-Jan-2026", "06-Jan-2026", "bad-date"],
            "Close Price": [1.92, 0.55, 1.91, 9.99],
        }
    )
    data = make_workbook_bytes(df)
    result = feed.process_workbook(data, "BOV")
    final = feed.dedupe_and_sort(result.quotes)

    assert final == [
        {"date": "2026-01-05", "close": 1.92},
        {"date": "2026-01-06", "close": 1.91},
    ]
    assert result.rows_dropped_invalid == 1


# ---- read_workbook engine routing --------------------------------------------

def test_read_workbook_routes_ole2_files_through_xlrd_with_corruption_tolerance(monkeypatch):
    calls = []

    def fake_read_excel(_buf, **kwargs):
        calls.append(kwargs)
        return pd.DataFrame()

    monkeypatch.setattr(feed.pd, "read_excel", fake_read_excel)

    ole2_bytes = feed.OLE2_MAGIC + b"\x00" * 24
    feed.read_workbook(ole2_bytes)

    assert calls == [{"engine": "xlrd", "engine_kwargs": {"ignore_workbook_corruption": True}}]


def test_read_workbook_leaves_xlsx_files_to_default_pandas_detection(monkeypatch):
    calls = []

    def fake_read_excel(_buf, **kwargs):
        calls.append(kwargs)
        return pd.DataFrame()

    monkeypatch.setattr(feed.pd, "read_excel", fake_read_excel)

    zip_bytes = b"PK\x03\x04" + b"\x00" * 28
    feed.read_workbook(zip_bytes)

    assert calls == [{}]


def test_read_workbook_falls_back_to_libreoffice_when_xlrd_rejects_a_valid_file(monkeypatch):
    ole2_bytes = feed.OLE2_MAGIC + b"\x00" * 24
    converted_marker = object()

    def fake_read_excel(_buf, **kwargs):
        if kwargs.get("engine") == "xlrd":
            raise Exception("directory corruption: seen[0] == 2")
        assert kwargs.get("engine") == "openpyxl"
        return converted_marker

    conversion_calls = []

    def fake_convert(data):
        conversion_calls.append(data)
        return b"fake-xlsx-bytes"

    monkeypatch.setattr(feed.pd, "read_excel", fake_read_excel)
    monkeypatch.setattr(feed, "convert_xls_to_xlsx_via_libreoffice", fake_convert)

    result = feed.read_workbook(ole2_bytes)

    assert result is converted_marker
    assert conversion_calls == [ole2_bytes]


def test_convert_xls_to_xlsx_via_libreoffice_real_roundtrip():
    """Integration test: exercises the real `soffice` binary, not a mock.

    Builds a genuine legacy .xls (via LibreOffice itself, converting from a
    synthetic xlsx) and confirms our conversion helper can turn it back into
    an xlsx that pandas reads correctly. This doesn't reproduce the specific
    xlrd bug (that needs a real MSE file, see docs/qa.md), but it does prove
    the LibreOffice subprocess plumbing itself works end-to-end.
    """
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        pytest.skip("soffice/libreoffice not available in this environment")

    df = pd.DataFrame({
        "Symbol code": ["BOV"],
        "DATE": ["05-Jan-2026"],
        "Close Price": [1.92],
    })
    xlsx_bytes = make_workbook_bytes(df)

    with tempfile.TemporaryDirectory() as tmpdir:
        xlsx_path = Path(tmpdir) / "roundtrip.xlsx"
        xlsx_path.write_bytes(xlsx_bytes)
        subprocess.run(
            [soffice, "--headless", "--convert-to", "xls", "--outdir", tmpdir, str(xlsx_path)],
            check=True, capture_output=True, timeout=60,
        )
        xls_path = Path(tmpdir) / "roundtrip.xls"
        if not xls_path.exists():
            # soffice can exit 0 while printing "source file could not be loaded"
            # instead of a nonzero code -- a real quirk this environment hits
            # (headless LibreOffice conversion is broken in this sandbox; it is
            # a standard, working setup on GitHub Actions' ubuntu-latest, which
            # is what actually matters for this project -- see docs/qa.md).
            pytest.skip("soffice silently failed to convert in this environment")
        real_xls_bytes = xls_path.read_bytes()

    assert real_xls_bytes[:8] == feed.OLE2_MAGIC

    converted = feed.convert_xls_to_xlsx_via_libreoffice(real_xls_bytes)
    roundtripped = pd.read_excel(io.BytesIO(converted), engine="openpyxl")

    assert roundtripped.iloc[0]["Symbol code"] == "BOV"
    assert roundtripped.iloc[0]["Close Price"] == 1.92


# ---- discover_urls -----------------------------------------------------------

def test_discover_urls_extracts_and_resolves_xls_links():
    html = """
    <a href="/download/statistics/archive/2025.xls">2025</a>
    <a href="/download/statistics/archive/2024.xlsx">2024</a>
    <a href="/not-a-workbook.pdf">ignore me</a>
    """
    urls = feed.discover_urls(html)
    assert urls == [
        "https://www.borzamalta.com.mt/download/statistics/archive/2025.xls",
        "https://www.borzamalta.com.mt/download/statistics/archive/2024.xlsx",
    ]


def test_discover_urls_filters_by_year_range():
    html = """
    <a href="/archive/2025.xls">2025</a>
    <a href="/archive/2020.xls">2020</a>
    <a href="/archive/no-year.xls">unknown</a>
    """
    urls = feed.discover_urls(html, start_year=2023, end_year=2026)
    assert any("2025" in u for u in urls)
    assert not any("2020" in u for u in urls)
    assert any("no-year" in u for u in urls)  # URLs without a year are kept, not dropped
