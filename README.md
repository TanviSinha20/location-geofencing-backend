# Location + Geofencing Backend API

Backend module for **Tanvi — Location + Geofencing + Backend Coordination** (SIH P0).

## Quick start

```bash
cd location/backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open Swagger UI: http://localhost:8000/docs

## Project structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── seed.py                 # Demo zones + test coordinates
│   ├── config/settings.py
│   ├── database/               # SQLAlchemy setup
│   ├── models/                 # location, geofence, events
│   ├── schemas/                # Pydantic request/response
│   ├── api/routes/             # location.py, geofence.py
│   ├── services/               # business logic
│   ├── geofence/engine.py      # point-in-zone detection
│   └── utils/geo.py            # haversine, path interpolation
├── tests/
├── docs/API.md                 # Frontend integration guide
└── requirements.txt
```

## Features implemented

- Tourist location update, current, last known, list all
- Mock GPS + movement simulation + test reset
- Circular and polygon geofences (unsafe, restricted, warning)
- Enter/exit event generation (`ENTERED_UNSAFE_ZONE`, etc.)
- Kaziranga demo seed zones and test coordinates

## Team integration

This module is designed to merge into the shared team backend:

| Owner | Files |
|---|---|
| **Tanvi** | `api/routes/location.py`, `geofence.py`, `services/location_service.py`, `geofence_service.py`, `schemas/location.py`, `geofence.py` |
| **Anish** | `models/location.py`, `models/geofence.py`, database setup |
| **Shreya** | Alert/incident APIs consume geofence events |

## Run tests

```bash
cd location/backend
pytest -v
```
