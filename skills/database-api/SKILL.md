---
name: database-api
description: Select backend and database architecture, define schemas and API contracts, and enforce validation, permissions, migrations, and data safety.
user-invocable: true
---

# Database and API

## Backend selection

Consider:

- Existing backend and database
- PostgreSQL
- Supabase
- MongoDB Atlas
- MySQL
- SQLite
- Firebase
- Custom Spring Boot/Node/Python backend
- Other justified options

Consult `rules/supabase.md` when Supabase is a candidate.

## Supabase fit

Select Supabase when PostgreSQL, authentication, realtime events, storage, generated APIs, or vector features materially reduce development work.

Do not select Supabase when it would replace an existing suitable backend without a clear migration benefit.

## Workflow

1. Define entities, relationships, sensitivity, and lifecycle.
2. Compare backend/database options.
3. Record selected and rejected alternatives.
4. Define schema and migrations.
5. Define indexes.
6. Define API contracts.
7. Define validation and error formats.
8. Define authentication and authorization.
9. For Supabase, define RLS and server-only service-role usage.
10. Define backups and export/exit strategy.
11. Define tests.

## Output format

```text
DATA/API PLAN:
- Backend:
- Database:
- Reason:
- Entities:
- Relationships:
- API:
- Validation:
- Auth:
- Permissions/RLS:
- Migrations:
- Backups:
- Exit strategy:
- Tests:
```

## Stop conditions

Stop before destructive migration, production data change, privileged-key exposure, or access-control weakening.
