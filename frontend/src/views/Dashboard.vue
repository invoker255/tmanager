<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import TaskItem from '../components/TaskItem.vue'
import { tasksApi, extractError } from '../services/api'
import { STATUSES, PRIORITIES, CATEGORIES, ORDERINGS, toIso } from '../utils'

const PAGE_SIZE = 10

const tasks = ref([])
const total = ref(0)
const page = ref(1)
const hasNext = ref(false)
const hasPrev = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showMore = ref(false)

const filters = reactive({ search: '', status: '', priority: '', category: '', ordering: '-created_at' })

const emptyForm = () => ({
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  category: 'Personal',
  deadline: ''
})
const form = reactive(emptyForm())

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))
const filtered = computed(() => Boolean(filters.search || filters.status || filters.priority || filters.category))

async function load() {
  loading.value = true
  const params = { page: page.value, ordering: filters.ordering }
  if (filters.search) params.search = filters.search
  if (filters.status) params.status = filters.status
  if (filters.priority) params.priority = filters.priority
  if (filters.category) params.category = filters.category
  try {
    const { data } = await tasksApi.list(params)
    const results = Array.isArray(data) ? data : data.results || []
    tasks.value = results
    total.value = Array.isArray(data) ? results.length : data.count ?? results.length
    hasNext.value = Array.isArray(data) ? false : Boolean(data.next)
    hasPrev.value = Array.isArray(data) ? false : Boolean(data.previous)
  } catch (e) {
    if (e.response?.status === 404 && page.value > 1) {
      page.value -= 1
      await load()
      return
    }
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}

let searchTimer = null
watch(
  () => filters.search,
  () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      page.value = 1
      load()
    }, 350)
  }
)
watch(
  () => [filters.status, filters.priority, filters.category, filters.ordering],
  () => {
    page.value = 1
    load()
  }
)

async function addTask() {
  saving.value = true
  error.value = ''
  try {
    await tasksApi.create({
      title: form.title.trim(),
      description: form.description.trim(),
      status: form.status,
      priority: form.priority,
      category: form.category,
      deadline: toIso(form.deadline)
    })
    Object.assign(form, emptyForm())
    showMore.value = false
    page.value = 1
    await load()
  } catch (e) {
    error.value = extractError(e)
  } finally {
    saving.value = false
  }
}

function onUpdated(data) {
  error.value = ''
  const index = tasks.value.findIndex((t) => t.id === data.id)
  if (index === -1) return
  tasks.value[index] = data
  if (filters.status && data.status !== filters.status) load()
}

function onDeleted() {
  error.value = ''
  load()
}

function go(delta) {
  page.value += delta
  load()
}

function resetFilters() {
  filters.search = ''
  filters.status = ''
  filters.priority = ''
  filters.category = ''
}

onMounted(load)
</script>

<template>
  <main class="mx-auto max-w-2xl px-5 py-10">
    <div class="flex items-baseline justify-between">
      <h1 class="text-3xl font-semibold tracking-tight">Your tasks</h1>
      <p class="text-sm text-ink/55">{{ total }} {{ total === 1 ? 'task' : 'tasks' }}</p>
    </div>

    <form class="mt-8" @submit.prevent="addTask">
      <div class="flex items-end gap-4">
        <div class="flex-1">
          <label class="sr-only" for="new-title">Task title</label>
          <input id="new-title" v-model="form.title" class="field text-lg" type="text" maxlength="255" placeholder="Add a task" required />
        </div>
        <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Adding' : 'Add' }}</button>
      </div>
      <button type="button" class="link-btn mt-3" :aria-expanded="showMore" @click="showMore = !showMore">
        {{ showMore ? 'Fewer options' : 'More options' }}
      </button>
      <div v-if="showMore" class="mt-4 grid gap-4 sm:grid-cols-2">
        <div class="sm:col-span-2">
          <label class="label" for="new-description">Description</label>
          <textarea id="new-description" v-model="form.description" class="field" rows="2"></textarea>
        </div>
        <div>
          <label class="label" for="new-deadline">Deadline</label>
          <input id="new-deadline" v-model="form.deadline" class="field" type="datetime-local" />
        </div>
        <div>
          <label class="label" for="new-status">Status</label>
          <select id="new-status" v-model="form.status" class="field">
            <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <div>
          <label class="label" for="new-priority">Priority</label>
          <select id="new-priority" v-model="form.priority" class="field">
            <option v-for="p in PRIORITIES" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>
        <div>
          <label class="label" for="new-category">Category</label>
          <select id="new-category" v-model="form.category" class="field">
            <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>
      </div>
    </form>

    <div class="mt-12 flex flex-wrap items-end justify-between gap-x-6 border-b border-ink/15">
      <div class="flex gap-6" role="group" aria-label="Filter by status">
        <button
          type="button"
          class="-mb-px border-b-2 pb-3 text-sm transition-colors"
          :class="filters.status === '' ? 'border-accent font-medium text-ink' : 'border-transparent text-ink/60 hover:text-ink'"
          @click="filters.status = ''"
        >
          All
        </button>
        <button
          v-for="s in STATUSES"
          :key="s.value"
          type="button"
          class="-mb-px border-b-2 pb-3 text-sm transition-colors"
          :class="filters.status === s.value ? 'border-accent font-medium text-ink' : 'border-transparent text-ink/60 hover:text-ink'"
          @click="filters.status = s.value"
        >
          {{ s.label }}
        </button>
      </div>
      <div class="w-40 pb-1">
        <label class="sr-only" for="search">Search tasks</label>
        <input id="search" v-model="filters.search" class="field !border-b-0 !py-1 text-sm" type="search" placeholder="Search" />
      </div>
    </div>

    <div class="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
      <select v-model="filters.priority" class="field !w-auto !border-b-0 !py-1" aria-label="Filter by priority">
        <option value="">Any priority</option>
        <option v-for="p in PRIORITIES" :key="p.value" :value="p.value">{{ p.label }} priority</option>
      </select>
      <select v-model="filters.category" class="field !w-auto !border-b-0 !py-1" aria-label="Filter by category">
        <option value="">Any category</option>
        <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
      </select>
      <select v-model="filters.ordering" class="field !w-auto !border-b-0 !py-1" aria-label="Sort tasks">
        <option v-for="o in ORDERINGS" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
    </div>

    <p v-if="error" class="msg-error mt-6" role="alert">{{ error }}</p>

    <p v-if="loading && !tasks.length" class="mt-10 text-ink/60">Loading tasks</p>

    <div v-else-if="!tasks.length" class="mt-10 text-ink/60">
      <template v-if="filtered">
        No tasks match these filters.
        <button type="button" class="font-medium text-accent underline-offset-4 hover:underline" @click="resetFilters">Clear filters</button>
      </template>
      <template v-else>No tasks yet. Type a title above and press Add.</template>
    </div>

    <ul v-else class="mt-2 transition-opacity" :class="loading ? 'opacity-50' : ''">
      <TaskItem v-for="task in tasks" :key="task.id" :task="task" @updated="onUpdated" @deleted="onDeleted" @error="error = $event" />
    </ul>

    <nav v-if="hasNext || hasPrev" class="mt-8 flex items-center justify-between text-sm" aria-label="Pagination">
      <button class="link-btn" type="button" :disabled="!hasPrev || loading" @click="go(-1)">Previous</button>
      <span class="text-ink/55">Page {{ page }} of {{ pageCount }}</span>
      <button class="link-btn" type="button" :disabled="!hasNext || loading" @click="go(1)">Next</button>
    </nav>
  </main>
</template>
