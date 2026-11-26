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
import { courseService } from '../services/courseService'
import { lectureService } from '../services/lectureService'

const INITIAL_FORM = {
  module_id: '',
  title: '',
  description: '',
  video_url: '',
  duration_minutes: 30,
  sort_order: 1,
  is_published: true,
}

export default function InstructorLecturesPage() {
  const { courseId } = useParams()
  const { showToast } = useToast()

  const [course, setCourse] = useState(null)
  const [lectures, setLectures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [videoFile, setVideoFile] = useState(null)
  const [saving, setSaving] = useState(false)

  const [matModalLecture, setMatModalLecture] = useState(null)
  const [matTitle, setMatTitle] = useState('')
  const [matFile, setMatFile] = useState(null)
  const [uploadingMat, setUploadingMat] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [cData, lData] = await Promise.all([
        courseService.getCourse(courseId),
        lectureService.listCourseLectures(courseId),
      ])
      setCourse(cData)
      setLectures(lData)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load lectures.')
    } finally {
      setLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const openCreate = () => {
    setEditing(null)
    setFormData({
      ...INITIAL_FORM,
      module_id: course?.modules?.[0]?.id ? String(course.modules[0].id) : '',
      sort_order: lectures.length + 1,
    })
    setVideoFile(null)
    setFormOpen(true)
  }

  const openEdit = (lec) => {
    setEditing(lec)
    setFormData({
      module_id: String(lec.module_id),
      title: lec.title,
      description: lec.description || '',
      video_url: lec.video_url || '',
      duration_minutes: lec.duration_minutes,
      sort_order: lec.sort_order,
      is_published: lec.is_published,
    })
    setVideoFile(null)
    setFormOpen(true)
  }

  const handleSaveLecture = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        module_id: Number(formData.module_id),
        title: formData.title,
        description: formData.description || null,
        video_url: formData.video_url || null,
        duration_minutes: Number(formData.duration_minutes),
        sort_order: Number(formData.sort_order),
        is_published: formData.is_published,
      }
      let saved
      if (editing) {
        saved = await lectureService.updateLecture(editing.id, payload)
      } else {
        saved = await lectureService.createLecture(payload)
      }
      if (videoFile) {
        await lectureService.uploadLectureVideo(saved.id, videoFile)
      }
      showToast(editing ? 'Lecture updated' : 'Lecture created', 'success')
      setFormOpen(false)
      fetchData()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to save lecture', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleMove = async (moduleId, index, direction) => {
    const modLectures = lectures.filter((l) => l.module_id === moduleId)
    const targetIdx = index + direction
    if (targetIdx < 0 || targetIdx >= modLectures.length) return
    const reordered = [...modLectures]
    const [moved] = reordered.splice(index, 1)
    reordered.splice(targetIdx, 0, moved)
    try {
      await lectureService.reorderLectures(
        moduleId,
        reordered.map((l) => l.id)
      )
      showToast('Lectures reordered', 'success')
      fetchData()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Reorder failed', 'error')
    }
  }

  const handleUploadMaterial = async (e) => {
    e.preventDefault()
    if (!matModalLecture || !matFile) return
    setUploadingMat(true)
    try {
      await lectureService.uploadMaterial({
        course_id: Number(courseId),
        module_id: matModalLecture.module_id,
        lecture_id: matModalLecture.id,
        title: matTitle,
        file: matFile,
      })
      showToast('Study material uploaded', 'success')
      setMatModalLecture(null)
      setMatTitle('')
      setMatFile(null)
      fetchData()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Upload failed', 'error')
    } finally {
      setUploadingMat(false)
    }
  }

  const handleDeleteLecture = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await lectureService.deleteLecture(deleteTarget.id)
      showToast('Lecture deleted', 'success')
      setDeleteTarget(null)
      fetchData()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to delete lecture', 'error')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) return <Spinner size="lg" label="Loading lectures..." />
  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to={`/courses/${courseId}`} className="text-xs font-medium text-indigo-600 hover:underline">
            ← Back to {course?.title}
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">Lecture & Material Manager</h1>
        </div>
        <Button onClick={openCreate} disabled={!course?.modules?.length}>
          + Add Lecture
        </Button>
      </div>

      {!course?.modules?.length ? (
        <EmptyState
          title="No modules in this course"
          description="Create at least one module on the Course Detail page before adding lectures."
        />
      ) : (
        course.modules.map((mod) => {
          const modLectures = lectures.filter((l) => l.module_id === mod.id)
          return (
            <Card key={mod.id} title={`${mod.sort_order}. ${mod.title}`}>
              {modLectures.length === 0 ? (
                <p className="text-sm text-slate-500">No lectures in this module yet.</p>
              ) : (
                <div className="divide-y divide-slate-100">
                  {modLectures.map((lec, idx) => (
                    <div key={lec.id} className="py-3 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-900">
                              {lec.sort_order}. {lec.title}
                            </span>
                            <Badge tone={lec.is_published ? 'success' : 'warning'}>
                              {lec.is_published ? 'Published' : 'Draft'}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-500">
                            {lec.duration_minutes} mins {lec.video_url ? '• Video attached' : ''}
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5">
                          <Button size="sm" variant="ghost" disabled={idx === 0} onClick={() => handleMove(mod.id, idx, -1)}>
                            ↑
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={idx === modLectures.length - 1}
                            onClick={() => handleMove(mod.id, idx, 1)}
                          >
                            ↓
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              setMatModalLecture(lec)
                              setMatTitle('')
                              setMatFile(null)
                            }}
                          >
                            + Material
                          </Button>
                          <Button size="sm" variant="secondary" onClick={() => openEdit(lec)}>
                            Edit
                          </Button>
                          <Button size="sm" variant="danger" onClick={() => setDeleteTarget(lec)}>
                            Delete
                          </Button>
                        </div>
                      </div>

                      {lec.materials?.length > 0 && (
                        <div className="ml-4 flex flex-wrap gap-2">
                          {lec.materials.map((m) => (
                            <span
                              key={m.id}
                              className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700"
                            >
                              {m.title} ({m.file_name})
                              <button
                                type="button"
                                onClick={() => lectureService.deleteMaterial(m.id).then(fetchData)}
                                className="text-rose-600 hover:text-rose-800"
                                title="Delete material"
                              >
                                ✕
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )
        })
      )}

      {/* Lecture Modal */}
      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? 'Edit Lecture' : 'Add Lecture'}
      >
        <form onSubmit={handleSaveLecture} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Module</label>
            <select
              required
              value={formData.module_id}
              onChange={(e) => setFormData({ ...formData, module_id: e.target.value })}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              {course?.modules?.map((m) => (
                <option key={m.id} value={m.id}>{m.title}</option>
              ))}
            </select>
          </div>
          <Input
            label="Lecture Title"
            required
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
          <Input
            label="Video URL (YouTube or direct link)"
            value={formData.video_url}
            onChange={(e) => setFormData({ ...formData, video_url: e.target.value })}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Or Upload Video File (.mp4, .webm, .mov)
            </label>
            <input
              type="file"
              accept=".mp4,.webm,.mov"
              onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
              className="block w-full text-xs text-slate-600"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Duration (minutes)"
              type="number"
              min="0"
              value={formData.duration_minutes}
              onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
            />
            <Input
              label="Sort Order"
              type="number"
              min="1"
              value={formData.sort_order}
              onChange={(e) => setFormData({ ...formData, sort_order: e.target.value })}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={formData.is_published}
              onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
            />
            Published
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" loading={saving}>Save</Button>
          </div>
        </form>
      </Modal>

      {/* Upload Material Modal */}
      <Modal
        isOpen={Boolean(matModalLecture)}
        onClose={() => setMatModalLecture(null)}
        title={`Upload Material: ${matModalLecture?.title || ''}`}
        maxWidth="max-w-md"
      >
        <form onSubmit={handleUploadMaterial} className="space-y-4">
          <Input
            label="Material Title"
            required
            value={matTitle}
            onChange={(e) => setMatTitle(e.target.value)}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              File (PDF, PPT/PPTX, DOCX, ZIP)
            </label>
            <input
              type="file"
              required
              accept=".pdf,.ppt,.pptx,.docx,.zip"
              onChange={(e) => setMatFile(e.target.files?.[0] || null)}
              className="block w-full text-xs text-slate-600"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setMatModalLecture(null)}>Cancel</Button>
            <Button type="submit" loading={uploadingMat}>Upload</Button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteLecture}
        loading={deleting}
        title="Delete Lecture"
        message={`Delete lecture "${deleteTarget?.title}"?`}
        confirmLabel="Delete"
      />
    </div>
  )
}
