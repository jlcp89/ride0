# Wingz Ride API — Postman collection

Drop-in Postman collection for exploring the Wingz ride management API. Covers JWT authentication and the rides list/retrieve endpoints against either a local Django runserver or the deployed instance.

## Files

| File | Purpose |
|------|---------|
| `wingz-api.postman_collection.json` | The collection — Auth folder (login/refresh/me/logout) + Rides folder (9 request examples) |
| `wingz-api.local.postman_environment.json` | Environment for local dev (`http://localhost:8000`) |
| `wingz-api.prod.postman_environment.json` | Environment for the deployed API (`https://wingz-ride.d3sarrollo.dev`) |

## Quick start

1. **Import the collection.** In Postman: *File → Import* → drop `wingz-api.postman_collection.json`.
2. **Import one environment.** Same flow with either `…local…` (local runserver) or `…prod…` (deployed).
3. **Select it** in the environment dropdown (top-right of Postman).
4. **Run `Auth → Login`.** The response test script automatically stores `access_token` and `refresh_token` in the active environment.
5. **Run anything else.** Every other request inherits `Authorization: Bearer {{accessToken}}` from the collection, so it just works.

## Requests at a glance

### Auth
- **Login** — `POST /api/auth/login/`, captures tokens into the environment
- **Refresh token** — `POST /api/auth/refresh/`, rotates `accessToken` only (refresh tokens are not rotated)
- **Current user (me)** — `GET /api/auth/me/`
- **Logout** — `POST /api/auth/logout/` (stateless, returns 204)

### Rides (all require `role=admin`)
- **List — defaults** — `GET /api/rides/`
- **List — paginated** — `?page=2&page_size=5`
- **List — filter by status** — `?status=en-route` (valid values: `to-pickup`, `en-route`, `dropoff`)
- **List — filter by rider email** — `?rider_email=alice@example.com`
- **List — combined filters** — status + rider_email
- **List — sort by pickup_time** — `?sort_by=pickup_time`
- **List — sort by distance** — `?sort_by=distance&latitude=14.5995&longitude=-90.5131` (Haversine at the DB level)
- **List — distance missing lat/lng (expect 400)** — validation example
- **Retrieve ride by id** — `GET /api/rides/{{rideId}}/`

## Credentials

The environment files are pre-filled with the seed admin from `backend/rides/management/commands/seed_db.py`:

- `adminEmail = admin@wingz.com`
- `adminPassword = adminpass123`

These are not secrets — they're synthetic seed values that `python manage.py seed_db` writes fresh on every deploy.

## Notes

- **Access tokens last 15 minutes.** When a request returns 401, re-run `Auth → Login` (or `Auth → Refresh token`) and retry.
- **Refresh tokens last 7 days.** They are not rotated — the same refresh token stays valid until its original expiry.
- **The API is read-only.** There are no POST/PUT/DELETE endpoints for rides.
- **`todays_ride_events`** on each ride only contains events from the last 24 hours (filtered at the database level).
- **Seed data is wiped and re-seeded on every deploy**, so `rideId=1` and `rider_email=alice@example.com` are always valid against the deployed instance.

## Running the API locally

```bash
cd ride0/backend
python manage.py migrate
python manage.py seed_db
python manage.py runserver
```

Then select the **Wingz Ride — Local** environment in Postman.

## Cross-checking against the shell regression

The query-param examples (especially the `latitude=14.5995&longitude=-90.5131` distance sort and the `rider_email=alice@example.com` filter) mirror `ride0/tests/test_deployed_api.sh` so Postman results can be compared directly against the 49-case regression script:

```bash
bash ride0/tests/test_deployed_api.sh https://wingz-ride.d3sarrollo.dev
```

If a Postman request and the regression disagree about the response, one of them is wrong and needs to be reconciled before claiming the API is healthy.
