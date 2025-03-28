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
                  <p>Arrastra tu archivo CSV aquí o haz clic para seleccionarlo</p>
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
    notifyError("Formato no válido",
    "Por favor, selecciona un archivo ZIP.");
    return;
  }
  
  // Validar tamaño máximo (50MB).
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    notifyError("Archivo demasiado grande",
    "El tamaño del archivo ZIP no puede superar los 50MB.");
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
    notifyError("Formato no válido",
    "Por favor, selecciona un archivo CSV.");
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
<style scoped src="@/assets/styles/upload.css"></style>
<style scoped>
/* Opciones de etiquetado */
.labeling-options {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

/* Zona de archivo CSV */
.csv-zone {
  margin-top: 15px;
  border-color: #e0e0e0;
  background-color: white;
  padding: 20px;
}
</style>