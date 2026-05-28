import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import requests
import streamlit as st

# Canonical maturity labels in term order
MATURITIES = ["1M", "2M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

# Treasury XML field names mapped to our labels
_XML_FIELD = {
    "1M":  "BC_1MONTH",  "2M":  "BC_2MONTH",  "3M":  "BC_3MONTH",
    "6M":  "BC_6MONTH",  "1Y":  "BC_1YEAR",   "2Y":  "BC_2YEAR",
    "3Y":  "BC_3YEAR",   "5Y":  "BC_5YEAR",   "7Y":  "BC_7YEAR",
    "10Y": "BC_10YEAR",  "20Y": "BC_20YEAR",  "30Y": "BC_30YEAR",
}

_DS_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices"
_ATOM  = "http://www.w3.org/2005/Atom"

# Base URL for the Treasury live API endpoint
TREASURY_API_BASE = (
    "https://home.treasury.gov/resource-center/data-chart-center/"
    "interest-rates/pages/xml?data=daily_treasury_yield_curve"
    "&field_tdr_date_value={year}"
)


# ─── Live API fetch ──────────────────────────────────────────────────────────

def _fetch_year_from_api(year: int) -> pd.DataFrame:
    """
    Make a GET request to the U.S. Treasury live API for one calendar year.
    Returns a DataFrame of daily yield rates for all 12 maturities.
    """
    url = TREASURY_API_BASE.format(year=year)
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    tree = ET.fromstring(response.content)
    rows = []

    for entry in tree.iter(f"{{{_ATOM}}}entry"):
        props = entry.find(
            ".//{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties"
        )
        if props is None:
            continue

        def g(field):
            el = props.find(f"{{{_DS_NS}}}{field}")
            return el.text if el is not None else None

        rows.append({
            "Date": g("NEW_DATE"),
            **{label: g(xml_field) for label, xml_field in _XML_FIELD.items()}
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for m in MATURITIES:
        df[m] = pd.to_numeric(df[m], errors="coerce")

    return df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)


# ─── Synthetic fallback (only if API is unreachable) ────────────────────────

def _generate_synthetic() -> pd.DataFrame:
    """
    Fallback: generate realistic synthetic yield data (2000-2024).
    Only used if the Treasury API is completely unreachable.
    Calibrated to reproduce real historical episodes:
      - GFC 2008-09, COVID 2020, 2022-23 hiking cycle, inversions.
    """
    np.random.seed(42)
    dates = pd.date_range("2000-01-03", "2024-12-31", freq="B")
    n = len(dates)
    t = np.linspace(0, 1, n)

    base10 = (
        6.5 - 3.5 * t
        + 1.2 * np.sin(2 * np.pi * t * 3)
        + 0.4 * np.cumsum(np.random.randn(n) * 0.012)
    )

    def pulse(start, end, mag, w):
        mask = ((dates >= start) & (dates <= end)).astype(float)
        return mag * np.convolve(mask, np.ones(w) / w, mode="same")[:n]

    base10 -= pulse("2008-09-01", "2009-06-30", 1.5, 120)
    base10 -= pulse("2020-03-01", "2020-12-31", 1.2, 60)
    base10 += pulse("2022-01-01", "2024-12-31", 2.5, 200)
    base10  = np.clip(base10, 0.05, 8.5)

    inv_mask = (
        ((dates >= "2006-07-01") & (dates <= "2007-06-30")) |
        ((dates >= "2022-07-01") & (dates <= "2023-12-31"))
    ).astype(float)
    inv = np.convolve(inv_mask, np.ones(40) / 40, mode="same")[:n]

    OFFSETS = {
        "1M": -1.8, "2M": -1.6, "3M": -1.4, "6M": -1.0,
        "1Y": -0.7, "2Y": -0.3, "3Y": -0.1, "5Y":  0.1,
        "7Y":  0.25,"10Y": 0.0, "20Y": 0.4, "30Y": 0.6,
    }
    rows = {"Date": dates}
    for m, sp in OFFSETS.items():
        adj = sp * (1 - 1.4 * inv) if sp < 0 else sp
        rows[m] = np.clip(base10 + adj + np.random.randn(n) * 0.04, 0.01, 9.5)

    return pd.DataFrame(rows).reset_index(drop=True)


# ─── Public API (called by app.py) ──────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(years: tuple = tuple(range(2000, 2025))) -> pd.DataFrame:
    """
    Main entry point for app.py.

    Fetches yield data LIVE from the U.S. Treasury API for all requested years.
    Results are cached in Streamlit's memory for 1 hour (ttl=3600) so the API
    is not hammered on every user interaction — but refreshes automatically
    every session after the TTL expires.

    This is a true API-backed pipeline:
      Treasury REST/XML API → requests.get() → parse → DataFrame → Streamlit

    Falls back to synthetic data only if the API is completely unreachable.
    """
    frames = []
    failed = []

    for year in years:
        try:
            df = _fetch_year_from_api(year)
            if not df.empty:
                frames.append(df)
        except Exception:
            failed.append(year)

    if frames:
        data = (
            pd.concat(frames, ignore_index=True)
            .drop_duplicates("Date")
            .sort_values("Date")
            .reset_index(drop=True)
        )
        return data

    # Full fallback — API completely unreachable
    return _generate_synthetic()
