# Module Note: Auth & Users

- **Title:** Auth & Users Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** JWT authentication, password reset/change, profile management, and Admin user lifecycle.
- **Roles:** Public (login/reset), Any Auth (`me`, `change-password`), Admin (`/api/users`).
- **Tables:** `roles`, `users`
- **API Endpoints:** `POST /api/auth/login`, `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`, `POST /api/auth/change-password`, `GET/PUT /api/auth/me`, `GET/POST /api/users`, `PUT /api/users/{user_id}`, `PATCH /api/users/{user_id}/deactivate`, `POST /api/users/{user_id}/reset-password`
- **Screens:** `LoginPage.jsx`, `ForgotPasswordPage.jsx`, `ResetPasswordPage.jsx`, `ProfilePage.jsx`, `AdminUsersPage.jsx`
- **Business Rules:** Passwords hashed with `bcrypt`; login rate-limited via `slowapi`; wrong email/password returns a single generic error; `UserResponse` omits `password_hash`; inactive users cannot log in.
- **Tests:** `backend/tests/test_auth_users.py` (8 tests passing), `backend/tests/test_security_validation.py`
- **Known Issues:** Password reset does not send external SMTP email in v1.
