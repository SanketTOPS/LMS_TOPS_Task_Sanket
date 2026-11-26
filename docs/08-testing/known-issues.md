# Known Issues & Environment Limitations

| ID | Area | Severity | Description | Impact / Workaround |
|---|---|---|---|---|
| KI-001 | Database / Migrations | Medium | Local MySQL server is not running in this environment, so `alembic upgrade head` (including migration `e738c8b6a123_add_payment_receipt_and_cert_verification.py`) has not been executed against a live MySQL instance. | Backend Pytest suite runs cleanly against SQLite in-memory (`Base.metadata.create_all()`). Run `alembic upgrade head` once MySQL is started before running the backend server. |
| KI-002 | Frontend Build / E2E | Medium | Node.js / npm is not installed on `PATH` in this workspace environment, so automated frontend builds (`npm run build`) and browser E2E tests could not be executed. | Frontend pages and services were verified by static code inspection. Run `npm install && npm run build` in `frontend/` on a Node-enabled machine. |
| KI-003 | Configuration | Low | `config.py` contains a development default `JWT_SECRET_KEY` and `DEBUG=True`. | Always override `JWT_SECRET_KEY` and set `DEBUG=False` in `.env` for staging/production deployments. |
| KI-004 | Dependency Warning | Low | `fastapi.testclient` emits a `StarletteDeprecationWarning` regarding `httpx` vs `httpx2`. | Informational only; does not affect runtime or test assertions. |
