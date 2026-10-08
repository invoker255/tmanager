<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersApi, extractError } from '../services/api'
import { auth } from '../stores/auth'
import { theme, applyTheme } from '../stores/theme'
import { REMINDERS } from '../utils'

const router = useRouter()

const THEMES = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' }
]

const loading = ref(true)
const loadError = ref('')

const profile = reactive({ username: '', email: '' })
const originalEmail = ref('')
const savingProfile = ref(false)
const profileMessage = ref('')
const profileError = ref('')

const prefs = reactive({ reminder_hours_before: 24, theme: theme.value })
const prefsMessage = ref('')
const prefsError = ref('')

const passwords = reactive({ old_password: '', new_password: '' })
const savingPassword = ref(false)
const passwordMessage = ref('')
const passwordError = ref('')

async function load() {
  try {
    const [me, settings] = await Promise.all([usersApi.me(), usersApi.settings()])
    profile.username = me.data.username || ''
    profile.email = me.data.email || ''
    originalEmail.value = profile.email
    prefs.reminder_hours_before = settings.data.reminder_hours_before
    prefs.theme = settings.data.theme
    applyTheme(settings.data.theme)
  } catch (e) {
    loadError.value = extractError(e)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  profileMessage.value = ''
  profileError.value = ''
  savingProfile.value = true
  try {
    const { data } = await usersApi.updateMe({ username: profile.username, email: profile.email })
    const emailChanged = data.email !== originalEmail.value
    profile.username = data.username
    profile.email = data.email
    originalEmail.value = data.email
    profileMessage.value = emailChanged
      ? 'Saved. We sent a verification link to your new email. You will need to verify it before your next log in.'
      : 'Profile saved.'
  } catch (e) {
    profileError.value = extractError(e)
  } finally {
    savingProfile.value = false
  }
}

async function savePrefs(change) {
  prefsMessage.value = ''
  prefsError.value = ''
  Object.assign(prefs, change)
  if (change.theme) applyTheme(change.theme)
  try {
    await usersApi.updateSettings(change)
    prefsMessage.value = 'Saved.'
  } catch (e) {
    prefsError.value = extractError(e)
  }
}

async function savePassword() {
  passwordMessage.value = ''
  passwordError.value = ''
  savingPassword.value = true
  try {
    const { data } = await usersApi.changePassword({ ...passwords })
    if (data.token) auth.setToken(data.token)
    passwords.old_password = ''
    passwords.new_password = ''
    passwordMessage.value = 'Password changed.'
  } catch (e) {
    passwordError.value = extractError(e)
  } finally {
    savingPassword.value = false
  }
}

function logout() {
  auth.clear()
  router.push({ name: 'login' })
}

onMounted(load)
</script>

<template>
  <main class="mx-auto max-w-2xl px-5 py-10">
    <h1 class="text-3xl font-semibold tracking-tight">Settings</h1>

    <p v-if="loadError" class="msg-error mt-8" role="alert">{{ loadError }}</p>
    <p v-else-if="loading" class="mt-8 text-ink/60">Loading settings</p>

    <div v-else class="mt-8">
      <section class="border-t border-ink/10 py-8">
        <h2 class="text-lg font-semibold">Profile</h2>
        <form class="mt-5 space-y-6" @submit.prevent="saveProfile">
          <div>
            <label class="label" for="username">Username</label>
            <input id="username" v-model.trim="profile.username" class="field" type="text" autocomplete="username" required />
          </div>
          <div>
            <label class="label" for="email">Email</label>
            <input id="email" v-model.trim="profile.email" class="field" type="email" autocomplete="email" required />
            <p class="mt-2 text-sm text-ink/50">Changing your email requires verifying the new address.</p>
          </div>
          <p v-if="profileMessage" class="msg-ok" role="status">{{ profileMessage }}</p>
          <p v-if="profileError" class="msg-error" role="alert">{{ profileError }}</p>
          <button class="btn" type="submit" :disabled="savingProfile">{{ savingProfile ? 'Saving' : 'Save profile' }}</button>
        </form>
      </section>

      <section class="border-t border-ink/10 py-8">
        <h2 class="text-lg font-semibold">Preferences</h2>
        <div class="mt-5 space-y-6">
          <div>
            <label class="label" for="reminders">Deadline reminder email</label>
            <select
              id="reminders"
              class="field"
              :value="prefs.reminder_hours_before"
              @change="savePrefs({ reminder_hours_before: Number($event.target.value) })"
            >
              <option v-for="r in REMINDERS" :key="r.value" :value="r.value">{{ r.label }}</option>
            </select>
          </div>
          <div>
            <p class="label">Theme</p>
            <div class="flex gap-6" role="group" aria-label="Theme">
              <button
                v-for="item in THEMES"
                :key="item.value"
                type="button"
                class="-mb-px border-b-2 pb-1 text-sm transition-colors"
                :class="prefs.theme === item.value ? 'border-accent font-medium text-ink' : 'border-transparent text-ink/60 hover:text-ink'"
                :aria-pressed="prefs.theme === item.value"
                @click="savePrefs({ theme: item.value })"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
          <p v-if="prefsMessage" class="msg-ok" role="status">{{ prefsMessage }}</p>
          <p v-if="prefsError" class="msg-error" role="alert">{{ prefsError }}</p>
        </div>
      </section>

      <section class="border-t border-ink/10 py-8">
        <h2 class="text-lg font-semibold">Password</h2>
        <form class="mt-5 space-y-6" @submit.prevent="savePassword">
          <div>
            <label class="label" for="old-password">Current password</label>
            <input id="old-password" v-model="passwords.old_password" class="field" type="password" autocomplete="current-password" required />
          </div>
          <div>
            <label class="label" for="new-password">New password</label>
            <input id="new-password" v-model="passwords.new_password" class="field" type="password" autocomplete="new-password" required />
          </div>
          <p v-if="passwordMessage" class="msg-ok" role="status">{{ passwordMessage }}</p>
          <p v-if="passwordError" class="msg-error" role="alert">{{ passwordError }}</p>
          <button class="btn" type="submit" :disabled="savingPassword">{{ savingPassword ? 'Saving' : 'Change password' }}</button>
        </form>
      </section>

      <section class="border-t border-ink/10 py-8">
        <h2 class="text-lg font-semibold">Session</h2>
        <p class="mt-2 text-sm text-ink/60">Logging out removes your access token from this browser.</p>
        <button class="link-btn mt-4" type="button" @click="logout">Log out</button>
      </section>
    </div>
  </main>
</template>
