---
paths:
  - ".github/**"
---

# CI/CD

## Pipeline: GitHub Actions (`deploy.yaml`)

### Test Job (all branches)
1. Checkout code
2. Setup Python 3.11
3. `pip install -r requirements.txt`
4. `ruff check .` — lint
5. `pytest -v` — tests

### Deploy DEV (PR to `dev` branch)
- Triggers on: PR opened/reopened/synchronized to `dev`
- Deploys PR branch to EC2 dev environment
- Uses `USE_SQLITE=1` for SQLite database
- Runs as `gunicorn` systemd service on port 8000

### Deploy PROD (push to `main` or merged PR to `main`)
- Triggers on: push to `main` OR merged PR to `main`
- Deploys `main` branch to EC2 prod environment
- Same setup as dev but with prod secrets

### Secrets Required
- `EC2_HOST_DEV` / `EC2_HOST_PROD` — EC2 instance hostnames
- `EC2_SSH_KEY` — SSH private key for deployment
- `PERSONAL_ACCESS_TOKEN` — GitHub PAT for cloning
- `DJANGO_SECRET_KEY` — Production secret key
