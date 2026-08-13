"""Safety resource type definitions."""

from enum import StrEnum


class SafetyResourceType(StrEnum):
    PATROL = "PATROL"
    POLICE = "POLICE"
    HOSPITAL = "HOSPITAL"
