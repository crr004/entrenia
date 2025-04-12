import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import PublicDatasetDetailView from '@/views/PublicDatasetDetailView.vue'
import { useAuthStore } from '@/stores/authStore'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../tests/helpers/test-utils'

// Mock de Chart.js
vi.mock('chart.js/auto', () => ({
  default: class ChartMock {
    constructor() {
      this.destroy = vi.fn()
    }
  }
}))

// Definir routerPushMock fuera del ámbito de los mocks para accederlo desde cualquier test
const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();

// Mock del store de autenticación
vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'mock-token',
    user: { 
      id: '1', 
      username: 'testuser',
      email: 'testuser@example.com',
      is_admin: false
    },
    isAuthenticated: true,
    logout: vi.fn()
  }))
}))

// Mock de las funciones de notificación
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock del router
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPushMock,
    replace: routerReplaceMock
  }),
  useRoute: () => ({
    params: { id: '1' },
    path: '/explore/1',
    query: {}
  })
}))

// Mock de los componentes utilizados
vi.mock('@/components/utils/ConfirmationModal.vue', () => ({
  default: {
    name: 'ConfirmationModal',
    props: ['isOpen', 'title', 'message', 'confirmText', 'cancelText', 'buttonType', 'isLoading'],
    template: '<div v-if="isOpen" class="mock-confirmation-modal"></div>',
    emits: ['confirm', 'cancel']
  }
}))

// Añadir el mock del componente ReadOnlyImagesTable
vi.mock('@/components/images/ReadOnlyImagesTable.vue', () => ({
  default: {
    name: 'ReadOnlyImagesTable',
    props: ['datasetId'],
    template: '<div class="mock-readonly-images-table"></div>'
  }
}))

// Datos mock para las pruebas
const mockDataset = {
  id: '1',
  name: 'Dataset público de prueba',
  description: 'Este es un dataset público para pruebas',
  image_count: 10,
  category_count: 3,
  created_at: '2023-03-15T14:30:00Z',
  is_public: true,
  user_id: '2', // ID diferente al usuario actual (que es 1)
  username: 'otro_usuario'
}

const mockLabelDetails = {
  labeled_images: 6,
  unlabeled_images: 4,
  categories: [
    { name: 'Categoría 1', image_count: 3 },
    { name: 'Categoría 2', image_count: 2 },
    { name: 'Categoría 3', image_count: 1 }
  ]
}

// Servidor mock para simular respuestas de la API
const server = setupServer(
  // Obtener detalles del dataset público
  http.get('/datasets/public/:id', () => {
    return HttpResponse.json(mockDataset, { status: 200 })
  }),
  
  // Obtener detalles de etiquetas del dataset público
  http.get('/datasets/public/:id/label-details', () => {
    return HttpResponse.json(mockLabelDetails, { status: 200 })
  }),
  
  // Clonar dataset
  http.post('/datasets/:id/clone', () => {
    return HttpResponse.json({
      id: '3',
      name: 'Dataset público de prueba (copia)',
      description: 'Este es un dataset público para pruebas',
      image_count: 10,
      category_count: 3,
      is_public: false
    }, { status: 200 })
  }),

  // Añadir handler para imágenes de datasets públicos
  http.get('/images/public-dataset/:id', () => {
    return HttpResponse.json({
      images: [
        {
          id: '101',
          name: 'imagen1.jpg',
          thumbnail: 'base64string',
          label: 'Categoría 1',
          created_at: '2023-03-16T10:00:00Z'
        },
        {
          id: '102',
          name: 'imagen2.jpg',
          thumbnail: 'base64string',
          label: 'Categoría 2',
          created_at: '2023-03-16T11:00:00Z'
        }
      ],
      count: 2
    }, { status: 200 })
  })
)

// Configuración del servidor
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

// Restaurar el objeto Element.scrollIntoView porque lo usamos en pruebas
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

