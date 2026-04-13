# Wingz Ride API — Postman Collections

Two self-contained collections. Import one, run Login, everything works. No environment files needed.

| File | Target |
|------|--------|
| `wingz-api.postman_collection.json` | Deployed API (`https://wingz-ride.d3sarrollo.dev`) |
| `wingz-api.local.postman_collection.json` | Local dev server (`http://localhost:8000`) |

## Quick start

1. Import either collection into Postman.
2. Run **Auth → Login**.
3. Run **Users → List users**.
4. Run anything else.

Tokens are injected into every request automatically via a collection-level pre-request script.

## Demo flow

Run the folders in this order for a clean walkthrough:

1. **Auth → Login**
2. **Users → List users** (saves rider/driver ids)
3. **Rides — Read** (list, filters, sorting, distance sort, retrieve)
4. **Rides — Write** (create → update → validation error → delete → verify 404)
5. **Reports → Trips over 1 hour**

## Running locally

```bash
cd ride0/backend
export USE_SQLITE=1
python manage.py migrate
python manage.py seed_db
python manage.py runserver
```

Then use the **Local** collection.
