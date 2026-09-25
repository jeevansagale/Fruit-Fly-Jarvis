"""Structured stderr logging: LEVEL subsystem message. No conversation dumps."""
from __future__ import annotations

import sys

LEVELS = ("DEBUG", "INFO", "WARN", "ERROR")


def log(subsystem: str, level: str, message: str) -> None:
    if level not in LEVELS:
        raise ValueError(f"unknown level: {level!r}")
    print(f"{level} {subsystem} {message}", file=sys.stderr)
