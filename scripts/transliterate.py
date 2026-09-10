#!/usr/bin/env python3
"""Transliteration entrypoint using Aksharamukha for Tamil->IAST.

Deterministic, audited script conversion. No LLM guessing.
"""
import argparse
import sys
from aksharamukha import transliterate


def transliterate_tamil_to_iast(text: str) -> str:
    """Convert Tamil text to IAST using Aksharamukha."""
    return transliterate.process('Tamil', 'IAST', text)


def main():
    ap = argparse.ArgumentParser(description='Transliterate Tamil to IAST')
    ap.add_argument('text', nargs='?', help='Tamil text to transliterate (or stdin)')
    ap.add_argument('--stdin', action='store_true', help='Read from stdin')
    args = ap.parse_args()

    if args.stdin or not args.text:
        text = sys.stdin.read().strip()
    else:
        text = args.text

    if not text:
        raise SystemExit("No input text provided")

    try:
        result = transliterate_tamil_to_iast(text)
        print(result)
    except Exception as e:
        raise SystemExit(f"Transliteration failed: {e}")


if __name__ == '__main__':
    main()