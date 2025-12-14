import requests
import pandas as pd
from datetime import datetime
import yfinance as yf
import os

###########################################
# Parsing OCC symbols (expiration, type, strike)
###########################################

def parse_occ_option_symbol(symbol: str, underlying: str):
    root_len = len(underlying)
    code = symbol[root_len:]  # e.g. '251212C00050000'

    # Expiration YYMMDD
    y = int(code[0:2])
    m = int(code[2:4])
    d = int(code[4:6])
    year = 2000 + y
    expiration = datetime(year, m, d).date()

    # Call/Put
    opt_type = code[6]  # 'C' or 'P'

    # Strike (/1000)
    strike = int(code[7:]) / 1000.0

    return expiration, opt_type, strike


###########################################
# Download NVDA option surface from CBOE
###########################################

def get_cboe_surface(ticker: str) -> pd.DataFrame:
    url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{ticker.upper()}.json"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    options = data["data"]["options"]
    rows = []

    for opt in options:
        occ = opt["option"]

        expiration, opt_type, strike = parse_occ_option_symbol(occ, ticker.upper())

        rows.append({
            "date": datetime.now().date(),          # TODAY'S DATE
            "option_symbol": occ,
            "expiration": expiration,
            "type": opt_type,
            "strike": strike,
            "bid": opt.get("bid", None),
            "ask": opt.get("ask", None),
            "iv": opt.get("iv", None),
            "delta": opt.get("delta", None),
            "gamma": opt.get("gamma", None),
            "theta": opt.get("theta", None),
            "vega": opt.get("vega", None),
            "rho": opt.get("rho", None),
            "volume": opt.get("volume", None),
            "open_interest": opt.get("open_interest", None),
            "last": opt.get("last_trade_price", None),
            "last_trade_time": opt.get("last_trade_time", None),
        })

    return pd.DataFrame(rows)


###########################################
# Get SPOT price from Yahoo Finance
###########################################

def get_spot_yahoo(ticker):
    t = yf.Ticker(ticker)
    price = t.history(period="1d")["Close"].iloc[-1]
    return float(price)


###########################################
# Clean and filter option surface
###########################################

def clean_surface(df: pd.DataFrame, spot: float):
    df = df.copy()

    # Remove bad or irrelevant options
    df = df[df["iv"] > 0]
    df = df[(df["bid"] + df["ask"]) > 0]
    df = df[df["volume"] > 0]

    # Remove extreme strikes
    df = df[df["strike"].between(0.5 * spot, 1.5 * spot)]

    return df


###########################################
# Append daily data to master CSV
###########################################

def update_history(df: pd.DataFrame, filename):
    if os.path.exists(filename):
        old = pd.read_csv(filename, parse_dates=["date", "expiration"])
        full = pd.concat([old, df], ignore_index=True)
        full = full.drop_duplicates(subset=["date", "option_symbol"])
    else:
        full = df

    full.to_csv(filename, index=False)
    print(f"Updated {filename} with {len(df)} new rows.")
    return full


###########################################
# Main
###########################################

if __name__ == "__main__":
    TICKER = "AAPL"

    print("Downloading spot price...")
    spot = get_spot_yahoo(TICKER)
    print("Spot =", spot)

    print("Downloading option surface from CBOE...")
    df = get_cboe_surface(TICKER)

    print("Cleaning data...")
    df_clean = clean_surface(df, spot)

    # ADD SPOT COLUMN (important!)
    df_clean["spot"] = spot

    print("Saving daily data...")
    df_all = update_history(df_clean, filename=f"market_data/{TICKER}.csv")

    print("Done! Total rows in history:", len(df_all))
