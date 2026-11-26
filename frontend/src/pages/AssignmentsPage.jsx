import { useCallback, useEffect, useState } from 'react'
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
import { assignmentService } from '../services/assignmentService'
import { batchService } from '../services/batchService'
import { courseService } from '../services/courseService'

const STATUS_TONE = {
  Pending: 'neutral',
  Submitted: 'primary',
  'Under Review': 'warning',
  Evaluated: 'success',
  'Late Submission': 'danger',
}

function getDeadlineCountdown(dueDateStr) {
  const diffMs = new Date(dueDateStr).getTime() - Date.now()
  if (diffMs <= 0) return 'Deadline passed'
  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)
  if (days > 0) return `${days}d ${hours % 24}h remaining`
  return `${hours}h remaining`
}

const INITIAL_FORM = {
  course_id: '',
  batch_id: '',
  title: '',
  description: '',
  max_marks: 100,
  due_date: '',
  allow_late: false,
}

export default function AssignmentsPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const isStaff = user?.role_name === 'Admin' || user?.role_name === 'Instructor'

  const [assignments, setAssignments] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [courses, setCourses] = useState([])
  const [batches, setBatches] = useState([])

  // Staff: create/edit assignment modal
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [attFile, setAttFile] = useState(null)
  const [saving, setSaving] = useState(false)

  // Staff: delete confirm
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  // Staff: submissions modal & evaluation modal
  const [subsModalAssignment, setSubsModalAssignment] = useState(null)
  const [submissions, setSubmissions] = useState([])
  const [subsLoading, setSubsLoading] = useState(false)

  const [evalTarget, setEvalTarget] = useState(null)
  const [evalMarks, setEvalMarks] = useState('')
  const [evalComments, setEvalComments] = useState('')
  const [evaluating, setEvaluating] = useState(false)

  // Student: submit modal
  const [submitTarget, setSubmitTarget] = useState(null)
  const [subText, setSubText] = useState('')
  const [subFile, setSubFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchAssignments = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await assignmentService.listAssignments({ page, page_size: 10 })
      setAssignments(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load assignments.')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    fetchAssignments()
  }, [fetchAssignments])

  useEffect(() => {
    if (isStaff) {
      courseService.listCourses({ page_size: 100 }).then((r) => setCourses(r.items)).catch(() => {})
      batchService.listBatches({ page_size: 100 }).then((r) => setBatches(r.items)).catch(() => {})
    }
  }, [isStaff])

  const handleSaveAssignment = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        course_id: Number(formData.course_id),
        batch_id: formData.batch_id ? Number(formData.batch_id) : null,
        title: formData.title,
        description: formData.description || null,
        max_marks: Number(formData.max_marks),
        due_date: new Date(formData.due_date).toISOString(),
        allow_late: formData.allow_late,
      }
      const saved = editing
        ? await assignmentService.updateAssignment(editing.id, payload)
        : await assignmentService.createAssignment(payload)
      if (attFile) {
        await assignmentService.uploadAttachment(saved.id, attFile)
      }
      showToast(editing ? 'Assignment updated' : 'Assignment created', 'success')
      setFormOpen(false)
      fetchAssignments()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to save assignment', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteAssignment = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await assignmentService.deleteAssignment(deleteTarget.id)
      showToast('Assignment deleted', 'success')
      setDeleteTarget(null)
      fetchAssignments()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Cannot delete assignment', 'error')
    } finally {
      setDeleting(false)
    }
  }

  const openSubmissions = async (assignment) => {
    setSubsModalAssignment(assignment)
    setSubsLoading(true)
    try {
      const list = await assignmentService.listSubmissions(assignment.id)
      setSubmissions(list)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to load submissions', 'error')
      setSubsModalAssignment(null)
    } finally {
      setSubsLoading(false)
    }
  }

  const handleEvaluate = async (e) => {
    e.preventDefault()
    if (!evalTarget) return
    setEvaluating(true)
    try {
      await assignmentService.evaluateSubmission(evalTarget.id, {
        marks: Number(evalMarks),
        comments: evalComments,
      })
      showToast('Submission evaluated', 'success')
      setEvalTarget(null)
      if (subsModalAssignment) {
        const list = await assignmentService.listSubmissions(subsModalAssignment.id)
        setSubmissions(list)
      }
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Evaluation failed', 'error')
    } finally {
      setEvaluating(false)
    }
  }

  const handleStudentSubmit = async (e) => {
    e.preventDefault()
    if (!submitTarget) return
    setSubmitting(true)
    try {
      await assignmentService.submitAssignment({
        assignment_id: submitTarget.id,
        submission_text: subText || undefined,
        file: subFile || undefined,
      })
      showToast('Assignment submitted', 'success')
      setSubmitTarget(null)
      setSubText('')
      setSubFile(null)
      fetchAssignments()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Submission failed', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    {
      key: 'title',
      header: 'Assignment',
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.title}</p>
          <p className="text-xs text-slate-500">
            {r.course_title} {r.batch_name ? `• ${r.batch_name}` : ''}
          </p>
          {r.attachment_name && (
            <button
              type="button"
              onClick={() => assignmentService.downloadAttachment(r.id, r.attachment_name)}
              className="mt-1 text-xs font-medium text-indigo-600 hover:underline"
            >
              📎 {r.attachment_name}
            </button>
          )}
        </div>
      ),
    },
    {
      key: 'due_date',
      header: 'Deadline',
      render: (r) => (
        <div className="text-xs">
          <p className="text-slate-800">{new Date(r.due_date).toLocaleString()}</p>
          <p className="text-slate-500">{getDeadlineCountdown(r.due_date)}</p>
        </div>
      ),
    },
    {
      key: 'max_marks',
      header: 'Marks',
      render: (r) =>
        isStaff
          ? `${r.max_marks}`
          : r.my_submission?.marks_obtained != null
            ? `${r.my_submission.marks_obtained} / ${r.max_marks}`
            : `— / ${r.max_marks}`,
    },
    ...(!isStaff
      ? [
          {
            key: 'status',
            header: 'Status',
            render: (r) => {
              const st = r.my_submission?.status || 'Pending'
              return <Badge tone={STATUS_TONE[st] || 'neutral'}>{st}</Badge>
            },
          },
        ]
      : []),
    {
      key: 'actions',
      header: 'Actions',
      render: (r) =>
        isStaff ? (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={() => openSubmissions(r)}>
              Submissions
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setEditing(r)
                setFormData({
                  course_id: String(r.course_id),
                  batch_id: r.batch_id ? String(r.batch_id) : '',
                  title: r.title,
                  description: r.description || '',
                  max_marks: r.max_marks,
                  due_date: r.due_date.slice(0, 16),
                  allow_late: r.allow_late,
                })
                setAttFile(null)
                setFormOpen(true)
              }}
            >
              Edit
            </Button>
            <Button size="sm" variant="danger" onClick={() => setDeleteTarget(r)}>
              Delete
            </Button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            {r.my_submission?.status !== 'Evaluated' && (
              <Button
                size="sm"
                onClick={() => {
                  setSubmitTarget(r)
                  setSubText(r.my_submission?.submission_text || '')
                  setSubFile(null)
                }}
              >
                {r.my_submission ? 'Resubmit' : 'Submit'}
              </Button>
            )}
            {r.my_submission?.feedback?.length > 0 && (
              <span className="text-xs text-slate-600">
                Feedback: {r.my_submission.feedback[0].comments}
              </span>
            )}
          </div>
        ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Assignments</h1>
          <p className="mt-1 text-sm text-slate-500">
            {isStaff
              ? 'Create assignments and evaluate student submissions.'
              : 'View deadlines, upload solutions, and check feedback.'}
          </p>
        </div>
        {isStaff && (
          <Button
            onClick={() => {
              setEditing(null)
              setFormData(INITIAL_FORM)
              setAttFile(null)
              setFormOpen(true)
            }}
          >
            + Create Assignment
          </Button>
        )}
      </div>

      <Card>
        <Table columns={columns} data={assignments} loading={loading} error={error} />
        <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
      </Card>

      {/* Staff Create / Edit Assignment Modal */}
      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? 'Edit Assignment' : 'Create Assignment'}
      >
        <form onSubmit={handleSaveAssignment} className="space-y-4">
          {!editing && (
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
          )}
          <Input
            label="Title"
            required
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Instructions</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Max Marks"
              type="number"
              min="1"
              required
              value={formData.max_marks}
              onChange={(e) => setFormData({ ...formData, max_marks: e.target.value })}
            />
            <Input
              label="Due Date & Time"
              type="datetime-local"
              required
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Reference Attachment (PDF, DOCX, PPTX, ZIP)
            </label>
            <input
              type="file"
              accept=".pdf,.ppt,.pptx,.docx,.zip"
              onChange={(e) => setAttFile(e.target.files?.[0] || null)}
              className="block w-full text-xs text-slate-600"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={formData.allow_late}
              onChange={(e) => setFormData({ ...formData, allow_late: e.target.checked })}
            />
            Allow late submissions
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>

      {/* Staff Submissions Modal */}
      <Modal
        isOpen={Boolean(subsModalAssignment)}
        onClose={() => setSubsModalAssignment(null)}
        title={`Submissions: ${subsModalAssignment?.title || ''}`}
        maxWidth="max-w-3xl"
      >
        {subsLoading ? (
          <Spinner label="Loading submissions..." />
        ) : submissions.length === 0 ? (
          <p className="text-sm text-slate-500">No submissions yet.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {submissions.map((sub) => (
              <div key={sub.id} className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
                <div>
                  <p className="font-medium text-slate-900">{sub.student_name} ({sub.student_email})</p>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge tone={STATUS_TONE[sub.status] || 'neutral'}>{sub.status}</Badge>
                    <span className="text-xs text-slate-500">
                      Versions: {sub.versions?.length || 1}
                    </span>
                    {sub.marks_obtained != null && (
                      <span className="text-xs font-semibold text-emerald-700">
                        Marks: {sub.marks_obtained} / {subsModalAssignment?.max_marks}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {sub.file_name && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => assignmentService.downloadSubmission(sub.id, sub.file_name)}
                    >
                      Download
                    </Button>
                  )}
                  <Button
                    size="sm"
                    onClick={() => {
                      setEvalTarget(sub)
                      setEvalMarks(sub.marks_obtained != null ? String(sub.marks_obtained) : '')
                      setEvalComments(sub.feedback?.[0]?.comments || '')
                    }}
                  >
                    Evaluate
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* Staff Evaluate Modal */}
      <Modal
        isOpen={Boolean(evalTarget)}
        onClose={() => setEvalTarget(null)}
        title={`Evaluate: ${evalTarget?.student_name || ''}`}
        maxWidth="max-w-md"
      >
        <form onSubmit={handleEvaluate} className="space-y-4">
          <Input
            label={`Marks (0 – ${subsModalAssignment?.max_marks})`}
            type="number"
            step="0.01"
            min="0"
            max={subsModalAssignment?.max_marks}
            required
            value={evalMarks}
            onChange={(e) => setEvalMarks(e.target.value)}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Feedback</label>
            <textarea
              rows={3}
              required
              value={evalComments}
              onChange={(e) => setEvalComments(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEvalTarget(null)}>Cancel</Button>
            <Button type="submit" loading={evaluating}>Save Grade</Button>
          </div>
        </form>
      </Modal>

      {/* Student Submit Modal */}
      <Modal
        isOpen={Boolean(submitTarget)}
        onClose={() => setSubmitTarget(null)}
        title={`Submit: ${submitTarget?.title || ''}`}
      >
        <form onSubmit={handleStudentSubmit} className="space-y-4">
          {submitTarget?.description && (
            <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">{submitTarget.description}</p>
          )}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Notes / Answer</label>
            <textarea
              rows={3}
              value={subText}
              onChange={(e) => setSubText(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Upload File (PDF, PPT/PPTX, DOCX, ZIP)
            </label>
            <input
              type="file"
              accept=".pdf,.ppt,.pptx,.docx,.zip"
              onChange={(e) => setSubFile(e.target.files?.[0] || null)}
              className="block w-full text-xs text-slate-600"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setSubmitTarget(null)}>Cancel</Button>
            <Button type="submit" loading={submitting}>Submit</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteAssignment}
        loading={deleting}
        title="Delete Assignment"
        message={`Delete "${deleteTarget?.title}"?`}
        confirmLabel="Delete"
      />
    </div>
  )
}
