<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal manual-labeling-modal">
        <button class="close-modal-button" @click="handleClose">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2>Etiquetado manual</h2>
        <div class="modal-content">
          <div class="progress-indicator">
            <span>Imagen {{ currentIndex + 1 }} de {{ totalImages }}</span>
          </div>
          <div v-if="isLoading" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando imágenes sin etiquetar...</p>
          </div>
          <div v-else-if="!currentImage" class="empty-state">
            <font-awesome-icon :icon="['fas', 'check-circle']" />
            <p>No hay imágenes sin etiquetar.</p>
            <button class="app-button" @click="handleClose">Volver</button>
          </div>
          <div v-else class="labeling-form">
            <div class="image-preview">
              <img 
                :src="`data:image/png;base64,${currentImage.thumbnail}`" 
                alt="Imagen a etiquetar" 
              />
            </div>
            <div class="image-info">
              <h3>{{ currentImage.name }}</h3>
            </div>
            <form @submit.prevent="submitLabel" class="auth-modal-form">
              <ImageLabelField
                v-model="labelInput"
                placeholder="Introduce una etiqueta"
                id="image-label"
                ref="labelInputRef"
                @input="() => {}"
              />
              <div class="navigation-buttons">
                <button 
                  type="button" 
                  class="navigation-button back-button"
                  @click="goBack"
                  :disabled="currentIndex === 0"
                >
                  <font-awesome-icon :icon="['fas', 'arrow-left']" />
                  <span>Anterior</span>
                </button>
                <button 
                  type="button" 
                  class="navigation-button next-button"
                  @click="skipImage"
                  :disabled="isLastImage"
                >
                  <span>Saltar</span>
                  <font-awesome-icon :icon="['fas', 'arrow-right']" />
                </button>
              </div>
            </form>
          </div>
        </div>
        <div class="modal-actions" v-if="!isLoading && currentImage">
          <div class="left-actions">
            <button type="button" class="secondary-button" @click="handleFinishLabeling">
              Terminar etiquetado
            </button>
          </div>
          <div class="right-actions">
            <button 
              type="button" 
              class="app-button" 
              @click="isLastImage ? submitLabelAndClose() : submitLabel()"
            >
              <font-awesome-icon :icon="['fas', 'tag']" />
              <span>{{ isLastImage ? 'Etiquetar y finalizar' : 'Etiquetar y continuar' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { defineProps, defineEmits } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ImageLabelField from '@/components/images/ImageLabelField.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  datasetId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['close', 'images-labeled']);
const router = useRouter();
const authStore = useAuthStore();

const isLoading = ref(true);
const unlabeledImages = ref([]);
const currentIndex = ref(0);
const labelInput = ref('');
const hasChanges = ref(false);
const labelInputRef = ref(null);
const labeledCount = ref(0);
const visitedImages = ref([]);

// Almacenar etiquetas temporales para cada imagen.
// Esto se utiliza para recordar etiquetas ya ingresadas en la sesión actual.
const tempLabels = ref({});

// Computar si estamos en la última imagen.
const isLastImage = computed(() => {
  return unlabeledImages.value.length > 0 && currentIndex.value === unlabeledImages.value.length - 1;
});

const currentImage = computed(() => {
  if (!unlabeledImages.value.length || currentIndex.value >= unlabeledImages.value.length) {
    return null;
  }
  return unlabeledImages.value[currentIndex.value];
});

const totalImages = computed(() => unlabeledImages.value.length);

watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await loadUnlabeledImages();
  } else {
    // Reiniciar estado cuando se cierra el modal.
    resetState();
  }
});

// Enfocar y colocar el cursor al final del input (campo de introducir la etiqueta).
const focusLabelInput = () => {
  setTimeout(() => {
    if (labelInputRef.value && labelInputRef.value.$el) {
      const inputElement = labelInputRef.value.$el.querySelector('input');
      if (inputElement) {
        inputElement.focus();
        
        const length = inputElement.value.length;
        if (length > 0) {
          inputElement.setSelectionRange(length, length);
        }
      }
    }
  }, 100); // Retraso para asegurar que el DOM está actualizado.
};

watch(currentImage, () => {
  if (currentImage.value) {
    // Verificar si ya hay una etiqueta temporal para esta imagen.
    const imageId = currentImage.value.id;
    if (tempLabels.value[imageId]) {
      // Si ya se ha etiquetado esta imagen en esta sesión, mostrar esa etiqueta.
      labelInput.value = tempLabels.value[imageId];
    } else {
      // Si no, limpiar el campo.
      labelInput.value = '';
    }
    
    // Añadir el índice actual a visitedImages si no está ya.
    if (!visitedImages.value.includes(currentIndex.value)) {
      visitedImages.value.push(currentIndex.value);
    }
  }
  
  // Enfocar el campo de etiqueta.
  focusLabelInput();
});

