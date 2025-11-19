📌 README.md (Tam Profesyonel Versiyon)

# 🚀 Flask Production-Ready Backend Boilerplate  
### JWT • RBAC • SQLAlchemy • Redis Cache • RQ Jobs • Metrics • Docker • CI • OpenAPI 3

This repository provides a **production-grade Flask backend skeleton** with modern architecture, layered design, JWT authentication, RBAC, Redis caching, rate limiting, background jobs, ETag versioning, metrics, observability, Docker support, CI pipeline, and a built-in Python SDK.

Use it as a **solid foundation** to build secure, scalable, maintainable backend services.

---

## ⭐ Executive Summary

This backend template includes:

- **Secure JWT auth** (access/refresh, rotation, blacklist, fingerprinting)  
- **Role-based authorization** (RBAC: admin, user)  
- **User CRUD** with soft-delete & ETag / If-Match support  
- **Admin features** (CSV export, async RQ jobs)  
- **Redis caching layer**  
- **Metrics & observability endpoints**  
- **Docker + Gunicorn production deployment**  
- **SQLite-based test environment**  
- **Python SDK for clients**  
- **Fully documented OpenAPI 3**  

Compatible with **Python 3.11+** and **MySQL 8**.

---

# 📁 Project Structure
.
├─ app.py # App factory, OpenAPI, metrics, middleware
├─ config/
│ ├─ settings.py # Dev/Test/Prod config, env validation, CORS/security
│ └─ logging_conf.py # Logging config, rotating handlers, JSON logs
├─ database/
│ ├─ base.py # SQLAlchemy engine, session, pooling
│ └─ migrations/ # Alembic migrations
├─ models/
│ └─ user.py # User model with soft-delete & timestamps
├─ repositories/
│ └─ user_repository.py # CRUD, filters, pagination, ETag
├─ services/
│ └─ user_service.py # Business logic, hashing, cache invalidation
├─ routes/
│ ├─ auth.py # register, login, refresh, logout, me
│ ├─ users.py # Admin CRUD, list, user me
│ └─ admin.py # CSV export (sync/async) + job status
├─ utils/
│ ├─ security.py # JWT, RBAC, fingerprint, blacklist, rotation
│ ├─ response.py # Response envelope helpers
│ ├─ errors.py # Global error handlers
│ ├─ pagination.py # Pagination & validation
│ ├─ cache.py # Redis/in-memory caching
│ ├─ rate_limit.py # Rate limiting by IP/email
│ ├─ metrics.py # Prometheus metrics generator
│ ├─ etag.py # ETag helpers
│ └─ logger.py # Logger getter
├─ schemas/ # Marshmallow schemas (optional)
├─ client/
│ └─ api.py # Python SDK client
├─ examples/
│ └─ demo_client.py # SDK usage example
├─ tests/ # pytest suite
├─ manage.py # CLI commands (create-admin / seed-data)
├─ Dockerfile # Multi-stage build (production)
├─ Dockerfile.alpine # Lightweight build
├─ docker-compose.yml # API + MySQL stack with healthchecks
├─ Makefile # Format, lint, typecheck, test, run
├─ pyproject.toml # Tool configs: black, ruff, mypy
└─ LICENSE # MIT License


---

# 🔄 Request Lifecycle (Flow Diagram)

    ┌──────────────────────────────┐
    │          HTTP Request        │
    └───────────────┬──────────────┘
                    ▼
       ┌─────────────────────────┐
       │         Routes          │
       └───────────┬────────────┘
                   ▼
       ┌─────────────────────────┐
       │        Services         │
       └───────────┬────────────┘
                   ▼
       ┌─────────────────────────┐
       │      Repositories       │
       └───────────┬────────────┘
                   ▼
       ┌─────────────────────────┐
       │ SQLAlchemy ORM / Cache  │
       └───────────┬────────────┘
                   ▼
         ┌───────────────────┐
         │   MySQL / Redis   │
         └───────────────────┘

---

# 🔐 Authentication & Authorization

