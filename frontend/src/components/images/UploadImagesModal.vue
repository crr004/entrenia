<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal upload-images-modal">
        <button class="close-modal-button" @click="closeModal">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2>¡Añade imágenes al conjunto!</h2>
        <div class="upload-content">
          <div class="drop-zone"
            :class="{ 'active-dropzone': isDraggingZip, 'has-file': zipFile }"
            @dragenter.prevent="zipDragCounter++; isDraggingZip = true"
            @dragover.prevent="isDraggingZip = true"
            @dragleave.prevent="onDragLeaveZip"
            @drop.prevent="onDropZip"
            @click="triggerZipInput($event)"
          >
            <input 
              type="file"
              ref="zipInput"
              accept=".zip"
              class="file-input"
              @change="onZipSelected"
            />
            <div v-if="!zipFile" class="drop-message">
              <font-awesome-icon :icon="['fas', 'file-archive']" size="2x" />
              <p>Arrastra tu archivo ZIP aquí o haz clic para seleccionarlo</p>
              <span class="drop-hint">El archivo debe contener imágenes (jpg, jpeg, png, gif, webp)</span>
            </div>
            <div v-else class="file-selected">
              <div class="file-preview">
                <font-awesome-icon :icon="['fas', 'file-archive']" size="lg" />
                <div class="file-info">
                  <div class="file-name">{{ zipFile.name }}</div>
                  <div class="file-size">{{ formatFileSize(zipFile.size) }}</div>
                </div>
                <button class="remove-file" @click.stop="removeZipFile">
                  <font-awesome-icon :icon="['fas', 'times']" />
                </button>
              </div>
            </div>
          </div>
          <div v-if="zipFile" class="labeling-options">
            <h3>Opciones de etiquetado</h3>
            <div class="radio-group">
              <label class="radio-option">
                <input type="radio" v-model="zipLabelingOption" value="none" />
                <span class="radio-label">No etiquetar imágenes</span>
                <span class="radio-hint">(podrás etiquetarlas después)</span>
              </label>
              <label class="radio-option">
                <input type="radio" v-model="zipLabelingOption" value="csv" />
                <span class="radio-label">Etiquetar con archivo CSV</span>
              </label>
            </div>
            <div v-if="zipLabelingOption === 'csv'" class="csv-upload">
              <div 
                class="drop-zone csv-zone"
                :class="{ 'active-dropzone': isDraggingCsv, 'has-file': csvFile }"
                @dragenter.prevent="isDraggingCsv = true"
                @dragover.prevent="isDraggingCsv = true"
                @dragleave.prevent="onDragLeaveCsv"
                @drop.prevent="onDropCsv"
                @click="triggerCsvInput($event)"
              >
                <input 
                  type="file"
                  ref="csvInput"
                  accept=".csv"
                  class="file-input"
                  @change="onCsvSelected"
                />
                <div v-if="!csvFile" class="drop-message">
                  <font-awesome-icon :icon="['fas', 'file-csv']" size="lg" />
                  <p>Selecciona un archivo CSV con las etiquetas</p>
                  <span class="drop-hint">Formato: nombre_imagen,etiqueta</span>
                </div>
                <div v-else class="file-selected">
                  <div class="file-preview">
                    <font-awesome-icon :icon="['fas', 'file-csv']" size="lg" />
                    <div class="file-info">
                      <div class="file-name">{{ csvFile.name }}</div>
                      <div class="file-size">{{ formatFileSize(csvFile.size) }}</div>
                    </div>
                    <button class="remove-file" @click.stop="removeCsvFile">
                      <font-awesome-icon :icon="['fas', 'times']" />
                    </button>
                  </div>
                </div>
              </div>
              <div class="csv-format-info">
                <p>El CSV debe tener dos columnas sin cabecera:</p>
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
        <div v-if="isUploading" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
          <div class="progress-text">{{ uploadProgress }}% completado</div>
        </div>
        <div class="modal-actions">
          <button class="cancel-button" @click="closeModal" :disabled="isUploading">
            Cancelar
          </button>
          <button 
            class="app-button" 
            @click="uploadFiles"
            :disabled="!canUpload || isUploading"
          >
            <span v-if="!isUploading">
              <font-awesome-icon :icon="['fas', 'upload']" class="upload-icon"/>
              <span>Subir imágenes</span>
            </span>
            <span v-else>
              <font-awesome-icon :icon="['fas', 'spinner']" spin />
              <span></span>
            </span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/authStore";
