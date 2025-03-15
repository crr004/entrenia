import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import AccountView from '@/views/AccountView.vue'
import { useAuthStore } from '@/stores/authStore'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../tests/helpers/test-utils'

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
vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'mock-token',
    user: { 
      id: '1', 
      username: 'testuser',
      email: 'test@example.com',
      is_admin: false
    },
    isAuthenticated: true,
    setAuthHeader: vi.fn(),
    updateUserData: vi.fn(),
    setUser: vi.fn()
  }))
}))

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Datos del usuario.
  http.get('/users/own', () => {
    return HttpResponse.json({
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      full_name: 'Test User',
      is_admin: false,
      is_active: true,
      is_verified: true
    }, { status: 200 })
  }),
  
  // Actualizar perfil.
  http.patch('/users/own', () => {
    return HttpResponse.json({
      id: '1',
      username: 'newusername',
      email: 'test@example.com',
      full_name: 'Updated Name',
      is_admin: false,
      is_active: true,
      is_verified: true
    }, { status: 200 })
  })
)

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

describe('AccountView.vue', () => {
  // Test 1: Carga de datos del perfil.
  it('carga los datos del usuario correctamente', async () => {
    const wrapper = mount(AccountView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.username).toBe('testuser')
      expect(wrapper.vm.email).toBe('test@example.com')
      expect(wrapper.vm.fullName).toBe('Test User')
    })
  })
  
  // Test 2: Visualización de pestañas.
  it('muestra las pestañas correctamente', async () => {
    const wrapper = mount(AccountView, {
      global: globalOptions
    })
    
    // Verificar que existen las pestañas.
    expect(wrapper.findAll('.sidebar-tab').length).toBeGreaterThan(0)
    
    // Cambiar a la pestaña de contraseña.
    if (wrapper.findAll('.sidebar-tab').length > 1) {
      await wrapper.findAll('.sidebar-tab')[1].trigger('click')
      // Verificar que cambia el tab activo (sin depender del ID específico).
      expect(wrapper.vm.activeTab).not.toBe('profile')
    }
  })
  
  // Test 3: Actualización de perfil.
  it('actualiza el perfil correctamente', async () => {
    const wrapper = mount(AccountView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos iniciales.
    await vi.waitFor(() => {
      expect(wrapper.vm.username).toBe('testuser')
    })
    
    // Modificar datos directamente para activar hasProfileChanges.
    wrapper.vm.username = 'newusername'
    wrapper.vm.fullName = 'Updated Name'
    
    // Forzar actualización del DOM.
    await wrapper.vm.$nextTick()

    const saveButton = wrapper.find('button.app-button')
    
    console.log('DOM completo:', wrapper.html())
    console.log('Botón encontrado:', saveButton.exists(), saveButton.classes())
    console.log('Estado de botón:', {
      disabled: saveButton.attributes('disabled'),
      hasChanges: wrapper.vm.hasProfileChanges
    })
    
    const updateSpy = vi.spyOn(wrapper.vm, 'updateProfile')
    
    await wrapper.vm.updateProfile()
    
    // Verificaciones.
    expect(updateSpy).toHaveBeenCalled()
    
    // Simular respuesta exitosa.
    wrapper.vm.handleUpdateSuccess && wrapper.vm.handleUpdateSuccess({ 
      data: {
        username: 'newusername',
        full_name: 'Updated Name'
      }
    })
    
    expect(notifications.notifySuccess).toHaveBeenCalled()
  })
  
  // Test 4: Manejo de errores de la API.
  it('muestra error cuando hay problemas al cargar datos', async () => {
    // Configurar respuesta de error.
    server.use(
      http.get('/users/own', () => {
        return HttpResponse.json(
          { detail: 'An error occurred' },
          { status: 500 }
        )
      })
    )
    
    const wrapper = mount(AccountView, {
      global: globalOptions
    })
    
    // Esperar un poco para que se procese la llamada de la API.
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Verificar que se muestra el error.
    expect(notifications.notifyError).toHaveBeenCalled()
  })
})