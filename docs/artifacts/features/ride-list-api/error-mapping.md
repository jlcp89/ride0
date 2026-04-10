# Error Mapping: Ride List API

All error responses from `GET /api/rides/` and their conditions.

| Condition | HTTP Status | Response Body |
|-----------|-------------|---------------|
| Unauthenticated (no credentials) | 401 | DRF default: `{"detail": "Authentication credentials were not provided."}` |
| Invalid credentials (wrong password) | 401 | DRF default: `{"detail": "Invalid username/password."}` |
| Non-admin role | 403 | DRF default: `{"detail": "You do not have permission to perform this action."}` |
| sort_by=distance without lat/lng | 400 | `{"error": "latitude and longitude are required for distance sorting"}` |
| Invalid lat/lng values (non-numeric) | 400 | `{"error": "latitude and longitude must be valid numbers"}` |
| Unhandled server exception | 500 | `{"error": "Internal server error"}` |
