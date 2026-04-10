# Phase 2 — React Frontend (ride1)

## Role

You are a **Senior Full-Stack Engineer** building the frontend companion for the Wingz ride management API. The backend (`ride0`) is already complete, tested, and deployed. This phase delivers a clean, functional React SPA that consumes that API — as a **separate, sibling project** at `wingz/ride1`.

## Mission

Deliver a React + Vite frontend that demonstrates the ride list API and deploys to the **same EC2 instance** currently running the backend:

1. **Scaffold** a new Vite + React project at `/home/jl2/work/wingz/ride1`
2. **Wire up** the ride list with filters, sorting, and pagination against the ride0 API
3. **Keep it focused** — functional UI, no decorative flourishes, no CSS frameworks
4. **Deploy to EC2** — same box as ride0, served by nginx on port 80 alongside the gunicorn API
5. **Ship it cleanly** — passes lint, builds without warnings, sensible commit history

The backend source is not in scope. Do not touch `/home/jl2/work/wingz/ride0/backend/` during this phase except to read the API contract. The backend **runtime** on EC2 (`wingz-api.service`) stays exactly as it is — the new deployment only adds nginx in front of it.

## Context

### Backend location
- **Source code** (read-only reference): `/home/jl2/work/wingz/ride0/backend/`
- **API contract**: `/home/jl2/work/wingz/ride0/docs/artifacts/features/ride-list-api/api-contract.md`
- **Deployed instance**: `http://107.23.122.99` (validated — see `ride0/tests/test_deployed_api.sh`)
- **Local dev instance**: `http://localhost:8000` (run via `cd ride0/backend && python manage.py runserver`)

### EC2 runtime (target deployment host)
The deployed backend runs on an EC2 instance as a systemd service:

- **Service**: `wingz-api.service` (systemd)
- **Process**: `gunicorn --bind 0.0.0.0:8000 wingz.wsgi:application`
- **App directory**: `/home/ec2-user/production/wingz/`
- **SSH user**: `ec2-user`
- **OS**: Amazon Linux (assume `dnf`/`yum` for package install)
- **Port 80 → 8000**: currently routed by some mechanism (iptables PREROUTING rule or similar) — `http://107.23.122.99/api/rides/` works without a `:8000` suffix. This routing **must be replaced** by the nginx reverse proxy introduced in Step 6.

The frontend deploy will **add** nginx and **remove** the port 80 → 8000 shortcut, but will not change gunicorn or the systemd unit.

### Seed credentials (deterministic — defined in `ride0/backend/rides/management/commands/seed_db.py`)
- Email: `admin@wingz.com`
- Password: `adminpass123`
- Role: `admin`

### Seed data expectations
- 24 rides total, 8 per status (`en-route`, `pickup`, `dropoff`), 8 per rider
- GPS zones in Guatemala City for distance-sort testing

### API endpoint summary
`GET /api/rides/` — HTTP Basic Auth, admin role required. Query params:

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | `en-route`, `pickup`, `dropoff` |
| rider_email | string | Exact match |
| sort_by | string | `pickup_time` or `distance` |
| latitude | float | Required when `sort_by=distance` |
| longitude | float | Required when `sort_by=distance` |
| page | int | Default 1 |
| page_size | int | Default 10, max 100 |

Response shape: `{ count, next, previous, results: [{ id_ride, status, id_rider: {...}, id_driver: {...}, pickup_time, pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude, todays_ride_events: [...] }] }`

---

## Project Location

```
/home/jl2/work/wingz/
├── ride0/          # Existing backend — DO NOT MODIFY
└── ride1/          # New frontend — created in this phase
```

Start from an empty `ride1/` directory. The scaffolding command creates it.

---

## Commit Strategy

Work inside `ride1/` as its own git repository. Initialize it as a fresh repo — do not nest it inside ride0's git history.

```
Commit 1: "scaffold: Vite + React project with .gitignore"
Commit 2: "api: fetchRides service with Basic Auth and env-driven base URL"
Commit 3: "ui: RideTable, Pagination, and App orchestrator with filters"
Commit 4: "style: functional layout, status badges, error states"
Commit 5: "deploy: nginx reverse proxy + GitHub Actions workflow for EC2"
Commit 6: "docs: README with setup, env config, and deployment notes"
```

