# Flock Energy Assignment – Urja Meter Ops API Wrapper

## Overview

This project is a **FastAPI-based REST API wrapper** for the legacy **Urja Meter Ops** web portal.

The original portal does not expose a public API. The objective of this assignment was to reverse engineer the application's communication with its backend and expose the same functionality through a clean, developer-friendly REST API.

The implementation maintains an authenticated session with the portal, communicates with its internal endpoints, and returns normalized JSON responses suitable for third-party applications.

---

## Features

- Reverse engineered authentication flow
- Better Auth session management
- Persistent HTTP session using `httpx.AsyncClient`
- Search meters
- Retrieve meter geographic coordinates
- Retrieve energy consumption history
- Retrieve distribution transformer information
- Export complete meter dataset
- Automatic session reuse
- OpenAPI (Swagger) documentation
- Modular FastAPI architecture

---

## Project Structure

```text
flock-energy-api/
│
├── app/
│   ├── client.py          # Legacy portal client
│   ├── config.py          # Environment configuration
│   ├── main.py            # FastAPI application
│   ├── services.py        # Business logic
│   ├── routes/
│   │   ├── meters.py
│   │   └── transformers.py
│   └── models.py
│
├── tests/
├── README.md
├── PROTOCOL.md
├── openapi.json
├── requirements.txt
└── .env
```

---

# Technology Stack

| Component | Technology |
|----------|------------|
| Language | Python 3.13 |
| Framework | FastAPI |
| HTTP Client | httpx |
| Configuration | python-dotenv |
| API Documentation | OpenAPI / Swagger |
| Authentication | Better Auth (Cookie-based) |

---

# Reverse Engineering Process

The following techniques were used to understand the legacy portal:

- Chrome Developer Tools
- HAR (HTTP Archive) analysis
- Browser Network inspection
- JavaScript bundle inspection
- Browser Storage (Cookies)
- Direct endpoint validation using Python

The reverse engineering findings are documented in **PROTOCOL.md**.

---

# Authentication

The portal uses **Better Auth** with secure cookie-based authentication.

Workflow

```
Client
    │
    ▼
POST /login
    │
    ▼
Better Auth
    │
    ▼
Session Cookie
(__Secure-better-auth.session_token)
    │
    ▼
Authenticated Requests
```

The HTTP client automatically stores and reuses the session cookie.

---

# API Endpoints

## List Meters

```
GET /api/v1/meters
```

Query Parameters

| Parameter | Description |
|----------|-------------|
| q | Search text |
| page | Page number |

---

## Meter Details

```
GET /api/v1/meters/{meterId}
```

Returns

- Meter Information
- Geographic Coordinates
- Installation Details

---

## Energy Consumption

```
GET /api/v1/meters/{meterId}/consumption
```

Returns historical meter readings.

---

## Transformers

```
GET /api/v1/transformers
```

Returns distribution transformer information.

---

## Export

```
GET /api/v1/export
```

Returns the complete meter dataset.

---

# Installation

Clone the repository

```bash
git clone <repository-url>
cd flock-energy-api
```

Create virtual environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file

```env
BASE_URL=https://urja-ops.flockenergy.tech

EMAIL=operator@urja.local
PASSWORD=urja-ops-2026

REQUEST_TIMEOUT=30
VERIFY_SSL=True
```

---

# Running the Application

Start the development server

```bash
uvicorn app.main:app --reload
```

Application

```
http://127.0.0.1:8000
```

Swagger UI

```
http://127.0.0.1:8000/docs
```

OpenAPI Specification

```
http://127.0.0.1:8000/openapi.json
```

---

# Testing

Run

```bash
python test_client.py
```

Successful output

```
Login successful

Search successful

Total meters: 403

Meters returned: 20
```

---

# Architecture

```
                FastAPI

                   │

                   ▼

            Service Layer

                   │

                   ▼

             UrjaClient

                   │

                   ▼

     Better Auth Authentication

                   │

                   ▼

      Legacy Urja Meter Ops Portal
```

---

# Reverse Engineered Endpoints

| Endpoint | Purpose |
|----------|----------|
| POST /login | Authentication |
| GET /portal/meters/search | Meter Search |
| GET /portal/meters/{id}/geo | Geographic Coordinates |
| GET /portal/meters/{id}/energy | Energy Consumption |
| GET /portal/dts | Distribution Transformers |
| GET /portal/export | Export Dataset |
| GET /portal/keys | Internal Metadata |

---

# Design Decisions

- Encapsulated portal communication inside `UrjaClient`
- Used persistent sessions to avoid repeated authentication
- Separated HTTP communication from business logic
- Exposed clean REST endpoints instead of directly proxying the legacy API
- Leveraged FastAPI's automatic OpenAPI generation

---

# Limitations

- The legacy portal does not provide official API documentation.
- Endpoint behavior was inferred from observed network traffic.
- Authentication depends on the availability of the upstream portal.

---

# Future Improvements

- Response caching
- Retry mechanism for transient failures
- Background synchronization
- Statistics endpoint
- Hierarchy endpoint
- Rate limiting
- Unit and integration tests
- Docker support

---

# Documentation

- **README.md** — Project overview and setup
- **PROTOCOL.md** — Reverse engineering findings
- **openapi.json** — API specification
- **REFLECTION.md.** — Actual Experience
  

---

# Author

**Avishkar Tambe**

Software Engineer | Full Stack & AI Developer

GitHub: https://github.com/Avishkar014

LinkedIn: https://www.linkedin.com/in/avishkar-tambe

---

# Assignment Summary

This project demonstrates:

- Reverse engineering of an undocumented web application
- Cookie-based authentication handling
- HTTP session management
- REST API design
- FastAPI development
- Clean software architecture
- API documentation
