# Code Review — `ride0` backend + `ride1` frontend vs. `docs/requirement/requirement.md`

*Reviewer: Claude Opus 4.6 · Original: 2026-04-11 · **Updated: 2026-04-11 (session 8)***

## Context

Complete code review of the Django backend at `/home/jl2/work/wingz/ride0/backend/` **and** the React + Vite frontend at `/home/jl2/work/wingz/ride1/`. Each requirement is graded against the source code with `file:line` evidence, followed by a prioritized list of fixes.

This is an update of the prior review. Key deltas since the previous pass:

1. **Both READMEs now exist and are in scope.** The previous review explicitly excluded them ("being authored in a parallel session"). They are now reviewed in their own stage below.
2. **Session-6 bonus-report code has landed.** Commits `379d9a0 expose endpoint for bonus report`, `5d266e9 added more seed data for bonus report`, and `744a435 added bonus report to front` are now in `main` (git log). The HANDOFF still labels them "uncommitted" — the HANDOFF is stale on this point.
3. **A new critical issue was discovered**: an orphaned, untracked `backend/seed_data.sql` exists at the wrong path while the canonical `backend/sql/seed_data.sql` is staged for deletion. Both READMEs and `ride0/CLAUDE.md` still reference the old path.
4. **Verification re-run, fresh:**
   ```
   $ cd /home/jl2/work/wingz/ride0/backend && .venv/bin/ruff check .
   All checks passed!

   $ .venv/bin/pytest -v
   65 passed in 6.86s

   $ cd /home/jl2/work/wingz/ride1 && npm run lint && npm run build
   (eslint clean) → vite build clean (dist 220.50 kB / 67.61 kB gzip)
   ```

**One-line verdict:** functionality, performance, and the README narrative all satisfy the spec. The two new critical findings are easy fixes (path of one file, presence of one license file) and do not affect runtime behavior.

---

## Stage 1 — Backend requirement-by-requirement scorecard

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1a | Models for `User`, `Ride`, `RideEvent` with spec column names + custom PKs | **PASS** | `rides/models.py:4-65`, `rides/migrations/0001_initial.py` (uses `db_column` to match `id_rider`/`id_driver`/`id_ride`/`id_user`/`id_ride_event`) |
| 1b | Serializers for JSON (nested rider/driver/events) | **PASS** | `rides/serializers.py:6-31` — `id_rider`/`id_driver` are `UserSerializer(read_only=True)`, `todays_ride_events = RideEventSerializer(many=True, read_only=True)` |
| 1c | "Use Viewsets for managing CRUD operations" | **PARTIAL** | `rides/views.py:15` is `ReadOnlyModelViewSet`. Only the list/retrieve verbs are exposed. The spec literally says CRUD; the only functional requirement is the list endpoint, so this is defensible. See P1 below. |
| 2 | Auth gates non-`role='admin'` users | **PASS** | `rides/permissions.py:4-6` (`request.user.role == "admin"`); set as DRF default in `wingz/settings.py`; covered by `tests/test_permissions.py` (5) and `tests/test_auth.py` (23, JWT-only — Basic Auth removed in session 2b). Spec asked for "authentication" generically — the JWT flow exceeds what's required. |
| 3a | Ride list returns related events + users | **PASS** | `rides/serializers.py:18-31`, response shape verified in `tests/test_views.py` (12 tests) |
| 3b | Pagination | **PASS** | `rides/pagination.py` (`StandardPagination`, `page_size_query_param='page_size'`, `max_page_size=100`); wired at `rides/views.py:18`; tested in `tests/test_views.py::test_pagination_*` |
| 3c | Filter by `status` and `rider_email` | **PASS** | `rides/views.py:32-37` — both filters are DB-side; FK traversal `id_rider__email` keeps email filtering in SQL; tested in `tests/test_views.py::test_filter_*` |
| 3d | Sort by `pickup_time` (DB-side, paginatable) | **PASS** | `rides/views.py:40-41` — `qs.order_by("pickup_time")`; tested in `tests/test_views.py::test_sort_by_pickup_time` |
| 3e | Sort by distance to a GPS point (DB-side, paginatable, scalable) | **PASS** | `rides/views.py:67-83` — Haversine via `RawSQL` with `%s` placeholders + `(lat, lat, lng)` tuple (no SQLi). Annotated `distance` column → `ORDER BY distance LIMIT … OFFSET …` runs in the DB. Tested in `tests/test_views.py::test_sort_by_distance_*` and `test_distance_sort_*`. SQLite math functions registered for tests in `tests/conftest.py`. |
| 4a | `todays_ride_events` field is last-24 h only, never loads full event table | **PASS** | `rides/views.py:21-26` — `Prefetch("ride_events", queryset=RideEvent.objects.filter(created_at__gte=last_24h), to_attr="todays_ride_events")`. `last_24h` is computed per-request via `timezone.now()`, not at module import. |
| 4b | Ride list ≤ 2 SQL queries (3 with `COUNT`) | **PASS** | Trace: (1) `COUNT(*)` for pagination, (2) `SELECT rides.* JOIN users JOIN users` with `select_related("id_rider","id_driver")`, (3) prefetch of filtered `ride_events`. Asserted in `tests/test_performance.py::TestQueryCount::test_max_3_queries` and `test_no_n_plus_1` (constant query count at 5 vs 25 rows — N+1 proof). |
| 5 | Table structure unmodified, custom PKs in place | **PASS** | `rides/migrations/0001_initial.py` keeps `db_column` mappings to the spec; no schema drift. |
| 6 | README that lets a stranger set up + run the project, includes the bonus SQL and design notes | **PASS** | `ride0/README.md` (676 lines, **new** in session 7). Reviewed in Stage 2 below. |
| 7 | Bonus SQL — trips > 1 h grouped by month + driver | **PASS** | `backend/sql/bonus_report.sql` uses `MIN(pickup) … MAX(dropoff) … TIMESTAMPDIFF(MINUTE, …) > 60`, grouped on `DATE_FORMAT(…, '%Y-%m')` + driver. Edge cases (multiple events, missing events, exact 60 min) handled. Also exposed as `GET /api/reports/trips-over-hour/` via `rides/report_views.py` (`_SQL_MYSQL` / `_SQL_SQLITE` selected by `connection.vendor`), gated by JWT + `IsAdminRole`, covered by `tests/test_reports.py` (4 tests). **Now committed** (`379d9a0`, `5d266e9`). |

