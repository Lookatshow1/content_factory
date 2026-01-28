import axios from 'axios'

export const api = axios.create({
  baseURL: '',  // Используем relative URL, обрабатывается через rewrites
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)
