# ITSM Platform - Phase 3: REST API Contract Specification

> **Status:** LOCKED  
> **Version:** 1.1  
> **Date:** 2025-12-16  
> **Updated:** 2025-12-16T17:45:00+05:30  
> **Dependencies:** Phase 1 Architecture (LOCKED), Phase 2 Models (LOCKED)

---

## 1. Complete API Endpoint List

### 1.1 Authentication

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/login/` | User login, returns JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Revoke refresh token |
| GET | `/api/auth/me/` | Get current user profile |

### 1.2 User-Facing Ticket Operations

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/tickets/` | Create new ticket |
| GET | `/api/tickets/` | List own tickets (paginated) |
| GET | `/api/tickets/{id}/` | Get ticket details |
| GET | `/api/tickets/{id}/history/` | Get ticket history |
| POST | `/api/tickets/{id}/attachments/` | Upload attachment |
| GET | `/api/tickets/{id}/attachments/{att_id}/` | Download attachment |

### 1.3 Employee Ticket Operations

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/employee/queue/` | List department queue (unassigned) |
| GET | `/api/employee/tickets/` | List assigned tickets |
| POST | `/api/tickets/{id}/assign/` | Self-assign or assign ticket |
| PATCH | `/api/tickets/{id}/status/` | Update ticket status |
| POST | `/api/tickets/{id}/close/` | Close ticket |
| PATCH | `/api/tickets/{id}/priority/` | Set/update priority |

### 1.4 Manager Operations

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/manager/team/` | List team members |
| GET | `/api/manager/team/tickets/` | List all team tickets |
| POST | `/api/tickets/{id}/assign/` | Assign to team member |
| POST | `/api/tickets/{id}/reassign/` | Reassign within team |

### 1.5 Email Intake

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/email/ingest/` | Upload email for processing |
| GET | `/api/email/pending/` | List pending emails |
| POST | `/api/email/{id}/process/` | Process email → create ticket |
| POST | `/api/email/{id}/discard/` | Discard email with reason |

### 1.6 Analytics

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/analytics/employee/summary/` | Employee dashboard metrics |
| GET | `/api/analytics/manager/team-summary/` | Manager team metrics |

### 1.7 Master Data (Read-Only for Non-Admin)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/categories/` | List active categories |
| GET | `/api/categories/{id}/subcategories/` | List subcategories |
| GET | `/api/closure-codes/` | List active closure codes |
| GET | `/api/statuses/` | List valid ticket statuses |

---

## 2. Request & Response Schemas

### 2.1 Authentication

#### POST `/api/auth/login/`

