import { createDiscreteApi } from 'naive-ui'

const { notification } = createDiscreteApi(['notification'])

export function notify(title, content, type = 'info') {
  notification[type]({
    title,
    content,
    duration: 3000,
    keepAliveOnHover: true
  })
}

export const notifySuccess = (title, content) => notify(title, content, 'success')
export const notifyError = (title, content) => notify(title, content, 'error')
export const notifyWarning = (title, content) => notify(title, content, 'warning')
export const notifyInfo = (title, content) => notify(title, content, 'info')