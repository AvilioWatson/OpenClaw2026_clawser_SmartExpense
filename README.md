# Smart Expense

Personal expense dashboard with a Go REST API, React frontend, and PostgreSQL. Sign in by pasting a one-time API token; the app issues a JWT and shows your transactions and categories with filters, summaries, and charts.

## Prerequisites

- **Docker** and **Docker Compose** (recommended), or
- **Go 1.22+**, **Node.js 20+**, and **PostgreSQL** for local development

## Quick start (Docker)

From the project root:

```bash
docker compose up --build
```

| Service | URL / port |
|---------|------------|
| Web UI | http://localhost:5173 |
| API | http://localhost:8080 |
| PostgreSQL | `localhost:5432` |

On first start, PostgreSQL runs migrations from [`migrations/`](migrations/) automatically.

### Create a login token

Connect to the database and insert a one-time token (replace `YOUR_TELEGRAM_ID` and choose a secret string):

```bash
docker compose exec db psql -U postgres -d smart_expense -c \
  "INSERT INTO tokens (telegram_id, token) VALUES (YOUR_TELEGRAM_ID, 'your-secret-token');"
```

Example:

```sql
INSERT INTO tokens (telegram_id, token) VALUES (552378634, 'my-login-token');
```

Open http://localhost:5173, paste the token, and sign in. The token is deleted after use; request a new one for the next login.

### Stop and reset

```bash
# Stop services
docker compose down

# Stop and remove database volume (re-runs migrations on next up)
docker compose down -v
```

## Local development (without Docker)

### 1. Database

Ensure PostgreSQL is running and create the database:

```bash
createdb -U postgres smart_expense
```

Apply migrations in order:

```bash
export PGPASSWORD=pg123
for f in migrations/V*.sql; do
  psql -h localhost -U postgres -d smart_expense -f "$f"
done
```

### 2. Backend

```bash
cd backend
cp .env.example .env   # optional; defaults work for local Postgres
export JWT_SECRET=dev-secret-change-in-production-min-32-chars
go run ./cmd/server
```

API listens on http://localhost:8080.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI at http://localhost:5173 (Vite proxies `/api` to the backend).

## Environment variables

### API (`backend`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgres://postgres:pg123@localhost:5432/smart_expense?sslmode=disable` | PostgreSQL connection string |
| `JWT_SECRET` | (required, min 32 chars) | HMAC secret for JWT signing |
| `JWT_TTL` | `24h` | JWT lifetime |
| `PORT` | `8080` | HTTP listen port |
| `CORS_ORIGIN` | `http://localhost:5173` | Allowed browser origin |

See [`backend/.env.example`](backend/.env.example).

### PostgreSQL (Docker `db` service)

| Variable | Value |
|----------|--------|
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `pg123` |
| `POSTGRES_DB` | `smart_expense` |

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Health check |
| `POST` | `/api/v1/auth/login` | No | Body: `{ "token": "..." }` → JWT (token consumed) |
| `GET` | `/api/v1/transactions` | JWT | List transactions (paginated, filterable) |
| `GET` | `/api/v1/transactions/summary` | JWT | Income / expense / net totals |
| `GET` | `/api/v1/transactions/by-category` | JWT | Totals grouped by category |
| `GET` | `/api/v1/categories` | JWT | Active categories |

### Transaction query parameters

- **Date:** `year`, `month`, `from`, `to` (ISO dates `YYYY-MM-DD`)
- **Filters:** `type` (`income` \| `expense`), `category_id`, `q` (search merchant/description)
- **Sort:** `sort` (`transaction_date`, `amount`, `category_name`, `created_at`), `order` (`asc` \| `desc`)
- **Pagination:** `limit` (default 50, max 200), `offset`

## Project structure

```
smart-expense/
├── backend/          # Go API (chi, pgx, JWT)
├── frontend/         # React + Vite dashboard
├── migrations/       # PostgreSQL schema (V001–V005)
├── docker-compose.yml
└── README.md
```

## Troubleshooting

- **Port 5432 already in use:** Stop local PostgreSQL or change the host port in `docker-compose.yml`.
- **Empty dashboard after login:** Transactions are scoped by `telegram_id`. Ensure your token’s `telegram_id` matches rows in `transactions`, or clear date filters on the dashboard.
- **Migrations not applied:** Use `docker compose down -v` and `docker compose up` for a fresh database volume.
