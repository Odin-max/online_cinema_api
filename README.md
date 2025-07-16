# Online Cinema Library API

A Django RESTful API for managing library books, users, borrowings, payments (via Stripe), and notifications (via Telegram), with Celery for background tasks and Docker for containerization.

## Features

- **Books Service**: CRUD operations on books with admin-only write access and public read.
- **Users Service**: Email-based authentication, registration, JWT tokens, and profile management.
- **Borrowings Service**: Create, list, detail, and return borrowings; inventory management; overdue fines.
- **Payments Service**: Stripe Checkout integration for payments and fines; success/cancel endpoints; status updates.
- **Notifications Service**: Telegram notifications on new borrowings, overdue reminders, and payment confirmations.
- **Background Tasks**: Celery workers & beat schedule (daily overdue check).
- **API Documentation**: Swagger UI (`drf-spectacular`).
- **Containerized**: `docker-compose` for Django, Celery, PostgreSQL, Redis.

## Tech Stack

- Python 3.13, Django 5.2
- Django REST Framework
- Simple JWT (`rest_framework_simplejwt`)
- drf-spectacular for OpenAPI/Swagger
- Stripe Python SDK
- Celery & Redis
- Telegram Bot API
- PostgreSQL
- Docker & Docker Compose
- Pytest & pytest-django

## Requirements

- Docker & Docker Compose (v2+)
- (Optional) Poetry for local development

## Environment Variables

Copy `.env.sample` to `.env` and fill in:

```dotenv
SECRET_KEY=...
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...

TELEGRAM_BOT_TOKEN=123456:ABCDEF...
TELEGRAM_ADMIN_CHAT_ID=123456789

```

## Running with Docker

1. Build and start services:
   ```bash
   docker-compose up -d --build
   ```
2. Run migrations and collect static (handled in `Dockerfile`).
3. Create superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
4. Access to schema:
   - Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`

## Testing

Install pytest and pytest-django, then:
```bash
pip install pytest pytest-django
pytest
```

## API Endpoints

- **Books** (`/api/books/`)
- **Users** (`/api/users/`, `/api/users/token/`)
- **Borrowings** (`/api/borrowings/`, `/api/borrowings/{id}/return/`)
- **Payments** (`/api/payments/`, `/api/payments/create-checkout-session/`)
- **Notifications** (handled internally via Celery/Telegram)