Adjust as needed — the point is a readable commit history, not rigid adherence to these exact messages.

---

## Step 1: Scaffold

**Commit: "scaffold: Vite + React project with .gitignore"**

From `/home/jl2/work/wingz/`:

```bash
npm create vite@latest ride1 -- --template react
cd ride1
npm install
git init
```

### Target structure
```
ride1/
├── src/
│   ├── components/
│   │   ├── RideTable.jsx       # Table of rides with status badges
│   │   └── Pagination.jsx      # Prev/Next + page info
│   ├── services/
│   │   └── api.js              # fetchRides() wrapper
│   ├── App.jsx                 # Orchestrator: filters + table + pagination
│   ├── App.css                 # Functional styles
│   └── main.jsx
├── .env.example                # VITE_API_BASE_URL, VITE_ADMIN_EMAIL, VITE_ADMIN_PASSWORD
├── .env.local                  # Gitignored — local dev overrides
├── .gitignore                  # node_modules, dist, .env.local
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

**Verify:** `npm run dev` launches successfully on port 5173 (even with default Vite template).

**COMMIT.**

---

## Step 2: API Service

**Commit: "api: fetchRides service with Basic Auth and env-driven base URL"**

### `vite.config.js`
Use the Vite dev proxy to route `/api/` requests to the backend, avoiding CORS entirely during local development:

```javascript
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
```

### `.env.example`
```env
# Backend base URL — where Vite dev proxy forwards /api requests
VITE_API_BASE_URL=http://localhost:8000

# Seed admin credentials from ride0/backend/rides/management/commands/seed_db.py
VITE_ADMIN_EMAIL=admin@wingz.com
VITE_ADMIN_PASSWORD=adminpass123
```

Copy to `.env.local` for local runs. Point `VITE_API_BASE_URL` at `http://107.23.122.99` to hit the deployed instance instead of local.

### `src/services/api.js`
```javascript
const API_BASE = '/api'

const email = import.meta.env.VITE_ADMIN_EMAIL || 'admin@wingz.com'
const password = import.meta.env.VITE_ADMIN_PASSWORD || 'adminpass123'
const AUTH_HEADER = 'Basic ' + btoa(`${email}:${password}`)

export async function fetchRides(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) query.append(k, v)
  })
  const res = await fetch(`${API_BASE}/rides/?${query}`, {
    headers: { Authorization: AUTH_HEADER },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || data.detail || `HTTP ${res.status}`)
  }
  return res.json()
}
```

**Note on credentials in env vars:** Vite inlines `VITE_*` variables into the client bundle — anyone inspecting the built JS can read them. This is acceptable for an assessment demo with seed credentials, but a production app would use a real login flow and token storage. Call this out in the README.

**Verify:** Import `fetchRides` in a scratch console in the browser and confirm it returns data.

**COMMIT.**

---

## Step 3: Components + Orchestrator

**Commit: "ui: RideTable, Pagination, and App orchestrator with filters"**

### `src/App.jsx`

Keep filters inline — they're part of the orchestrator, not a separate component.

```jsx
import { useState, useEffect } from 'react'
import { fetchRides } from './services/api'
import RideTable from './components/RideTable'
import Pagination from './components/Pagination'
import './App.css'

const PAGE_SIZE = 10

export default function App() {
  const [rides, setRides] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [status, setStatus] = useState('')
  const [riderEmail, setRiderEmail] = useState('')
  const [sortBy, setSortBy] = useState('')

  async function load(p = page) {
    setLoading(true)
    setError('')
    try {
      const params = { page: p, page_size: PAGE_SIZE }
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
        <input
          placeholder="Rider email"
          value={riderEmail}
          onChange={e => setRiderEmail(e.target.value)}
        />
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
          <Pagination
            count={count}
            page={page}
            pageSize={PAGE_SIZE}
            onChange={p => { setPage(p); load(p) }}
          />
        </>
      )}
    </div>
  )
}
```

