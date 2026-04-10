# Handoff

## 2026-04-10 | session 4

### Intent
Rewrite `docs/prompts/PHASE_2_FRONTEND.md` so it drives the implementation of a React frontend as a **separate sibling project** at `wingz/ride1`, with no Docker anywhere, and a deploy path that lands on the **same EC2 instance** currently running `wingz-api.service`.

### Decisions
- Scoped the prompt to frontend-only — because the original Phase 2 prompt bundled Docker Compose, backend Dockerfile, project-root README, and Makefile into one monolithic doc; all of those belong to ride0 and are out of scope now
- `ride1/` is its own git repo (not nested in ride0) — because ride0 is already deployed and the frontend is an independent deliverable with its own CI
- Vite dev proxy for local CORS handling — standard, zero backend changes
- `VITE_*` env vars for credentials with an explicit README callout — because they get inlined into the bundle at build time; acceptable for an assessment seed admin but flagged as not production-safe
- nginx reverse proxy on EC2 (over CORS headers on the backend or running the frontend on a different port) — because single-origin keeps the browser simple, avoids modifying ride0, and mirrors how this would actually ship
- Build on CI, ship `dist/` via SCP (instead of cloning ride1 on EC2 and building there) — avoids installing Node on the production host and makes deploys faster and lighter
- Mandatory pre-flight SSH investigation in Step 5 with explicit STOP-and-report before infra changes — because the current port 80 → 8000 routing mechanism is opaque (iptables PREROUTING assumed but not confirmed), and the user's global rule forbids unilaterally working around unknowns
- Regression gate: `ride0/tests/test_deployed_api.sh http://107.23.122.99` must still pass after the nginx cutover — ensures the reverse proxy is transparent and ride0 behavior is preserved

### Unresolved
- [ ] Frontend setup (React + Vite) not yet scaffolded — prompt is now ready; execution is the next step
- [ ] Actual mechanism fronting EC2 port 80 → 8000 is unverified — Step 5 pre-flight must confirm (iptables rule? already-installed nginx? something else?) before the cutover
- [ ] `todays_ride_events` test (EVENTS-03) is time-sensitive — will SKIP once seed data events age past 24h; re-seed or re-deploy to restore freshness

### Handoff
1. Execute `docs/prompts/PHASE_2_FRONTEND.md` against a fresh `wingz/ride1/` directory — Steps 1–4 are local-only and safe to run end-to-end
2. Step 5 (EC2 deploy) requires the pre-flight SSH investigation first — do not make infra changes before reporting current state and getting approval
3. After cutover, re-run `bash ride0/tests/test_deployed_api.sh http://107.23.122.99` as the regression gate
