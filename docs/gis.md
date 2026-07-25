# GIS Geospatial Core (Stage 3)

An independent, extensible module (`backend/app/gis/`) providing **address search,
geocoding, reverse geocoding, address normalization, geographic storage and
PostGIS spatial queries**. It reuses the Stage-1/2 foundation (config, database,
ORM base, repository pattern) without changing it.

> **Out of scope by design:** dispatch logic, nearest-resource selection, route
> building, ETA, map rendering, AI. This stage only *prepares* the data and
> primitives the next stage (nearest-resource search) will consume.

## Module layout

```
backend/app/gis/
├── models.py            # Address, Coordinate, Region, District, Settlement,
│                        # Street, Building, GeocodingLog (UUID, PostGIS geom)
├── providers/           # GeoProvider interface + pluggable backends
│   ├── base.py          #   GeoProvider ABC + DTOs (GeocodeResult, ReverseResult…)
│   ├── http.py          #   shared httpx plumbing
│   ├── nominatim.py     #   default backend (OpenStreetMap)
│   ├── photon.py  pelias.py  arcgis.py
│   ├── fake.py          #   deterministic offline backend (dev/tests)
│   └── factory.py       #   create_provider(settings) — registry
├── cache/               # GeoCache interface (Redis-ready) + in-memory impl
├── services/            # normalization, geocoding (fwd/rev/validate), spatial
├── repositories/        # entity repos + SpatialRepository (PostGIS queries)
├── schemas/             # Pydantic Create/Update/Response + API request/response
├── utils/               # address abbreviation dictionaries + tokenizer
├── deps.py              # FastAPI dependency wiring
├── router.py            # aggregate GIS router
└── api/                 # geocoding.py, spatial.py endpoints
```

## Provider abstraction (`GeoProvider`)

All geocoding goes through the `GeoProvider` interface, so backends are swapped
purely via configuration (`GIS_PROVIDER`). Implemented backends:

| Provider | `GIS_PROVIDER` | Notes |
|----------|----------------|-------|
| Nominatim (OSM) | `nominatim` | **default**; public or self-hosted |
| Photon (Komoot) | `photon` | OSM-based, GeoJSON |
| Pelias | `pelias` | e.g. geocode.earth; API key optional |
| ArcGIS | `arcgis` | World GeocodeServer; token optional |
| Fake | `fake` | offline deterministic — dev & tests |

Google Maps and Yandex are **future** backends: add a class implementing
`GeoProvider` and register it in `providers/factory.py::PROVIDER_REGISTRY` — no
other code changes (Open/Closed).

Each backend maps its native response onto the shared DTOs
(`GeocodeResult`, `ReverseResult`, `AddressComponents`), so the services and API
see one consistent model. Results carry `formatted_address`,
`normalized_address`, `latitude`, `longitude`, `accuracy` and `source`.

## Address normalization

`NormalizationService` (pure, no I/O) canonicalizes free-form Russian addresses:

- expands abbreviations (`ул.`→`улица`, `пр-т`→`проспект`, `д.`→`дом`, `г.`→`город`, …);
- splits glued forms (`д.7`, `г.Москва`);
- lowercases, tidies punctuation/whitespace, places the house number after a comma.

It returns two forms:

- **`normalized`** — human canonical text (`улица ленина, 15`);
- **`canonical`** — an order-independent comparison key with type words removed,
  so `ул Ленина 15`, `улица Ленина,15` and `Ленина 15` all yield `15 ленина`
  (used for cache keys and de-duplication).

## Geocoding service

`GeocodingService` orchestrates provider + cache + normalization + logging:

- **`geocode(address)`** → normalizes, checks cache, calls the provider, caches
  and returns ranked candidates.
- **`reverse(lat, lon)`** → structured address (country, region, district,
  settlement, street, house number, formatted).
- **`validate(address)`** → is the address geocodable? returns the best match.

Every call is recorded in `gis_geocoding_logs` (time, provider, source,
response time, success, error, cache-hit) in its **own transaction**, so the log
survives regardless of the request outcome (requirement 11).

## Caching (Redis-ready)

`GeoCache` is an async key/value interface with TTL. The default
`InMemoryGeoCache` is process-local with TTL + size bound. A Redis backend can be
added behind the same interface (`GIS_CACHE_BACKEND=redis`, `GIS_REDIS_URL`) with
no changes to the services — Redis is intentionally **not** wired yet.

## Spatial operations (PostGIS)

`SpatialService` / `SpatialRepository` provide the required primitives, all using
PostGIS and casting to `geography` for metric distance:

| Operation | Function |
|-----------|----------|
| distance between two points | `ST_Distance` (geography) |
| objects within a radius | `ST_DWithin` (geography) |
| objects within a polygon | `ST_Within` (WKT polygon) |
| objects within an administrative area | `ST_Within` (Stage-2 boundary) |
| objects within a bounding box | `ST_MakeEnvelope` + `&&` + `ST_Within` |

These return **candidate sets** only — no ranking or selection (that is the next
stage).

## Geographic models

`Region → District → Settlement → Street → Building` form the geocoding gazetteer;
`Address` links raw/normalized text + structured components + a `Coordinate`.
`Region` may optionally reference the Stage-2 `administrative_areas` (dispatch
territory) via `administrative_area_id` — complementary, not duplicated. All use
UUID PKs, `Mapped`/`relationship`, PostGIS `Geometry(Point/Polygon, 4326)` with
GiST indexes, and the common `created_at`/`updated_at`/`is_deleted` columns.

## REST API

Mounted under `/api/v1`:

| Method & path | Purpose |
|---------------|---------|
| `GET /geocode?q=&limit=&language=&country_codes=` | address → coordinates |
| `GET /reverse-geocode?lat=&lon=&language=` | coordinates → address |
| `GET /coordinates?address=` | coordinates of the best match |
| `GET /validate-address?address=` | is the address geocodable |
| `GET /normalize-address?address=` | canonical form |
| `GET /spatial/distance` | distance between two points (m) |
| `GET /spatial/within-radius` | resources within a radius |
| `GET /spatial/within-bbox` | resources within a bounding box |
| `GET /spatial/within-polygon` | resources within a WKT polygon |
| `GET /spatial/within-area/{area_id}` | resources within an administrative area |

Full request/response schemas are in the OpenAPI docs at `/docs`.

## Configuration

GIS settings (see `.env.example`): `GIS_PROVIDER`, `GIS_HTTP_TIMEOUT`,
`GIS_USER_AGENT`, `GIS_DEFAULT_LANGUAGE`, `GIS_DEFAULT_COUNTRY_CODES`, provider
URLs/keys (`GIS_NOMINATIM_URL`, `GIS_PHOTON_URL`, `GIS_PELIAS_URL`,
`GIS_PELIAS_API_KEY`, `GIS_ARCGIS_URL`, `GIS_ARCGIS_TOKEN`), and caching
(`GIS_CACHE_BACKEND`, `GIS_CACHE_TTL_SECONDS`, `GIS_CACHE_MAX_ENTRIES`,
`GIS_REDIS_URL`).

## Testing

- **Unit** (hermetic, no network/DB): normalization, provider response mapping
  (mocked `httpx`), cache, geocoding service (fake provider + SQLite log).
- **Integration**: REST endpoints via ASGI (fake provider); PostGIS spatial
  tests run against a real database and **skip** automatically when none is
  reachable.

## Readiness for the next stage

The nearest-resource search stage can build directly on: `SpatialService`
(radius/bbox/polygon/area candidate sets), stored `Address`/`Coordinate`
records, resources' live `geom`, and the provider/cache abstractions — no
architectural change required.
