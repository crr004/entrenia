import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import TrainModelView from '@/views/TrainModelView.vue';

// Mocks.
import axios from 'axios';
import { useRouter, useRoute } from 'vue-router';
import { notifySuccess, notifyError } from '@/utils/notifications';


// Configuración de mocks.
vi.mock('axios');

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn()
  })),
  useRoute: vi.fn(() => ({
    query: {}
  }))
}));

vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}));

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'fake-token',
    setAuthHeader: vi.fn(),
    logout: vi.fn()
  }))
}));

vi.mock('@/components/models/ModelNameField.vue', () => ({
  default: {
    name: 'ModelNameField',
    template: '<div class="mock-model-name-field"><input v-model="modelValue" /></div>',
    props: ['modelValue', 'error', 'label'],
    emits: ['update:modelValue', 'input']
  }
}));

vi.mock('@/components/models/ModelDescriptionField.vue', () => ({
  default: {
    name: 'ModelDescriptionField',
    template: '<div class="mock-model-description-field"><textarea v-model="modelValue"></textarea></div>',
    props: ['modelValue', 'error'],
    emits: ['update:modelValue', 'input']
  }
}));

vi.mock('@/components/datasets/DatasetNameField.vue', () => ({
  default: {
    name: 'DatasetNameField',
    template: '<div class="mock-dataset-name-field"><input v-model="modelValue" /></div>',
    props: ['modelValue', 'error', 'label', 'placeholder'],
    emits: ['update:modelValue', 'input']
  }
}));

vi.mock('@/components/utils/HelpTooltip.vue', () => ({
  default: {
    name: 'HelpTooltip',
    template: '<div class="mock-tooltip"></div>',
    props: ['text', 'label']
  }
}));