const resetState = () => {
  isLoading.value = true;
  unlabeledImages.value = [];
  currentIndex.value = 0;
  labelInput.value = '';
  hasChanges.value = false;
  labeledCount.value = 0;
  visitedImages.value = [];
  tempLabels.value = {};
};

const loadUnlabeledImages = async () => {
  isLoading.value = true;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    // Obtener imágenes sin etiquetar para este dataset.
    const response = await axios.get(`/datasets/${props.datasetId}/unlabeled-images`);
    unlabeledImages.value = response.data.images || [];
    currentIndex.value = 0;
    
    // Si no hay imágenes sin etiquetar, mostrar un mensaje informativo.
    // (Esto no debería suceder, ya que el botón de etiquetar se activa solo si hay imágenes sin etiquetar).
    if (unlabeledImages.value.length === 0) {
      notifyInfo("No hay imágenes para etiquetar", 
      "Todas las imágenes en este conjunto ya tienen etiquetas.");
    } else {
      // Si hay imágenes, agregar el índice 0 a visitedImages.
      visitedImages.value = [0];
    }
  } catch (error) {
    console.error('Error loading unlabeled images: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

// Si es la última imagen, se etiqueta y se cierra el modal.
const submitLabelAndClose = async () => {
  if (!currentImage.value) return;
  
  const imageId = currentImage.value.id;
  const labelText = labelInput.value.trim();
  
  if (labelText) {
    try {
      // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
      const hasToken = !!localStorage.getItem('token') || !!authStore.token;
      if(hasToken){
        authStore.setAuthHeader();
      }
      
      await axios.patch(`/images/${imageId}`, {
        label: labelText
      });
      
      // Almacenar en las etiquetas temporales para recordarla.
      tempLabels.value[imageId] = labelText;
      
      labeledCount.value++;
      hasChanges.value = true;
      
      notifySuccess("Etiquetado finalizado", 
      `Has etiquetado ${labeledCount.value} imágenes de ${visitedImages.value.length} vistas.`);
    } catch (error) {
      console.error('Error updating image label: ', error);
      handleApiError(error);
      return;
    }
  }

  handleClose();
};

// Si no es la última imagen, se etiqueta y se avanza a la siguiente.
const submitLabel = async () => {
  if (!currentImage.value) return;
  
  const imageId = currentImage.value.id;
  const labelText = labelInput.value.trim();
  
  if (labelText) {
    try {
      // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
      const hasToken = !!localStorage.getItem('token') || !!authStore.token;
      if(hasToken){
        authStore.setAuthHeader();
      }
      
      await axios.patch(`/images/${imageId}`, {
        label: labelText
      });
      
      // Almacenar en las etiquetas temporales para recordarla.
      tempLabels.value[imageId] = labelText;
      
      labeledCount.value++;
      hasChanges.value = true;
    } catch (error) {
      console.error('Error updating image label: ', error);
      handleApiError(error);
      return;
    }
  } else {
    // Si no hay texto pero previamente había una etiqueta temporal, eliminarla.
    if (tempLabels.value[imageId]) {
      delete tempLabels.value[imageId];
    }
  }
  // Avanzar a la siguiente imagen (tanto si se etiquetó como si no).
  moveToNextImage();
};

const skipImage = () => {
  // Guardar la etiqueta actual en las etiquetas temporales antes de avanzar.
  if (currentImage.value && labelInput.value.trim()) {
    tempLabels.value[currentImage.value.id] = labelInput.value.trim();
  }
  
  moveToNextImage();
  focusLabelInput();
};

const goBack = () => {
  if (currentIndex.value > 0) {
    // Guardar la etiqueta actual en las etiquetas temporales antes de retroceder.
    if (currentImage.value && labelInput.value.trim()) {
      tempLabels.value[currentImage.value.id] = labelInput.value.trim();
    }
    
    currentIndex.value--;
    focusLabelInput();
  }
};

const moveToNextImage = () => {
  currentIndex.value++;
  
  if (currentIndex.value >= unlabeledImages.value.length) {
    currentIndex.value = unlabeledImages.value.length - 1;
    
    // Informar al usuario que ha llegado al final.
    notifyInfo("Has llegado al final",
    "Esta es la última imagen. Finaliza cuando termines.");
  } else {
    // Si no se han terminado, enfocar el campo de etiqueta.
    focusLabelInput();
  }
};

const handleFinishLabeling = () => {
  // Guardar la etiqueta actual en etiquetas temporales antes de cerrar.
  if (currentImage.value && labelInput.value.trim()) {
    tempLabels.value[currentImage.value.id] = labelInput.value.trim();
  }
  
  // Mostrar un mensaje con el resumen del etiquetado.
  if (hasChanges.value) {
    notifySuccess("Etiquetado finalizado", 
    `Has etiquetado ${labeledCount.value} imágenes de ${visitedImages.value.length} vistas.`);
  } else {
    notifyInfo("Etiquetado finalizado", 
    "No has etiquetado ninguna imagen.");
  }

  handleClose();
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;

    console.error("Error response: ", data);
    
    switch (status) {
      case 401:
        router.push("/");
        break; 
      case 403:
        if (data.detail && data.detail.includes("credentials")) {
          notifyInfo("Sesión expirada",
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else if (data.detail && data.detail.includes("privileges")) {
          router.push('/my-datasets');
        } else {
          notifyError("Acceso denegado",
          "No tienes permiso para realizar esta acción.");
        }
        break;
      case 404:
        notifyError("Imagen o conjunto no encontrado",
        "La imagen o el conjunto que intentas etiquetar no existe o ha sido eliminado.");
        break;
      case 422:
        notifyError("Datos inválidos",
        "El formato de los datos enviados no es correcto.");
        break;
      default:
        notifyError("Error en el servidor",
        "No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.");
        break;
    }
  } else if (error.request) {
    notifyError("Error de conexión",
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado",
    "Ha ocurrido un problema al etiquetar la imagen.");
  }
};

const handleClose = () => {
  if (hasChanges.value) {
    emit('images-labeled', { labeledCount: labeledCount.value });
  }
  emit('close');
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped>
.manual-labeling-modal {
  width: 520px;
  max-width: 95%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  padding: 25px;
  box-sizing: border-box;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 15px;
}

/* Indicador de progreso */
.progress-indicator {
  text-align: center;
  margin-bottom: 15px;
  color: #666;
  font-size: 0.9rem;
  background-color: #f7f7f7;
  padding: 8px;
  border-radius: 4px;
}

/* Vista de imagen */
.labeling-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.image-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
  border-radius: 6px;
  padding: 12px;
  min-height: 120px;
}

.image-preview img {
  max-width: 100%;
  max-height: 180px;
  object-fit: contain;
}

.image-info {
  text-align: center;
}

.image-info h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
  color: #333;
  word-break: break-word;
}

/* Botones de navegación */
.navigation-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}

.navigation-button {
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px 15px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.navigation-button:hover {
  background-color: #f5f5f5;
  color: #333;
}

.navigation-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.back-button {
  padding-left: 12px;
}

.next-button {
  padding-right: 12px;
}

/* Estados de carga y vacío */
.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 25px;
  text-align: center;
  color: #666;
}

.loading-container svg,
.empty-state svg {
  font-size: 1.8rem;
  margin-bottom: 12px;
  color: #999;
}

.empty-state .app-button {
  margin-top: 15px;
}

/* Mensaje de finalización */
.completion-message {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255,255,255,0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: inherit;
}

.message-content {
  text-align: center;
  padding: 20px;
}

.message-content svg {
  font-size: 2.5rem;
  color: #4caf50;
  margin-bottom: 15px;
}

.message-content h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.message-content p {
  margin: 0 0 20px 0;
  color: #666;
}

/* Acciones del formulario */
.modal-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.left-actions, .right-actions {
  display: flex;
}

.cancel-button {
  display: none;
}

/* Estilo para el botón secundario */
.secondary-button {
  background: none;
  border: none;
  color: #666;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.95rem;
  transition: color 0.2s;
}

.secondary-button:hover {
  color: rgb(34, 134, 141);
}

.app-button {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 8px 16px;
  margin-top: 0;
  width: auto;
}

/* Responsive */
@media (max-width: 640px) {
  .modal-actions {
    flex-direction: column;
  }
  
  .left-actions, .right-actions {
    width: 100%;
    margin-bottom: 10px;
  }
  
  .modal-actions button {
    width: 100%;
  }
  
  .navigation-buttons {
    flex-direction: column;
    gap: 10px;
  }
  
  .navigation-button {
    width: 100%;
    justify-content: center;
  }
}
</style>