import numpy as np
from scipy.stats import norm


def call(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(- r * T) * norm.cdf(d2)

def put(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(- r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def straddle(S, K, T, r, sigma):
    return call(S, K, T, r, sigma) + put(S, K, T, r, sigma)


def compute_iv(price_market, S, K, T, r, right,
               tol=1e-6, max_iter=100,
               sig_low=1e-8, sig_high=10.0):

    # ---- 1. Cas triviaux ------------------------------------
    if price_market <= 0 or T <= 0:
        return np.nan

    # ---- 2. Bornes du prix ----------------------------------
    # prix min et max en BS
    forward = S * np.exp(r * T)
    
    if right == 'C':
        price_min = max(0, S - K * np.exp(-r*T))
    else:  # PUT
        price_min = max(0, K * np.exp(-r*T) - S)

    if price_market < price_min - 1e-12:
        # aucune volatilité ne peut générer ce prix (option trop bon marché)
        return np.nan

    # ---- 3. Algo dichotomique --------------------------------
    for _ in range(max_iter):
        sig_mid = 0.5 * (sig_low + sig_high)

        # Prix modèle
        if right == 'C':
            model = call(S, K, T, r, sig_mid)
        else:
            model = put(S, K, T, r, sig_mid)

        diff = model - price_market

        if abs(diff) < tol:
            return sig_mid

        # mise à jour des bornes
        if diff > 0:
            sig_high = sig_mid
        else:
            sig_low = sig_mid

        # si bornes se touchent
        if sig_high - sig_low < tol:
            return sig_mid

    # ---- 4. pas de convergence -------------------------------
    return np.nan



