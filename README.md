# Flock Energy API

A production-ready FastAPI wrapper for the Flock Energy API.

## Project Overview

This project provides a modular, async-ready FastAPI wrapper for interacting with the Flock Energy backend system. It is designed with clean architecture, type hints, and reusable components for future authentication and API integration.

## Features

- FastAPI with async support
- Modular route structure (Meters, Transformers, Hierarchy)
- Reusable HTTP client with `httpx`
- Pydantic models for data validation
- Environment-based configuration
- Utility functions for response formatting and error handling

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/flock-energy-api.git
cd flock-energy-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the `.env` file and update the values:

```env
BASE_URL=
USERNAME=
PASSWORD=
ACCESS_TOKEN=
REQUEST_TIMEOUT=30
```

## Run Server

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

## API Documentation

Once the server is running, you can access the interactive API docs:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Folder Structure

```text
flock-energy-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Environment variable configuration
│   ├── client.py             # Reusable HTTP client (httpx)
│   ├── models.py             # Pydantic data models
│   ├── services.py           # Business logic service functions
│   ├── utils.py              # Utility functions
│   │
│   └── routes/
│       ├── __init__.py
│       ├── meters.py         # Meter endpoints
│       ├── transformers.py   # Transformer endpoints
│       └── hierarchy.py      # Hierarchy endpoints
│
├── tests/
│   └── __init__.py
│
├── README.md
├── PROTOCOL.md
├── openapi.json
├── requirements.txt
└── .env
```

## License

MIT
