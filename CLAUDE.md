# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 5.1 back-office for **Complexe Marbika**, a leisure complex combining a hair/beauty salon, a restaurant/bar, a pool & gym, event-space rental, and vocational training. The UI is French; code identifiers, comments, and user-facing strings are all in French — follow that convention.

Monetary amounts are integers in GNF (Guinean Franc), stored as `BigIntegerField`. Format them for display with `salon.views.currency()`.

## Commands

The project uses a venv at `.venv` and PostgreSQL (configured via `.env`).

```bash
# Activate venv (Git Bash on Windows)
source .venv/Scripts/activate

python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# Tests (Django test runner; note: tests.py files are currently empty stubs)
python manage.py test                       # all apps
python manage.py test salon                 # one app
python manage.py test salon.tests.MyTest.test_x   # single test
```

Configuration is read from `.env` (via `python-dotenv`): `SECRET_KEY`, `DEBUG`, `DB_*`, `ALLOWED_HOSTS`. There is no `settings.py` split for prod — the same file reads env vars.

Note: `requirements.txt` is **incomplete** — it omits `djangorestframework` even though `pointage` and `settings.INSTALLED_APPS` depend on `rest_framework` + `rest_framework.authtoken`. Install DRF manually (`pip install djangorestframework`) if setting up a fresh venv. `TIME_ZONE = 'UTC'` with `USE_TZ = True`, so the manual `timezone.now()` stamping described below writes UTC.

## Architecture

Django project `marbika/` with domain apps mounted in `marbika/urls.py`:

- **`employe`** — custom user model + the analytics/admin dashboard. This is the hub.
- **`salon`** — services, prestations (jobs), products, sales, expenses, subscriptions.
- **`restaurant`** — dishes, drinks, orders, stock-control sessions.
- **`client`** — clients, zone rental/reservation, pool entries, gym subscriptions.
- **`formation`** — training courses and enrollments (minimal; registered in `INSTALLED_APPS` but has **no `urls.py`** and is not mounted in `marbika/urls.py`).
- **`pointage`** — staff attendance, the only DRF/REST app.
- **`services/`** — plain-Python domain services (not a Django app), e.g. `prestation_service.py`.

### Custom user model
`AUTH_USER_MODEL = 'employe.Employe'` (`employe/models.py`). `Employe` extends `AbstractUser` with a **UUID primary key**, `telephone`, and audit fields. Employees are created via `Employe.objects.create_user(...)` with an auto-generated `username` (`firstname_<uuid8>`) and a random password — see `employe.views.add_employe`.

### MyBaseModel audit pattern
Almost every model extends `employe.models.MyBaseModel` (abstract), which supplies a UUID `id` and audit columns: `created_at` (auto), `created_by` (FK Employe), `updated_at`, `updated_by`. When writing/updating records, set `created_by`/`updated_by` to `request.user` and stamp `updated_at` with `timezone.now()` manually (see `add_attributions`, `attribuer_montant_total`). A few models redefine `created_at` as a manually-set field (`InitPrestation`, `Prestation`) so historic dates can be entered.

### Salon prestation → attribution flow
The core salon business logic, spread across `employe/views.py`, `services/prestation_service.py`, and `salon/models.py`:
1. An `InitPrestation` (reference, `montant_total`, `remise`, client) groups one or more `Prestation` rows. Each `Prestation` links a `Service` and `fait_par` (M2M of `Employe`s who performed it).
2. Revenue is later attributed to staff via `add_attributions` (`employe/views.py`). Two cases: **single prestataire** across all prestations → `attribuer_montant_total()` assigns the full net amount; **multiple** → per-service `RepartitionMontantPrestation` rows are `bulk_create`d inside a transaction, with `DetailRepartitionMontant` details.
3. `get_unique_prestataire()` (`services/prestation_service.py`) decides which case applies. Once attributed, `InitPrestation.montant_attribue` is set `True` to exclude it from the pending list.

### Views convention
Views are **function-based**, not class-based (except the one DRF ViewSet in `pointage`). AJAX endpoints read `json.loads(request.body)`, return `JsonResponse({"success": bool, ...})`, and are guarded with `@require_http_methods([...])`. Page-rendering views use `@login_required(login_url="login")`. `salon/urls.py` and `restaurant/urls.py` import views with `from ... import *`.

### Frontend
Server-rendered Django templates in `templates/` (shared `base.html`, `sidebar.html`, `head.html`) plus per-app `templates/<app>/`. Bootstrap 5 via `crispy-forms`/`crispy-bootstrap5`. Dynamic tables/forms are populated by AJAX calls to the JSON endpoints above. The `marbika.context_processors.current_url_name` processor exposes the active URL name to every template (used for sidebar highlighting). Static assets in `static/assets`, user uploads in `media/`.

### Attendance API (DRF)
`pointage` mounts under `attendance/api/v1/` via a DRF `DefaultRouter`. `Attendance` enforces one open check-in per employee with a `UniqueConstraint` (`check_out_time__isnull=True`). This is the only app using serializers/viewsets. The whole DRF API requires authentication (`REST_FRAMEWORK` sets `IsAuthenticated`); auth classes are `TokenAuthentication` (mobile app) + `SessionAuthentication` (browsable API in dev/back-office). Clients obtain a token via `POST attendance/api/v1/token/` with `{username, password}` — that endpoint is the only public one. Employees are scanned by `badge_token` (opaque, rotatable QR credential on `Employe`), not by primary key. See `pointage/API.md` for the mobile-facing API doc.
