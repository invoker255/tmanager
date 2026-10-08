import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { theme, applyTheme } from './stores/theme'
import './style.css'

applyTheme(theme.value)

createApp(App).use(router).mount('#app')
