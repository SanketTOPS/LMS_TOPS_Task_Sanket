import { useCallback, useEffect, useState } from 'react'
import {
  Badge,
  Button,
  Card,
  Input,
  Modal,
  Pagination,
  Table,
  useToast,
} from '../components'
import { useAuth } from '../context/AuthContext'
import { batchService } from '../services/batchService'
import { courseService } from '../services/courseService'
import { instructorService } from '../services/instructorService'

const INITIAL_FORM = {
  full_name: '',
  email: '',
  phone: '',
  password: '',
  expertise: '',
  qualification: '',
  experience_years: 0,
  bio: '',
}

export default function InstructorsPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const isAdmin = user?.role_name === 'Admin'

  const [instructors, setInstructors] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const [assignTarget, setAssignTarget] = useState(null)
  const [courses, setCourses] = useState([])
  const [batches, setBatches] = useState([])
  const [assignCourseId, setAssignCourseId] = useState('')
  const [assignBatchId, setAssignBatchId] = useState('')
  const [assigning, setAssigning] = useState(false)

  const fetchInstructors = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (isAdmin) {
        const res = await instructorService.listInstructors({
          q: search || undefined,
          page,
          page_size: 10,
        })
        setInstructors(res.items)
        setTotal(res.total)
        setTotalPages(res.total_pages)
      } else {
        const me = await instructorService.getMyProfile()
        setInstructors([me])
        setTotal(1)
        setTotalPages(1)
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load instructors.')
    } finally {
      setLoading(false)
    }
  }, [isAdmin, search, page])

  useEffect(() => {
    fetchInstructors()
  }, [fetchInstructors])

  useEffect(() => {
    if (isAdmin) {
      courseService.listCourses({ page_size: 100 }).then((r) => setCourses(r.items)).catch(() => {})
      batchService.listBatches({ page_size: 100 }).then((r) => setBatches(r.items)).catch(() => {})
    }
  }, [isAdmin])

  const handleSave = async (e) => {
    e.preventDefault()
    setFormError('')
    setSaving(true)
    try {
      if (editing) {
        await instructorService.updateInstructor(editing.id, {
          full_name: formData.full_name,
          phone: formData.phone || null,
          expertise: formData.expertise || null,
          qualification: formData.qualification || null,
          experience_years: Number(formData.experience_years),
          bio: formData.bio || null,
        })
        showToast('Instructor updated', 'success')
      } else {
        await instructorService.createInstructor({
          ...formData,
          experience_years: Number(formData.experience_years),
        })
        showToast('Instructor created', 'success')
      }
      setFormOpen(false)
      fetchInstructors()
    } catch (err) {
      setFormError(err?.response?.data?.detail || 'Failed to save instructor.')
    } finally {
      setSaving(false)
    }
  }

  const handleAssign = async (e) => {
    e.preventDefault()
    if (!assignTarget) return
    setAssigning(true)
    try {
      await instructorService.assignInstructor(assignTarget.id, {
        course_id: assignCourseId ? Number(assignCourseId) : null,
        batch_id: assignBatchId ? Number(assignBatchId) : null,
      })
      showToast('Instructor assigned successfully', 'success')
      setAssignTarget(null)
      setAssignCourseId('')
      setAssignBatchId('')
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to assign instructor', 'error')
    } finally {
      setAssigning(false)
    }
  }

  const columns = [
    {
      key: 'full_name',
      header: 'Instructor',
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.full_name}</p>
          <p className="text-xs text-slate-500">{r.email}</p>
        </div>
      ),
    },
    { key: 'expertise', header: 'Expertise', render: (r) => r.expertise || '—' },
    { key: 'qualification', header: 'Qualification', render: (r) => r.qualification || '—' },
    { key: 'experience_years', header: 'Experience', render: (r) => `${r.experience_years} yrs` },
    {
      key: 'is_active',
      header: 'Status',
      render: (r) => <Badge tone={r.is_active ? 'success' : 'danger'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) => (
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              setEditing(r)
              setFormData({
                full_name: r.full_name,
                email: r.email,
                phone: r.phone || '',
                password: '',
                expertise: r.expertise || '',
                qualification: r.qualification || '',
                experience_years: r.experience_years,
                bio: r.bio || '',
              })
              setFormError('')
              setFormOpen(true)
            }}
          >
            Edit Profile
          </Button>
          {isAdmin && (
            <Button size="sm" variant="ghost" onClick={() => setAssignTarget(r)}>
              Assign
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
          <h1 className="text-2xl font-bold text-slate-900">Instructors</h1>
          <p className="mt-1 text-sm text-slate-500">Manage instructor profiles and assignments.</p>
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
            + Add Instructor
          </Button>
        )}
      </div>

      <Card>
        {isAdmin && (
          <div className="mb-4 max-w-sm">
            <Input
              placeholder="Search by name, email, or expertise..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
        )}
        <Table columns={columns} data={instructors} loading={loading} error={error} />
        {isAdmin && <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />}
      </Card>

      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? 'Edit Instructor Profile' : 'Add Instructor'}
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
          {!editing && (
            <>
              <Input
                label="Email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
              <Input
                label="Password"
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </>
          )}
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Phone"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
            <Input
              label="Experience (years)"
              type="number"
              min="0"
              value={formData.experience_years}
              onChange={(e) => setFormData({ ...formData, experience_years: e.target.value })}
            />
          </div>
          <Input
            label="Expertise"
            value={formData.expertise}
            onChange={(e) => setFormData({ ...formData, expertise: e.target.value })}
          />
          <Input
            label="Qualification"
            value={formData.qualification}
            onChange={(e) => setFormData({ ...formData, qualification: e.target.value })}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Bio</label>
            <textarea
              rows={3}
              value={formData.bio}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={Boolean(assignTarget)}
        onClose={() => setAssignTarget(null)}
        title={`Assign ${assignTarget?.full_name || ''}`}
        maxWidth="max-w-md"
      >
        <form onSubmit={handleAssign} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Assign to Course</label>
            <select
              value={assignCourseId}
              onChange={(e) => setAssignCourseId(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">None</option>
              {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Assign to Batch</label>
            <select
              value={assignBatchId}
              onChange={(e) => setAssignBatchId(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">None</option>
              {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setAssignTarget(null)}>Cancel</Button>
            <Button type="submit" loading={assigning}>Assign</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
