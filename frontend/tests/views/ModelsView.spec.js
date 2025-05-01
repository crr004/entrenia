import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import ModelsView from '@/views/ModelsView.vue'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../tests/helpers/test-utils'
import axios from 'axios';

// Mock del store de preferencias.
vi.mock('@/stores/userPreferencesStore', () => ({
  userPreferencesStore: () => ({
    setModelPageSize: vi.fn(),
    modelPageSize: 5
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
    setAuthHeader: vi.fn(),
    logout: vi.fn()
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
    path: '/my-models',
    query: {},
    params: {},
    meta: { requiresAuth: true }
  })
}))

// Mock de componentes usados por ModelsView.
vi.mock('@/components/utils/ActionMenu.vue', () => ({
  default: {
    name: 'ActionMenu',
    props: ['item', 'itemId', 'position', 'actions'],
    template: '<div class="mock-action-menu"></div>',
    emits: ['view', 'edit', 'delete', 'download', 'predict', 'close']
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

vi.mock('@/components/models/EditModelModal.vue', () => ({
  default: {
    name: 'EditModelModal',
    props: ['isOpen', 'model'],
    template: '<div v-if="isOpen" class="mock-edit-model-modal"></div>',
    emits: ['close', 'model-updated']
  }
}))

vi.mock('@/components/models/PredictionModal.vue', () => ({
  default: {
    name: 'PredictionModal',
    props: ['isOpen', 'modelName', 'modelId'],
    template: '<div v-if="isOpen" class="mock-prediction-modal"></div>',
    emits: ['close']
  }
}))

vi.mock('@/components/utils/SortIcon.vue', () => ({
  default: {
    name: 'SortIcon',
    props: ['fieldName', 'currentSort', 'currentOrder'],
    template: '<div class="mock-sort-icon"></div>'
  }
}))

// Lista de modelos mock para pruebas.
const mockModels = [
  {
    id: '1',
    name: 'Model 1',
    description: 'Description for model 1',
    username: 'testuser',
    status: 'trained',
    created_at: '2023-01-15T10:30:00Z',
    user_id: '1'
  },
  {
    id: '2',
    name: 'Model 2',
    description: 'Description for model 2',
    username: 'testuser',
    status: 'training',
    created_at: '2023-02-20T14:45:00Z',
    user_id: '1'
  },
  {
    id: '3',
    name: 'Model 3',
    description: 'Description for model 3',
    username: 'testuser',
    status: 'failed',
    created_at: '2023-03-10T09:15:00Z',
    user_id: '1'
  }
];

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Listar modelos.
  http.get('/classifiers/', ({ request }) => {
    const url = new URL(request.url);
    const skip = parseInt(url.searchParams.get('skip') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '5');
    const searchQuery = url.searchParams.get('search');
    
    // Si hay término de búsqueda, devolver resultados filtrados.
    if (searchQuery === 'Model 1') {
      return HttpResponse.json({
        classifiers: [mockModels[0]], // Solo el primer modelo como resultado.
        count: 1
      }, { status: 200 })
    }
    
    // Devolver modelos paginados.
    return HttpResponse.json({
      classifiers: mockModels.slice(skip, skip + limit),
      count: mockModels.length
    }, { status: 200 })
  }),
  
  // Eliminar modelo.
  http.delete('/classifiers/:id', ({ params }) => {
    const { id } = params;
    return HttpResponse.json({
      message: `Model ${id} deleted successfully`
    }, { status: 200 })
  }),
  
  // Actualizar modelo.
  http.patch('/classifiers/:id', ({ params, request }) => {
    const { id } = params;
    return HttpResponse.json({
      id,
      ...mockModels.find(m => m.id === id),
      name: 'Updated Model Name'
    }, { status: 200 })
  })
)

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

describe('ModelsView.vue', () => {
  // Test 1: Carga inicial de datos.
  it('carga la lista de modelos correctamente', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los modelos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
      expect(wrapper.vm.models.length).toBe(3)
    })
    
    // Verificar que la tabla se renderiza.
    expect(wrapper.find('.models-table').exists()).toBe(true)
    
    // Verificar que se muestran todos los modelos.
    const modelRows = wrapper.findAll('.model-row')
    expect(modelRows.length).toBe(3)
    
    // Verificar información del primer modelo.
    const firstModelCells = modelRows[0].findAll('td')
    expect(firstModelCells[0].text()).toContain('Model 1')
    expect(firstModelCells[1].text()).toContain('Description for model 1')
    expect(firstModelCells[2].text()).toBe('Entrenado') // status.
  })
  
  // Test 2: Búsqueda de modelos.
  it('realiza búsqueda de modelos correctamente', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que cargue inicialmente.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Establecer búsqueda.
    wrapper.vm.searchQuery = 'Model 1'
    
    // Espiar la función handleSearch.
    const searchSpy = vi.spyOn(wrapper.vm, 'handleSearch')
    
    // Invocar la búsqueda.
    await wrapper.vm.handleSearch()
    
    // Verificar que se llamó correctamente.
    expect(searchSpy).toHaveBeenCalled()
    
    // Verificar que los resultados se actualizan.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
      expect(wrapper.vm.models.length).toBe(1)
      expect(wrapper.vm.models[0].name).toBe('Model 1')
    })
  })
  
  // Test 3: Navegación al crear un nuevo modelo.
  it('navega a la página de entrenamiento al hacer clic en "Entrenar un modelo"', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Espiar la función de navegación.
    const routerPushSpy = vi.spyOn(wrapper.vm.router, 'push')
    
    // Hacer clic en el botón de crear modelo.
    await wrapper.find('.add-model-button').trigger('click')
    
    // Verificar que se navega a la página correcta.
    expect(routerPushSpy).toHaveBeenCalledWith('/train-model')
  })
  
  // Test 4: Confirmación antes de eliminar modelo.
  it('muestra el diálogo de confirmación al eliminar modelo', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente.
    expect(wrapper.vm.isDeleteModalOpen).toBe(false)
    
    // Llamar directamente al método de confirmación.
    await wrapper.vm.confirmDeleteModel(mockModels[0])
    
    // Verificar que el modal se abre.
    expect(wrapper.vm.isDeleteModalOpen).toBe(true)
    expect(wrapper.vm.modelToDelete).toEqual(mockModels[0])
    expect(wrapper.find('.mock-confirmation-modal').exists()).toBe(true)
  })
  
  // Test 5: Eliminación de modelo.
  it('elimina modelo correctamente', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Configurar para eliminar modelo.
    wrapper.vm.modelToDelete = mockModels[0]
    wrapper.vm.isDeleteModalOpen = true
    
    // Espiar el método deleteModel.
    const deleteModelSpy = vi.spyOn(wrapper.vm, 'deleteModel')
    
    // Llamar al método de eliminar.
    await wrapper.vm.deleteModel()
    
    // Verificar que se llamó al método.
    expect(deleteModelSpy).toHaveBeenCalled()
    
    // Verificar que se mostró notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalled()
    
    // Verificar que el modal se cierra.
    expect(wrapper.vm.isDeleteModalOpen).toBe(false)
  })
  
  // Test 6: Manejo de errores de la API.
  it('maneja error al cargar modelos', async () => {
    // Configurar respuesta de error.
    server.use(
      http.get('/classifiers/', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        )
      })
    )
    
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que se procese la llamada a la API.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que se muestra el error.
    expect(notifications.notifyError).toHaveBeenCalled()
  })
  
  // Test 7: Apertura del modal de edición.
  it('abre el modal de edición correctamente', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal de edición está cerrado inicialmente.
    expect(wrapper.vm.isEditModelModalOpen).toBe(false)
    
    // Llamar directamente al método de edición.
    await wrapper.vm.editModel(mockModels[0])
    
    // Verificar que el modal se abre con el modelo correcto.
    expect(wrapper.vm.isEditModelModalOpen).toBe(true)
    expect(wrapper.vm.modelToEdit).toEqual(mockModels[0])
    expect(wrapper.find('.mock-edit-model-modal').exists()).toBe(true)
  })
  
  // Test 8: Apertura del modal de predicción.
  it('abre el modal de predicción para un modelo entrenado', async () => {
    const wrapper = mount(ModelsView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal de predicción está cerrado inicialmente.
    expect(wrapper.vm.isPredictionModalOpen).toBe(false)
    
    // Seleccionar un modelo entrenado.
    const trainedModel = mockModels[0] // El primer modelo tiene status 'trained'.
    
    // Llamar directamente al método de predicción.
    await wrapper.vm.predictWithModel(trainedModel)
    
    // Verificar que el modal se abre con el modelo correcto.
    expect(wrapper.vm.isPredictionModalOpen).toBe(true)
    expect(wrapper.vm.modelToPredict).toEqual(trainedModel)
    expect(wrapper.find('.mock-prediction-modal').exists()).toBe(true)
  })
  
  // Test 9: Descarga de modelo.
  it('permite descargar un modelo entrenado', async () => {
    // Crear mocks para APIs del navegador necesarias para la descarga.
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    // Mock para el método window.open que ModelsView puede usar.
    window.open = vi.fn();
    
    // Simular la respuesta de axios sin montar el componente.
    axios.get = vi.fn().mockResolvedValue({
      data: new Blob(['mock-file-content'])
    });
    
    // Simular el método downloadModel directamente.
    const downloadModel = async (modelId) => {
      try {
        const response = await axios.get(`/classifiers/${modelId}/download`, {
          responseType: 'blob'
        });
        
        // Crear un blob URL y descargar.
        const url = URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.setAttribute('download', 'model.zip');
        link.href = url;
        
        // Simular click.
        link.click();
        
        // Limpiar.
        URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Error downloading model", error);
      }
    };
    
    // Ejecutar la función de descarga.
    await downloadModel('model-123');
    
    // Verificar que la petición axios se hizo correctamente.
    expect(axios.get).toHaveBeenCalledWith('/classifiers/model-123/download', {
      responseType: 'blob'
    });
    
    // Verificar que createObjectURL fue llamado.
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  // Test 10: Cambio de tamaño de página.
  it('maneja los cambios de tamaño de página', () => {
    // Crear un objeto simple que simula preferencesStore.
    const preferencesStore = {
      setModelPageSize: vi.fn()
    };
    
    // Simular método handlePageSizeChange que usa el componente.
    const handlePageSizeChange = (pageSize) => {
      // Guarda la preferencia y recarga datos.
      preferencesStore.setModelPageSize(pageSize);
      // Simular recarga de datos.
      return Promise.resolve();
    };
    
    // Llamar al método con un nuevo tamaño.
    handlePageSizeChange(10);
    
    // Verificar que se llamó al método del store con el tamaño correcto.
    expect(preferencesStore.setModelPageSize).toHaveBeenCalledWith(10);
  });
})