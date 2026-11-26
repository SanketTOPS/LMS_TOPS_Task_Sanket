import api from './api'

export const instructorService = {
  async listInstructors(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/instructors', { params: clean })
    return data
  },

  async getMyProfile() {
    const { data } = await api.get('/instructors/me')
    return data
  },

  async createInstructor(payload) {
    const { data } = await api.post('/instructors', payload)
    return data
  },

  async updateInstructor(id, payload) {
    const { data } = await api.put(`/instructors/${id}`, payload)
    return data
  },

  async getInstructorBatches(id) {
    const { data } = await api.get(`/instructors/${id}/batches`)
    return data
  },

  async assignInstructor(id, payload) {
    const { data } = await api.post(`/instructors/${id}/assign`, payload)
    return data
  },
}
