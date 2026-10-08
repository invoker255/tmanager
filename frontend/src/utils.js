export const STATUSES = [
  { value: 'todo', label: 'To do' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'done', label: 'Done' }
]

export const PRIORITIES = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' }
]

export const CATEGORIES = [
  { value: 'Personal', label: 'Personal' },
  { value: 'Work', label: 'Work' }
]

export const ORDERINGS = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: 'deadline', label: 'Deadline, soonest' },
  { value: '-deadline', label: 'Deadline, latest' }
]

export const REMINDERS = [
  { value: 12, label: '12 hours before a deadline' },
  { value: 24, label: '24 hours before a deadline' },
  { value: 72, label: '72 hours before a deadline' },
  { value: 0, label: 'Reminders off' }
]

export const NEXT_STATUS = {
  todo: 'in_progress',
  in_progress: 'done',
  done: 'todo'
}

export function labelOf(list, value) {
  return list.find((item) => item.value === value)?.label || value
}

export function toIso(local) {
  return local ? new Date(local).toISOString() : null
}

export function toLocalInput(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function formatDate(iso) {
  return new Date(iso).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function daysLeftText(value) {
  if (!value) return ''
  if (value === 'Missed') return 'overdue'
  const match = value.match(/(\d+)/)
  if (!match) return value
  const n = Number(match[1])
  if (n === 0) return 'less than a day left'
  return `${n} ${n === 1 ? 'day' : 'days'} left`
}
