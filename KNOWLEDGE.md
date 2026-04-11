# KNOWLEDGE.md — Persistent Insights

Debugging insights, environment quirks, and dependency gotchas that survive across sessions. Updated by `/wrap`, read by `/recover`.

## Troubleshooting Patterns

### SQLite math functions for Haversine tests
- **Context**: Running `pytest -v` with distance sorting tests
- **Problem**: SQLite doesn't have `RADIANS`, `SIN`, `COS`, `ASIN`, `SQRT`, `POWER` functions natively
- **Solution**: `conftest.py` has an `autouse` fixture `_register_sqlite_math` that registers Python `math` module functions into SQLite connection
- **Prevention**: Always check this fixture exists when adding new RawSQL that uses math functions

## Environment Quirks

### Database switching via settings.py
- `pytest` in `sys.modules` → SQLite in-memory (automatic for tests)
- `USE_SQLITE=1` env var → SQLite file-based (for dev/EC2 deployment)
- Neither → MySQL (production default)

## Dependencies & Gotchas

### PyMySQL + cryptography
- `pymysql` requires `cryptography` package for MySQL 8.0 authentication
- Both pinned in `requirements.txt`

### Deploy workflow missing seed data
- **Context**: Deployed API returned "Invalid credentials" for all requests
- **Problem**: `deploy.yaml` ran `migrate` but never loaded seed data — tables were empty
- **Solution**: Created `seed_db` management command (ORM-based, idempotent) and added `python manage.py seed_db` after migrate in both dev/prod deploy jobs
- **Prevention**: Any new data requirements need a corresponding seed command update, not just SQL file changes

### nginx can't serve static files from `/home/ec2-user` on Amazon Linux
- **Context**: Deploying the ride1 React SPA to EC2, serving `dist/` via nginx on port 80
- **Problem**: nginx returned `HTTP 500` with `[crit] stat() "/home/ec2-user/production/ride1/dist/" failed (13: Permission denied)` and `rewrite or internal redirection cycle` in the error log. The files existed and were owned `ec2-user:ec2-user`, but the `nginx` worker user couldn't traverse into `/home/ec2-user` because that directory is mode `0700` by default on Amazon Linux 2023. SELinux was in permissive mode so it wasn't contributing.
- **Solution**: Serve static files from `/usr/share/nginx/html/ride1/dist/` instead. That path is root-owned, world-readable (world-traversable), and part of nginx's default search tree. Update the nginx `root` directive and the deploy script's `mv` target together.
- **Prevention**: Never set an nginx `root` inside `/home/<user>/` on a multi-user box. Standard places for web roots: `/usr/share/nginx/html/`, `/var/www/`, or `/srv/`. If serving from a home dir is unavoidable, it requires either `chmod 0755 ~` (weakens security) or ACLs (fragile).

### Django `ALLOWED_HOSTS` + in-box smoke tests
- **Context**: Post-deploy smoke test in GitHub Actions SSH script: `curl http://localhost/` against the EC2 box
- **Problem**: Curl returned HTTP 400 from inside the EC2 box even though the API worked perfectly from the outside world. Django's `ALLOWED_HOSTS` contained the public IP (`107.23.122.99`) but not `localhost` or `127.0.0.1`, so any request with `Host: localhost` got rejected with "Bad Request (400): Disallowed Host".
- **Solution**: Always pass an explicit `-H "Host: <public-ip>"` header in in-box smoke tests so the request looks like real user traffic. In the GitHub Actions workflow, use `${{ secrets.EC2_HOST_PROD }}` as the header value so the host is sourced from the same secret as the SSH target.
- **Prevention**: When writing smoke tests that run from inside a box behind nginx, remember that nginx forwards the incoming `Host` header unchanged via `proxy_set_header Host $host;`. If the backend validates hosts, your test Host header must be in the allowed list.

### SQLite and MySQL don't reset AUTO_INCREMENT on DELETE
- **Context**: The `seed_db` management command wipes and rebuilds the dataset on every run (`User.objects.all().delete()` cascades to rides + events). Running it twice in a row.
- **Problem**: After the second run, ride IDs were 121-144 instead of 1-24. SQLite's `sqlite_sequence` table persists across DELETEs; MySQL's `AUTO_INCREMENT` counter also doesn't reset on DELETE (only on TRUNCATE, and TRUNCATE CASCADE doesn't work the way you'd think either). The UI then shows `#121, #122, ...` which looks bad on a demo.
- **Solution**: After the delete, issue vendor-specific raw SQL to reset the counter. SQLite: `DELETE FROM sqlite_sequence WHERE name IN ('users', 'rides', 'ride_events')`. MySQL: `ALTER TABLE <t> AUTO_INCREMENT = 1` for each table. Detect the vendor via `django.db.connection.vendor`. Django has no built-in helper.
- **Prevention**: Any Django management command that wipes and rebuilds auto-increment PKs needs an explicit sequence reset. The wipe itself is not enough.

### Ride status has no enforced enum — it's a free-form CharField
- **Context**: Considering a rename of the status value `pickup` → `to-pickup` and wondering whether a migration was needed
- **Problem**: Had to trace where status was validated to know if renaming required schema changes
- **Solution**: `rides/models.py` defines `status = models.CharField(max_length=50)` with **no `choices=` constraint, no DB CHECK, no DRF serializer validation**. The three canonical values (`en-route`, `to-pickup`, `dropoff`) are enforced only by convention — by seed_db, by the frontend dropdown, and by the regression script. Renaming is a pure text replacement across those locations; no migration required.
- **Prevention**: When a Django model field has no `choices=`, the "valid values" are a documentation/convention problem, not a schema problem. Grep for literal strings across tests + frontend + regression + seed before declaring the rename complete.

## Dev Tooling

### Vite 8 ESLint flat config only gives `globals.browser`
- **Context**: Added `loadEnv(mode, process.cwd(), '')` to `vite.config.js` in a fresh `npm create vite@latest --template react` scaffold
- **Problem**: `npm run lint` failed with `'process' is not defined  no-undef` on `vite.config.js`. Vite's default `eslint.config.js` (flat config) declares `languageOptions.globals: globals.browser` for `**/*.{js,jsx}`, which doesn't include Node globals like `process`.
- **Solution**: Add a narrow file-scoped config block at the end of `eslint.config.js`:
  ```js
  {
    files: ['vite.config.js', 'eslint.config.js'],
    languageOptions: { globals: globals.node },
  }
  ```
- **Prevention**: Any Node-only config file (vite.config.js, postcss.config.js, eslint.config.js itself) in a Vite-scaffolded project needs an explicit node globals override — flat config doesn't auto-detect.
