"""
converter.py
Core logic for fetching exchange rates (fiat + crypto) and converting amounts.

APIs used (both free, no API key required):
  - Frankfurter (https://www.frankfurter.app)  -> fiat-to-fiat rates
  - CoinGecko   (https://www.coingecko.com)    -> crypto prices

Results are cached locally in cache.json for CACHE_TTL_MINUTES to avoid
hammering the APIs and to allow basic offline reuse of recent rates.
"""

import json
import os
import time
from datetime import datetime, timezone

import requests

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache.json")
CACHE_TTL_MINUTES = 10

FIAT_API_URL = "https://api.frankfurter.app/latest"
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# A small lookup so users can type "BTC" instead of CoinGecko's id "bitcoin"
CRYPTO_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LTC": "litecoin",
    "AVAX": "avalanche-2",
}


class ConverterError(Exception):
    """Raised when a conversion can't be completed (bad code, network issue, etc.)."""
    pass


# --------------------------------------------------------------------------
# Cache helpers
# --------------------------------------------------------------------------

def _load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except OSError:
        pass  # caching is best-effort; never block a conversion on a write failure


def _cache_get(key: str):
    cache = _load_cache()
    entry = cache.get(key)
    if not entry:
        return None
    age_minutes = (time.time() - entry["timestamp"]) / 60
    if age_minutes > CACHE_TTL_MINUTES:
        return None
    return entry["value"]


def _cache_set(key: str, value) -> None:
    cache = _load_cache()
    cache[key] = {"value": value, "timestamp": time.time()}
    _save_cache(cache)


# --------------------------------------------------------------------------
# Rate fetchers
# --------------------------------------------------------------------------

def is_crypto(code: str) -> bool:
    return code.upper() in CRYPTO_ID_MAP


def get_fiat_rate(base: str, target: str) -> float:
    """Return how many `target` units equal 1 `base` unit."""
    base, target = base.upper(), target.upper()
    if base == target:
        return 1.0

    cache_key = f"fiat:{base}:{target}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            FIAT_API_URL, params={"from": base, "to": target}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"].get(target)
        if rate is None:
            raise ConverterError(f"Unsupported fiat currency code: {target}")
        _cache_set(cache_key, rate)
        return rate
    except requests.exceptions.RequestException as e:
        raise ConverterError(f"Network error fetching fiat rate: {e}") from e
    except KeyError as e:
        raise ConverterError(f"Unexpected API response format: {e}") from e


def get_crypto_price_usd(symbol: str) -> float:
    """Return the USD price of one unit of a crypto symbol, e.g. 'BTC'."""
    symbol = symbol.upper()
    coin_id = CRYPTO_ID_MAP.get(symbol)
    if not coin_id:
        raise ConverterError(
            f"Unknown crypto symbol '{symbol}'. Supported: {', '.join(CRYPTO_ID_MAP)}"
        )

    cache_key = f"crypto:{symbol}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            CRYPTO_API_URL,
            params={"ids": coin_id, "vs_currencies": "usd"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        price = data[coin_id]["usd"]
        _cache_set(cache_key, price)
        return price
    except requests.exceptions.RequestException as e:
        raise ConverterError(f"Network error fetching crypto price: {e}") from e
    except KeyError as e:
        raise ConverterError(f"Unexpected API response format: {e}") from e


# --------------------------------------------------------------------------
# Public conversion function
# --------------------------------------------------------------------------

def convert(amount: float, from_code: str, to_code: str) -> dict:
    """
    Convert `amount` from from_code to to_code.
    Handles four cases: fiat->fiat, crypto->fiat, fiat->crypto, crypto->crypto.
    Returns a dict with the result and metadata (useful for logging/history).
    """
    from_code, to_code = from_code.upper(), to_code.upper()
    from_is_crypto = is_crypto(from_code)
    to_is_crypto = is_crypto(to_code)

    if not from_is_crypto and not to_is_crypto:
        rate = get_fiat_rate(from_code, to_code)
        result = amount * rate

    elif from_is_crypto and not to_is_crypto:
        usd_price = get_crypto_price_usd(from_code)
        usd_amount = amount * usd_price
        rate = 1.0 if to_code == "USD" else get_fiat_rate("USD", to_code)
        result = usd_amount * rate

    elif not from_is_crypto and to_is_crypto:
        usd_amount = amount if from_code == "USD" else amount * get_fiat_rate(from_code, "USD")
        crypto_usd_price = get_crypto_price_usd(to_code)
        result = usd_amount / crypto_usd_price

    else:  # crypto -> crypto, via USD
        from_usd_price = get_crypto_price_usd(from_code)
        to_usd_price = get_crypto_price_usd(to_code)
        result = (amount * from_usd_price) / to_usd_price

    return {
        "amount": amount,
        "from": from_code,
        "to": to_code,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def supported_crypto_symbols() -> list:
    return sorted(CRYPTO_ID_MAP.keys())
