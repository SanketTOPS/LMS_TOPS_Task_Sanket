import api from './api'

async function downloadBlob(url, fileName) {
  const response = await api.get(url, { responseType: 'blob' })
  const blobUrl = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = blobUrl
  link.setAttribute('download', fileName)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(blobUrl)
}

export const assignmentService = {
  async listAssignments(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/assignments', { params: clean })
    return data
  },

  async createAssignment(payload) {
    const { data } = await api.post('/assignments', payload)
    return data
  },

  async updateAssignment(id, payload) {
    const { data } = await api.put(`/assignments/${id}`, payload)
    return data
  },

  async deleteAssignment(id) {
    await api.delete(`/assignments/${id}`)
  },

  async uploadAttachment(id, file) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`/assignments/${id}/attachment`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async downloadAttachment(id, fileName) {
    await downloadBlob(`/assignments/${id}/attachment`, fileName)
  },

  async listSubmissions(assignmentId) {
    const { data } = await api.get(`/assignments/${assignmentId}/submissions`)
    return data
  },

  async submitAssignment({ assignment_id, submission_text, file }) {
    const form = new FormData()
    form.append('assignment_id', assignment_id)
    if (submission_text) form.append('submission_text', submission_text)
    if (file) form.append('file', file)
    const { data } = await api.post('/submissions', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async evaluateSubmission(submissionId, payload) {
    const { data } = await api.post(`/submissions/${submissionId}/evaluate`, payload)
    return data
  },

  async downloadSubmission(submissionId, fileName) {
    await downloadBlob(`/submissions/${submissionId}/download`, fileName)
  },
}
