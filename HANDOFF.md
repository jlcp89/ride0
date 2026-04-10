# Handoff

## 2026-04-10 | session 5

### Intent
Execute `docs/prompts/PHASE_2_FRONTEND.md` against the existing `wingz/ride1` repo — scaffold a React + Vite SPA for the ride list API, wire up filters/sort/pagination, and deploy alongside ride0 on the same EC2 instance behind an nginx reverse proxy.

### Decisions
- **Scaffolded via temp dir + `cp -a` instead of `npm create vite@latest .`** — because `ride1/` was already an initialized git repo with `.git/` and `.claude/settings.local.json` that had to be preserved. Scaffolding into a temp directory and then copying contents with `cp -a` avoids any "directory not empty" prompt and guarantees existing dotfiles/repo state are left alone.
- **Served the SPA from `/usr/share/nginx/html/ride1/dist` (not `/home/ec2-user/...`)** — because `/home/ec2-user` is mode `0700` on Amazon Linux and the `nginx` worker user can't `stat()` anything inside it. First deploy attempt failed with `Permission denied` + `rewrite or internal redirection cycle` errors. `/usr/share/nginx/html` is root-owned, world-readable, and part of nginx's default search tree — no chmod or SELinux contexts needed.
- **Explicitly `rm -f /etc/nginx/conf.d/wingz-api.conf` in the deploy script** — because the ride0 deploy had previously installed that file with `listen 80`, and adding `wingz.conf` (also `listen 80 default_server`) without removing the old one would make `nginx -t` fail with a duplicate listener. Cleaner than overwriting in place because the new file reflects the new purpose (SPA + /api/ proxy, not everything-to-gunicorn).
- **Dropped the `iptables -t nat -F PREROUTING` line from deploy.yaml** — because pre-flight showed `sudo: iptables: command not found` on Amazon Linux 2023. The original PHASE_2_FRONTEND.md prompt assumed iptables handled the port 80 → 8000 forwarding, but the actual mechanism turned out to be nginx (already installed) routing via `wingz-api.conf`.
- **In-box smoke tests use `-H "Host: ${{ secrets.EC2_HOST_PROD }}"`** — because Django's `ALLOWED_HOSTS` accepts the public IP but not `localhost`, so a plain `curl http://localhost/...` from inside the EC2 box returns HTTP 400 "Disallowed Host". Passing the public IP as the Host header simulates real user traffic through nginx.
- **Added `globals.node` override in `eslint.config.js`** for `vite.config.js` and `eslint.config.js` themselves — because Vite 8's default flat ESLint config only exposes `globals.browser`, and `loadEnv(mode, process.cwd(), '')` in the Vite config triggered `'process' is not defined`. Narrow file-scoped override is the idiomatic Vite fix.
- **`ride1` is still a single-origin deploy** (nginx serves `/` from static + proxies `/api/` to gunicorn on the same box) — confirmed by the 49/0/0 regression pass of `ride0/tests/test_deployed_api.sh http://107.23.122.99` post-cutover. No CORS, no second origin, no changes to `wingz-api.service`.

### Unresolved
- [ ] **Checkpoint F — `ride1/README.md`** not yet written. Full content drafted in the plan at `/home/jl2/.claude/plans/wondrous-hatching-knuth.md` (Quick Start, dev + production diagrams, deployment section, Basic Auth tradeoff callout, "What I'd Change for Production" list).
- [ ] **`todays_ride_events` test (EVENTS-03) is time-sensitive** — will SKIP once deployed seed events age past 24h. Re-seed via `ssh ec2-user@107.23.122.99 'cd /home/ec2-user/wingz-ride0/backend && .venv/bin/python manage.py seed_db'` if needed.
- [ ] **`VITE_ADMIN_EMAIL` / `VITE_ADMIN_PASSWORD` are inlined into the client bundle** — acceptable for an assessment seed admin but flagged as the main production improvement to call out in the pending README.
- [ ] **Orphan `/home/ec2-user/production/ride1` directory** on EC2 left behind by the failed first deploy — the successful deploy script now cleans it up with `sudo rm -rf`, but re-verify absence on next SSH.

### Handoff
1. **Write `ride1/README.md`** following the Checkpoint F section of the plan file. Hand off as the 6th commit (`docs: README with setup, env config, and deployment notes`).
2. **Final regression sanity** — after README commit, re-run `bash ride0/tests/test_deployed_api.sh http://107.23.122.99` once more and confirm 49/0/0 still holds.
3. **Update `ride0/REQUIREMENTS.md`** to mark the React Frontend work item as `done` once the README lands.
