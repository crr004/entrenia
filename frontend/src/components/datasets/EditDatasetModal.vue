<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal edit-dataset-modal">
        <h1>Editar conjunto de imágenes</h1>
        <button class="close-modal-button" @click="closeModal">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="signup-body" @submit.prevent="handleSubmit">
          <div class="auth-modal-form">
            <DatasetNameField
              v-model="datasetData.name"
              :error="nameError"
              @input="validateName"
              ref="datasetNameFieldRef"
            />
            <DatasetDescriptionField
              v-model="datasetData.description"
              :error="descriptionError"
              @input="validateDescription"
            />
            <button 
              type="submit" 
              class="app-button" 
              :disabled="isSubmitting || !isFormValid || !hasChanges"
            >
              <span v-if="!isSubmitting">
                Guardar cambios
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'spinner']" />
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import DatasetNameField from '@/components/datasets/DatasetNameField.vue';
import DatasetDescriptionField from '@/components/datasets/DatasetDescriptionField.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  dataset: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['close', 'dataset-updated']);

const isSubmitting = ref(false);
const nameError = ref('');
const descriptionError = ref('');
const datasetNameFieldRef = ref(null);
const originalData = ref({});

const authStore = useAuthStore();

const router = useRouter();

const datasetData = ref({
  name: '',
  description: ''
});

// Foco en el campo de nombre del conjunto de imágenes al abrir el modal.
watch([() => props.isOpen, () => props.dataset], async ([newIsOpen, newDataset]) => {
  if (newIsOpen && newDataset) {
    initForm();
    await nextTick();
    const inputElement = datasetNameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
}, { immediate: true });

// Verificar si hay cambios respecto a los datos originales.
const hasChanges = computed(() => {
  return datasetData.value.name !== originalData.value.name || 
         datasetData.value.description !== originalData.value.description;
});

const isFormValid = computed(() => {
  return !nameError.value && !descriptionError.value && datasetData.value.name;
});

const validateName = () => {
  if (!datasetData.value.name) {
    nameError.value = 'El nombre del conjunto es obligatorio.';
    return false;
  } else if (datasetData.value.name.length < 1) {
    nameError.value = 'El nombre debe tener al menos 1 carácter.';
    return false;
  } else if (datasetData.value.name.length > 255) {
    nameError.value = 'El nombre no puede exceder los 255 caracteres.';
    return false;
  } else {
    nameError.value = '';
    return true;
  }
};

const validateDescription = () => {
  if (datasetData.value.description && datasetData.value.description.length > 1000) {
    descriptionError.value = 'La descripción no puede exceder los 1000 caracteres.';
    return false;
  } else {
    descriptionError.value = '';
    return true;
  }
};

const validateForm = () => {
  const isNameValid = validateName();
  const isDescriptionValid = validateDescription();
  return isNameValid && isDescriptionValid;
};

const initForm = () => {
  // Guardar una copia de los datos originales (se pasan desde la tabla del DatasetsView).
  originalData.value = {
    name: props.dataset.name || '',
    description: props.dataset.description || ''
  };

  // Inicializar los datos de edición.
  datasetData.value = {
    name: props.dataset.name || '',
    description: props.dataset.description || ''
  };

  nameError.value = '';
  descriptionError.value = '';
};

const closeModal = () => {
  emit('close');
};

const handleSubmit = async () => {
  if (!validateForm() || isSubmitting.value || !hasChanges.value) return;
  
  isSubmitting.value = true;
  
  try {

    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    // Solo enviar los campos que han cambiado.
    const updateData = {};
    
    if (datasetData.value.name !== originalData.value.name) {
      updateData.name = datasetData.value.name;
    }
    
    if (datasetData.value.description !== originalData.value.description) {
      updateData.description = datasetData.value.description || null;
    }
    
    const response = await axios.patch(`/datasets/${props.dataset.id}`, updateData);
    
    notifySuccess(
      "Conjunto de imágenes actualizado", 
      `Se ha actualizado el conjunto ${datasetData.value.name} con éxito.`
    );
    
    emit('dataset-updated', response.data);
    closeModal();
  } catch (error) {
    console.error('Error while editing dataset: ', error);
    handleApiError(error);
  } finally {
    isSubmitting.value = false;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    const detail = data.detail || "Unknown error";

    console.error("Error response: ", data);
    
    switch (status) {
      case 400:
        notifyError("Error de validación", 
        "Ha ocurrido un error de validación.");
      case 403:
        if (detail.includes("credentials")) {
          notifyInfo("Sesión expirada", 
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else if (detail.includes("privileges")) {
          notifyError("Acceso denegado", 
          "No tienes permisos suficientes para realizar esta acción.");
          router.push('/');
        } else {
          notifyError("Acceso denegado", 
          "No tienes permisos suficientes para realizar esta acción.");
        }
        break;
      case 404:
        notifyError("Conjunto de imágenes no encontrado",
        "El conjunto que intentas editar no existe en el sistema.");
        break;
      case 409:
        if (data.detail && data.detail.includes('name')) {
          nameError.value = 'Ya tienes un conjunto de imágenes con este nombre.';
        } else {
          notifyError("Nombre duplicado",
          "Ya tienes un conjunto de imágenes con este nombre.");
        }
        break;
      case 422:
        notifyError("Error de validación", 
        "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada.");
        break;
      default:
        notifyError("Error en el servidor",
        "No se pudo completar la actualización del conjunto de imágenes. Por favor, intenta nuevamente más tarde.");
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", 
    "Ha ocurrido un problema al actualizar el conjunto de imágenes.");
  }
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>