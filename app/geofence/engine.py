"""Geofence detection engine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

from app.geofence.zone_types import GeometryType, ZoneType

if TYPE_CHECKING:
    from app.models.geofence import GeoFence


EARTH_RADIUS_METERS = 6_371_000.0


@dataclass(frozen=True)
class ZoneMatch:
    zone_id: str
    zone_name: str
    zone_type: ZoneType
    severity: str
    warning_message: str


def _circle_to_polygon(lat: float, lng: float, radius_m: float, segments: int = 64) -> BaseGeometry:
    """Approximate a geodesic circle as a local planar buffer."""
    # Local equirectangular projection for small radii (adequate for P0 geofences).
    lat_rad = lat * 3.141592653589793 / 180.0
    dx = radius_m / (EARTH_RADIUS_METERS * max(abs(__import__("math").cos(lat_rad)), 1e-6))
    dy = radius_m / EARTH_RADIUS_METERS
    center_x = lng
    center_y = lat
    point = Point(center_x, center_y)
    buffer_x = radius_m / (EARTH_RADIUS_METERS * max(abs(__import__("math").cos(lat_rad)), 1e-6)) * (180.0 / 3.141592653589793)
    buffer_y = radius_m / EARTH_RADIUS_METERS * (180.0 / 3.141592653589793)
    return point.buffer(max(buffer_x, buffer_y))


def zone_to_geometry(zone: GeoFence) -> BaseGeometry:
    geometry_type = GeometryType(zone.geometry_type)
    if geometry_type == GeometryType.CIRCLE:
        if zone.center_lat is None or zone.center_lng is None or zone.radius_m is None:
            raise ValueError(f"Circle zone {zone.id} missing center or radius")
        return _circle_to_polygon(zone.center_lat, zone.center_lng, zone.radius_m)

    if not zone.polygon_coordinates:
        raise ValueError(f"Polygon zone {zone.id} missing coordinates")

    coordinates = json.loads(zone.polygon_coordinates)
    geojson = {"type": "Polygon", "coordinates": coordinates}
    return shape(geojson)


def point_in_zone(lat: float, lng: float, zone: GeoFence) -> bool:
    geometry = zone_to_geometry(zone)
    return geometry.contains(Point(lng, lat))


def evaluate_point(lat: float, lng: float, zones: list[GeoFence]) -> list[ZoneMatch]:
    matches: list[ZoneMatch] = []
    for zone in zones:
        if not zone.is_active:
            continue
        try:
            if point_in_zone(lat, lng, zone):
                matches.append(
                    ZoneMatch(
                        zone_id=zone.id,
                        zone_name=zone.name,
                        zone_type=ZoneType(zone.zone_type),
                        severity=zone.severity,
                        warning_message=zone.warning_message,
                    )
                )
        except ValueError:
            continue
    return matches


def split_transitions(
    previous_zone_ids: set[str],
    current_matches: list[ZoneMatch],
) -> tuple[list[ZoneMatch], set[str]]:
    """Return newly entered zone matches and zone ids that were exited."""
    entered = [match for match in current_matches if match.zone_id not in previous_zone_ids]
    current_ids = {match.zone_id for match in current_matches}
    exited_ids = previous_zone_ids - current_ids
    return entered, exited_ids
