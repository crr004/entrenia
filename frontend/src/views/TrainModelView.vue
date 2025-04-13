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
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ModelNameField from '@/components/models/ModelNameField.vue';
import ModelDescriptionField from '@/components/models/ModelDescriptionField.vue';
import DatasetNameField from '@/components/datasets/DatasetNameField.vue';

const router = useRouter();
const authStore = useAuthStore();

const formData = ref({
  name: '',
  description: '',
  dataset_name: '',
  architecture: '',
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

    const response = await axios.post('/classifiers/', {
      name: formData.value.name,
      description: formData.value.description || null,
      dataset_name: formData.value.dataset_name,
      architecture: formData.value.architecture
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

/* Responsive */
@media (max-width: 768px) {
  .train-model-view {
    padding: 15px;
    padding-top: 75px;
  }
  
  h1 {
    font-size: 1.5rem;
  }
}
</style>