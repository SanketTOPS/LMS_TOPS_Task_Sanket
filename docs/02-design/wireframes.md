# UI Wireframes & Design System

- **Title:** LMS UI Wireframes & Design System
- **Version:** 1.0
- **Author:** LMS Engineering Team
- **Last Updated:** 2026-11-25

---

## 1. Screen Inventory (from `frontend/src/App.jsx`)

| Route | Page Component | Allowed Roles | Purpose |
|---|---|---|---|
| `/login` | `LoginPage.jsx` | Public | Email/password login form |
| `/forgot-password` | `ForgotPasswordPage.jsx` | Public | Request password reset token |
| `/reset-password` | `ResetPasswordPage.jsx` | Public | Submit reset token + new password |
| `/dashboard` | `DashboardPage.jsx` | All Auth | Role-tailored KPI summary & quick links |
| `/courses` | `CoursesPage.jsx` | All Auth | Browse/create/filter courses |
| `/courses/:id` | `CourseDetailPage.jsx` | All Auth | Course overview, modules, syllabus |
| `/courses/:courseId/learn` | `StudentLecturePage.jsx` | All Auth (Student view) | Video player, study materials, mark complete |
| `/courses/:courseId/manage-lectures` | `InstructorLecturesPage.jsx` | Admin, Instructor | Module/lecture CRUD, reorder, video & material upload |
| `/batches` | `BatchesPage.jsx` | All Auth | Batch list, roster, student enrollment |
| `/assignments` | `AssignmentsPage.jsx` | All Auth | Assignment manager, file submission, evaluation modal |
| `/quizzes` | `QuizzesPage.jsx` | All Auth | Quiz list & availability status |
| `/quizzes/:quizId/builder` | `QuizBuilderPage.jsx` | Admin, Instructor | MCQ question builder & results table |
| `/quiz-attempts/:attemptId` | `QuizAttemptPage.jsx` | Student | Question navigator, options, live server-synced timer |
| `/quiz-attempts/:attemptId/result` | `QuizResultPage.jsx` | Student | Score summary, pass/fail badge, answer review |
| `/attendance` | `AttendancePage.jsx` | All Auth | Instructor bulk roster toggles / Student monthly summary |
| `/progress` | `ProgressPage.jsx` | All Auth | Weighted course progress bars & completion checklist |
| `/students` | `StudentsPage.jsx` | Admin, Instructor | Student directory & detail view |
| `/instructors` | `InstructorsPage.jsx` | Admin, Instructor | Instructor directory & batch assignment |
| `/admin/users` | `AdminUsersPage.jsx` | Admin | User management, role filter, deactivate, password reset |
| `/profile` | `ProfilePage.jsx` | All Auth | View/edit profile and change password |

---

## 2. Navigation Flow

```text
Unauthenticated -> /login <-> /forgot-password -> /reset-password
Authenticated   -> ProtectedRoute -> DashboardLayout (Sidebar + Header + <Outlet />)
                   ├── Admin: All nav items including Users (/admin/users)
                   ├── Instructor: Dashboard, Courses, Batches, Assignments, Quizzes, Attendance, Progress, Students, Instructors, Profile
                   └── Student: Dashboard, Courses, Batches, Assignments, Quizzes, Attendance, Progress, Profile
```

---

## 3. Colour Palette & Typography (Tailwind CSS)

Derived from `frontend/index.html` and `frontend/src/layouts/DashboardLayout.jsx`:
- **Page Background:** `bg-slate-50` (`#F8FAFC`)
- **Surface / Cards / Sidebar:** `bg-white` (`#FFFFFF`) with `border-slate-200` (`#E2E8F0`)
- **Primary Brand Accent:** Indigo (`text-indigo-600`, active nav `bg-indigo-50 text-indigo-700`)
- **Primary Text:** `text-slate-900` (`#0F172A`), Secondary Text: `text-slate-600` / `text-slate-500`
- **Status Tones (`Badge.jsx`):** `primary` (indigo), `success` (emerald), `warning` (amber), `danger` (rose), `neutral` (slate)
- **Typography:** System sans-serif stack with Tailwind `antialiased`, `text-lg font-bold tracking-tight` for brand headers, `text-sm font-medium` for navigation and labels, `text-xs` for metadata.

---

## 4. Shared UI Component Library (`frontend/src/components/`)

- `Badge.jsx` — Status & role pills
- `Button.jsx` — Primary, secondary, danger, size variants
- `Card.jsx` — Standard padded white container with border
- `ConfirmDialog.jsx` — Destructive/submit confirmation modal
- `EmptyState.jsx` — Zero-data placeholder state
- `Input.jsx` — Labeled form input with validation state
- `Modal.jsx` — Accessible dialog overlay
- `Pagination.jsx` — Page navigation controls
- `Spinner.jsx` — Loading indicator
- `Table.jsx` — Responsive data table
- `Toast.jsx` — Global notification provider (`ToastProvider`)
