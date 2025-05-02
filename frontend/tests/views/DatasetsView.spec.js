import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import DatasetsView from '@/views/DatasetsView.vue'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../tests/helpers/test-utils'

// Mock del store de preferencias.
vi.mock('@/stores/userPreferencesStore', () => ({
  userPreferencesStore: () => ({
    setDatasetPageSize: vi.fn(),
    datasetPageSize: 5
  })
}))

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
    push: vi.fn(),
    replace: vi.fn()
  }),
  useRoute: () => ({
    path: '/my-datasets',
    query: {},
    params: {},
    meta: { requiresAuth: true }
  })
}))

// Mock de componentes usados por DatasetsView.
vi.mock('@/components/utils/ActionMenu.vue', () => ({
  default: {
    name: 'ActionMenu',
    props: ['item', 'itemId', 'position', 'actions'],
    template: '<div class="mock-action-menu"></div>',
    emits: ['view', 'edit', 'delete', 'publish', 'unpublish', 'close']
  }
}))

vi.mock('@/components/utils/ConfirmationModal.vue', () => ({
  default: {
    name: 'ConfirmationModal',
    props: ['isOpen', 'title', 'message', 'confirmText', 'cancelText', 'buttonType'],
    template: '<div v-if="isOpen" class="mock-confirmation-modal"></div>',
    emits: ['confirm', 'cancel']
  }
}))

vi.mock('@/components/datasets/AddDatasetModal.vue', () => ({
  default: {
    name: 'AddDatasetModal',
    props: ['isOpen'],
    template: '<div v-if="isOpen" class="mock-add-dataset-modal"></div>',
    emits: ['close', 'dataset-added']
  }
}))

vi.mock('@/components/datasets/EditDatasetModal.vue', () => ({
  default: {
    name: 'EditDatasetModal',
    props: ['isOpen', 'dataset'],
    template: '<div v-if="isOpen" class="mock-edit-dataset-modal"></div>',
    emits: ['close', 'dataset-updated']
  }
}))

vi.mock('@/components/utils/SortIcon.vue', () => ({
  default: {
    name: 'SortIcon',
    props: ['fieldName', 'currentSort', 'currentOrder'],
    template: '<div class="mock-sort-icon"></div>'
  }
}))

// Lista de datasets mock para pruebas.
const mockDatasets = [
  {
    id: '1',
    name: 'Dataset 1',
    description: 'Description for dataset 1',
    username: 'testuser',
    image_count: 10,
    category_count: 3,
    created_at: '2023-01-15T10:30:00Z',
    is_public: true,
    user_id: '1'
  },
  {
    id: '2',
    name: 'Dataset 2',
    description: 'Description for dataset 2',
    username: 'testuser',
    image_count: 5,
    category_count: 2,
    created_at: '2023-02-20T14:45:00Z',
    is_public: false,
    user_id: '1'
  },
  {
    id: '3',
    name: 'Dataset 3',
    description: 'Description for dataset 3',
    username: 'testuser',
    image_count: 15,
    category_count: 5,
    created_at: '2023-03-10T09:15:00Z',
    is_public: false,
    user_id: '1'
  }
];

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Listar datasets.
  http.get('/datasets/', ({ request }) => {
    // Parsear parámetros de la URL para paginación.
    const url = new URL(request.url);
    const skip = parseInt(url.searchParams.get('skip') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '5');
    const searchQuery = url.searchParams.get('search');
    
    // Si hay término de búsqueda, devolver resultados filtrados.
    if (searchQuery === 'Dataset 1') {
      return HttpResponse.json({
        datasets: [mockDatasets[0]], // Solo el primer dataset como resultado.
        count: 1
      }, { status: 200 })
    }
    
    // Devolver datasets paginados.
    return HttpResponse.json({
      datasets: mockDatasets.slice(skip, skip + limit),
      count: mockDatasets.length
    }, { status: 200 })
  }),
  
  // Eliminar dataset.
  http.delete('/datasets/:id', ({ params }) => {
    const { id } = params;
    // Simular eliminación exitosa.
    return HttpResponse.json({
      message: `Dataset ${id} deleted successfully`
    }, { status: 200 })
  }),
  
  // Actualizar dataset (para publicar/despublicar).
  http.patch('/datasets/:id', ({ params, request }) => {
    const { id } = params;
    return HttpResponse.json({
      id,
      ...mockDatasets.find(d => d.id === id),
      is_public: true // Simulamos que se actualizó a público
    }, { status: 200 })
  })
)

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