### Evaluation criteria

| Criterion | Verdict | Notes |
|---|---|---|
| Functionality | **PASS** | All required endpoints behave correctly. |
| Code quality | **PASS** | Clean module split. Largest backend file is `auth_views.py` at 144 lines, well under the 300-line cap. **Ruff clean** (`All checks passed!`). PEP 8 naming, grouped imports, no bare `except`, no mutable defaults, no dead code. |
| Error handling | **PASS** | `rides/exceptions.py:6-13` is wired in `wingz/settings.py` as `EXCEPTION_HANDLER`. The list view validates lat/lng before calling Haversine (`rides/views.py:48-65`) with `{"error": …}` envelopes for both "missing" and "non-numeric" cases. Auth failures return 401, role failures 403. |
| Performance | **PASS** | 3-query budget hit and asserted; `Prefetch(to_attr=…)` blocks N+1; Haversine in SQL keeps distance sort O(log n) per page. |

---

## Stage 2 — README & frontend review (new in this update)

### `ride0/README.md` (676 lines)

**Strengths**

- **Requirements Compliance scorecard** at the top maps every spec bullet to its implementation file + test. Eliminates the "did they actually do X" question for any reviewer who skims.
- **Three quick-start paths** (SQLite zero-setup / MySQL parity / live-demo `curl`) — power move for an assessment because the reviewer can verify the live API in 30 seconds without cloning.
- **Bonus SQL inlined byte-for-byte** from `backend/sql/bonus_report.sql`. Verified identical to the canonical file by content diff.
- **Performance Deep-Dive section** quotes the actual `get_queryset` and `assertNumQueries` test verbatim — reviewers can verify the 3-query claim against the source without cross-referencing.
- **Distance Sort Algorithm walkthrough** exposes the Haversine RawSQL with the safety + portability rationale (parameter substitution + SQLite UDF registration).
- **Design Decisions section** has 7 numbered items; each names what was rejected and why. This is the kind of self-aware narrative the spec literally asks for.
- **Top-banner badges + live-demo `curl`** make the README readable on GitHub at a glance.

**Spot-checks performed against the source**

- Test count `65 passing` matches `pytest -v` exactly (23 + 12 + 4 + 5 + 4 + 5 + 12 = 65, see Testing section).
- The inlined `get_queryset` snippet (README L367–395) matches `rides/views.py:20-46` line-for-line.
- The inlined Haversine `_annotate_haversine` (README L434–446) matches `rides/views.py:67-83`.
- The inlined Bonus SQL (README L463–510) is byte-identical to `backend/sql/bonus_report.sql`.
- Component / file names referenced in the Project Structure tree exist on disk **except for `seed_data.sql` — see C1 below**.

