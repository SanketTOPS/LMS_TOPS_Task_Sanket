# Production Deployment Guide

Target architecture:
- **Database:** Hosted MySQL 8.x (Aiven, Railway, or PlanetScale-compatible MySQL)
- **Backend:** Render Web Service (Python 3.11 + FastAPI + Uvicorn)
- **File Storage:** Cloudinary (`STORAGE_BACKEND=cloudinary`, authenticated private raw assets)
- **Frontend:** Vercel (React + Vite static SPA with `frontend/vercel.json` rewrites)

---

## Step 1: Provision Managed MySQL

1. Create a MySQL 8.x database instance on **Aiven**, **Railway**, or **PlanetScale** (with foreign keys enabled).
2. Create a database named `lms_db` (or use the provider's default database).
3. Copy the connection details and construct the SQLAlchemy URI:
   ```text
   mysql+pymysql://<USER>:<PASSWORD>@<HOST>:<PORT>/lms_db
   ```
   *(If your provider requires TLS/SSL, append `?ssl_ca=/etc/ssl/certs/ca-certificates.crt` or the provider's CA path.)*

---

## Step 2: Configure Private Cloud File Storage (Cloudinary)

1. Create a Cloudinary account and copy your **Cloud Name**, **API Key**, and **API Secret**.
2. Set `STORAGE_BACKEND=cloudinary` on Render so uploads are stored in Cloudinary with `type=authenticated` and `access_mode=authenticated`, and served through backend RBAC/IDOR checks.

---

## Step 3: Deploy Backend on Render

1. Create a new **Web Service** in Render connected to this repository.
2. Configure service settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3.11
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Pre-Deploy Command** (runs Alembic migrations automatically on every deploy):
     ```bash
     alembic upgrade head
     ```
   - **Start Command** (matches `backend/Procfile`):
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path:** `/api/health`
3. Add all production environment variables from [env-guide.md](./env-guide.md) (`APP_ENV=production`, `DEBUG=false`, `ENABLE_API_DOCS=false`, `DATABASE_URL`, `JWT_SECRET_KEY`, `FRONTEND_ORIGIN`, `STORAGE_BACKEND=cloudinary`, and `CLOUDINARY_*`).
4. Deploy and verify the health endpoint:
   ```bash
   curl https://<your-render-service>.onrender.com/api/health
   ```
   Expected response (`200 OK`):
   ```json
   {"status":"ok","database":"connected","app":"LMS API","env":"production"}
   ```

---

## Step 4: Seed Initial Roles & Admin User

Run the seed script once via Render Shell (or locally pointing `DATABASE_URL` to the production DB):

```bash
cd backend
python -m app.utils.seed
```

Change the seeded Admin password immediately after first login.

---

## Step 5: Deploy Frontend on Vercel

1. Import the repository in **Vercel**.
2. Configure project settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://<your-render-service>.onrender.com/api`
4. `frontend/vercel.json` is already configured with SPA fallback rewrites (`/(.*) -> /index.html`).
5. Deploy and copy your production Vercel URL (e.g. `https://lms-app.vercel.app`).
6. Update `FRONTEND_ORIGIN` in Render to match your exact Vercel URL and trigger a Render restart if needed.

---

## Step 6: Rollback Procedure

1. **Application Rollback (Render / Vercel):**
   - In Render Dashboard -> **Deploys** -> select the last known good deploy -> **Rollback to this deploy**.
   - In Vercel Dashboard -> **Deployments** -> select the previous production deployment -> **Promote to Production**.
2. **Database Migration Rollback (if a schema migration caused issues):**
   ```bash
   cd backend
   alembic downgrade -1
   ```
   *(If data loss could occur on downgrade, restore from the pre-deploy `mysqldump` backup per [backup-restore.md](./backup-restore.md).)*

---

## Step 7: Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `/api/health` returns `503` (`database: disconnected`) | Wrong `DATABASE_URL`, firewall/IP allowlist, or missing SSL param | Verify `DATABASE_URL`, allow Render outbound IPs (or `0.0.0.0/0` with TLS), check DB credentials |
| CORS error in browser console | `FRONTEND_ORIGIN` does not match Vercel URL (trailing slash or wrong protocol) | Set `FRONTEND_ORIGIN=https://your-app.vercel.app` (no trailing slash) |
| 404 on page refresh in Vercel | Missing SPA rewrite | Ensure `frontend/vercel.json` is committed in `frontend/` |
| File upload returns `500 STORAGE_MISCONFIGURED` | `STORAGE_BACKEND=cloudinary` without `CLOUDINARY_*` vars | Populate `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` in Render |
