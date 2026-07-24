# PROTOCOL.md

# Reverse Engineering Notes – Urja Meter Ops Portal

**Author:** Avishkar Tambe

## Objective

The objective of this exercise was to understand how the legacy **Urja Meter Ops** web portal communicates with its backend and expose the same functionality through a clean REST API.

The investigation was performed using:

- Browser Developer Tools (Chrome)
- Network tab (HAR capture)
- JavaScript bundle inspection
- Browser Storage (Cookies)
- Direct endpoint testing using Python (httpx)

---

# Technology Stack Observed

| Component | Observation |
|-----------|-------------|
| Frontend | SvelteKit |
| Authentication | Better Auth |
| Session | Cookie-based Authentication |
| Data Format | JSON |
| Communication | HTTP REST endpoints |

---

# Authentication

## Login Endpoint

```
POST /login
```

### Request

Content-Type

```
application/x-www-form-urlencoded
```

Parameters

| Name | Description |
|------|-------------|
| email | Operator email |
| password | Operator password |

Example

```
email=operator@urja.local
password=urja-ops-2026
```

---

## Authentication Method

After a successful login the server issues an HTTP-only secure session cookie.

Cookie observed:

```
__Secure-better-auth.session_token
```

Characteristics

- HttpOnly
- Secure
- SameSite=Lax

The cookie is automatically stored by the HTTP client and reused for subsequent authenticated requests.

No Bearer Token or JWT is exposed to the client.

---

# Meter Search

Endpoint

```
GET /portal/meters/search
```

Query Parameters

| Parameter | Description |
|-----------|-------------|
| q | Search text |
| page | Page number |

Example

```
GET /portal/meters/search?q=&page=1
```

Observed Response

```json
{
  "data": [],
  "total": 403,
  "page": 1,
  "pageSize": 20
}
```

Each meter contains fields similar to:

```json
{
  "meterId": "J100000",
  "serialNo": "SE33962",
  "make": "HPL",
  "phaseType": "single",
  "installStatus": "Decommissioned",
  "dtCode": "DT-001"
}
```

Observations

- Search is server-side.
- Results are paginated.
- Default page size is **20**.
- Total meter count observed: **403**.

---

# Meter Details

Meter detail pages are rendered through SvelteKit page loaders.

Observed endpoint

```
/meters/{meterId}/__data.json
```

The page combines multiple backend requests to display complete meter information.

Information displayed includes:

- Meter Information
- Installation Details
- Hierarchy
- Geographic Coordinates
- Energy Consumption

---

# Geographic Coordinates

Endpoint

```
GET /portal/meters/{meterId}/geo
```

Returns

- Latitude
- Longitude

Used to display the installation location of the meter.

---

# Energy Consumption

Endpoint

```
GET /portal/meters/{meterId}/energy
```

Returns historical energy readings.

Observed fields include

- Timestamp
- KWH
- KVAH
- Voltage

---

# Distribution Transformers

Endpoint

```
GET /portal/dts
```

Supports pagination.

Returns transformer information used by the portal.

---

# Bulk Export

Endpoint

```
GET /portal/export
```

Purpose

Returns a richer dataset than the paginated search endpoint.

Observed fields include

- meterId
- serialNo
- make
- phaseType
- installStatus
- installType
- firmware build
- dtCode
- Zone
- Circle
- Division
- Subdivision
- Substation
- Feeder
- Distribution Transformer
- Latitude
- Longitude

This endpoint is useful for bulk processing and statistics.

---

# Internal Endpoint

Observed endpoint

```
GET /portal/keys
```

Purpose was not fully documented.

The endpoint appears to provide internal metadata used by the application.

It is **not exposed** through the public wrapper API.

---

# Frontend Observations

The application is built using **SvelteKit**.

During inspection of the compiled JavaScript bundles, the following behaviors were observed:

- Meter search requests are debounced (~250 ms).
- Pagination size is fixed at 20 records.
- Search requests call:

```
GET /portal/meters/search
```

instead of loading all data into the browser.

---

# Session Handling

The API wrapper maintains a persistent HTTP session using `httpx.AsyncClient`.

Workflow

```
Client

↓

POST /login

↓

Better Auth

↓

Session Cookie Stored

↓

Authenticated Requests

↓

Portal APIs
```

This avoids logging in before every request.

---

# Public Wrapper API Design

The wrapper exposes cleaner REST endpoints while hiding legacy implementation details.

Examples

```
GET /api/v1/meters
```

```
GET /api/v1/meters/{meterId}
```

```
GET /api/v1/meters/{meterId}/consumption
```

```
GET /api/v1/transformers
```

These endpoints internally communicate with the legacy portal and return normalized JSON responses.

---

# Reverse Engineering Process

The following techniques were used:

- Browser Network inspection
- HAR file analysis
- Browser Storage inspection
- Cookie analysis
- JavaScript bundle inspection
- Direct endpoint validation using Python httpx
- Verification of authenticated requests using persistent sessions

---

# Assumptions

The portal does not provide official API documentation.

All endpoint behavior documented above was inferred from observed network traffic and validated through authenticated requests where possible.

Undocumented internal implementation details were intentionally not assumed.

---

# Summary

Successfully identified:

- Authentication flow
- Better Auth session management
- Search endpoint
- Meter detail loading
- Geo endpoint
- Energy endpoint
- Transformer endpoint
- Export endpoint
- Internal metadata endpoint
- Pagination behavior
- Search behavior
- Session persistence strategy

These findings were used to implement a clean FastAPI wrapper without modifying the legacy application.
