---
paths:
  - ".env*"
  - "**/settings.py"
  - "**/config.*"
---

# Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Yes (prod) | Django secret key | `django-insecure-dev-key-change-in-production` |
| `DJANGO_DEBUG` | No | Enable debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Yes (prod) | Comma-separated allowed hosts | `*` |
| `USE_SQLITE` | No | Use SQLite instead of MySQL | unset (MySQL) |
| `DB_NAME` | No | MySQL database name | `wingz_db` |
| `DB_USER` | No | MySQL user | `root` |
| `DB_PASSWORD` | No | MySQL password | empty |
| `DB_HOST` | No | MySQL host | `localhost` |
| `DB_PORT` | No | MySQL port | `3306` |
