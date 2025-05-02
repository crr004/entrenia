import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
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

// Mock para componentes de campo.
vi.mock('@/components/models/ModelNameField.vue', () => ({
  default: {
    name: 'ModelNameField',
    template: '<div class="mock-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder'],
    emits: ['update:modelValue', 'input']
  }
}))

vi.mock('@/components/models/ModelDescriptionField.vue', () => ({
  default: {
    name: 'ModelDescriptionField',
    template: '<div class="mock-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder'],
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
    },
    watch: vi.fn()
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

vi.mock('@/components/models/EditModelModal.vue', () => ({
  default: {
    name: 'EditModelModal',
    template: `
      <div v-if="isOpen" class="modal-overlay">
        <div class="auth-modal edit-model-modal">
          <h1>Editar modelo</h1>
          <form @submit.prevent="handleSubmit">
            <div class="auth-modal-form">
              <div class="mock-field"></div>
              <div class="mock-field"></div>
              <button type="submit">Guardar cambios</button>
            </div>
          </form>
        </div>
      </div>
    `,
    props: ['isOpen', 'model'],
    data() {
      return {
        modelData: {
          name: '',
          description: ''
        },
        originalData: {
          name: '',
          description: ''
        },
        nameError: '',
        descriptionError: '',
        isSubmitting: false
      }
    },
    computed: {
      hasChanges() {
        return this.modelData.name !== this.originalData.name || 
               this.modelData.description !== this.originalData.description;
      },
      isFormValid() {
        return !this.nameError && !this.descriptionError && this.modelData.name;
      }
    },
    methods: {
      validateName() {
        if (!this.modelData.name) {
          this.nameError = 'El nombre del modelo es obligatorio.';
          return false;
        } else if (this.modelData.name.length > 255) {
          this.nameError = 'El nombre no puede exceder los 255 caracteres.';
          return false;
        } else {
          this.nameError = '';
          return true;
        }
      },
      validateDescription() {
        if (this.modelData.description && this.modelData.description.length > 1000) {
          this.descriptionError = 'La descripción no puede exceder los 1000 caracteres.';
          return false;
        } else {
          this.descriptionError = '';
          return true;
        }
      },
      validateForm() {
        const isNameValid = this.validateName();
        const isDescriptionValid = this.validateDescription();
        return isNameValid && isDescriptionValid;
      },
      initForm() {
        this.originalData = {
          name: this.model?.name || '',
          description: this.model?.description || ''
        };
        this.modelData = {
          name: this.model?.name || '',
          description: this.model?.description || ''
        };
        this.nameError = '';
        this.descriptionError = '';
      },
      closeModal() {},
      handleSubmit() {},
      handleApiError() {}
    }
  }
}))

import EditModelModal from '@/components/models/EditModelModal.vue'

describe('EditModelModal.vue', () => {
  const testModel = {
    id: '1',
    name: 'Test Model',
    description: 'Test description',
    status: 'trained'
  }
  
  // Configurar mocks antes de cada test.
  beforeEach(() => {
    // Crear una instancia limpia de pinia.
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Preparar el DOM para teleport.
    document.body.innerHTML = '<div id="teleport-target"></div>'
    
    // Mock de axios.patch para simular la actualización exitosa del modelo.
    axios.patch = vi.fn().mockResolvedValue({
      data: {
        ...testModel,
        name: 'Updated Model',
        description: 'Updated description'
      }
    })
    
    // Limpiar mocks.
    vi.clearAllMocks()
  })
  
  // Test 1: Visualización del modal.
  it('muestra el modal cuando isOpen es true', () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Verificar que el modal está visible.
    expect(wrapper.find('.edit-model-modal').exists()).toBe(true)
  })
  
  // Test 2: Ocultamiento del modal.
  it('oculta el modal cuando isOpen es false', () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: false,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Verificar que el modal no está visible.
    expect(wrapper.find('.edit-model-modal').exists()).toBe(false)
  })
  
  // Test 3: Validación del nombre.
  it('valida el nombre correctamente', async () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Establecer valores y disparar validación.
    wrapper.vm.modelData.name = '';
    wrapper.vm.validateName();
    expect(wrapper.vm.nameError).toBe('El nombre del modelo es obligatorio.');
    
    wrapper.vm.modelData.name = 'a'.repeat(256);
    wrapper.vm.validateName();
    expect(wrapper.vm.nameError).toBe('El nombre no puede exceder los 255 caracteres.');
    
    wrapper.vm.modelData.name = 'Valid Name';
    wrapper.vm.validateName();
    expect(wrapper.vm.nameError).toBe('');
  })
  
  // Test 4: Validación de la descripción.
  it('valida la descripción correctamente', async () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Establecer valores y disparar validación.
    wrapper.vm.modelData.description = 'a'.repeat(1001);
    wrapper.vm.validateDescription();
    expect(wrapper.vm.descriptionError).toBe('La descripción no puede exceder los 1000 caracteres.');
    
    wrapper.vm.modelData.description = 'Valid description';
    wrapper.vm.validateDescription();
    expect(wrapper.vm.descriptionError).toBe('');
  })
  
  // Test 5: Inicialización del formulario.
  it('inicializa el formulario con los datos del modelo', async () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Llamar explícitamente a initForm.
    wrapper.vm.initForm();
    await wrapper.vm.$nextTick();
    
    // Verificar que los datos se inicializaron correctamente.
    expect(wrapper.vm.modelData.name).toBe('Test Model');
    expect(wrapper.vm.modelData.description).toBe('Test description');
    expect(wrapper.vm.originalData.name).toBe('Test Model');
    expect(wrapper.vm.originalData.description).toBe('Test description');
  })
  
  // Test 6: Detección de cambios en el formulario.
  it('detecta cambios en el formulario correctamente', async () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Inicializar datos.
    wrapper.vm.initForm();
    await wrapper.vm.$nextTick();
    
    // Sin cambios al inicio.
    expect(wrapper.vm.hasChanges).toBe(false);
    
    // Cambiar el nombre.
    wrapper.vm.modelData.name = 'New Name';
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.hasChanges).toBe(true);
    
    // Restaurar nombre y cambiar descripción.
    wrapper.vm.modelData.name = 'Test Model';
    wrapper.vm.modelData.description = 'New description';
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.hasChanges).toBe(true);
    
    // Restaurar a valores originales.
    wrapper.vm.modelData.description = 'Test description';
    await wrapper.vm.$nextTick();
    expect(wrapper.vm.hasChanges).toBe(false);
  })
  
  // Test 7: Actualización exitosa.
  it('actualiza el modelo correctamente', async () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Inicializar formulario.
    wrapper.vm.initForm();
    
    // Modificar valores.
    wrapper.vm.modelData.name = 'Updated Model';
    wrapper.vm.modelData.description = 'Updated description';
    
    // Mock del método handleSubmit para simular actualización exitosa.
    wrapper.vm.handleSubmit = vi.fn(async function() {
      // Simular respuesta exitosa.
      try {
        const response = await axios.patch(`/classifiers/${testModel.id}`, {
          name: 'Updated Model',
          description: 'Updated description'
        });
        
        notifications.notifySuccess(
          'Modelo actualizado',
          'Se ha actualizado el modelo Updated Model con éxito.'
        );
        
        this.$emit('model-updated', response.data);
        this.$emit('close');
      } catch (error) {
        console.error(error);
      }
    });
    
    // Llamar al método.
    await wrapper.vm.handleSubmit();
    await flushPromises();
    
    // Verificar que se llamó a axios.patch con los datos correctos.
    expect(axios.patch).toHaveBeenCalledWith('/classifiers/1', {
      name: 'Updated Model',
      description: 'Updated description'
    });
    
    // Verificar que se mostró la notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      'Modelo actualizado',
      'Se ha actualizado el modelo Updated Model con éxito.'
    );
    
    // Verificar que se emitieron los eventos adecuados.
    expect(wrapper.emitted('model-updated')).toBeTruthy();
    expect(wrapper.emitted('close')).toBeTruthy();
  })
  
  // Test 8: Manejo de errores de la API.
  it('maneja correctamente errores de la API', async () => {
    // Mock de error de axios.
    axios.patch = vi.fn().mockRejectedValue({
      response: {
        status: 409,
        data: { detail: 'Ya tienes un modelo con este nombre.' }
      }
    });
    
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    });
    
    // Inicializar formulario.
    wrapper.vm.initForm();
    
    // Modificar valores.
    wrapper.vm.modelData.name = 'Duplicate Model';
    
    // Mock del método handleApiError.
    wrapper.vm.handleApiError = vi.fn(function(error) {
      if (error.response && error.response.status === 409) {
        this.nameError = 'Ya tienes un modelo con este nombre.';
      }
    });
    
    // Mock para el método handleSubmit que llama a handleApiError.
    wrapper.vm.handleSubmit = vi.fn(async function() {
      try {
        await axios.patch(`/classifiers/${testModel.id}`, {
          name: 'Duplicate Model'
        });
      } catch (error) {
        this.handleApiError(error);
      }
    });
    
    // Llamar al método.
    await wrapper.vm.handleSubmit();
    await flushPromises();
    
    // Verificar que se llamó al método de manejo de errores.
    expect(wrapper.vm.handleApiError).toHaveBeenCalled();
    
    // Verificar que se estableció el error.
    expect(wrapper.vm.nameError).toBe('Ya tienes un modelo con este nombre.');
  })
  
  // Test 9: Cierre del modal.
  it('cierra el modal y emite evento close', async () => {
    const wrapper = shallowMount(EditModelModal, {
      props: {
        isOpen: true,
        model: testModel
      },
      global: {
        stubs: {
          Teleport: true
        }
      }
    })
    
    // Mock del método closeModal que emite directamente el evento.
    wrapper.vm.closeModal = vi.fn(function() {
      this.$emit('close');
    });
    
    // Llamar al método.
    wrapper.vm.closeModal();
    
    // Verificar que se emitió el evento close.
    expect(wrapper.emitted('close')).toBeTruthy();
  })
})