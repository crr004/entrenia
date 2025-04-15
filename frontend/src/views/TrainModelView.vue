<template>
  <div class="train-model-view">
    <div class="back-link">
      <router-link to="/my-models" class="back-button">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
        <span>Volver a Mis modelo de clasificación de imágenes</span>
      </router-link>
    </div>
    <h1>Entrenar nuevo modelo</h1>
    <form @submit.prevent="submitForm" class="train-model-form">
      <ModelNameField 
        v-model="formData.name"
        :error="errors.name"
        @input="validateName"
        label="Nombre del modelo*"
        ref="modelNameFieldRef"
      />
      <ModelDescriptionField
        v-model="formData.description"
        :error="errors.description"
        @input="validateDescription"
      />
      <DatasetNameField 
        v-model="formData.dataset_name"
        :error="errors.dataset_name"
        @input="validateDataset"
        label="Conjunto de imágenes*"
        placeholder="Nombre del conjunto de imágenes a utilizar"
      />
      <div class="form-field">
        <label for="architecture-select">
          Arquitectura
          <span class="required-asterisk">*</span>
        </label>
        <div class="input-container">
          <div class="input-icon">
            <font-awesome-icon :icon="['fas', 'microchip']" />
          </div>
          <select 
            id="architecture-select" 
            v-model="formData.architecture"
            class="text-input has-icon"
            :class="{ 'input-error': errors.architecture }"
            @change="validateArchitecture"
          >
            <option value="" disabled>Selecciona una arquitectura</option>
            <option v-for="arch in architectures" :key="arch" :value="arch">
              {{ getArchitectureLabel(arch) }}
            </option>
          </select>
        </div>
        <span v-if="errors.architecture" class="error">{{ errors.architecture }}</span>
        <span v-else class="hint">La arquitectura determina el tipo de red neuronal que se utilizará para el modelo.</span>
      </div>
      <div v-if="formData.architecture" class="training-parameters">
        <h3>Parámetros de entrenamiento</h3>
        <div class="param-slider">
          <div class="param-header">
            <div class="param-label">
              <label for="learning-rate">Tasa de aprendizaje</label>
              <HelpTooltip 
                text="Controla cuánto cambian los pesos de la red en cada paso. Valores más pequeños suelen dar resultados más precisos pero requieren más tiempo de entrenamiento."
                label="tasa de aprendizaje"
              />
            </div>
            <span class="param-value">{{ formatLearningRate(formData.model_parameters.learning_rate) }}</span>
          </div>
          <input 
            type="range" 
            id="learning-rate" 
            v-model="logSliderValue" 
            min="0" 
            max="100" 
            step="1"
            class="slider"
            @input="updateLearningRate"
          >
          <div class="param-range">
            <span>0.00001</span>
            <span>0.1</span>
          </div>
        </div>
        <div class="param-slider">
          <div class="param-header">
            <div class="param-label">
              <label for="epochs">Épocas</label>
              <HelpTooltip 
                text="Número de veces que el modelo procesará todo el conjunto de datos. Más épocas pueden mejorar los resultados pero también aumentar el riesgo de sobreajuste."
                label="épocas"
              />
            </div>
            <span class="param-value">{{ formData.model_parameters.epochs }}</span>
          </div>
          <input 
            type="range" 
            id="epochs" 
            v-model.number="formData.model_parameters.epochs" 
            min="1" 
            max="200" 
            step="1"
            class="slider"
          >
          <div class="param-range">
            <span>1</span>
            <span>200</span>
          </div>
        </div>
        <div class="param-slider">
          <div class="param-header">
            <div class="param-label">
              <label for="batch-size">Tamaño del lote</label>
              <HelpTooltip 
                text="Número de imágenes procesadas antes de actualizar los pesos. Valores más altos pueden acelerar el entrenamiento pero pueden reducir la capacidad de generalización del modelo."
                label="tamaño del lote"
              />
            </div>
            <span class="param-value">{{ formData.model_parameters.batch_size }}</span>
          </div>
          <input 
            type="range" 
            id="batch-size" 
            v-model.number="formData.model_parameters.batch_size" 
            :min="8" 
            :max="256" 
            :step="8"
            class="slider"
          >
          <div class="param-range">
            <span>8</span>
            <span>256</span>
          </div>
        </div>
        <div class="param-slider">
          <div class="param-header">
            <div class="param-label">
              <label for="validation-split">División de entrenamiento</label>
              <HelpTooltip 
                text="Porcentaje de datos utilizados para entrenar el modelo (el resto se usa para validación)."
                label="división de entrenamiento"
              />
            </div>
            <span class="param-value">{{ (formData.model_parameters.train_split * 100).toFixed(0) }}%</span>
          </div>
          <input 
            type="range" 
            id="validation-split" 
            v-model.number="formData.model_parameters.train_split" 
            min="0.5" 
            max="0.95" 
            step="0.01"
            class="slider"
          >
          <div class="param-range">
            <span>50%</span>
            <span>95%</span>
          </div>
        </div>
      </div>
      <button 
        type="submit" 
        class="app-button"
        :disabled="isSubmitting || !isFormValid"
      >
        <font-awesome-icon v-if="isSubmitting" :icon="['fas', 'spinner']" spin class="button-icon" />
        <font-awesome-icon v-else :icon="['fas', 'robot']" class="button-icon" />
        {{ isSubmitting ? '' : 'Entrenar modelo' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ModelNameField from '@/components/models/ModelNameField.vue';
import ModelDescriptionField from '@/components/models/ModelDescriptionField.vue';
import DatasetNameField from '@/components/datasets/DatasetNameField.vue';
import HelpTooltip from '@/components/utils/HelpTooltip.vue';

const router = useRouter();
const authStore = useAuthStore();

// Para la escala logarítmica del learning rate.
const logSliderValue = ref(50); // Valor inicial en el medio (corresponde a ~0.001).

const formData = ref({
  name: '',
  description: '',
  dataset_name: '',
  architecture: '',
  model_parameters: {
    learning_rate: 0.001,
    epochs: 20,
    batch_size: 32,
    train_split: 0.8
  }
});

const errors = ref({
  name: '',
  description: '',
  dataset_name: '',
  architecture: '',
});

const architectures = ref([]);
const isSubmitting = ref(false);
const datasetExists = ref(true);

const modelNameFieldRef = ref(null);

const isFormValid = computed(() => {
  return (
    formData.value.name && 
    formData.value.dataset_name &&
    formData.value.architecture &&
    !errors.value.name &&
    !errors.value.description &&
    !errors.value.dataset_name &&
    !errors.value.architecture &&
    datasetExists.value
  );
});

const validateName = (value) => {
  if (!value || value.trim() === '') {
    errors.value.name = 'El nombre es obligatorio.';
  } else if (value.length < 1) {
    errors.value.name = 'El nombre debe tener al menos 1 caracter.';
  } else if (value.length > 255) {
    errors.value.name = 'El nombre no puede superar los 255 caracteres.';
  } else {
    errors.value.name = '';
  }
};

const validateDescription = (value) => {
  if (value && value.length > 1000) {
    errors.value.description = 'La descripción no puede superar los 1000 caracteres.';
  } else {
    errors.value.description = '';
  }
};

const validateDataset = async (value) => {
  if (!value || value.trim() === '') {
    errors.value.dataset_name = 'Debes especificar un conjunto de imágenes.';
    datasetExists.value = false;
  } else {
    errors.value.dataset_name = '';
    datasetExists.value = true;
  }
};

const validateArchitecture = () => {
  if (!formData.value.architecture) {
    errors.value.architecture = 'Debes seleccionar una arquitectura.';
  } else {
    errors.value.architecture = '';
  }
};

const getArchitectureLabel = (architecture) => {
  const architectureLabels = {
    'xception_mini': 'Xception Mini',
    'resnet18': 'ResNet-18',
    'resnet34': 'ResNet-34',
    'resnet50': 'ResNet-50',
    'mobilenet': 'MobileNet',
    'efficientnet': 'EfficientNet'
  };
  
  return architectureLabels[architecture] || architecture;
};

const fetchArchitectures = async () => {
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    const response = await axios.get('/classifiers/architectures');
    architectures.value = response.data;
  } catch (error) {
    console.error('Error fetching architectures: ', error);
    handleApiError(error);
  }
};

// Convertir el valor del slider a learning rate (escala logarítmica).
const updateLearningRate = () => {
  // Convertir de 0-100 a 0.00001-0.1 en escala logarítmica.
  const min = Math.log10(0.00001);
  const max = Math.log10(0.1);
  const scale = (max - min) / 100;
  
  formData.value.model_parameters.learning_rate = 
    Math.pow(10, min + scale * logSliderValue.value);
};

const formatLearningRate = (value) => {
  // Primero convertir a string con suficientes decimales.
  let strValue = value.toFixed(8);
  
  // Eliminar ceros a la derecha.
  strValue = strValue.replace(/\.?0+$/, '');
  
  // Si termina con punto, se eliminar.
  if (strValue.endsWith('.')) {
    strValue = strValue.slice(0, -1);
  }
  
  return strValue;
};

// Inicializar el valor del slider basado en el learning rate inicial.
onMounted(() => {
  const min = Math.log10(0.00001);
  const max = Math.log10(0.1);
  const scale = (max - min) / 100;
  
  logSliderValue.value = Math.round(
    (Math.log10(formData.value.model_parameters.learning_rate) - min) / scale
  );
});

const submitForm = async () => {
  // Validar todos los campos.
  validateName(formData.value.name);
  validateDescription(formData.value.description);
  await validateDataset(formData.value.dataset_name);
  validateArchitecture();
  
  if (!isFormValid.value) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    // Convertir el train_split al formato validation_split que espera el backend.
    const validation_split = 1 - formData.value.model_parameters.train_split;
    
    // Asegurar que los valores numéricos son números, no strings.
    const model_parameters = {
      learning_rate: Number(formData.value.model_parameters.learning_rate),
      epochs: Number(formData.value.model_parameters.epochs),
      batch_size: Number(formData.value.model_parameters.batch_size),
      validation_split: Number(validation_split)
    };

    const response = await axios.post('/classifiers/', {
      name: formData.value.name,
      description: formData.value.description || null,
      dataset_name: formData.value.dataset_name,
      architecture: formData.value.architecture,
      model_parameters: model_parameters
    });
    
    notifySuccess("Modelo en entrenamiento", 
    `El modelo ${formData.value.name} se ha creado y está siendo entrenado.`
    );
    
    // Redireccionar a la vista de modelos.
    router.push('/my-models');
    
  } catch (error) {
    console.error('Error creating classifier: ', error);
    handleApiError(error);
  } finally {
    isSubmitting.value = false;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;

    console.error("Error response: ", data);
    
    switch (status) {
      case 400:
        if (data.detail && data.detail.includes('architecture')) {
          notifyError("Arquitectura no válida",
          "La arquitectura seleccionada no es válida.");
        } else {
          notifyError("Formulario inválido",
          "Revisa los campos del formulario");
        }
        break;
      case 401:
        router.push('/');
        break;
      case 403:
        if (data.detail && data.detail.includes("credentials")) {
          notifyInfo("Sesión expirada", 
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else if (data.detail && data.detail.includes("privileges")) {
          notifyError("Acceso denegado", 
          "No tienes permisos para realizar esta acción.");
        } else {
          notifyError("Acceso denegado", 
            "No tienes permiso para realizar esta acción.");
        }
        break;
      case 404:
        errors.value.dataset_name = 'Este conjunto de imágenes no existe en tu biblioteca.';
        datasetExists.value = false;
        break;
      case 409:
        notifyError("Nombre duplicado",
        "Ya tienes un modelo con ese nombre");
        break;
      default:
        notifyError('Error en el servidor',
        'No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.');
        break;
    }
  } else if (error.request) {
    notifyError("Error de conexión",
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado",
    "Ha ocurrido un problema.");
  }
};

onMounted(async () => {
  // Cargar arquitecturas disponibles.
  await fetchArchitectures();
  
  // Enfocar el campo de nombre del modelo después de renderizar.
  await nextTick(() => {
    const inputElement = modelNameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  });
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/form_fields.css"></style>
<style scoped>
.train-model-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  padding-top: 90px;
  padding-bottom: 40px;
}

/* Botón (link) de retorno */
.back-link {
  margin-bottom: 15px;
}

.back-button {
  display: flex;
  align-items: center;
  color: #555;
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.2s;
}

.back-button:hover {
  color: rgb(34, 134, 141);
}

.back-button svg {
  margin-right: 6px;
}

h1 {
  color: #333;
  margin-bottom: 25px;
  font-size: 1.8rem;
}

h3 {
  font-size: 1.2rem;
  color: #333;
  margin-bottom: 15px;
  font-weight: 500;
}

.train-model-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.button-icon {
  margin-right: 8px;
}

.hint {
  display: block;
  color: #757575;
  font-size: 12px;
  margin-top: 6px;
  text-align: left;
}

/* Estilos para el select de arquitectura */
select.text-input {
  width: 100%;
  padding: 10px 12px;
  padding-left: 40px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 16px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  background-color: #f9f9f9;
  color: black;
  appearance: auto;
}

select.text-input:focus {
  border-color: black;
  outline: none;
  box-shadow: 0 0 0 2px rgba(34, 134, 141, 0.2);
}

select.text-input.input-error {
  border-color: #e53935;
  box-shadow: 0 0 0 2px rgba(229, 57, 53, 0.1);
}

/* Estilos para parámetros de entrenamiento */
.training-parameters {
  background: transparent;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid rgba(226, 215, 190, 0.7);
  margin-top: 10px;
  backdrop-filter: blur(2px);
}

.training-parameters h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.param-slider {
  margin-bottom: 20px;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.param-label {
  display: flex;
  align-items: baseline;
}

.param-header label {
  font-weight: 500;
  color: #444;
  margin-right: 2px;
}

.param-value {
  background-color: rgba(224, 229, 235, 0.8);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
}

.slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 5px;
  background: #d3d3d3;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgb(34, 134, 141);
  cursor: pointer;
  transition: all 0.2s;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgb(34, 134, 141);
  cursor: pointer;
  transition: all 0.2s;
}

.slider::-webkit-slider-thumb:hover {
  background: rgb(24, 96, 100);
  box-shadow: 0 0 5px rgba(34, 134, 141, 0.5);
}

.slider::-moz-range-thumb:hover {
  background: rgb(24, 96, 100);
  box-shadow: 0 0 5px rgba(34, 134, 141, 0.5);
}

.param-range {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #777;
  margin-top: 6px;
}

/* Responsive */
@media (max-width: 768px) {
  .train-model-view {
    padding: 15px;
    padding-top: 75px;
  }
  
  h1 {
    font-size: 1.5rem;
  }

  .training-parameters {
    padding: 15px;
  }
}
</style>