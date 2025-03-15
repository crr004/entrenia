import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import HomeContent from '@/components/general/HomeContent.vue'
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

// Mock de window.history.replaceState.
const originalReplaceState = window.history.replaceState
beforeEach(() => {
  window.history.replaceState = vi.fn()
})
afterEach(() => {
  window.history.replaceState = originalReplaceState
  vi.clearAllMocks()
})

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Respuesta exitosa por defecto.
  http.post('/signup/account-verification', () => {
    return HttpResponse.json({}, { status: 200 })
  })
)

// Iniciar el servidor antes de los tests.
beforeEach(() => server.listen())
// Resetear handlers entre tests.
afterEach(() => server.resetHandlers())
// Cerrar el servidor después de los tests.
afterEach(() => server.close())

describe('HomeContent.vue - Sin token', () => {
  // Test 1: Renderizado sin token.
  it('renderiza correctamente sin token en la URL', async () => {
    // Simular que no hay token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue(null)
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Verificar que el componente se renderiza correctamente.
    expect(wrapper.find('h1').text()).toBe('EntrenIA')
    expect(wrapper.find('p').text()).toBe('Texto de inicio.')
    
    // Verificar que no se llama a ninguna notificación.
    expect(notifications.notifySuccess).not.toHaveBeenCalled()
    expect(notifications.notifyError).not.toHaveBeenCalled()
    expect(notifications.notifyInfo).not.toHaveBeenCalled()
  })
})

describe('HomeContent.vue - Con token válido', () => {
  // Test 2: Verificación exitosa con token válido.
  it('verifica la cuenta con éxito cuando hay un token válido', async () => {
    // Simular token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue('valid-token')
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Esperar a que se complete el proceso asíncrono.
    await vi.waitFor(() => {
      expect(notifications.notifySuccess).toHaveBeenCalledWith(
        "Cuenta verificada", 
        "Tu cuenta ha sido verificada con éxito. Ahora puedes iniciar sesión."
      )
    })
    
    // Verificar que se limpió el token de la URL.
    expect(window.history.replaceState).toHaveBeenCalled()
  })
})

describe('HomeContent.vue - Manejo de errores API', () => {
  // Test 3: Error 400 - token inválido.
  it('maneja error 400 - token inválido o expirado', async () => {
    // Configurar el servidor para devolver error 400.
    server.use(
      http.post('/signup/account-verification', () => {
        return HttpResponse.json(
          { detail: 'Token inválido o expirado' },
          { status: 400 }
        )
      })
    )
    
    // Simular token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue('invalid-token')
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Esperar a que se complete el proceso asíncrono.
    await vi.waitFor(() => {
      expect(notifications.notifyError).toHaveBeenCalledWith(
        "Error de verificación", 
        "El token de verificación no es válido o ha expirado."
      )
    })
    
    // Verificar que se limpió el token de la URL.
    expect(window.history.replaceState).toHaveBeenCalled()
  })
  
  // Test 4: Error 404 - cuenta no encontrada.
  it('maneja error 404 - cuenta no encontrada', async () => {
    // Configurar el servidor para devolver error 404.
    server.use(
      http.post('/signup/account-verification', () => {
        return HttpResponse.json(
          { detail: 'Cuenta no encontrada' },
          { status: 404 }
        )
      })
    )
    
    // Simular token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue('nonexistent-token')
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Esperar a que se complete el proceso asíncrono.
    await vi.waitFor(() => {
      expect(notifications.notifyError).toHaveBeenCalledWith(
        "Error de verificación", 
        "No se encontró ninguna cuenta asociada."
      )
    })
  })
  
  // Test 5: Error 409 - ya verificado.
  it('maneja error 409 - cuenta ya verificada', async () => {
    // Configurar el servidor para devolver error 409.
    server.use(
      http.post('/signup/account-verification', () => {
        return HttpResponse.json(
          { detail: 'Cuenta ya verificada' },
          { status: 409 }
        )
      })
    )
    
    // Simular token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue('already-verified-token')
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Esperar a que se complete el proceso asíncrono.
    await vi.waitFor(() => {
      expect(notifications.notifyInfo).toHaveBeenCalledWith(
        "Cuenta verificada anteriormente", 
        "Tu identidad ya ha sido verificada anteriormente. Puedes iniciar sesión."
      )
    })
  })
  
  // Test 6: Error 500 - error de servidor.
  it('maneja errores desconocidos', async () => {
    // Configurar el servidor para devolver error 500.
    server.use(
      http.post('/signup/account-verification', () => {
        return HttpResponse.json(
          { detail: 'Error interno del servidor' },
          { status: 500 }
        )
      })
    )
    
    // Simular token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue('server-error-token')
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Esperar a que se complete el proceso asíncrono.
    await vi.waitFor(() => {
      expect(notifications.notifyError).toHaveBeenCalledWith(
        "Error de verificación", 
        "Ha ocurrido un error de verificación."
      )
    })
  })
  
  // Test 7: Error de red.
  it('maneja errores de conexión', async () => {
    // Configurar el servidor para simular un error de red.
    server.use(
      http.post('/signup/account-verification', () => {
        return HttpResponse.error()
      })
    )
    
    // Simular token en la URL.
    vi.spyOn(URLSearchParams.prototype, 'get').mockReturnValue('network-error-token')
    
    const wrapper = mount(HomeContent, {
      global: globalOptions
    })
    
    // Esperar a que se complete el proceso asíncrono.
    await vi.waitFor(() => {
      expect(notifications.notifyError).toHaveBeenCalledWith(
        "Error de conexión", 
        "No se pudo conectar con el servidor. Verifica tu conexión a internet."
      )
    })
  })
})