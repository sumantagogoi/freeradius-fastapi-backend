# FreeRADIUS FastAPI Backend

A lightweight REST API for managing FreeRADIUS users, built with **FastAPI** and **SQLAlchemy**. Designed to be consumed by the [FreeRADIUS React Frontend](https://github.com/sumantagogoi/freeradius-simplefront-react) or any other client (ERP, automation scripts, etc.).

---

## Features

- **JWT-based authentication** — Bearer token auth with configurable expiry
- **Admin user management** — Separate `admin_users` table for dashboard access
- **FreeRADIUS CRUD** — Manage `radcheck` and `radreply` entries directly
- **Extra user attributes** — Store Full Name, Email, Phone, Notes alongside password
- **Auto-generated Swagger docs** — Interactive API explorer at `/docs`
- **Dual database engines** — FreeRADIUS tables preserved as-is, admin tables managed by the app

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.9+) |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL (via psycopg2) |
| Auth | JWT (python-jose) + bcrypt |
| Docs | Swagger UI / OpenAPI |

## Quick Start

```bash
# Prerequisites: PostgreSQL running on localhost:5432 with a "radius" database

git clone git@github.com:sumantagogoi/freeradius-fastapi-backend.git
cd freeradius-fastapi-backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (or set env vars)
cp .env.example .env

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Seed the first admin user

```bash
curl -X POST http://localhost:8000/auth/seed \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/seed` | Create first admin user (no auth required) |
| POST | `/auth/login` | Login → JWT token |
| GET | `/auth/me` | Current user info (auth required) |

### RADIUS Users (`radcheck`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/radius/users` | List users (filtered by `attribute=Cleartext-Password` by default) |
| GET | `/radius/users?all=true` | List all radcheck entries including extras |
| GET | `/radius/users?username=jane&all=true` | Filter by username |
| POST | `/radius/users` | Create a radcheck entry (password or extra attribute) |
| PUT | `/radius/users/{id}` | Update a radcheck entry |
| DELETE | `/radius/users/{id}` | Delete a radcheck entry |

### RADIUS Replies (`radreply`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/radius/replies` | List all reply entries |
| POST | `/radius/replies` | Create a reply entry |
| DELETE | `/radius/replies/{id}` | Delete a reply entry |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://radiususer:radiuspass@localhost:5432/radius` | FreeRADIUS PostgreSQL connection |
| `JWT_SECRET` | `change-me-to-a-real-secret-in-production` | Secret key for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | `480` | Token expiry |

## Database Schema

The FreeRADIUS tables (`radcheck`, `radreply`, `radusergroup`, `nas`, etc.) are read/written as-is. The app also creates its own `admin_users` table for dashboard authentication.

Extra user attributes (Full Name, Email, Phone, Notes) are stored as additional rows in `radcheck` with custom attribute names — no schema changes needed.

## Related

- [FreeRADIUS React Frontend](https://github.com/sumantagogoi/freeradius-simplefront-react) — Web dashboard for this API
- [FreeRADIUS Project](https://freeradius.org/) — The RADIUS server itself

## License

[MIT](LICENSE)