describe('TrainModelView.vue', () => {
  let wrapper;
  let routerPushMock;
  const availableArchitectures = ['xception_mini', 'resnet50', 'efficientnetb3'];
  
  beforeEach(() => {
    // Resetear todos los mocks antes de cada test.
    vi.clearAllMocks();
    
    // Crear un mock específico para router.push.
    routerPushMock = vi.fn();
    vi.mocked(useRouter).mockReturnValue({
      push: routerPushMock
    });
    
    // Mock de respuesta para arquitecturas disponibles.
    axios.get.mockResolvedValue({
      data: availableArchitectures
    });
    
    // Montar el componente
    wrapper = mount(TrainModelView, {
      global: {
        stubs: {
          FontAwesomeIcon: true // Asegurarse de que FontAwesomeIcon esté correctamente stubeado.
        }
      }
    });
  });
  
  // Test 1: Renderización del componente.
  it('renderiza correctamente el componente', async () => {
    // Esperar a que se resuelvan las promesas.
    await wrapper.vm.$nextTick();
    
    // Verificar elementos clave del formulario.
    expect(wrapper.find('h1').text()).toBe('Entrenar nuevo modelo');
    expect(wrapper.find('.mock-model-name-field').exists()).toBe(true);
    expect(wrapper.find('.mock-model-description-field').exists()).toBe(true);
    expect(wrapper.find('.mock-dataset-name-field').exists()).toBe(true);
    expect(wrapper.find('#architecture-select').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });
  
  // Test 2: Carga de arquitecturas al montar.
  it('carga las arquitecturas disponibles al montar el componente', async () => {
    // Esperar a que se resuelvan las promesas.
    await wrapper.vm.$nextTick();
    
    // Verificar que se llamó a la API para obtener arquitecturas.
    expect(axios.get).toHaveBeenCalledWith('/classifiers/architectures');
    
    // Verificar el array de arquitecturas.
    expect(wrapper.vm.architectures).toEqual(
      expect.arrayContaining(availableArchitectures)
    );
  });
  
  // Test 3: Validación de campos obligatorios.
  it('valida correctamente los campos obligatorios', async () => {
    // Inicialmente el botón debe estar deshabilitado.
    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined();
    
    // Simular llenado del formulario.
    wrapper.vm.formData.name = 'Test Model';
    await wrapper.vm.validateName('Test Model');
    
    wrapper.vm.formData.dataset_name = 'test_dataset';
    await wrapper.vm.validateDataset('test_dataset');
    
    wrapper.vm.formData.architecture = 'resnet50';
    await wrapper.vm.validateArchitecture();
    
    // Disparar la actualización del DOM.
    await wrapper.vm.$nextTick();
    
    // El formulario debería ser válido ahora.
    expect(wrapper.vm.isFormValid).toBe(true);
  });
  
  // Test 4: Envío del formulario.
  it('envía correctamente el formulario con los datos proporcionados', async () => {
    // Mock de respuesta exitosa.
    axios.post.mockResolvedValue({ data: { id: '123' } });
    
    // Llenar formulario.
    wrapper.vm.formData.name = 'Test Model';
    wrapper.vm.formData.description = 'Test Description';
    wrapper.vm.formData.dataset_name = 'test_dataset';
    wrapper.vm.formData.architecture = 'resnet50';
    
    // Validar campos.
    await wrapper.vm.validateName('Test Model');
    await wrapper.vm.validateDescription('Test Description');
    await wrapper.vm.validateDataset('test_dataset');
    await wrapper.vm.validateArchitecture();
    
    // Forzar que el formulario sea válido.
    wrapper.vm.datasetExists = true;
    await wrapper.vm.$nextTick();
    
    // Enviar formulario.
    await wrapper.vm.submitForm();
    
    // Verificar que se envió la solicitud a la API.
    expect(axios.post).toHaveBeenCalledWith('/classifiers/', {
      name: 'Test Model',
      description: 'Test Description',
      dataset_name: 'test_dataset',
      architecture: 'resnet50',
      model_parameters: expect.objectContaining({
        learning_rate: expect.any(Number),
        epochs: expect.any(Number),
        batch_size: expect.any(Number),
        validation_split: expect.any(Number)
      })
    });
    
    // Verificar notificación de éxito.
    expect(notifySuccess).toHaveBeenCalled();
    
    // Verificar que router.push fue llamado con la ruta correcta.
    expect(routerPushMock).toHaveBeenCalledWith('/my-models');
  });
  
  // Test 5: Manejo de errores al enviar el formulario.
  it('maneja correctamente los errores al enviar el formulario', async () => {
    // Mock de respuesta de error 404 (dataset no encontrado).
    const errorResponse = {
      response: {
        status: 404,
        data: { detail: 'Dataset not found' }
      }
    };
    axios.post.mockRejectedValue(errorResponse);
    
    // Llenar formulario.
    wrapper.vm.formData.name = 'Test Model';
    wrapper.vm.formData.dataset_name = 'nonexistent_dataset';
    wrapper.vm.formData.architecture = 'resnet50';
    
    // Validar campos.
    await wrapper.vm.validateName('Test Model');
    await wrapper.vm.validateDataset('nonexistent_dataset');
    await wrapper.vm.validateArchitecture();
    
    // Forzar que el formulario sea válido para la prueba.
    wrapper.vm.datasetExists = true;
    await wrapper.vm.$nextTick();
    
    // Enviar formulario.
    await wrapper.vm.submitForm();
    
    // Verificar que se actualizó el error del dataset.
    expect(wrapper.vm.errors.dataset_name).toBeTruthy();
    expect(wrapper.vm.datasetExists).toBe(false);
  });
  
  // Test 6: Actualización de la tasa de aprendizaje.
  it('actualiza correctamente la tasa de aprendizaje al mover el slider', async () => {
    // Valor inicial.
    const initialLearningRate = wrapper.vm.formData.model_parameters.learning_rate;
    
    // Cambiar valor del slider.
    wrapper.vm.logSliderValue = 0;  // Valor mínimo.
    wrapper.vm.updateLearningRate();
    
    // Verificar que cambió la tasa de aprendizaje.
    expect(wrapper.vm.formData.model_parameters.learning_rate).not.toBe(initialLearningRate);
    expect(wrapper.vm.formData.model_parameters.learning_rate).toBeCloseTo(0.00001);
    
    // Cambiar a valor máximo.
    wrapper.vm.logSliderValue = 100;
    wrapper.vm.updateLearningRate();
    expect(wrapper.vm.formData.model_parameters.learning_rate).toBeCloseTo(0.1);
  });
  
  // Test 7: Carga de dataset desde la ruta.
  it('carga un dataset desde los parámetros de la ruta', async () => {
    wrapper.unmount();
    
    // Simular que la ruta tiene un parámetro dataset.
    const mockRouteWithDataset = {
      query: { dataset: 'route_dataset' }
    };
    
    // Establecer el mock antes de montar el componente.
    vi.mocked(useRoute).mockReturnValue(mockRouteWithDataset);
    
    // Volver a montar el componente para que use la nueva ruta mock.
    const newWrapper = mount(TrainModelView);
    
    // Esperar a que se resuelvan las promesas y se procese el ciclo de vida.
    await newWrapper.vm.$nextTick();
    await newWrapper.vm.$nextTick(); // A veces se necesita un tick adicional.
    
    // Verificar que el método de carga fue llamado con el valor correcto.
    expect(newWrapper.vm.formData.dataset_name).toBe('route_dataset');
  });
  
  // Test 8: Formateo de la tasa de aprendizaje.
  it('formatea correctamente la tasa de aprendizaje', () => {
    expect(wrapper.vm.formatLearningRate(0.001)).toBe('0.001');
    expect(wrapper.vm.formatLearningRate(0.00100)).toBe('0.001');
    expect(wrapper.vm.formatLearningRate(1)).toBe('1');
    expect(wrapper.vm.formatLearningRate(0.00001)).toBe('0.00001');
  });
  
  // Test 9: Obtención de etiqueta de arquitectura.
  it('obtiene correctamente las etiquetas de arquitecturas', () => {
    expect(wrapper.vm.getArchitectureLabel('xception_mini')).toBe('Xception Mini');
    expect(wrapper.vm.getArchitectureLabel('resnet50')).toBe('ResNet-50');
    expect(wrapper.vm.getArchitectureLabel('efficientnetb3')).toBe('EfficientNet-B3');
    expect(wrapper.vm.getArchitectureLabel('unknown_arch')).toBe('unknown_arch');
  });
  
  // Test 10: Manejo de errores en la API.
  it('maneja correctamente diferentes tipos de errores', async () => {
    
    // Error 401 - verifica que se llama a router.push('/').
    const unauthorizedError = {
      response: {
        status: 401,
        data: { detail: 'Not authenticated' }
      }
    };
    await wrapper.vm.handleApiError(unauthorizedError);
    // Verificar que router.push fue llamado con '/'.
    expect(routerPushMock).toHaveBeenCalledWith('/');
    vi.clearAllMocks();
    
    // El resto de los errores se puede mantener igual.
    // Error 400.
    const badRequestError = {
      response: {
        status: 400,
        data: { detail: 'Invalid architecture' }
      }
    };
    await wrapper.vm.handleApiError(badRequestError);
    expect(notifyError).toHaveBeenCalledWith("Arquitectura no válida", expect.any(String));
    vi.clearAllMocks();
    
    // Error 409 (conflicto de nombre).
    const conflictError = {
      response: {
        status: 409,
        data: { detail: 'Model with this name already exists' }
      }
    };
    await wrapper.vm.handleApiError(conflictError);
    expect(notifyError).toHaveBeenCalledWith("Nombre duplicado", expect.any(String));
  });
});