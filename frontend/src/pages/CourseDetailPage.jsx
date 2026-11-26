import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  Input,
  Modal,
  Spinner,
  useToast,
} from '../components'
import { useAuth } from '../context/AuthContext'
import { courseService } from '../services/courseService'

export default function CourseDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()

  const canManageModules = user?.role_name === 'Admin' || user?.role_name === 'Instructor'

  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [modModalOpen, setModModalOpen] = useState(false)
  const [modTitle, setModTitle] = useState('')
  const [modDesc, setModDesc] = useState('')
  const [modOrder, setModOrder] = useState(1)
  const [savingMod, setSavingMod] = useState(false)

  const [deleteModTarget, setDeleteModTarget] = useState(null)
  const [deletingMod, setDeletingMod] = useState(false)

  const fetchDetail = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await courseService.getCourse(id)
      setCourse(data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load course details.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchDetail()
  }, [fetchDetail])

  const handleAddModule = async (e) => {
    e.preventDefault()
    setSavingMod(true)
    try {
      await courseService.createModule(id, {
        title: modTitle,
        description: modDesc || null,
        sort_order: Number(modOrder),
      })
      showToast('Module added', 'success')
      setModModalOpen(false)
      setModTitle('')
      setModDesc('')
      fetchDetail()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to add module', 'error')
    } finally {
      setSavingMod(false)
    }
  }

  const handleDeleteModule = async () => {
    if (!deleteModTarget) return
    setDeletingMod(true)
    try {
      await courseService.deleteModule(id, deleteModTarget.id)
      showToast('Module deleted', 'success')
      setDeleteModTarget(null)
      fetchDetail()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to delete module', 'error')
    } finally {
      setDeletingMod(false)
    }
  }

  if (loading) return <Spinner size="lg" label="Loading course..." />
  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    )
  }
  if (!course) return null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/courses" className="text-xs font-medium text-indigo-600 hover:underline">
            ← Back to Courses
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{course.title}</h1>
          <p className="text-sm text-slate-500">
            {course.code} {course.category ? `• ${course.category}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={course.status === 'published' ? 'success' : 'warning'}>{course.status}</Badge>
          {course.is_enrolled && <Badge tone="primary">Enrolled</Badge>}
          {canManageModules ? (
            <Link to={`/courses/${course.id}/manage-lectures`}>
              <Button size="sm">Manage Lectures</Button>
            </Link>
          ) : (
            <Link to={`/courses/${course.id}/learn`}>
              <Button size="sm">Open Lectures</Button>
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card title="Course Overview" className="lg:col-span-2">
          <p className="text-sm text-slate-700 whitespace-pre-line">
            {course.description || 'No description available.'}
          </p>
        </Card>

        <Card title="Details">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Instructor</dt>
              <dd className="font-medium text-slate-900">{course.instructor_name || 'Unassigned'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Duration</dt>
              <dd className="font-medium text-slate-900">{course.duration_weeks} weeks</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Course Fee</dt>
              <dd className="font-medium text-slate-900">₹{course.fee_amount}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Total Enrollments</dt>
              <dd className="font-medium text-slate-900">{course.enrollment_count}</dd>
            </div>
          </dl>
        </Card>
      </div>

      <Card
        title="Course Modules"
        actions={
          canManageModules && (
            <Button
              size="sm"
              onClick={() => {
                setModOrder((course.modules?.length || 0) + 1)
                setModModalOpen(true)
              }}
            >
              + Add Module
            </Button>
          )
        }
      >
        {!course.modules || course.modules.length === 0 ? (
          <EmptyState title="No modules yet" description="Modules added to this course will appear here." />
        ) : (
          <div className="divide-y divide-slate-100">
            {course.modules.map((mod) => (
              <div key={mod.id} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {mod.sort_order}. {mod.title}
                  </p>
                  {mod.description && <p className="mt-0.5 text-xs text-slate-500">{mod.description}</p>}
                </div>
                {canManageModules && (
                  <Button size="sm" variant="danger" onClick={() => setDeleteModTarget(mod)}>
                    Delete
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      <Modal isOpen={modModalOpen} onClose={() => setModModalOpen(false)} title="Add Module">
        <form onSubmit={handleAddModule} className="space-y-4">
          <Input label="Title" required value={modTitle} onChange={(e) => setModTitle(e.target.value)} />
          <Input
            label="Sort Order"
            type="number"
            min="1"
            required
            value={modOrder}
            onChange={(e) => setModOrder(e.target.value)}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Description</label>
            <textarea
              rows={3}
              value={modDesc}
              onChange={(e) => setModDesc(e.target.value)}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setModModalOpen(false)}>Cancel</Button>
            <Button type="submit" loading={savingMod}>Add Module</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleteModTarget)}
        onClose={() => setDeleteModTarget(null)}
        onConfirm={handleDeleteModule}
        loading={deletingMod}
        title="Delete Module"
        message={`Delete module "${deleteModTarget?.title}"?`}
        confirmLabel="Delete"
      />
    </div>
  )
}
