import yfinance as yf

# Liste enrichie d'ETF incluant les proxys sans risque
etf_tickers = [

    # ▶️ Indices US
    "SPY", "VOO", "VTI", "IVV", "QQQ", "DIA", "IWM",

    # ▶️ Marchés internationaux
    "VEA", "IEFA", "ACWI", "VT", "VXUS",

    # ▶️ Pays émergents
    "EEM", "VWO", "IEMG", "EMXC",

    # ▶️ Obligations
    "BND", "AGG", "TLT", "LQD", "HYG", "IEF", "SHY", "SGOV", "BIL", "SHV",

    # ▶️ Secteurs US
    "XLK", "XLF", "XLV", "XLY", "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC",

    # ▶️ Matières premières
    "GLD", "SLV", "DBC", "USO", "DBA", "PPLT", "CPER",

    # ▶️ Immobilier
    "VNQ", "IYR", "SCHH", "REET",

    # ▶️ Stratégies / Facteurs
    "SPLV", "USMV", "MTUM", "QUAL", "VIG", "DVY", "RSP", "SPHD",

    # ▶️ Devise / hedging
    "UUP", "FXE", "FXF"
]


# Téléchargement des prix ajustés et des volumes
df = yf.download(etf_tickers, period="max", auto_adjust=False, group_by='ticker')


# Affichage sous forme MultiIndex (Ticker -> OHLC)
df.columns.names = ['Ticker', 'Price']

df.to_pickle('etf.pkl')
print(df.head())