### `src/components/RideTable.jsx`
- HTML `<table>` with columns: ID, Status (color-coded badge), Rider, Driver, Pickup Time, Events (count from `todays_ride_events`)
- Status badge colors inline via `style`: blue=`en-route`, amber=`pickup`, green=`dropoff`
- Empty state: "No rides match these filters."
- No expandable rows, no CSS Grid cards, no icons

### `src/components/Pagination.jsx`
- Previous/Next buttons, disabled at boundaries
- "Page X of Y" text between them
- `totalPages = Math.max(1, Math.ceil(count / pageSize))`

**Verify:** `npm run dev`, load the page, confirm:
- Table renders seed data
- Status filter narrows to 8 rows per status
- Rider email filter narrows to 8 rows per rider
- Sort by pickup_time reorders
- Pagination Prev/Next walk through the 24 rows

**COMMIT.**

---

## Step 4: Styling

**Commit: "style: functional layout, status badges, error states"**

### `src/App.css`

Minimal, functional. No CSS framework, no decorative elements.

- Centered `.app` container, ~1000px max-width, comfortable padding
- `.filters` as a horizontal flex row with consistent gap
- `<table>` with clean borders, zebra striping, left-aligned headers
- Status badges: small rounded rectangle, white text, bold, 12px padding
- `.error` in red with a light red background
- Loading state: simple italic text (no spinner)

Delete the default Vite CSS (`index.css` styles, `App.css` template content, logo assets) — leave a clean slate.

**Verify:** Visual inspection in browser — the page should look like a no-nonsense internal tool, not a marketing page.

**COMMIT.**

---

## Step 5: EC2 Deployment

**Commit: "deploy: nginx reverse proxy + GitHub Actions workflow for EC2"**

The frontend deploys to the **same EC2 instance** that already runs `wingz-api.service`. The target topology is nginx on port 80 serving the static build and proxying `/api/` to `localhost:8000`.

### ⚠️ Pre-flight — STOP before making any infrastructure changes

Before running any commands on EC2, SSH in and **investigate the current state**:

```bash
ssh ec2-user@107.23.122.99
sudo systemctl status wingz-api          # Confirm gunicorn is healthy
sudo ss -tlnp | grep -E ':(80|8000)'      # What's listening on 80 and 8000?
sudo iptables -t nat -L PREROUTING -n    # Is there a port forward rule?
which nginx && nginx -v || echo "nginx not installed"
ls /etc/nginx/ 2>/dev/null || echo "no nginx config dir"
```

