"""Broadcast severity levels matching authority dashboard UI."""

from enum import StrEnum


class BroadcastSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    ADVISORY = "ADVISORY"