### `ride1/README.md` (302 lines)

**Strengths**

- Mirrors the ride0 README's banner, badge, ToC, and section ordering — the two READMEs read like one coherent submission.
- **ASCII feature walkthrough** at the top gives the reviewer an instant mental picture of the UI without screenshots.
- **Component tree** + **`apiFetch` 401-refresh sequence diagram** show the only two non-trivial interactions in the app.
- **Design Decisions (6) + Known Limitations (6)** with explicit "what was rejected and why" framing — same self-aware tone as ride0.
- **Dependencies callout** ("Zero runtime dependencies beyond React and React-DOM") — verified against `package.json`: `dependencies` is exactly `react ^19.2.4` + `react-dom ^19.2.4`. Accurate.

**Spot-checks performed**

- Component list (`LoginForm`, `FilterBar`, `RideTable`, `RideDetailDrawer`, `Pagination`, `SkeletonRow`, `EmptyState`, `TripsReport`, `icons`) → all 9 files exist in `src/components/`.
- Hooks (`useSearchParamsState`, `useDebouncedValue`) → both exist in `src/hooks/`.
- Stylesheets list (`tokens.css`, `base.css`, `layout.css`, `forms.css`, `login.css`, `table.css`, `drawer.css`, `pagination.css`, `index.css`) → all 9 exist in `src/styles/`.
- `apiFetch` 401-refresh-retry contract → confirmed in `src/services/api.js` (142 lines).

---

## Findings worth acting on, in priority order

### Critical (broken doc references — must fix before submission)

#### C1. Orphaned `backend/seed_data.sql` at the wrong path

`git status` in `ride0` shows:

```
 D backend/sql/seed_data.sql
?? backend/seed_data.sql
```

The file content is identical (both start with `-- Seed Data for Wingz Ride Management API`), but it has been moved from `backend/sql/seed_data.sql` (the canonical, git-tracked location) to an untracked copy at `backend/seed_data.sql`. The old file is staged for deletion; the new one is not staged at all.

This breaks two reviewer-visible references:

- `ride0/README.md:623` — Project Structure tree shows `seed_data.sql` under `└── sql/`. After commit, that file would not exist.
- `ride0/CLAUDE.md:79` — Project Structure tree also lists `seed_data.sql` under `sql/`.

**Fix:** decide whether the move was intentional. Most likely it was not (no commit message mentions a move; the new file is sitting in the parent dir alone). Recommended: revert. Concretely:

```bash
cd /home/jl2/work/wingz/ride0
git checkout -- backend/sql/seed_data.sql
rm backend/seed_data.sql
```

If the move *was* intentional, then both `README.md:623` and `CLAUDE.md:79` need to be updated, and `backend/seed_data.sql` needs to be `git add`-ed.

#### C2. Both READMEs link to a non-existent `LICENSE` file

`ride0/README.md:674` and `ride1/README.md:300` both contain:

> MIT. See [`LICENSE`](LICENSE) if present; otherwise treat the entire repository as MIT-licensed take-home submission code.

There is no `LICENSE` file in either `ride0/` or `ride1/`:

```
$ ls /home/jl2/work/wingz/ride0/LICENSE* /home/jl2/work/wingz/ride1/LICENSE*
(no matches)
```

The "if present" hedge is graceful, but the markdown renders as a clickable link that 404s on GitHub. For a hire-grade submission this is the kind of detail a senior reviewer notices in the first 30 seconds.

**Fix (pick one):**

1. Drop a real `LICENSE` file into each sub-repo. The MIT template is 21 lines; copy the standard text and fill in the year + copyright holder.
2. Remove the `[LICENSE](LICENSE)` markdown link and replace with plain "MIT licensed."

Option 1 is the right call for a take-home — it costs nothing and removes the broken link.

### Important (consistency / standards — should fix)

#### I1. `ride1/src/App.jsx` exceeds the 300-line workspace file limit

```
$ wc -l ride1/src/App.jsx
308 ride1/src/App.jsx
```

The workspace `quality.md` rule caps files at 300 lines for both languages. `App.jsx` is 8 lines over and trending upwards as features are added (Reports tab, distance sort, drawer state). The README's component tree even names two inline pieces (`AppHeader`, `Nav`) that could become real components.

