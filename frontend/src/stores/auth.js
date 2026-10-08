import { reactive } from 'vue'

const TOKEN_KEY = 'auth_token'

export const auth = reactive({
  token: localStorage.getItem(TOKEN_KEY),
  get isAuthenticated() {
    return Boolean(this.token)
  },
  setToken(token) {
    this.token = token
    localStorage.setItem(TOKEN_KEY, token)
  },
  clear() {
    this.token = null
    localStorage.removeItem(TOKEN_KEY)
  }
})
