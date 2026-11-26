import { useEffect, useState } from 'react'
import { Badge, Button, Card, Input, useToast } from '../components'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const { showToast } = useToast()

  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [profileLoading, setProfileLoading] = useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [pwError, setPwError] = useState('')
  const [pwLoading, setPwLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '')
      setPhone(user.phone || '')
    }
  }, [user])

  const handleProfileSave = async (e) => {
    e.preventDefault()
    setProfileLoading(true)
    try {
      await authService.updateMe({ full_name: fullName, phone: phone || null })
      await refreshUser()
      showToast('Profile updated successfully', 'success')
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to update profile', 'error')
    } finally {
      setProfileLoading(false)
    }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setPwError('')
    if (newPassword !== confirmPassword) {
      setPwError('New passwords do not match.')
      return
    }
    setPwLoading(true)
    try {
      await authService.changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      showToast('Password changed successfully', 'success')
    } catch (err) {
      setPwError(err?.response?.data?.detail || 'Failed to change password.')
    } finally {
      setPwLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
        <p className="mt-1 text-sm text-slate-500">Manage your account details and password.</p>
      </div>

      <Card
        title="Account Information"
        actions={<Badge tone="primary">{user?.role_name}</Badge>}
      >
        <form onSubmit={handleProfileSave} className="space-y-4">
          <Input label="Email" value={user?.email || ''} disabled />
          <Input
            label="Full Name"
            name="fullName"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <Input
            label="Phone"
            name="phone"
            placeholder="+91-9000000000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <div className="flex justify-end">
            <Button type="submit" loading={profileLoading}>
              Save Changes
            </Button>
          </div>
        </form>
      </Card>

      <Card
        title="Change Password"
        subtitle="Minimum 8 characters with uppercase, lowercase, and a digit."
      >
        <form onSubmit={handlePasswordChange} className="space-y-4">
          {pwError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {pwError}
            </div>
          )}
          <Input
            label="Current Password"
            type="password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          <Input
            label="New Password"
            type="password"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <Input
            label="Confirm New Password"
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          <div className="flex justify-end">
            <Button type="submit" loading={pwLoading}>
              Update Password
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
