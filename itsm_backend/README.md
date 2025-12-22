# ITSM Django Backend

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for SQL Server)
- ODBC Driver 18 for SQL Server

### 1. Start SQL Server
```bash
docker-compose up -d mssql
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create Database
```sql
-- Connect to SQL Server and run:
CREATE DATABASE ITSM;
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Seed Roles
```bash
python manage.py shell
```
```python
from accounts.models import Role
Role.objects.bulk_create([
    Role(id=1, name='USER'),
    Role(id=2, name='EMPLOYEE'),
    Role(id=3, name='MANAGER'),
    Role(id=4, name='ADMIN'),
])
```

### 6. Run Development Server
```bash
python manage.py runserver
```

### 7. Access Swagger UI
- http://localhost:8000/api/schema/swagger-ui/

## API Endpoints

### Implemented - Step 1: Authentication
| Method | Path | Status |
|--------|------|--------|
| POST | `/api/auth/login/` | ✓ Implemented |
| POST | `/api/auth/refresh/` | ✓ Implemented |
| POST | `/api/auth/logout/` | ✓ Implemented |
| GET | `/api/auth/me/` | ✓ Implemented |

### Implemented - Step 2: Ticket Creation & Listing
| Method | Path | Status |
|--------|------|--------|
| POST | `/api/tickets/` | ✓ Implemented |
| GET | `/api/tickets/` | ✓ Implemented |
| GET | `/api/tickets/{id}/` | ✓ Implemented |
| GET | `/api/tickets/{id}/history/` | ✓ Implemented |
| GET | `/api/employee/queue/` | ✓ Implemented |
| GET | `/api/employee/tickets/` | ✓ Implemented |
| GET | `/api/categories/` | ✓ Implemented |
| GET | `/api/categories/{id}/subcategories/` | ✓ Implemented |
| GET | `/api/closure-codes/` | ✓ Implemented |
| GET | `/api/statuses/` | ✓ Implemented |

### Implemented - Step 3: Assignment, Status, Closure, Priority
| Method | Path | Status |
|--------|------|--------|
| POST | `/api/tickets/{id}/assign/` | ✓ Implemented |
| POST | `/api/tickets/{id}/reassign/` | ✓ Implemented |
| PATCH | `/api/tickets/{id}/status/` | ✓ Implemented |
| POST | `/api/tickets/{id}/close/` | ✓ Implemented |
| PATCH | `/api/tickets/{id}/priority/` | ✓ Implemented |
| GET | `/api/manager/team/` | ✓ Implemented |
| GET | `/api/manager/team/tickets/` | ✓ Implemented |

### Implemented - Step 4: Attachments
| Method | Path | Status |
|--------|------|--------|
| POST | `/api/tickets/{id}/attachments/` | ✓ Implemented |
| GET | `/api/tickets/{id}/attachments/` | ✓ Implemented |
| GET | `/api/tickets/{tid}/attachments/{aid}/download/` | ✓ Implemented |
| DELETE | `/api/tickets/{tid}/attachments/{aid}/` | ✓ Implemented |

**Limits:** 5 files/ticket, 25MB/file, 100MB/ticket total

### Implemented - Step 5: Email Intake
| Method | Path | Status |
|--------|------|--------|
| POST | `/api/email/ingest/` | ✓ Implemented |
| GET | `/api/email/pending/` | ✓ Implemented |
| GET | `/api/email/{id}/` | ✓ Implemented |
| POST | `/api/email/{id}/process/` | ✓ Implemented |
| POST | `/api/email/{id}/discard/` | ✓ Implemented |

**Features:** Idempotency via message_id, email attachments copied to tickets

## Running Tests
```bash
python manage.py test tests
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DB_NAME | ITSM | Database name |
| DB_USER | sa | Database user |
| DB_PASSWORD | YourStrong@Passw0rd | Database password |
| DB_HOST | localhost | Database host |
| DB_PORT | 1433 | Database port |
| DJANGO_SECRET_KEY | (dev key) | Secret key for production |
| DEBUG | True | Debug mode |

## Project Structure
```
itsm_backend/
├── accounts/        # Authentication app
├── tickets/         # Ticket management (Step 2)
├── analytics/       # Dashboard analytics (Step 6)
├── email_intake/    # Email intake (Step 5)
├── core/            # Shared utilities
└── tests/           # Test suite
```
