"""Domain enums for geofencing."""

from enum import StrEnum


class ZoneType(StrEnum):
    UNSAFE = "UNSAFE"
    RESTRICTED = "RESTRICTED"
    WARNING = "WARNING"


class GeometryType(StrEnum):
    CIRCLE = "CIRCLE"
    POLYGON = "POLYGON"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GeofenceEventType(StrEnum):
    ENTERED_UNSAFE_ZONE = "ENTERED_UNSAFE_ZONE"
    EXITED_UNSAFE_ZONE = "EXITED_UNSAFE_ZONE"
    ENTERED_RESTRICTED_ZONE = "ENTERED_RESTRICTED_ZONE"
    LEFT_RESTRICTED_ZONE = "LEFT_RESTRICTED_ZONE"
    ENTERED_WARNING_ZONE = "ENTERED_WARNING_ZONE"
    LEFT_WARNING_ZONE = "LEFT_WARNING_ZONE"


ZONE_TYPE_TO_ENTER_EVENT: dict[ZoneType, GeofenceEventType] = {
    ZoneType.UNSAFE: GeofenceEventType.ENTERED_UNSAFE_ZONE,
    ZoneType.RESTRICTED: GeofenceEventType.ENTERED_RESTRICTED_ZONE,
    ZoneType.WARNING: GeofenceEventType.ENTERED_WARNING_ZONE,
}

ZONE_TYPE_TO_EXIT_EVENT: dict[ZoneType, GeofenceEventType] = {
    ZoneType.UNSAFE: GeofenceEventType.EXITED_UNSAFE_ZONE,
    ZoneType.RESTRICTED: GeofenceEventType.LEFT_RESTRICTED_ZONE,
    ZoneType.WARNING: GeofenceEventType.LEFT_WARNING_ZONE,
}
