# Orvanta — Web-Oriented Information System for Service Business Management

A multi-tenant SaaS platform for managing service businesses — appointments, clients, staff, and revenue analytics. Built as a bachelor's thesis project.

> **Stack:** Python · Django · PostgreSQL · Bootstrap 5 · Chart.js · Django REST Framework · Railway

---

## Screenshots

**Dashboard**
![Dashboard](docs/screenshots/dashboard.png)

**Financial Analytics**
![Finance](docs/screenshots/finance.png)

**Client Management**
![Clients](docs/screenshots/clients.png)

**Dark Mode**
![Dark Mode](docs/screenshots/dark-mode.png)

---

## Overview

Orvanta is built as a multi-tenant web application. Each registered business creates its own organization workspace, and all business data is isolated within that organization.

The system supports:

- organization-based data isolation
- user authentication with organization-scoped login
- role-based access control (Admin, Manager, Employee)
- client management
- service catalog and category management
- appointment scheduling and status tracking
- appointment conflict validation
- actual service price tracking per appointment
- financial analytics with filtering
- CSV data export
- audit logging
- REST API endpoints
- Docker-based local deployment
- Railway-based cloud deployment

---

## Main Features

### Multi-Tenant Architecture

Each organization has its own isolated workspace. Main tenant-related features:

- automatic organization creation during signup
- user-to-organization binding
- organization-scoped clients, services, appointments, audit logs, and analytics
- protection against accessing data from another organization

---

### User Roles

The system supports three main roles:

| Role | Description |
|---|---|
| Admin | Full access: manages organization settings, users, services, clients, appointments, finances, audit logs, and can delete appointments |
| Manager | Manages operational data: clients, services, appointments, and financial analytics |
| Employee | Works with assigned appointments |

Role-based access is enforced across the web interface and business logic using custom decorators.

---

### Authentication

Users log in using a username, password, and organization name. This prevents users from accessing the wrong organization workspace and supports the multi-tenant structure of the system.

---

### Client Management

- create, edit, activate, and deactivate clients
- search and filter clients
- export client list to CSV

Client records are scoped to the current organization.

---

### Service Management

The service catalog allows users to manage:

- service categories
- services with base price and duration
- active or inactive service status

---

### Appointment Management

- create appointments with client, service, employee, date, and time
- quick status changes from the appointment list
- inline editing of actual appointment price
- appointment conflict validation per employee
- appointment deletion (Admin only) with confirmation modal and audit log entry
- filtering, search, and pagination

---

### Financial Analytics

The financial analytics page (Admin and Manager only) allows analysis by date range, service, and employee. It includes:

- total revenue and average check
- number of paid appointments
- grouped analytics by services and employees
- revenue chart by date with period toggle (week / month / year)
- detailed appointment revenue table
- CSV export of financial data

---

### Dashboard

The dashboard provides a compact overview:

- operational KPIs with month-over-month comparison
- upcoming appointments
- appointment status statistics
- daily revenue summary (Admin and Manager)
- onboarding checklist for new organizations

---

### Onboarding

For newly created organizations the system shows a checklist:

- create the first service category
- create the first service
- add an employee
- add a client
- create the first appointment

---

### Audit Log

The audit module tracks important system events including user actions, entity changes, appointment status changes, and appointment deletions.

---

### CSV Export

CSV export is available for clients, services, appointments, and financial analytics. Exports respect organization boundaries, user roles, and active filters. Files include a BOM marker for correct display of Cyrillic characters in Microsoft Excel.

---

### REST API

Read-only REST API endpoints built with Django REST Framework. Available for clients, services, appointments, and dashboard analytics. Access is restricted to authenticated users with organization-based data isolation.

---

## Technology Stack

### Backend

- Python 3.14
- Django 6.0
- Django REST Framework
- PostgreSQL
- Gunicorn (production WSGI server)
- WhiteNoise (static file serving)
- dj-database-url (Railway DATABASE_URL support)
- python-decouple (environment variable management)
- django-ratelimit (API rate limiting)

### Frontend

- Django Templates
- HTML / CSS / Vanilla JavaScript
- Chart.js 4.4 (served locally, no CDN dependency)

### Database

- PostgreSQL 18
- Organization-scoped relational data model

### Infrastructure

- Docker + Docker Compose (local development)
- Railway (cloud deployment via Dockerfile + railway.toml)
- Environment-based configuration via `.env`

---

## Project Structure

```text
Thesis/
├── Dockerfile
├── railway.toml
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt
├── README.md
└── src/
    ├── manage.py
    ├── seed_salon.py
    ├── config/           # Django settings, URLs, WSGI, views, utils, CSV export
    ├── users/            # Custom user model, roles, decorators, profile, password change
    ├── clients/          # Client model, views, CSV export
    ├── services_catalog/ # Service categories and services
    ├── appointments/     # Appointments, status flow, conflict validation, deletion
    ├── audit/            # Audit log model and views
    ├── api/              # REST API endpoints (DRF)
    ├── templates/        # All HTML templates
    └── static/           # CSS, JS (including Chart.js), images
```

---

## Local Development

### Requirements

- Docker
- Docker Compose

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd Thesis
```

2. Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

3. Build and start the containers:

```bash
docker-compose up --build
```

4. Apply migrations:

```bash
docker-compose exec web python src/manage.py migrate
```

5. Create a superuser:

```bash
docker-compose exec web python src/manage.py createsuperuser
```

6. (Optional) Seed demo data:

```bash
docker-compose exec web python src/seed_salon.py
```

The application will be available at `http://localhost:8000`.

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `long-random-string` |
| `DEBUG` | Debug mode | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Full DB URL (used on Railway) | `postgresql://user:pass@host/db` |
| `DATABASE_NAME` | DB name (local only) | `orvanta_db` |
| `DATABASE_USER` | DB user (local only) | `orvanta_user` |
| `DATABASE_PASSWORD` | DB password (local only) | `secret` |
| `DATABASE_HOST` | DB host (local only) | `db` |
| `DATABASE_PORT` | DB port (local only) | `5432` |
| `RATELIMIT_ENABLE` | Enable API rate limiting | `True` / `False` |

---

## Cloud Deployment (Railway)

The project is configured for deployment on [Railway](https://railway.app) using Docker.

1. Push the repository to GitHub.
2. Create a new project on Railway and connect the GitHub repository.
3. Add a PostgreSQL plugin — Railway will provide `DATABASE_URL` automatically.
4. Set the required environment variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`.
5. Railway will build the Docker image and run migrations automatically on each deploy.
