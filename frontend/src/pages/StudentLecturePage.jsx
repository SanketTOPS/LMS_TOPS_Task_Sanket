import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, Button, Card, EmptyState, Spinner, useToast } from '../components'
import { lectureService } from '../services/lectureService'

function getYouTubeEmbedUrl(url) {
  if (!url) return null
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]{11})/)
  return match ? `https://www.youtube.com/embed/${match[1]}` : null
}

export default function StudentLecturePage() {
  const { courseId } = useParams()
  const { showToast } = useToast()

  const [lectures, setLectures] = useState([])
  const [progress, setProgress] = useState(null)
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [marking, setMarking] = useState(false)

  const fetchContent = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [lecData, progData] = await Promise.all([
        lectureService.listCourseLectures(courseId),
        lectureService.getCourseProgress(courseId),
      ])
      setLectures(lecData)
      setProgress(progData)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load course lectures.')
    } finally {
      setLoading(false)
    }
  }, [courseId])

  useEffect(() => {
    fetchContent()
  }, [fetchContent])

  const currentLecture = lectures[selectedIdx] || null

  const handleMarkCompleted = async () => {
    if (!currentLecture) return
    setMarking(true)
    try {
      await lectureService.completeLecture(currentLecture.id)
      showToast('Lecture marked as completed', 'success')
      await fetchContent()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to mark completed', 'error')
    } finally {
      setMarking(false)
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

  if (lectures.length === 0) {
    return (
      <div className="space-y-4">
        <Link to={`/courses/${courseId}`} className="text-xs font-medium text-indigo-600 hover:underline">
          ← Back to Course
        </Link>
        <EmptyState title="No lectures available" description="Lectures will appear here once published." />
      </div>
    )
  }

  const embedUrl = getYouTubeEmbedUrl(currentLecture?.video_url)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to={`/courses/${courseId}`} className="text-xs font-medium text-indigo-600 hover:underline">
            ← Back to Course
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{currentLecture.title}</h1>
        </div>
        {progress && (
          <div className="text-right">
            <p className="text-xs text-slate-500">Course Progress</p>
            <p className="text-sm font-semibold text-indigo-600">
              {progress.completed_lectures} / {progress.total_lectures} ({progress.progress_percentage}%)
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Video & Details */}
        <div className="space-y-4 lg:col-span-2">
          <Card>
            {embedUrl ? (
              <div className="aspect-video w-full overflow-hidden rounded-lg bg-slate-900">
                <iframe
                  title={currentLecture.title}
                  src={embedUrl}
                  className="h-full w-full"
                  allowFullScreen
                />
              </div>
            ) : currentLecture.video_url ? (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center">
                <p className="text-sm text-slate-700 mb-3">External / Uploaded Lecture Media</p>
                <a
                  href={currentLecture.video_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-indigo-600 hover:underline"
                >
                  Open Lecture Video →
                </a>
              </div>
            ) : (
              <div className="rounded-lg bg-slate-100 p-8 text-center text-sm text-slate-500">
                No video attached to this lecture.
              </div>
            )}

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Badge tone={currentLecture.is_completed ? 'success' : 'neutral'}>
                  {currentLecture.is_completed ? 'Completed' : 'In Progress'}
                </Badge>
                <span className="text-xs text-slate-500">{currentLecture.duration_minutes} mins</span>
              </div>
              <Button
                onClick={handleMarkCompleted}
                loading={marking}
                disabled={currentLecture.is_completed}
                variant={currentLecture.is_completed ? 'secondary' : 'primary'}
              >
                {currentLecture.is_completed ? '✓ Completed' : 'Mark as Completed'}
              </Button>
            </div>

            {currentLecture.description && (
              <p className="mt-4 border-t border-slate-100 pt-4 text-sm text-slate-600">
                {currentLecture.description}
              </p>
            )}
          </Card>

          {/* Study Materials */}
          <Card title="Study Materials">
            {!currentLecture.materials || currentLecture.materials.length === 0 ? (
              <p className="text-sm text-slate-500">No study materials for this lecture.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {currentLecture.materials.map((m) => (
                  <div key={m.id} className="flex items-center justify-between py-2.5 text-sm">
                    <div>
                      <p className="font-medium text-slate-900">{m.title}</p>
                      <p className="text-xs text-slate-500">
                        {m.file_name} • {Math.max(1, Math.round(m.file_size_bytes / 1024))} KB
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => lectureService.downloadMaterial(m.id, m.file_name)}
                    >
                      Download
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Prev / Next Navigation */}
          <div className="flex items-center justify-between">
            <Button
              variant="secondary"
              disabled={selectedIdx === 0}
              onClick={() => setSelectedIdx((i) => Math.max(0, i - 1))}
            >
              ← Previous Lecture
            </Button>
            <Button
              variant="secondary"
              disabled={selectedIdx >= lectures.length - 1}
              onClick={() => setSelectedIdx((i) => Math.min(lectures.length - 1, i + 1))}
            >
              Next Lecture →
            </Button>
          </div>
        </div>

        {/* Lecture Playlist */}
        <Card title="Lectures">
          <div className="space-y-1.5">
            {lectures.map((lec, idx) => (
              <button
                key={lec.id}
                type="button"
                onClick={() => setSelectedIdx(idx)}
                className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition ${
                  idx === selectedIdx
                    ? 'bg-indigo-50 text-indigo-700 font-medium'
                    : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                <span className="truncate">{idx + 1}. {lec.title}</span>
                {lec.is_completed && <span className="text-emerald-600 text-xs">✓</span>}
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
