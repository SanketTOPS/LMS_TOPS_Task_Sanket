import api from './api'

export const authService = {
  async login(email, password) {
    const { data } = await api.post('/auth/login', { email, password })
    return data
  },

  async forgotPassword(email) {
    const { data } = await api.post('/auth/forgot-password', { email })
    return data
  },

  async resetPassword(token, new_password) {
    const { data } = await api.post('/auth/reset-password', { token, new_password })
    return data
  },

  async changePassword(current_password, new_password) {
    const { data } = await api.post('/auth/change-password', {
      current_password,
      new_password,
    })
    return data
  },

  async getMe() {
    const { data } = await api.get('/auth/me')
    return data
  },

  async updateMe(payload) {
    const { data } = await api.put('/auth/me', payload)
    return data
  },
}
