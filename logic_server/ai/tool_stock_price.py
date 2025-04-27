import requests
import os
from dotenv import load_dotenv

load_dotenv()

SYMBOL_MAP = {
    "apple": "AAPL", "aapl": "AAPL",
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "googl": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "facebook": "META", "meta platforms": "META",
    "tesla": "TSLA", "tsla": "TSLA",
    "nvidia": "NVDA", "nvda": "NVDA",
    "netflix": "NFLX", "nflx": "NFLX",
    "intel": "INTC", "intc": "INTC",
    "amd": "AMD", "advanced micro devices": "AMD",
    "adobe": "ADBE", "adbe": "ADBE",
    "paypal": "PYPL", "pypl": "PYPL",
    "cisco": "CSCO", "csco": "CSCO",
    "oracle": "ORCL", "orcl": "ORCL",
    "ibm": "IBM",
    "jpmorgan": "JPM", "jpm": "JPM",
    "goldman sachs": "GS", "gs": "GS",
    "bank of america": "BAC", "bac": "BAC",
    "wells fargo": "WFC", "wfc": "WFC",
    "citigroup": "C", "c": "C",
    "morgan stanley": "MS", "ms": "MS",
    "walmart": "WMT", "wmt": "WMT",
    "target": "TGT", "tgt": "TGT",
    "costco": "COST", "cost": "COST",
    "home depot": "HD", "hd": "HD",
    "lowe's": "LOW", "low": "LOW",
    "starbucks": "SBUX", "sbux": "SBUX",
    "mcdonald's": "MCD", "mcd": "MCD",
    "nike": "NKE", "nke": "NKE",
    "coca cola": "KO", "ko": "KO",
    "pepsico": "PEP", "pep": "PEP",
    "exxon": "XOM", "xom": "XOM",
    "chevron": "CVX", "cvx": "CVX",
    "boeing": "BA", "ba": "BA",
    "ford": "F", "f": "F",
    "gm": "GM", "general motors": "GM",
    "caterpillar": "CAT", "cat": "CAT",
    "johnson & johnson": "JNJ", "jnj": "JNJ",
    "pfizer": "PFE", "pfe": "PFE",
    "merck": "MRK", "mrk": "MRK",
    "abbvie": "ABBV", "abbv": "ABBV",
    "unitedhealth": "UNH", "unh": "UNH",
    "comcast": "CMCSA", "cmcsa": "CMCSA",
    "disney": "DIS", "dis": "DIS",
    "verizon": "VZ", "vz": "VZ",
    "at&t": "T", "t": "T",
    "spy": "SPY", "qqq": "QQQ", "vti": "VTI", "voo": "VOO", "iwm": "IWM", "dia": "DIA", "arkk": "ARKK",
    "toyota": "TM", "tm": "TM",
    "samsung": "005930.KS",
    "alibaba": "BABA", "baba": "BABA",
    "sony": "SONY",
    "shopify": "SHOP", "shop": "SHOP",
    "bitcoin": "BINANCE:BTCUSDT", "btc": "BINANCE:BTCUSDT",
    "ethereum": "BINANCE:ETHUSDT", "eth": "BINANCE:ETHUSDT",
    "solana": "BINANCE:SOLUSDT", "sol": "BINANCE:SOLUSDT",
    "dogecoin": "BINANCE:DOGEUSDT", "doge": "BINANCE:DOGEUSDT",
    "cardano": "BINANCE:ADAUSDT", "ada": "BINANCE:ADAUSDT",
    "binance coin": "BINANCE:BNBUSDT", "bnb": "BINANCE:BNBUSDT",
    "ripple": "BINANCE:XRPUSDT", "xrp": "BINANCE:XRPUSDT",
    "polkadot": "BINANCE:DOTUSDT", "dot": "BINANCE:DOTUSDT",
    "litecoin": "BINANCE:LTCUSDT", "ltc": "BINANCE:LTCUSDT",
    "tron": "BINANCE:TRXUSDT", "trx": "BINANCE:TRXUSDT",
    "avalanche": "BINANCE:AVAXUSDT", "avax": "BINANCE:AVAXUSDT",
    "chainlink": "BINANCE:LINKUSDT", "link": "BINANCE:LINKUSDT",
    "stellar": "BINANCE:XLMUSDT", "xlm": "BINANCE:XLMUSDT",
    "filecoin": "BINANCE:FILUSDT", "fil": "BINANCE:FILUSDT",
    "uniswap": "BINANCE:UNIUSDT", "uni": "BINANCE:UNIUSDT",
    "aptos": "BINANCE:APTUSDT", "apt": "BINANCE:APTUSDT",
    "arbitrum": "BINANCE:ARBUSDT", "arb": "BINANCE:ARBUSDT",
    "vechain": "BINANCE:VETUSDT", "vet": "BINANCE:VETUSDT",
    "the sandbox": "BINANCE:SANDUSDT", "sand": "BINANCE:SANDUSDT",
    "axie infinity": "BINANCE:AXSUSDT", "axs": "BINANCE:AXSUSDT",
}

def resolve_symbol(query: str) -> str:
    q = query.strip().lower()
    return SYMBOL_MAP.get(q, query.upper().strip())

def get_stock_price(query: str) -> dict:
    """
    Gets the latest price for a stock or cryptocurrency using the Finnhub API.
    Args:
        query: The company name, crypto, or symbol to look up (e.g., 'Tesla', 'BTC', 'AAPL').
    Returns:
        A dictionary with the formatted price information or error message.
    """
    finnhub_api_key = os.getenv("FINNHUB_API_KEY")
    if not finnhub_api_key:
        return {"result": "API key for Finnhub is not set. Please set FINNHUB_API_KEY in your environment."}
    symbol = resolve_symbol(query)
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_api_key}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {"result": f"Finnhub error: {resp.text}"}
        data = resp.json()
        if not data or data.get("c", 0) == 0:
            return {"result": f"No price data found for '{query}' (symbol: {symbol})"}
        return {
            "result": f"{symbol} price: ${data['c']:.2f} (open: ${data['o']:.2f}, high: ${data['h']:.2f}, low: ${data['l']:.2f}, prev close: ${data['pc']:.2f})"
        }
    except Exception as e:
        return {"result": f"Failed to fetch price: {e}"}