**Fix:** extract `AppHeader` (currently inline at `App.jsx:30`) and the `<nav>` block (currently at `App.jsx:200`) into `src/components/AppHeader.jsx` and `src/components/AppNav.jsx`. That brings `App.jsx` back under the limit, makes the README's component-tree wording literally accurate, and gives the auth-aware shell its own seam to test against once Vitest lands.

#### I2. Component tree in `ride1/README.md` lists inline pieces as if they were files

`ride1/README.md:124-141` shows `AppHeader` and `Nav` in the component tree alongside real component files. Both are actually inline JSX inside `App.jsx`:

- `AppHeader` is a `function AppHeader(...)` declared at `App.jsx:30`
- `Nav` is just a `<nav className="app-nav">` block at `App.jsx:200` — no named component at all

**Fix:** either annotate them as "(inline in App.jsx)" or solve I1 by extracting them. The latter is cleaner.

### P1 — strict-reading gap (carried over from prior review)

#### P1-1. Decide whether `RideViewSet` should be full CRUD

- `rides/views.py:15` is `ReadOnlyModelViewSet`. The spec says *"Use Viewsets for managing CRUD operations"* — strict reading wants Create/Update/Delete too. Pragmatic reading: the only functional API requirement is the Ride **List** endpoint, so read-only is sensible.
- Two viable paths:
  - **(a) Leave it.** Document the choice in the README ("only the list endpoint is functionally required, so the viewset is read-only — write paths would need additional validation, audit trails, and tests not in scope for the assessment").
  - **(b) Switch to `ModelViewSet`.** Need to add: writable serializer fields (currently `id_rider`/`id_driver` are read-only nested), `POST`/`PUT`/`PATCH`/`DELETE` tests, write-permission scoping (the existing `IsAdminRole` already allows admin writes), validation on create/update, and a decision about whether `todays_ride_events` is writable.
- I lean toward **(a) + a one-paragraph README note in the Design Decisions section** because it preserves the "minimum surface area" principle and the assessment never asks for ride creation. The user should choose. *Note: the current `ride0/README.md` Design Decisions section does not address this trade-off — adding it would close the gap with no code changes.*

> **Resolved 2026-04-11 (session 9).** User chose path (b). `RideViewSet` is now `ModelViewSet`; write paths use a split `RideReadSerializer` / `RideWriteSerializer` behind a `get_serializer_class()` switch, with strict validation (status whitelist, lat/lng ranges, `id_rider != id_driver`) and a `create`/`update` re-hydration so every write response matches the GET shape. The custom exception handler now flattens DRF `ValidationError` payloads into `{"error": "..."}` for shape consistency. Coverage: `tests/test_views_crud.py` (17 tests, 82 total), regression `test_deployed_api.sh` jumps from 49/0/0 to 53/0/0 (EDGE-01 repurposed to "POST empty body → 400" + four new CRUD-NN assertions exercising POST → PATCH → DELETE → GET 404). See README Design Decisions item 8.

### P2 — best-practice polish (none of these block submission)

#### P2-1. Add explicit DB indexes on `Ride.pickup_time` and `Ride.status` *(carried over)*

The spec assumes the Ride table is "very large." Sorting on `pickup_time` and filtering on `status` will both touch the optimizer. Django auto-indexes PKs and FKs, but not these two columns. Verified: `rides/models.py` `Ride.Meta` has `db_table` and `ordering` but no `indexes` declaration. The only index in the file is `RideEvent.Meta.indexes = [models.Index(fields=["created_at"], …)]`.

**Fix:** add to `rides/models.py` `Ride.Meta.indexes`: one composite index on `(status, pickup_time)` covers both the filter and the sort. Generate a migration. Tests stay green because SQLite ignores most index hints.

#### P2-2. Consolidate the distance-sort validation *(carried over)*

Validation is split across `rides/views.py:48-65` (the `list()` override checks presence + numeric) and `:42-45` (`get_queryset()` does the actual `float()` conversion). It works, but the duplication is a smell — and `get_queryset()` would crash if it were ever called outside `list()` (e.g., schema generation, OPTIONS for `drf-spectacular`).

**Fix:** do the parsing and validation **once** in `get_queryset()`, raising `rest_framework.exceptions.ValidationError` so the exception handler converts it to `{"error": …}` 400. Drop the `list()` override.

#### P2-3. Test coverage gaps *(carried over)*

Currently 65 tests passing, but missing:

