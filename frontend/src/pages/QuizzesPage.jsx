import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  Input,
  Modal,
  Pagination,
  Spinner,
  Table,
  useToast,
} from '../components'
import { useAuth } from '../context/AuthContext'
import { batchService } from '../services/batchService'
import { courseService } from '../services/courseService'
import { quizService } from '../services/quizService'

const INITIAL_FORM = {
  course_id: '',
  batch_id: '',
  title: '',
  description: '',
  time_limit_minutes: 30,
  passing_marks: 5,
  allow_retake: false,
  max_attempts: 1,
  available_from: '',
  available_until: '',
  is_published: false,
}

export default function QuizzesPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const isStaff = user?.role_name === 'Admin' || user?.role_name === 'Instructor'

  const [quizzes, setQuizzes] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [courses, setCourses] = useState([])
  const [batches, setBatches] = useState([])

  const [formOpen, setFormOpen] = useState(false)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [saving, setSaving] = useState(false)

  const [resultsQuiz, setResultsQuiz] = useState(null)
  const [results, setResults] = useState([])
  const [resultsLoading, setResultsLoading] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const fetchQuizzes = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await quizService.listQuizzes({ page, page_size: 10 })
      setQuizzes(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load quizzes.')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    fetchQuizzes()
  }, [fetchQuizzes])

  useEffect(() => {
    if (isStaff) {
      courseService.listCourses({ page_size: 100 }).then((r) => setCourses(r.items)).catch(() => {})
      batchService.listBatches({ page_size: 100 }).then((r) => setBatches(r.items)).catch(() => {})
    }
  }, [isStaff])

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const created = await quizService.createQuiz({
        course_id: Number(formData.course_id),
        batch_id: formData.batch_id ? Number(formData.batch_id) : null,
        title: formData.title,
        description: formData.description || null,
        time_limit_minutes: Number(formData.time_limit_minutes),
        passing_marks: Number(formData.passing_marks),
        allow_retake: formData.allow_retake,
        max_attempts: Number(formData.max_attempts),
        available_from: formData.available_from ? new Date(formData.available_from).toISOString() : null,
        available_until: formData.available_until ? new Date(formData.available_until).toISOString() : null,
        is_published: formData.is_published,
      })
      showToast('Quiz created', 'success')
      setFormOpen(false)
      navigate(`/quizzes/${created.id}/builder`)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to create quiz', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleStartQuiz = async (quizId) => {
    try {
      const attempt = await quizService.startQuiz(quizId)
      navigate(`/quiz-attempts/${attempt.attempt_id}`)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Cannot start quiz', 'error')
    }
  }

  const openResults = async (quiz) => {
    setResultsQuiz(quiz)
    setResultsLoading(true)
    try {
      const data = await quizService.listResults(quiz.id)
      setResults(data)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to load results', 'error')
      setResultsQuiz(null)
    } finally {
      setResultsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await quizService.deleteQuiz(deleteTarget.id)
      showToast('Quiz deleted', 'success')
      setDeleteTarget(null)
      fetchQuizzes()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Cannot delete quiz', 'error')
    } finally {
      setDeleting(false)
    }
  }

  const columns = [
    {
      key: 'title',
      header: 'Quiz',
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.title}</p>
          <p className="text-xs text-slate-500">
            {r.course_title} {r.batch_name ? `• ${r.batch_name}` : ''} • {r.question_count} Qs
          </p>
        </div>
      ),
    },
    {
      key: 'duration',
      header: 'Duration / Marks',
      render: (r) => `${r.time_limit_minutes}m • Pass ${r.passing_marks}/${r.total_marks}`,
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <Badge tone={r.is_published ? 'success' : 'warning'}>
          {r.is_published ? 'Published' : 'Draft'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) =>
        isStaff ? (
          <div className="flex flex-wrap gap-2">
            <Link to={`/quizzes/${r.id}/builder`}>
              <Button size="sm" variant="secondary">Questions</Button>
            </Link>
            <Button size="sm" variant="ghost" onClick={() => openResults(r)}>
              Results
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={async () => {
                await quizService.updateQuiz(r.id, { is_published: !r.is_published })
                fetchQuizzes()
              }}
            >
              {r.is_published ? 'Unpublish' : 'Publish'}
            </Button>
            <Button size="sm" variant="danger" onClick={() => setDeleteTarget(r)}>
              Delete
            </Button>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {r.latest_attempt_id && r.latest_attempt_submitted && (
              <Link to={`/quiz-attempts/${r.latest_attempt_id}/result`}>
                <Button size="sm" variant="secondary">View Result</Button>
              </Link>
            )}
            {(!r.latest_attempt_id || !r.latest_attempt_submitted || (r.allow_retake && r.my_attempts_count < r.max_attempts)) && (
              <Button size="sm" onClick={() => handleStartQuiz(r.id)}>
                {r.latest_attempt_id && !r.latest_attempt_submitted ? 'Resume Quiz' : 'Start Quiz'}
              </Button>
            )}
          </div>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Quizzes</h1>
          <p className="mt-1 text-sm text-slate-500">
            {isStaff ? 'Build MCQ quizzes and inspect student results.' : 'Take timed quizzes and review answers.'}
          </p>
        </div>
        {isStaff && (
          <Button onClick={() => { setFormData(INITIAL_FORM); setFormOpen(true) }}>
            + Create Quiz
          </Button>
        )}
      </div>

      <Card>
        <Table columns={columns} data={quizzes} loading={loading} error={error} />
        <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
      </Card>

      <Modal isOpen={formOpen} onClose={() => setFormOpen(false)} title="Create Quiz">
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Course</label>
              <select
                required
                value={formData.course_id}
                onChange={(e) => setFormData({ ...formData, course_id: e.target.value })}
                className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value="">Select course</option>
                {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Batch (optional)</label>
              <select
                value={formData.batch_id}
                onChange={(e) => setFormData({ ...formData, batch_id: e.target.value })}
                className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value="">All batches</option>
                {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
          </div>
          <Input
            label="Quiz Title"
            required
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Duration (minutes)"
              type="number"
              min="1"
              required
              value={formData.time_limit_minutes}
              onChange={(e) => setFormData({ ...formData, time_limit_minutes: e.target.value })}
            />
            <Input
              label="Passing Marks"
              type="number"
              step="0.5"
              min="0"
              required
              value={formData.passing_marks}
              onChange={(e) => setFormData({ ...formData, passing_marks: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Available From"
              type="datetime-local"
              value={formData.available_from}
              onChange={(e) => setFormData({ ...formData, available_from: e.target.value })}
            />
            <Input
              label="Available Until"
              type="datetime-local"
              value={formData.available_until}
              onChange={(e) => setFormData({ ...formData, available_until: e.target.value })}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={formData.allow_retake}
              onChange={(e) => setFormData({ ...formData, allow_retake: e.target.checked })}
            />
            Allow retakes
          </label>
          {formData.allow_retake && (
            <Input
              label="Max Attempts"
              type="number"
              min="1"
              value={formData.max_attempts}
              onChange={(e) => setFormData({ ...formData, max_attempts: e.target.value })}
            />
          )}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Create & Add Questions</Button>
          </div>
        </form>
      </Modal>

      {/* Staff Results Modal */}
      <Modal
        isOpen={Boolean(resultsQuiz)}
        onClose={() => setResultsQuiz(null)}
        title={`Results: ${resultsQuiz?.title || ''}`}
        maxWidth="max-w-2xl"
      >
        {resultsLoading ? (
          <Spinner label="Loading results..." />
        ) : results.length === 0 ? (
          <p className="text-sm text-slate-500">No attempts yet.</p>
        ) : (
          <div className="divide-y divide-slate-100 text-sm">
            {results.map((r) => (
              <div key={r.attempt_id} className="flex items-center justify-between py-2.5">
                <div>
                  <p className="font-medium text-slate-900">
                    {r.student_name} (Attempt #{r.attempt_number})
                  </p>
                  <p className="text-xs text-slate-500">{r.student_email}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-slate-900">Score: {r.score}</span>
                  <Badge tone={r.is_passed ? 'success' : 'danger'}>
                    {r.is_passed ? 'Passed' : 'Failed'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleting}
        title="Delete Quiz"
        message={`Delete "${deleteTarget?.title}"?`}
        confirmLabel="Delete"
      />
    </div>
  )
}
