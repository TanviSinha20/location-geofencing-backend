# Location & Geofencing API — Frontend Integration Guide

Base URL: `http://localhost:8000/api/v1`

All successful responses use:

```json
{
  "success": true,
  "data": { },
  "message": "optional string"
}
```

Errors:

```json
{
  "success": false,
  "error": "Human-readable message",
  "detail": null
}
```

---

## Location APIs

### Update tourist location

- **Method:** `POST`
- **Route:** `/locations/{tourist_id}`

**Request**

```json
{
  "latitude": 26.5775,
  "longitude": 93.1711,
  "accuracy": 12.5,
  "speed": 1.4,
  "heading": 180,
  "recorded_at": "2026-08-13T00:00:00Z"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "location": {
      "tourist_id": "123",
      "latitude": 26.5775,
      "longitude": 93.1711,
      "accuracy": 12.5,
      "speed": 1.4,
      "heading": 180,
      "recorded_at": "2026-08-13T00:00:00Z",
      "last_updated": "2026-08-13T00:00:00Z",
      "is_current": true
    },
    "geofence_status": "ENTERING",
    "active_zones": ["unsafe_core_1"],
    "events": [
      {
        "type": "ENTERED_UNSAFE_ZONE",
        "userId": "123",
        "zoneId": "unsafe_core_1",
        "time": "2026-08-13T00:00:00Z",
        "severity": "HIGH",
        "message": "You have entered an unsafe area. Turn back immediately.",
        "latitude": 26.5775,
        "longitude": 93.1711
      }
    ],
    "nearby_safety": {
      "search_radius_km": 25,
      "patrol_units": [
        {
          "id": "patrol_kohora_1",
          "name": "Kaziranga Kohora Forest Patrol Unit",
          "resource_type": "PATROL",
          "latitude": 26.5835,
          "longitude": 93.1745,
          "distance_m": 712.5,
          "phone": "+91-3776-262001"
        }
      ],
      "police": [],
      "hospitals": []
    }
  },
  "message": "Location updated"
}
```

---

### Get live location (with nearby safety resources)

- **Method:** `GET`
- **Route:** `/locations/{tourist_id}/live?radius_km=25`

Returns current location, geofence status, and nearest **patrol units**, **police**, and **hospitals** within the search radius.

**Response `200`**

```json
{
  "success": true,
  "data": {
    "location": { "tourist_id": "123", "latitude": 26.5775, "longitude": 93.1711 },
    "geofence_status": "INSIDE",
    "active_zones": ["unsafe_core_1"],
    "events": [],
    "nearby_safety": {
      "search_radius_km": 25,
      "patrol_units": [],
      "police": [],
      "hospitals": []
    }
  }
}
```

**Errors:** `404` no location for tourist

---

### Get current location

- **Method:** `GET`
- **Route:** `/locations/{tourist_id}/current`

**Response `200`:** `data` = location object only (no nearby safety — use `/live` for full safety context)

**Errors:** `404` no location for tourist

---

## Safety Resource APIs

Pre-seeded for **Kaziranga National Park, Assam** with patrol units, police outposts, and hospitals.

### List all safety resources

- **Method:** `GET`
- **Route:** `/safety-resources?resource_type=PATROL&active_only=true`

`resource_type` values: `PATROL`, `POLICE`, `HOSPITAL`

### Find nearby safety resources

- **Method:** `GET`
- **Route:** `/safety-resources/nearby?latitude=26.5775&longitude=93.1711&radius_km=25`

**Response `200`**

```json
{
  "success": true,
  "data": {
    "search_radius_km": 25,
    "patrol_units": [
      {
        "id": "patrol_kohora_1",
        "name": "Kaziranga Kohora Forest Patrol Unit",
        "resource_type": "PATROL",
        "latitude": 26.5835,
        "longitude": 93.1745,
        "address": "Kohora Range, Kaziranga National Park, Assam",
        "phone": "+91-3776-262001",
        "distance_m": 712.5,
        "is_24x7": true
      }
    ],
    "police": [],
    "hospitals": []
  }
}
```

### Create / update / delete safety resource

- `POST /safety-resources`
- `GET /safety-resources/{resource_id}`
- `PATCH /safety-resources/{resource_id}`
- `DELETE /safety-resources/{resource_id}`

---

## Location APIs (continued)

### Update tourist location (original docs)

- **Method:** `POST`
- **Route:** `/locations/{tourist_id}`

**Request**

```json
{
  "latitude": 26.5775,
  "longitude": 93.1711,
  "accuracy": 12.5,
  "speed": 1.4,
  "heading": 180,
  "recorded_at": "2026-08-13T00:00:00Z"
}
```

