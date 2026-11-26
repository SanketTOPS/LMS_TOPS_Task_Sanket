import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  Input,
  Modal,
  Pagination,
  Spinner,
  Table,
  useToast,
} from '../components'
import { useAuth } from '../context/AuthContext'
import { courseService } from '../services/courseService'
import { instructorService } from '../services/instructorService'

const STATUS_TONE = {
  published: 'success',
  draft: 'warning',
  archived: 'neutral',
}

function getCourseThumbnail(course) {
  if (course.thumbnail_url) return course.thumbnail_url
  const text = `${course.title || ''} ${course.category || ''} ${course.code || ''}`.toLowerCase()
  if (text.includes('web') || text.includes('full') || text.includes('react') || text.includes('fswd')) {
    return '/images/course-fullstack.jpg'
  }
  if (text.includes('data') || text.includes('python') || text.includes('ml') || text.includes('ai')) {
    return '/images/course-data-ml.jpg'
  }
  return '/images/course-default.jpg'
}

const INITIAL_FORM = {
  title: '',
  code: '',
  category: '',
  description: '',
  duration_weeks: 8,
  fee_amount: '0.00',
  thumbnail_url: '',
  instructor_id: '',
  status: 'draft',
}

export default function CoursesPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const isAdmin = user?.role_name === 'Admin'

  const [courses, setCourses] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('cards')

  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const [instructors, setInstructors] = useState([])
  const [formOpen, setFormOpen] = useState(false)
  const [editingCourse, setEditingCourse] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const [archiveTarget, setArchiveTarget] = useState(null)
  const [archiving, setArchiving] = useState(false)

  const fetchCourses = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await courseService.listCourses({
        q: search || undefined,
        category: categoryFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 9,
      })
      setCourses(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load courses.')
    } finally {
      setLoading(false)
    }
  }, [search, categoryFilter, statusFilter, page])

  useEffect(() => {
    fetchCourses()
  }, [fetchCourses])

  useEffect(() => {
    if (isAdmin) {
      instructorService.listInstructors({ page_size: 100 }).then((r) => setInstructors(r.items)).catch(() => {})
    }
  }, [isAdmin])

  const openCreate = () => {
    setEditingCourse(null)
    setFormData(INITIAL_FORM)
    setFormError('')
    setFormOpen(true)
  }

  const openEdit = (course) => {
    setEditingCourse(course)
    setFormData({
      title: course.title,
      code: course.code,
      category: course.category || '',
      description: course.description || '',
      duration_weeks: course.duration_weeks,
      fee_amount: String(course.fee_amount),
      thumbnail_url: course.thumbnail_url || '',
      instructor_id: course.instructor_id ? String(course.instructor_id) : '',
      status: course.status,
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
        title: formData.title,
        code: formData.code,
        category: formData.category || null,
        description: formData.description || null,
        duration_weeks: Number(formData.duration_weeks),
        fee_amount: Number(formData.fee_amount),
        thumbnail_url: formData.thumbnail_url || null,
        instructor_id: formData.instructor_id ? Number(formData.instructor_id) : null,
      }
      if (editingCourse) {
        await courseService.updateCourse(editingCourse.id, payload)
        showToast('Course updated', 'success')
      } else {
        await courseService.createCourse({ ...payload, status: formData.status })
        showToast('Course created', 'success')
      }
      setFormOpen(false)
      fetchCourses()
    } catch (err) {
      setFormError(err?.response?.data?.detail || 'Failed to save course.')
    } finally {
      setSaving(false)
    }
  }

  const handlePublishToggle = async (course) => {
    try {
      const shouldPublish = course.status !== 'published'
      await courseService.publishCourse(course.id, shouldPublish)
      showToast(shouldPublish ? 'Course published' : 'Course unpublished', 'success')
      fetchCourses()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Action failed', 'error')
    }
  }

  const handleArchive = async () => {
    if (!archiveTarget) return
    setArchiving(true)
    try {
      await courseService.archiveCourse(archiveTarget.id)
      showToast('Course archived', 'success')
      setArchiveTarget(null)
      fetchCourses()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to archive course', 'error')
    } finally {
      setArchiving(false)
    }
  }

  const columns = [
    {
      key: 'title',
      header: 'Course',
      render: (row) => (
        <div>
          <Link to={`/courses/${row.id}`} className="font-medium text-indigo-600 hover:underline">
            {row.title}
          </Link>
          <p className="text-xs text-slate-500">{row.code} {row.category ? `• ${row.category}` : ''}</p>
        </div>
      ),
    },
    { key: 'instructor_name', header: 'Instructor', render: (r) => r.instructor_name || 'Unassigned' },
    { key: 'duration_weeks', header: 'Duration', render: (r) => `${r.duration_weeks} weeks` },
    { key: 'fee_amount', header: 'Fee', render: (r) => `₹${r.fee_amount}` },
    {
      key: 'status',
      header: 'Status',
      render: (r) => <Badge tone={STATUS_TONE[r.status] || 'neutral'}>{r.status}</Badge>,
    },
    ...(isAdmin
      ? [
          {
            key: 'actions',
            header: 'Actions',
            render: (r) => (
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={() => openEdit(r)}>Edit</Button>
                {r.status !== 'archived' && (
                  <Button size="sm" variant="ghost" onClick={() => handlePublishToggle(r)}>
                    {r.status === 'published' ? 'Unpublish' : 'Publish'}
                  </Button>
                )}
                {r.status !== 'archived' && (
                  <Button size="sm" variant="danger" onClick={() => setArchiveTarget(r)}>
                    Archive
                  </Button>
                )}
              </div>
            ),
          },
        ]
      : []),
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Courses</h1>
          <p className="mt-1 text-sm text-slate-500">Browse and manage institute courses.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'cards' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setViewMode('cards')}
          >
            Cards
          </Button>
          <Button
            variant={viewMode === 'table' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setViewMode('table')}
          >
            Table
          </Button>
          {isAdmin && <Button onClick={openCreate}>+ Create Course</Button>}
        </div>
      </div>

      <Card>
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Input
            placeholder="Search by title or code..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
          <Input
            placeholder="Filter by category..."
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1) }}
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        {viewMode === 'table' ? (
          <Table columns={columns} data={courses} loading={loading} error={error} />
        ) : loading ? (
          <Spinner label="Loading courses..." />
        ) : error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
        ) : courses.length === 0 ? (
          <EmptyState title="No courses found" description="Try adjusting your search or filters." />
        ) : (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {courses.map((course) => (
              <div
                key={course.id}
                className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm card-hover"
              >
                <div>
                  <div className="relative h-44 overflow-hidden bg-slate-100">
                    <img
                      src={getCourseThumbnail(course)}
                      alt={course.title}
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                    <div className="absolute top-3 left-3">
                      <span className="rounded-full bg-brand-900/90 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-white backdrop-blur-sm">
                        {course.code}
                      </span>
                    </div>
                    <div className="absolute top-3 right-3">
                      <Badge tone={STATUS_TONE[course.status] || 'neutral'}>{course.status}</Badge>
                    </div>
                  </div>

                  <div className="p-5 pb-0">
                    <Link
                      to={`/courses/${course.id}`}
                      className="block text-base font-bold text-slate-900 group-hover:text-brand-700"
                    >
                      {course.title}
                    </Link>
                    <p className="mt-1.5 line-clamp-2 text-xs text-slate-500 leading-relaxed">
                      {course.description || 'No description provided.'}
                    </p>
                  </div>
                </div>

                <div className="mt-4 border-t border-slate-100 p-5 pt-3 text-xs text-slate-600 space-y-1.5">
                  <div className="flex justify-between">
                    <span>Instructor:</span>
                    <strong className="text-slate-800">{course.instructor_name || 'Unassigned'}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Duration / Fee:</span>
                    <strong className="text-accent-600">{course.duration_weeks}w • ₹{course.fee_amount}</strong>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-2">
                    <Link to={`/courses/${course.id}`}>
                      <Button size="sm" variant="primary">View Details</Button>
                    </Link>
                    {isAdmin && (
                      <>
                        <Button size="sm" variant="ghost" onClick={() => openEdit(course)}>Edit</Button>
                        {course.status !== 'archived' && (
                          <Button size="sm" variant="ghost" onClick={() => handlePublishToggle(course)}>
                            {course.status === 'published' ? 'Unpublish' : 'Publish'}
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
      </Card>

      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingCourse ? 'Edit Course' : 'Create Course'}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {formError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <Input
            label="Course Title"
            required
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Course Code"
              required
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            />
            <Input
              label="Category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Duration (weeks)"
              type="number"
              min="1"
              required
              value={formData.duration_weeks}
              onChange={(e) => setFormData({ ...formData, duration_weeks: e.target.value })}
            />
            <Input
              label="Fee (₹)"
              type="number"
              step="0.01"
              min="0"
              required
              value={formData.fee_amount}
              onChange={(e) => setFormData({ ...formData, fee_amount: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Assigned Instructor</label>
            <select
              value={formData.instructor_id}
              onChange={(e) => setFormData({ ...formData, instructor_id: e.target.value })}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">Unassigned</option>
              {instructors.map((inst) => (
                <option key={inst.id} value={inst.id}>{inst.full_name}</option>
              ))}
            </select>
          </div>
          <Input
            label="Thumbnail URL"
            value={formData.thumbnail_url}
            onChange={(e) => setFormData({ ...formData, thumbnail_url: e.target.value })}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Description</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(archiveTarget)}
        onClose={() => setArchiveTarget(null)}
        onConfirm={handleArchive}
        loading={archiving}
        title="Archive Course"
        message={`Archive "${archiveTarget?.title}"? Students will no longer see it in the active catalog.`}
        confirmLabel="Archive"
      />
    </div>
  )
}
