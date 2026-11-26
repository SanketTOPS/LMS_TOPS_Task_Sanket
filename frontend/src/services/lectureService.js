import api from './api'

export const lectureService = {
  async listCourseLectures(courseId) {
    const { data } = await api.get(`/courses/${courseId}/lectures`)
    return data
  },

  async getCourseProgress(courseId) {
    const { data } = await api.get(`/courses/${courseId}/progress`)
    return data
  },

  async createLecture(payload) {
    const { data } = await api.post('/lectures', payload)
    return data
  },

  async updateLecture(id, payload) {
    const { data } = await api.put(`/lectures/${id}`, payload)
    return data
  },

  async deleteLecture(id) {
    await api.delete(`/lectures/${id}`)
  },

  async reorderLectures(module_id, lecture_ids) {
    const { data } = await api.post('/lectures/reorder', { module_id, lecture_ids })
    return data
  },

  async uploadLectureVideo(lectureId, file) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`/lectures/${lectureId}/video`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async completeLecture(lectureId) {
    const { data } = await api.post(`/lectures/${lectureId}/complete`)
    return data
  },

  async uploadMaterial({ course_id, module_id, lecture_id, title, file }) {
    const form = new FormData()
    form.append('course_id', course_id)
    if (module_id) form.append('module_id', module_id)
    if (lecture_id) form.append('lecture_id', lecture_id)
    form.append('title', title)
    form.append('file', file)
    const { data } = await api.post('/materials', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async deleteMaterial(materialId) {
    await api.delete(`/materials/${materialId}`)
  },

  async downloadMaterial(materialId, fileName) {
    const response = await api.get(`/materials/${materialId}/download`, {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
