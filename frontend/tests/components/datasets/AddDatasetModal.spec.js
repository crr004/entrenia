import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AddDatasetModal from '@/components/datasets/AddDatasetModal.vue'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../../tests/helpers/test-utils'
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

describe('AddDatasetModal.vue', () => {
  // Configurar mocks antes de cada test
  beforeEach(() => {
    // Crear una instancia limpia de pinia
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock de axios.post para simular la creación exitosa de dataset
    axios.post = vi.fn().mockResolvedValue({
      data: {
        id: '1',
        name: 'Test Dataset',
        description: 'Test description',
        is_public: false
      }
    })
    
    // Limpiar mocks
    vi.clearAllMocks()
  })
  
  // Test 1: Visualización del modal
  it('muestra el modal cuando isOpen es true', () => {
    const wrapper = shallowMount(AddDatasetModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Verificar que el modal está visible
    expect(wrapper.find('.auth-modal').exists()).toBe(true)
  })
  
  // Test 2: Validación de campos
  it('valida el nombre del dataset correctamente', async () => {
    const wrapper = shallowMount(AddDatasetModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Caso 1: Nombre vacío
    wrapper.vm.datasetData.name = ''
    wrapper.vm.validateName()
    expect(wrapper.vm.nameError).toBe('El nombre del conjunto es obligatorio.')
    
    // Caso 2: Nombre demasiado largo
    wrapper.vm.datasetData.name = 'a'.repeat(256)
    wrapper.vm.validateName()
    expect(wrapper.vm.nameError).toBe('El nombre no puede exceder los 255 caracteres.')
    
    // Caso 3: Nombre válido
    wrapper.vm.datasetData.name = 'Test Dataset'
    wrapper.vm.validateName()
    expect(wrapper.vm.nameError).toBe('')
  })
  
  // Test 3: Validación de descripción
  it('valida la descripción correctamente', async () => {
    const wrapper = shallowMount(AddDatasetModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Caso 1: Descripción demasiado larga
    wrapper.vm.datasetData.description = 'a'.repeat(1001)
    wrapper.vm.validateDescription()
    expect(wrapper.vm.descriptionError).toBe('La descripción no puede exceder los 1000 caracteres.')
    
    // Caso 2: Descripción válida
    wrapper.vm.datasetData.description = 'Test description'
    wrapper.vm.validateDescription()
    expect(wrapper.vm.descriptionError).toBe('')
    
    // Caso 3: Descripción vacía (opcional)
    wrapper.vm.datasetData.description = ''
    wrapper.vm.validateDescription()
    expect(wrapper.vm.descriptionError).toBe('')
  })
  
  // Test 4: Creación exitosa de dataset
  it('crea un nuevo dataset correctamente', async () => {
    const wrapper = shallowMount(AddDatasetModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Configurar datos válidos
    wrapper.vm.datasetData.name = 'Test Dataset'
    wrapper.vm.datasetData.description = 'Test description'
    
    // Llamar al método
    await wrapper.vm.handleSubmit()
    await flushPromises()
    
    // Verificar que se llamó a axios.post
    expect(axios.post).toHaveBeenCalledWith('/datasets/', {
      name: 'Test Dataset',
      description: 'Test description',
      is_public: false
    })
    
    // Verificar que se mostró la notificación de éxito
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      'Conjunto de imágenes creado',
      'Se ha creado el conjunto Test Dataset con éxito.'
    )
    
    // Verificar que se emitieron los eventos adecuados
    expect(wrapper.emitted('dataset-added')).toBeTruthy()
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 5: Reset del formulario al cerrar
  it('resetea el formulario al cerrar el modal', async () => {
    const wrapper = shallowMount(AddDatasetModal, {
      props: {
        isOpen: true
      },
      global: globalOptions
    })
    
    // Configurar datos
    wrapper.vm.datasetData.name = 'Test Dataset'
    wrapper.vm.datasetData.description = 'Test description'
    wrapper.vm.nameError = 'Error de prueba'
    
    // Cerrar modal
    wrapper.vm.closeModal()
    
    // Verificar que se resetearon los campos
    expect(wrapper.vm.datasetData.name).toBe('')
    expect(wrapper.vm.datasetData.description).toBe('')
    expect(wrapper.vm.nameError).toBe('')
    expect(wrapper.vm.descriptionError).toBe('')
    
    // Verificar que se emitió el evento close
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})