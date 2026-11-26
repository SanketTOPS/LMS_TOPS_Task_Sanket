import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Card, ConfirmDialog, Spinner, useToast } from '../components'
import { quizService } from '../services/quizService'

function formatSeconds(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function QuizAttemptPage() {
  const { attemptId } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [attempt, setAttempt] = useState(null)
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [answers, setAnswers] = useState({})
  const [remaining, setRemaining] = useState(0)
  const [loading, setLoading] = useState(true)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = useCallback(async () => {
    setSubmitting(true)
    try {
      await quizService.submitAttempt(attemptId)
      showToast('Quiz submitted', 'success')
      navigate(`/quiz-attempts/${attemptId}/result`, { replace: true })
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Submission failed', 'error')
    } finally {
      setSubmitting(false)
      setConfirmOpen(false)
    }
  }, [attemptId, navigate, showToast])

  useEffect(() => {
    let active = true
    quizService
      .getAttempt(attemptId)
      .then((data) => {
        if (!active) return
        if (data.is_submitted) {
          navigate(`/quiz-attempts/${attemptId}/result`, { replace: true })
          return
        }
        setAttempt(data)
        setRemaining(data.remaining_seconds)
        const initialAns = {}
        data.questions.forEach((q) => {
          if (q.selected_option_id) initialAns[q.id] = q.selected_option_id
        })
        setAnswers(initialAns)
      })
      .catch((err) => {
        showToast(err?.response?.data?.detail || 'Failed to load quiz attempt', 'error')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [attemptId, navigate, showToast])

  // Countdown timer synced from server remaining_seconds
  useEffect(() => {
    if (!attempt) return
    if (remaining <= 0) {
      handleSubmit()
      return
    }
    const timer = setInterval(() => {
      setRemaining((prev) => Math.max(0, prev - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [attempt, remaining, handleSubmit])

  const handleSelectOption = async (questionId, optionId) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }))
    try {
      await quizService.saveAnswer(attemptId, questionId, optionId)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to save answer', 'error')
      if (err?.response?.data?.code === 'QUIZ_TIME_EXPIRED') {
        navigate(`/quiz-attempts/${attemptId}/result`, { replace: true })
      }
    }
  }

  if (loading) return <Spinner size="lg" label="Loading quiz..." />
  if (!attempt) return null

  const questions = attempt.questions || []
  const currentQ = questions[selectedIdx]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{attempt.quiz_title}</h1>
          <p className="text-sm text-slate-500">Attempt #{attempt.attempt_number}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700">
            Time Left: {formatSeconds(remaining)}
          </div>
          <Button onClick={() => setConfirmOpen(true)}>Submit Quiz</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          {currentQ && (
            <Card title={`Question ${selectedIdx + 1} of ${questions.length} (${currentQ.marks} marks)`}>
              <p className="mb-4 text-base font-medium text-slate-900">{currentQ.question_text}</p>
              <div className="space-y-2.5">
                {currentQ.options.map((opt) => {
                  const isSelected = answers[currentQ.id] === opt.id
                  return (
                    <label
                      key={opt.id}
                      className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 text-sm transition ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-900'
                          : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`q-${currentQ.id}`}
                        checked={isSelected}
                        onChange={() => handleSelectOption(currentQ.id, opt.id)}
                      />
                      <span>{opt.option_text}</span>
                    </label>
                  )
                })}
              </div>

              <div className="mt-6 flex items-center justify-between">
                <Button
                  variant="secondary"
                  disabled={selectedIdx === 0}
                  onClick={() => setSelectedIdx((i) => Math.max(0, i - 1))}
                >
                  ← Previous
                </Button>
                <Button
                  variant="secondary"
                  disabled={selectedIdx >= questions.length - 1}
                  onClick={() => setSelectedIdx((i) => Math.min(questions.length - 1, i + 1))}
                >
                  Next →
                </Button>
              </div>
            </Card>
          )}
        </div>

        <Card title="Question Navigator">
          <div className="grid grid-cols-5 gap-2">
            {questions.map((q, idx) => {
              const answered = Boolean(answers[q.id])
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => setSelectedIdx(idx)}
                  className={`rounded-lg py-2 text-xs font-semibold transition ${
                    idx === selectedIdx
                      ? 'bg-indigo-600 text-white'
                      : answered
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {idx + 1}
                </button>
              )
            })}
          </div>
        </Card>
      </div>

      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleSubmit}
        loading={submitting}
        variant="primary"
        title="Submit Quiz"
        message={`You have answered ${Object.keys(answers).length} of ${questions.length} questions. Submit now?`}
        confirmLabel="Submit Quiz"
      />
    </div>
  )
}
