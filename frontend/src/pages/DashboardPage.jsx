import { Link } from 'react-router-dom'
import { Badge, Button, Card } from '../components'
import { useAuth } from '../context/AuthContext'

const QUICK_LINKS = [
  {
    title: 'Explore Courses',
    desc: 'Browse curriculum modules, lectures, and study materials.',
    to: '/courses',
    img: '/images/course-fullstack.jpg',
    badge: 'Curriculum',
    roles: ['Admin', 'Instructor', 'Student'],
  },
  {
    title: 'Assignments & Labs',
    desc: 'Submit practical work or evaluate student submissions.',
    to: '/assignments',
    img: '/images/course-default.jpg',
    badge: 'Practical',
    roles: ['Admin', 'Instructor', 'Student'],
  },
  {
    title: 'Quizzes & Progress',
    desc: 'Take timed MCQ assessments and track completion eligibility.',
    to: '/progress',
    img: '/images/course-data-ml.jpg',
    badge: 'Assessments',
    roles: ['Admin', 'Instructor', 'Student'],
  },
]

export default function DashboardPage() {
  const { user } = useAuth()
  const roleName = user?.role_name || ''

  const visibleLinks = QUICK_LINKS.filter((item) => item.roles.includes(roleName))

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-brand-900 text-white shadow-lg">
        <img
          src="/images/hero-lms.jpg"
          alt="Training Institute Banner"
          className="absolute inset-0 h-full w-full object-cover opacity-25"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-brand-900 via-brand-800/90 to-brand-700/75" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6 p-6 sm:p-8">
          <div className="max-w-2xl space-y-2">
            <div className="flex items-center gap-2">
              <Badge tone="accent">{roleName} Workspace</Badge>
              <span className="text-xs text-blue-200">Active Session</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Welcome back, {user?.full_name}
            </h1>
            <p className="text-sm text-blue-100">
              Manage your IT training modules, live batches, practical assignments, timed quizzes,
              attendance, and course completion progress from one place.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/courses">
              <Button variant="accent" size="md">
                Browse Courses
              </Button>
            </Link>
            <Link to="/attendance">
              <Button variant="outlineLight" size="md">
                View Attendance
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Institute Highlights */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Practical Training', value: '100%', tone: 'text-brand-700' },
          { label: 'Attendance Target', value: '75%+', tone: 'text-accent-600' },
          { label: 'Completion Goal', value: '80%+', tone: 'text-emerald-600' },
          { label: 'Evaluation Mode', value: 'Server-Verified', tone: 'text-brand-700' },
        ].map((stat) => (
          <Card key={stat.label} hover className="text-center">
            <p className={`text-2xl font-extrabold ${stat.tone}`}>{stat.value}</p>
            <p className="mt-1 text-xs font-medium text-slate-500">{stat.label}</p>
          </Card>
        ))}
      </div>

      {/* Visual Quick-Access Cards */}
      <div>
        <h2 className="mb-3 text-lg font-bold text-slate-900">Quick Access</h2>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {visibleLinks.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm card-hover"
            >
              <div className="relative h-40 overflow-hidden bg-slate-100">
                <img
                  src={item.img}
                  alt={item.title}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
                <span className="absolute top-3 left-3 rounded-full bg-brand-900/85 px-2.5 py-0.5 text-[11px] font-semibold text-white backdrop-blur-sm">
                  {item.badge}
                </span>
              </div>
              <div className="p-5">
                <h3 className="text-base font-bold text-slate-900 group-hover:text-brand-700">
                  {item.title}
                </h3>
                <p className="mt-1 text-xs text-slate-500 leading-relaxed">{item.desc}</p>
                <span className="mt-3 inline-block text-xs font-semibold text-accent-600">
                  Open module →
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