### ✔ Access Token (short TTL)  
### ✔ Refresh Token (long TTL)  
### ✔ Rotation (token_version)  
### ✔ Blacklist (jti)  
### ✔ Fingerprinting (ip + ua)  
### ✔ RBAC (`roles = admin,user`)  

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Idempotent user registration |
| POST | /auth/login | Get access & refresh token |
| POST | /auth/refresh | Rotate tokens |
| POST | /auth/logout | Revoke current token |
| POST | /auth/logout-all | Revoke all tokens |
| GET | /auth/me | Current user |

---

# 👤 Users API

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /users | admin | Create user |
| GET | /users | admin | List users (cached) |
| GET | /users/<id> | admin | Fetch user (ETag) |
| PUT | /users/<id> | admin | Update with If-Match |
| PATCH | /users/<id> | admin | Partial update |
| DELETE | /users/<id> | admin | Soft delete |
| GET | /users/me | user | Self info |

---

# 🧮 Pagination / Sorting / Filtering
/users?page=1&per_page=20&sort=desc&sort_by=created_at&name=ali&email=@gmail.com


- **page** ≥ 1  
- **per_page** ≤ 100  
- **sort**: asc | desc  
- **sort_by**: created_at | email | name | id  
- **Filtering**: name, email (case-insensitive)

---

# 🧱 Error Handling (Standard Envelope)

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": { "email": ["Not a valid email"] }
  }
}

Error Codes
Code	Meaning
VALIDATION_ERROR	Bad input
INVALID_CREDENTIALS	Wrong password
EMAIL_EXISTS	Duplicate email
TOKEN_EXPIRED	Token expired
TOKEN_REVOKED	Blacklisted
TOKEN_CONTEXT_MISMATCH	IP/UA mismatch
VERSION_CONFLICT	ETag mismatch
FORBIDDEN	RBAC
RATE_LIMITED	Too many requests

⚙️ Configuration & Environment Variables
| Name                  | Required | Default | Example                               | Description          |
| --------------------- | -------- | ------- | ------------------------------------- | -------------------- |
| DATABASE_URL          | yes      | —       | mysql+pymysql://root:pass@db:3306/app | DB URI               |
| SECRET_KEY            | yes      | —       | change-me                             | Flask secret         |
| JWT_SECRET            | yes      | —       | change-me-too                         | JWT signing key      |
| JWT_ALG               | no       | HS256   | HS256                                 | Algorithm            |
| ACCESS_TOKEN_EXPIRES  | no       | 600     | 900                                   | Seconds              |
| REFRESH_TOKEN_EXPIRES | no       | 2592000 | 2592000                               | Seconds              |
| CORS_ORIGINS          | no       | *       | [https://site.com](https://site.com)  | Allowed origins      |
| LOG_JSON              | no       | false   | true                                  | Structured logs      |
| REDIS_URL             | no       | —       | redis://redis:6379/0                  | Enables cache & jobs |
| MAX_CONTENT_LENGTH    | no       | 2MB     | 1MB                                   | Request size limit   |
| FLASK_ENV             | no       | dev     | prod                                  | Environment          |

🐳 Docker Deployment
Build & Run
Includes

MySQL 8 (persistent)

API (Gunicorn)

Healthchecks

Automatic Alembic migrations (attempt)

🔥 Production Notes
Gunicorn

Binds to 0.0.0.0:5000

Recommended workers: 2 * CPU + 1

Security Recommendations

Strong SECRET_KEY & JWT_SECRET

Restrict CORS_ORIGINS

Use HTTPS via Nginx reverse proxy

Enable LOG_JSON=true for production logs

🧪 Testing & Tooling
pytest -q
make format
make lint
make typecheck
make test
SQLite in-memory used for test DB.
🧰 Python SDK Example
from client import APIClient

api = APIClient("http://localhost:5000")
api.login("admin@example.com", "secret123")

me = api.get_current_user()
print(me)
📈 Roadmap

Additional resources (posts, products, organizations)

RBAC permissions matrix

Metrics histograms (latency buckets)

SDKs for Node.js / Go / Java

Distributed rate limiting (Redis-backed)

OTP / MFA login

🤝 Contributing

Fork the repo

Create a feature branch

Follow formatting rules:
make format && make lint && make typecheck
Submit a PR with a clear description

All tests must pass

📄 License

Licensed under the MIT License.
See LICENSE for details.
