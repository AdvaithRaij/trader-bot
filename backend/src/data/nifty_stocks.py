"""
NIFTY 200 Stock Universe for Screening.
Contains F&O eligible stocks with market cap data.
"""

# NIFTY 50 stocks (highest liquidity)
NIFTY_50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN",
    "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "WIPRO", "ASIANPAINT",
    "MARUTI", "HCLTECH", "TATAMOTORS", "SUNPHARMA", "BAJFINANCE", "TITAN",
    "ULTRACEMCO", "NESTLEIND", "POWERGRID", "NTPC", "M&M", "TECHM", "TATASTEEL",
    "JSWSTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", "ONGC", "BPCL", "IOC",
    "GRASIM", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP", "EICHERMOT",
    "BAJAJFINSV", "BAJAJ-AUTO", "HEROMOTOCO", "TATACONSUM", "BRITANNIA",
    "SBILIFE", "HDFCLIFE", "INDUSINDBK", "HINDALCO", "UPL"
]

# NIFTY NEXT 50 stocks
# Updated for Yahoo Finance compatibility (Jan 2026)
NIFTY_NEXT_50 = [
    "SHREECEM", "VEDL", "DABUR", "PIDILITIND", "HAVELLS", "SIEMENS", "ABB",
    "GODREJCP", "COLPAL", "MARICO", "BERGEPAINT", "AMBUJACEM", "ACC", "DLF",
    "GODREJPROP", "CHOLAFIN", "MUTHOOTFIN", "BANDHANBNK", "FEDERALBNK",
    "IDFCFIRSTB", "TRENT", "JUBLFOOD", "INDIGO", "IRCTC", "LICI",
    "ADANIGREEN", "ADANIPOWER", "TATAPOWER", "NHPC", "PFC", "RECLTD", "CANBK",
    "BANKBARODA", "PNB", "SAIL", "NMDC", "GAIL", "PETRONET", "IGL", "MGL",
    "TORNTPHARM", "LUPIN", "BIOCON", "AUROPHARMA", "ALKEM", "IPCALAB",
    "LAURUSLABS", "SYNGENE", "GLENMARK"
]

# Additional F&O stocks (high liquidity)
# Updated symbols for Yahoo Finance compatibility (Jan 2026)
FNO_STOCKS = [
    "AARTIIND", "ABCAPITAL", "ABFRL", "ADANIENSOL", "ALKEM",
    "ASHOKLEY", "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA", "BALKRISIND",
    "BATAINDIA", "BEL", "BHEL", "BIOCON", "BOSCHLTD", "CANFINHOME", "CHAMBLFERT",
    "COFORGE", "CONCOR", "COROMANDEL", "CROMPTON", "CUB", "CUMMINSIND",
    "DEEPAKNTR", "DELTACORP", "DIXON", "ESCORTS", "EXIDEIND", "FSL",
    "GLENMARK", "GMRAIRPORT", "GNFC", "GRANULES", "GSPL", "HAL", "HDFCAMC",
    "HINDCOPPER", "HINDPETRO", "HONAUT", "ICICIPRULI", "IDEA",
    "IDFCFIRSTB", "INDUSTOWER", "INTELLECT", "JINDALSTEL", "JKCEMENT", "JSWENERGY",
    "KAJARIACER", "KPITTECH", "LTFH", "LALPATHLAB", "LICHSGFIN", "LTIM",
    "LTTS", "MANAPPURAM", "UNITDSPR", "MCX", "METROPOLIS", "MFSL", "MGL",
    "MOTHERSON", "MPHASIS", "MRF", "NATIONALUM", "NAUKRI",
    "NAVINFLUOR", "OBEROIRLTY", "OFSS", "PAGEIND", "PERSISTENT", "PETRONET",
    "PFIZER", "PIIND", "POLYCAB", "PVRINOX", "RAMCOCEM", "RBLBANK",
    "SBICARD", "SRF", "STAR", "SUNTV", "TATACHEM", "TATACOMM", "TATAELXSI",
    "TVSMOTOR", "UBL", "UNIONBANK", "VOLTAS", "WHIRLPOOL", "ZEEL", "ZYDUSLIFE"
]

# Complete NIFTY 200 universe
NIFTY_200 = list(set(NIFTY_50 + NIFTY_NEXT_50 + FNO_STOCKS))

# Market cap data (approximate, in Crores) - for filtering
# This should be updated periodically or fetched from API
MARKET_CAP_DATA = {
    "RELIANCE": 1850000, "TCS": 1450000, "HDFCBANK": 1200000, "INFY": 650000,
    "ICICIBANK": 750000, "HINDUNILVR": 580000, "SBIN": 650000, "BHARTIARTL": 750000,
    "ITC": 550000, "KOTAKBANK": 350000, "LT": 450000, "AXISBANK": 320000,
    "WIPRO": 250000, "ASIANPAINT": 280000, "MARUTI": 380000, "HCLTECH": 380000,
    "TATAMOTORS": 280000, "SUNPHARMA": 350000, "BAJFINANCE": 450000, "TITAN": 280000,
    "ULTRACEMCO": 280000, "NESTLEIND": 220000, "POWERGRID": 280000, "NTPC": 350000,
    "M&M": 280000, "TECHM": 150000, "TATASTEEL": 180000, "JSWSTEEL": 220000,
    "ADANIENT": 350000, "ADANIPORTS": 280000, "COALINDIA": 280000, "ONGC": 280000,
    "BPCL": 120000, "IOC": 180000, "GRASIM": 180000, "DRREDDY": 100000,
    "CIPLA": 100000, "DIVISLAB": 120000, "APOLLOHOSP": 85000, "EICHERMOT": 120000,
    "BAJAJFINSV": 280000, "BAJAJ-AUTO": 180000, "HEROMOTOCO": 85000,
    "TATACONSUM": 100000, "BRITANNIA": 120000, "SBILIFE": 150000, "HDFCLIFE": 150000,
    "INDUSINDBK": 85000, "HINDALCO": 120000, "UPL": 45000, "SHREECEM": 85000,
}

# Default market cap for stocks not in the list (assume large cap)
DEFAULT_MARKET_CAP = 10000  # 10,000 Cr

# Stock metadata (name and sector) - fetched from yfinance on first use
NIFTY_STOCKS_DATA = {}

def get_market_cap(symbol: str) -> float:
    """Get market cap for a symbol in Crores."""
    return MARKET_CAP_DATA.get(symbol, DEFAULT_MARKET_CAP)

def get_all_symbols() -> list:
    """Get all symbols in the NIFTY 200 universe."""
    return NIFTY_200.copy()

def get_nifty50_symbols() -> list:
    """Get NIFTY 50 symbols only."""
    return NIFTY_50.copy()

def get_fno_symbols() -> list:
    """Get all F&O eligible symbols."""
    return list(set(NIFTY_50 + NIFTY_NEXT_50 + FNO_STOCKS))

def get_stock_metadata(symbol: str) -> dict:
    """
    Get stock metadata (name, sector) from yfinance.
    Cached in NIFTY_STOCKS_DATA to avoid repeated API calls.
    """
    if symbol in NIFTY_STOCKS_DATA:
        return NIFTY_STOCKS_DATA[symbol]

    try:
        import yfinance as yf
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info

        metadata = {
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "Unknown")
        }
        NIFTY_STOCKS_DATA[symbol] = metadata
        return metadata
    except Exception:
        # Fallback to symbol as name
        metadata = {"name": symbol, "sector": "Unknown"}
        NIFTY_STOCKS_DATA[symbol] = metadata
        return metadata

