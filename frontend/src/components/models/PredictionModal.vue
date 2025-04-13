<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal upload-images-modal prediction-modal">
        <button class="close-modal-button" @click="closeModal" :disabled="isProcessing">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2>¡Realiza inferencia con el modelo!</h2>
        <div v-if="!showResults" class="upload-content">
          <p class="info-text">
            <font-awesome-icon :icon="['fas', 'info-circle']" />
            Sube imágenes para realizar inferencia con el modelo seleccionado.
          </p>
          <div class="drop-zone"
            :class="{ 'active-dropzone': isDragging, 'has-file': hasFiles }"
            @dragenter.prevent="dragCounter++; isDragging = true"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
            @click="triggerFileInput"
          >
            <input 
              type="file"
              ref="fileInput"
              accept="image/*"
              class="file-input"
              @change="onFileSelected"
              multiple
            />
            <div v-if="!hasFiles" class="drop-message">
              <font-awesome-icon :icon="['fas', 'images']" size="2x" />
              <p>Arrastra tus imágenes aquí o haz clic para seleccionarlas</p>
              <span class="drop-hint">Formatos soportados: jpg, jpeg, png, gif, webp</span>
            </div>
            <div v-else class="file-selected">
              <div class="file-count">
                <font-awesome-icon :icon="['fas', 'images']" />
                <span>{{ selectedFiles.length }} imagen(es) subida(s)</span>
              </div>
              <div class="selected-files-list">
                <div v-for="(file, index) in selectedFiles" :key="index" class="selected-file">
                  <div class="file-preview">
                    <font-awesome-icon :icon="['fas', 'image']" />
                    <div class="file-info">
                      <div class="file-name">{{ file.name }}</div>
                      <div class="file-size">{{ formatFileSize(file.size) }}</div>
                    </div>
                    <button class="remove-file" @click.stop="removeFile(index)">
                      <font-awesome-icon :icon="['fas', 'times']" />
                    </button>
                  </div>
                </div>
              </div>
              <button class="remove-all-files" @click.stop="resetFiles">
                <font-awesome-icon :icon="['fas', 'trash']" />
                <span>Quitar todo</span>
              </button>
            </div>
          </div>
        </div>
        <div v-else class="prediction-results">
          <div class="result-info">
            <font-awesome-icon :icon="['fas', 'brain']" class="result-icon" />
            <div class="result-summary">
              <h3>Inferencia completada</h3>
              <p>Se han analizado {{ results.length }} imágenes.</p>
            </div>
          </div>
          <div class="results-list">
            <div v-for="(result, index) in results" :key="index" class="result-item">
              <div class="result-img">
                <img :src="`data:image/jpeg;base64,${result.thumbnail}`" alt="Thumbnail" />
              </div>
              <div class="result-content">
                <div class="result-name">{{ getFileName(result.filename) }}</div>
                <div v-if="!result.error" class="result-prediction">
                  <div class="prediction-main">
                    <span class="prediction-class">{{ result.predicted_class }}</span>
                    <span class="prediction-confidence">{{ formatConfidence(result.confidence) }}%</span>
                  </div>
                  <div class="prediction-details">
                    <div v-for="(probability, className) in result.all_predictions" 
                         :key="className" 
                         class="prediction-bar">
                      <div class="bar-label">{{ className }}</div>
                      <div class="bar-container">
                        <div class="bar-fill" 
                             :style="{ width: `${probability * 100}%`, backgroundColor: getClassColor(className, result.predicted_class) }"></div>
                      </div>
                      <div class="bar-value">{{ formatConfidence(probability) }}%</div>
                    </div>
                  </div>
                </div>
                <div v-else class="result-error">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" />
                  <span>{{ result.error }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <template v-if="showResults">
            <div class="modal-actions-left">
              <button 
                class="download-csv-button" 
                @click="downloadResultsAsCSV"
                :disabled="!results.length"
              >
                <font-awesome-icon :icon="['fas', 'file-csv']" />
                Descargar como CSV
              </button>
            </div>
            <button 
              class="app-button" 
              @click="closeModal"
            >
              Aceptar
            </button>
          </template>
          <template v-else>
            <button class="cancel-button" @click="closeModal" :disabled="isProcessing">
              Cancelar
            </button>
            <button 
              class="app-button" 
              @click="predictImages"
              :disabled="!canPredict || isProcessing"
            >
              <span v-if="!isProcessing">
                <font-awesome-icon :icon="['fas', 'brain']" class="upload-icon"/>
                <span>Realizar inferencia</span>
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'spinner']" spin />
                <span></span>
              </span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/authStore";
