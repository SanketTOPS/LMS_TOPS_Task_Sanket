import api from './api'

export const userService = {
  async listUsers(params = {}) {
    const cleanParams = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/users', { params: cleanParams })
    return data
  },

  async createUser(payload) {
    const { data } = await api.post('/users', payload)
    return data
  },

  async updateUser(id, payload) {
    const { data } = await api.put(`/users/${id}`, payload)
    return data
  },

  async deactivateUser(id) {
    const { data } = await api.patch(`/users/${id}/deactivate`)
    return data
  },

  async resetPassword(id, new_password) {
    const { data } = await api.post(`/users/${id}/reset-password`, { new_password })
    return data
  },
}
