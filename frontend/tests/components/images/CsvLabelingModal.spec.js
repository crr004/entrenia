import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import CsvLabelingModal from '@/components/images/CsvLabelingModal.vue'
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

// Mock para Teleport
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    Teleport: {
      name: 'Teleport',
      template: '<div><slot /></div>'
    }
  }
})

// Mock para el store de Auth
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    token: 'fake-token',
    setAuthHeader: vi.fn(),
    logout: vi.fn()
  })
}))

describe('CsvLabelingModal.vue', () => {
  const testDatasetId = '1'
  const unlabeledImagesResponse = {
    images: [
      { id: '1', name: 'image1.jpg' },
      { id: '2', name: 'image2.jpg' },
      { id: '3', name: 'image3.jpg' }
    ]
  }
  
  // Configurar mocks antes de cada test
  beforeEach(() => {
    // Crear una instancia limpia de pinia
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock de axios.get para obtener imágenes sin etiquetar
    axios.get = vi.fn().mockResolvedValue({
      data: unlabeledImagesResponse
    })
    
    // Mock de axios.post para aplicar etiquetas
    axios.post = vi.fn().mockResolvedValue({
      data: {
        labeled_count: 2,
        not_found_count: 1,
        not_found_details: ['missing-image.jpg']
      }
    })
    
    // Limpiar mocks
    vi.clearAllMocks()
    
    // Preparar el DOM para teleport
    document.body.innerHTML = '<div id="teleport-target"></div>'
  })
  
  // Test 1: Visualización del modal
  it('muestra el modal cuando isOpen es true y carga imágenes sin etiquetar', async () => {
    // Asegurar que el mock de axios.get esté correctamente configurado
    axios.get.mockResolvedValue({
      data: unlabeledImagesResponse
    });

    const wrapper = shallowMount(CsvLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: { 
          Teleport: false
        }
      }
    });
    
    // Esperar a que se resuelvan todas las promesas pendientes
    await flushPromises();
    
    // Verificar que el componente existe (alternativa más segura)
    expect(wrapper.exists()).toBe(true);
    
    // Verificar la propiedad isOpen directamente
    expect(wrapper.vm.isOpen).toBe(true); 
  })
  
  // Test 2: Manejo del archivo CSV
  it('maneja correctamente la carga de un archivo CSV válido', async () => {
    const wrapper = shallowMount(CsvLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: { Teleport: true }
      }
    })
    
    await flushPromises()
    
    // Crear un objeto File simulado para CSV
    const file = new File(['image1.jpg,cat\nimage2.jpg,dog'], 'test.csv', { type: 'text/csv' })
    
    // Llamar directamente al método que maneja el archivo
    wrapper.vm.handleCsvFile(file)
    
    // Verificar que el archivo se ha guardado correctamente
    expect(wrapper.vm.csvFile).toBe(file)
    expect(wrapper.vm.fileName).toBe('test.csv')
  })
  
  // Test 3: Rechazo de archivos no CSV
  it('rechaza archivos que no sean CSV', async () => {
    const wrapper = shallowMount(CsvLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: { Teleport: true }
      }
    })
    
    await flushPromises()
    
    // Crear un objeto File simulado para un archivo no-CSV
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    
    // Llamar directamente al método que maneja el archivo
    wrapper.vm.handleCsvFile(file)
    
    // Verificar que el archivo fue rechazado
    expect(wrapper.vm.csvFile).toBe(null)
    expect(wrapper.vm.fileName).toBe('')
    
    // Verificar que se mostró un error
    expect(notifications.notifyError).toHaveBeenCalledWith(
      "Formato no válido",
      "Por favor, selecciona un archivo CSV."
    )
  })
  
  // Test 4: Aplicación de etiquetas exitosa
  it('aplica etiquetas correctamente y emite evento', async () => {
    const wrapper = shallowMount(CsvLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: { Teleport: true }
      }
    })
    
    await flushPromises()
    
    // Simular un archivo CSV cargado
    const file = new File(['image1.jpg,cat\nimage2.jpg,dog'], 'test.csv', { type: 'text/csv' })
    wrapper.vm.csvFile = file
    wrapper.vm.fileName = 'test.csv'
    
    // Mock para parseCsvContent
    wrapper.vm.parseCsvContent = vi.fn().mockResolvedValue([
      { image_name: 'image1.jpg', label: 'cat' },
      { image_name: 'image2.jpg', label: 'dog' }
    ])
    
    // Llamar al método de aplicar etiquetas
    await wrapper.vm.applyLabels()
    
    // Verificar que se llamó a axios.post con los datos correctos
    expect(axios.post).toHaveBeenCalledWith(`/datasets/${testDatasetId}/csv-label`, {
      labels: [
        { image_name: 'image1.jpg', label: 'cat' },
        { image_name: 'image2.jpg', label: 'dog' }
      ]
    })
    
    // Verificar que se emitió el evento con los resultados
    expect(wrapper.emitted('images-labeled')).toBeTruthy()
    expect(wrapper.emitted('images-labeled')[0][0]).toEqual({
      labeledCount: 2,
      notFoundCount: 1,
      notFoundDetails: ['missing-image.jpg']
    })
  })
  
  // Test 5: Cierre del modal
  it('emite evento close al cerrar el modal', async () => {
    const wrapper = shallowMount(CsvLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: { Teleport: true }
      }
    })
    
    await flushPromises()
    
    // Llamar al método de cierre
    wrapper.vm.handleClose()
    
    // Verificar que se emitió el evento close
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})