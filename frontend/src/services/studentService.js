import api from './api'

export const studentService = {
  async listStudents(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/students', { params: clean })
    return data
  },

  async getStudent(id) {
    const { data } = await api.get(`/students/${id}`)
    return data
  },

  async createStudent(payload) {
    const { data } = await api.post('/students', payload)
    return data
  },

  async updateStudent(id, payload) {
    const { data } = await api.put(`/students/${id}`, payload)
    return data
  },

  async deactivateStudent(id) {
    const { data } = await api.delete(`/students/${id}`)
    return data
  },
}