- Page out of range (`?page=999` on a tiny dataset).
- `page_size` clamping (`?page_size=500` should cap at 100).
- Special characters / SQLi-shaped strings in `rider_email`.
- Combining `status=<nonexistent>` with `sort_by=distance` (filter+sort interaction on empty result).
- Auth header edge cases (`bearer …` lowercase, double-space, missing space).

Add ~5 short tests; none should require new fixtures.

#### P2-4. Extend `tests/test_deployed_api.sh` to hit `/api/reports/trips-over-hour/` *(carried over, still open)*

Confirmed: `grep -c "trips-over-hour\|/api/reports" tests/test_deployed_api.sh → 0`. The regression script's "49/0/0" total is now an undercount. ~4 assertions: 200, results length > 0, every row has `month`/`driver`/`count`, at least one row has `count > 1`.

#### P2-5. Document why the bonus report SQL escapes `%` to `%%` for the MySQL variant *(carried over)*

`rides/report_views.py` already comments the dual-vendor approach, but the `%%` doubling for `DATE_FORMAT('%%Y-%%m')` is the kind of non-obvious detail a reviewer will pause on. Two-line comment beside `_SQL_MYSQL`.

#### P2-6. Refresh stale Claude rules docs *(carried over)*

- `ride0/.claude/rules/api-design.md` still says *"HTTP Basic Auth in Authorization header (email:password)"*. Basic Auth was removed in session 2b. The HANDOFF tracks this as a parking-lot item.
- `ride0/CLAUDE.md:79` and `ride0/README.md:623` reference `backend/sql/seed_data.sql` — see C1 above. (Either fix C1 by reverting the move, or update both docs to point at the new path.)

#### P2-7. Drop a `LICENSE` file in each sub-repo

See C2 above. Listed here as a P2 reminder because the README links are the visible symptom; the underlying fix is mechanical.

#### P2-8. README "Future Work" claim about `seed_db` is destructive but not quite right

`ride0/README.md:657` says *"`seed_db` is destructive. It deletes all users (cascading to rides and events) and rebuilds from scratch."* This is accurate, but the README also pitches Quick Start Option A (`USE_SQLITE=1 python manage.py seed_db`) as a clean first-run experience without flagging that re-running the script wipes data. A one-line note in the Quick Start ("`seed_db` is idempotent: it deletes and recreates everything every run, which is the right behaviour for the assessment but the wrong behaviour for any environment with real data") would close the loop.

Optional, not blocking.

### P3 — optional polish

#### P3-1. README screenshots

Both READMEs use ASCII art for visuals. A `docs/images/` folder with three real screenshots (login, ride list with filters open, reports tab) would lift the "feel" of the submission another notch. The user already chose ASCII-only in session 7 to avoid follow-up work, so this stays optional.

#### P3-2. README claim "65 automated tests" hard-codes the number

It will go stale the moment a new test lands. A `[![Tests](…/tests-65%20passing-success)](…)` badge is similarly fragile. Low priority — just be aware that `pytest -v` is the source of truth.

---

## Things that look right and don't need touching

Listed so the user knows they were checked, not skipped:

- Custom `User` model uses `make_password`/`check_password` (not plain text), and `UserSerializer` does **not** expose the `password` field.
- `RawSQL` Haversine uses parameterized `%s` placeholders — no SQL injection vector. README documents the safety property explicitly.
- `select_related("id_rider", "id_driver")` is the correct ORM call given the FK names; both User joins land in a single SQL statement.
- `Prefetch(to_attr="todays_ride_events")` correctly bypasses the default `ride_events` reverse manager so the serializer reads the prefetched attribute, not a fresh query.
- Custom DRF `EXCEPTION_HANDLER` is wired up; auth/permission failures get 401/403 envelopes consistently.
- `RideEvent` has an explicit `Meta.indexes` entry on `created_at` — exactly the column the prefetch filters on. Verified at `rides/models.py:Meta`.
- Bonus SQL handles the multi-event edge case (`MIN(pickup)`, `MAX(dropoff)`) and excludes negative durations via `TIMESTAMPDIFF > 60`.
- Bonus SQL is committed both as a `.sql` file (`backend/sql/bonus_report.sql`) and as a live endpoint (`rides/report_views.py`) gated by the same JWT + IsAdminRole. Tested in `tests/test_reports.py`.
- Git history is a clean per-feature progression (`raw SQL for trips > 1hr`, `serializers nested rider/driver + todays_ride_events`, `assertNumQueries tests proving 2-3 query target`, `expose endpoint for bonus report`, `added more seed data for bonus report`) — exactly what the spec asks for.
- No secrets in source; `SECRET_KEY` and `JWT_SECRET_KEY` come from env vars; `.gitignore` excludes `.env`, `__pycache__`, `.venv`, `.sqlite3`.
- All backend files are under the 300-line workspace cap (largest: `auth_views.py` at 144 lines).
- 65/65 pytest tests pass; ruff is clean; ride1 ESLint is clean; Vite production build is clean (220.50 kB → 67.61 kB gzipped).