import { notifyError, notifyInfo } from "@/utils/notifications";

const props = defineProps({
  isOpen: Boolean,
  modelName: {
    type: String,
    default: ''
  },
  modelId: String
});

const emit = defineEmits(["close"]);
const router = useRouter();
const authStore = useAuthStore();

const fileInput = ref(null);
const isDragging = ref(false);
const dragCounter = ref(0);
const selectedFiles = ref([]);
const isProcessing = ref(false);
const results = ref([]);
const showResults = ref(false);

const hasFiles = computed(() => selectedFiles.value.length > 0);
const canPredict = computed(() => selectedFiles.value.length > 0);

// Gestión de eventos de drag and drop.
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
    handleFiles(files);
  }
};

const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click();
  }
};

const onFileSelected = (e) => {
  if (e.target.files.length) {
    handleFiles(e.target.files);
  }
};

const handleFiles = (fileList) => {
  // Filtrar solo imágenes válidas.
  const imageFiles = Array.from(fileList).filter(file => 
    file.type.startsWith('image/') ||
    ['.jpg', '.jpeg', '.png', '.gif', '.webp'].some(ext => 
      file.name.toLowerCase().endsWith(ext)
    )
  );
  
  if (imageFiles.length === 0) {
    notifyInfo("Sin imágenes válidas",
    "No se han seleccionado imágenes válidas.");
    return;
  }
  
  // Añadir a la lista existente.
  selectedFiles.value = [...selectedFiles.value, ...imageFiles];
};

const resetFiles = () => {
  selectedFiles.value = [];
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
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

const getFileName = (fullPath) => {
  if (!fullPath) return 'Sin nombre';
  // Extraer solo el nombre de archivo sin la ruta.
  const parts = fullPath.split(/[\\\/]/);
  return parts[parts.length - 1];
};

// Función para formatear la confianza de la predicción (que salga en pocentaje).
const formatConfidence = (value) => {
  return (value * 100).toFixed(1);
};

const getClassColor = (className, predictedClass) => {
  return className === predictedClass ? '#4CAF50' : '#9E9E9E';
};

const predictImages = async () => {
  if (isProcessing.value || !canPredict.value) return;
  
  isProcessing.value = true;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem("token") || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    const formData = new FormData();
    
    // Añadir cada imagen al formData.
    selectedFiles.value.forEach(file => {
      formData.append("files", file);
    });
    
    const response = await axios.post(
      `/classifiers/${props.modelId}/predict`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      }
    );
    
    // Guardar resultados y mostrar vista de resultados.
    results.value = response.data.results;
    showResults.value = true;
    
  } catch (error) {
    console.error("Error while predicting images: ", error);
    handleApiError(error);
  } finally {
    isProcessing.value = false;
  }
};

const closeModal = () => {
  if (isProcessing.value) return;
  
  resetFiles();
  showResults.value = false;
  results.value = [];
  emit('close');
};

