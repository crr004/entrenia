<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal edit-image-modal">
        <h1>Editar imagen</h1>
        <button class="close-modal-button" @click="close">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="signup-body" @submit.prevent="handleSubmit">
          <div class="form-preview">
            <img 
              :src="`data:image/png;base64,${image.thumbnail}`" 
              alt="Vista previa de la imagen" 
              class="image-preview"
            />
          </div>
          <div class="auth-modal-form">
            <ImageNameField
              v-model="formData.name"
              :error="errors.name"
              label="Nombre*"
              placeholder="Introduce un nombre para la imagen"
              id="image-name"
              :required="true"
              @input="validateName"
              ref="imageNameFieldRef"
            />
            <ImageLabelField
              v-model="formData.label"
              :error="errors.label"
              label="Etiqueta"
              placeholder="Introduce una etiqueta"
              id="image-label"
              :required="false"
              @input="validateLabel"
            />
            <button 
              type="submit" 
              class="app-button" 
              :disabled="isSubmitting || !isFormValid || !hasChanges"
            >
              <span v-if="!isSubmitting">Guardar cambios</span>
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
import { ref, computed, defineProps, defineEmits, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ImageNameField from '@/components/images/ImageNameField.vue';
import ImageLabelField from '@/components/images/ImageLabelField.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  image: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['close', 'image-updated']);

const router = useRouter();
const authStore = useAuthStore();
const formData = ref({
  name: '',
  label: ''
});
const originalData = ref({
  name: '',
  label: ''
});
const isSubmitting = ref(false);
const errors = ref({
  name: '',
  label: ''
});
const imageNameFieldRef = ref(null);


watch(() => [props.isOpen, props.image], async ([newIsOpen, newImage]) => {
  if (newIsOpen && newImage) {
    // Guardar datos originales.
    originalData.value = {
      name: newImage.name || '',
      label: newImage.label || ''
    };
    
    formData.value = {
      name: newImage.name || '',
      label: newImage.label || ''
    };
    
    errors.value = { name: '', label: '' };
    
    // Foco en el campo de nombre de la imagen al abrir el modal.
    await nextTick();
    const inputElement = imageNameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
}, { immediate: true });

const hasChanges = computed(() => {
  const nameChanged = formData.value.name !== originalData.value.name;
  
  const formattedNewLabel = formData.value.label.trim() === '' ? null : formData.value.label;
  const formattedOriginalLabel = originalData.value.label || null;
  
  const labelChanged = formattedNewLabel !== formattedOriginalLabel;
  
  return nameChanged || labelChanged;
});

const validateName = () => {
  if (!formData.value.name.trim()) {
    errors.value.name = 'El nombre de la imagen es obligatorio.';
    return false;
  } else if (formData.value.name.length > 255) {
    errors.value.name = 'El nombre no puede exceder los 255 caracteres.';
    return false;
  } else {
    errors.value.name = '';
    return true;
  }
};

const validateLabel = () => {
  if (formData.value.label && formData.value.label.length > 255) {
    errors.value.label = 'La etiqueta no puede exceder los 255 caracteres.';
    return false;
  } else {
    errors.value.label = '';
    return true;
  }
};

const validateForm = () => {
  const isNameValid = validateName();
  const isLabelValid = validateLabel();
  return isNameValid && isLabelValid;
};

const isFormValid = computed(() => {
  return formData.value.name.trim() !== '' && !errors.value.name && !errors.value.label;
});

const handleSubmit = async () => {
  if (!validateForm() || isSubmitting.value || !hasChanges.value) return;
  
  isSubmitting.value = true;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    authStore.setAuthHeader();
    
    // Crear un objeto con los datos modificados.
    const updateData = {};
    if (formData.value.name !== originalData.value.name) {
      updateData.name = formData.value.name;
    }
    
    // Para la etiqueta, tratar cadena vacía como null.
    if (formData.value.label !== originalData.value.label) {
      updateData.label = formData.value.label.trim() === '' ? null : formData.value.label;
    }
    
    const response = await axios.patch(`/images/${props.image.id}`, updateData);
    
    notifySuccess("Imagen actualizada", 
    `Se ha actualizado la imagen ${formData.value.name} con éxito.`);
    
    emit('image-updated', response.data);
    
    close();
  } catch (error) {
    console.error('Error while updating the image: ', error);
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
        notifyError("Imagen no encontrada",
        "La imagen que intentas editar no existe en el sistema.");
        break;
      case 409:
        if (data.detail && data.detail.includes('name')) {
          errors.value.name = 'Ya existe una imagen con este nombre en este conjunto.';
        } else {
          notifyError("Nombre duplicado",
          "Ya existe una imagen con este nombre en este conjunto.");
        }
        break;
      case 422:
        notifyError("Error de validación",
        "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada.");
        break;
      default:
        notifyError("Error en el servidor",
        "No se pudo completar la actualización de la imagen. Por favor, intenta nuevamente más tarde.");
    }
  } else if (error.request) {
    notifyError("Error de conexión",
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado",
    "Ha ocurrido un problema al actualizar la imagen.");
  }
};

const close = () => {
  emit('close');
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped>
.form-preview {
  display: flex;
  justify-content: center;
  margin: 0 auto 20px;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  max-width: 80%;
}

.image-preview {
  max-height: 150px;
  max-width: 100%;
  object-fit: contain;
}

@media (max-width: 768px) {
  .form-preview {
    padding: 10px;
    max-width: 90%;
  }
  
  .image-preview {
    max-height: 120px;
  }
}
</style>