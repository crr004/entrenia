import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/authStore'
import axios from 'axios'

// Mock de axios.
vi.mock('axios', () => ({
  default: {
    defaults: {
      headers: {
        common: {}
      }
    }
  }
}))

// Mock del plugin de persistencia.
vi.mock('pinia-plugin-persistedstate', () => ({
  default: () => {
    return {
      // Este es un mock simplificado del plugin que no hace nada.
    }
  }
}))

describe('AuthStore', () => {
  beforeEach(() => {
    // Crear una instancia limpia de pinia para cada test.
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Limpiar los headers de axios entre tests.
    axios.defaults.headers.common = {}
  })
  
  // Test 1: Establecimiento de token.
  it('establece correctamente el token', () => {
    const store = useAuthStore()
    store.setToken('test-token')
    
    expect(store.token).toBe('test-token')
    expect(store.isAuthenticated).toBe(true)
    expect(axios.defaults.headers.common['Authorization']).toBe('Bearer test-token')
  })
  
  // Test 2: Establecimiento de datos de usuario.
  it('establece los datos del usuario', () => {
    const store = useAuthStore()
    const userData = { id: '1', username: 'test', email: 'test@example.com' }
    
    store.setUser(userData)
    
    expect(store.user).toEqual(userData)
  })
  
  // Test 3: Funcionalidad de logout.
  it('realiza correctamente el logout', () => {
    const store = useAuthStore()
    
    // Primero configurar un estado autenticado.
    store.setToken('test-token')
    store.setUser({ id: '1', username: 'test' })
    expect(store.isAuthenticated).toBe(true)
    
    // Luego hacer logout.
    store.logout()
    
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(axios.defaults.headers.common['Authorization']).toBeUndefined()
  })
  
  // Test 4: Establecimiento de headers de autenticación.
  it('establece el header de autorización con setAuthHeader', () => {
    const store = useAuthStore()
    
    // Establecer manualmente el token en el estado.
    store.$patch({
      token: 'test-token',
      isAuthenticated: true
    })
    
    // Llamar al método que queremos probar.
    store.setAuthHeader()
    
    // Verificar que se estableció el header de autorización.
    expect(axios.defaults.headers.common['Authorization']).toBe('Bearer test-token')
  })
  
  // Test 5: Inicialización desde estado previo.
  it('inicializa la autenticación desde el estado actual', () => {
    const store = useAuthStore()
    
    // Establecer manualmente el token en el estado.
    store.$patch({
      token: 'stored-token',
      user: { id: '1', username: 'stored-user' },
      isAuthenticated: true
    })
    
    // Llamar al método que queremos probar.
    store.initializeAuth()
    
    // Verificar que se estableció el header de autorización.
    expect(axios.defaults.headers.common['Authorization']).toBe('Bearer stored-token')
  })
  
  // Test 6: Actualización de datos de usuario.
  it('actualiza los datos de usuario y persiste en localStorage', () => {
    // Mock de localStorage.
    const localStorageMock = {
      getItem: vi.fn().mockReturnValue(JSON.stringify({
        token: 'existing-token',
        user: { id: '1', username: 'old-username' }
      })),
      setItem: vi.fn()
    }
    
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    })
    
    const store = useAuthStore()
    const updatedUserData = { 
      id: '1', 
      username: 'new-username', 
      email: 'new@example.com' 
    }
    
    store.updateUserData(updatedUserData)
    
    // Verificar que el estado del store se actualizó.
    expect(store.user).toEqual(updatedUserData)
    
    // Verificar que se llamó a localStorage.setItem con los datos actualizados.
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'auth',
      expect.stringContaining('new-username')
    )
  })
})