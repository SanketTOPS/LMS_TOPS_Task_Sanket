import { useEffect, useState } from 'react'
import { Badge, Button, Card, EmptyState, Input, Spinner, Table, useToast } from '../components'
import { useAuth } from '../context/AuthContext'
import { attendanceService } from '../services/attendanceService'
import { batchService } from '../services/batchService'

export default function AttendancePage() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const isStudent = user?.role_name === 'Student'

  // Admin/Instructor state
  const [batches, setBatches] = useState([])
  const [selectedBatchId, setSelectedBatchId] = useState('')
  const [classDate, setClassDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [sessionStatus, setSessionStatus] = useState('held')
  const [sessionNotes, setSessionNotes] = useState('')
  const [roster, setRoster] = useState([])
  const [attendanceMap, setAttendanceMap] = useState({})
  const [remarksMap, setRemarksMap] = useState({})
  const [loadingRoster, setLoadingRoster] = useState(false)
  const [saving, setSaving] = useState(false)

  // Student state
  const [studentSummary, setStudentSummary] = useState(null)
  const [loadingStudent, setLoadingStudent] = useState(false)

  // 1. Initial Load for Admin/Instructor: Batches
  useEffect(() => {
    if (!isStudent) {
      batchService
        .listBatches({ page_size: 100 })
        .then((res) => {
          const list = res.items || []
          setBatches(list)
          if (list.length > 0) {
            setSelectedBatchId(list[0].id)
          }
        })
        .catch((err) => {
          addToast(err?.response?.data?.detail || 'Failed to load batches', 'error')
        })
    } else {
      loadStudentAttendance()
    }
  }, [isStudent])

  // 2. Fetch Roster when Batch or Date changes (Admin/Instructor)
  useEffect(() => {
    if (!isStudent && selectedBatchId && classDate) {
      loadRoster()
    }
  }, [selectedBatchId, classDate, isStudent])

  const loadRoster = async () => {
    setLoadingRoster(true)
    try {
      const data = await attendanceService.getRoster(selectedBatchId, classDate)
      setRoster(data.students || [])
      setSessionStatus(data.session_status || 'held')
      setSessionNotes(data.notes || '')

      const initialStatus = {}
      const initialRemarks = {}
      data.students.forEach((s) => {
        initialStatus[s.student_id] = s.status || 'Present'
        initialRemarks[s.student_id] = s.remarks || ''
      })
      setAttendanceMap(initialStatus)
      setRemarksMap(initialRemarks)
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Failed to load roster', 'error')
    } finally {
      setLoadingRoster(false)
    }
  }

  const loadStudentAttendance = async () => {
    setLoadingStudent(true)
    try {
      const data = await attendanceService.getMyAttendance()
      setStudentSummary(data)
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Failed to load your attendance', 'error')
    } finally {
      setLoadingStudent(false)
    }
  }

  const handleStatusChange = (studentId, status) => {
    setAttendanceMap((prev) => ({ ...prev, [studentId]: status }))
  }

  const handleRemarkChange = (studentId, remark) => {
    setRemarksMap((prev) => ({ ...prev, [studentId]: remark }))
  }

  const handleMarkAll = (status) => {
    const updated = {}
    roster.forEach((s) => {
      updated[s.student_id] = status
    })
    setAttendanceMap(updated)
  }

  const handleSaveAttendance = async () => {
    setSaving(true)
    try {
      const records = roster.map((s) => ({
        student_id: s.student_id,
        status: attendanceMap[s.student_id] || 'Present',
        remarks: remarksMap[s.student_id] || null,
      }))

      await attendanceService.bulkSave({
        batch_id: Number(selectedBatchId),
        class_date: classDate,
        session_status: sessionStatus,
        notes: sessionNotes || null,
        records,
      })
      addToast('Attendance saved successfully', 'success')
      loadRoster()
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Failed to save attendance', 'error')
    } finally {
      setSaving(false)
    }
  }

  // Render for Student
  if (isStudent) {
    if (loadingStudent) {
      return (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )
    }

    const {
      total_eligible_classes = 0,
      total_present = 0,
      total_absent = 0,
      total_approved_leave = 0,
      attendance_percentage = 0,
      monthly_summary = [],
      records = [],
    } = studentSummary || {}

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">My Attendance</h1>
          <p className="mt-1 text-sm text-slate-500">
            Track your class attendance history, monthly trends, and overall attendance rate.
          </p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Card className="p-4 border-l-4 border-l-indigo-500">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Overall Rate
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-indigo-600">
                {attendance_percentage.toFixed(1)}%
              </span>
              <Badge variant={attendance_percentage >= 75 ? 'success' : 'danger'}>
                {attendance_percentage >= 75 ? 'Meets 75% Criteria' : 'Below Threshold'}
              </Badge>
            </div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Eligible Classes
            </span>
            <div className="mt-2 text-3xl font-extrabold text-slate-800">
              {total_eligible_classes}
            </div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Present
            </span>
            <div className="mt-2 text-3xl font-extrabold text-emerald-600">{total_present}</div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Absent
            </span>
            <div className="mt-2 text-3xl font-extrabold text-rose-600">{total_absent}</div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Approved Leave
            </span>
            <div className="mt-2 text-3xl font-extrabold text-amber-600">{total_approved_leave}</div>
          </Card>
        </div>

        {/* Monthly Summary */}
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-base font-semibold text-slate-800">Monthly Breakdown</h2>
          </div>
          {monthly_summary.length === 0 ? (
            <div className="p-6">
              <EmptyState title="No monthly data" description="No attendance records recorded yet." />
            </div>
          ) : (
            <Table
              headers={['Month', 'Eligible Classes', 'Present', 'Absent', 'Approved Leave', 'Attendance %']}
              rows={monthly_summary.map((m) => [
                m.month,
                m.eligible_classes,
                m.present,
                m.absent,
                m.approved_leave,
                <Badge
                  key={m.month}
                  variant={m.percentage >= 75 ? 'success' : m.percentage >= 50 ? 'warning' : 'danger'}
                >
                  {m.percentage.toFixed(1)}%
                </Badge>,
              ])}
            />
          )}
        </Card>

        {/* Detailed Records */}
        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-base font-semibold text-slate-800">Class Session Logs</h2>
          </div>
          {records.length === 0 ? (
            <div className="p-6">
              <EmptyState title="No records found" description="You have no recorded attendance entries." />
            </div>
          ) : (
            <Table
              headers={['Date', 'Batch', 'Session Status', 'Attendance Status', 'Remarks']}
              rows={records.map((r) => [
                r.class_date,
                r.batch_name || `Batch #${r.batch_id}`,
                <Badge
                  key={`ss-${r.id}`}
                  variant={
                    r.session_status === 'held'
                      ? 'info'
                      : r.session_status === 'holiday'
                      ? 'warning'
                      : 'danger'
                  }
                >
                  {r.session_status}
                </Badge>,
                <Badge
                  key={`st-${r.id}`}
                  variant={
                    r.status === 'Present'
                      ? 'success'
                      : r.status === 'Approved Leave'
                      ? 'warning'
                      : 'danger'
                  }
                >
                  {r.status}
                </Badge>,
                r.remarks || '—',
              ])}
            />
          )}
        </Card>
      </div>
    )
  }

  // Render for Admin & Instructor
  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Attendance Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            Record, update, and manage daily attendance rosters with an automated audit trail.
          </p>
        </div>
      </div>

      {/* Control Panel */}
      <Card className="p-6 space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Select Batch
            </label>
            <select
              value={selectedBatchId}
              onChange={(e) => setSelectedBatchId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
            >
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.code})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Class Date
            </label>
            <Input
              type="date"
              value={classDate}
              onChange={(e) => setClassDate(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Class Session Status
            </label>
            <select
              value={sessionStatus}
              onChange={(e) => setSessionStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
            >
              <option value="held">Held (Normal Class)</option>
              <option value="cancelled">Cancelled (Excluded from attendance denominator)</option>
              <option value="holiday">Holiday (Excluded from attendance denominator)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
            Session Notes (Optional)
          </label>
          <Input
            placeholder="e.g. Chapter 4 covered, substitute lab session, public holiday"
            value={sessionNotes}
            onChange={(e) => setSessionNotes(e.target.value)}
          />
        </div>
      </Card>

      {/* Roster Sheet */}
      <Card className="overflow-hidden">
        <div className="flex flex-col sm:flex-row items-center justify-between border-b border-slate-200 px-6 py-4 gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-800">
              Student Roster ({roster.length} students)
            </h2>
            {sessionStatus !== 'held' && (
              <p className="text-xs text-amber-600 font-medium">
                Note: This session is marked as "{sessionStatus}". Individual student attendance will not penalize attendance percentage.
              </p>
            )}
          </div>

          {sessionStatus === 'held' && roster.length > 0 && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleMarkAll('Present')}
              >
                Mark All Present
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleMarkAll('Absent')}
              >
                Mark All Absent
              </Button>
            </div>
          )}
        </div>

        {loadingRoster ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner />
          </div>
        ) : roster.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No students found in this batch"
              description="Enroll students in this batch before taking attendance."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-700 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Student Name</th>
                  <th className="px-6 py-3">Email</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {roster.map((s) => {
                  const currentStatus = attendanceMap[s.student_id] || 'Present'
                  return (
                    <tr key={s.student_id} className="hover:bg-slate-50/60">
                      <td className="px-6 py-3 font-medium text-slate-900">{s.full_name}</td>
                      <td className="px-6 py-3 text-slate-500">{s.email}</td>
                      <td className="px-6 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            disabled={sessionStatus !== 'held'}
                            onClick={() => handleStatusChange(s.student_id, 'Present')}
                            className={`px-3 py-1 text-xs font-medium rounded-md border transition ${
                              currentStatus === 'Present'
                                ? 'bg-emerald-600 text-white border-emerald-600'
                                : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'
                            } disabled:opacity-50`}
                          >
                            Present
                          </button>
                          <button
                            type="button"
                            disabled={sessionStatus !== 'held'}
                            onClick={() => handleStatusChange(s.student_id, 'Absent')}
                            className={`px-3 py-1 text-xs font-medium rounded-md border transition ${
                              currentStatus === 'Absent'
                                ? 'bg-rose-600 text-white border-rose-600'
                                : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'
                            } disabled:opacity-50`}
                          >
                            Absent
                          </button>
                          <button
                            type="button"
                            disabled={sessionStatus !== 'held'}
                            onClick={() => handleStatusChange(s.student_id, 'Approved Leave')}
                            className={`px-3 py-1 text-xs font-medium rounded-md border transition ${
                              currentStatus === 'Approved Leave'
                                ? 'bg-amber-600 text-white border-amber-600'
                                : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'
                            } disabled:opacity-50`}
                          >
                            Leave
                          </button>
                        </div>
                      </td>
                      <td className="px-6 py-3">
                        <Input
                          placeholder="Optional notes..."
                          value={remarksMap[s.student_id] || ''}
                          onChange={(e) => handleRemarkChange(s.student_id, e.target.value)}
                          className="text-xs py-1"
                        />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {roster.length > 0 && (
          <div className="border-t border-slate-200 px-6 py-4 flex justify-end bg-slate-50">
            <Button
              variant="primary"
              onClick={handleSaveAttendance}
              disabled={saving || loadingRoster}
            >
              {saving ? 'Saving...' : 'Save Attendance'}
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}
