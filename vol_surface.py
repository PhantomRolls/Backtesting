import pandas as pd
from pandasql import sqldf
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns
import scipy.interpolate as interpolate



def get_data(ticker, date):
    OPTIONS_CSV = f"market_data/{ticker}.csv"
    df_full = pd.read_csv(OPTIONS_CSV)
    df = df_full[df_full["date"]==date].copy()
    df['daysToExpiration'] = (pd.to_datetime(df['expiration'])-pd.to_datetime(df['date']))/pd.Timedelta(days=1)
    df = df[
    (df['iv'] < 1.5) &
    (df["volume"] > 0) &
    (df["open_interest"] > 10) &
    (df["daysToExpiration"] > 25) &
    (df["daysToExpiration"] < 200)
    ]
    df["k"] = np.log(df["strike"] / df["spot"])
    df = df[
    ((df["type"] == "C") & (df["k"] >= 0)) |
    ((df["type"] == "P") & (df["k"] <= 0))
    ]
    return df


def max_area_complete_grid(df):
    adjK = defaultdict(set)
    adjT = defaultdict(set)

    for _, r in df.iterrows():
        adjK[r["strike"]].add(r["daysToExpiration"])
        adjT[r["daysToExpiration"]].add(r["strike"])

    K = set(adjK)
    T = set(adjT)

    while True:
        badK = [k for k in K if len(adjK[k] & T) < len(T)]
        badT = [t for t in T if len(adjT[t] & K) < len(K)]

        if not badK and not badT:
            break

        # aire si on supprime un strike ou une maturité
        area_remove_k = (len(K) - 1) * len(T) if badK else -1
        area_remove_t = len(K) * (len(T) - 1) if badT else -1

        if area_remove_k >= area_remove_t:
            k = max(badK, key=lambda k: len(T) - len(adjK[k] & T))
            K.remove(k)
        else:
            t = max(badT, key=lambda t: len(K) - len(adjT[t] & K))
            T.remove(t)
    return K, T

def create_volatility_surface(options_data, interpolation):
    K_active, T_active = max_area_complete_grid(options_data)
    options_grid = options_data[options_data["strike"].isin(K_active) & options_data["daysToExpiration"].isin(T_active)]
    spot = options_grid['spot'].iloc[-1]
    print("nombre d'options:", len(options_grid))
    print(len(K_active), "strikes")
    print(np.log((options_grid["strike"].unique()/spot)).round(2))
    print(len(T_active), "maturités")
    print(options_grid["daysToExpiration"].unique())
    
    surface = (
        options_grid[["daysToExpiration", "strike", "iv"]]
        .pivot_table(
            values="iv", index="strike", columns="daysToExpiration"
        )
        .dropna()
    )
    # Prepare interpolation data
    x = surface.columns.values
    y = np.log(surface.index.values/spot)
    X, Y = np.meshgrid(x, y)
    Z = surface.values

    if interpolation:   
        # Create interpolation points
        x_new = np.linspace(x.min(), x.max(), 100)
        y_new = np.linspace(y.min(), y.max(), 100)

        # Perform interpolation
        spline = interpolate.SmoothBivariateSpline(
            X.flatten(), Y.flatten(), Z.flatten(), s=0.1
        )
        X, Y = np.meshgrid(x_new, y_new)
        Z = spline(x_new, y_new).T

    return X, Y, Z, options_grid


def plot_volatility_surface(X, Y, Z, vmin=0.2, vmax=0.6):
    plt.style.use("default")
    sns.set_style("whitegrid", {"axes.grid": False})

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(
        Y, X, Z, cmap="viridis", vmin=vmin, vmax=vmax, alpha=0.9, linewidth=0, antialiased=True
    )
    fig.colorbar(surface, ax=ax, shrink=0.5, aspect=10, label="IV")
    ax.set_ylabel("Days to Expiration")
    ax.set_xlabel("log-moneyness ln(K / S0)")
    ax.set_zlabel("Implied Volatility")
    ax.set_title(f"{TICKER} Volatility Surface")
    ax.view_init(elev=20, azim=45)
    ax.invert_yaxis()

    plt.tight_layout()
    plt.show()


def volsurface(TICKER, date, interpolation):  
    options = get_data(TICKER, date)
    X, Y, Z, options_grid = create_volatility_surface(options, interpolation)
    vmin = options_grid['iv'].quantile(0.05)
    vmax = options_grid['iv'].quantile(0.95)
    plot_volatility_surface(X, Y, Z, vmin, vmax)

def skew(TICKER, date, daysToExpiration, visual="log-moneyness"):
    options = get_data(TICKER, date)
    daysToExpiration = options[options["daysToExpiration"]>=daysToExpiration].iloc[0] ["daysToExpiration"]
    options = options[options["daysToExpiration"]==daysToExpiration]
    log_moneynes = np.log(options["strike"]/options["spot"])
    options["call_delta"] = np.where(
        options["type"] == "P",
        options["delta"] + 1,
        options["delta"]
    )
    if visual == "log-moneyness":
        x_axis = log_moneynes
        x_label = "Log-moneyness"
    elif visual == "delta":
        x_axis = options["call_delta"] * 100
        x_label = "Delta"
    plt.plot(x_axis, options["iv"], marker='+')
    plt.title(f"{TICKER} skew | Days to Expiration = {daysToExpiration}")
    plt.xlabel(x_label)
    plt.ylabel("IV")
    plt.ylim(bottom=0, top=1)
    plt.show()
    
if __name__ == "__main__":
    TICKER = "NVDA"
    date = "2025-12-12"
    interpolation = True
    # volsurface(TICKER, date, interpolation=interpolation)
    skew(TICKER, date, 100, visual="log-moneyness")