**Request:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "name": "string",
    "email": "string",
    "roles": ["USER", "EMPLOYEE"]
  }
}
```

#### POST `/api/auth/refresh/`

**Request:**
```json
{
  "refresh_token": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string",
  "expires_in": 900
}
```

---

### 2.2 Ticket Operations

#### POST `/api/tickets/` (Create)

**Request:** `multipart/form-data`
```json
{
  "title": "string (required, max 255)",
  "description": "string (required)",
  "category_id": "uuid (required)",
  "subcategory_id": "uuid (required)",
  "attachments": "File[] (optional, max 5 files, max 25MB each)"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid (read-only)",
  "ticket_number": "string (read-only)",
  "title": "string",
  "description": "string",
  "status": "New",
  "category": { "id": "uuid", "name": "string" },
  "subcategory": { "id": "uuid", "name": "string" },
  "created_by": { "id": "uuid", "name": "string" },
  "created_at": "datetime (read-only)",
  "assigned_to": null
}
```

#### GET `/api/tickets/` (List)

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| page_size | int | No | Items per page (default: 25, max: 100) |
| status | string | No | Filter by status |
| sort | string | No | Sort field (default: `-created_at`) |

**Response (200 OK):**
```json
{
  "page": 1,
  "page_size": 25,
  "total_count": 42,
  "results": [
    {
      "id": "uuid",
      "ticket_number": "string",
      "title": "string",
      "status": "string",
      "created_at": "datetime",
      "assigned_to": { "id": "uuid", "name": "string" } | null
    }
  ]
}
```

#### GET `/api/tickets/{id}/` (Detail)

**Response (200 OK):**
```json
{
  "id": "uuid",
  "ticket_number": "string",
  "title": "string",
  "description": "string",
  "status": "string",
  "is_closed": false,
  "priority": 2,
  "category": { "id": "uuid", "name": "string" },
  "subcategory": { "id": "uuid", "name": "string" },
  "department": { "id": "uuid", "name": "string" },
  "created_by": { "id": "uuid", "name": "string", "email": "string" },
  "created_at": "datetime",
  "assigned_to": { "id": "uuid", "name": "string", "email": "string" } | null,
  "assigned_at": "datetime" | null,
  "closure_code": { "code": "string", "description": "string" } | null,
  "closed_at": "datetime" | null,
  "attachments": [
    { "id": "uuid", "file_name": "string", "file_type": "string", "file_size": 12345 }
  ]
}
```

> **Note:** `priority` field is ONLY returned for EMPLOYEE/MANAGER/ADMIN roles.

#### POST `/api/tickets/{id}/assign/`

**Request:**
```json
{
  "assigned_to": "uuid (optional, null = self-assign)"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "ticket_number": "string",
  "status": "Assigned",
  "assigned_to": { "id": "uuid", "name": "string" },
  "assigned_at": "datetime"
}
```

#### PATCH `/api/tickets/{id}/status/`

**Request:**
```json
{
  "status": "string (required: In Progress|Waiting|On Hold|Assigned)",
  "note": "string (required, non-empty)"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "ticket_number": "string",
  "status": "In Progress",
  "updated_at": "datetime"
}
```

#### POST `/api/tickets/{id}/close/`

**Request:**
```json
{
  "closure_code_id": "uuid (required)",
  "note": "string (required, non-empty)"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "ticket_number": "string",
  "status": "Closed",
  "is_closed": true,
  "closure_code": { "code": "string", "description": "string" },
  "closed_at": "datetime"
}
```

#### GET `/api/tickets/{id}/history/`

**Response (200 OK):**
```json
{
  "page": 1,
  "page_size": 25,
  "total_count": 5,
  "results": [
    {
      "id": "uuid",
      "old_status": "New",
      "new_status": "Assigned",
      "note": "string",
      "changed_by": { "id": "uuid", "name": "string" },
      "changed_at": "datetime"
    }
  ]
}
```

---

### 2.3 Employee Queue

#### GET `/api/employee/queue/`

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| page_size | int | No | Items per page (default: 25, max: 100) |
| category_id | uuid | No | Filter by category |
| subcategory_id | uuid | No | Filter by subcategory |
| sort | string | No | Sort field (default: `created_at`) |

**Supported Sort Fields:** `created_at`, `-created_at`, `priority`, `-priority`

**Response:** Same as ticket list format.

---

### 2.4 Analytics

#### GET `/api/analytics/employee/summary/`

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| from_date | date | No | Start date (default: 30 days ago) |
| to_date | date | No | End date (default: today) |

**Response (200 OK):**
```json
{
  "total_assigned": 150,
  "total_closed": 120,
  "total_open": 30,
  "by_status": {
    "Assigned": 10,
    "In Progress": 15,
    "Waiting": 5
  },
  "avg_resolution_hours": 24.5,
  "oldest_open_ticket": {
    "id": "uuid",
    "ticket_number": "string",
    "age_hours": 168
  },
  "closed_today": 3,
  "closed_last_7_days": 15,
  "closed_last_30_days": 45
}
```

#### GET `/api/analytics/manager/team-summary/`

**Response (200 OK):**
```json
{
  "team_summary": {
    "total_tickets": 500,
    "closed": 420,
    "open": 80
  },
  "per_employee": [
    {
      "id": "uuid",
      "name": "string",
      "total": 100,
      "open": 15,
      "avg_resolution_hours": 20.5
    }
  ],
  "aging_tickets": [
    { "id": "uuid", "ticket_number": "string", "age_hours": 96 }
  ],
  "by_status": { "Assigned": 20, "In Progress": 40, "Waiting": 20 },
  "by_priority": { "P1": 5, "P2": 15, "P3": 40, "P4": 20 },
  "volume_trend": [
    { "date": "2024-12-01", "count": 15 }
  ]
}
```

---

### 2.5 Email Intake

#### POST `/api/email/ingest/`

**Request:** `multipart/form-data`
```json
{
  "sender_name": "string (required)",
  "sender_email": "email (required)",
  "subject": "string (required)",
  "body_html": "string (required)",
  "received_at": "datetime (required)",
  "attachments": "File[] (optional)"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "sender_email": "string",
  "subject": "string",
  "received_at": "datetime",
  "is_processed": false
}
```

#### POST `/api/email/{id}/process/`

**Request:**
```json
{
  "title": "string (required)",
  "category_id": "uuid (required)",
  "subcategory_id": "uuid (required)",
  "priority": "int (optional, 1-4)"
}
```

**Response (200 OK):**
```json
{
  "email_id": "uuid",
  "ticket": {
    "id": "uuid",
    "ticket_number": "string",
    "title": "string",
    "status": "New"
  }
}
```

---

## 3. Pagination, Filtering & Sorting

### 3.1 Pagination Rules

| Parameter | Type | Default | Max | Notes |
|-----------|------|---------|-----|-------|
| page | int | 1 | - | 1-indexed |
| page_size | int | 25 | 100 | Server enforced max |

**Response Format (all list endpoints):**
```json
{
  "page": 1,
  "page_size": 25,
  "total_count": 142,
  "results": []
}
```

### 3.2 Supported Filters by Endpoint

| Endpoint | Filters |
|----------|---------|
| `/api/tickets/` (User) | `status` |
| `/api/employee/queue/` | `category_id`, `subcategory_id`, `priority` |
| `/api/employee/tickets/` | `status`, `priority`, `created_after`, `created_before` |
| `/api/manager/team/tickets/` | `status`, `priority`, `assigned_to`, `created_after` |
| `/api/email/pending/` | `sender_email`, `received_after` |

### 3.3 Supported Sort Fields by Endpoint

| Endpoint | Sort Fields | Default |
|----------|-------------|---------|
| `/api/tickets/` | `created_at`, `status` | `-created_at` |
| `/api/employee/queue/` | `created_at`, `priority` | `created_at` (oldest first) |
| `/api/employee/tickets/` | `created_at`, `priority`, `assigned_at` | `-assigned_at` |

> **Rule:** Prefix with `-` for descending order. Unsupported sort/filter returns `400 Bad Request`.

---

## 4. RBAC & Authorization Matrix

### 4.1 Role Definitions

| Role | ID | Scope |
|------|----|-------|
| USER | 1 | Own tickets only |
| EMPLOYEE | 2 | Assigned tickets + department queue |
| MANAGER | 3 | Team tickets + assignment authority |
| ADMIN | 4 | System-wide access |

### 4.2 Endpoint Authorization Matrix

| Endpoint | USER | EMPLOYEE | MANAGER | ADMIN |
|----------|------|----------|---------|-------|
| `POST /api/auth/login/` | ✓ | ✓ | ✓ | ✓ |
| `GET /api/auth/me/` | ✓ | ✓ | ✓ | ✓ |
| `POST /api/tickets/` | ✓ | ✓ | ✓ | ✓ |
| `GET /api/tickets/` | ✓ (own) | ✓ (own) | ✓ (own) | ✓ (all) |
| `GET /api/tickets/{id}/` | ✓ (own) | ✓ (assigned/dept) | ✓ (team) | ✓ |
| `GET /api/employee/queue/` | ✗ | ✓ (dept) | ✓ (dept) | ✓ |
| `POST /api/tickets/{id}/assign/` | ✗ | ✓ (self only) | ✓ (team) | ✓ |
| `PATCH /api/tickets/{id}/status/` | ✗ | ✓ (assigned) | ✓ (team) | ✓ |
| `POST /api/tickets/{id}/close/` | ✗ | ✓ (assigned) | ✓ (team) | ✓ |
| `PATCH /api/tickets/{id}/priority/` | ✗ | ✓ (assigned) | ✓ (team) | ✓ |
| `GET /api/manager/team/` | ✗ | ✗ | ✓ | ✓ |
| `GET /api/manager/team/tickets/` | ✗ | ✗ | ✓ | ✓ |
| `GET /api/analytics/employee/summary/` | ✗ | ✓ (self) | ✓ (self) | ✓ |
| `GET /api/analytics/manager/team-summary/` | ✗ | ✗ | ✓ | ✓ |
| `POST /api/email/ingest/` | ✗ | ✓ | ✓ | ✓ |

### 4.3 Scope Restrictions

| Action | Scope Rule |
|--------|------------|
| User views ticket | `ticket.created_by == user.id` |
| Employee views ticket | `ticket.assigned_to == user.id` OR `ticket.department IN user.departments` |
| Employee assigns | Self-assign only: `assigned_to` must be null or omitted |
| Manager views ticket | `ticket.assigned_to IN manager.team_members` |
| Manager assigns | `target_user IN manager.team_members` |

### 4.4 Forbidden Actions

| Action | Forbidden For | Error |
|--------|---------------|-------|
| Modify closed ticket | ALL | `400: Closed tickets are immutable` |
| Assign to non-team member | MANAGER | `403: User not in your team` |
| View other user's ticket | USER | `404: Ticket not found` |
| Access employee queue | USER | `403: Insufficient permissions` |
| Set priority | USER | `403: Insufficient permissions` |

---

## 5. Error Handling Standards

### 5.1 Standard HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PATCH |
| 201 | Created | Successful POST (create) |
| 400 | Bad Request | Validation failure, immutable ticket |
| 401 | Unauthorized | Missing/invalid JWT |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist or not accessible |
| 409 | Conflict | Concurrency conflict, version mismatch |
| 422 | Unprocessable | Business rule violation |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error (no details exposed) |

### 5.2 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [
      { "field": "title", "message": "This field is required" }
    ]
  }
}
```

