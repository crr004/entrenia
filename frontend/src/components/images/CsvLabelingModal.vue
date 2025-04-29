<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal csv-labeling-modal">
        <button class="close-modal-button" @click="handleClose">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2>Etiquetar imágenes con CSV</h2>
        <div class="modal-content">
          <div v-if="isLoading" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando imágenes sin etiquetar...</p>
          </div>
          <div v-else-if="unlabeledImages.length === 0" class="empty-state">
            <font-awesome-icon :icon="['fas', 'check-circle']" />
            <p>No hay imágenes sin etiquetar.</p>
            <button class="app-button" @click="handleClose">Volver</button>
          </div>
          <div v-else>
            <div class="csv-intro">
              <p>Sube un archivo CSV para etiquetar múltiples imágenes a la vez.</p>
              <p class="info-text">
                <font-awesome-icon :icon="['fas', 'info-circle']" />
                Hay {{ unlabeledImages.length }} imágenes sin etiquetar en este conjunto.
              </p>
            </div>
            <div class="upload-section">
              <div 
                class="drop-zone"
                :class="{ 'active-dropzone': isDragging, 'has-file': csvFile }"
                @dragenter.prevent="dragCounter++; isDragging = true"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="onDragLeave"
                @drop.prevent="onDrop"
                @click="triggerFileInput"
              >
                <input 
                  type="file"
                  id="csv-file"
                  ref="fileInput"
                  accept=".csv"
                  @change="handleFileChange"
                  class="file-input"
                />
                <div v-if="!csvFile" class="drop-message">
                  <font-awesome-icon :icon="['fas', 'file-csv']" size="2x" />
                  <p>Arrastra tu archivo CSV aquí o haz clic para seleccionarlo</p>
                  <span class="drop-hint">Formato: nombre_imagen,etiqueta</span>
                </div>
                <div v-else class="file-selected">
                  <div class="file-preview">
                    <font-awesome-icon :icon="['fas', 'file-csv']" size="lg" />
                    <div class="file-info">
                      <div class="file-name">{{ fileName }}</div>
                      <div class="file-size" v-if="csvFile.size">{{ formatFileSize(csvFile.size) }}</div>
                    </div>
                    <button class="remove-file" @click.stop="resetFileInput">
                      <font-awesome-icon :icon="['fas', 'times']" />
                    </button>
                  </div>
                </div>
              </div>
              <div class="csv-format-info">
                <p>El CSV debe tener dos columnas:</p>
                <div class="csv-columns">
                  <div class="csv-column">
                    <span class="column-number">1</span>
                    <span class="column-desc">Nombre de la imagen<br>(incluyendo extensión)</span>
                  </div>
                  <div class="csv-column">
                    <span class="column-number">2</span>
                    <span class="column-desc">Etiqueta de<br>la imagen</span>
                  </div>
                </div>
                <p class="example">Ejemplo: gato01.jpg,gato</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions" v-if="!isLoading && unlabeledImages.length > 0">
          <button type="button" class="cancel-button" @click="handleClose" v-if="!isProcessing">
            Cancelar
          </button>
          <button 
            class="app-button" 
            @click="applyLabels"
            :disabled="!csvFile || isProcessing"
          >
            <span v-if="!isProcessing">
              <font-awesome-icon :icon="['fas', 'tags']" class="upload-icon"/>
              <span>Aplicar etiquetas</span>
            </span>
            <span v-else>
              <font-awesome-icon :icon="['fas', 'spinner']" spin />
              <span> Procesando...</span>
            </span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

import { notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';

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
const isProcessing = ref(false);
const unlabeledImages = ref([]);
const fileInput = ref(null);
const fileName = ref('');
const csvFile = ref(null);
const isDragging = ref(false);
const dragCounter = ref(0);

watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await loadUnlabeledImages();
  } else {
    resetState();
  }
});

