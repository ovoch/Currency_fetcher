Currency_fetcher

A small backend I wrote to practice the parts of a real web service: login, a database, caching, background jobs and calls to an outside API.

You register, log in and ask for an exchange rate, for example USD to EUR. The service gets it from Frankfurter, keeps the answer in Redis for an hour and saves the request in your history.
You can also create an alert like "tell me when USD to EUR goes above 0.95" and get an email when it happens.

Also i want it to be future diploma project.The theme is "Development of a web application for arbitrage opportunities in financial markets, 
utilizing algorithms for detecting negative-weight cycles in directed graphs".

Run it

You need Docker.

git clone https://github.com/ovoch/Currency_fetcher.git
cd Currency_fetcher
cp .env.example .env

Open .env and fill in your own values. Inside Docker the hosts are the service names, 
so use DB_Host=postgres and REDIS_Host=redis (and redis in the Celery URLs too).

docker compose up --build
docker compose exec api alembic upgrade head

The second command creates the tables. Compose doesn't run migrations by itself yet.

Swagger UI is at http://localhost:8000/docs. Alert emails end up in Mailpit at http://localhost:8025.

Try it

If curl quoting is annoying on Windows, use Swagger UI instead.

# register
curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name": "test", "email": "test@example.com", "password": "123456"}'

# log in, you get an access token and a refresh token
curl -X POST http://localhost:8000/users/login -d "username=test@example.com&password=123456"

# ask for a rate
curl -X POST http://localhost:8000/currency -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{"base": "USD", "target": "EUR"}'

How it is organised

<img width="641" height="289" alt="image" src="https://github.com/user-attachments/assets/00ac4a67-443e-4775-a212-93428d5266fc" />

Routes in api/ only deal with HTTP. The logic is in services/ and the database queries are in repository/. Services know nothing about HTTP, so when something goes wrong they raise my own exceptions (CurrencyNotFoundError, ExternalServiceError, UserAlreadyExistsError) and main.py turns them into status codes. 
Settings, the database engine, Redis and the security helpers live in core/. Celery tasks are in tasks/.

Method	Path	Needs login	What it does
POST	/users	no	register
POST	/users/login	no	get access and refresh tokens
POST	/users/refresh/tokens	refresh token	get a new pair
POST	/users/logout	yes	revoke both tokens
PATCH	/users/me/change_password	yes	change password
POST	/currency	yes	get a rate, saved to your history
GET	/currency/history	yes	your past requests, with limit and offset
GET	/currency/multirates	yes	several currencies at once
POST	/currency/alerts	yes	create alerts for a rate threshold

Decisions I made
-Unknown currency returns 404. If Frankfurter is down or answers with an error, I return 502. The first one is the client's mistake, the second one is not.
-Repositories call flush, services call commit, so one service method is one transaction.
-One httpx.AsyncClient is created at startup and reused. A new client for every request would throw away the connection pool.
-Frankfurter updates its rates about once per working day, so I cache them for an hour.
-A JWT can't be cancelled, so logout puts the token's jti in Redis until the token would expire anyway.
-The audit log uses BackgroundTasks: it's small and I can live with losing it if the process dies. Emails go through Celery, because they are scheduled and need retries.
-Requests for several currencies run in parallel, at most 10 at a time and 2 seconds each. One slow currency doesn't break the rest.

## Problems I ran into

**"Event loop is closed" in tests and Celery.** My engine and Redis client were created once, when the module was imported. Every test, and every Celery task that calls `asyncio.run`, gets its own event loop and the loop is closed when it finishes. The connection pool kept connections that were opened on the old loop, so the next test tried to reuse one that belonged to a dead loop. [How I fixed it.]

**The test database didn't exist.** I create `test_db` with `init.sql`. Postgres runs init scripts only when its data volume is empty, so with an old volume the script never ran and the tests failed with "database does not exist". [How I fixed it.]

**Gmail SMTP didn't work.** [What I tried, which ports, what error I got.] The port decides how TLS starts: 587 uses STARTTLS, 465 starts with TLS. In the end I used Mailpit, a local fake SMTP server, so development doesn't depend on a real mailbox.

**`delete-orphan` raised an error.** I put `cascade="all, delete-orphan"` on [the child side of the relationship]. SQLAlchemy raised an error when the models were loaded (it was SQLAlchemy, not Postgres). [How I fixed it.]

**A forgotten `await`.** In the token blacklist I called Redis without `await`. That returns a coroutine object, and a coroutine is always truthy, so the check never worked as I expected. I found it during code review and fixed it.


Status

Tests so far: unit tests for the security helpers and integration tests for registration. Still to do: tests for the external API errors, the cache, the rate limiter, token refresh and alerts.
Also GitHub Actions, running migrations when the container starts, and checking which endpoints should require login.