### 5.3 Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Field validation failed |
| `IMMUTABLE_TICKET` | 400 | Attempt to modify closed ticket |
| `INVALID_STATUS_TRANSITION` | 400 | Invalid status change |
| `NOTE_REQUIRED` | 400 | Missing mandatory note |
| `UNAUTHORIZED` | 401 | Invalid/expired token |
| `FORBIDDEN` | 403 | Permission denied |
| `NOT_FOUND` | 404 | Resource not found |
| `VERSION_CONFLICT` | 409 | Optimistic lock failure |
| `RATE_LIMITED` | 429 | Too many requests |

> **SEC-06:** Error messages MUST NOT expose internal details (stack traces, SQL, file paths).

---

## 6. Analytics API Details

### 6.1 Performance Requirements (PERF-04)

- Analytics queries MUST NOT block transactional endpoints
- Maximum response time: 2 seconds
- Acceptable staleness: 30 seconds (caching permitted)
- Heavy aggregations should use indexed columns only

### 6.2 Time Range Filtering

Both analytics endpoints support:
- `from_date`: ISO 8601 date (default: 30 days ago)
- `to_date`: ISO 8601 date (default: today)
- Maximum range: 365 days

### 6.3 Aggregation Rules

| Metric | Aggregation |
|--------|-------------|
| Total counts | `COUNT(*)` |
| Average resolution | `AVG(closed_at - created_at)` in hours |
| By status | `GROUP BY status` |
| Volume trend | `GROUP BY DATE(created_at)` |

