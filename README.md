# 🧑‍💻 Author  
**znuzhg (Mahmut Balıkçı)**  
GitHub: https://github.com/znuzhg  

---

🚀 Flask Production-Ready Backend Boilerplate
JWT • RBAC • SQLAlchemy • Redis Cache • RQ Jobs • Metrics • Docker • CI • OpenAPI 3

Bu proje, modern bir production-grade Flask backend oluşturmak için gerekli tüm yapıyı sunar.
Güvenli, ölçeklenebilir ve profesyonel bir mimariye sahip bir web servisi geliştirmen için hazır altyapı sağlar.

---

## ⭐ Executive Summary

Bu backend aşağıdaki özellikleri içerir:

🔐 JWT Authentication
(Access/Refresh token, rotation, blacklist, fingerprinting)

🛡 RBAC yetkilendirme (admin, user)

👤 User CRUD (ETag + If-Match destekli)

⚙️ Admin tools (CSV export, async jobs)

⚡ Redis Cache entegrasyonu

📊 Metrics / Observability endpointleri

🧵 Background jobs (RQ)

🧱 SQLAlchemy ORM

🐳 Docker + Gunicorn Deployment

🔍 OpenAPI 3 / Swagger dokümantasyonu

🧪 pytest test suite

🧰 Python SDK (Client)

Python 3.11+ & MySQL 8 ile tamamen uyumludur.

## 📁 Project Structure

