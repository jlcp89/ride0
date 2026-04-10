# Test Scenarios: Authentication

## Happy Path
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-001 | Admin accesses ride list | force_authenticate(admin_user) → GET /api/rides/ | 200 | P0 |
| T-002 | Admin authenticates via BasicAuth | HTTP BasicAuth with admin email:password → GET /api/rides/ | 200 | P0 |

## Error Cases
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-003 | Non-admin gets rejected | force_authenticate(rider_user) → GET /api/rides/ | 403 | P0 |
| T-004 | Unauthenticated request | No auth → GET /api/rides/ | 401 | P0 |
| T-005 | Wrong password | BasicAuth with admin email + wrong password → GET /api/rides/ | 401 | P0 |
| T-006 | Case-sensitive role check | user.role="Admin" (capital A) → GET /api/rides/ | 403 | P1 |
| T-007 | Driver cannot access | force_authenticate(driver_user) → GET /api/rides/ | 403 | P1 |
