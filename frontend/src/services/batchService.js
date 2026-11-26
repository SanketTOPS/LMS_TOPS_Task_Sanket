import api from './api'

export const batchService = {
  async listBatches(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/batches', { params: clean })
    return data
  },

  async getBatch(id) {
    const { data } = await api.get(`/batches/${id}`)
    return data
  },

  async createBatch(payload) {
    const { data } = await api.post('/batches', payload)
    return data
  },

  async updateBatch(id, payload) {
    const { data } = await api.put(`/batches/${id}`, payload)
    return data
  },

  async closeBatch(id) {
    const { data } = await api.patch(`/batches/${id}/close`)
    return data
  },

  async archiveBatch(id) {
    const { data } = await api.patch(`/batches/${id}/archive`)
    return data
  },

  async getRoster(id) {
    const { data } = await api.get(`/batches/${id}/roster`)
    return data
  },

  async addStudent(batchId, student_id) {
    const { data } = await api.post(`/batches/${batchId}/students`, { student_id })
    return data
  },

  async removeStudent(batchId, studentId) {
    await api.delete(`/batches/${batchId}/students/${studentId}`)
  },
}
