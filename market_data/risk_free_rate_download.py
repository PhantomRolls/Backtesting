import requests
import pandas as pd
from datetime import datetime
import os

FRED_API_KEY = "345db1b4f6073c599418caa080dadfea"


FRED_SERIES = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}

def get_fred_rate(series_id):
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    value = data["observations"][0]["value"]
    return None if value == "." else float(value)/100.0  # convert % → decimal


def get_fred_curve():
    rows = []
    today = datetime.now().date()

    for tenor, sid in FRED_SERIES.items():
        rate = get_fred_rate(sid)
        rows.append({
            "date": today,
            "tenor": tenor,
            "rate": rate
        })

    return pd.DataFrame(rows)

def update_fred_history(df, filename="market_data/riskfree.csv"):
    df["rate"] = df["rate"].round(4)
    if os.path.exists(filename):
        old = pd.read_csv(filename, parse_dates=["date"])
        old["rate"] = old["rate"].round(4)

        full = pd.concat([old, df], ignore_index=True)
        full = full.drop_duplicates(subset=["date", "tenor"])
    else:
        full = df

    full["rate"] = full["rate"].round(4)
    full.to_csv(filename, index=False, float_format="%.4f")

    print("Saved/Updated", filename)
    return full



if __name__ == "__main__":
    update_fred_history(get_fred_curve())



