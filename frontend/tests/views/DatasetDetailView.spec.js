import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import DatasetDetailView from '@/views/DatasetDetailView.vue'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../tests/helpers/test-utils'

// Mock de Chart.js.
vi.mock('chart.js/auto', () => ({
  default: class ChartMock {
    constructor() {
      this.destroy = vi.fn()
    }
  }
}))

// Definir routerPushMock fuera del ámbito de los mocks para accederlo desde cualquier test.
const routerPushMock = vi.fn();

// Mock del store de autenticación.
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
    setAuthHeader: vi.fn()
  }))
}))

// Mock de las funciones de notificación.
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock del router.
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPushMock,
    replace: vi.fn()
  }),
  useRoute: () => ({
    params: { id: '1' },
    path: '/dataset/1',
    query: {}
  })
}))

// Mock de los componentes utilizados en DatasetDetailView.
vi.mock('@/components/images/ImagesTable.vue', () => ({
  default: {
    name: 'ImagesTable',
    props: ['datasetId'],
    template: '<div class="mock-images-table"></div>',
    emits: ['refresh-dataset-stats'],
    methods: {
      fetchImages: vi.fn()
    }
  }
}))

vi.mock('@/components/images/UploadImagesModal.vue', () => ({
  default: {
    name: 'UploadImagesModal',
    props: ['isOpen', 'datasetId'],
    template: '<div v-if="isOpen" class="mock-upload-modal"></div>',
    emits: ['close', 'images-uploaded']
  }
}))

vi.mock('@/components/images/UploadResultModal.vue', () => ({
  default: {
    name: 'UploadResultModal',
    props: ['show', 'stats', 'invalidImageDetails', 'duplicatedImageDetails', 'skippedLabelDetails'],
    template: '<div v-if="show" class="mock-result-modal"></div>',
    emits: ['close', 'view-images']
  }
}))

vi.mock('@/components/images/LabelingMethodModal.vue', () => ({
  default: {
    name: 'LabelingMethodModal',
    props: ['isOpen', 'unlabeledCount'],
    template: '<div v-if="isOpen" class="mock-labeling-method-modal"></div>',
    emits: ['close', 'select-method']
  }
}))

vi.mock('@/components/images/ManualLabelingModal.vue', () => ({
  default: {
    name: 'ManualLabelingModal',
    props: ['isOpen', 'datasetId'],
    template: '<div v-if="isOpen" class="mock-manual-labeling-modal"></div>',
    emits: ['close', 'images-labeled']
  }
}))

vi.mock('@/components/images/CsvLabelingModal.vue', () => ({
  default: {
    name: 'CsvLabelingModal',
    props: ['isOpen', 'datasetId'],
    template: '<div v-if="isOpen" class="mock-csv-labeling-modal"></div>',
    emits: ['close', 'images-labeled']
  }
}))

vi.mock('@/components/images/LabelingResultsModal.vue', () => ({
  default: {
    name: 'LabelingResultsModal',
    props: ['isOpen', 'result'],
    template: '<div v-if="isOpen" class="mock-labeling-results-modal"></div>',
    emits: ['close']
  }
}))

// Datos mock para las pruebas.
const mockDataset = {
  id: '1',
  name: 'Dataset de prueba',
  description: 'Este es un dataset para pruebas',
  image_count: 10,
  category_count: 3,
  created_at: '2023-03-15T14:30:00Z',
  is_public: false,
  user_id: '1'
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

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Obtener detalles del dataset.
  http.get('/datasets/:id', ({ params }) => {
    return HttpResponse.json(mockDataset, { status: 200 })
  }),
  
  // Obtener detalles de etiquetas.
  http.get('/datasets/:id/label-details', ({ params }) => {
    return HttpResponse.json(mockLabelDetails, { status: 200 })
  })
)

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

// Restaurar el objeto Element.scrollIntoView porque lo usamos en pruebas.
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

