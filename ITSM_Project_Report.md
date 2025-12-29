# ITSM Tool - Industrial Training Project Report

---

**Project Title:** Enterprise IT Service Management (ITSM) Platform  
**Submitted By:** Akshat Shah  
**Date:** December 2025  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Vision & Goals](#2-project-vision--goals)
3. [System Architecture](#3-system-architecture)
4. [Middleware & API Layer](#4-middleware--api-layer)
5. [Feature Implementation by Role](#5-feature-implementation-by-role)
6. [Organization Hierarchy](#6-organization-hierarchy)
7. [Progressive Web App (PWA) Implementation](#7-progressive-web-app-pwa-implementation)
8. [Authentication System](#8-authentication-system)
9. [Database Design](#9-database-design)
10. [Conclusion & Future Scope](#10-conclusion--future-scope)

---

## 1. Executive Summary

### 1.1 Project Overview

This project presents the design and implementation of an enterprise-grade IT Service Management (ITSM) platform, developed to streamline IT support operations within organizations. The platform enables end-users to log IT-related complaints and track their resolution, while providing IT support staff with tools to manage, prioritize, and resolve tickets efficiently.

The system implements a comprehensive role-based access control (RBAC) model with four distinct roles—User, Employee, Manager, and Admin—each with specific capabilities and access levels. A key innovation is the email intake feature, which allows IT employees to convert emails directly into tickets through a drag-and-drop interface.

### 1.2 Key Achievements

| Objective | Status | Implementation |
|-----------|--------|----------------|
| Role-based ticket management | ✅ Complete | 4 roles with full RBAC |
| Single sign-on authentication | ✅ Complete | Azure AD + database fallback |
| Email-to-ticket conversion | ✅ Complete | Drag-and-drop .eml parsing |
| Ticket tracking & history | ✅ Complete | Timeline view with status history |
| Manager analytics dashboard | ✅ Complete | Per-employee stats & trends |
| Progressive Web App | ✅ Complete | Offline-capable, installable |

### 1.3 Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS |
| **Backend** | Django 4.x, Django REST Framework |
| **Database** | Microsoft SQL Server |
| **Authentication** | JWT + Azure Active Directory |
| **PWA** | Vite-PWA plugin with Workbox |

---

## 2. Project Vision & Goals

### 2.1 Initial Vision

The ITSM Tool was conceived with the following core objectives:

1. **Unified Login System**: A single login page with dual-logic authentication—first checking Active Directory for corporate users, then falling back to database authentication for external users.

2. **Role-Based Portal Access**: Four distinct roles with hierarchical permissions:
   - **User**: End-users who log and track tickets
   - **Employee**: IT support staff who handle tickets
   - **Manager**: Team leads who oversee employees and assign work
   - **Admin**: System administrators with full access via Django Admin

3. **Comprehensive Ticket Lifecycle**: Complete ticket management from creation to closure, with full audit trails and status tracking.

4. **Email Integration**: Enable IT employees to convert incoming emails directly into tickets without manual data entry.

5. **Analytics & Reporting**: Provide managers with insights into team performance, ticket volumes, and resolution times.

### 2.2 Additional Goal: Progressive Web App

During development, an additional goal was identified—converting the application into a Progressive Web App (PWA). This enables:
- Installation on mobile devices and desktops
- Offline access to critical functionality
- Native app-like experience without app store distribution

### 2.3 Vision to Implementation Mapping

| Vision Component | Planned Features | Implemented | Status |
|------------------|------------------|-------------|--------|
| Login System | AD + DB authentication | Fully implemented | ✅ 100% |
| User Role | 7 features | 7 features | ✅ 100% |
| Employee Role | 12 features | 12 features | ✅ 100% |
| Manager Role | 4 features | 4 features | ✅ 100% |
| Admin Portal | Django Admin | Django Admin | ✅ 100% |
| PWA | (Added during dev) | Fully implemented | ✅ BONUS |

---

## 3. System Architecture

### 3.1 High-Level Architecture

The ITSM platform follows a modern three-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    React Frontend (PWA)                              │   │
│  │  • React 18 + TypeScript    • Vite Build Tool                       │   │
│  │  • TailwindCSS              • React Router                          │   │
│  │  • Service Worker           • Workbox Caching                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ HTTPS / REST API
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUSINESS LOGIC LAYER                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Django Backend (DRF)                              │   │
│  │  • Django REST Framework    • JWT Authentication                    │   │
│  │  • Azure AD Integration     • Email Parser                          │   │
│  │  • RBAC Permissions         • Service Layer                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ mssql-django
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Microsoft SQL Server                              │   │
│  │  • UUID Primary Keys        • Indexed Queries                       │   │
│  │  • Constraints              • Audit Tables                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Frontend Architecture

The frontend is built as a single-page application (SPA) using React with TypeScript for type safety.

**Key Components:**

| Component | Purpose |
|-----------|---------|
| `pages/` | Route-level components (LoginPage, DashboardPage) |
| `components/` | Reusable UI components (TicketCard, Modal) |
| `api/` | API client modules for backend communication |
| `auth/` | Authentication context and hooks |
| `router/` | React Router configuration with role guards |

**Directory Structure:**
```
itsm-frontend/src/
├── api/                 # API client modules
├── auth/                # Authentication context
├── components/          # Reusable components
│   ├── common/          # Buttons, Modals, Forms
│   ├── layout/          # AppLayout, Sidebar
│   └── tickets/         # TicketCard, TicketList
├── pages/               # Route components
│   ├── user/            # User-role pages
│   ├── employee/        # Employee-role pages
│   └── manager/         # Manager-role pages
├── router/              # Route definitions
├── types/               # TypeScript interfaces
└── utils/               # Utility functions
```

### 3.3 Backend Architecture

The backend is implemented using Django with Django REST Framework (DRF) for API development.

**Django Apps:**

| App | Responsibility |
|-----|----------------|
| `accounts` | User management, authentication, roles |
| `tickets` | Ticket CRUD, status management, attachments |
| `email_intake` | Email parsing, conversion to tickets |
| `analytics` | Dashboard metrics, reporting |
| `core` | Shared models (Category, Department, etc.) |

**Backend Structure:**
```
itsm_backend/
├── accounts/            # User & authentication
│   ├── models.py        # User, Role, UserRole
│   ├── views.py         # Login, profile endpoints
│   ├── serializers.py   # User serialization
│   └── azure_ad.py      # AD integration
├── tickets/             # Ticket management
│   ├── models.py        # Ticket, TicketHistory
│   ├── views.py         # CRUD endpoints
│   ├── services.py      # Business logic
│   └── permissions.py   # RBAC permissions
├── email_intake/        # Email processing
│   ├── parser.py        # .eml file parsing
│   ├── views.py         # Ingest, process, discard
│   └── services.py      # Email-to-ticket logic
└── analytics/           # Metrics & reporting
    ├── views.py         # Summary endpoints
    └── services.py      # Aggregation logic
```

---

## 4. Middleware & API Layer

### 4.1 API Architecture

The backend exposes a RESTful API following industry best practices:

- **Base URL**: `/api/`
- **Authentication**: Bearer JWT tokens
- **Content-Type**: `application/json` (except file uploads)
- **Error Format**: Standardized error responses with codes

### 4.2 API Endpoints Summary

| Module | Endpoint Count | Key Endpoints |
|--------|----------------|---------------|
| **Authentication** | 4 | `POST /auth/login/`, `POST /auth/refresh/`, `GET /auth/me/` |
| **Tickets** | 6 | `POST /tickets/`, `GET /tickets/{id}/`, `PATCH /tickets/{id}/status/` |
| **Employee** | 3 | `GET /employee/queue/`, `GET /employee/tickets/`, `POST /tickets/{id}/assign/` |
| **Manager** | 4 | `GET /manager/team/`, `GET /manager/team/tickets/`, `GET /analytics/manager/team-summary/` |
| **Email Intake** | 4 | `POST /email/ingest/`, `GET /email/pending/`, `POST /email/{id}/process/` |
| **Master Data** | 4 | `GET /categories/`, `GET /closure-codes/`, `GET /statuses/` |

**Total: 25 API Endpoints**

### 4.3 Middleware Components

```
Request Flow:
┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  Client  │───▶│   CORS   │───▶│   Auth    │───▶│   Rate   │───▶│   View   │
│          │    │Middleware│    │Middleware │    │  Limit   │    │          │
└──────────┘    └──────────┘    └───────────┘    └──────────┘    └──────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │ JWT Validation│
                              │ User Context  │
                              └───────────────┘
```

**Middleware Stack:**

1. **CORS Middleware**: Handles cross-origin requests from the frontend
2. **Authentication Middleware**: Validates JWT tokens and sets user context
3. **Rate Limiting**: Role-based request limits (User < Employee < Manager < Admin)
4. **Error Handling**: Catches exceptions and returns standardized error responses

### 4.4 Serializers & Data Validation

Django REST Framework serializers handle:
- Input validation with field-level validators
- Nested object serialization for related data
- Custom validation for business rules (e.g., mandatory notes)

**Example Serializer Chain:**
```
Request JSON → TicketSerializer → Validation → Service Layer → Model → Database
```

### 4.5 RBAC Implementation

The authorization system is implemented using custom DRF permission classes:

| Permission Class | Purpose |
|------------------|---------|
| `IsAuthenticated` | Base authentication check |
| `IsTicketOwner` | User owns the ticket |
| `IsAssignedEmployee` | Employee is assigned to ticket |
| `IsTeamManager` | Manager of the assigned employee's team |
| `IsAdminUser` | Full system access |

**Authorization Matrix:**

| Endpoint | User | Employee | Manager | Admin |
|----------|------|----------|---------|-------|
| Create ticket | ✅ | ✅ | ✅ | ✅ |
| View own tickets | ✅ | ✅ | ✅ | ✅ |
| View department queue | ❌ | ✅ | ✅ | ✅ |
| Assign tickets | ❌ | Self only | Team | ✅ |
| Update status | ❌ | Assigned | Team | ✅ |
| View analytics | ❌ | Self | Team | ✅ |

---

## 5. Feature Implementation by Role

### 5.1 User Role Swimlane Diagram

The following swimlane diagram shows the complete ticket lifecycle from a User's perspective:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        User Role - Ticket Lifecycle                                  │
├──────────┬──────────────────────────────────────────────────────────────────────────┤
│          │                                                                           │
│  USER    │ [Login] ──→ [View Dashboard] ──→ [Create Ticket] ──→ [View Ticket List]  │
│  🟡      │     │              │                    │                    │            │
│          │     ↓              ↓                    ↓                    ↓            │
├──────────┼──────────────────────────────────────────────────────────────────────────┤
│          │     │              │                    │                    │            │
│ FRONTEND │ [Login Form] → [Dashboard] ──→ [Ticket Form] ──→ [Ticket List Page]     │
│  🔵      │     │              │          Fill category,│         Track status,      │
│          │     ↓              ↓          subcategory,  │         view timeline      │
│          │                               attachments   ↓                            │
├──────────┼──────────────────────────────────────────────────────────────────────────┤
│          │     │              │                    │                    │            │
│ BACKEND  │ [POST /auth/] → [GET /tickets/] ──→ [POST /tickets/] ──→ [GET /tickets/] │
│ API 🟠   │  Validate AD     Return user's      Create ticket,    Return ticket      │
│          │  or DB auth      open tickets       route to dept     details + history  │
│          │     ↓              ↓                    ↓                    ↓            │
├──────────┼──────────────────────────────────────────────────────────────────────────┤
│          │     │              │                    │                    │            │
│ DATABASE │ [User table] → [Ticket table] ──→ [INSERT Ticket] ──→ [SELECT + JOIN]   │
│  ⬜      │  Check creds    Filter by          Auto-generate      TicketHistory      │
│          │                 created_by         ticket_number      for timeline       │
└──────────┴──────────────────────────────────────────────────────────────────────────┘
```

**User Features Implemented:**

| Feature | Description | Implementation |
|---------|-------------|----------------|
| Log new tickets | Create tickets with pre-filled user info | `CreateTicketPage.tsx` |
| Category routing | Category → SubCategory → Department | `Category`, `SubCategory` models |
| Dashboard view | View open tickets at a glance | `DashboardPage.tsx` |
| Ticket tracking | Parcel-style tracking tree | `TicketHistory` model |
| Employee contact | View assigned employee details | `TicketDetailPage.tsx` |
| Ticket history | View all previously logged tickets | `TicketListPage.tsx` |
| Attachments | Upload files with tickets | `TicketAttachment` model |

### 5.2 Employee Role Swimlane Diagram

Employees have access to all User functions plus additional capabilities:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        Employee Role - Full Ticket Workflow                                  │
├──────────┬──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ EMPLOYEE │ [All User     [View Dept    [Self-assign] ──→ [Update      [Close Ticket]       │
│  🟢      │  Functions] ─→ Queue] ─────→     ↓            Status] ───→ with closure code    │
│          │     │             │              │               │              │                │
│          │     ↓             ↓              ↓               ↓              ↓                │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ FRONTEND │ [Dashboard] → [QueuePage] → [Assign Btn] → [Status Modal] → [Close Modal]       │
│  🔵      │  + MyWork      Filter by     Click to      Select status,   Enter closure       │
│          │  Page          department    claim ticket  add note (req)   code + note         │
│          │     │             │              │               │              │                │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ BACKEND  │ [GET         [GET /employee/ [POST /assign/] [PATCH /status/] [POST /close/]    │
│ API 🟠   │  /tickets/]   queue/]         Set assigned_to  Validate note,   Set closure_code │
│          │  Own tickets   Dept tickets   Update status    add history      Set closed_at    │
│          │     │             │              │               │              │                │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ DATABASE │ [Ticket      [Ticket WHERE   [UPDATE         [INSERT          [UPDATE Ticket    │
│  ⬜      │  WHERE        dept=emp.dept   Ticket SET      TicketHistory]   is_closed=true]   │
│          │  created_by]  AND unassigned] assigned_to]                                       │
└──────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

**Email Intake Workflow:**

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        Employee Role - Email Intake Workflow                                 │
├──────────┬──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ EMPLOYEE │ [Drag & Drop  [Review Email   [Convert to    ─── OR ───  [Discard Email]        │
│  🟢      │  .eml file] ─→ Preview] ────→  Ticket]                   with reason            │
│          │     │             │              │                           │                   │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ FRONTEND │ [EmailInbox   [Preview Modal  [Process Form   ─── OR ───  [Discard Modal]       │
│  🔵      │  Drop Zone]    HTML render]    Select category]            Enter reason          │
│          │     │             │              │                           │                   │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ BACKEND  │ [POST /email/ [GET /email/    [POST /email/   ─── OR ───  [POST /email/         │
│ API 🟠   │  ingest/]      pending/]       {id}/process/]              {id}/discard/]        │
│          │  Parse .eml    List pending    Create ticket               Store reason          │
│          │     │             │              │                           │                   │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ DATABASE │ [INSERT       [SELECT WHERE   [INSERT Ticket  ─── OR ───  [UPDATE EmailIngest   │
│  ⬜      │  EmailIngest]  is_processed    + UPDATE email]             is_discarded=true]    │
│          │                =false]                                                           │
└──────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

**Employee Features (Additional to User):**

| Feature | Description | Implementation |
|---------|-------------|----------------|
| Email drag & drop | Ingest emails from Outlook | `EmailInboxPage.tsx` |
| Email preview | View email in HTML format | `parser.py`, body_html |
| Review bucket | Convert or discard emails | Pending list + actions |
| Department queue | View unassigned tickets | `QueuePage.tsx` |
| Self-assign | Claim tickets from queue | `POST /assign/` |
| My Work page | View assigned tickets | `MyTicketsPage.tsx` |
| Status updates | Update ticket status | `PATCH /status/` |
| Mandatory notes | Required notes for status changes | `TicketHistory` |
| Priority levels | Set internal priority (P1-P4) | Hidden from Users |
| Closure codes | Close with predefined/custom codes | `ClosureCode` model |

### 5.3 Manager Role Swimlane Diagram

Managers have access to all User and Employee functions plus team management:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        Manager Role - Full Workflow                                          │
├──────────┬──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ MANAGER  │ [All User +   [View Team     [Assign to      [View Team    [View Team           │
│  🟣      │  Employee] ─→  Members] ───→  Team Member] ─→ Tickets] ──→  Analytics]           │
│          │  Functions         │              │               │              │               │
│          │     │              ↓              ↓               ↓              ↓               │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ FRONTEND │ [Dashboard    [TeamPage]  →  [Assign Modal   [Team Tickets  [AdvancedAnalytics  │
│  🔵      │  + All Emp     List team      Select member]  Table + Filter] Charts + Stats]   │
│          │  Pages]        members            │               │              │               │
│          │     │              │              ↓               ↓              ↓               │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ BACKEND  │ [All Emp     [GET /manager/  [POST /assign/   [GET /manager/  [GET /analytics/  │
│ API 🟠   │  endpoints]   team/]          {assigned_to}]   team/tickets/]  manager/summary/] │
│          │               List team       Assign ticket    All team        Aggregate stats   │
│          │     │              │              │               │              │               │
├──────────┼──────────────────────────────────────────────────────────────────────────────────┤
│          │                                                                                   │
│ DATABASE │ [All Emp     [SELECT User    [UPDATE Ticket   [SELECT Ticket  [Aggregate        │
│  ⬜      │  queries]     WHERE team=     SET assigned_to  WHERE           per-employee,     │
│          │               manager.team]   IN team_members] assigned_to     resolution time]  │
│          │                                                IN team]                          │
└──────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

**Manager Features (Additional to Employee):**

| Feature | Description | Implementation |
|---------|-------------|----------------|
| View team members | List all employees in team | `TeamPage.tsx` |
| Assign to team | Assign tickets to team members | `POST /assign/` |
| Team tickets | View all tickets assigned to team | `GET /manager/team/tickets/` |
| Team analytics | Per-employee stats, aging, trends | `AdvancedAnalyticsPage.tsx` |

### 5.4 Admin Role

The Admin role provides full system access through the Django Admin interface at `/admin/`. Administrators can:

- Manage all users and roles
- Configure categories, subcategories, and departments
- View and modify all tickets
- Access system logs and audit trails
- Configure closure codes and master data

---

## 6. Organization Hierarchy

### 6.1 Hierarchical Structure

The system implements a five-level organizational hierarchy as envisioned:

```
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS GROUP                              │
│                    (Top-level entity)                            │
│                           │                                      │
│              ┌────────────┴────────────┐                        │
│              ▼                         ▼                        │
│        ┌─────────────┐           ┌─────────────┐                │
│        │   COMPANY   │           │   COMPANY   │                │
│        └──────┬──────┘           └─────────────┘                │
│               │                                                  │
│     ┌─────────┴─────────┐                                       │
│     ▼                   ▼                                       │
│ ┌──────────┐      ┌──────────┐                                  │
│ │DEPARTMENT│      │DEPARTMENT│   (IT, HR, Finance, etc.)       │
│ └────┬─────┘      └──────────┘                                  │
│      │                                                          │
│  ┌───┴───┐                                                      │
│  ▼       ▼                                                      │
│┌────┐  ┌────┐                                                   │
││TEAM│  │TEAM│     (Support L1, Support L2, etc.)               │
│└──┬─┘  └────┘                                                   │
│   │                                                             │
│   ▼                                                             │
│┌──────────────────────────────┐                                 │
││   USERS (with UserRoles)     │                                 │
││   • User, Employee, Manager  │                                 │
│└──────────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Model Implementation

| Model | Key Fields | Relationships |
|-------|------------|---------------|
| `BusinessGroup` | name, created_at | Has many Companies |
| `Company` | name, business_group | Belongs to BusinessGroup, has many Departments |
| `Department` | name, company | Belongs to Company, has many Teams |
| `Team` | name, department, manager | Belongs to Department, has Users |
| `User` | alias, name, email, phone | Has many UserRoles |
| `UserRole` | user, role, department, team | Links User to Role with scope |

### 6.3 Role Assignment

Users can have multiple roles with different scopes:

```python
# Example: User with Employee role in IT Department
UserRole(
    user=user,
    role=Role.EMPLOYEE,
    department=it_department,
    team=support_l1_team
)

# Same user as Manager of a different team
UserRole(
    user=user,
    role=Role.MANAGER,
    department=it_department,
    team=support_l2_team
)
```

---

## 7. Progressive Web App (PWA) Implementation

### 7.1 Overview

The PWA implementation was an additional goal not in the original vision. It transforms the web application into an installable, offline-capable app.

### 7.2 PWA Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PWA Architecture                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │   Web Manifest  │    │         Service Worker               │ │
│  │                 │    │  ┌─────────────────────────────────┐ │ │
│  │ • App name      │    │  │     Workbox Strategies          │ │ │
│  │ • Icons         │    │  │                                 │ │ │
│  │ • Theme color   │    │  │  ┌───────────┐  ┌───────────┐  │ │ │
│  │ • Display mode  │    │  │  │NetworkFirst│  │CacheFirst │  │ │ │
│  │ • Start URL     │    │  │  │  (API)    │  │ (Assets)  │  │ │ │
│  └─────────────────┘    │  │  └───────────┘  └───────────┘  │ │ │
│                         │  └─────────────────────────────────┘ │ │
│                         └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Configuration

**Web Manifest (vite.config.ts):**

| Property | Value |
|----------|-------|
| name | Blackbox ITSM |
| short_name | ITSM |
| theme_color | #ed1c24 |
| background_color | #0a0a0a |
| display | standalone |
| orientation | portrait-primary |

**Caching Strategies:**

| Resource Type | Strategy | Cache Duration |
|---------------|----------|----------------|
| API responses | NetworkFirst | 24 hours |
| Images | CacheFirst | 30 days |
| Fonts | CacheFirst | 1 year |

### 7.4 Key Features

1. **Installability**: Users can install the app on mobile devices and desktops
2. **Offline Support**: Cached content available without network
3. **Auto-Update**: Service worker updates automatically in the background
4. **Native Experience**: Standalone mode without browser UI

---

## 8. Authentication System

### 8.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐                                                   │
│  │  User    │                                                   │
│  │  Login   │                                                   │
│  └────┬─────┘                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐     YES    ┌─────────────────────┐         │
│  │  Check Azure    │───────────▶│  Authenticate with  │         │
│  │  Active Dir?    │            │  Azure AD           │         │
│  └────────┬────────┘            └──────────┬──────────┘         │
│           │ NO                             │                     │
│           ▼                                │                     │
│  ┌─────────────────┐                       │                     │
│  │  Check Database │                       │                     │
│  │  Credentials    │                       │                     │
│  └────────┬────────┘                       │                     │
│           │                                │                     │
│           ▼                                ▼                     │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              Generate JWT Tokens                     │        │
│  │  • Access Token (15 min expiry)                     │        │
│  │  • Refresh Token (7 day expiry)                     │        │
│  └─────────────────────────────────────────────────────┘        │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              Role-Based Redirect                     │        │
│  │  • User → User Dashboard                            │        │
│  │  • Employee → Employee Dashboard                    │        │
│  │  • Manager → Manager Dashboard                      │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Implementation Details

| Component | File | Purpose |
|-----------|------|---------|
| AD Integration | `azure_ad.py` | Azure AD authentication |
| DB Backend | `backends.py` | Database password verification |
| JWT Handler | `authentication.py` | Token generation and validation |
| Login View | `views.py` | Login endpoint |

### 8.3 Security Features

- **Password Hashing**: Secure password storage using Django's built-in hasher
- **JWT Tokens**: Short-lived access tokens with refresh capability
- **HTTPS Required**: All API communication over encrypted connection
- **CORS Protection**: Whitelisted origins only

---

## 9. Database Design

### 9.1 Database Technology

The system uses Microsoft SQL Server with the `mssql-django` driver for Django integration.

**Key Design Decisions:**
- UUID primary keys using `NEWSEQUENTIALID()` for clustered index efficiency
- Indexed columns for frequent queries
- Constraints for data integrity
- Audit tables for ticket history

### 9.2 Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  BusinessGroup  │────▶│     Company     │────▶│   Department    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┴─────────────┐
                              ▼                                        ▼
                        ┌─────────────┐                         ┌─────────────┐
                        │    Team     │◀────────────────────────│ SubCategory │
                        └──────┬──────┘                         └──────┬──────┘
                               │                                       │
                               ▼                                       │
                        ┌─────────────┐                                │
                        │    User     │                                │
                        └──────┬──────┘                                │
                               │                                       │
              ┌────────────────┼────────────────┐                      │
              ▼                ▼                ▼                      ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        ┌─────────────┐
      │  UserRole   │  │   Ticket    │◀─┼─────────────┼────────│  Category   │
      └─────────────┘  └──────┬──────┘  │EmailIngest  │        └─────────────┘
                              │         └─────────────┘
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │TicketHistory│ │ Attachment  │ │ ClosureCode │
      └─────────────┘ └─────────────┘ └─────────────┘
```

### 9.3 Key Tables

| Table | Purpose | Key Indexes |
|-------|---------|-------------|
| `User` | User accounts | email, alias, is_active |
| `Ticket` | Ticket records | ticket_number, status, created_by, assigned_to |
| `TicketHistory` | Audit trail | ticket_id, changed_at |
| `EmailIngest` | Ingested emails | is_processed, is_discarded |
| `Category` | Ticket categories | name |
| `SubCategory` | Subcategories | category_id, department_id |
| `ClosureCode` | Closure codes | code, is_active |

### 9.4 Data Integrity Constraints

| Constraint | Table | Purpose |
|------------|-------|---------|
| `CK_Ticket_ClosureData` | Ticket | Closed tickets must have closure data |
| `CK_Ticket_Priority` | Ticket | Priority must be 1-4 if set |
| `UQ_UserRole_Unique` | UserRole | Prevent duplicate role assignments |

---

## 10. Conclusion & Future Scope

### 10.1 Summary

This project successfully implemented an enterprise-grade ITSM platform that fulfills all objectives from the initial vision:

| Objective | Achievement |
|-----------|-------------|
| Unified login system | ✅ AD + database authentication implemented |
| Role-based access | ✅ 4 roles with full RBAC |
| Ticket lifecycle | ✅ Complete create-to-close workflow |
| Email integration | ✅ Drag-and-drop .eml intake |
| Manager analytics | ✅ Per-employee stats and trends |
| PWA (bonus) | ✅ Installable, offline-capable app |

### 10.2 Key Learnings

1. **Architecture**: Three-tier architecture with clear separation of concerns
2. **Security**: JWT-based authentication with proper RBAC
3. **UX**: Modern React frontend with TailwindCSS
4. **PWA**: Modern web capabilities for native-like experience

### 10.3 Future Enhancements

| Feature | Priority | Description |
|---------|----------|-------------|
| SLA Management | High | Define and track service level agreements |
| Knowledge Base | Medium | Self-service article repository |
| Chatbot Integration | Medium | AI-powered ticket creation |
| Mobile Native App | Low | React Native version for enhanced mobile UX |
| Reporting Module | Medium | Advanced reporting and exports |

### 10.4 References

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- React Documentation: https://react.dev/
- Vite PWA Plugin: https://vite-pwa-org.netlify.app/
- Microsoft SQL Server: https://docs.microsoft.com/sql/

---

*End of Report*
