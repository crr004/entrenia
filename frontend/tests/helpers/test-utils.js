import { vi } from 'vitest'

// Configuraciones globales comunes para tests.
export const globalOptions = {
  stubs: {
    RouterLink: {
      name: 'RouterLink',
      props: ['to'],
      template: '<a :href="to"><slot/></a>'
    },
    FontAwesomeIcon: {
      name: 'FontAwesomeIcon',
      template: '<span class="mock-icon"></span>'
    },
    Teleport: true
  },
  mocks: {
    $style: {}
  }
}

// Mock de las funciones de notificación.
export function setupNotificationMocks() {
  vi.mock('@/utils/notifications', () => ({
    notifySuccess: vi.fn(),
    notifyError: vi.fn(),
    notifyInfo: vi.fn()
  }))
}

// Mock del router.
export function setupRouterMock() {
  vi.mock('vue-router', () => ({
    useRouter: () => ({
      push: vi.fn()
    })
  }))
}

// Mock para FontAwesome.
export function setupFontAwesomeMock() {
  vi.mock('@fortawesome/vue-fontawesome', () => ({
    FontAwesomeIcon: {
      name: 'FontAwesomeIcon',
      template: '<span class="mock-icon"></span>'
    }
  }))
}

// Configuración completa de mocks comunes.
export function setupCommonMocks() {
  setupNotificationMocks()
  setupRouterMock()
  setupFontAwesomeMock()
}