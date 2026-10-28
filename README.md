# Currency Fetcher

A small backend I wrote to practice the moving parts of a real web service: authentication, async database queries, caching, background jobs, and calls to an external API.

You register, log in, and ask for an exchange rate, for example `USD` to `EUR`. The service fetches it from the Frankfurter API, caches the answer in Redis for an hour, and saves the request to your history. You can also set up rate alerts like *"tell me when USD to EUR goes above 0.95"* and get an email notification when it happens.

This repository is also the foundation for my upcoming diploma project: **"Development of a web application for arbitrage opportunities in financial markets, utilizing algorithms for detecting negative-weight cycles in directed graphs."**

---

## Stack

* **Backend:** Python, FastAPI, SQLAlchemy 2.0 (asyncpg), Alembic, Pydantic v2
* **Storage & Cache:** PostgreSQL, Redis
* **Async & Background:** httpx, Celery, Redis Lock (distributed locking)
* **Testing & Dev:** Pytest, Mailpit (local SMTP), Docker Compose

---

## Run it

You need Docker installed.

```bash
git clone [https://github.com/ovoch/Currency_fetcher.git](https://github.com/ovoch/Currency_fetcher.git)
cd Currency_fetcher
cp .env.example .env
```

Open `.env` and fill in your values. Inside Docker, hosts are the service names from `docker-compose.yml`, so use `DB_Host=postgres` and `REDIS_Host=redis` (and `redis` in the Celery broker/backend URLs too).

```bash
docker compose up --build
docker compose exec api alembic upgrade head
```

