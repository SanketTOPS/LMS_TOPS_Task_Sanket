import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Button, Card, Input, useToast } from '../components'
import { authService } from '../services/authService'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [token, setToken] = useState(searchParams.get('token') || '')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await authService.resetPassword(token, newPassword)
      showToast('Password reset successfully. Please sign in.', 'success')
      navigate('/login')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to reset password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md">
        <Card
          title="Reset Password"
          subtitle="Minimum 8 characters with uppercase, lowercase, and a digit."
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </div>
            )}
            <Input
              label="Reset Token"
              name="token"
              required
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <Input
              label="New Password"
              name="newPassword"
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <Input
              label="Confirm New Password"
              name="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
            <Button type="submit" loading={loading} className="w-full">
              Reset Password
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
