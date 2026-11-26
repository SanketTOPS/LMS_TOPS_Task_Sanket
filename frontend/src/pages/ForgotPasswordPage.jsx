import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, Input } from '../components'
import { authService } from '../services/authService'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)
    try {
      const res = await authService.forgotPassword(email)
      setMessage(res.detail)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Request failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md">
        <Card title="Forgot Password" subtitle="Enter your account email to receive a reset link.">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </div>
            )}
            {message && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                {message}
              </div>
            )}
            <Input
              label="Email Address"
              name="email"
              type="email"
              required
              placeholder="you@institute.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" loading={loading} className="w-full">
              Send Reset Link
            </Button>
            <div className="text-center">
              <Link to="/login" className="text-xs font-medium text-indigo-600 hover:text-indigo-500">
                Back to Sign In
              </Link>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}
