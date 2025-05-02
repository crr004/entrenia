import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ManualLabelingModal from '@/components/images/ManualLabelingModal.vue'
import * as notifications from '@/utils/notifications'
import axios from 'axios'

// Mock de las funciones de notificación.
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock de axios.
vi.mock('axios')

// Mock del router.
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock para FontAwesome.
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

// Mock para ImageLabelField.
vi.mock('@/components/images/ImageLabelField.vue', () => ({
  default: {
    name: 'ImageLabelField',
    template: '<div class="mock-label-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder', 'label', 'id', 'required'],
    emits: ['update:modelValue', 'input']
  }
}))

// Mock para Teleport.
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

// Mock para el store de Auth.
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    token: 'fake-token',
    setAuthHeader: vi.fn(),
    logout: vi.fn()
  })
}))

describe('ManualLabelingModal.vue', () => {
  // Datos de prueba.
  const testDatasetId = '123'
  const unlabeledImagesResponse = {
    images: [
      { id: '1', name: 'imagen1.jpg', thumbnail: 'base64data1' },
      { id: '2', name: 'imagen2.jpg', thumbnail: 'base64data2' },
      { id: '3', name: 'imagen3.jpg', thumbnail: 'base64data3' }
    ]
  }

  // Configurar mocks antes de cada test.
  beforeEach(() => {
    // Preparar el DOM para teleport.
    document.body.innerHTML = '<div id="teleport-target"></div>'
    
    // Mock de axios.get para obtener imágenes sin etiquetar.
    axios.get = vi.fn().mockResolvedValue({
      data: unlabeledImagesResponse
    })
    
    // Mock de axios.patch para actualizar etiqueta.
    axios.patch = vi.fn().mockResolvedValue({
      data: { success: true }
    })
    
    // Limpiar mocks.
    vi.clearAllMocks()
  })
  
  // Test 1: Visualización del modal.
  it('muestra el modal cuando isOpen es true y carga imágenes sin etiquetar', async () => {
    // Asegurarnos que el mock de axios.get está configurado correctamente.
    axios.get.mockClear();
    axios.get.mockResolvedValue({
      data: unlabeledImagesResponse
    });

    const wrapper = mount(ManualLabelingModal, {
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
    
    // Llamar manualmente a loadUnlabeledImages para asegurar que se ejecuta.
    await wrapper.vm.loadUnlabeledImages();
    
    // Esperar a que se resuelvan todas las promesas.
    await flushPromises();
    
    // Verificar que el componente existe.
    expect(wrapper.exists()).toBe(true);
    
    // Verificar que la prop isOpen se pasó correctamente.
    expect(wrapper.props().isOpen).toBe(true);
    
    // Verificar que se llamó a axios.get con la URL correcta.
    expect(axios.get).toHaveBeenCalledWith(`/datasets/${testDatasetId}/unlabeled-images`);
    
    // Verificar que se cargaron las imágenes sin etiquetar.
    expect(wrapper.vm.unlabeledImages.length).toBe(3);
    expect(wrapper.vm.currentIndex).toBe(0);
    expect(wrapper.vm.totalImages).toBe(3);
  });
  
  // Test 2: Navegación entre imágenes.
  it('permite navegar entre imágenes con los botones de navegación', async () => {
    const wrapper = mount(ManualLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true
        }
      }
    })
    
    // Establecer manualmente el estado para simular imágenes cargadas.
    wrapper.vm.isLoading = false
    wrapper.vm.unlabeledImages = unlabeledImagesResponse.images
    await wrapper.vm.$nextTick()
    
    // Verificar posición inicial.
    expect(wrapper.vm.currentIndex).toBe(0)
    
    // Simular navegación llamando directamente a los métodos.
    wrapper.vm.skipImage()
    await wrapper.vm.$nextTick()
    
    // Verificar que se avanzó a la siguiente imagen.
    expect(wrapper.vm.currentIndex).toBe(1)
    
    // Simular retroceso.
    wrapper.vm.goBack()
    await wrapper.vm.$nextTick()
    
    // Verificar que se retrocedió a la imagen anterior.
    expect(wrapper.vm.currentIndex).toBe(0)
  })
  
  // Test 3: Etiquetar imagen y continuar.
  it('etiqueta una imagen y avanza a la siguiente', async () => {
    const wrapper = mount(ManualLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true
        }
      }
    })
    
    // Establecer manualmente el estado para simular imágenes cargadas.
    wrapper.vm.isLoading = false
    wrapper.vm.unlabeledImages = unlabeledImagesResponse.images
    await wrapper.vm.$nextTick()
    
    // Establecer valor de etiqueta.
    wrapper.vm.labelInput = 'gato'
    
    // Llamar directamente al método submitLabel.
    await wrapper.vm.submitLabel()
    
    // Verificar que se llamó a axios.patch con los datos correctos.
    expect(axios.patch).toHaveBeenCalledWith('/images/1', {
      label: 'gato'
    })
    
    // Verificar que se incrementó el contador de etiquetas.
    expect(wrapper.vm.labeledCount).toBe(1)
    expect(wrapper.vm.hasChanges).toBe(true)
  })
  
  // Test 4: Finalizar etiquetado.
  it('emite evento al finalizar el etiquetado', async () => {
    const wrapper = mount(ManualLabelingModal, {
      props: {
        isOpen: true,
        datasetId: testDatasetId
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true
        }
      }
    })
    
    // Establecer manualmente el estado para simular imágenes cargadas.
    wrapper.vm.isLoading = false
    wrapper.vm.unlabeledImages = unlabeledImagesResponse.images
    wrapper.vm.hasChanges = true
    wrapper.vm.labeledCount = 1
    await wrapper.vm.$nextTick()
    
    // Llamar directamente al método handleFinishLabeling.
    await wrapper.vm.handleFinishLabeling()
    
    // Verificar que se emitió el evento 'close'.
    expect(wrapper.emitted('close')).toBeTruthy()
    
    // Verificar que se emitió el evento 'images-labeled' con el contador correcto.
    expect(wrapper.emitted('images-labeled')).toBeTruthy()
    expect(wrapper.emitted('images-labeled')[0][0]).toEqual({
      labeledCount: 1
    })
    
    // Verificar que se mostró la notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      'Etiquetado finalizado',
      expect.stringContaining('Has etiquetado 1')
    )
  })
  
  // Test 5: Manejo de errores.
  it('muestra una notificación de error cuando falla la carga de imágenes', async () => {
    // Mock de error de axios.
    axios.get.mockClear();
    axios.get.mockRejectedValue({
      response: {
        status: 404,
        data: { detail: 'Dataset not found' }
      }
    });
    
    // Limpiar mocks de notificaciones.
    notifications.notifyError.mockClear();
    
    const wrapper = mount(ManualLabelingModal, {
      props: {
        isOpen: true,
        datasetId: 'invalid-id'
      },
      global: {
        stubs: {
          Teleport: false
        }
      }
    });
    
    // Llamar manualmente al método que carga las imágenes.
    try {
      await wrapper.vm.loadUnlabeledImages();
    } catch (error) {
      // Ignorar el error, solo se quiere comprobar la notificación.
    }
    
    // Esperar a que se resuelvan todas las promesas.
    await flushPromises();
    
    // Verificar que se llamó a la función de notificación de error.
    expect(notifications.notifyError).toHaveBeenCalledWith(
      'Imagen o conjunto no encontrado',
      'La imagen o el conjunto que intentas etiquetar no existe o ha sido eliminado.'
    );
  });
})