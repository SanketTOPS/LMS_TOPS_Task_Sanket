# Database Backup & Restore Policy

## 1. Backup Schedule & Storage

- **Automated Managed Snapshots:** Enable daily automated snapshots on your managed MySQL provider (Aiven / Railway) with at least **7–14 days** retention.
- **Logical Backups (`mysqldump`):** Run a daily cron backup (and a mandatory manual backup before any Alembic schema migration) and store encrypted `.sql.gz` archives in an off-site private bucket (e.g., S3 / GCS / Backblaze B2) with 30-day retention.
- **File Assets:** Private uploaded assets are stored in Cloudinary (`lms_private` folder); enable Cloudinary backup/versioning or periodic sync.

---

## 2. Backup Command (`mysqldump`)

```bash
mysqldump \
  --host="<DB_HOST>" \
  --port="<DB_PORT>" \
  --user="<DB_USER>" \
  --password="<DB_PASSWORD>" \
  --single-transaction \
  --routines \
  --triggers \
  --set-gtid-purged=OFF \
  lms_db | gzip > "lms_db_$(date +%Y%m%d_%H%M%S).sql.gz"
```

---

## 3. Restore Command

1. **Put the backend in maintenance mode** (or scale down Render workers) to prevent concurrent writes during restore.
2. **Restore into the target database:**
   ```bash
   gunzip -c lms_db_20261125_020000.sql.gz | mysql \
     --host="<DB_HOST>" \
     --port="<DB_PORT>" \
     --user="<DB_USER>" \
     --password="<DB_PASSWORD>" \
     lms_db
   ```
3. **Verify schema revision and health:**
   ```bash
   cd backend
   alembic current
   curl https://<your-render-service>.onrender.com/api/health
   ```

---

## 4. Restore Drill Policy

Perform a quarterly restore drill into a staging MySQL instance and verify:
- Row counts for `users`, `courses`, `enrollments`, `payments`, and `certificates`.
- `/api/health` returns `200 OK` (`database: connected`).
- Existing Alembic revision matches `alembic heads`.
