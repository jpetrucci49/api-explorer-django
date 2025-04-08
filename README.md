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

## Next Steps

- Add `/analyze` endpoint for profile insights (e.g., language stats).
- Add `/network` endpoint for collaboration mapping.
- Deploy to Render or Heroku.

---
Built by Joseph Petrucci | March 2025