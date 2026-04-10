---
paths:
  - "**/*.py"
---

# Security Rules

## Credentials
- NEVER commit secrets, API keys, tokens, or passwords
- Use environment variables for all secrets (`DJANGO_SECRET_KEY`, `DB_PASSWORD`)
- Check for `.env` files in `.gitignore`
- If you find hardcoded credentials, flag immediately

## Input Validation
- Validate and sanitize ALL user input at system boundaries
- Use parameterized queries — NEVER string-concatenate SQL
- `RawSQL` uses parameter substitution (`%s` placeholders) — verified in Haversine implementation

## Authentication
- Passwords stored with `django.contrib.auth.hashers.make_password` (bcrypt/PBKDF2)
- Verified with `check_password` — never plain text comparison
- HTTP Basic Auth decoded safely with error handling for malformed headers

## Dependencies
- Pin dependency versions in `requirements.txt` (e.g., `django==5.1.*`)
- Check for known vulnerabilities before adding dependencies

## Data Exposure
- Never log sensitive data (passwords, tokens, PII)
- Serializer `fields` uses explicit allowlist — don't return `password` field
- `UserSerializer` excludes `password` from output fields