---

## Decisions for the user

Before any code changes, need a call on:

1. **C1 — was the seed_data.sql move intentional?** If no, revert (1 command). If yes, update `README.md:623` and `CLAUDE.md:79` and `git add backend/seed_data.sql`.
2. **C2 — drop a real LICENSE file or rewrite the README link?** Recommendation: drop the MIT license text into both sub-repos (low cost, removes the broken link).
3. **I1 — extract `AppHeader` / `AppNav` from `App.jsx`?** Brings the file under the 300-line cap and makes the README accurate. Low risk, no behaviour change.
4. **P1-1 — CRUD literal vs. pragmatic.** Stay `ReadOnlyModelViewSet` and add a sentence to the README's Design Decisions section, or expand to `ModelViewSet` with full write paths + tests?
5. **Index migration (P2-1).** Add the `(status, pickup_time)` index now, or defer to a future "production hardening" pass?
6. **Touch the in-flight deploy?** The HANDOFF still flags an open ride1 deploy blocker (login smoke-test JSONDecodeError). None of the review findings here are urgent — confirm whether you want any of this work to land before or after that deploy is unblocked.

## Files to read or modify when acting on the findings

Read-only references the implementer will need:

- `/home/jl2/work/wingz/ride0/docs/requirement/requirement.md` — source of truth.
- `/home/jl2/work/wingz/ride0/backend/rides/views.py` — for P1-1, P2-2.
- `/home/jl2/work/wingz/ride0/backend/rides/models.py` — for P2-1.
- `/home/jl2/work/wingz/ride0/backend/rides/report_views.py` — for P2-5.
- `/home/jl2/work/wingz/ride0/tests/test_deployed_api.sh` — for P2-4.
- `/home/jl2/work/wingz/ride0/README.md` — for C1, C2, P1-1, P2-8.
- `/home/jl2/work/wingz/ride1/README.md` — for C2, I2.
- `/home/jl2/work/wingz/ride1/src/App.jsx` — for I1.

Files to modify:

- `/home/jl2/work/wingz/ride0/backend/sql/seed_data.sql` *(C1: revert deletion)* and remove `/home/jl2/work/wingz/ride0/backend/seed_data.sql`.
- `/home/jl2/work/wingz/ride0/LICENSE` and `/home/jl2/work/wingz/ride1/LICENSE` *(C2: create)*.
- `/home/jl2/work/wingz/ride1/src/App.jsx` + new `src/components/AppHeader.jsx` and `src/components/AppNav.jsx` *(I1)*.
- `/home/jl2/work/wingz/ride1/README.md` *(I2 if not extracting)*.
- `/home/jl2/work/wingz/ride0/backend/rides/views.py` *(P1-1 if CRUD; P2-2)*.
- `/home/jl2/work/wingz/ride0/backend/rides/models.py` + new migration *(P2-1)*.
- `/home/jl2/work/wingz/ride0/backend/tests/test_views.py` *(P2-3)*.
- `/home/jl2/work/wingz/ride0/tests/test_deployed_api.sh` *(P2-4)*.
- `/home/jl2/work/wingz/ride0/backend/rides/report_views.py` *(P2-5, comment-only)*.
- `/home/jl2/work/wingz/ride0/CLAUDE.md` *(P2-6 if not reverting C1)*.

## Verification after any fixes land

Standard ride0 + ride1 proof cycles, plus the cross-repo regression if anything in the API contract moves:

```
cd /home/jl2/work/wingz/ride0/backend
.venv/bin/ruff check .             # expect: All checks passed!
.venv/bin/pytest -v                # expect: 65+ passed

cd /home/jl2/work/wingz/ride1
npm run lint                       # expect: clean
npm run build                      # expect: clean

bash /home/jl2/work/wingz/ride0/tests/test_deployed_api.sh https://wingz-ride.d3sarrollo.dev   # expect 49/0/0 (or 53/0/0 after P2-4)
```