The second command creates the database tables (Compose doesn't run migrations automatically on startup yet).

* **Swagger UI:** http://localhost:8000/docs
* **Mailpit (web inbox for alert emails):** http://localhost:8025

---

## Try it

If `curl` quoting is annoying on Windows, use Swagger UI instead.

```bash
# 1. Register
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "email": "test@example.com", "password": "123456"}'

# 2. Log in (returns access_token and refresh_token)
curl -X POST http://localhost:8000/users/login \
  -d "username=test@example.com&password=123456"

# 3. Ask for a rate
curl -X POST http://localhost:8000/currency \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"base": "USD", "target": "EUR"}'
```

---

## How it is organised

<img width="641" height="289" alt="Architecture diagram" src="https://github.com/user-attachments/assets/00ac4a67-443e-4775-a212-93428d5266fc" />

Routes in `api/` only deal with HTTP. Business logic lives in `services/` and database queries are in `repository/`. Services know nothing about HTTP or status codes (except auth helpers), so when something goes wrong in the domain layer they raise custom exceptions (`CurrencyNotFoundError`, `ExternalServiceError`, `UserAlreadyExistsError`) and exception handlers in `main.py` turn them into proper HTTP responses.

Settings, the database engine, Redis setup, dependencies, and security helpers live in `core/`. Celery workers and scheduled jobs are in `tasks/`.

### Endpoints

| Method | Path | Needs login | What it does |
| :--- | :--- | :--- | :--- |
| `POST` | `/users` | no | Register a new user |
| `POST` | `/users/login` | no | Get access and refresh tokens |
| `POST` | `/users/refresh/tokens` | refresh token | Rotate tokens and get a new pair |
| `POST` | `/users/logout` | yes | Revoke both access and refresh tokens |
| ` GET` | `/users/me` | yes | Get current user profile |
| `PATCH` | `/users/me/change_password` | yes | Change current user password |
| `GET` | `/users/count_users` | no | Get total number of registered users |
| `GET` | `/users/{email}` | no | Find a user by email |
| `POST` | `/currency` | yes | Fetch a rate (cached) and save to history (rate-limited) |
| `GET` | `/currency/history` | yes | Your past requests, with `limit` and `offset` pagination |
| `GET` | `/currency/stats` | no | Count how many times a pair was requested and its average rate |
| `GET` | `/currency/multirates` | yes | Fetch several target currencies in parallel |
| `POST` | `/currency/alerts` | yes | Create email alerts for a rate threshold (`more` / `less`) |

---

## Decisions I made

* **404 vs 502 for external calls:** Unknown currency returns `404` (`CurrencyNotFoundError`). If Frankfurter is down, times out, or answers with a `5xx` error, I return `502` (`ExternalServiceError`). The first one is the client's mistake, the second one is not.
* **Transaction boundaries:** Repositories call `flush()`, services call `commit()`, so one service method is always one atomic transaction.
* **Connection reuse:** One `httpx.AsyncClient` is created inside FastAPI's `lifespan` at startup and stored in `request.state`. Creating a new client on every request would throw away the TCP/TLS connection pool.
* **Precision:** Exchange rates are converted from floats/strings to `Decimal` and quantized to `0.001` before touching the database, avoiding floating-point rounding bugs.
* **Caching:** Frankfurter updates its reference rates once per working day around 16:00 CET, so caching pairs in Redis for 1 hour (`ex=3600`) cuts down external calls without serving stale data.
* **Stateless JWT revocation:** A JWT can't be cancelled on its own, so `/logout` and token refresh extract the token's `jti` and store `blacklist:access:<jti>` / `blacklist:refresh:<jti>` in Redis with a TTL equal to the remaining lifetime of the token (`exp - now`).
* **Rate limiting:** `POST /currency` is protected by a Redis counter per client IP (`INCR` + `EXPIRE 3600`). After 10 requests per hour it returns `429 Too Many Requests`.
* **BackgroundTasks vs Celery:** The audit log uses FastAPI's `BackgroundTasks` because it's lightweight and I can live with losing a log line if the process crashes. Alert checks and emails go through Celery Beat/Worker because they run on a schedule, need retries, and use a Redis lock so two workers don't send the same email twice.
* **Bounded concurrency:** `/currency/multirates` runs requests in parallel via `asyncio.gather`, capped by `asyncio.Semaphore(10)` and wrapped in `asyncio.wait_for(..., timeout=2.0)` with `return_exceptions=True`. One slow or broken currency won't hang or crash the rest of the batch.

---

## Problems I ran into

**"Event loop is closed" (`RuntimeError`) in tests and Celery.**
My SQLAlchemy async engine and Redis client were created once when the module was imported. Every pytest function and every Celery task that calls `asyncio.run()` spins up its own event loop and closes it when done. The connection pool kept connections attached to the old loop, so the next test or task tried to reuse a socket bound to a dead loop.
*How I fixed it:* For the test engine I switched to `poolclass=NullPool` so SQLAlchemy doesn't hold onto connections between loops, and wrapped each test in a dedicated connection with an explicit transaction rollback. In Celery tasks, I create a fresh client inside the task loop and close it in a `finally` block.

**The test database didn't exist (`InvalidCatalogNameError`).**
I create `test_db` using an `init.sql` script mounted into `/docker-entrypoint-initdb.d/`. PostgreSQL only runs scripts in that folder when the data directory is completely empty. Since I already had a persistent Docker volume from earlier runs, Postgres skipped the script and pytest failed with `database "test_db" does not exist`.
*How I fixed it:* Recreated the stack with `docker compose down -v` so the volume was wiped and initialized cleanly (and ran `CREATE DATABASE` manually when I didn't want to lose local dev data).

**Gmail SMTP timeouts and TLS handshakes.**
At first I tried sending real emails through `smtp.gmail.com`. Connecting failed with `SMTPNotSupportedError` and connection timeouts because port `587` expects plain connect followed by `start_tls=True` (STARTTLS), while port `465` requires implicit TLS from byte one (`use_tls=True`), plus Google blocks standard passwords without an App Password.
*How I fixed it:* For local development I dropped external SMTP and added **Mailpit** to `docker-compose.yml` (listening on port `1025` with no TLS/auth required and a web UI on `8025`). Now dev and tests don't depend on a real mailbox or internet access.

**`delete-orphan` raised `ArgumentError` when loading models.**
I put `cascade="all, delete-orphan"` on the child side of the relationship (`Many-to-One`, pointing to `User`). SQLAlchemy immediately failed on mapper initialization with `ArgumentError: On relationship ..., delete-orphan cascade is not supported on a many-to-one or many-to-many relationship`.
*How I fixed it:* Moved `cascade="all, delete-orphan"` to the parent side (`User` model's `relationship()` list), because a User owns their history/alerts, not the other way around.

**A forgotten `await` in the token blacklist.**
When checking if a token's `jti` was blacklisted in Redis, I wrote `cached_data = self.redis_client.get(redis_key)` without `await`. In async Python that returns a `coroutine` object instead of `None`. Since a coroutine object is always truthy (`bool(coroutine) is True`), my `if not cached_data:` check thought every single token was already blacklisted and rejected valid logins with `401` (plus a `RuntimeWarning: coroutine 'Redis.get' was never awaited`). Caught it during review and added `await`.

**SQLAlchemy `scalar_one()` on raw SQL vs ORM.**
In tests, calling `result.scalar_one()` on `text("SELECT * FROM users ...")` returned just the integer `id` (the first column of the first row) instead of the user row, causing `TypeError` when accessing fields. Switched test queries to ORM `select(User)` where the first scalar column is the mapped `User` entity itself.

---

## Running tests

Tests run against a real test Postgres database (isolated per test via transaction rollback) and Redis DB `1` (wiped via `flushdb`), with external HTTP calls intercepted by `httpx.MockTransport`:

```bash
docker compose exec api pytest -v
```

---

## Status & Next Steps

* **Done:** Unit tests for security helpers, full integration test suite for the `Users` module (registration, login, `/me`, token refresh rotation, logout blacklisting, password change).
* **In progress:** Integration tests for the `Currency` module using `httpx.MockTransport` and `dependency_overrides`.
* **Todo:**
  * Finish integration tests for external API errors (`404`/`502`), Redis cache hits, rate limiter (`429`), and alerts.
  * Move `GET /users/{email}` from a path parameter to a query parameter (`GET /users?email=...`).
  * Run `alembic upgrade head` automatically via an entrypoint script on container startup.
  * Add GitHub Actions CI pipeline to run `pytest` on every push.
