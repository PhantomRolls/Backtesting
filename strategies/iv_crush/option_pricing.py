import numpy as np
from scipy.stats import norm


def call(S, K, T, sigma, r=0.05):
    d1 = (np.log(S / K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(- r * T) * norm.cdf(d2)

def put(S, K, T, sigma, r=0.05):
    d1 = (np.log(S / K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(- r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def straddle(S, K, T, sigma, r=0.05):
    return call(S, K, T, sigma, r) + put(S, K, T, sigma, r)