const downloadResultsAsCSV = () => {
  if (!results.value || results.value.length === 0) {
    notifyInfo("Sin datos",
    "No hay resultados para descargar");
    return;
  }
  
  try {
    // Obtener todas las clases únicas de todos los resultados.
    const allClasses = new Set();
    results.value.forEach(result => {
      if (result.all_predictions) {
        Object.keys(result.all_predictions).forEach(className => {
          allClasses.add(className);
        });
      }
    });
    
    // Crear array con nombres de columnas (encabezados).
    const headers = ['Nombre de archivo', 'Clase predicha', 'Confianza', ...Array.from(allClasses)];
    
    // Crear filas de datos.
    const rows = results.value.map(result => {
      const row = [
        getFileName(result.filename),
        result.error ? 'ERROR' : result.predicted_class,
        result.error ? 'N/A' : result.confidence.toFixed(4)
      ];
      
      // Añadir valores de predicción para cada clase.
      allClasses.forEach(className => {
        if (result.error) {
          row.push('N/A');
        } else {
          const probability = result.all_predictions[className] || 0;
          row.push(probability.toFixed(4));
        }
      });
      
      return row;
    });
    
    // Combinar encabezados y filas.
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    // Crear blob y enlace de descarga.
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'resultados.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 100);
  } catch (error) {
    console.error("Error generando CSV: ", error);
    notifyError("Error al generar CSV",
    "No se pudo generar el archivo CSV");
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
          notifyError("Acceso denegado",
          "No tienes permiso para realizar esta acción.");
        } else {
          notifyError("Acceso denegado",
          "No tienes permiso para realizar esta acción.");
        }
        break;
      case 404:
        notifyError("Modelo no encontrado",
        "El modelo solicitado no existe o ha sido eliminado.");
        break;
      case 400:
        notifyError("Modelo no disponible",
        "El modelo no está entrenado o no está disponible para inferencia.");
        break;
      default:
        notifyError("Error en el servidor",
        "No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.");
        break;
    }
  } else if (error.request) {
    notifyError("Error de conexión", "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", "Ha ocurrido un problema al procesar las imágenes.");
  }
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/upload.css"></style>
<style scoped>
.prediction-modal {
  width: 90%;
  max-width: 700px;
}

.info-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.info-text svg {
  color: #3498db;
}

.selected-files-list {
  max-height: 200px;
  overflow-y: auto;
  margin: 10px 0;
}

.selected-file {
  margin-bottom: 8px;
}

.file-count {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #333;
  padding: 8px 10px;
  background-color: #e9f5f6;
  border-radius: 6px;
}

.remove-all-files {
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  padding: 8px 12px;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  transition: background-color 0.2s;
}

.remove-all-files:hover {
  background-color: #e0e0e0;
  color: #333;
}

/* Resultados de predicción */
.prediction-results {
  max-height: 500px;
  overflow-y: auto;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background-color: #f5f8fb;
  border-radius: 8px;
  margin-bottom: 20px;
}

.result-icon {
  font-size: 2rem;
  color: #3498db;
}

.result-summary h3 {
  margin: 0 0 5px 0;
  color: #333;
}

.result-summary p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  border-radius: 8px;
  background-color: #fff;
  border: 1px solid #eee;
  transition: transform 0.2s;
}

.result-img {
  width: 100px;
  height: 100px;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 6px;
  overflow: hidden;
}

.result-img img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.result-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-name {
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
  word-break: break-all;
}

.result-prediction {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prediction-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.prediction-class {
  font-weight: 600;
  color: #4CAF50;
  font-size: 1.1rem;
}

.prediction-confidence {
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.prediction-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 5px;
}

.prediction-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.85rem;
}

.bar-label {
  width: 80px;
  text-align: right;
  color: #555;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-container {
  flex: 1;
  height: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background-color: #9E9E9E;
  transition: width 0.3s;
}

.bar-value {
  width: 50px;
  text-align: right;
  color: #555;
  font-weight: 500;
}

.result-error {
  color: #d32f2f;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

/* Botón de descarga del CSV */
.download-csv-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 15px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background-color 0.2s;
  height: 100%;
}

.download-csv-button:hover {
  background-color: #5a6268;
}

.download-csv-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.download-csv-button svg {
  font-size: 0.9rem;
}

.modal-actions-left {
  margin-right: auto;
}
/* Responsive */
@media (max-width: 600px) {
  .result-item {
    flex-direction: column;
  }
  
  .result-img {
    width: 100%;
    height: 120px;
  }
  
  .prediction-bar {
    flex-wrap: wrap;
  }
  
  .bar-label {
    width: 100%;
    text-align: left;
  }
}
</style>