**Response `200`** — includes `nearby_safety` (see above)

**Errors:** `422` validation, `500` server

---

### Get current location (legacy — location only)

- **Method:** `GET`
- **Route:** `/locations/{tourist_id}/current`

**Response `200`:** `data` = location object

**Errors:** `404` no location for tourist

---

### Get last known location

- **Method:** `GET`
- **Route:** `/locations/{tourist_id}/last`

**Response `200`:** latest location from history (even if not current)

**Errors:** `404`

---

### List all tourists (admin/testing)

- **Method:** `GET`
- **Route:** `/locations`

**Response `200`**

```json
{
  "success": true,
  "data": [
    {
      "tourist_id": "123",
      "latitude": 26.55,
      "longitude": 93.14,
      "recorded_at": "2026-08-13T00:00:00Z",
      "last_updated": "2026-08-13T00:00:00Z"
    }
  ]
}
```

---

### Simulate tourist movement

- **Method:** `POST`
- **Route:** `/locations/{tourist_id}/simulate`

**Request**

```json
{
  "start_latitude": 26.55,
  "start_longitude": 93.14,
  "end_latitude": 26.5775,
  "end_longitude": 93.1711,
  "steps": 5
}
```

**Response `200`:** array of location update results in `data.updates`

---

### Mock GPS update

- **Method:** `POST`
- **Route:** `/locations/{tourist_id}/mock`

**Request**

```json
{
  "latitude": 26.5775,
  "longitude": 93.1711,
  "label": "unsafe_entry"
}
```

---

### Reset test data

- **Method:** `POST`
- **Route:** `/locations/test/reset`

Clears all location history, zone states, and geofence events.

---

## Geofence APIs

### List zones

- **Method:** `GET`
- **Route:** `/geofences?active_only=true`

**Response `200`:** array of zones

```json
{
  "id": "unsafe_core_1",
  "name": "Kaziranga Core Restricted Habitat",
  "zone_type": "UNSAFE",
  "geometry_type": "CIRCLE",
  "severity": "HIGH",
  "description": "...",
  "warning_message": "...",
  "is_active": true,
  "center_lat": 26.5775,
  "center_lng": 93.1711,
  "radius_m": 800,
  "polygon_coordinates": null
}
```

For polygon zones, `polygon_coordinates` follows GeoJSON: `[[[lng, lat], ...]]`.

---

### Create zone

- **Method:** `POST`
- **Route:** `/geofences`

**Circle example**

```json
{
  "id": "unsafe_1",
  "name": "Unsafe Area",
  "zone_type": "UNSAFE",
  "geometry_type": "CIRCLE",
  "severity": "HIGH",
  "description": "Wildlife habitat",
  "warning_message": "You have entered an unsafe area.",
  "circle": {
    "center_lat": 26.5775,
    "center_lng": 93.1711,
    "radius_m": 800
  }
}
```

**Polygon example**

```json
{
  "id": "warning_1",
  "name": "Flood Plain",
  "zone_type": "WARNING",
  "geometry_type": "POLYGON",
  "severity": "LOW",
  "warning_message": "Warning: flood-prone area.",
  "polygon": {
    "coordinates": [
      [
        [93.16, 26.57],
        [93.17, 26.57],
        [93.17, 26.56],
        [93.16, 26.56],
        [93.16, 26.57]
      ]
    ]
  }
}
```

**Errors:** `422` validation, `400` duplicate zone id

---

### Get / Update / Delete zone

- `GET /geofences/{zone_id}`
- `PATCH /geofences/{zone_id}`
- `DELETE /geofences/{zone_id}` → `204`

---

### List geofence events

- **Method:** `GET`
- **Route:** `/geofences/events/list?tourist_id=123&limit=50`

---

### Check point (testing)

- **Method:** `POST`
- **Route:** `/geofences/check/{tourist_id}`

Runs geofence detection and persists enter/exit state/events.

---

## Geofence status values

| Status | Meaning |
|---|---|
| `OUTSIDE` | Not in any zone |
| `ENTERING` | Just entered one or more zones |
| `INSIDE` | Remains inside same zone(s) |
| `LEAVING` | Exited all zones |
| `TRANSITION` | Simultaneous enter and exit |

---

## Event types

| Event | When |
|---|---|
| `ENTERED_UNSAFE_ZONE` | Tourist enters unsafe zone |
| `EXITED_UNSAFE_ZONE` | Tourist leaves unsafe zone |
| `ENTERED_RESTRICTED_ZONE` | Enters restricted zone |
| `LEFT_RESTRICTED_ZONE` | Leaves restricted zone |
| `ENTERED_WARNING_ZONE` | Enters warning zone |
| `LEFT_WARNING_ZONE` | Leaves warning zone |