describe('PublicDatasetDetailView.vue', () => {
  // Test 1: Carga inicial de datos del dataset público
  it('carga correctamente los detalles del dataset público', async () => {
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que los datos del dataset están presentes
    expect(wrapper.vm.dataset).toEqual(mockDataset)
    expect(wrapper.vm.labelDetails).toEqual(mockLabelDetails)
    
    // Verificar título y detalles básicos
    expect(wrapper.find('h1').text()).toBe(mockDataset.name)
    expect(wrapper.find('.dataset-description p').text()).toBe(mockDataset.description)
    
    // Verificar información del usuario creador
    expect(wrapper.find('.dataset-user').text()).toContain('otro_usuario')
    
    // Verificar que se muestra como público
    expect(wrapper.find('.dataset-visibility.public').exists()).toBe(true)
  })
  
  // Test 2: Visualización correcta de categorías
  it('muestra correctamente las categorías del dataset público', async () => {
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que la tabla de categorías existe
    expect(wrapper.find('.categories-table').exists()).toBe(true)
    
    // Verificar que se muestran todas las categorías
    const categoryRows = wrapper.findAll('.categories-table tbody tr')
    expect(categoryRows.length).toBe(3)
    
    // Verificar el contenido de la primera categoría
    const firstCategoryRow = categoryRows[0]
    expect(firstCategoryRow.findAll('td')[0].text()).toBe('Categoría 1')
    expect(firstCategoryRow.findAll('td')[1].text()).toBe('3')
  })
  
  // Test 3: Redireccionamiento si es el propietario del dataset
  it('redirige a la vista personal cuando el usuario es propietario del dataset', async () => {
    // Mock del store con el usuario como propietario del dataset
    vi.mocked(useAuthStore).mockReturnValue({
      token: 'mock-token',
      user: { 
        id: '2',  // Mismo ID que el propietario del dataset
        username: 'otro_usuario',
        email: 'otro@example.com',
        is_admin: false
      },
      isAuthenticated: true,
      logout: vi.fn()
    })
    
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos y se procese la redirección
    await vi.waitFor(() => {
      expect(routerReplaceMock).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'dataset-detail',
          params: { id: '1' }
        })
      )
    })
  })
  
  // Test 4: Mostrar modal de confirmación para clonar dataset
  it('muestra el modal de confirmación al intentar clonar el dataset', async () => {
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente
    expect(wrapper.vm.showCloneModal).toBe(false)
    
    // Buscar el botón de clonar y hacer clic
    const cloneButton = wrapper.find('.clone-button')
    expect(cloneButton.exists()).toBe(true)
    
    await cloneButton.trigger('click')
    
    // Verificar que el modal se abrió
    expect(wrapper.vm.showCloneModal).toBe(true)
    expect(wrapper.find('.mock-confirmation-modal').exists()).toBe(true)
  })
  
  // Test 5: Clonación exitosa de dataset
  it('clona el dataset correctamente y redirige al usuario', async () => {
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Abrir modal de confirmación
    wrapper.vm.showCloneConfirmation()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.showCloneModal).toBe(true)
    
    // Confirmar la clonación
    await wrapper.vm.confirmCloneDataset()
    
    // Verificar que se muestra notificación de éxito
    expect(notifications.notifySuccess).toHaveBeenCalled()
    
    // Verificar que se redirige al usuario a la vista del dataset clonado
    expect(routerPushMock).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'dataset-detail',
        params: { id: '3' }
      })
    )
    
    // Verificar que el modal se cierra
    expect(wrapper.vm.showCloneModal).toBe(false)
  })
  
  // Test 6: No mostrar botón de clonar si no está autenticado
  it('no muestra el botón de clonar si el usuario no está autenticado', async () => {
    // Mock del store con usuario no autenticado
    vi.mocked(useAuthStore).mockReturnValue({
      token: null,
      user: null,
      isAuthenticated: false,
      logout: vi.fn()
    })
    
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el botón de clonar no existe
    expect(wrapper.find('.clone-button').exists()).toBe(false)
  })
  
  // Test 7: Manejo de intento de clonar sin autenticación
  it('muestra notificación y redirige al intentar clonar sin estar autenticado', async () => {
    // Mock del store con usuario no autenticado
    vi.mocked(useAuthStore).mockReturnValue({
      token: null,
      user: null,
      isAuthenticated: false,
      logout: vi.fn()
    })
    
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Llamar directamente al método de confirmar clonación
    wrapper.vm.showCloneConfirmation()
    
    // Verificar que se muestra notificación informativa
    expect(notifications.notifyInfo).toHaveBeenCalled()
    
    // Verificar que se redirige al inicio
    expect(routerPushMock).toHaveBeenCalledWith('/')
  })
  
  // Test 8: Manejo de error al clonar dataset
  it('maneja correctamente los errores al clonar el dataset', async () => {
    // Configurar respuesta de error para la clonación
    server.use(
      http.post('/datasets/:id/clone', () => {
        return HttpResponse.json(
          { detail: 'Error al clonar el dataset' },
          { status: 500 }
        )
      })
    )
    
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Preparar para clonar
    wrapper.vm.showCloneModal = true
    await wrapper.vm.$nextTick()
    
    // Intentar clonar
    await wrapper.vm.confirmCloneDataset()
    
    // Verificar que se muestra notificación de error
    expect(notifications.notifyError).toHaveBeenCalled()
    
    // Verificar que isCloning vuelve a false
    expect(wrapper.vm.isCloning).toBe(false)
  })
  
  // Test 9: Manejo de dataset ya clonado
  it('redirige al dataset existente si ya fue clonado previamente', async () => {
    // Configurar respuesta para dataset ya clonado
    server.use(
      http.post('/datasets/:id/clone', () => {
        return new HttpResponse(
          null,
          { 
            status: 409,
            headers: {
              'X-Dataset-Id': '5'
            }
          }
        )
      })
    )
    
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Preparar para clonar
    wrapper.vm.showCloneModal = true
    await wrapper.vm.$nextTick()
    
    // Intentar clonar
    await wrapper.vm.confirmCloneDataset()
    
    // Verificar que se redirige al dataset existente
    expect(routerPushMock).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'dataset-detail',
        params: { id: '5' }
      })
    )
    
    // Verificar que el modal se cierra
    expect(wrapper.vm.showCloneModal).toBe(false)
  })
  
  // Test 10: Formateo correcto de fechas
  it('formatea correctamente las fechas', async () => {
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Probar la función de formateo de fechas
    const formattedDate = wrapper.vm.formatDate('2023-03-15T14:30:00Z')
    
    // La implementación exacta dependerá del navegador y la zona horaria,
    // pero podemos comprobar que devuelve un string no vacío
    expect(typeof formattedDate).toBe('string')
    expect(formattedDate.length).toBeGreaterThan(0)
  })

  // Test 11: Mostrar tabla de imágenes del dataset público
  it('muestra la tabla de imágenes del dataset público', async () => {
    const wrapper = mount(PublicDatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que la tabla de imágenes existe
    expect(wrapper.find('.images-section').exists()).toBe(true)
    expect(wrapper.find('.mock-readonly-images-table').exists()).toBe(true)
  })
})