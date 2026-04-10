---
paths:
  - "**/*.py"
---

# Toolchain Quick Reference

Single lookup table for all project commands. No searching across files.

## Commands

| Concern | Command | Notes |
|---------|---------|-------|
| Lint | `cd backend && ruff check .` | Run after every code change |
| Test | `cd backend && pytest -v` | Run after every code change |
| Dev server | `cd backend && python manage.py runserver` | Local development |
| Migrations | `cd backend && python manage.py makemigrations` | After model changes |
| Apply migrations | `cd backend && python manage.py migrate` | After makemigrations |
| Secret scan | `bash .claude/hooks/scan-secrets.sh` | Pre-commit hook |

## Stack

| Aspect | Value |
|--------|-------|
| Language | Python 3.11+ |
| Framework | Django 5.1 + DRF 3.15 |
| Test runner | pytest 8.3 + pytest-django 4.9 |
| Linter | ruff 0.9 |

## Config Files

| File | Purpose |
|------|---------|
| `backend/wingz/settings.py` | Django settings (env-driven DB selection) |
| `backend/pytest.ini` | pytest configuration |
| `backend/requirements.txt` | Python dependencies |
| `.github/workflows/deploy.yaml` | CI/CD pipeline |
