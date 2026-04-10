---
paths:
  - "**/views.py"
  - "**/serializers.py"
  - "**/urls.py"
  - "**/permissions.py"
  - "**/authentication.py"
  - "**/pagination.py"
---

# API Design Rules

## REST Conventions
- URLs: plural nouns (`/rides/`), registered via DRF `DefaultRouter`
- HTTP methods: GET only (ReadOnlyModelViewSet per spec)
- Status codes: 200 (ok), 400 (bad input), 401 (unauthenticated), 403 (forbidden), 404 (not found), 500 (server error)

## Response Format
- DRF default envelope: `{ count, next, previous, results }`
- Pagination: page-number based via `StandardPagination` (`page`, `page_size` params)
- Error responses: `{ "error": "description" }` via custom exception handler
- Nested related objects (rider, driver as full objects, not IDs)

## Filtering & Sorting
- Query params: `status`, `rider_email` for filtering
- Query params: `sort_by=pickup_time` or `sort_by=distance&latitude=X&longitude=Y`
- All filtering and sorting happens at DB level (tables assumed VERY LARGE)

## Validation
- Validate at the view level — reject bad input early (missing lat/lng for distance sort → 400)
- Use DRF serializer validation for write operations
- Return specific error messages

## Authentication
- HTTP Basic Auth in Authorization header (email:password)
- Auth extracted in `EmailBasicAuthentication` middleware
- Return 401 for missing/invalid credentials, 403 for non-admin users
