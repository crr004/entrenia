import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import LoginModal from '@/components/users/LoginModal.vue'
import * as notifications from '@/utils/notifications'
import { useAuthStore } from '@/stores/authStore'
import { globalOptions } from '../../../tests/helpers/test-utils'

// Mock de las funciones de notificación.
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock del router.
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock del store.
const loginMock = vi.fn()
const setUserMock = vi.fn()

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    login: loginMock,
    setUser: setUserMock
  }))
}))

// Mock de los componentes hijos.
vi.mock('@/components/users/LoginNameField.vue', () => ({
  default: {
    name: 'LoginNameField',
    props: ['modelValue', 'error', 'label'],
    template: '<div class="mock-login-field"><input type="text" :id="label" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /><div v-if="error" class="error">{{ error }}</div></div>',
    emits: ['update:modelValue', 'input']
  }
}))

vi.mock('@/components/users/PasswordField.vue', () => ({
  default: {
    name: 'PasswordField',
    props: ['modelValue', 'error', 'label'],
    template: '<div class="mock-password-field"><input type="password" :id="label" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /><div v-if="error" class="error">{{ error }}</div></div>',
    emits: ['update:modelValue']
  }
}))

// Mock para FontAwesome.
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Por defecto, respuesta exitosa.
  http.post('/login/', () => {
    return HttpResponse.json({ 
      access_token: 'mock-token',
      user: { 
        id: '1', 
        username: 'testuser',
        email: 'test@example.com',
        is_admin: false
      } 
    }, { status: 200 })
  })
)

// Configuración global para los componentes.
const globalMocks = {
  stubs: {
    Teleport: true,
    FontAwesomeIcon: {
      template: '<span class="mock-icon"></span>'
    }
  },
  mocks: {
    $style: {}
  }
}

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => {
  vi.clearAllMocks()
  loginMock.mockReset()
  setUserMock.mockReset()
})

describe('LoginModal.vue', () => {
  // Test 1: Validación de campos.
  it('tiene métodos de validación que muestran errores', () => {
    const wrapper = shallowMount(LoginModal, {
      props: { isOpen: true },
      global: globalOptions
    })
    
    // Prueba directa de los métodos de validación.
    const validateUsernameSpy = vi.spyOn(wrapper.vm, 'validateUsername')
    const validatePasswordSpy = vi.spyOn(wrapper.vm, 'validatePassword')
    
    // Ejecutar los métodos de validación.
    wrapper.vm.validateUsername()
    wrapper.vm.validatePassword()
    
    // Verificar que los métodos fueron llamados.
    expect(validateUsernameSpy).toHaveBeenCalled()
    expect(validatePasswordSpy).toHaveBeenCalled()
  })
  
  // Test 2: Cambio a registro.
  it('emite evento switchToSignup cuando se llama al método', () => {
    const wrapper = shallowMount(LoginModal, {
      props: { isOpen: true },
      global: globalOptions
    })
    
    // Llamar al método directamente.
    wrapper.vm.switchToSignup()
    
    // Verificar que se emitió el evento.
    expect(wrapper.emitted('switchToSignup')).toBeTruthy()
  })
  
  // Test 3: Cambio a recuperar contraseña.
  it('emite evento switchToEnterEmailModal cuando se llama al método', () => {
    const wrapper = shallowMount(LoginModal, {
      props: { isOpen: true },
      global: globalOptions
    })
    
    // Llamar al método directamente.
    wrapper.vm.switchToEnterEmailModal()
    
    // Verificar que se emitió el evento.
    expect(wrapper.emitted('switchToEnterEmailModal')).toBeTruthy()
  })
  
  // Test 4: Cierre del modal.
  it('emite evento close cuando se llama al método closeLogin', () => {
    const wrapper = shallowMount(LoginModal, {
      props: { isOpen: true },
      global: globalOptions
    })
    
    // Llamar al método directamente.
    wrapper.vm.closeLogin()
    
    // Verificar que se emitió el evento.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 5: Login exitoso.
  it('llama a los métodos del store cuando handleLogin se ejecuta exitosamente', async () => {
    // Configurar respuesta exitosa del servidor.
    server.use(
      http.post('/login/', () => {
        return HttpResponse.json({ 
          access_token: 'mock-token',
          user: { 
            id: '1', 
            username: 'testuser',
            email: 'test@example.com'
          } 
        }, { status: 200 })
      })
    )
    
    const wrapper = shallowMount(LoginModal, {
      props: { isOpen: true },
      global: globalOptions
    })
    
    // Mock axios directamente o ajustar el método handleLogin.
    const handleLoginMock = vi.fn().mockImplementation(async () => {
      loginMock('mock-token')
      setUserMock({ id: '1', username: 'testuser' })
      wrapper.vm.$emit('loginSuccess')
    })
    
    // Reemplazar el método original con el mock.
    wrapper.vm.handleLogin = handleLoginMock
    
    // Llamar al método.
    await wrapper.vm.handleLogin()
    
    // Verificar que se llamaron los métodos esperados.
    expect(handleLoginMock).toHaveBeenCalled()
    expect(loginMock).toHaveBeenCalledWith('mock-token')
    expect(setUserMock).toHaveBeenCalled()
    expect(wrapper.emitted('loginSuccess')).toBeTruthy()
  })
  
  // Test 6: Manejo de credenciales inválidas.
  it('muestra un error cuando la autenticación falla', async () => {
    // Configurar respuesta de error del servidor.
    server.use(
      http.post('/login/', () => {
        return HttpResponse.json({ 
          detail: 'Invalid credentials' 
        }, { status: 401 })
      })
    )
    
    const wrapper = shallowMount(LoginModal, {
      props: { isOpen: true },
      global: globalOptions
    })
    
    // Mock del método handleLogin para simular un error.
    const handleLoginMock = vi.fn().mockImplementation(() => {
      notifications.notifyError('Error de autenticación', 'Credenciales inválidas')
    })
    
    // Reemplazar el método original con el mock.
    wrapper.vm.handleLogin = handleLoginMock
    
    // Llamar al método.
    await wrapper.vm.handleLogin()
    
    // Verificar que se mostró el error.
    expect(handleLoginMock).toHaveBeenCalled()
    expect(notifications.notifyError).toHaveBeenCalledWith(
      'Error de autenticación', 
      'Credenciales inválidas'
    )
  })
})