import { Navigate, Route, Routes } from 'react-router-dom'
import { ToastProvider } from './components'
import { AuthProvider } from './context/AuthContext'
import DashboardLayout from './layouts/DashboardLayout'
import AdminUsersPage from './pages/AdminUsersPage'
import AssignmentsPage from './pages/AssignmentsPage'
import AttendancePage from './pages/AttendancePage'
import BatchesPage from './pages/BatchesPage'
import CourseDetailPage from './pages/CourseDetailPage'
import CoursesPage from './pages/CoursesPage'
import DashboardPage from './pages/DashboardPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import InstructorLecturesPage from './pages/InstructorLecturesPage'
import InstructorsPage from './pages/InstructorsPage'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import ProgressPage from './pages/ProgressPage'
import QuizAttemptPage from './pages/QuizAttemptPage'
import QuizBuilderPage from './pages/QuizBuilderPage'
import QuizResultPage from './pages/QuizResultPage'
import QuizzesPage from './pages/QuizzesPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import StudentLecturePage from './pages/StudentLecturePage'
import StudentsPage from './pages/StudentsPage'
import ProtectedRoute from './routes/ProtectedRoute'

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/courses" element={<CoursesPage />} />
              <Route path="/courses/:id" element={<CourseDetailPage />} />
              <Route path="/courses/:courseId/learn" element={<StudentLecturePage />} />
              <Route path="/batches" element={<BatchesPage />} />
              <Route path="/assignments" element={<AssignmentsPage />} />
              <Route path="/quizzes" element={<QuizzesPage />} />
              <Route path="/attendance" element={<AttendancePage />} />
              <Route path="/progress" element={<ProgressPage />} />
              <Route path="/quiz-attempts/:attemptId" element={<QuizAttemptPage />} />
              <Route path="/quiz-attempts/:attemptId/result" element={<QuizResultPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route element={<ProtectedRoute allowedRoles={['Admin', 'Instructor']} />}>
                <Route path="/quizzes/:quizId/builder" element={<QuizBuilderPage />} />
                <Route path="/courses/:courseId/manage-lectures" element={<InstructorLecturesPage />} />
                <Route path="/students" element={<StudentsPage />} />
                <Route path="/instructors" element={<InstructorsPage />} />
              </Route>
              <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
                <Route path="/admin/users" element={<AdminUsersPage />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </ToastProvider>
  )
}