import { notifyError, notifyInfo, notifySuccess } from "@/utils/notifications";

const props = defineProps({
  isOpen: Boolean,
  datasetId: String
});

const emit = defineEmits(["close", "images-uploaded"]);
const router = useRouter();
const authStore = useAuthStore();

const zipInput = ref(null);
const csvInput = ref(null);

const zipFile = ref(null);
const isDraggingZip = ref(false);
const zipDragCounter = ref(0);
const zipLabelingOption = ref('none');

const csvFile = ref(null);
const isDraggingCsv = ref(false);
const csvDragCounter = ref(0);

const isUploading = ref(false);
const uploadProgress = ref(0);

// Verificar si se puede realizar la subida.
const canUpload = computed(() => {
  if (!zipFile.value) return false;
  if (zipLabelingOption.value === 'csv' && !csvFile.value) return false;
  return true;
});

// Gestión de eventos para arrastrar archivos ZIP...
const onDragLeaveZip = () => {
  zipDragCounter.value--;
  if (zipDragCounter.value <= 0) {
    isDraggingZip.value = false;
    zipDragCounter.value = 0;
  }
};

const onDropZip = (e) => {
  isDraggingZip.value = false;
  zipDragCounter.value = 0;
  
  const files = e.dataTransfer.files;
  if (files.length) {
    handleZipFile(files[0]);
  }
};

const triggerZipInput = (e) => {
  e?.stopPropagation();
  
  if (!zipFile.value) {
    zipInput.value.click();
  }
};

const onZipSelected = (e) => {
  if (e.target.files.length) {
    handleZipFile(e.target.files[0]);
  }
};

const handleZipFile = (file) => {

  // Validar que sea un ZIP.
  if (file.type !== 'application/zip' && !file.name.toLowerCase().endsWith('.zip')) {
    notifyError("Error",
    "Solo se permiten archivos ZIP.");
    return;
  }
  
  // Validar tamaño máximo (50MB).
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    notifyError("Error",
    "El archivo no puede superar los 50MB.");
    return;
  }
  
  zipFile.value = file;
};

const removeZipFile = () => {
  zipFile.value = null;
  if (zipInput.value) {
    zipInput.value.value = '';
  }
};

// Gestión de eventos para arrastrar archivos CSV...
const onDragLeaveCsv = () => {
  csvDragCounter.value--;
  if (csvDragCounter.value <= 0) {
    isDraggingCsv.value = false;
    csvDragCounter.value = 0;
  }
};

const onDropCsv = (e) => {
  isDraggingCsv.value = false;
  csvDragCounter.value = 0;
  
  const files = e.dataTransfer.files;
  if (files.length) {
    handleCsvFile(files[0]);
  }
};

const triggerCsvInput = (e) => {
  e?.stopPropagation();
  
  if (!csvFile.value) {
    csvInput.value.click();
  }
};

const onCsvSelected = (e) => {
  if (e.target.files.length) {
    handleCsvFile(e.target.files[0]);
  }
};

const handleCsvFile = (file) => {

  // Validar que sea un archivo CSV.
  if (file.type !== 'text/csv' && !file.name.toLowerCase().endsWith('.csv')) {
    notifyError('Error',
    'Solo se permiten archivos CSV.');
    return;
  }
  
  csvFile.value = file;
};

const removeCsvFile = () => {
  csvFile.value = null;
  if (csvInput.value) {
    csvInput.value.value = '';
  }
};

// Función para mostrar el tamaño de archivos en formato legible.
const formatFileSize = (size) => {
  if (size > 1024 * 1024) {
    return (size / (1024 * 1024)).toFixed(2) + ' MB';
  } else if (size > 1024) {
    return (size / 1024).toFixed(2) + ' KB';
  } else {
    return size + ' B';
  }
};

const closeModal = () => {
  resetForm();
  emit('close');
};

const resetForm = () => {
  zipFile.value = null;
  csvFile.value = null;
  zipLabelingOption.value = 'none';
  isUploading.value = false;
  uploadProgress.value = 0;
  
  if (zipInput.value) zipInput.value.value = '';
  if (csvInput.value) csvInput.value.value = '';
};

