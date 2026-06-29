#!/usr/bin/env python3
"""
main.py
Command-line interface for the currency/crypto converter.

Usage:
    python main.py                      Interactive mode
    python main.py 100 USD EUR          One-shot conversion
    python main.py --history            Show recent conversions
    python main.py --coins              List supported crypto symbols
    python main.py --clear-history      Wipe local conversion history
"""

import sys

from converter import convert, ConverterError, supported_crypto_symbols
from history import log_conversion, get_recent, clear_history


def print_result(record: dict) -> None:
    amt, frm, to, result = record["amount"], record["from"], record["to"], record["result"]
    # Crypto amounts deserve more decimal places than fiat
    decimals = 8 if result < 1 else 4
    print(f"\n{amt:,.2f} {frm} = {result:,.{decimals}f} {to}\n")


def run_conversion(amount: float, from_code: str, to_code: str) -> None:
    try:
        record = convert(amount, from_code, to_code)
        print_result(record)
        log_conversion(record)
    except ConverterError as e:
        print(f"\nError: {e}\n")


def show_history() -> None:
    recent = get_recent(10)
    if not recent:
        print("\nNo conversion history yet.\n")
        return
    print("\nRecent conversions:")
    for r in recent:
        print(f"  {r['timestamp'][:19]}  {r['amount']:,.2f} {r['from']} -> {r['result']:,.4f} {r['to']}")
    print()


def show_coins() -> None:
    print("\nSupported crypto symbols:")
    print(", ".join(supported_crypto_symbols()))
    print("\n(Any standard 3-letter fiat code like USD, EUR, GBP, INR, JPY also works.)\n")


def interactive_mode() -> None:
    print("=== Currency / Crypto Converter ===")
    print("Type 'q' at any prompt to quit, or '--coins' to see supported crypto symbols.\n")
    while True:
        amt_in = input("Amount (or command): ").strip()
        if amt_in.lower() in ("q", "quit", "exit"):
            break
        if amt_in == "--coins":
            show_coins()
            continue
        if amt_in == "--history":
            show_history()
            continue
        try:
            amount = float(amt_in)
        except ValueError:
            print("Please enter a numeric amount.\n")
            continue

        from_code = input("From currency (e.g. USD, BTC): ").strip()
        to_code = input("To currency (e.g. EUR, ETH): ").strip()
        run_conversion(amount, from_code, to_code)


def main() -> None:
    args = sys.argv[1:]

    if not args:
        interactive_mode()
        return

    if args[0] == "--history":
        show_history()
        return

    if args[0] == "--coins":
        show_coins()
        return

    if args[0] == "--clear-history":
        clear_history()
        print("\nHistory cleared.\n")
        return

    if len(args) == 3:
        try:
            amount = float(args[0])
        except ValueError:
            print("Amount must be a number, e.g.: python main.py 100 USD EUR")
            return
        run_conversion(amount, args[1], args[2])
        return

    print(__doc__)


if __name__ == "__main__":
    main()
