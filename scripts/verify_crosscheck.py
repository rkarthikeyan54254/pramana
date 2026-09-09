#!/usr/bin/env python3
"""Mechanical helper only: compare two Unicode verse strings without deciding correctness."""
import argparse
import difflib
import unicodedata


def norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFC", s).split())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("primary")
    p.add_argument("secondary")
    args = p.parse_args()
    a, b = norm(args.primary), norm(args.secondary)
    print("MATCH" if a == b else "DIFF")
    if a != b:
        for line in difflib.ndiff([a], [b]):
            print(line)

if __name__ == "__main__":
    main()