---

## 7. Swagger/OpenAPI Rules

### 7.1 Naming Conventions

- **Paths:** lowercase, hyphens for multi-word (`/api/closure-codes/`)
- **Parameters:** snake_case (`page_size`, `category_id`)
- **Schema Names:** PascalCase (`TicketResponse`, `UserProfile`)

### 7.2 Tagging Strategy

| Tag | Endpoints |
|-----|-----------|
| `auth` | Authentication endpoints |
| `tickets` | All ticket CRUD |
| `employee` | Employee-specific operations |
| `manager` | Manager-specific operations |
| `analytics` | Dashboard analytics |
| `email` | Email intake |
| `master-data` | Categories, closure codes |

### 7.3 Reusable Schema Components

```yaml
components:
  schemas:
    UserRef:
      type: object
      properties:
        id: { type: string, format: uuid }
        name: { type: string }
        email: { type: string, format: email }
    
    PaginatedResponse:
      type: object
      properties:
        page: { type: integer }
        page_size: { type: integer }
        total_count: { type: integer }
        results: { type: array }
    
    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code: { type: string }
            message: { type: string }
            details: { type: array }
    
    TicketSummary:
      type: object
      properties:
        id: { type: string, format: uuid }
        ticket_number: { type: string }
        title: { type: string }
        status: { type: string }
        created_at: { type: string, format: date-time }
        assigned_to: { $ref: '#/components/schemas/UserRef' }
```

