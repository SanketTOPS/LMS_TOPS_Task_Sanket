import { useEffect, useState } from 'react'
import { Badge, Card, EmptyState, Spinner, useToast } from '../components'
import { useAuth } from '../context/AuthContext'
import { attendanceService } from '../services/attendanceService'
import { studentService } from '../services/studentService'

function ProgressBar({ label, current, total, percentage, weight, color = 'bg-indigo-600' }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs font-medium text-slate-700">
        <span>
          {label} {weight && <span className="text-slate-400 font-normal">({weight} weight)</span>}
        </span>
        <span className="font-semibold text-slate-900">
          {current !== undefined && total !== undefined ? `${current} / ${total} ` : ''}
          ({percentage.toFixed(1)}%)
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full transition-all duration-300 ${color}`}
          style={{ width: `${Math.min(Math.max(percentage, 0), 100)}%` }}
        />
      </div>
    </div>
  )
}

export default function ProgressPage() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const isStudent = user?.role_name === 'Student'

  // Admin/Instructor student selection
  const [students, setStudents] = useState([])
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [progressData, setProgressData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isStudent) {
      loadOwnProgress()
    } else {
      studentService
        .listStudents({ page_size: 100 })
        .then((res) => {
          const list = res.items || []
          setStudents(list)
          if (list.length > 0) {
            setSelectedStudentId(list[0].id)
          }
        })
        .catch((err) => {
          addToast(err?.response?.data?.detail || 'Failed to load students', 'error')
        })
    }
  }, [isStudent])

  useEffect(() => {
    if (!isStudent && selectedStudentId) {
      loadStudentProgress(selectedStudentId)
    }
  }, [selectedStudentId, isStudent])

  const loadOwnProgress = async () => {
    setLoading(true)
    try {
      const data = await attendanceService.getMyProgress()
      setProgressData(data)
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Failed to load progress', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadStudentProgress = async (studentId) => {
    setLoading(true)
    try {
      const data = await attendanceService.getStudentProgress(studentId)
      setProgressData(data)
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Failed to load student progress', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {isStudent ? 'My Course Progress' : 'Student Academic Progress'}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Course completion requires ≥80% academic progress (40% lectures + 30% assignments + 30% quizzes), ≥75% attendance, and all quizzes attempted.
          </p>
        </div>

        {!isStudent && students.length > 0 && (
          <div className="w-full sm:w-72">
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Select Student
            </label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
            >
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.user?.full_name || s.name || `Student #${s.id}`} ({s.enrollment_no || s.user?.email})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      ) : !progressData || progressData.courses.length === 0 ? (
        <Card className="p-8">
          <EmptyState
            title="No course progress found"
            description={
              isStudent
                ? "You are not enrolled in any courses yet."
                : "No enrolled courses found for this student."
            }
          />
        </Card>
      ) : (
        <>
          {/* Top Level Summary Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4 border-l-4 border-l-indigo-500">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Overall Progress
              </span>
              <div className="mt-2 text-3xl font-extrabold text-indigo-600">
                {progressData.overall_progress_percentage.toFixed(1)}%
              </div>
              <p className="mt-1 text-xs text-slate-400">Weighted average across courses</p>
            </Card>

            <Card className="p-4 border-l-4 border-l-emerald-500">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Overall Attendance
              </span>
              <div className="mt-2 text-3xl font-extrabold text-emerald-600">
                {progressData.overall_attendance_percentage.toFixed(1)}%
              </div>
              <p className="mt-1 text-xs text-slate-400">Class presence across all batches</p>
            </Card>

            <Card className="p-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Enrolled Courses
              </span>
              <div className="mt-2 text-3xl font-extrabold text-slate-800">
                {progressData.courses.length}
              </div>
              <p className="mt-1 text-xs text-slate-400">Total active course enrollments</p>
            </Card>

            <Card className="p-4">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Completed Courses
              </span>
              <div className="mt-2 text-3xl font-extrabold text-purple-600">
                {progressData.courses.filter((c) => c.is_complete).length}
              </div>
              <p className="mt-1 text-xs text-slate-400">Satisfied all criteria</p>
            </Card>
          </div>

          {/* Detailed Course Cards */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {progressData.courses.map((course) => (
              <Card key={course.course_id} className="p-6 space-y-5">
                <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">{course.course_title}</h3>
                    <span className="text-xs font-medium text-slate-500">{course.course_code}</span>
                  </div>
                  <Badge variant={course.is_complete ? 'success' : 'info'}>
                    {course.is_complete ? 'Completed' : 'In Progress'}
                  </Badge>
                </div>

                {/* Overall Score for Course */}
                <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-semibold text-slate-800">
                      Weighted Course Progress
                    </span>
                    <span className="text-lg font-extrabold text-indigo-600">
                      {course.course_progress_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-indigo-600 transition-all duration-300"
                      style={{
                        width: `${Math.min(Math.max(course.course_progress_percentage, 0), 100)}%`,
                      }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    40% Lectures + 30% Assignments + 30% Quizzes
                  </p>
                </div>

                {/* Sub-Metric Bars */}
                <div className="space-y-3 pt-1">
                  <ProgressBar
                    label="Lectures Completed"
                    weight="40%"
                    current={course.lectures_completed}
                    total={course.lectures_total}
                    percentage={course.lecture_percentage}
                    color="bg-sky-500"
                  />

                  <ProgressBar
                    label="Assignments Submitted"
                    weight="30%"
                    current={course.assignments_submitted}
                    total={course.assignments_total}
                    percentage={course.assignment_percentage}
                    color="bg-amber-500"
                  />

                  <ProgressBar
                    label="Quizzes Attempted"
                    weight="30%"
                    current={course.quizzes_attempted}
                    total={course.quizzes_total}
                    percentage={course.quiz_percentage}
                    color="bg-purple-500"
                  />

                  <ProgressBar
                    label="Batch Attendance"
                    percentage={course.attendance_percentage}
                    color={course.attendance_percentage >= 75 ? 'bg-emerald-500' : 'bg-rose-500'}
                  />
                </div>

                {/* Completion Criteria Checklist */}
                <div className="border-t border-slate-100 pt-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">
                    Completion Checklist
                  </span>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center gap-2">
                      <span className={course.course_progress_percentage >= 80 ? 'text-emerald-600 font-bold' : 'text-slate-400'}>
                        {course.course_progress_percentage >= 80 ? '✓' : '○'}
                      </span>
                      <span className={course.course_progress_percentage >= 80 ? 'text-slate-800 font-medium' : 'text-slate-500'}>
                        Course Progress ≥ 80% (Current: {course.course_progress_percentage.toFixed(1)}%)
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={course.attendance_percentage >= 75 ? 'text-emerald-600 font-bold' : 'text-slate-400'}>
                        {course.attendance_percentage >= 75 ? '✓' : '○'}
                      </span>
                      <span className={course.attendance_percentage >= 75 ? 'text-slate-800 font-medium' : 'text-slate-500'}>
                        Attendance ≥ 75% (Current: {course.attendance_percentage.toFixed(1)}%)
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={course.all_quizzes_attempted ? 'text-emerald-600 font-bold' : 'text-slate-400'}>
                        {course.all_quizzes_attempted ? '✓' : '○'}
                      </span>
                      <span className={course.all_quizzes_attempted ? 'text-slate-800 font-medium' : 'text-slate-500'}>
                        All Quizzes Attempted ({course.quizzes_attempted}/{course.quizzes_total})
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
