import api from './api'

export const courseService = {
  async listCourses(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/courses', { params: clean })
    return data
  },

  async getCourse(id) {
    const { data } = await api.get(`/courses/${id}`)
    return data
  },

  async createCourse(payload) {
    const { data } = await api.post('/courses', payload)
    return data
  },

  async updateCourse(id, payload) {
    const { data } = await api.put(`/courses/${id}`, payload)
    return data
  },

  async publishCourse(id, publish = true) {
    const { data } = await api.patch(`/courses/${id}/publish`, null, { params: { publish } })
    return data
  },

  async archiveCourse(id) {
    const { data } = await api.patch(`/courses/${id}/archive`)
    return data
  },

  async deleteCourse(id) {
    await api.delete(`/courses/${id}`)
  },

  async createModule(courseId, payload) {
    const { data } = await api.post(`/courses/${courseId}/modules`, payload)
    return data
  },

  async updateModule(courseId, moduleId, payload) {
    const { data } = await api.put(`/courses/${courseId}/modules/${moduleId}`, payload)
    return data
  },

  async deleteModule(courseId, moduleId) {
    await api.delete(`/courses/${courseId}/modules/${moduleId}`)
  },
}
