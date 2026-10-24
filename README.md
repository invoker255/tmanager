# Task Manager

A full-stack task manager with email verification, deadline reminders and a REST API. Built as a portfolio project: Django REST Framework on the backend, Vue 3 on the frontend, PostgreSQL, Docker, deployed on Render.

**Live demo:** <add your Render frontend URL here>
**API docs (Swagger):** <add your Render backend URL here>/api/docs/

## Features

- Registration with email verification (one-time link, expires after one hour) and resend with rate limiting
- Token authentication, password change that rotates the token
- Tasks with status, priority, category and deadline
- Filtering by status, priority and category, search, sorting, pagination
- Deadline reminder emails, configurable per user (12, 24, 72 hours before, or off), sent by a scheduled management command
- Per-user settings (theme, reminders) stored on the server
- Throttling on sensitive endpoints, per-user data isolation
- Interactive API documentation generated with drf-spectacular
- 60+ automated tests (pytest)

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python, Django, Django REST Framework, django-filter, drf-spectacular |
| Database | PostgreSQL (SQLite for quick local runs) |
| Frontend | Vue 3 (Composition API), Vue Router, Vite, Tailwind CSS, Axios |
| Infrastructure | Docker, docker compose, gunicorn, WhiteNoise, nginx, Render |
| Testing | pytest, pytest-django |

## Quick start with Docker

```bash
git clone <repository-url>
cd <repository-folder>
docker compose up --build
```

- Frontend: http://localhost:8080
- API: http://localhost:8000/api/
- Swagger UI: http://localhost:8000/api/docs/

Emails are printed to the backend logs in this mode. After registering, open the verification link from:

```bash
docker compose logs backend
```

## Local development without Docker

Backend:

```bash
cd tmanager
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend runs on http://localhost:5173 and expects the API at `VITE_API_URL` (default http://localhost:8000).

## Tests

```bash
cd tmanager
pytest
```

## Configuration

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key (required) |
| `DEBUG` | `True` for local development |
| `DATABASE_URL` | PostgreSQL connection string; SQLite is used if empty |
| `FRONTEND_URL` | Public frontend URL, used in emails and CORS |
| `CORS_ALLOWED_ORIGINS` | Extra allowed origins, comma separated |
| `CSRF_TRUSTED_ORIGINS` | Backend origins for the Django admin over HTTPS |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | Email delivery |
| `VITE_API_URL` | Backend URL baked into the frontend at build time |

## API overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Create an account and send a verification email |
| POST | `/api/users/verify-email/` | Confirm the email with `uid` and `token` |
| POST | `/api/resend-verification/` | Send a new verification email |
| POST | `/api/login/` | Get an API token (`Authorization: Token <key>`) |
| GET, PATCH | `/api/users/me/` | Profile |
| GET, PATCH | `/api/users/settings/` | Theme and reminder settings |
| POST | `/api/users/change-password/` | Change the password |
| GET, POST | `/api/tasks/` | List (filter, search, order, paginate) and create tasks |
| GET, PATCH, DELETE | `/api/tasks/{id}/` | Read, update, delete a task |
| GET | `/api/health/` | Health check |

Full interactive documentation: `/api/docs/`.

## Deadline reminders

Reminders are sent by a management command meant to run on a schedule (for example every 30 minutes):

```bash
python manage.py send_deadline_reminders
```

## Project structure

```
.
├── tmanager/            Django project (config, users, tasks, tests)
├── frontend/            Vue 3 application with Dockerfile and nginx config
└── docker-compose.yml   PostgreSQL, backend and frontend for local use
```