describe('DatasetsView.vue', () => {
  // Test 1: Carga inicial de datos.
  it('carga la lista de datasets correctamente', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datasets.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
      expect(wrapper.vm.datasets.length).toBe(3)
    })
    
    // Verificar que la tabla se renderiza.
    expect(wrapper.find('.datasets-table').exists()).toBe(true)
    
    // Verificar que se muestran todos los datasets.
    const datasetRows = wrapper.findAll('.dataset-row')
    expect(datasetRows.length).toBe(3)
    
    // Verificar información del primer dataset.
    const firstDatasetCells = datasetRows[0].findAll('td')
    expect(firstDatasetCells[0].text()).toContain('Dataset 1')
    expect(firstDatasetCells[1].text()).toContain('Description for dataset 1')
    expect(firstDatasetCells[2].text()).toBe('10') // image_count.
    expect(firstDatasetCells[3].text()).toBe('3') // category_count.
  })
  
  // Test 2: Búsqueda de datasets.
  it('realiza búsqueda de datasets correctamente', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que cargue inicialmente.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Establecer búsqueda.
    wrapper.vm.searchQuery = 'Dataset 1'
    
    // Espiar la función handleSearch.
    const searchSpy = vi.spyOn(wrapper.vm, 'handleSearch')
    
    // Invocar la búsqueda.
    await wrapper.vm.handleSearch()
    
    // Verificar que se llamó correctamente.
    expect(searchSpy).toHaveBeenCalled()
    
    // Verificar que los resultados se actualizan.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
      expect(wrapper.vm.datasets.length).toBe(1)
      expect(wrapper.vm.datasets[0].name).toBe('Dataset 1')
    })
  })
  
  // Test 3: Apertura de modal para añadir dataset.
  it('muestra el modal para añadir dataset', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Verificar que inicialmente el modal está cerrado.
    expect(wrapper.vm.isAddDatasetModalOpen).toBe(false)
    
    // Abrir modal.
    await wrapper.find('.add-dataset-button').trigger('click')
    
    // Verificar que el modal se abre.
    expect(wrapper.vm.isAddDatasetModalOpen).toBe(true)
    expect(wrapper.find('.mock-add-dataset-modal').exists()).toBe(true)
  })
  
  // Test 4: Confirmación antes de eliminar dataset.
  it('muestra el diálogo de confirmación al eliminar dataset', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente.
    expect(wrapper.vm.isDeleteModalOpen).toBe(false)
    
    // Llamar directamente al método de confirmación.
    await wrapper.vm.confirmDeleteDataset(mockDatasets[0])
    
    // Verificar que el modal se abre.
    expect(wrapper.vm.isDeleteModalOpen).toBe(true)
    expect(wrapper.vm.datasetToDelete).toEqual(mockDatasets[0])
  })
  
  // Test 5: Eliminación de dataset.
  it('elimina dataset correctamente', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Configurar para eliminar dataset.
    wrapper.vm.datasetToDelete = mockDatasets[0]
    wrapper.vm.isDeleteModalOpen = true
    
    // Espiar el método deleteDataset
    const deleteDatasetSpy = vi.spyOn(wrapper.vm, 'deleteDataset')
    
    // Llamar al método de eliminar.
    await wrapper.vm.deleteDataset()
    
    // Verificar que se llamó al método.
    expect(deleteDatasetSpy).toHaveBeenCalled()
    
    // Verificar que se mostró notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalled()
    
    // Verificar que el modal se cierra.
    expect(wrapper.vm.isDeleteModalOpen).toBe(false)
  })
  
  // Test 6: Manejo de errores de la API.
  it('maneja error al cargar datasets', async () => {
    // Configurar respuesta de error.
    server.use(
      http.get('/datasets/', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        )
      })
    )
    
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se procese la llamada a la API.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que se muestra el error.
    expect(notifications.notifyError).toHaveBeenCalled()
  })
  
  // Test 7: Compartir dataset.
  it('muestra el diálogo de confirmación para compartir dataset', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente.
    expect(wrapper.vm.isShareModalOpen).toBe(false)
    
    // Llamar directamente al método de confirmación para compartir un dataset privado.
    const privateDataset = mockDatasets[1]; // Dataset 2 que no es público.
    await wrapper.vm.confirmPublishDataset(privateDataset)
    
    // Verificar que el modal se abre con los datos correctos.
    expect(wrapper.vm.isShareModalOpen).toBe(true)
    expect(wrapper.vm.datasetToShare).toEqual(privateDataset)
    expect(wrapper.vm.shareModalAction).toBe('publish')
  })
  
  // Test 8: Cambio de visibilidad del dataset.
  it('cambia la visibilidad de un dataset correctamente', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Configurar para cambiar visibilidad.
    wrapper.vm.datasetToShare = mockDatasets[1]; // Dataset privado.
    wrapper.vm.shareModalAction = 'publish';
    wrapper.vm.isShareModalOpen = true;
    
    // Espiar el método processShareAction.
    const processShareActionSpy = vi.spyOn(wrapper.vm, 'processShareAction')
    
    // Llamar al método para procesar el cambio.
    await wrapper.vm.processShareAction()
    
    // Verificar que se llamó al método.
    expect(processShareActionSpy).toHaveBeenCalled()
    
    // Verificar que se mostró notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalled()
    
    // Verificar que el modal se cierra.
    expect(wrapper.vm.isShareModalOpen).toBe(false)
  })
  
  // Test 9: Edición de dataset.
  it('abre el modal de edición correctamente', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal de edición está cerrado inicialmente.
    expect(wrapper.vm.isEditDatasetModalOpen).toBe(false)
    
    // Llamar directamente al método de edición.
    await wrapper.vm.editDataset(mockDatasets[0])
    
    // Verificar que el modal se abre con el dataset correcto.
    expect(wrapper.vm.isEditDatasetModalOpen).toBe(true)
    expect(wrapper.vm.datasetToEdit).toEqual(mockDatasets[0])
    expect(wrapper.find('.mock-edit-dataset-modal').exists()).toBe(true)
  })
  
  // Test 10: Cambio de tamaño de página.
  it('cambia el tamaño de página correctamente', async () => {
    const wrapper = mount(DatasetsView, {
      global: globalOptions
    })
    
    // Esperar a que cargue inicialmente.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Espiar el método handlePageSizeChange.
    const pageSizeChangeSpy = vi.spyOn(wrapper.vm, 'handlePageSizeChange')
    
    // Cambiar el tamaño de página.
    wrapper.vm.pageSize = 10;
    await wrapper.vm.handlePageSizeChange();
    
    // Verificar que se llamó al método.
    expect(pageSizeChangeSpy).toHaveBeenCalled()
    
    // Verificar que se guardó la preferencia del usuario.
    expect(wrapper.vm.preferencesStore.setDatasetPageSize).toHaveBeenCalledWith(10)
  })
})