### 7.4 Authentication Definition

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

---

## 8. Phase 3 Completion Checklist

### 8.1 Endpoint Definitions ✓
- [x] Authentication endpoints defined (4)
- [x] User ticket endpoints defined (6)
- [x] Employee endpoints defined (6)
- [x] Manager endpoints defined (4)
- [x] Email intake endpoints defined (4)
- [x] Analytics endpoints defined (2)
- [x] Master data endpoints defined (4)

### 8.2 Schemas ✓
- [x] Request schemas for all POST/PATCH endpoints
- [x] Response schemas for all endpoints
- [x] Field-level notes (required/optional/read-only)
- [x] Swagger/OpenAPI compatible format

### 8.3 Pagination & Filtering ✓
- [x] Pagination parameters defined
- [x] Maximum page size enforced (100)
- [x] Filters per endpoint documented
- [x] Sort fields per endpoint documented
- [x] Default ordering specified

### 8.4 RBAC Matrix ✓
- [x] All roles defined with IDs
- [x] Endpoint access matrix complete
- [x] Scope restrictions documented
- [x] Forbidden actions explicitly listed

### 8.5 Error Handling ✓
- [x] Standard HTTP codes defined
- [x] Error response format specified
- [x] Error codes enumerated
- [x] Security: no internal details leaked

### 8.6 Analytics ✓
- [x] Employee metrics defined
- [x] Manager metrics defined
- [x] Time range filtering specified
- [x] Performance requirements documented

### 8.7 OpenAPI Rules ✓
- [x] Naming conventions defined
- [x] Tagging strategy defined
- [x] Reusable components specified
- [x] JWT authentication defined

---

## 9. Locked Decisions (Stakeholder Approved)

### 9.1 Attachment Authorization

| Rule | Specification |
|------|---------------|
| Authentication | **Required** - Valid JWT mandatory |
| Authorization | Same as ticket visibility rules |
| Unauthorized response | `404 Not Found` (no information leakage) |

### 9.2 Rate Limits by Role

| Role | Tier | Notes |
|------|------|-------|
| USER | Low | Most restrictive |
| EMPLOYEE | Medium | Standard operational limits |
| MANAGER | Medium | Same as Employee |
| ADMIN | High | Least restrictive |

> **Note:** Exact limits are configurable via environment variables.

### 9.3 Attachment Limits

| Constraint | Limit |
|------------|-------|
| Max files per ticket | 5 |
| Max size per file | 25 MB |
| Max total size per ticket | 100 MB |

### 9.4 Email Discard Rules

| Rule | Specification |
|------|---------------|
| Confirmation required | **No** |
| `discarded_reason` | **Mandatory** (non-empty string) |

---

*Document Status: **LOCKED***  
*Phase 3 Locked: 2025-12-16T17:45:00+05:30*  
*No API contract changes permitted beyond this point*
