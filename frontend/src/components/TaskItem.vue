<script setup>
import { ref, reactive, computed } from 'vue'
import { tasksApi, extractError } from '../services/api'
import {
  STATUSES,
  PRIORITIES,
  CATEGORIES,
  NEXT_STATUS,
  labelOf,
  toIso,
  toLocalInput,
  formatDate,
  daysLeftText
} from '../utils'

const props = defineProps({
  task: { type: Object, required: true }
})
const emit = defineEmits(['updated', 'deleted', 'error'])

const editing = ref(false)
const confirming = ref(false)
const busy = ref(false)
const initialDeadline = ref('')
const form = reactive({
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  category: 'Personal',
  deadline: ''
})

const isDone = computed(() => props.task.status === 'done')
const overdue = computed(() => props.task.days_left === 'Missed' && !isDone.value)
const statusLabel = computed(() => labelOf(STATUSES, props.task.status))

async function cycleStatus() {
  busy.value = true
  try {
    const { data } = await tasksApi.update(props.task.id, { status: NEXT_STATUS[props.task.status] })
    emit('updated', data)
  } catch (e) {
    emit('error', extractError(e))
  } finally {
    busy.value = false
  }
}

function startEdit() {
  initialDeadline.value = toLocalInput(props.task.deadline)
  Object.assign(form, {
    title: props.task.title,
    description: props.task.description || '',
    status: props.task.status,
    priority: props.task.priority,
    category: props.task.category,
    deadline: initialDeadline.value
  })
  confirming.value = false
  editing.value = true
}

async function save() {
  busy.value = true
  const payload = {
    title: form.title.trim(),
    description: form.description.trim(),
    status: form.status,
    priority: form.priority,
    category: form.category
  }
  if (form.deadline !== initialDeadline.value) {
    payload.deadline = toIso(form.deadline)
  }
  try {
    const { data } = await tasksApi.update(props.task.id, payload)
    emit('updated', data)
    editing.value = false
  } catch (e) {
    emit('error', extractError(e))
  } finally {
    busy.value = false
  }
}

async function remove() {
  busy.value = true
  try {
    await tasksApi.remove(props.task.id)
    emit('deleted')
  } catch (e) {
    emit('error', extractError(e))
    confirming.value = false
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <li class="border-b border-ink/10 py-4">
    <form v-if="editing" class="space-y-4" @submit.prevent="save">
      <div>
        <label class="label" :for="`t-${task.id}-title`">Title</label>
        <input :id="`t-${task.id}-title`" v-model="form.title" class="field" type="text" maxlength="255" required />
      </div>
      <div>
        <label class="label" :for="`t-${task.id}-desc`">Description</label>
        <textarea :id="`t-${task.id}-desc`" v-model="form.description" class="field" rows="2"></textarea>
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="label" :for="`t-${task.id}-status`">Status</label>
          <select :id="`t-${task.id}-status`" v-model="form.status" class="field">
            <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>
        <div>
          <label class="label" :for="`t-${task.id}-priority`">Priority</label>
          <select :id="`t-${task.id}-priority`" v-model="form.priority" class="field">
            <option v-for="p in PRIORITIES" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>
        <div>
          <label class="label" :for="`t-${task.id}-category`">Category</label>
          <select :id="`t-${task.id}-category`" v-model="form.category" class="field">
            <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>
        <div>
          <label class="label" :for="`t-${task.id}-deadline`">Deadline</label>
          <input :id="`t-${task.id}-deadline`" v-model="form.deadline" class="field" type="datetime-local" />
        </div>
      </div>
      <div class="flex items-center gap-5">
        <button class="btn" type="submit" :disabled="busy">Save</button>
        <button class="link-btn" type="button" @click="editing = false">Cancel</button>
      </div>
    </form>

    <div v-else class="flex items-start gap-4">
      <button
        type="button"
        class="mt-0.5 shrink-0 text-ink/45 transition-colors hover:text-accent disabled:opacity-50"
        :class="isDone ? '!text-accent' : ''"
        :disabled="busy"
        :aria-label="`${task.title}: ${statusLabel}. Select to change status`"
        :title="statusLabel"
        @click="cycleStatus"
      >
        <svg viewBox="0 0 20 20" class="h-5 w-5" aria-hidden="true">
          <circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="1.6" />
          <path v-if="task.status === 'in_progress'" d="M10 4a6 6 0 0 1 0 12z" fill="currentColor" />
          <template v-if="isDone">
            <circle cx="10" cy="10" r="8.8" fill="currentColor" />
            <path d="M6.2 10.3l2.6 2.6 5-5.6" fill="none" stroke="rgb(var(--canvas))" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          </template>
        </svg>
      </button>

      <div class="min-w-0 flex-1">
        <p class="break-words font-medium" :class="isDone ? 'text-ink/40 line-through' : ''">{{ task.title }}</p>
        <p v-if="task.description" class="mt-0.5 whitespace-pre-line break-words text-sm text-ink/60">{{ task.description }}</p>
        <p class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink/55">
          <span :class="task.priority === 'high' && !isDone ? 'font-medium text-danger' : ''">{{ labelOf(PRIORITIES, task.priority) }} priority</span>
          <span>{{ labelOf(CATEGORIES, task.category) }}</span>
          <span v-if="task.deadline">Due {{ formatDate(task.deadline) }}</span>
          <span v-if="task.deadline" :class="overdue ? 'font-medium text-danger' : ''">{{ daysLeftText(task.days_left) }}</span>
        </p>
      </div>

      <div class="flex shrink-0 items-center gap-4">
        <template v-if="confirming">
          <span class="text-sm text-ink/60">Delete this task?</span>
          <button type="button" class="text-sm font-medium text-danger underline-offset-4 hover:underline" :disabled="busy" @click="remove">Delete</button>
          <button type="button" class="link-btn" @click="confirming = false">Keep</button>
        </template>
        <template v-else>
          <button type="button" class="link-btn" @click="startEdit">Edit</button>
          <button type="button" class="link-btn hover:!text-danger" @click="confirming = true">Delete</button>
        </template>
      </div>
    </div>
  </li>
</template>
