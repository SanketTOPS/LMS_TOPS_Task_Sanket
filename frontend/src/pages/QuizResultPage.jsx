import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, Button, Card, Spinner, useToast } from '../components'
import { quizService } from '../services/quizService'

export default function QuizResultPage() {
  const { attemptId } = useParams()
  const { showToast } = useToast()

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    quizService
      .getAttempt(attemptId)
      .then((data) => setResult(data))
      .catch((err) => showToast(err?.response?.data?.detail || 'Failed to load result', 'error'))
      .finally(() => setLoading(false))
  }, [attemptId, showToast])

  if (loading) return <Spinner size="lg" label="Loading result..." />
  if (!result) return null

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/quizzes" className="text-xs font-medium text-indigo-600 hover:underline">
            ← Back to Quizzes
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{result.quiz_title} — Result</h1>
        </div>
        <Badge tone={result.is_passed ? 'success' : 'danger'}>
          {result.is_passed ? 'PASSED' : 'FAILED'}
        </Badge>
      </div>

      <Card>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-slate-500">Score</p>
            <p className="text-2xl font-bold text-slate-900">
              {result.score} / {result.total_marks}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Passing Marks</p>
            <p className="text-2xl font-bold text-slate-900">{result.passing_marks}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Attempt</p>
            <p className="text-2xl font-bold text-slate-900">#{result.attempt_number}</p>
          </div>
        </div>
      </Card>

      <Card title="Answer Review">
        <div className="divide-y divide-slate-100 space-y-4">
          {result.questions?.map((q, idx) => (
            <div key={q.id} className="pt-4 first:pt-0">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-slate-900">
                  {idx + 1}. {q.question_text}
                </p>
                <Badge tone={q.is_correct ? 'success' : 'danger'}>
                  {q.is_correct ? `+${q.marks}` : '0'}
                </Badge>
              </div>
              <div className="mt-2 space-y-1 text-xs">
                {q.options.map((opt) => {
                  const isSelected = opt.id === q.selected_option_id
                  const isCorrect = opt.id === q.correct_option_id
                  return (
                    <div
                      key={opt.id}
                      className={`rounded px-3 py-1.5 ${
                        isCorrect
                          ? 'bg-emerald-50 text-emerald-800 font-medium'
                          : isSelected
                            ? 'bg-rose-50 text-rose-800'
                            : 'text-slate-600'
                      }`}
                    >
                      {opt.option_text}
                      {isCorrect && ' ✓ (Correct Answer)'}
                      {isSelected && !isCorrect && ' ✗ (Your Answer)'}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div className="flex justify-end">
        <Link to="/quizzes">
          <Button variant="secondary">Back to Quizzes</Button>
        </Link>
      </div>
    </div>
  )
}
