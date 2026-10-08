import { ref } from 'vue'

const KEY = 'theme'

export const theme = ref(localStorage.getItem(KEY) === 'light' ? 'light' : 'dark')

export function applyTheme(value) {
  const next = value === 'light' ? 'light' : 'dark'
  theme.value = next
  localStorage.setItem(KEY, next)
  document.documentElement.setAttribute('data-theme', next)
}
