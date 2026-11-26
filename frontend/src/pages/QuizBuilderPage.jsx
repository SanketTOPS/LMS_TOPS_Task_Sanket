import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, Button, Card, Input, Spinner, useToast } from '../components'
import { quizService } from '../services/quizService'

export default function QuizBuilderPage() {
  const { quizId } = useParams()
  const { showToast } = useToast()

  const [quiz, setQuiz] = useState(null)
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)

  const [qText, setQText] = useState('')
  const [marks, setMarks] = useState('1')
  const [options, setOptions] = useState(['', '', '', ''])
  const [correctIdx, setCorrectIdx] = useState(0)
  const [adding, setAdding] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [qz, qs] = await Promise.all([
        quizService.getQuiz(quizId),
        quizService.listAdminQuestions(quizId),
      ])
      setQuiz(qz)
      setQuestions(qs)
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to load quiz', 'error')
    } finally {
      setLoading(false)
    }
  }, [quizId, showToast])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleAddQuestion = async (e) => {
    e.preventDefault()
    const cleanOpts = options.map((o) => o.trim()).filter(Boolean)
    if (cleanOpts.length < 2) {
      showToast('Provide at least 2 options', 'error')
      return
    }
    setAdding(true)
    try {
      await quizService.addQuestion(quizId, {
        question_text: qText,
        marks: Number(marks),
        sort_order: questions.length + 1,
        options: cleanOpts,
        correct_option_index: Math.min(correctIdx, cleanOpts.length - 1),
      })
      showToast('Question added', 'success')
      setQText('')
      setOptions(['', '', '', ''])
      setCorrectIdx(0)
      fetchData()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to add question', 'error')
    } finally {
      setAdding(false)
    }
  }

  if (loading) return <Spinner size="lg" label="Loading quiz builder..." />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/quizzes" className="text-xs font-medium text-indigo-600 hover:underline">
            ← Back to Quizzes
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">
            Quiz Builder: {quiz?.title}
          </h1>
          <p className="text-sm text-slate-500">
            Total Marks: {quiz?.total_marks} • Passing: {quiz?.passing_marks}
          </p>
        </div>
        <Badge tone={quiz?.is_published ? 'success' : 'warning'}>
          {quiz?.is_published ? 'Published' : 'Draft'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Add MCQ Question">
          <form onSubmit={handleAddQuestion} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Question</label>
              <textarea
                rows={3}
                required
                value={qText}
                onChange={(e) => setQText(e.target.value)}
                className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
              />
            </div>
            <Input
              label="Marks"
              type="number"
              step="0.5"
              min="0.5"
              required
              value={marks}
              onChange={(e) => setMarks(e.target.value)}
            />
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">
                Options (select the correct one)
              </label>
              {options.map((opt, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="correctOpt"
                    checked={correctIdx === idx}
                    onChange={() => setCorrectIdx(idx)}
                  />
                  <Input
                    placeholder={`Option ${idx + 1}`}
                    value={opt}
                    onChange={(e) => {
                      const next = [...options]
                      next[idx] = e.target.value
                      setOptions(next)
                    }}
                  />
                </div>
              ))}
            </div>
            <Button type="submit" loading={adding}>+ Add Question</Button>
          </form>
        </Card>

        <Card title={`Questions (${questions.length})`}>
          {questions.length === 0 ? (
            <p className="text-sm text-slate-500">No questions added yet.</p>
          ) : (
            <div className="divide-y divide-slate-100 space-y-3">
              {questions.map((q, idx) => (
                <div key={q.id} className="pt-3 first:pt-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-900">
                      {idx + 1}. {q.question_text} ({q.marks}m)
                    </p>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => quizService.deleteQuestion(quizId, q.id).then(fetchData)}
                    >
                      Delete
                    </Button>
                  </div>
                  <ul className="mt-1.5 space-y-1 text-xs text-slate-600">
                    {q.options.map((o) => (
                      <li
                        key={o.id}
                        className={o.id === q.correct_option_id ? 'font-semibold text-emerald-700' : ''}
                      >
                        • {o.option_text} {o.id === q.correct_option_id ? '(Correct)' : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
