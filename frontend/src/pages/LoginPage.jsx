import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Button, Input, useToast } from '../components'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      showToast('Signed in successfully', 'success')
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to sign in. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2 bg-slate-50">
      {/* Left Hero Panel */}
      <div className="relative hidden lg:flex flex-col justify-between bg-blue-950 p-10 text-white overflow-hidden">
        <img
          src="/images/hero-lms.jpg"
          alt="IT Training Classroom"
          className="absolute inset-0 h-full w-full object-cover opacity-30"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950/95 via-blue-900/85 to-blue-800/75" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-orange-500 text-lg font-extrabold text-white shadow-lg">
            IT
          </div>
          <div>
            <span className="block text-xl font-bold tracking-tight text-white">Institute LMS</span>
            <span className="block text-xs uppercase tracking-widest text-orange-400 font-semibold">
              Tech Career & Placement Portal
            </span>
          </div>
        </div>

        <div className="relative z-10 max-w-lg space-y-6 animate-fade-in-up">
          <span className="inline-block rounded-full bg-orange-500/20 border border-orange-400/50 px-3.5 py-1 text-xs font-semibold text-orange-200">
            Industry-Aligned IT Training
          </span>
          <h1 className="text-4xl font-extrabold leading-tight text-white">
            Launch Your Tech Career with Hands-On Mentorship
          </h1>
          <p className="text-sm leading-relaxed text-slate-200">
            Access live batch schedules, recorded lectures, practical assignments, timed
            assessments, attendance tracking, and verified course completion certificates in one
            unified portal.
          </p>

          <div className="grid grid-cols-3 gap-4 pt-2">
            <div className="rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 p-3.5">
              <p className="text-xl font-extrabold text-orange-400">100%</p>
              <p className="text-xs text-slate-200">Practical Labs</p>
            </div>
            <div className="rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 p-3.5">
              <p className="text-xl font-extrabold text-orange-400">Live</p>
              <p className="text-xs text-slate-200">Batch Mentors</p>
            </div>
            <div className="rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 p-3.5">
              <p className="text-xl font-extrabold text-orange-400">Verified</p>
              <p className="text-xs text-slate-200">Certificates</p>
            </div>
          </div>
        </div>

        <p className="relative z-10 text-xs text-slate-300">
          © {new Date().getFullYear()} Institute LMS — Training & Placement Management
        </p>
      </div>

      {/* Right Login Card */}
      <div className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md animate-fade-in-up">
          <div className="mb-8 text-center lg:text-left">
            <div className="mx-auto lg:mx-0 mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-900 text-white font-extrabold shadow-md lg:hidden">
              IT
            </div>
            <h2 className="text-3xl font-extrabold text-blue-950">Welcome Back</h2>
            <p className="mt-1.5 text-sm text-slate-600">
              Sign in with your institute credentials to continue
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-lg shadow-slate-200/60">
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
                  {error}
                </div>
              )}
              <Input
                label="Email Address"
                name="email"
                type="email"
                required
                autoComplete="email"
                placeholder="you@institute.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Input
                label="Password"
                name="password"
                type="password"
                required
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <div className="flex items-center justify-end">
                <Link
                  to="/forgot-password"
                  className="text-xs font-semibold text-orange-600 hover:text-orange-500"
                >
                  Forgot password?
                </Link>
              </div>
              <Button type="submit" variant="accent" size="lg" loading={loading} className="w-full">
                Sign In to Portal
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