const resetState = () => {
  isLoading.value = true;
  isProcessing.value = false;
  unlabeledImages.value = [];
  fileName.value = '';
  csvFile.value = null;
  isDragging.value = false;
  dragCounter.value = 0;
  
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const loadUnlabeledImages = async () => {
  isLoading.value = true;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem("token") || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    const response = await axios.get(`/datasets/${props.datasetId}/unlabeled-images`);
    unlabeledImages.value = response.data.images || [];
    
    // Si no hay imágenes sin etiquetar, mostrar un mensaje informativo.
    // (Esto no debería suceder, ya que el botón de etiquetar se activa solo si hay imágenes sin etiquetar).
    if (unlabeledImages.value.length === 0) {
      notifyInfo("No hay imágenes para etiquetar", 
      "Todas las imágenes en este conjunto ya tienen etiquetas.");
    }
  } catch (error) {
    console.error('Error loading unlabeled images: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

// Manejadores de drag and drop.
const onDragLeave = () => {
  dragCounter.value--;
  if (dragCounter.value <= 0) {
    isDragging.value = false;
    dragCounter.value = 0;
  }
};

const onDrop = (e) => {
  isDragging.value = false;
  dragCounter.value = 0;
  
  const files = e.dataTransfer.files;
  if (files.length) {
    handleCsvFile(files[0]);
  }
};

const triggerFileInput = () => {
  if (!csvFile.value && fileInput.value) {
    fileInput.value.click();
  }
};

const handleFileChange = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  handleCsvFile(file);
};

const handleCsvFile = (file) => {
  if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
    notifyError("Formato no válido",
    "Por favor, selecciona un archivo CSV.");
    resetFileInput();
    return;
  }
  
  fileName.value = file.name;
  csvFile.value = file;
};

const formatFileSize = (size) => {
  if (size > 1024 * 1024) {
    return (size / (1024 * 1024)).toFixed(2) + ' MB';
  } else if (size > 1024) {
    return (size / 1024).toFixed(2) + ' KB';
  } else {
    return size + ' B';
  }
};

// Analizar y formatear el contenido del archivo CSV.
const parseCsvContent = async (file) => {
  // Verifica si el archivo es un CSV y formatearlo correctamente.
  // Crea pares de nombre de imagen y etiqueta, tal y como espera la API.
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        const lines = content.split('\n');
        
        const labels = [];
        
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          if (!line) continue;
          
          const parts = line.split(',');
          if (parts.length >= 2) {
            const imageName = parts[0].trim();
            const label = parts[1].trim();
            
            if (imageName && label) {
              labels.push({
                image_name: imageName,
                label: label
              });
            }
          }
        }
        
        resolve(labels);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => {
      reject(new Error("Error reading file"));
    };
    
    reader.readAsText(file);
  });
};

const resetFileInput = () => {
  fileName.value = '';
  csvFile.value = null;
  
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const applyLabels = async () => {
  if (!csvFile.value || isProcessing.value) return;
  
  isProcessing.value = true;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem("token") || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    const labels = await parseCsvContent(csvFile.value);
    
    if (labels.length === 0) {
      notifyError("CSV vacío o inválido",
      "El archivo no contiene datos en el formato correcto.");
      isProcessing.value = false;
      return;
    }
    
    const response = await axios.post(`/datasets/${props.datasetId}/csv-label`, {
      labels: labels
    });
    
    emit('images-labeled', { 
      labeledCount: response.data.labeled_count || 0,
      notFoundCount: response.data.not_found_count || 0,
      notFoundDetails: response.data.not_found_details || []
    });
    
  } catch (error) {
    console.error('Error applying CSV labels: ', error);
    handleApiError(error);
  } finally {
    isProcessing.value = false;
  }
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
        notifyError("Conjunto de imágenes no encontrado",
        "El conjunto en el que intentas etiquetar imágenes no existe o ha sido eliminado.");
        break;
      case 413:
        notifyError("Archivo demasiado grande",
        "El tamaño del archivo supera el límite permitido por el servidor.");
        break;
      case 400:
        notifyError("Formato inválido",
        "El archivo CSV proporcionado no es válido o tiene un formato incorrecto.");
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
    "Ha ocurrido un problema al etiquetar las imágenes.");
  }
};

const handleClose = () => {
  emit('close');
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/upload.css"></style>
<style scoped>
.csv-intro {
  margin-bottom: 15px;
  color: #555;
}

.info-text {
  font-size: 0.9rem;
  color: #3182ce;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
  color: #666;
}

.loading-container svg,
.empty-state svg {
  font-size: 2rem;
  margin-bottom: 15px;
  color: #999;
}

.empty-state{
  margin-top: 15px;
}
</style>