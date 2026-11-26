import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Badge, Button } from '../components'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/dashboard', icon: '🏠', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Courses', to: '/courses', icon: '📚', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Batches', to: '/batches', icon: '👥', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Assignments', to: '/assignments', icon: '📝', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Quizzes', to: '/quizzes', icon: '⏱️', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Attendance', to: '/attendance', icon: '📅', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Progress', to: '/progress', icon: '📈', roles: ['Admin', 'Instructor', 'Student'] },
  { label: 'Students', to: '/students', icon: '🎓', roles: ['Admin', 'Instructor'] },
  { label: 'Instructors', to: '/instructors', icon: '🧑‍🏫', roles: ['Admin', 'Instructor'] },
  { label: 'Users', to: '/admin/users', icon: '🛡️', roles: ['Admin'] },
  { label: 'Profile', to: '/profile', icon: '⚙️', roles: ['Admin', 'Instructor', 'Student'] },
]

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const roleName = user?.role_name || ''
  const visibleNav = NAV_ITEMS.filter((item) => item.roles.includes(roleName))

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-150 ${
      isActive
        ? 'bg-accent-500 text-white shadow-sm'
        : 'text-blue-100/85 hover:bg-brand-800 hover:text-white'
    }`

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between bg-brand-900 text-white">
      <div>
        <div className="flex items-center justify-between border-b border-brand-800 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-500 text-sm font-extrabold text-white shadow">
              IT
            </div>
            <div>
              <span className="block text-base font-bold tracking-tight text-white">
                Institute LMS
              </span>
              <span className="block text-[10px] font-medium uppercase tracking-wider text-accent-500">
                Tech Career Portal
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setDrawerOpen(false)}
            className="rounded p-1 text-blue-200 hover:bg-brand-800 lg:hidden"
            aria-label="Close menu"
          >
            ✕
          </button>
        </div>
        <nav className="space-y-1 p-3">
          {visibleNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setDrawerOpen(false)}
              className={navLinkClass}
            >
              <span className="text-base leading-none">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="border-t border-brand-800 p-4 text-xs text-blue-200/80">
        Signed in as <strong className="block truncate text-white">{user?.full_name}</strong>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 shadow-lg z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
          />
          <aside className="relative z-50 w-64 shadow-2xl">{sidebarContent}</aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex flex-1 flex-col lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 backdrop-blur px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setDrawerOpen(true)}
              className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Open menu"
            >
              ☰
            </button>
            <span className="text-sm font-semibold text-brand-700 hidden sm:inline">
              Skill-First IT Training & Placement LMS
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-slate-900">{user?.full_name}</p>
              <p className="text-xs text-slate-500">{user?.email}</p>
            </div>
            <Badge tone="accent">{roleName}</Badge>
            <Button variant="secondary" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 animate-fade-in-up">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
