# Module Note: Payments

- **Title:** Payments Module
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

- **Purpose:** Record manual fee installments, enforce overpayment protection, process refunds, and generate PDF fee receipts.
- **Roles:** Admin (record payment, refund, list all payments), Student (view own payments/balances, download own PDF receipts).
- **Tables:** `payments`, `courses`, `enrollments`, `users`
- **API Endpoints:** `POST /api/payments`, `POST /api/payments/{payment_id}/refund`, `GET /api/payments`, `GET /api/payments/me`, `GET /api/payments/{payment_id}/receipt`
- **Screens:** API-ready in v1 (dedicated frontend page planned for v2)
- **Business Rules:** Status auto-derived (`Pending`, `Partially Paid`, `Paid`, `Refunded`); overpayments rejected (`400`) inside a transaction; refund requires `reason` and restores pending balance; unique `RCP-YYYY-XXXXXXXX` receipt number; no card data stored.
- **Tests:** `backend/tests/test_payments_certificates.py` (4 payment tests passing)
- **Known Issues:** Requires Alembic migration `e738c8b6a123` on live MySQL (`receipt_number` column).
