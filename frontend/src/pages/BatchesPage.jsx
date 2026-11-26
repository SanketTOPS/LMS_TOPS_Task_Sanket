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
import { batchService } from '../services/batchService'
import { courseService } from '../services/courseService'
import { instructorService } from '../services/instructorService'
import { studentService } from '../services/studentService'

const STATUS_TONE = {
  upcoming: 'primary',
  active: 'success',
  closed: 'warning',
  archived: 'neutral',
}

const INITIAL_FORM = {
  name: '',
  code: '',
  course_id: '',
  instructor_id: '',
  start_date: '',
  end_date: '',
  schedule_info: '',
  max_students: 30,
  status: 'upcoming',
}

export default function BatchesPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const isAdmin = user?.role_name === 'Admin'
  const canViewRoster = isAdmin || user?.role_name === 'Instructor'

  const [batches, setBatches] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const [courses, setCourses] = useState([])
  const [instructors, setInstructors] = useState([])
  const [allStudents, setAllStudents] = useState([])

  const [formOpen, setFormOpen] = useState(false)
  const [editingBatch, setEditingBatch] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const [rosterOpen, setRosterOpen] = useState(false)
  const [rosterData, setRosterData] = useState(null)
  const [rosterLoading, setRosterLoading] = useState(false)
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [enrolling, setEnrolling] = useState(false)

  const [statusAction, setStatusAction] = useState(null) // { batch, type: 'close' | 'archive' }
  const [updatingStatus, setUpdatingStatus] = useState(false)

  const fetchBatches = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await batchService.listBatches({
        q: search || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 10,
      })
      setBatches(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load batches.')
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter, page])

  useEffect(() => {
    fetchBatches()
  }, [fetchBatches])

  useEffect(() => {
    if (isAdmin) {
      courseService.listCourses({ page_size: 100 }).then((r) => setCourses(r.items)).catch(() => {})
      instructorService.listInstructors({ page_size: 100 }).then((r) => setInstructors(r.items)).catch(() => {})
      studentService.listStudents({ page_size: 100, is_active: true }).then((r) => setAllStudents(r.items)).catch(() => {})
    }
  }, [isAdmin])

  const openCreate = () => {
    setEditingBatch(null)
    setFormData(INITIAL_FORM)
    setFormError('')
    setFormOpen(true)
  }

  const openEdit = (b) => {
    setEditingBatch(b)
    setFormData({
      name: b.name,
      code: b.code,
      course_id: String(b.course_id),
      instructor_id: String(b.instructor_id),
      start_date: b.start_date,
      end_date: b.end_date || '',
      schedule_info: b.schedule_info || '',
      max_students: b.max_students,
      status: b.status,
    })
    setFormError('')
    setFormOpen(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setFormError('')
    setSaving(true)
    try {
      const payload = {
        name: formData.name,
        code: formData.code,
        course_id: Number(formData.course_id),
        instructor_id: Number(formData.instructor_id),
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        schedule_info: formData.schedule_info || null,
        max_students: Number(formData.max_students),
      }
      if (editingBatch) {
        await batchService.updateBatch(editingBatch.id, payload)
        showToast('Batch updated', 'success')
      } else {
        await batchService.createBatch({ ...payload, status: formData.status })
        showToast('Batch created', 'success')
      }
      setFormOpen(false)
      fetchBatches()
    } catch (err) {
      setFormError(err?.response?.data?.detail || 'Failed to save batch.')
    } finally {
      setSaving(false)
    }
  }

  const openRoster = async (batch) => {
    setRosterOpen(true)
    setRosterLoading(true)
    setSelectedStudentId('')
    try {
      const data = await batchService.getRoster(batch.id)
      setRosterData(data)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to load roster', 'error')
      setRosterOpen(false)
    } finally {
      setRosterLoading(false)
    }
  }

  const handleAddStudent = async (e) => {
    e.preventDefault()
    if (!selectedStudentId || !rosterData) return
    setEnrolling(true)
    try {
      await batchService.addStudent(rosterData.batch_id, Number(selectedStudentId))
      showToast('Student enrolled in batch', 'success')
      const updated = await batchService.getRoster(rosterData.batch_id)
      setRosterData(updated)
      setSelectedStudentId('')
      fetchBatches()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to enroll student', 'error')
    } finally {
      setEnrolling(false)
    }
  }

  const handleRemoveStudent = async (studentId) => {
    if (!rosterData) return
    try {
      await batchService.removeStudent(rosterData.batch_id, studentId)
      showToast('Student removed from batch', 'success')
      const updated = await batchService.getRoster(rosterData.batch_id)
      setRosterData(updated)
      fetchBatches()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to remove student', 'error')
    }
  }

  const handleStatusConfirm = async () => {
    if (!statusAction) return
    setUpdatingStatus(true)
    try {
      if (statusAction.type === 'close') {
        await batchService.closeBatch(statusAction.batch.id)
        showToast('Batch closed', 'success')
      } else {
        await batchService.archiveBatch(statusAction.batch.id)
        showToast('Batch archived', 'success')
      }
      setStatusAction(null)
      fetchBatches()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Action failed', 'error')
    } finally {
      setUpdatingStatus(false)
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Batch',
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.name}</p>
          <p className="text-xs text-slate-500">{r.code} • {r.course_title}</p>
        </div>
      ),
    },
    { key: 'instructor_name', header: 'Instructor', render: (r) => r.instructor_name || '—' },
    {
      key: 'dates',
      header: 'Dates',
      render: (r) => (
        <span className="text-xs">
          {r.start_date} → {r.end_date || 'Open'}
        </span>
      ),
    },
    {
      key: 'capacity',
      header: 'Capacity',
      render: (r) => `${r.enrolled_count} / ${r.max_students}`,
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => <Badge tone={STATUS_TONE[r.status] || 'neutral'}>{r.status}</Badge>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) => (
        <div className="flex flex-wrap gap-2">
          {canViewRoster && (
            <Button size="sm" variant="secondary" onClick={() => openRoster(r)}>
              Roster
            </Button>
          )}
          {isAdmin && (
            <>
              <Button size="sm" variant="ghost" onClick={() => openEdit(r)}>Edit</Button>
              {r.status !== 'closed' && r.status !== 'archived' && (
                <Button size="sm" variant="ghost" onClick={() => setStatusAction({ batch: r, type: 'close' })}>
                  Close
                </Button>
              )}
              {r.status !== 'archived' && (
                <Button size="sm" variant="danger" onClick={() => setStatusAction({ batch: r, type: 'archive' })}>
                  Archive
                </Button>
              )}
            </>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Batches</h1>
          <p className="mt-1 text-sm text-slate-500">Manage training cohorts and student rosters.</p>
        </div>
        {isAdmin && <Button onClick={openCreate}>+ Create Batch</Button>}
      </div>

      <Card>
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input
            placeholder="Search batch name or code..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="upcoming">Upcoming</option>
            <option value="active">Active</option>
            <option value="closed">Closed</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        <Table columns={columns} data={batches} loading={loading} error={error} />
        <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
      </Card>

      {/* Create / Edit Batch Modal */}
      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingBatch ? 'Edit Batch' : 'Create Batch'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {formError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Batch Name"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <Input
              label="Batch Code"
              required
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            />
          </div>
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
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>{c.title}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Instructor</label>
              <select
                required
                value={formData.instructor_id}
                onChange={(e) => setFormData({ ...formData, instructor_id: e.target.value })}
                className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value="">Select instructor</option>
                {instructors.map((i) => (
                  <option key={i.id} value={i.id}>{i.full_name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start Date"
              type="date"
              required
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            />
            <Input
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Schedule / Timing"
              placeholder="Mon-Fri 09:00-11:00"
              value={formData.schedule_info}
              onChange={(e) => setFormData({ ...formData, schedule_info: e.target.value })}
            />
            <Input
              label="Max Capacity"
              type="number"
              min="1"
              required
              value={formData.max_students}
              onChange={(e) => setFormData({ ...formData, max_students: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>

      {/* Roster Modal */}
      <Modal
        isOpen={rosterOpen}
        onClose={() => setRosterOpen(false)}
        title={rosterData ? `Roster: ${rosterData.batch_name} (${rosterData.enrolled_count}/${rosterData.max_students})` : 'Batch Roster'}
        maxWidth="max-w-2xl"
      >
        {rosterLoading ? (
          <Spinner label="Loading roster..." />
        ) : rosterData ? (
          <div className="space-y-4">
            {isAdmin && (
              <form onSubmit={handleAddStudent} className="flex flex-wrap gap-2">
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                >
                  <option value="">Select student to enroll...</option>
                  {allStudents.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.full_name} ({s.email})
                    </option>
                  ))}
                </select>
                <Button type="submit" loading={enrolling} disabled={!selectedStudentId}>
                  Add Student
                </Button>
              </form>
            )}

            {rosterData.students.length === 0 ? (
              <p className="text-sm text-slate-500">No students enrolled in this batch yet.</p>
            ) : (
              <div className="divide-y divide-slate-100 rounded-lg border border-slate-200">
                {rosterData.students.map((st) => (
                  <div key={st.student_id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                    <div>
                      <p className="font-medium text-slate-900">{st.full_name}</p>
                      <p className="text-xs text-slate-500">{st.email}</p>
                    </div>
                    {isAdmin && (
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleRemoveStudent(st.student_id)}
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(statusAction)}
        onClose={() => setStatusAction(null)}
        onConfirm={handleStatusConfirm}
        loading={updatingStatus}
        title={statusAction?.type === 'close' ? 'Close Batch' : 'Archive Batch'}
        message={`Are you sure you want to ${statusAction?.type} "${statusAction?.batch?.name}"?`}
        confirmLabel={statusAction?.type === 'close' ? 'Close Batch' : 'Archive Batch'}
      />
    </div>
  )
}
