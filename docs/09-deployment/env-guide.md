# Environment Variables Guide

This guide documents all environment variables required for local development and production deployment. Never commit `.env` files containing real credentials to version control.

---

## 1. Backend Environment Variables (`backend/.env`)

| Variable | Required | Default | Production Value / Notes |
|---|---|---|---|
| `APP_NAME` | No | `LMS API` | Display name in health/OpenAPI metadata |
| `APP_ENV` | Yes | `development` | Set to `production` in Render |
| `DEBUG` | Yes | `false` | Must be `false` in production |
| `ENABLE_API_DOCS` | No | `false` | Keep `false` in production to disable `/api/docs`, `/api/redoc`, and `/api/openapi.json` |
| `DATABASE_URL` | Yes | `mysql+pymysql://root:password@localhost:3306/lms_db` | Managed MySQL URI (`mysql+pymysql://user:pass@host:port/db`) |
| `JWT_SECRET_KEY` | Yes | *(dev placeholder)* | Generate a 48+ byte random secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_ALGORITHM` | No | `HS256` | Keep `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token TTL in minutes |
| `RESET_TOKEN_EXPIRE_MINUTES` | No | `15` | Password reset token TTL in minutes |
| `FRONTEND_ORIGIN` | Yes | `http://localhost:5173` | Exact Vercel frontend URL(s), comma-separated (e.g. `https://lms-app.vercel.app`) |
| `STORAGE_BACKEND` | Yes | `local` | Set to `cloudinary` in production (Render filesystem is ephemeral) |
| `UPLOAD_DIR` | No | `uploads` | Used only when `STORAGE_BACKEND=local` |
| `MAX_UPLOAD_SIZE_MB` | No | `10` | Max upload size per file in MB |
| `CLOUDINARY_CLOUD_NAME` | If `cloudinary` | `""` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | If `cloudinary` | `""` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | If `cloudinary` | `""` | Cloudinary API secret |
| `CLOUDINARY_FOLDER` | No | `lms_private` | Root folder for authenticated private assets |
| `PROGRESS_WEIGHT_LECTURES` | No | `0.40` | Course progress weight for lectures |
| `PROGRESS_WEIGHT_ASSIGNMENTS` | No | `0.30` | Course progress weight for assignments |
| `PROGRESS_WEIGHT_QUIZZES` | No | `0.30` | Course progress weight for quizzes |
| `COURSE_COMPLETE_MIN_PROGRESS` | No | `80.0` | Minimum weighted progress % for completion |
| `COURSE_COMPLETE_MIN_ATTENDANCE` | No | `75.0` | Minimum attendance % for completion |
| `COURSE_COMPLETE_REQUIRE_ALL_QUIZZES` | No | `true` | Require all published quizzes attempted |

---

## 2. Frontend Environment Variables (`frontend/.env`)

| Variable | Required | Default | Production Value / Notes |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000/api` | Full Render backend API URL ending in `/api` (e.g. `https://lms-api.onrender.com/api`). Never place secrets in `VITE_*` variables because Vite embeds them in the client bundle. |
