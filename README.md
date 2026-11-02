# API Explorer Django Backend

A RESTful API built with Django and DRF to fetch and cache GitHub user data. Integrates with the [API Explorer Frontend](https://github.com/jpetrucci49/api-explorer-frontend).

## Features

- Endpoint: `/github?username={username}`
- Returns GitHub user details (e.g., login, id, name, repos, followers).
- Redis caching with 30-minute TTL.

## Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/jpetrucci49/api-explorer-django.git
   cd api-explorer-django
   ```
2. **Install dependencies**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run locally**  
   ```bash
   make dev
   ```
   Runs on `http://localhost:3003`. Requires Redis at `redis:6379`.  
   *Note*: If `make` isn’t installed:  
   ```bash
   source venv/bin/activate && python manage.py runserver 0.0.0.0:3003
   ```

## Usage

- GET `/github?username=octocat` to fetch data for "octocat".
- Test with `curl -v` (check `X-Cache`) or the frontend.

## Example Response

```json
{
  "login": "octocat",
  "id": 583231,
  "name": "The Octocat",
  "public_repos": 8,
  "followers": 17529
}
```

## Production

The process reads `PORT` (default 3003), `GITHUB_TOKEN`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, and `FRONTEND_ORIGIN` (default `http://localhost:3000`). Also set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and `ALLOWED_HOSTS` if the host does not set `RENDER_EXTERNAL_HOSTNAME`. Redis must be plain TCP, with TLS off. Copy `.env.example` to `.env` and do not commit `.env`.

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

`GET /health` returns 200 for the host health check. Deploy steps live in the [umbrella README](https://github.com/jpetrucci49/fullstack-api-explorer).

## Next Steps

- Add `/analyze` endpoint for profile insights (e.g., language stats).
- Add `/network` endpoint for collaboration mapping.
- Deploy to Render or Heroku.

---
Built by Joseph Petrucci | March 2025