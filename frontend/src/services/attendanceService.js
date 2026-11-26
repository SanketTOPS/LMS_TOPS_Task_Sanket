import api from './api'

export const attendanceService = {
  getRoster: async (batchId, classDate) => {
    const response = await api.get('/attendance/roster', {
      params: { batch_id: batchId, class_date: classDate },
    })
    return response.data
  },

  getDailyView: async (batchId, classDate) => {
    const response = await api.get('/attendance/daily', {
      params: { batch_id: batchId, class_date: classDate },
    })
    return response.data
  },

  createSingle: async (payload) => {
    const response = await api.post('/attendance', payload)
    return response.data
  },

  bulkSave: async (payload) => {
    const response = await api.post('/attendance/bulk', payload)
    return response.data
  },

  getMyAttendance: async (batchId) => {
    const params = batchId ? { batch_id: batchId } : {}
    const response = await api.get('/attendance/me', { params })
    return response.data
  },

  getMyProgress: async () => {
    const response = await api.get('/progress/me')
    return response.data
  },

  getStudentProgress: async (studentId) => {
    const response = await api.get(`/progress/student/${studentId}`)
    return response.data
  },
}

export default attendanceService
