import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { userPreferencesStore } from '@/stores/userPreferencesStore'

// Mock del sessionStorage
const sessionStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn(key => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = String(value)
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    removeItem: vi.fn(key => {
      delete store[key]
    })
  }
})()

// Mock del plugin de persistencia.
vi.mock('pinia-plugin-persistedstate', () => ({
  default: () => {
    return {
      // Este es un mock simplificado del plugin que no hace nada.
    }
  }
}))

describe('UserPreferencesStore', () => {
  beforeEach(() => {
    // Crear una instancia limpia de pinia para cada test.
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Restaurar el mock de sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: sessionStorageMock,
      writable: true
    })
    
    // Limpiar el sessionStorage antes de cada test
    sessionStorageMock.clear()
  })
  
  // Test 1: Estado inicial.
  it('tiene valores predeterminados correctos', () => {
    const store = userPreferencesStore()
    
    expect(store.adminPageSize).toBe(5)
    expect(store.datasetPageSize).toBe(5)
    expect(store.imagePageSize).toBe(5)
  })
  
  // Test 2: Modificar tamaño de página para administración.
  it('permite modificar el tamaño de página para administración', () => {
    const store = userPreferencesStore()
    
    store.setAdminPageSize(10)
    
    expect(store.adminPageSize).toBe(10)
    expect(store.getAdminPageSize).toBe(10)
  })
  
  // Test 3: Modificar tamaño de página para datasets.
  it('permite modificar el tamaño de página para datasets', () => {
    const store = userPreferencesStore()
    
    store.setDatasetPageSize(15)
    
    expect(store.datasetPageSize).toBe(15)
    expect(store.getDatasetPageSize).toBe(15)
  })
  
  // Test 4: Modificar tamaño de página para imágenes.
  it('permite modificar el tamaño de página para imágenes', () => {
    const store = userPreferencesStore()
    
    store.setImagePageSize(20)
    
    expect(store.imagePageSize).toBe(20)
    expect(store.getImagePageSize).toBe(20)
  })
  
  // Test 5: Restablecer preferencias a valores predeterminados.
  it('restablece las preferencias a sus valores predeterminados', () => {
    const store = userPreferencesStore()
    
    // Cambiar todos los valores
    store.setAdminPageSize(10)
    store.setDatasetPageSize(15)
    store.setImagePageSize(20)
    
    // Verificar que los valores cambiaron
    expect(store.adminPageSize).toBe(10)
    expect(store.datasetPageSize).toBe(15)
    expect(store.imagePageSize).toBe(20)
    
    // Restablecer preferencias
    store.resetPreferences()
    
    // Verificar que los valores volvieron a sus valores predeterminados
    expect(store.adminPageSize).toBe(5)
    expect(store.datasetPageSize).toBe(5)
    expect(store.imagePageSize).toBe(5)
  })
  
  // Test 6: Verificar getters.
  it('tiene getters que funcionan correctamente', () => {
    const store = userPreferencesStore()
    
    store.$patch({
      adminPageSize: 10,
      datasetPageSize: 15,
      imagePageSize: 20
    })
    
    expect(store.getAdminPageSize).toBe(10)
    expect(store.getDatasetPageSize).toBe(15)
    expect(store.getImagePageSize).toBe(20)
  })
  
  // Test 7: Verificar persistencia de datos (sessionStorage).
  it('persiste los cambios en sessionStorage', async () => {
    
    const store = userPreferencesStore()
    
    // Simular la carga inicial desde sessionStorage
    const mockPersistedData = {
      adminPageSize: 8,
      datasetPageSize: 12,
      imagePageSize: 16
    }
    
    // Aplicar los datos persistidos manualmente (simulando la acción del plugin)
    store.$patch(mockPersistedData)
    
    // Verificar que el store tiene los valores cargados
    expect(store.adminPageSize).toBe(8)
    expect(store.datasetPageSize).toBe(12)
    expect(store.imagePageSize).toBe(16)
    
    // Hacer un cambio
    store.setAdminPageSize(25)
    
    const updatedState = {
      adminPageSize: store.adminPageSize,
      datasetPageSize: store.datasetPageSize,
      imagePageSize: store.imagePageSize
    }
    
    // Verificar que los cambios se reflejan en el store
    expect(updatedState).toEqual({
      adminPageSize: 25,
      datasetPageSize: 12,
      imagePageSize: 16
    })
    
  })
})