| Path | Description |
|------|-------------|
| `app.py` | App factory, OpenAPI, metrics, middleware |
| **config/** | — |
| `config/settings.py` | Dev/Test/Prod config, env validation, CORS/security |
| `config/logging_conf.py` | JSON logging, rotating handlers |
| **database/** | — |
| `database/base.py` | SQLAlchemy engine, session, pooling |
| `database/migrations/` | Alembic migrations |
| **models/** | — |
| `models/user.py` | User model (soft delete, timestamps) |
| **repositories/** | — |
| `repositories/user_repository.py` | CRUD, filters, pagination, ETag management |
| **services/** | — |
| `services/user_service.py` | Business logic, hashing, cache invalidation |
| **routes/** | — |
| `routes/auth.py` | Register, login, refresh, logout, me |
| `routes/users.py` | Admin CRUD |
| `routes/admin.py` | CSV export (sync/async) |
| **utils/** | — |
| `utils/security.py` | JWT, RBAC, fingerprint, rotation |
| `utils/response.py` | Response envelope helper |
| `utils/errors.py` | Global error handlers |
| `utils/pagination.py` | Pagination logic |
| `utils/cache.py` | Redis / in-memory cache layer |
| `utils/rate_limit.py` | Rate limiting module |
| `utils/metrics.py` | Prometheus metrics |
| `utils/etag.py` | ETag helpers |
| `utils/logger.py` | Centralized logger |
| **schemas/** | — |
| `schemas/auth_schema.py` | Marshmallow schema for auth |
| `schemas/user_schema.py` | Marshmallow schema for users |
| **client/** | — |
| `client/api.py` | Python SDK client |
| **examples/** | — |
| `examples/demo_client.py` | Example client usage |
| **tests/** | pytest suite |
| `manage.py` | CLI commands (create-admin, seed-data) |
| `Dockerfile` | Production build with Gunicorn |
| `Dockerfile.alpine` | Lightweight Alpine image |
| `docker-compose.yml` | API + MySQL + Redis stack |
| `Makefile` | Format, lint, test, typecheck commands |
| `pyproject.toml` | ruff, mypy, black configuration |
| `LICENSE` | MIT License |


🔄 Request Lifecycle (Flow Diagram)

| Step | Layer                      | Description                                                |
| ---- | -------------------------- | ---------------------------------------------------------- |
| 1    | **HTTP Request**           | Client → API endpoint                                      |
| 2    | **Routes (Blueprints)**    | URL eşleşmesi, schema validation, rate-limit kontrolü      |
| 3    | **Services**               | İş mantığı, validation, security rules, cache invalidation |
| 4    | **Repositories**           | Veritabanı CRUD, filter, pagination, ETag hesaplama        |
| 5    | **SQLAlchemy ORM / Cache** | ORM query çalışır veya Redis cache kontrol edilir          |
| 6    | **MySQL / Redis**          | Final işlem; DB read/write veya Redis get/set              |


🔐 Authentication & Authorization
✔ Access Token (short TTL)
✔ Refresh Token (long TTL)
✔ Rotation (token_version)
✔ Blacklist (jti)
✔ Fingerprinting (IP + User-Agent)
✔ RBAC (admin / user)

Endpoints

| Method | Endpoint           | Description           |
| ------ | ------------------ | --------------------- |
| POST   | `/auth/register`   | New user (idempotent) |
| POST   | `/auth/login`      | Access+Refresh tokens |
| POST   | `/auth/refresh`    | Rotate tokens         |
| POST   | `/auth/logout`     | Revoke token          |
| POST   | `/auth/logout-all` | Revoke all tokens     |
| GET    | `/auth/me`         | Logged-in user        |

👤 Users API

| Method | Endpoint      | Role  | Description       |
| ------ | ------------- | ----- | ----------------- |
| POST   | `/users`      | admin | Create            |
| GET    | `/users`      | admin | List (cached)     |
| GET    | `/users/<id>` | admin | Fetch (ETag)      |
| PUT    | `/users/<id>` | admin | Update (If-Match) |
| PATCH  | `/users/<id>` | admin | Partial update    |
| DELETE | `/users/<id>` | admin | Soft delete       |
| GET    | `/users/me`   | user  | Own profile       |

🧮 Pagination / Sorting / Filtering

Örnek:

/users?page=1&per_page=20&sort=desc&sort_by=created_at&name=ali&email=@gmail.com

page ≥ 1

per_page ≤ 100

Sorting: asc | desc

Sort fields: created_at, email, name, id

Filtering: name, email

🧱 Error Handling (Standard Envelope)

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

| Code                   | Meaning                  |
| ---------------------- | ------------------------ |
| VALIDATION_ERROR       | Bad input                |
| INVALID_CREDENTIALS    | Wrong password           |
| EMAIL_EXISTS           | Duplicate email          |
| TOKEN_EXPIRED          | Token expired            |
| TOKEN_REVOKED          | Blacklisted              |
| TOKEN_CONTEXT_MISMATCH | IP / User-Agent mismatch |
| VERSION_CONFLICT       | ETag mismatch            |
| FORBIDDEN              | RBAC denied              |
| RATE_LIMITED           | Too many requests        |


⚙️ Environment Variables

| Name                  | Required | Default | Example                               | Description     |
| --------------------- | -------- | ------- | ------------------------------------- | --------------- |
| DATABASE_URL          | yes      | —       | mysql+pymysql://root:pass@db:3306/app | DB URI          |
| SECRET_KEY            | yes      | —       | change-me                             | Flask secret    |
| JWT_SECRET            | yes      | —       | change-me-too                         | JWT signing     |
| JWT_ALG               | no       | HS256   | HS256                                 | Algorithm       |
| ACCESS_TOKEN_EXPIRES  | no       | 600     | 900                                   | sec             |
| REFRESH_TOKEN_EXPIRES | no       | 2592000 | 2592000                               | sec             |
| CORS_ORIGINS          | no       | *       | [https://site.com](https://site.com)  | Allowed origins |
| LOG_JSON              | no       | false   | true                                  | JSON logs       |
| REDIS_URL             | no       | —       | redis://redis:6379/0                  | Cache + RQ      |
| MAX_CONTENT_LENGTH    | no       | 2MB     | 1MB                                   | Upload limit    |
| FLASK_ENV             | no       | dev     | prod                                  | Environment     |

🐳 Docker Deployment

Build
docker build -t flask-api .

Run (with compose)
docker-compose up --build

İçerir:

MySQL 8

Redis

API (Gunicorn)

Healthchecks

Alembic migrations

🔥 Production Notes
Gunicorn workers: 2 * CPU + 1

Mutlaka strong SECRET_KEY ve JWT_SECRET kullan

CORS’u prod ortamında kısıtla

Reverse proxy olarak Nginx + HTTPS kullan

Prod logları için:
LOG_JSON=true

🧪 Testing & Tooling
pytest -q
make format
make lint
make typecheck
make test

Test DB → SQLite (in-memory)

🧰 Python SDK Example

from client import APIClient

api = APIClient("http://localhost:5000")
api.login("admin@example.com", "secret123")

me = api.get_current_user()
print(me)

📈 Roadmap
Better metrics (latency histograms)

RBAC matrix expansion

Node.js / Go / Java SDKs

Redis-backed distributed rate limiting

OTP / MFA login

More background jobs

🤝 Contributing
Fork the repo

Feature branch oluştur

Format & lint kurallarına uy:
make format && make lint && make typecheck

Açıklayıcı bir PR gönder

Tüm testler geçmeli

📄 License
Bu proje MIT License ile lisanslanmıştır.
Detaylar için: LICENSE
