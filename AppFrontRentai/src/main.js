import './env'
import { migrateLegacyLocalStorageTokens } from '@/utils/authStorage'
import { createApp } from 'vue'

migrateLegacyLocalStorageTokens()
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
