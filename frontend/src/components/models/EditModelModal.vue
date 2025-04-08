<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal edit-model-modal">
        <h1>Editar modelo</h1>
        <button class="close-modal-button" @click="closeModal">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="signup-body" @submit.prevent="handleSubmit">
          <div class="auth-modal-form">
            <ModelNameField
              v-model="modelData.name"
              :error="nameError"
              @input="validateName"
              ref="modelNameFieldRef"
            />
            <ModelDescriptionField
              v-model="modelData.description"
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
                <font-awesome-icon :icon="['fas', 'spinner']" spin />
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
import ModelNameField from '@/components/models/ModelNameField.vue';
import ModelDescriptionField from '@/components/models/ModelDescriptionField.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  model: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['close', 'model-updated']);

const isSubmitting = ref(false);
const nameError = ref('');
const descriptionError = ref('');
const modelNameFieldRef = ref(null);
const originalData = ref({});

const authStore = useAuthStore();

const router = useRouter();

const modelData = ref({
  name: '',
  description: ''
});

// Foco en el campo de nombre del modelo al abrir el modal.
watch([() => props.isOpen, () => props.model], async ([newIsOpen, newModel]) => {
  if (newIsOpen && newModel) {
    initForm();
    await nextTick();
    const inputElement = modelNameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
}, { immediate: true });

// Verificar si hay cambios respecto a los datos originales.
const hasChanges = computed(() => {
  return modelData.value.name !== originalData.value.name || 
         modelData.value.description !== originalData.value.description;
});

const isFormValid = computed(() => {
  return !nameError.value && !descriptionError.value && modelData.value.name;
});

const validateName = () => {
  if (!modelData.value.name) {
    nameError.value = 'El nombre del modelo es obligatorio.';
    return false;
  } else if (modelData.value.name.length < 1) {
    nameError.value = 'El nombre debe tener al menos 1 carácter.';
    return false;
  } else if (modelData.value.name.length > 255) {
    nameError.value = 'El nombre no puede exceder los 255 caracteres.';
    return false;
  } else {
    nameError.value = '';
    return true;
  }
};

const validateDescription = () => {
  if (modelData.value.description && modelData.value.description.length > 1000) {
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
  // Guardar una copia de los datos originales (se pasan desde la tabla del ModelsView).
  originalData.value = {
    name: props.model.name || '',
    description: props.model.description || ''
  };

  // Inicializar los datos de edición.
  modelData.value = {
    name: props.model.name || '',
    description: props.model.description || ''
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
    
    if (modelData.value.name !== originalData.value.name) {
      updateData.name = modelData.value.name;
    }
    
    if (modelData.value.description !== originalData.value.description) {
      updateData.description = modelData.value.description || null;
    }
    
    const response = await axios.patch(`/classifiers/${props.model.id}`, updateData);
    
    notifySuccess("Modelo actualizado", 
    `Se ha actualizado el modelo ${modelData.value.name} con éxito.`);
    
    emit('model-updated', response.data);
    closeModal();
  } catch (error) {
    console.error('Error while editing model: ', error);
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
        break;
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
        notifyError("Modelo no encontrado",
        "El modelo que intentas editar no existe en el sistema.");
        break;
      case 409:
        if (data.detail && data.detail.includes('name')) {
          nameError.value = 'Ya tienes un modelo con este nombre.';
        } else {
          notifyError("Nombre duplicado",
          "Ya tienes un modelo con este nombre.");
        }
        break;
      case 422:
        notifyError("Error de validación", 
        "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada.");
        break;
      default:
        notifyError("Error en el servidor",
        "No se pudo completar la actualización del modelo. Por favor, intenta nuevamente más tarde.");
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", 
    "Ha ocurrido un problema al actualizar el modelo.");
  }
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>