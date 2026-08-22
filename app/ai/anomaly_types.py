"""Enums for AI Anomaly Detection and Safety Scoring."""

from enum import StrEnum


class AnomalyType(StrEnum):
    INACTIVITY = "INACTIVITY"
    ROUTE_DEVIATION = "ROUTE_DEVIATION"
    SIGNAL_LOSS = "SIGNAL_LOSS"
    RESTRICTED_ZONE_ENTRY = "RESTRICTED_ZONE_ENTRY"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
