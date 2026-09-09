#!/usr/bin/env python3
"""Transliteration entrypoint. Tamil is deliberately not guessed by an LLM.
Wire this to an audited Tamil->IAST tool before marking transliteration complete.
"""
import argparse

p = argparse.ArgumentParser()
p.add_argument("text")
args = p.parse_args()
raise SystemExit("Tamil transliteration backend not yet pinned/audited; refusing to guess diacritics.")
