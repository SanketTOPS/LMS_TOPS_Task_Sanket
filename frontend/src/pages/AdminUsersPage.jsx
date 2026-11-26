import { useCallback, useEffect, useState } from 'react'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  Input,
  Modal,
  Pagination,
  Table,
  useToast,
} from '../components'
import { userService } from '../services/userService'

const INITIAL_FORM = {
  full_name: '',
  email: '',
  phone: '',
  role_name: 'Student',
  password: '',
  is_active: true,
}

export default function AdminUsersPage() {
  const { showToast } = useToast()

  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  // Create / Edit modal
  const [formOpen, setFormOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Deactivate confirm
  const [deactivateTarget, setDeactivateTarget] = useState(null)
  const [deactivating, setDeactivating] = useState(false)

  // Admin reset password modal
  const [resetTarget, setResetTarget] = useState(null)
  const [resetPw, setResetPw] = useState('')
  const [resetting, setResetting] = useState(false)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await userService.listUsers({
        q: search || undefined,
        role: roleFilter || undefined,
        is_active: statusFilter === '' ? undefined : statusFilter === 'true',
        page,
        page_size: 10,
      })
      setUsers(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load users.')
    } finally {
      setLoading(false)
    }
  }, [search, roleFilter, statusFilter, page])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const openCreateModal = () => {
    setEditingUser(null)
    setFormData(INITIAL_FORM)
    setFormError('')
    setFormOpen(true)
  }

  const openEditModal = (u) => {
    setEditingUser(u)
    setFormData({
      full_name: u.full_name,
      email: u.email,
      phone: u.phone || '',
      role_name: u.role_name,
      password: '',
      is_active: u.is_active,
    })
    setFormError('')
    setFormOpen(true)
  }

  const handleSaveUser = async (e) => {
    e.preventDefault()
    setFormError('')
    setSubmitting(true)
    try {
      if (editingUser) {
        await userService.updateUser(editingUser.id, {
          full_name: formData.full_name,
          email: formData.email,
          phone: formData.phone || null,
          role_name: formData.role_name,
          is_active: formData.is_active,
        })
        showToast('User updated successfully', 'success')
      } else {
        await userService.createUser({
          full_name: formData.full_name,
          email: formData.email,
          phone: formData.phone || null,
          role_name: formData.role_name,
          password: formData.password,
          is_active: formData.is_active,
        })
        showToast('User created successfully', 'success')
      }
      setFormOpen(false)
      fetchUsers()
    } catch (err) {
      setFormError(err?.response?.data?.detail || 'Failed to save user.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeactivate = async () => {
    if (!deactivateTarget) return
    setDeactivating(true)
    try {
      await userService.deactivateUser(deactivateTarget.id)
      showToast('User deactivated', 'success')
      setDeactivateTarget(null)
      fetchUsers()
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to deactivate user', 'error')
    } finally {
      setDeactivating(false)
    }
  }

  const handleAdminResetPassword = async (e) => {
    e.preventDefault()
    if (!resetTarget) return
    setResetting(true)
    try {
      await userService.resetPassword(resetTarget.id, resetPw)
      showToast('Password reset successfully', 'success')
      setResetTarget(null)
      setResetPw('')
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to reset password', 'error')
    } finally {
      setResetting(false)
    }
  }

  const columns = [
    {
      key: 'full_name',
      header: 'Name',
      render: (row) => (
        <div>
          <p className="font-medium text-slate-900">{row.full_name}</p>
          <p className="text-xs text-slate-500">{row.email}</p>
        </div>
      ),
    },
    {
      key: 'role_name',
      header: 'Role',
      render: (row) => <Badge tone="primary">{row.role_name}</Badge>,
    },
    {
      key: 'phone',
      header: 'Phone',
      render: (row) => row.phone || '—',
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <Badge tone={row.is_active ? 'success' : 'danger'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => openEditModal(row)}>
            Edit
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setResetTarget(row)
              setResetPw('')
            }}
          >
            Reset PW
          </Button>
          {row.is_active && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setDeactivateTarget(row)}
            >
              Deactivate
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage admins, instructors, and students.
          </p>
        </div>
        <Button onClick={openCreateModal}>+ Create User</Button>
      </div>

      <Card>
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value)
              setPage(1)
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          >
            <option value="">All Roles</option>
            <option value="Admin">Admin</option>
            <option value="Instructor">Instructor</option>
            <option value="Student">Student</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          >
            <option value="">All Statuses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        <Table columns={columns} data={users} loading={loading} error={error} />
        <Pagination
          page={page}
          totalPages={totalPages}
          total={total}
          onPageChange={setPage}
        />
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        title={editingUser ? 'Edit User' : 'Create User'}
      >
        <form onSubmit={handleSaveUser} className="space-y-4">
          {formError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <Input
            label="Full Name"
            required
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
          />
          <Input
            label="Email"
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <Input
            label="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Role</label>
            <select
              value={formData.role_name}
              onChange={(e) => setFormData({ ...formData, role_name: e.target.value })}
              className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            >
              <option value="Student">Student</option>
              <option value="Instructor">Instructor</option>
              <option value="Admin">Admin</option>
            </select>
          </div>
          {!editingUser && (
            <Input
              label="Password"
              type="password"
              required
              hint="Min 8 chars, uppercase, lowercase, and digit"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          )}
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            Active account
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setFormOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={submitting}>
              {editingUser ? 'Save Changes' : 'Create User'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Admin Reset Password Modal */}
      <Modal
        isOpen={Boolean(resetTarget)}
        onClose={() => setResetTarget(null)}
        title={`Reset Password: ${resetTarget?.full_name || ''}`}
        maxWidth="max-w-md"
      >
        <form onSubmit={handleAdminResetPassword} className="space-y-4">
          <Input
            label="New Password"
            type="password"
            required
            hint="Min 8 chars, uppercase, lowercase, and digit"
            value={resetPw}
            onChange={(e) => setResetPw(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setResetTarget(null)}>
              Cancel
            </Button>
            <Button type="submit" loading={resetting}>
              Reset Password
            </Button>
          </div>
        </form>
      </Modal>

      {/* Deactivate Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(deactivateTarget)}
        onClose={() => setDeactivateTarget(null)}
        onConfirm={handleDeactivate}
        loading={deactivating}
        title="Deactivate User"
        message={`Are you sure you want to deactivate ${deactivateTarget?.full_name}? They will no longer be able to sign in.`}
        confirmLabel="Deactivate"
      />
    </div>
  )
}