describe('DatasetDetailView.vue', () => {
  // Test 1: Carga inicial de datos.
  it('carga correctamente los detalles del dataset', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que los datos del dataset están presentes.
    expect(wrapper.vm.dataset).toEqual(mockDataset)
    expect(wrapper.vm.labelDetails).toEqual(mockLabelDetails)
    
    // Verificar el título del dataset.
    expect(wrapper.find('h1').text()).toBe(mockDataset.name)
    
    // Verificar que se muestra la descripción.
    expect(wrapper.find('.dataset-description p').text()).toBe(mockDataset.description)
    
    // Verificar las estadísticas del dataset.
    const statItems = wrapper.findAll('.stat-item')
    expect(statItems.length).toBe(4)
    
    // Verificar que el componente ImagesTable está presente.
    expect(wrapper.find('.mock-images-table').exists()).toBe(true)
  })
  
  // Test 2: Visualización correcta de categorías.
  it('muestra correctamente las categorías del dataset', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que la tabla de categorías existe.
    expect(wrapper.find('.categories-table').exists()).toBe(true)
    
    // Verificar que se muestran todas las categorías.
    const categoryRows = wrapper.findAll('.categories-table tbody tr')
    expect(categoryRows.length).toBe(3)
    
    // Verificar el contenido de la primera categoría.
    const firstCategoryRow = categoryRows[0]
    expect(firstCategoryRow.findAll('td')[0].text()).toBe('Categoría 1')
    expect(firstCategoryRow.findAll('td')[1].text()).toBe('3')
  })
  
  // Test 3: Apertura del modal para subir imágenes.
  it('abre el modal para subir imágenes', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente.
    expect(wrapper.vm.isUploadModalOpen).toBe(false)
    
    // Buscar el botón de subir imágenes y hacer clic.
    const uploadButton = wrapper.findAll('.app-button').filter(button => 
      button.text().includes('Subir imágenes')
    )[0]
    
    await uploadButton.trigger('click')
    
    // Verificar que el modal se abrió.
    expect(wrapper.vm.isUploadModalOpen).toBe(true)
    expect(wrapper.find('.mock-upload-modal').exists()).toBe(true)
  })
  
  // Test 4: Apertura del modal de selección de método de etiquetado.
  it('abre el modal de selección de método de etiquetado', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente.
    expect(wrapper.vm.isLabelingMethodModalOpen).toBe(false)
    
    // Buscar el botón de etiquetar imágenes y hacer clic.
    const labelButton = wrapper.findAll('.app-button').filter(button => 
      button.text().includes('Etiquetar imágenes')
    )[0]
    
    await labelButton.trigger('click')
    
    // Verificar que el modal se abrió.
    expect(wrapper.vm.isLabelingMethodModalOpen).toBe(true)
    expect(wrapper.find('.mock-labeling-method-modal').exists()).toBe(true)
  })
  
  // Test 5: Selección de método de etiquetado manual.
  it('abre el modal de etiquetado manual al seleccionar este método', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Abrir el modal de selección de método.
    wrapper.vm.isLabelingMethodModalOpen = true
    await wrapper.vm.$nextTick()
    
    // Simular selección de etiquetado manual.
    await wrapper.vm.handleSelectLabelingMethod('manual')
    
    // Verificar que se cerró el modal de selección.
    expect(wrapper.vm.isLabelingMethodModalOpen).toBe(false)
    
    // Verificar que se abrió el modal de etiquetado manual.
    expect(wrapper.vm.isManualLabelingModalOpen).toBe(true)
    expect(wrapper.find('.mock-manual-labeling-modal').exists()).toBe(true)
  })
  
  // Test 6: Selección de método de etiquetado CSV.
  it('abre el modal de etiquetado CSV al seleccionar este método', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Abrir el modal de selección de método.
    wrapper.vm.isLabelingMethodModalOpen = true
    await wrapper.vm.$nextTick()
    
    // Simular selección de etiquetado CSV.
    await wrapper.vm.handleSelectLabelingMethod('csv')
    
    // Verificar que se cerró el modal de selección.
    expect(wrapper.vm.isLabelingMethodModalOpen).toBe(false)
    
    // Verificar que se abrió el modal de etiquetado CSV.
    expect(wrapper.vm.isCsvLabelingModalOpen).toBe(true)
    expect(wrapper.find('.mock-csv-labeling-modal').exists()).toBe(true)
  })
  
  // Test 7: Manejo de imágenes etiquetadas.
  it('muestra el modal de resultados después de etiquetar imágenes', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Establecer isLoading a false directamente y asegurar que los componentes necesarios existan.
    wrapper.vm.isLoading = false;
    wrapper.vm.dataset = {...mockDataset};
    wrapper.vm.labelDetails = {...mockLabelDetails};
    await wrapper.vm.$nextTick();
    
    // Verificar que los modales están cerrados inicialmente.
    expect(wrapper.vm.isLabelingResultModalOpen).toBe(false);
    
    const labelingResult = {
      labeledCount: 3,
      notFoundCount: 1,
      notFoundDetails: ['image1.jpg']
    }
    
    // Llamar directamente al método que maneja el etiquetado completado.
    wrapper.vm.handleImagesLabeled(labelingResult);
    await wrapper.vm.$nextTick(); // Esperar a que Vue actualice el DOM.
    
    // Verificar que los modales de etiquetado se cerraron.
    expect(wrapper.vm.isManualLabelingModalOpen).toBe(false)
    expect(wrapper.vm.isCsvLabelingModalOpen).toBe(false)
    
    // Verificar que se abrió el modal de resultados.
    expect(wrapper.vm.isLabelingResultModalOpen).toBe(true)
    expect(wrapper.vm.labelingResultData).toEqual(labelingResult)
  })

  // Test 8: Manejo de carga de imágenes.
  it('muestra el modal de resultados después de cargar imágenes', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Establecer isLoading a false directamente y asegurar que los componentes necesarios existan.
    wrapper.vm.isLoading = false;
    wrapper.vm.dataset = {...mockDataset};
    wrapper.vm.labelDetails = {...mockLabelDetails};
    await wrapper.vm.$nextTick();
    
    // Verificar que los modales están cerrados inicialmente.
    expect(wrapper.vm.showResultModal).toBe(false);
    
    const uploadResult = {
      processed_images: 5,
      skipped_images: 1,
      invalid_images: 1,
      labels_applied: 2,
      labels_skipped: 0,
      invalid_image_details: ['invalid.txt'],
      duplicated_image_details: ['duplicate.jpg'],
      skipped_label_details: []
    }
    
    // Llamar directamente al método que maneja la carga completada.
    wrapper.vm.handleImagesUploaded(uploadResult);
    await wrapper.vm.$nextTick(); // Esperar a que Vue actualice el DOM.
    
    // Verificar que el modal de carga se cerró.
    expect(wrapper.vm.isUploadModalOpen).toBe(false)
    
    // Verificar que se actualizaron las estadísticas.
    expect(wrapper.vm.uploadStats).toMatchObject({
      processed_images: 5,
      skipped_images: 1,
      invalid_images: 1,
      labels_applied: 2,
      labels_skipped: 0
    })
    
    // Verificar que se abrió el modal de resultados.
    expect(wrapper.vm.showResultModal).toBe(true)
  })
  
  // Test 9: Manejo de errores al cargar dataset.
  it('maneja correctamente el error cuando el dataset no existe', async () => {
    // Configurar el servidor para devolver un error 404.
    server.use(
      http.get('/datasets/:id', () => {
        return HttpResponse.json(
          { detail: 'Dataset not found' },
          { status: 404 }
        )
      })
    )
    
    
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Esperar a que se procese el error.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que se notificó el error.
    expect(notifications.notifyError).toHaveBeenCalledWith(
      'Conjunto de imágenes no encontrado',
      expect.any(String)
    )
  })
  
  // Test 10: Formateo correcto de fechas.
  it('formatea correctamente las fechas', async () => {
    const wrapper = mount(DatasetDetailView, {
      global: globalOptions
    })
    
    // Probar la función de formateo de fechas.
    const formattedDate = wrapper.vm.formatDate('2023-03-15T14:30:00Z')
    
    // La implementación exacta dependerá del navegador y la zona horaria,
    // pero se puede comprobar que devuelve un string no vacío.
    expect(typeof formattedDate).toBe('string')
    expect(formattedDate.length).toBeGreaterThan(0)
  })
})