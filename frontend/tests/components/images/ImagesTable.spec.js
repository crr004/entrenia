import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ImagesTable from '@/components/images/ImagesTable.vue'
import * as notifications from '@/utils/notifications'
import axios from 'axios'

// Mock de las funciones de notificación
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock de axios
vi.mock('axios')

// Mock del router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock para FontAwesome
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

// Mock para componentes utilizados por ImagesTable
vi.mock('@/components/utils/ActionMenu.vue', () => ({
  default: {
    name: 'ActionMenu',
    props: ['item', 'itemId', 'position', 'actions'],
    template: '<div class="mock-action-menu"></div>',
    emits: ['edit', 'delete', 'close']
  }
}))

vi.mock('@/components/utils/ConfirmationModal.vue', () => ({
  default: {
    name: 'ConfirmationModal',
    props: ['isOpen', 'title', 'message', 'confirmText', 'cancelText'],
    template: '<div class="mock-confirmation-modal"></div>',
    emits: ['confirm', 'cancel']
  }
}))

vi.mock('@/components/utils/SortIcon.vue', () => ({
  default: {
    name: 'SortIcon',
    props: ['fieldName', 'currentSort', 'currentOrder'],
    template: '<span class="mock-sort-icon"></span>'
  }
}))

vi.mock('@/components/images/EditImageModal.vue', () => ({
  default: {
    name: 'EditImageModal',
    props: ['isOpen', 'image'],
    template: '<div class="mock-edit-image-modal"></div>',
    emits: ['close', 'image-updated']
  }
}))

// Mock para el store de Auth
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    token: 'fake-token',
    setAuthHeader: vi.fn(),
    logout: vi.fn()
  })
}))

// Mock para el store de preferencias
vi.mock('@/stores/userPreferencesStore', () => ({
  userPreferencesStore: () => ({
    imagePageSize: 10,
    setImagePageSize: vi.fn()
  })
}))

describe('ImagesTable.vue', () => {
  // Datos de prueba
  const testDatasetId = '123'
  const mockImagesResponse = {
    images: [
      { 
        id: '1', 
        name: 'imagen1.jpg', 
        thumbnail: 'base64data1', 
        label: 'gato', 
        created_at: '2023-04-15T10:30:00Z' 
      },
      { 
        id: '2', 
        name: 'imagen2.jpg', 
        thumbnail: 'base64data2', 
        label: 'perro', 
        created_at: '2023-04-16T14:20:00Z' 
      },
      { 
        id: '3', 
        name: 'imagen3.jpg', 
        thumbnail: 'base64data3', 
        label: null, 
        created_at: '2023-04-17T09:15:00Z' 
      }
    ],
    count: 3
  }

  // Configurar mocks antes de cada test
  beforeEach(() => {
    // Crear una instancia limpia de pinia
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock de axios.get para obtener imágenes
    axios.get = vi.fn().mockResolvedValue({
      data: mockImagesResponse
    })
    
    // Mock de axios.delete para eliminar imágenes
    axios.delete = vi.fn().mockResolvedValue({
      data: { success: true }
    })
    
    // Mock de window.scrollTo
    window.scrollTo = vi.fn()
    
    // Limpiar mocks
    vi.clearAllMocks()
    
    // Mock para el DOM para eventos de scroll
    Object.defineProperty(window, 'scrollY', {
      writable: true,
      value: 0
    })
  })

  // Test 1: Carga de imágenes
  it('carga imágenes correctamente al montar el componente', async () => {
    const wrapper = mount(ImagesTable, {
      props: {
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          FontAwesomeIcon: true,
          ActionMenu: true,
          ConfirmationModal: true,
          EditImageModal: true,
          SortIcon: true
        }
      }
    })
    
    await flushPromises()
    
    // Verificar que se llamó a axios.get con la URL correcta
    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining(`/images/dataset/${testDatasetId}`))
    
    // Verificar que las imágenes se cargaron correctamente
    expect(wrapper.vm.images.length).toBe(3)
    expect(wrapper.vm.totalImages).toBe(3)
  })

  // Test 2: Visualización de la tabla
  it('muestra la tabla de imágenes cuando hay datos', async () => {
    const wrapper = mount(ImagesTable, {
      props: {
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          FontAwesomeIcon: true,
          ActionMenu: true,
          ConfirmationModal: true,
          EditImageModal: true,
          SortIcon: true
        }
      }
    })
    
    await flushPromises()
    
    // Verificar que la tabla está visible
    expect(wrapper.find('table.images-table').exists()).toBe(true)
    
    // Verificar que se muestran las filas de imágenes
    const rows = wrapper.findAll('.image-row')
    expect(rows.length).toBe(3)
  })

  // Test 3: Búsqueda de imágenes
  it('realiza búsqueda de imágenes correctamente', async () => {
    const wrapper = mount(ImagesTable, {
      props: {
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          FontAwesomeIcon: true,
          ActionMenu: true,
          ConfirmationModal: true,
          EditImageModal: true,
          SortIcon: true
        }
      }
    })
    
    await flushPromises()
    
    // Limpiar el mock para preparar la siguiente llamada
    axios.get.mockClear()
    
    // Establecer directamente el valor de búsqueda en el componente
    wrapper.vm.searchQuery = 'gato'
    
    await wrapper.vm.fetchImages()
    
    await flushPromises()
    
    // Verificar que se llamó a axios.get con el término de búsqueda
    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('search=gato'))
  })

  // Test 4: Cambio de ordenación
  it('cambia la ordenación al hacer clic en una columna ordenable', async () => {
    const wrapper = mount(ImagesTable, {
      props: {
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          FontAwesomeIcon: true,
          ActionMenu: true,
          ConfirmationModal: true,
          EditImageModal: true,
          SortIcon: true
        }
      }
    })
    
    await flushPromises()
    
    // Limpiar el mock para preparar la siguiente llamada
    axios.get.mockClear()
    
    // Hacer clic en el encabezado de nombre para ordenar por nombre
    await wrapper.find('th:nth-child(2)').trigger('click')
    
    await flushPromises()
    
    // Verificar que se actualizó el campo de ordenación
    expect(wrapper.vm.sortBy).toBe('name')
    
    // Verificar que se llamó a axios.get con los nuevos parámetros de ordenación
    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('sort_by=name'))
    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('sort_order=asc'))
  })

  // Test 5: Eliminar imagen
  it('elimina una imagen correctamente', async () => {
    const wrapper = mount(ImagesTable, {
      props: {
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          FontAwesomeIcon: true,
          ConfirmationModal: true,
          EditImageModal: true,
          SortIcon: true
        }
      }
    })
    
    await flushPromises()
    
    // Simular directamente la confirmación de eliminación
    wrapper.vm.imageToDelete = mockImagesResponse.images[0]
    wrapper.vm.isDeleteModalOpen = true
    
    await wrapper.vm.deleteImage()
    
    // Verificar que se llamó a axios.delete con el ID correcto
    expect(axios.delete).toHaveBeenCalledWith(`/images/1`)
    
    // Verificar que se mostró la notificación de éxito
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      "Imagen eliminada",
      expect.stringContaining("imagen1.jpg")
    )
    
    // Verificar que se emitió el evento para actualizar estadísticas
    expect(wrapper.emitted('refresh-dataset-stats')).toBeTruthy()
  })
})