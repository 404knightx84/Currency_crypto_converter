# Currency / Crypto Converter

## Project Description

This is a Python command-line application that converts amounts between
fiat currencies (USD, EUR, INR, etc.) and cryptocurrencies (BTC, ETH, SOL, etc.)
using real-time exchange rate data pulled from public APIs, rather than
hardcoded or outdated rates.

The project was built to explore practical API integration: making HTTP
requests, parsing JSON responses, handling network failures gracefully, and
reducing redundant API calls through local caching. It supports four
conversion directions — fiat→fiat, fiat→crypto, crypto→fiat, and
crypto→crypto — by routing every conversion through USD as a common
intermediary when a direct rate isn't available.

Beyond the core conversion logic, the project includes a lightweight
persistence layer (conversion history saved to a local JSON file) and a
caching layer (recent rates stored for 10 minutes) to keep the tool fast and
considerate of free-tier API rate limits. It runs either as a single
one-line command or as a guided interactive session.

**Tech used:** Python 3, the `requests` library, JSON-based file storage,
and two free public APIs — [Frankfurter](https://www.frankfurter.app/) for
fiat exchange rates and [CoinGecko](https://www.coingecko.com/en/api) for
cryptocurrency prices.

**What it demonstrates:**
- Consuming and combining data from multiple third-party REST APIs
- Designing a small multi-module codebase (separation between API logic,
  persistence, and the CLI interface)
- Defensive error handling for real-world failure cases (bad currency codes,
  network errors, malformed responses)
- Basic caching strategy to reduce API load and improve response time

## Features

- Convert fiat ↔ fiat, crypto ↔ fiat, and crypto ↔ crypto
- Local caching (10 min TTL) so repeated lookups don't hit the API every time
- Conversion history saved to `history.json`
- Works as a one-shot CLI command or an interactive prompt

## Setup

```bash
pip install -r requirements.txt
```

## Usage

**Interactive mode:**
```bash
python main.py
```

**One-shot conversion:**
```bash
python main.py 100 USD EUR
python main.py 0.5 BTC USD
python main.py 250 INR ETH
```

**View recent conversions:**
```bash
python main.py --history
```

**List supported crypto symbols:**
```bash
python main.py --coins
```

**Clear history:**
```bash
python main.py --clear-history
```

## Supported currencies

- **Fiat:** any standard 3-letter ISO code (USD, EUR, GBP, INR, JPY, etc.) —
  these are passed straight through to Frankfurter, which supports most major currencies.
- **Crypto:** BTC, ETH, USDT, BNB, SOL, XRP, ADA, DOGE, DOT, MATIC, LTC, AVAX
  (easy to extend — just add entries to `CRYPTO_ID_MAP` in `converter.py`
  using the symbol and its [CoinGecko id](https://api.coingecko.com/api/v3/coins/list))

## File structure

```
currency_converter/
├── main.py          # CLI entry point
├── converter.py     # API calls, caching, conversion logic
├── history.py       # Conversion history logging
├── requirements.txt
├── cache.json       # auto-created — cached rates
└── history.json     # auto-created — past conversions
```

## Notes

- `cache.json` and `history.json` are created automatically on first run.
- If a request fails (no internet, bad currency code), you'll get a clear
  error message instead of a crash.
- Frankfurter doesn't require an API key and has no rate limit issues for
  casual use; CoinGecko's free tier has a generous rate limit (~10-30 calls/min)
  which the caching layer helps you stay under.
