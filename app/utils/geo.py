"""Geospatial helpers."""

from __future__ import annotations

import math


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance between two WGS84 points in meters."""
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def interpolate_path(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    steps: int,
) -> list[tuple[float, float]]:
    if steps < 2:
        return [(start_lat, start_lng)]
    points: list[tuple[float, float]] = []
    for i in range(steps):
        t = i / (steps - 1)
        lat = start_lat + (end_lat - start_lat) * t
        lng = start_lng + (end_lng - start_lng) * t
        points.append((lat, lng))
    return points
