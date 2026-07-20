import io
import json

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
