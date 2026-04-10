# Feature: Authentication & Authorization

## Summary
Custom DRF authentication backend using HTTP Basic Auth. Looks up User by email,
verifies password via Django's `check_password()`. Admin-only access enforced via
a custom permission class that checks `user.role == 'admin'` (exact, case-sensitive).

## Requirements
- REQ-1: Custom `EmailBasicAuthentication` class extending DRF's `BasicAuthentication`
  - Authenticate by email (not username) + password
  - Look up User by email, verify password via `check_password()`
  - User model must implement `is_authenticated` property (returns `True`)
- REQ-2: Custom `IsAdminRole` permission class
  - Check `request.user.role == 'admin'` (exact match, case-sensitive)
  - Return `False` for any other role value including "Admin", "ADMIN", etc.
- REQ-3: DRF global configuration in settings.py
  - `DEFAULT_AUTHENTICATION_CLASSES`: `[EmailBasicAuthentication]`
  - `DEFAULT_PERMISSION_CLASSES`: `[IsAdminRole]`
- REQ-4: Seed admin user with known password (`adminpass123`) for curl/testing

## Dependencies
- Depends on: database-schema (User model with password field)
- Depended by: ride-list-api, performance, sorting

## Acceptance Criteria
- [ ] Admin user authenticates via BasicAuth and gets 200
- [ ] Non-admin user (rider/driver) gets 403 Forbidden
- [ ] Unauthenticated request gets 401 Unauthorized
- [ ] Wrong password gets 401 Unauthorized
- [ ] Role check is case-sensitive ("Admin" ≠ "admin")
- [ ] User model has `is_authenticated` property returning `True`

## Technical Notes
- BasicAuth sends `email:password` base64-encoded in the `Authorization` header
- User model is NOT Django's `AbstractUser` — we implement `is_authenticated` ourselves
- Password stored hashed via `make_password()`, verified via `check_password()`
- DRF's `BasicAuthentication.authenticate_credentials()` is overridden to use email lookup
