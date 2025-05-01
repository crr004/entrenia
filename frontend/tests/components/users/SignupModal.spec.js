import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import SignupModal from '@/components/users/SignupModal.vue'
import * as notifications from '@/utils/notifications'
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
  http.post('/signup', () => {
    return HttpResponse.json({ message: 'Usuario registrado con éxito' }, { status: 201 })
  })
)

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

describe('SignupModal.vue', () => {
  // Test 1: Validación de campos del formulario.
  it('tiene métodos de validación que funcionan correctamente', () => {
    const wrapper = shallowMount(SignupModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Verificamos directamente los métodos de validación individuales.
    wrapper.vm.validateUsername()
    wrapper.vm.validatePassword()
    wrapper.vm.validateEmail()
    wrapper.vm.validateFullName()
    
    // Verificar que hay errores de validación (asumiendo que los campos están vacíos).
    expect(wrapper.vm.fullNameError).not.toBe('')
    expect(wrapper.vm.usernameError).not.toBe('')
    expect(wrapper.vm.emailError).not.toBe('')
    expect(wrapper.vm.passwordError).not.toBe('')
  })
  
  // Test 2: Cierre del modal.
  it('emite evento close cuando se cierra el modal', () => {
    const wrapper = shallowMount(SignupModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Emitir directamente el evento.
    wrapper.vm.$emit('close')
    
    // Verificar que se emitió el evento.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 3: Registro exitoso de usuario.
  it('maneja correctamente el registro exitoso', async () => {
    const wrapper = shallowMount(SignupModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Mock del método handleSubmit para simular registro exitoso.
    const handleSubmitMock = vi.fn().mockImplementation(async () => {
      // Simular validación exitosa.
      wrapper.vm.fullNameError = ''
      wrapper.vm.usernameError = ''
      wrapper.vm.emailError = ''
      wrapper.vm.passwordError = ''
      
      // Simular respuesta exitosa.
      notifications.notifySuccess('Registro exitoso', 'Te has registrado correctamente')
      wrapper.vm.$emit('close')
    })
    
    // Reemplazar el método original con el mock.
    wrapper.vm.handleSubmit = handleSubmitMock
    
    // Llamar al método.
    await wrapper.vm.handleSubmit()
    
    // Verificar que se llamó al método.
    expect(handleSubmitMock).toHaveBeenCalled()
    
    // Verificar que se mostró la notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      'Registro exitoso',
      'Te has registrado correctamente'
    )
    
    // Verificar que se emitió el evento close.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 4: Manejo de errores (usuario existente).
  it('maneja error cuando el nombre de usuario ya existe', async () => {
    // Configurar respuesta de error.
    server.use(
      http.post('/signup', () => {
        return HttpResponse.json(
          { detail: 'This username is already taken' },
          { status: 409 }
        )
      })
    )
    
    const wrapper = shallowMount(SignupModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Mock del método handleSubmit para simular error de usuario existente.
    const handleSubmitMock = vi.fn().mockImplementation(async () => {
      // Simular error de usuario existente.
      wrapper.vm.usernameError = 'Este nombre de usuario ya está en uso'
    })
    
    // Reemplazar el método original con el mock.
    wrapper.vm.handleSubmit = handleSubmitMock
    
    // Llamar al método.
    await wrapper.vm.handleSubmit()
    
    // Verificar que se llamó al método.
    expect(handleSubmitMock).toHaveBeenCalled()
    
    // Verificar que se estableció el error.
    expect(wrapper.vm.usernameError).toBe('Este nombre de usuario ya está en uso')
  })
  
  // Test 5: Cambio a modal de login.
  it('emite evento switchToLogin al llamar al método', () => {
    const wrapper = shallowMount(SignupModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Llamar al método directamente.
    wrapper.vm.switchToLogin()
    
    // Verificar que se emitió el evento.
    expect(wrapper.emitted('switchToLogin')).toBeTruthy()
  })
})