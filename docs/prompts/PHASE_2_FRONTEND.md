# Phase 2 — Frontend + Docker + Documentation

## Role

You are a **Senior Full-Stack Engineer** finishing a take-home assessment. Phase 0 generated artifacts. Phase 1 built the backend with TDD. This phase makes the project **submission-ready** — Docker orchestration, a README that demonstrates senior-level thinking, and a clean frontend.

## Mission

Priority order:
1. **Docker Compose** — `docker compose up` and everything works, first try
2. **README** — the single most important file for the assessor. Architecture decisions, tradeoffs, production considerations.
3. **Frontend** — functional, clean, demonstrates the API. Don't over-invest.
4. **Makefile** — operational convenience that signals production mindset
5. **Final git polish**

## Context

Read before starting:
- `./CLAUDE.md` — conventions
- `./docs/artifacts/features/ride-list-api/api-contract.md` — response format
- `./docs/artifacts/analysis/architecture-decisions.md` — decisions to include in README
- Backend is complete in `./backend/` with passing tests

---

## Commit Strategy (continued from Phase 1)

```
Commit 13: "docker: Compose + backend Dockerfile + healthchecks"
Commit 14: "frontend: React app with ride list, filters, pagination"
Commit 15: "docs: comprehensive README with architecture decisions and Makefile"
```

---

## Step 1: Docker Compose

**Commit: "docker: Compose + backend Dockerfile + healthchecks"**

This commit includes the backend Dockerfile created at the end of Phase 1.

### `docker-compose.yml` (project root)

```yaml
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpass}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-wingz_db}
      MYSQL_USER: ${MYSQL_USER:-appuser}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-apppass}
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
      - ./backend/sql/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./backend/sql/seed_data.sql:/docker-entrypoint-initdb.d/02-seed.sql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DB_HOST: db
      DB_PORT: "3306"
      DB_USER: ${MYSQL_USER:-appuser}
      DB_PASSWORD: ${MYSQL_PASSWORD:-apppass}
      DB_NAME: ${MYSQL_DATABASE:-wingz_db}
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

volumes:
  db_data:
```

Design notes (these go in the README, not as inline comments):
- Init scripts prefixed `01-`, `02-` for deterministic execution order
- `service_healthy` prevents backend from starting before MySQL accepts connections
- Named volume preserves data across restarts
- Sensible `.env` defaults so `docker compose up` works without configuration

**Verify:** `docker compose config` validates the file.

**COMMIT.**

---

## Step 2: Frontend

**Commit: "frontend: React app with ride list, filters, pagination"**

### Scaffold
```bash
npm create vite@latest frontend -- --template react
cd frontend && npm install
```

**IMPORTANT:** The assessment asks for a RESTful API, not a frontend. The frontend is a bonus to demonstrate full-stack capability. If the frontend build fails or causes Docker issues, **skip it and move on** — the backend is the priority. Ensure the backend service is independently accessible on port 8000 regardless of frontend status.

### Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── RideTable.jsx        # Table of rides with all fields + status badges
│   │   └── Pagination.jsx       # Prev/Next + page info
│   ├── services/
│   │   └── api.js               # fetchRides() wrapper with auth
│   ├── App.jsx                  # Main orchestrator: filters + table + pagination
│   ├── App.css                  # Clean functional styles
│   └── main.jsx
├── Dockerfile                   # Multi-stage: build + nginx
├── nginx.conf                   # Reverse proxy for /api/
├── .dockerignore
├── package.json
└── vite.config.js
```

### `vite.config.js`
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
```

### `src/services/api.js`
```javascript
const API_BASE = '/api'

// Default admin credentials — matches seed data
const AUTH_HEADER = 'Basic ' + btoa('admin@wingz.com:adminpass123')

export async function fetchRides(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) query.append(k, v)
  })
  const res = await fetch(`${API_BASE}/rides/?${query}`, {
    headers: { 'Authorization': AUTH_HEADER },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || data.detail || `HTTP ${res.status}`)
  }
  return res.json()
}
```

### `src/App.jsx`
Main orchestrator with inline filter form. Keep it simple — filters are part of App, not a separate component.

