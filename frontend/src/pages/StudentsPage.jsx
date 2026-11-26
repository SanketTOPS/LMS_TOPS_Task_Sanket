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
import { studentService } from '../services/studentService'

const INITIAL_FORM = {
  full_name: '',
  email: '',
  phone: '',
  password: '',
  is_active: true,
}

export default function StudentsPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const isAdmin = user?.role_name === 'Admin'

  const [students, setStudents] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const [detailOpen, setDetailOpen] = useState(false)
  const [detailData, setDetailData] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const [deactivateTarget, setDeactivateTarget] = useState(null)
  const [deactivating, setDeactivating] = useState(false)

  const fetchStudents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await studentService.listStudents({
        q: search || undefined,
        is_active: statusFilter === '' ? undefined : statusFilter === 'true',
        page,
        page_size: 10,
      })
      setStudents(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load students.')
    } finally {
      setLoading(false)
    }
  }, [search, statusFilter, page])

  useEffect(() => {
    fetchStudents()
  }, [fetchStudents])

  const openDetail = async (student) => {
    setDetailOpen(true)
    setDetailLoading(true)
    try {
      const data = await studentService.getStudent(student.id)
      setDetailData(data)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to load student details', 'error')
      setDetailOpen(false)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setFormError('')
    setSaving(true)
    try {
      if (editing) {
        await studentService.updateStudent(editing.id, {
          full_name: formData.full_name,
          email: formData.email,
          phone: formData.phone || null,
          is_active: formData.is_active,
        })
        showToast('Student updated', 'success')
      } else {
        await studentService.createStudent(formData)
        showToast('Student created', 'success')
      }
      setFormOpen(false)
      fetchStudents()
    } catch (err) {
      setFormError(err?.response?.data?.detail || 'Failed to save student.')
    } finally {
      setSaving(false)
    }
  }

  const handleDeactivate = async () => {
    if (!deactivateTarget) return
    setDeactivating(true)
    try {
      await studentService.deactivateStudent(deactivateTarget.id)
      showToast('Student deactivated', 'success')
      setDeactivateTarget(null)
      fetchStudents()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to deactivate student', 'error')
    } finally {
      setDeactivating(false)
    }
  }

  const columns = [
    {
      key: 'full_name',
      header: 'Student',
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.full_name}</p>
          <p className="text-xs text-slate-500">{r.email}</p>
        </div>
      ),
    },
    { key: 'phone', header: 'Phone', render: (r) => r.phone || '—' },
    {
      key: 'is_active',
      header: 'Status',
      render: (r) => (
        <Badge tone={r.is_active ? 'success' : 'danger'}>
          {r.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) => (
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={() => openDetail(r)}>View</Button>
          {isAdmin && (
            <>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setEditing(r)
                  setFormData({
                    full_name: r.full_name,
                    email: r.email,
                    phone: r.phone || '',
                    password: '',
                    is_active: r.is_active,
                  })
                  setFormError('')
                  setFormOpen(true)
                }}
              >
                Edit
              </Button>
              {r.is_active && (
                <Button size="sm" variant="danger" onClick={() => setDeactivateTarget(r)}>
                  Deactivate
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
          <h1 className="text-2xl font-bold text-slate-900">Students</h1>
          <p className="mt-1 text-sm text-slate-500">View and manage enrolled students.</p>
        </div>
        {isAdmin && (
          <Button
            onClick={() => {
              setEditing(null)
              setFormData(INITIAL_FORM)
              setFormError('')
              setFormOpen(true)
            }}
          >
            + Add Student
          </Button>
        )}
      </div>

      <Card>
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        <Table columns={columns} data={students} loading={loading} error={error} />
        <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
      </Card>

      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? 'Edit Student' : 'Add Student'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {formError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <Input
            label="Full Name"
            required
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
          />
          <Input
            label="Email"
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <Input
            label="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          />
          {!editing && (
            <Input
              label="Password"
              type="password"
              required
              hint="Min 8 chars, uppercase, lowercase, and digit"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={detailOpen}
        onClose={() => setDetailOpen(false)}
        title={detailData ? `Student: ${detailData.full_name}` : 'Student Details'}
        maxWidth="max-w-2xl"
      >
        {detailLoading ? (
          <Spinner label="Loading student details..." />
        ) : detailData ? (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-3">
              <div>
                <p className="text-xs text-slate-500">Attendance</p>
                <p className="text-lg font-semibold text-slate-900">{detailData.attendance_percentage}%</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Course Progress</p>
                <p className="text-lg font-semibold text-slate-900">{detailData.progress_percentage}%</p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-slate-800 mb-2">Enrollments</h4>
              {detailData.enrollments.length === 0 ? (
                <p className="text-slate-500">No enrollments yet.</p>
              ) : (
                <div className="divide-y divide-slate-100 rounded-lg border border-slate-200">
                  {detailData.enrollments.map((e) => (
                    <div key={e.enrollment_id} className="flex items-center justify-between px-3 py-2">
                      <div>
                        <p className="font-medium text-slate-900">{e.course_title}</p>
                        <p className="text-xs text-slate-500">{e.course_code} {e.batch_name ? `• ${e.batch_name}` : ''}</p>
                      </div>
                      <Badge tone="primary">{e.status}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deactivateTarget)}
        onClose={() => setDeactivateTarget(null)}
        onConfirm={handleDeactivate}
        loading={deactivating}
        title="Deactivate Student"
        message={`Deactivate ${deactivateTarget?.full_name}?`}
        confirmLabel="Deactivate"
      />
    </div>
  )
}
