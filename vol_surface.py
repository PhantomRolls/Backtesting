import pandas as pd
from pandasql import sqldf
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import seaborn as sns
import scipy.interpolate as interpolate

TICKER = "SPY"
date = "2025-12-12"
interpolation = False

def get_data(TICKER):
    df = pd.read_csv(f"market_data/{TICKER}.csv")
    q = """
    SELECT *
    FROM df
    WHERE date = "2025-12-12"
    """
    df = sqldf(q)
    df['daysToExpiration'] = (pd.to_datetime(df['expiration'])-pd.to_datetime(df['date']))/pd.Timedelta(days=365)
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
            # enlever le strike "le plus incompatible"
            k = max(badK, key=lambda k: len(T) - len(adjK[k] & T))
            K.remove(k)
        else:
            # enlever la maturité "la plus incompatible"
            t = max(badT, key=lambda t: len(K) - len(adjT[t] & K))
            T.remove(t)

    return K, T

def create_volatility_surface(calls_data, interpolation):
    
    K_active, T_active = max_area_complete_grid(calls_data)
    calls_grid = calls_data[calls_data["strike"].isin(K_active) & calls_data["daysToExpiration"].isin(T_active)]

    surface = (
        calls_grid[["daysToExpiration", "strike", "iv"]]
        .pivot_table(
            values="iv", index="strike", columns="daysToExpiration"
        )
        .dropna()
    )
    spot = calls_grid['spot'].iloc[-1]

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

    return X, Y, Z


def plot_volatility_surface(X, Y, Z):
    plt.style.use("default")
    sns.set_style("whitegrid", {"axes.grid": False})

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(
        X, Y, Z, cmap="viridis", vmin=0.10, vmax=0.60, alpha=0.9, linewidth=0, antialiased=True
    )
    fig.colorbar(surface, ax=ax, shrink=0.5, aspect=10, label="IV")
    ax.set_xlabel("Days to Expiration")
    ax.set_ylabel("log-moneyness ln(K / S0)")
    ax.set_zlabel("Implied Volatility")
    ax.set_title("SPY Volatility Surface")
    ax.view_init(elev=20, azim=45)

    plt.tight_layout()
    plt.show()


def volsurface(TICKER, date, interpolation):  
    # Load and process calls data
    OPTIONS_CSV = f"market_data/{TICKER}.csv"
    df = pd.read_csv(OPTIONS_CSV)
    calls = df[(df["date"]==date) & (df["type"]=="C")]
    calls['daysToExpiration'] = (pd.to_datetime(calls['expiration'])-pd.to_datetime(calls['date']))/pd.Timedelta(days=1)

    # Create and plot surface
    X_new, Y_new, Z_smooth = create_volatility_surface(calls, interpolation)
    plot_volatility_surface(X_new, Y_new, Z_smooth)
    

volsurface(TICKER, date, interpolation=interpolation)