```jsx
import { useState, useEffect } from 'react'
import { fetchRides } from './services/api'
import RideTable from './components/RideTable'
import Pagination from './components/Pagination'
import './App.css'

export default function App() {
  const [rides, setRides] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  // Filter state
  const [status, setStatus] = useState('')
  const [riderEmail, setRiderEmail] = useState('')
  const [sortBy, setSortBy] = useState('')

  async function load(p = page) {
    setLoading(true)
    setError('')
    try {
      const params = { page: p, page_size: 10 }
      if (status) params.status = status
      if (riderEmail) params.rider_email = riderEmail
      if (sortBy) params.sort_by = sortBy
      const data = await fetchRides(params)
      setRides(data.results || [])
      setCount(data.count || 0)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(1) }, [])

  function handleSubmit(e) {
    e.preventDefault()
    setPage(1)
    load(1)
  }

  return (
    <div className="app">
      <h1>Wingz Ride Management</h1>
      <form onSubmit={handleSubmit} className="filters">
        <select value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="en-route">en-route</option>
          <option value="pickup">pickup</option>
          <option value="dropoff">dropoff</option>
        </select>
        <input placeholder="Rider email" value={riderEmail}
               onChange={e => setRiderEmail(e.target.value)} />
        <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
          <option value="">No sorting</option>
          <option value="pickup_time">Pickup Time</option>
        </select>
        <button type="submit" disabled={loading}>Search</button>
      </form>

      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <>
          <RideTable rides={rides} />
          <Pagination count={count} page={page} pageSize={10}
                      onChange={p => { setPage(p); load(p) }} />
        </>
      )}
    </div>
  )
}
```

### Components

**`RideTable.jsx`:**
- HTML table with columns: ID, Status (color-coded badge inline), Rider, Driver, Pickup Time, Events count
- Status badge colors inline via style (blue=en-route, amber=pickup, green=dropoff)
- Simple, functional — no CSS Grid cards or expandable sections

**`Pagination.jsx`:**
- Previous/Next buttons (disabled at boundaries)
- "Page X of Y" text

### `App.css`
Minimal, functional:
- Clean table styling
- Filter bar as horizontal flex row
- Status badge colors
- Error state styling
- No CSS framework, nothing decorative

### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### `nginx.conf`
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
```

### `.dockerignore`
```
node_modules
dist
.git
```

**Verify:** `cd frontend && npm run build` succeeds.

**COMMIT.**

---

## Step 3: README — The Differentiator

**Commit: "docs: comprehensive README with architecture decisions"**

**Read:** `docs/artifacts/analysis/architecture-decisions.md` — weave these into the README.

### `README.md` (project root)

This is the single most impactful file. Write it as a senior engineer would write an architecture document — not just setup instructions.

```markdown
# Wingz Ride Management API

RESTful API built with Django REST Framework for managing ride information,
featuring optimized query performance, database-level distance sorting, and
comprehensive test coverage.

## Quick Start

```bash
# Prerequisites: Docker and Docker Compose installed
cp .env.example .env
docker compose up -d

# Wait ~30s for MySQL to initialize, then:
# API:      http://localhost:8000/api/rides/
# Frontend: http://localhost:8080
```

## Architecture

```
┌────────────┐      ┌────────────┐      ┌──────────────┐
│  Frontend  │─────▶│   nginx    │─────▶│   Backend    │
│   (React)  │      │  (proxy)   │      │ (Django/DRF) │
└────────────┘      └────────────┘      └──────┬───────┘
                                               │
                                         ┌─────▼──────┐
                                         │   MySQL    │
                                         │    8.0     │
                                         └────────────┘
```

nginx serves the React SPA and proxies `/api/` requests to the Django backend.
This eliminates CORS entirely — frontend and API share the same origin.

## API Reference

### `GET /api/rides/`

Paginated list of rides with nested rider, driver, and today's ride events.

**Authentication:** HTTP Basic Auth with email and password. Only users with `role='admin'` can access.

```bash
curl -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/
```

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter: en-route, pickup, dropoff |
| rider_email | string | Filter: exact match on rider email |
| sort_by | string | `pickup_time` or `distance` |
| latitude | float | Required when sort_by=distance |
| longitude | float | Required when sort_by=distance |
| page | int | Page number (default 1) |
| page_size | int | Results per page (default 10, max 100) |