**Report findings to the user** (what's on port 80, how 80→8000 works today, whether nginx is already present) **and wait for approval** before proceeding. This matches the global rule: when something is unclear or a destructive change is needed, stop and ask.

Only after approval, continue with the steps below.

### `ride1/deploy/nginx-wingz.conf`

Commit this file to the repo as the source of truth for the nginx site config. The GitHub Actions workflow copies it to `/etc/nginx/conf.d/wingz.conf` on the EC2 host.

```nginx
server {
    listen 80 default_server;
    server_name _;

    root /home/ec2-user/production/ride1/dist;
    index index.html;

    # SPA fallback — any non-file path returns index.html so client-side
    # routing works even if a user refreshes a deep link.
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Reverse proxy /api/ to gunicorn. Same origin for the browser → no CORS.
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Cache static assets aggressively — Vite produces hashed filenames.
    location ~* \.(?:js|css|woff2?|svg|png|jpg|jpeg|gif|ico)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

### `.github/workflows/deploy.yaml` (in `ride1/`)

Build on CI (not on EC2 — avoids installing Node on the production host) and ship the `dist/` directory over SSH.

```yaml
name: Deploy Frontend to EC2

on:
  push:
    branches: [main]
  pull_request:
    types: [opened, reopened, synchronize, closed]
    branches: [main, dev]

jobs:
  build:
    name: Lint & Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: dist/
          retention-days: 1

  deploy_prod:
    name: Deploy PROD
    needs: build
    if: |
      github.event_name == 'push' ||
      (github.event.pull_request.base.ref == 'main' &&
       github.event.action == 'closed' &&
       github.event.pull_request.merged == true)
    runs-on: ubuntu-latest
    environment: prod
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: frontend-dist
          path: dist/

      - name: Copy dist + nginx config to EC2
        uses: appleboy/scp-action@master
        with:
          host: ${{ secrets.EC2_HOST_PROD }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          source: "dist/*,deploy/nginx-wingz.conf"
          target: "/home/ec2-user/ride1-staging"
          strip_components: 0

      - name: Install nginx + activate new build
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST_PROD }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            set -e
            # One-time install (idempotent)
            if ! command -v nginx >/dev/null 2>&1; then
              sudo dnf install -y nginx
              sudo systemctl enable nginx
            fi

            # Remove any stale port 80 → 8000 forwarding rule left from the
            # previous deployment. Safe to run even if no rule exists.
            sudo iptables -t nat -F PREROUTING || true

            # Atomically swap in the new build
            sudo mkdir -p /home/ec2-user/production/ride1
            sudo rm -rf /home/ec2-user/production/ride1/dist
            sudo mv /home/ec2-user/ride1-staging/dist /home/ec2-user/production/ride1/dist
            sudo chown -R ec2-user:ec2-user /home/ec2-user/production/ride1

            # Install the nginx site config
            sudo cp /home/ec2-user/ride1-staging/deploy/nginx-wingz.conf \
                    /etc/nginx/conf.d/wingz.conf
            # Disable the default welcome server if Amazon Linux shipped one
            sudo rm -f /etc/nginx/conf.d/default.conf

            # Validate and reload — fail loudly if the config is bad
            sudo nginx -t
            sudo systemctl restart nginx

            # Clean up staging dir
            rm -rf /home/ec2-user/ride1-staging

            # Smoke test both the frontend and the proxied API
            curl -sf http://localhost/ -o /dev/null -w "FRONTEND %{http_code}\n"
            curl -sf -u admin@wingz.com:adminpass123 \
              http://localhost/api/rides/ -o /dev/null -w "API %{http_code}\n"
```

### Required GitHub Actions secrets (in `ride1` repo settings)

| Secret | Description |
|--------|-------------|
| `EC2_HOST_PROD` | Same value as ride0's secret — `107.23.122.99` |
| `EC2_SSH_KEY` | Same SSH private key as ride0 |

### Post-deploy sanity checks

After the first successful run, verify from a local machine:

```bash
curl -sf http://107.23.122.99/ -o /dev/null -w "%{http_code}\n"
curl -sf -u admin@wingz.com:adminpass123 http://107.23.122.99/api/rides/ | jq '.count'
bash /home/jl2/work/wingz/ride0/tests/test_deployed_api.sh http://107.23.122.99
```

The ride0 validation script must still pass end-to-end — the nginx reverse proxy should be transparent to it.

**COMMIT.**

---

## Step 6: README

**Commit: "docs: README with setup, env config, and deployment notes"**

### `ride1/README.md`

```markdown
# Wingz Ride Management — Frontend

React + Vite SPA for the Wingz ride management API. Companion to the
[`ride0`](../ride0) backend.

## Quick Start

```bash
# Prerequisites: Node 18+, npm
cp .env.example .env.local
# Edit .env.local if you want to point at a deployed backend

npm install
npm run dev
# Open http://localhost:5173
```

By default, the Vite dev proxy routes `/api` to `http://localhost:8000` (local
ride0 backend). To hit the deployed instance instead:

```env
VITE_API_BASE_URL=http://107.23.122.99
```

## Features

- Paginated ride list with nested rider, driver, and today's events
- Filter by status (`en-route`, `pickup`, `dropoff`)
- Filter by rider email (exact match)
- Sort by pickup time
- Prev/Next pagination with page count

## Architecture

### Local development
```
┌──────────────┐   /api proxy   ┌──────────────┐
│  React SPA   │───────────────▶│ ride0 Django │
│  (Vite 5173) │                │ (port 8000)  │
└──────────────┘                └──────────────┘
```

The Vite dev server proxies `/api/*` to the backend, so the browser never makes
a cross-origin request — no CORS configuration needed.

### Production (EC2, single instance)
```
           http://107.23.122.99
                   │
                   ▼
        ┌──────────────────────┐
        │   nginx :80          │
        │   ┌──────────────┐   │
        │   │ / → dist/    │   │  (static React build)
        │   │ /api/ → :8000│   │  (reverse proxy)
        │   └──────────────┘   │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  gunicorn :8000      │  (wingz-api.service)
        │  Django + DRF        │
        └──────────────────────┘
```

Same origin for frontend and API — no CORS. nginx replaces the previous
port 80 → 8000 shortcut. The gunicorn systemd service is untouched.

## Project Structure

```
ride1/
├── src/
│   ├── components/
│   │   ├── RideTable.jsx    # Ride rows with status badges
│   │   └── Pagination.jsx   # Prev/Next controls
│   ├── services/
│   │   └── api.js           # fetchRides() with Basic Auth
│   ├── App.jsx              # Orchestrator with inline filters
│   ├── App.css              # Functional styles
│   └── main.jsx
├── deploy/
│   └── nginx-wingz.conf     # nginx site config shipped to EC2
├── .github/workflows/
│   └── deploy.yaml          # Build on CI, ship dist/ via SSH
├── .env.example
├── vite.config.js
└── package.json
```

## Deployment

The frontend deploys to the **same EC2 instance** that runs the ride0 backend.
`nginx` serves the static build on port 80 and reverse-proxies `/api/` to the
`gunicorn` service already listening on `127.0.0.1:8000`.

On every push to `main`, GitHub Actions:

1. Runs `npm ci && npm run lint && npm run build`
2. SCPs `dist/` and `deploy/nginx-wingz.conf` to the EC2 host
3. Installs nginx if missing (one-time, idempotent)
4. Swaps in the new build at `/home/ec2-user/production/ride1/dist/`
5. Copies the nginx config to `/etc/nginx/conf.d/wingz.conf` and reloads
6. Smoke-tests both the root path and a proxied API call

The `wingz-api.service` systemd unit is never touched — nginx simply sits in
front of it.

## Authentication

The backend uses HTTP Basic Auth with admin role. Seed credentials come from
`ride0/backend/rides/management/commands/seed_db.py`:

- Email: `admin@wingz.com`
- Password: `adminpass123`

These are injected into the bundle via `VITE_*` env vars. **This is an
assessment convenience** — `VITE_*` variables are inlined into the client
bundle at build time, so anyone inspecting the JS can read them. A production
frontend would implement a real login flow against a token endpoint.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server on port 5173 |
| `npm run build` | Build production bundle to `dist/` |
| `npm run preview` | Preview the production build |
| `npm run lint` | Run ESLint (from Vite template) |

## What I'd Change for Production

1. **Real auth flow** — login form → token endpoint → httpOnly cookie or secure storage
2. **Request caching** — React Query or SWR to dedupe, cache, and revalidate
3. **Debounced filter input** — avoid a request on every keystroke for rider_email
4. **URL state** — sync filters and page to query string for shareable links
5. **Error boundaries** — graceful recovery from unexpected API shape changes
6. **Type safety** — TypeScript with generated types from the DRF schema
7. **Accessibility pass** — keyboard nav, ARIA labels, focus management
```

**COMMIT.**

---

## Verification

Run the full proof cycle before declaring done:

```bash
cd /home/jl2/work/wingz/ride1

# Lint (uses ESLint config from Vite template)
npm run lint

# Production build must succeed with zero warnings
npm run build

# Dev server smoke test
npm run dev
# Manually verify in browser:
#   - Table loads 10 rows (page 1 of 3)
#   - Status=pickup → 8 rows, 1 page
#   - Rider email filter → 8 rows
#   - Sort by pickup_time → rows reorder
#   - Prev/Next walks through pages
#   - Invalid filter → error state renders, not a blank page
```

### Against the deployed backend (pre-deploy)

```bash
# Point the dev server at the live EC2 backend to sanity-check CORS, auth,
# and response shape BEFORE shipping anything to EC2.
echo 'VITE_API_BASE_URL=http://107.23.122.99' > .env.local
npm run dev
# Re-run all manual checks above
```

### Post-deploy (end-to-end on EC2)

```bash
# Frontend should return the SPA shell
curl -sf http://107.23.122.99/ | grep -q '<div id="root">' && echo "SPA OK"

# API should be reachable through the nginx proxy (same origin, no :8000)
curl -sf -u admin@wingz.com:adminpass123 http://107.23.122.99/api/rides/ | jq '.count'

# Full regression against the ride0 validation script
bash /home/jl2/work/wingz/ride0/tests/test_deployed_api.sh http://107.23.122.99
```

If the ride0 validation script fails after the nginx cutover, the reverse proxy is misbehaving — do **not** patch ride0 to "fix" it. Debug nginx instead (`sudo nginx -t`, `sudo tail /var/log/nginx/error.log`).

---

## Submission Checklist

### Functionality
- [ ] Ride list loads on page open
- [ ] Status filter works for all three values
- [ ] Rider email filter works (exact match)
- [ ] Sort by pickup_time reorders results
- [ ] Pagination Prev/Next works, disabled at boundaries
- [ ] Error state renders a readable message (not a blank page)
- [ ] Loading state visible between requests

### Code quality
- [ ] `npm run lint` → 0 errors
- [ ] `npm run build` → 0 warnings
- [ ] Components in separate files under `src/components/`
- [ ] No unused Vite template leftovers (logos, default CSS, counter demo)
- [ ] Comments only on non-obvious decisions

### UX
- [ ] Status badges color-coded and readable
- [ ] Filter bar visually grouped
- [ ] Table doesn't overflow on 1280px viewport
- [ ] Empty state has helpful copy

### Deployment
- [ ] `deploy/nginx-wingz.conf` committed and documented
- [ ] `.github/workflows/deploy.yaml` builds on CI (not on EC2) and ships `dist/`
- [ ] `EC2_HOST_PROD` and `EC2_SSH_KEY` secrets added to the ride1 repo
- [ ] Pre-flight EC2 state investigation completed and approved before cutover
- [ ] Stale iptables PREROUTING rule removed as part of deploy
- [ ] nginx serves `http://107.23.122.99/` (frontend) and `/api/` (proxied)
- [ ] `ride0/tests/test_deployed_api.sh http://107.23.122.99` still passes post-cutover
- [ ] `wingz-api.service` systemd unit is unchanged (confirm with `systemctl cat wingz-api`)

### Documentation
- [ ] README has Quick Start (< 4 commands)
- [ ] README explains env var config and deployed URL override
- [ ] README notes the Basic Auth credential tradeoff
- [ ] README has both dev and production architecture diagrams
- [ ] README has a Deployment section describing the nginx + CI flow
- [ ] README includes "What I'd Change for Production"

### Git
- [ ] `ride1/` is its own repo (not nested in ride0's git history)
- [ ] 5–6 atomic commits with clear messages
- [ ] `.env.local` is gitignored
- [ ] `node_modules/` and `dist/` are gitignored

---

## Constraints

- **Do not modify ride0 source.** Read-only reference for the API contract and credentials.
- **Do not touch the `wingz-api.service` systemd unit.** nginx sits in front of it; gunicorn stays exactly as ride0 deployed it.
- **Do not modify ride0's deploy workflow.** The new `.github/workflows/deploy.yaml` lives in the ride1 repo only.
- **Do not scaffold a full design system.** No Tailwind, no Material UI, no styled-components. Plain CSS is sufficient and faster.
- **Do not add state management libraries.** `useState` + `useEffect` is enough for this scope.
- **Do not add TypeScript.** The assessment is about full-stack judgment, not type gymnastics. Call TS out as a production improvement in the README instead.
- **Do not run destructive EC2 commands without the pre-flight check.** SSH in, report state, wait for approval, then proceed.
- **If something fails and you're tempted to work around it, STOP and ask.** Do not silently mock the API, fake data, disable a failing check, or bypass nginx.
