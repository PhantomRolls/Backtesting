import pandas as pd
import numpy as np

def get_options_data(config):
    OPTIONS_CSV = f"market_data/{config.ticker}.csv"
    df_full = pd.read_csv(OPTIONS_CSV)
    df = df_full[df_full["date"]==config.date].copy()
    df['daysToExpiration'] = (pd.to_datetime(df['expiration'])-pd.to_datetime(df['date']))/pd.Timedelta(days=1)
    df = df[
    (df['iv'] < 1.5) &
    (df["volume"] > 0) &
    (df["open_interest"] > 10)
    ]
    df["k"] = np.log(df["strike"] / df["spot"])
    df["price"] = (df["bid"] + df["ask"]) / 2
    df["tau"] = df['daysToExpiration']/365
    return df

def filter_df(df):
    df = df[
        (
            ((df["type"] == "C") & (df["k"] >= 0)) |
            ((df["type"] == "P") & (df["k"] <= 0))
        ) &
        (df["daysToExpiration"] > 25) &
        (df["daysToExpiration"] < 200)
    ]
    df = df[
            ((df["type"] == "C") & (df["k"] >= 0)) |
            ((df["type"] == "P") & (df["k"] <= 0))
            ]
    return df

def get_riskfree_rate(date, tau):
    RISKFREE_CSV = f"market_data/riskfree.csv"
    df = pd.read_csv(RISKFREE_CSV, parse_dates=["date"])
    row = df.loc[(df["date"] == date)]
    idx = (row["tenor_years"] - tau).abs().idxmin()
    row = row.loc[idx]
    return row["rate"]


def tenor_to_days():
    df = pd.read_csv("market_data/riskfree.csv", parse_dates=["date"])
    TENOR_TO_DAYS = {
        "1W": 7,
        "2W": 14,
        "1M": 30,
        "2M": 60,
        "3M": 90,
        "6M": 180,
        "9M": 270,
        "1Y": 365,
        "2Y": 730,
        "3Y": 3 * 365,
        "5Y": 5 * 365,
        "7Y": 7 * 365,
        "10Y": 10 * 365,
        "20Y": 20 * 365,
        "30Y": 30 * 365,
    }
    df["tenor_days"] = df["tenor"].map(TENOR_TO_DAYS)
    df["tenor_years"] = df["tenor_days"] / 365.0
    df.to_csv("market_data/riskfree.csv", index=False)
   