**Examples:**
```bash
# All rides (admin credentials required)
curl -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/

# Filter + sort
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?status=pickup&sort_by=pickup_time"

# Distance from Zone 10, Guatemala City
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131"
```

## Design Decisions

### Performance: 2-3 SQL Queries for the Ride List

This was the hardest requirement. The full ride list — with nested rider, driver,
and today's events — loads in exactly **3 queries**:

1. `COUNT(*)` for pagination total
2. `SELECT rides JOIN users` via `select_related('id_rider', 'id_driver')`
3. `SELECT ride_events WHERE created_at >= 24h ago` via `Prefetch` with filtered
   queryset and `to_attr='todays_ride_events'`

**Why `Prefetch(to_attr=...)` over a serializer method field?**
A `SerializerMethodField` like `get_todays_ride_events(obj)` would execute a query
per ride — the classic N+1 problem. With 100 rides per page, that's 100 extra queries.
`Prefetch` batches all into a single filtered query regardless of page size.

This is verified in `test_performance.py` using Django's `CaptureQueriesContext`.

### Distance Sorting: Haversine at the Database Level

The spec assumes a very large rides table, so sorting MUST happen in the database.
Loading all rides into Python to sort would:
- Break pagination (can't LIMIT/OFFSET after an in-memory sort)
- Require O(n) memory
- Be unacceptably slow at scale

I use a `RawSQL` annotation with the Haversine formula, which lets
`ORDER BY distance` work with standard pagination.

**Tradeoffs and production alternatives:**
| Approach | Pros | Cons |
|----------|------|------|
| RawSQL Haversine (current) | Works on MySQL+SQLite, no schema changes | Full table scan for sorting |
| MySQL `ST_Distance_Sphere()` | Native, well-optimized | MySQL-specific, breaks SQLite tests |
| Spatial index on POINT column | O(log n) lookup | Requires schema change (spec prohibits) |
| PostGIS + GeoDjango | Most powerful geo support | PostgreSQL required, heavy dependency |

For production with millions of rides, I would add a spatial index — but the spec says
we cannot modify the table structure.

### Custom User Model with BasicAuthentication

The spec defines a custom `users` table with `id_user` and `role`. Rather than force-fit
this into Django's `AbstractUser`, I created a standalone model with a `password` field
(hashed via Django's `make_password`). A custom `EmailBasicAuthentication` class handles
HTTP Basic Auth using email + password, while `IsAdminRole` checks `user.role == 'admin'`.

**Why not Django's auth system?** The spec's table structure doesn't match `AbstractUser`
(no `username`, no `is_staff`, custom PK). Forcing compatibility would add complexity
for no benefit. A standalone model with Basic Auth is simpler and sufficient.

**Tradeoff:** We lose Django admin login, but the spec doesn't require it. Production
would use Token/JWT auth instead of Basic Auth.

### SQLite for Tests, MySQL for Production

Tests run on SQLite in-memory for speed (~2s full suite vs ~10s with MySQL). SQLite lacks
math functions needed for Haversine, so a pytest autouse fixture registers them:

```python
@pytest.fixture(autouse=True)
def _register_sqlite_math(db):
    if connection.vendor == 'sqlite':
        connection.connection.create_function("RADIANS", 1, math.radians)
        # ... SIN, COS, ASIN, SQRT, POWER
```

## Running Tests

```bash
cd backend && pytest -v          # ~34 tests
cd backend && ruff check .       # Linting
```

Key test highlights:
- `test_performance.py` — **proves** the 2-3 query target with `CaptureQueriesContext`
- `test_views.py` — verifies distance sort using real Guatemala City GPS coordinates
- `test_permissions.py` — tests exact role matching (case-sensitive) and real BasicAuth flow

### Why ReadOnlyModelViewSet?

The spec says "Use Viewsets for managing CRUD operations" but only defines a list/query
API. `ReadOnlyModelViewSet` provides `list()` and `retrieve()` — exactly what's needed.
Using a full `ModelViewSet` would expose create/update/delete endpoints that aren't
specified and would need additional permission logic.

## Bonus SQL: Trips > 1 Hour by Month and Driver

```bash
make bonus-sql    # Runs the query against Docker MySQL
```

Full query: [`backend/sql/bonus_report.sql`](backend/sql/bonus_report.sql)

**Edge cases handled:**
- Rides with multiple pickup/dropoff events: uses `MIN(pickup)` / `MAX(dropoff)`
- Boundary: strictly `> 60 minutes` (a 60-minute trip is NOT counted)
- Driver name format: `CONCAT(first_name, ' ', LEFT(last_name, 1))` matches sample output

## What I'd Change for Production

1. **Spatial index** — `SPATIAL INDEX` on a `POINT` column for O(log n) distance queries
2. **Cursor pagination** — eliminates the COUNT query for faster responses on large tables
3. **Token/JWT auth** — stateless authentication for API consumers
4. **Redis caching** — cache ride list with TTL, invalidate on writes
5. **Read replica** — route list queries to a replica for horizontal read scaling
6. **Connection pooling** — `django-db-connection-pool` for MySQL connection reuse
7. **Rate limiting** — protect the API from abuse (DRF throttling or nginx level)

## Project Structure

```
├── backend/
│   ├── rides/              # Models, views, serializers, permissions
│   ├── tests/              # pytest suite (~34 tests)
│   ├── sql/       # SQL: schema, seed data, bonus report
│   ├── wingz/              # Django project settings
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/components/     # React components
│   ├── Dockerfile          # Multi-stage: npm build → nginx
│   └── nginx.conf          # Reverse proxy /api/ → backend
├── docs/artifacts/         # Phase 0 analysis and specs
├── docker-compose.yml
├── Makefile
└── README.md
```

## Development Approach

This project was built using a **structured AI-assisted development workflow**:

1. **Phase 0 — Analysis:** Generated implementation-ready specs under `docs/artifacts/`
   (data models, API contracts, query strategies, test scenarios) before writing any code.
2. **Phase 1 — Backend TDD:** Each module was implemented test-first, consuming the
   Phase 0 artifacts as the single source of truth.
3. **Phase 2 — Integration:** Docker orchestration, frontend, documentation.

The artifacts in `docs/artifacts/` demonstrate how I approach AI-assisted development:
specifications first, then methodical implementation — ensuring the AI operates from
well-defined constraints rather than open-ended prompts.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| MySQL not ready | `docker compose logs db` — wait for "ready for connections" |
| Schema not loaded | Init scripts run only once. Reset: `docker compose down -v` |
| Frontend 502 | Backend still starting — wait 10s |
| Tests fail on math | SQLite math fixtures registered in `conftest.py` (autouse) |
| Permission denied on API | Need admin user with `role='admin'` exactly |
```

### `backend/README.md`
Shorter developer-focused README:
- Local dev setup (venv, pip install, pytest)
- Environment variables
- API endpoint with all params
- Performance notes
- Linting with ruff

### `frontend/README.md`
Brief:
- `npm install && npm run dev`
- Component list
- Vite proxy for dev, nginx for production

**COMMIT.**

---

## Step 4: Makefile + Final Cleanup

**Include in the README commit: "docs: comprehensive README with architecture decisions and Makefile"**

### `Makefile` (project root)
```makefile
.PHONY: test lint up down logs restart seed-check bonus-sql clean

test:
	cd backend && pytest -v

lint:
	cd backend && ruff check .

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down && docker compose up -d

logs:
	docker compose logs -f

seed-check:
	docker compose exec db mysql -u appuser -papppass wingz_db \
		-e "SELECT COUNT(*) AS rides FROM rides; \
		    SELECT COUNT(*) AS events FROM ride_events; \
		    SELECT COUNT(*) AS users FROM users;"

bonus-sql:
	docker compose exec db mysql -u appuser -papppass wingz_db \
		< backend/sql/bonus_report.sql

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

### `.env.example` (project root)
```env
MYSQL_ROOT_PASSWORD=rootpass
MYSQL_DATABASE=wingz_db
MYSQL_USER=appuser
MYSQL_PASSWORD=apppass
DB_HOST=db
DB_PORT=3306
DB_USER=appuser
DB_PASSWORD=apppass
DB_NAME=wingz_db
```

**This is part of the README commit — do not make a separate commit.**

---

## Integration Verification

Run the full stack and verify everything:

```bash
# Build and start
docker compose up -d --build

# Wait for MySQL
sleep 30

# Verify all services running
docker compose ps

# Test API (BasicAuth: admin@wingz.com / adminpass123)
curl -s -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/ | python3 -m json.tool
curl -s -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?status=pickup" | python3 -m json.tool
curl -s -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?sort_by=pickup_time" | python3 -m json.tool
curl -s -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?sort_by=distance&latitude=14.6&longitude=-90.5" | python3 -m json.tool
curl -s -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?page=1&page_size=5" | python3 -m json.tool

# Test frontend (auth is hardcoded in frontend for this assessment)
curl -s http://localhost:8080/ | head -5
curl -s -u admin@wingz.com:adminpass123 http://localhost:8080/api/rides/ | python3 -m json.tool

# Test seed data
make seed-check

# Test bonus SQL
make bonus-sql

# Run backend tests
make test
make lint
```

---

## Final Git Log

```bash
git log --oneline
```

Expected (~15 commits total):
```
 docs: comprehensive README with architecture decisions and Makefile
 frontend: React app with ride list, filters, pagination
 docker: Compose + backend Dockerfile + healthchecks
 bonus: raw SQL for trips > 1hr with edge case handling
 perf: assertNumQueries tests proving 2-3 query target
 sorting: pickup_time and Haversine distance with DB-level sort
 api: ride list endpoint with pagination and filtering
 serializers: nested rider/driver + todays_ride_events
 auth: admin-only permission class + BasicAuth with tests
 schema: MySQL DDL + intentional seed data for edge cases
 models: User, Ride, RideEvent with custom PKs matching spec
 scaffold: Django project + rides app + test config
 docs: implementation specs and feature artifacts
 init: project structure, conventions, and architecture decisions
```

**~15 commits telling a complete story** from analysis → foundation → core features → optimization → infrastructure → documentation.

---

## Submission Checklist

### Functionality
- [ ] `GET /api/rides/` returns paginated rides with nested rider, driver, todays_ride_events
- [ ] Filter by status works
- [ ] Filter by rider_email works
- [ ] Sort by pickup_time works
- [ ] Sort by distance works (with coordinates)
- [ ] Distance sort without coords → 400
- [ ] BasicAuth with admin credentials works: `curl -u admin@wingz.com:adminpass123`
- [ ] Admin gets 200, non-admin gets 403, unauthenticated gets 401
- [ ] Pagination works correctly

### Performance
- [ ] ≤ 3 DB queries for ride list (proven by test)
- [ ] No N+1 queries (proven by test)
- [ ] Prefetch filters on created_at (proven by SQL inspection test)
- [ ] Distance sort happens in DB, not Python

### Code Quality
- [ ] `ruff check .` → 0 errors
- [ ] Models, serializers, views, permissions in separate modules
- [ ] Comments only on non-obvious "why" decisions
- [ ] No over-engineering

### Testing
- [ ] ~36 tests, all passing
- [ ] Performance tests prove query count
- [ ] Distance sort tested with real coordinates
- [ ] Auth tested for exact role matching and BasicAuth flow

### Docker
- [ ] `docker compose up` starts all 3 services
- [ ] MySQL healthcheck gates backend startup
- [ ] Schema + seed data load automatically
- [ ] Frontend proxies /api/ to backend

### Documentation
- [ ] README has Quick Start (< 4 commands)
- [ ] README has Architecture section with diagram
- [ ] README has Design Decisions (performance, Haversine, auth)
- [ ] README has "What I'd Change for Production"
- [ ] README has Bonus SQL with edge case explanation
- [ ] README has "Development Approach" section referencing AI-assisted workflow
- [ ] Commit history tells a progression story

### Bonus
- [ ] SQL query runs: `make bonus-sql`
- [ ] Handles multiple events per ride (MIN/MAX)
- [ ] Boundary: exactly 60 min NOT counted
- [ ] Output format matches sample