const uploadFiles = async () => {
  if (isUploading.value || !canUpload.value) return;
  
  isUploading.value = true;
  uploadProgress.value = 0;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem("token") || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    const formData = new FormData();
    
    formData.append("file", zipFile.value);
    formData.append("labeling_option", zipLabelingOption.value);
    
    if (zipLabelingOption.value === "csv" && csvFile.value) {
      formData.append("csv_file", csvFile.value);
    }
    
    // Subir el archivo ZIP (y el CSV si lo hay) al servidor.
    const response = await axios.post(
      `/datasets/${props.datasetId}/upload-zip`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          uploadProgress.value = percentCompleted;
        }
      }
    );
    
    emit("images-uploaded", response.data);
    
  } catch (error) {
    console.error("Error while uploading files: ", error);
    handleApiError(error);
  } finally {
    isUploading.value = false;
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
        "El conjunto al que intentas subir imágenes no existe o ha sido eliminado.");
        break;
      case 413:
        notifyError("Archivo demasiado grande",
        "El tamaño del archivo supera el límite permitido por el servidor (50MB).");
        break;
      case 400:
        notifyError("Formato inválido",
        "El archivo proporcionado no es válido.");
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
    "Ha ocurrido un problema al subir las imágenes.");
  }
};

watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    resetForm();
  }
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped>
.upload-images-modal {
  width: 90%;
  max-width: 650px;
  max-height: 85vh;
  padding: 25px;
  transform: translateY(0);
  overflow-y: auto;
}

h3 {
  font-size: 1rem;
  color: #444;
  margin: 15px 0 10px;
  text-align: left;
}

.upload-content {
  padding: 10px 0;
}

.radio-hint {
  font-size: 0.8rem;
  color: #666;
  margin-left: 6px;
  font-style: italic;
}

/* Zona de drag and drop */
.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 30px 20px;
  text-align: center;
  background-color: #f9f9f9;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  margin-bottom: 15px;
}

.active-dropzone {
  border-color: rgb(34, 134, 141);
  background-color: rgba(34, 134, 141, 0.05);
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: -1;
}

/* Mensajes para drag and drop */
.drop-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #666;
}

.drop-message svg {
  color: #999;
  margin-bottom: 10px;
}

.drop-message p {
  margin: 5px 0;
  font-size: 1rem;
}

.drop-hint {
  font-size: 0.8rem;
  color: #999;
  margin-top: 5px;
}

/* Archivo seleccionado */
.file-selected {
  text-align: left;
}

.file-preview {
  display: flex;
  align-items: center;
  background-color: #f3f3f3;
  padding: 10px 15px;
  border-radius: 6px;
  position: relative;
}

.file-preview svg {
  color: #666;
  margin-right: 12px;
}

.file-info {
  flex-grow: 1;
}

.file-name {
  font-weight: 500;
  font-size: 0.9rem;
  color: #333;
  word-break: break-all;
}

.file-size {
  font-size: 0.8rem;
  color: #666;
  margin-top: 2px;
}

.remove-file {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 5px;
  transition: color 0.2s;
}

.remove-file:hover {
  color: #d32f2f;
}

/* Opciones de etiquetado */
.labeling-options {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-option {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.radio-option input[type="radio"] {
  margin-right: 10px;
}

.radio-label {
  font-size: 0.95rem;
  color: #333;
}

/* Zona de archivo CSV */
.csv-zone {
  margin-top: 15px;
  border-color: #e0e0e0;
  background-color: white;
  padding: 20px;
}

.csv-format-info {
  margin-top: 15px;
  font-size: 0.85rem;
  color: #666;
  background-color: #fff;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #eee;
  text-align: center;
}

.csv-format-info p {
  margin: 5px 0;
}

.csv-columns {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 15px 0;
}

.csv-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 45%;
}

.column-number {
  background-color: #e3dacc;
  color: white;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 500;
  margin-bottom: 8px;
}

.column-desc {
  text-align: center;
  line-height: 1.4;
}

.example {
  font-family: monospace;
  background-color: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 10px;
}

/* Barra de progreso */
.upload-progress {
  margin: 15px 0;
}

.progress-bar {
  height: 6px;
  background-color: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: rgb(34, 134, 141);
  transition: width 0.3s;
}

.progress-text {
  font-size: 0.8rem;
  color: #666;
  margin-top: 5px;
  text-align: right;
}

/* Botones de acción */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.app-button {
  margin-top: 0;
  width: auto;
}

.upload-icon {
  margin-right: 8px;
}

/* Responsive */
@media (max-width: 640px) {
  .upload-images-modal {
    padding: 20px 15px;
    max-width: none;
  }
  
  .drop-zone {
    padding: 20px 15px;
  }
  
  .modal-actions {
    flex-direction: column-reverse;
  }
  
  .modal-actions button {
    width: 100%;
  }
}
</style>