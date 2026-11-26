import api from './api'

export const quizService = {
  async listQuizzes(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined)
    )
    const { data } = await api.get('/quizzes', { params: clean })
    return data
  },

  async getQuiz(id) {
    const { data } = await api.get(`/quizzes/${id}`)
    return data
  },

  async createQuiz(payload) {
    const { data } = await api.post('/quizzes', payload)
    return data
  },

  async updateQuiz(id, payload) {
    const { data } = await api.put(`/quizzes/${id}`, payload)
    return data
  },

  async deleteQuiz(id) {
    await api.delete(`/quizzes/${id}`)
  },

  async listAdminQuestions(quizId) {
    const { data } = await api.get(`/quizzes/${quizId}/questions`)
    return data
  },

  async addQuestion(quizId, payload) {
    const { data } = await api.post(`/quizzes/${quizId}/questions`, payload)
    return data
  },

  async deleteQuestion(quizId, questionId) {
    await api.delete(`/quizzes/${quizId}/questions/${questionId}`)
  },

  async listResults(quizId) {
    const { data } = await api.get(`/quizzes/${quizId}/results`)
    return data
  },

  async startQuiz(quizId) {
    const { data } = await api.post(`/quizzes/${quizId}/start`)
    return data
  },

  async getAttempt(attemptId) {
    const { data } = await api.get(`/quiz-attempts/${attemptId}`)
    return data
  },

  async saveAnswer(attemptId, question_id, selected_option_id) {
    const { data } = await api.put(`/quiz-attempts/${attemptId}/answer`, {
      question_id,
      selected_option_id,
    })
    return data
  },

  async submitAttempt(attemptId) {
    const { data } = await api.post(`/quiz-attempts/${attemptId}/submit`)
    return data
  },
}