---

## Test coordinates

- **Method:** `GET`
- **Route:** `/api/v1/test-coordinates`

Returns seeded safe, unsafe, restricted, warning, boundary, and approach coordinates for Kaziranga demo.

---

## Map integration notes (for Sneha)

1. Poll `GET /locations/{tourist_id}/current` or use location update response for marker position.
2. Fetch `GET /geofences?active_only=true` to render zone overlays.
3. Use `events` array from location updates to show geofence warnings in UI.
4. Circle zones: use `center_lat`, `center_lng`, `radius_m`.
5. Polygon zones: use `polygon_coordinates` (GeoJSON order: lng, lat).

---

## SOS integration notes (for Shreya)

Before creating an SOS incident, call:

`GET /locations/{tourist_id}/current`

Use returned `latitude`, `longitude`, and `recorded_at` as the incident location snapshot.

---

## Geofenced Emergency Broadcast Centre (Authority Dashboard)

Matches the authority UI: target zone dropdown, **geofence radius slider**, severity toggle, title, and message.

### Get radius slider config

- **Method:** `GET`
- **Route:** `/broadcast/radius-config?zone_id=hp_solang_rohtang`

**Response**

```json
{
  "success": true,
  "data": {
    "min_km": 1,
    "max_km": 50,
    "default_km": 14,
    "step_km": 1
  }
}
```

Use `default_km` when user selects a target zone. Re-fetch when zone changes.

---

### List target zones (dropdown)

- **Method:** `GET`
- **Route:** `/broadcast/target-zones`

**Response**

```json
{
  "success": true,
  "data": [
    {
      "id": "hp_solang_rohtang",
      "name": "Himachal Pradesh (Solang / Rohtang)",
      "state": "Himachal Pradesh",
      "center_lat": 32.3167,
      "center_lng": 77.1333,
      "default_radius_km": 14
    }
  ]
}
```

---

### Preview affected tourists (on radius slider change)

- **Method:** `POST`
- **Route:** `/broadcast/preview`

Call this whenever the user moves the **Geofence Radius (km)** slider.

**Request**

```json
{
  "zone_id": "hp_solang_rohtang",
  "radius_km": 14
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "zone_id": "hp_solang_rohtang",
    "zone_name": "Himachal Pradesh (Solang / Rohtang)",
    "state": "Himachal Pradesh",
    "radius_km": 14,
    "center_lat": 32.3167,
    "center_lng": 77.1333,
    "tourist_count": 2,
    "affected_tourists": [
      {
        "tourist_id": "tourist_hp_1",
        "latitude": 32.32,
        "longitude": 77.14,
        "distance_km": 0.85,
        "recorded_at": "2026-08-13T05:00:00Z"
      }
    ]
  },
  "message": "2 tourist(s) within 14 km"
}
```

---

### Send emergency broadcast

- **Method:** `POST`
- **Route:** `/broadcast/send`

**Request** (matches authority form fields)

```json
{
  "zone_id": "hp_solang_rohtang",
  "radius_km": 14,
  "severity": "CRITICAL",
  "title": "⚠️ Flash Flood & Sudden Cloudburst Warning",
  "message": "Heavy rainfall alert active in Solang Valley. Avoid unmapped riverbanks and move to higher ground immediately."
}
```

`severity` values: `CRITICAL`, `WARNING`, `ADVISORY`

**Response**

```json
{
  "success": true,
  "data": {
    "broadcast_id": 1,
    "zone_id": "hp_solang_rohtang",
    "zone_name": "Himachal Pradesh (Solang / Rohtang)",
    "state": "Himachal Pradesh",
    "radius_km": 14,
    "severity": "CRITICAL",
    "title": "⚠️ Flash Flood & Sudden Cloudburst Warning",
    "message": "Heavy rainfall alert active...",
    "tourists_notified": 2,
    "deliveries": [],
    "sent_at": "2026-08-13T05:00:00Z"
  }
}
```

---

### User-configurable radius on live location

Tourist-side nearby safety search also respects user radius:

- **Body field:** `safety_radius_km` on `POST /locations/{tourist_id}`
- **Query param:** `radius_km` on `GET /locations/{tourist_id}/live`
- **Query param:** `radius_km` on `GET /safety-resources/nearby`

```json
{
  "latitude": 26.5775,
  "longitude": 93.1711,
  "safety_radius_km": 14
}
```
