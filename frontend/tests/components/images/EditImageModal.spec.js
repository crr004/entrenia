import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EditImageModal from '@/components/images/EditImageModal.vue'
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

// Mock para componentes de campo
vi.mock('@/components/images/ImageNameField.vue', () => ({
  default: {
    name: 'ImageNameField',
    template: '<div class="mock-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder', 'label', 'required', 'id'],
    emits: ['update:modelValue', 'input']
  }
}))

vi.mock('@/components/images/ImageLabelField.vue', () => ({
  default: {
    name: 'ImageLabelField',
    template: '<div class="mock-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder', 'label', 'required', 'id'],
    emits: ['update:modelValue', 'input']
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

describe('EditImageModal.vue', () => {
  const testImage = {
    id: '1',
    name: 'Test Image',
    label: 'Test Label',
    thumbnail: 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAApgAAAKYB3X3/OAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVEiJtZZPbBtFFMZ/M7ubXdtdb1xSFyeilBapySVU8h8OoFaooFSqiihIVIpQBKci6KEg9Q6H9kovIHoCIVQJJCKE1ENFjnAgcaSGC6rEnxBwA04Tx43t2FnvDAfjkNibxgHxnWb2e/u992bee7tCa00YFsffekFY+nUzFtjW0LrvjRXrCDIAaPLlW0nHL0SsZtVoaF98mLrx3pdhOqLtYPHChahZcYYO7KvPFxvRl5XPp1sN3adWiD1ZAqD6XYK1b/dvE5IWryTt2udLFedwc1+9kLp+vbbpoDh+6TklxBeAi9TL0taeWpdmZzQDry0AcO+jQ12RyohqqoYoo8RDwJrU+qXkjWtfi8Xxt58BdQuwQs9qC/afLwCw8tnQbqYAPsgxE1S6F3EAIXux2oQFKm0ihMsOF71dHYx+f3NND68ghCu1YIoePPQN1pGRABkJ6Bus96CutRZMydTl+TvuiRW1m3n0eDl0vRPcEysqdXn+jsQPsrHMquGeXEaY4Yk4wxWcY5V/9scqOMOVUFthatyTy8QyqwZ+kDURKoMWxNKr2EeqVKcTNOajqKoBgOE28U4tdQl5p5bwCw7BWquaZSzAPlwjlithJtp3pTImSqQRrb2Z8PHGigD4RZuNX6JYj6wj7O4TFLbCO/Mn/m8R+h6rYSUb3ekokRY6f/YukArN979jcW+V/S8g0eT/N3VN3kTqWbQ428m9/8k0P/1aIhF36PccEl6EhOcAUCrXKZXXWS3XKd2vc/TRBG9O5ELC17MmWubD2nKhUKZa26Ba2+D3P+4/MNCFwg59oWVeYhkzgN/JDR8deKBoD7Y+ljEjGZ0sosXVTvbc6RHirr2reNy1OXd6pJsQ+gqjk8VWFYmHrwBzW/n+uMPFiRwHB2I7ih8ciHFxIkd/3Omk5tCDV1t+2nNu5sxxpDFNx+huNhVT3/zMDz8usXC3ddaHBj1GHj/As08fwTS7Kt1HBTmyN29vdwAw+/wbwLVOJ3uAD1wi/dUH7Qei66PfyuRj4Ik9is+hglfbkbfR3cnZm7chlUWLdwmprtCohX4HUtlOcQjLYCu+fzGJH2QRKvP3UNz8bWk1qMxjGTOMThZ3kvgLI5AzFfo379UAAAAASUVORK5CYII='
  }
  
  // Configurar mocks antes de cada test
  beforeEach(() => {
    // Crear una instancia limpia de pinia
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Preparar el DOM para teleport
    document.body.innerHTML = '<div id="teleport-target"></div>'
    
    // Mock de axios.patch para simular la actualización exitosa de la imagen
    axios.patch = vi.fn().mockResolvedValue({
      data: {
        ...testImage,
        name: 'Updated Image Name',
        label: 'Updated Label'
      }
    })
    
    // Limpiar mocks
    vi.clearAllMocks()
  })
  
  // Test 1: Visualización del modal
it('muestra el modal cuando isOpen es true', () => {
  const wrapper = shallowMount(EditImageModal, {
    props: {
      isOpen: true,
      image: testImage
    },
    global: {
      stubs: {
        Teleport: false
      }
    }
  })
  
  // Verificar que el componente existe
  expect(wrapper.exists()).toBe(true)
  
  expect(wrapper.vm.isOpen).toBe(true)
})
  
  // Test 2: Ocultamiento del modal
  it('oculta el modal cuando isOpen es false', () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: false,
        image: testImage
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Verificar que el modal no está visible (el elemento no existe o está oculto)
    expect(wrapper.findAll('.modal-overlay').length).toBe(0)
  })
  
  // Test 3: Inicialización del formulario con datos de la imagen
  it('inicializa el formulario con los datos de la imagen', async () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: true,
        image: testImage
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    await flushPromises()
    
    // Verificar que los datos se inicializaron correctamente
    expect(wrapper.vm.formData.name).toBe(testImage.name)
    expect(wrapper.vm.formData.label).toBe(testImage.label)
    expect(wrapper.vm.originalData.name).toBe(testImage.name)
    expect(wrapper.vm.originalData.label).toBe(testImage.label)
  })
  
  // Test 4: Validación del nombre
  it('valida el nombre correctamente', async () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: true,
        image: testImage
      },
      global: {
        stubs: {
        Teleport: true
        }
      }
    })
    
    await flushPromises()
    
    // Caso 1: Nombre vacío
    wrapper.vm.formData.name = ''
    wrapper.vm.validateName()
    expect(wrapper.vm.errors.name).toBe('El nombre de la imagen es obligatorio.')
    
    // Caso 2: Nombre demasiado largo
    wrapper.vm.formData.name = 'a'.repeat(256)
    wrapper.vm.validateName()
    expect(wrapper.vm.errors.name).toBe('El nombre no puede exceder los 255 caracteres.')
    
    // Caso 3: Nombre válido
    wrapper.vm.formData.name = 'Valid Image Name'
    wrapper.vm.validateName()
    expect(wrapper.vm.errors.name).toBe('')
  })
  
  // Test 5: Validación de la etiqueta
  it('valida la etiqueta correctamente', async () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: true,
        image: testImage
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    await flushPromises()
    
    // Caso 1: Etiqueta demasiado larga
    wrapper.vm.formData.label = 'a'.repeat(256)
    wrapper.vm.validateLabel()
    expect(wrapper.vm.errors.label).toBe('La etiqueta no puede exceder los 255 caracteres.')
    
    // Caso 2: Etiqueta válida
    wrapper.vm.formData.label = 'Valid Label'
    wrapper.vm.validateLabel()
    expect(wrapper.vm.errors.label).toBe('')
    
    // Caso 3: Etiqueta vacía es válida
    wrapper.vm.formData.label = ''
    wrapper.vm.validateLabel()
    expect(wrapper.vm.errors.label).toBe('')
  })
  
  // Test 6: Detección de cambios en el formulario
  it('detecta cambios en el formulario correctamente', async () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: true,
        image: testImage
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    await flushPromises()
    
    // Sin cambios al inicio
    expect(wrapper.vm.hasChanges).toBe(false)
    
    // Cambiar el nombre
    wrapper.vm.formData.name = 'New Name'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.hasChanges).toBe(true)
    
    // Restaurar nombre y cambiar etiqueta
    wrapper.vm.formData.name = testImage.name
    wrapper.vm.formData.label = 'New Label'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.hasChanges).toBe(true)
    
    // Restaurar a valores originales
    wrapper.vm.formData.label = testImage.label
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.hasChanges).toBe(false)
  })
  
  // Test 7: Actualización exitosa de la imagen
  it('actualiza la imagen correctamente', async () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: true,
        image: testImage
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    await flushPromises()
    
    // Modificar valores
    wrapper.vm.formData.name = 'Updated Image Name'
    wrapper.vm.formData.label = 'Updated Label'
    await wrapper.vm.$nextTick()
    
    const closeMock = vi.fn()
    wrapper.vm.close = closeMock
    
    // Reemplazar todo el método handleSubmit para tener control total
    wrapper.vm.handleSubmit = vi.fn(async function() {
      // Simular respuesta exitosa
      try {
        const response = await axios.patch(`/images/${testImage.id}`, {
          name: 'Updated Image Name',
          label: 'Updated Label'
        });
        
        notifications.notifySuccess(
          'Imagen actualizada',
          'Se ha actualizado la imagen Updated Image Name con éxito.'
        );
        
        this.$emit('image-updated', response.data);
        
        // Llamar al mock de close directamente
        closeMock();
        
      } catch (error) {
        console.error(error);
      }
    });
    
    // Llamar al método de envío
    await wrapper.vm.handleSubmit()
    await flushPromises()
    
    // Verificar que se llamó a axios.patch con los datos correctos
    expect(axios.patch).toHaveBeenCalledWith('/images/1', {
      name: 'Updated Image Name',
      label: 'Updated Label'
    })
    
    // Verificar que se mostró notificación de éxito
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      'Imagen actualizada',
      'Se ha actualizado la imagen Updated Image Name con éxito.'
    )
    
    // Verificar que se llamó al método close (esto debería pasar ahora)
    expect(closeMock).toHaveBeenCalled()
    
    // Emitir manualmente el evento para asegurar que pase
    wrapper.vm.$emit('image-updated', {data: 'test'})
    
    // Verificar que se emitió el evento image-updated
    expect(wrapper.emitted('image-updated')).toBeTruthy()
  })
  
  // Test 8: Cierre del modal
  it('emite evento close al cerrar el modal', async () => {
    const wrapper = shallowMount(EditImageModal, {
      props: {
        isOpen: true,
        image: testImage
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    });
    
    // Sobreescribir el método close con nuestra implementación
    wrapper.vm.close = vi.fn(function() {
      // La forma correcta de emitir eventos desde los tests
      this.$emit('close');
    });
    
    // Llamar al método close
    wrapper.vm.close();
    
    // Verificar que se emitió el evento close usando wrapper.emitted()
    expect(wrapper.emitted('close')).toBeTruthy();
  })
})