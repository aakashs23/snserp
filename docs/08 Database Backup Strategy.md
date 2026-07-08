# Database Backup Strategy – Sri Naga Sai ERP

## Overview

Sri Naga Sai ERP uses **Supabase** (managed PostgreSQL) as its primary database. This document outlines the backup, restore, and recovery verification procedures.

---

## 1. Supabase Managed Backups

Supabase provides automatic daily backups on **Pro** and **Team** plans.

### Point-in-Time Recovery (PITR)

- Available on Pro plans and above.
- Allows restoring the database to any second within the retention window.
- Retention: **7 days** (Pro) / **28 days** (Team/Enterprise).

### How to Restore via Supabase Dashboard

1. Navigate to **Project Settings → Database → Backups**.
2. Select the desired restore point (date/time).
3. Click **Restore** — Supabase will create a new project with the restored data.
4. Update `.env` with the new database URL and Supabase credentials.

---

## 2. Logical Backups (pg_dump)

For additional safety, schedule daily logical backups using `pg_dump`.

### Manual Backup

```bash
# Export using the Supabase connection string
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" \
    --format=custom \
    --no-owner \
    --no-acl \
    -f backup_$(date +%Y%m%d_%H%M%S).dump
```

### Automated Daily Backup (cron)

```bash
# Add to crontab: crontab -e
0 2 * * * /usr/bin/pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" \
    --format=custom --no-owner --no-acl \
    -f /backups/snserp_$(date +\%Y\%m\%d).dump 2>&1 | logger -t snserp-backup
```

### Restore from pg_dump

```bash
pg_restore --clean --no-owner --no-acl \
    -d "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres" \
    backup_20260708.dump
```

---

## 3. Storage Backups

Uploaded documents are stored in **Supabase Storage** (S3-compatible).

- Supabase Storage objects are persisted and not affected by database restores.
- For additional redundancy, sync the storage bucket to a secondary location:

```bash
# Using Supabase CLI or S3-compatible tools
supabase storage ls documents --project-ref [REF]
```

---

## 4. Recovery Verification

After any restore operation, verify:

| Check | Command / Action |
|---|---|
| Database connectivity | `curl http://localhost:8000/health/readiness` |
| User login | Attempt login via the frontend |
| Document listing | Navigate to Documents page |
| AI chat | Ask a question about an uploaded document |
| Invoice generation | Create a test invoice |

---

## 5. Recommended Schedule

| Backup Type | Frequency | Retention |
|---|---|---|
| Supabase auto-backup | Daily (automatic) | 7–28 days |
| pg_dump logical backup | Daily at 02:00 | 30 days |
| Storage sync | Weekly | 90 days |

---

## 6. Disaster Recovery Checklist

1. ☐ Identify the incident and required restore point.
2. ☐ If using PITR: restore via Supabase dashboard.
3. ☐ If using pg_dump: restore using `pg_restore`.
4. ☐ Update `.env` with new connection strings (if project changed).
5. ☐ Run `/health/readiness` to verify all subsystems.
6. ☐ Verify a sample of documents and AI queries.
7. ☐ Notify users of any data loss window.
