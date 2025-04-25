<template>
  <div class="model-detail-view">
    <div class="back-link">
      <router-link to="/my-models" class="back-button">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
        <span>Volver a Mis modelos de clasificación de imágenes</span>
      </router-link>
    </div>
    <div v-if="isLoading" class="loading-container">
      <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
      <p>Cargando detalles del modelo...</p>
    </div>
    <div v-else-if="error" class="error-container">
      <font-awesome-icon :icon="['fas', 'exclamation-triangle']" size="2x" />
      <p>{{ error }}</p>
    </div>
    <div v-else-if="model" class="model-content">
      <div class="model-header">
        <h1>{{ model.name }}</h1>
        <div class="model-meta">
          <span class="model-status" :class="getStatusClass(model.status)">
            <font-awesome-icon :icon="getStatusIcon(model.status)" />
            {{ getStatusLabel(model.status) }}
          </span>
          <span class="model-date">
            <font-awesome-icon :icon="['fas', 'calendar-alt']" />
            Creado: {{ formatDate(model.created_at) }}
          </span>
        </div>
      </div>
      <div v-if="model.status === 'trained'" class="model-actions">
        <button @click="predictWithModel" class="app-button prediction-button">
          <font-awesome-icon :icon="['fas', 'brain']" class="button-icon" />
          Realizar inferencia
        </button>
        <button @click="downloadModel" class="app-button download-button">
          <font-awesome-icon :icon="['fas', 'download']" class="button-icon" />
          Descargar modelo
        </button>
      </div>
      <div class="model-description" v-if="model.description">
        <h2>Descripción</h2>
        <p>{{ model.description }}</p>
      </div>
      <div class="model-info">
        <h2>Información general</h2>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">Conjunto de imágenes utilizado:</div>
            <div class="info-value">
              <template v-if="datasetName">
                <router-link :to="`/dataset/${model.dataset_id}`" class="dataset-link">
                  {{ datasetName }}
                </router-link>
              </template>
              <template v-else>
                <span class="not-available">No disponible</span>
              </template>
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Fecha de creación:</div>
            <div class="info-value">{{ formatDate(model.created_at) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Tiempo de entrenamiento:</div>
            <div class="info-value">
              <template v-if="model.trained_at">
                {{ calculateTrainingTime(model.created_at, model.trained_at) }}
              </template>
              <template v-else>
                <span class="not-available">No disponible</span>
              </template>
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Fecha de entrenamiento:</div>
            <div class="info-value">
              <template v-if="model.trained_at">
                {{ formatDate(model.trained_at) }}
              </template>
              <template v-else>
                <span class="not-available">No disponible</span>
              </template>
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">Estado:</div>
            <div class="info-value">
              <span class="model-status-text" :class="getStatusTextClass(model.status)">
                {{ getStatusLabel(model.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="model-parameters">
        <h2>Parámetros del modelo</h2>
        <div class="parameters-grid">
          <div class="parameter-item">
            <div class="parameter-label">Arquitectura:</div>
            <div class="parameter-value">{{ getArchitectureLabel(model.architecture) }}</div>
          </div>
          <template v-if="model.model_parameters">
            <div class="parameter-item" v-if="model.model_parameters.learning_rate !== undefined">
              <div class="parameter-label">Tasa de aprendizaje:</div>
              <div class="parameter-value">{{ formatLearningRate(model.model_parameters.learning_rate) }}</div>
            </div>
            <div class="parameter-item" v-if="model.model_parameters.epochs !== undefined">
              <div class="parameter-label">Épocas:</div>
              <div class="parameter-value">{{ model.model_parameters.epochs }}</div>
            </div>
            <div class="parameter-item" v-if="model.model_parameters.batch_size !== undefined">
              <div class="parameter-label">Tamaño del lote:</div>
              <div class="parameter-value">{{ model.model_parameters.batch_size }}</div>
            </div>
            <div class="parameter-item" v-if="model.model_parameters.validation_split !== undefined">
              <div class="parameter-label">División de validación:</div>
              <div class="parameter-value">{{ (model.model_parameters.validation_split * 100).toFixed(0) }}%</div>
            </div>
          </template>
          <template v-else>
            <div class="parameter-item not-available">
              <div class="parameter-value">No hay parámetros disponibles</div>
            </div>
          </template>
        </div>
      </div>
      <div class="model-metrics">
        <h2 v-if="model.status === 'failed'">Error en el entrenamiento</h2>
        <h2 v-else>Métricas del entrenamiento</h2>
        <div v-if="model.status === 'trained'" class="metrics-container">
          <div class="basic-metrics">
            <h3>Rendimiento general</h3>
            <div class="metrics-grid">
              <div class="metric-item" v-if="model.metrics && model.metrics.accuracy !== undefined">
                <div class="metric-label">
                  Precisión (entrenamiento)
                  <HelpTooltip 
                    text="Porcentaje de imágenes correctamente clasificadas durante el entrenamiento."
                    label="precisión de entrenamiento"
                  />
                </div>
                <div class="metric-value">{{ formatPercentage(model.metrics.accuracy) }}</div>
              </div>
              <div class="metric-item" v-if="model.metrics && model.metrics.val_accuracy !== undefined">
                <div class="metric-label">
                  Precisión (validación)
                  <HelpTooltip 
                    text="Porcentaje de imágenes correctamente clasificadas en el conjunto de validación."
                    label="precisión de validación"
                  />
                </div>
                <div class="metric-value">{{ formatPercentage(model.metrics.val_accuracy) }}</div>
              </div>
              <div class="metric-item" v-if="model.metrics && model.metrics.loss !== undefined">
                <div class="metric-label">
                  Pérdida (entrenamiento)
                  <HelpTooltip 
                    text="Medida del error durante el entrenamiento."
                    label="pérdida de entrenamiento"
                  />
                </div>
                <div class="metric-value">{{ model.metrics.loss.toFixed(4) }}</div>
              </div>
              <div class="metric-item" v-if="model.metrics && model.metrics.val_loss !== undefined">
                <div class="metric-label">
                  Pérdida (validación)
                  <HelpTooltip 
                    text="Medida del error en el conjunto de validación."
                    label="pérdida de validación"
                  />
                </div>
                <div class="metric-value">{{ model.metrics.val_loss.toFixed(4) }}</div>
              </div>
            </div>
          </div>
          <div class="confusion-matrix-section" v-if="model.metrics && model.metrics.confusion_matrix">
            <h3>
              Matriz de confusión
              <HelpTooltip 
                text="Muestra cómo se han clasificado las imágenes del conjunto de validación para cada clase. Las filas representan la clase real, las columnas la clase predicha. Los valores en la diagonal principal (verde) son predicciones correctas."
                label="matriz de confusión"
              />
            </h3>
            <div class="confusion-matrix-container">
              <div class="confusion-matrix-wrapper">
                <table class="confusion-matrix">
                  <thead>
                    <tr>
                      <th></th>
                      <th
                        v-for="(_, colIndex) in model.metrics.confusion_matrix[0]"
                        :key="`col-${colIndex}`"
                      >
                        Pred: {{ getClassName(colIndex) }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, rowIndex) in model.metrics.confusion_matrix" :key="`row-${rowIndex}`">
                      <th>Real: {{ getClassName(rowIndex) }}</th>
                      <td
                        v-for="(cell, colIndex) in row"
                        :key="`cell-${rowIndex}-${colIndex}`"
                        :class="{
                          'diagonal': rowIndex === colIndex,
                          'non-diagonal': rowIndex !== colIndex,
                          'zero-value': cell === 0
                        }"
                      >
                        {{ cell }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="confusion-matrix-legend">
                <div class="legend-item">
                  <div class="legend-color diagonal"></div>
                  <div class="legend-text">Predicciones correctas</div>
                </div>
                <div class="legend-item">
                  <div class="legend-color non-diagonal"></div>
                  <div class="legend-text">Predicciones incorrectas</div>
                </div>
                <div class="legend-item">
                  <div class="legend-color zero-value"></div>
                  <div class="legend-text">Sin muestras</div>
                </div>
              </div>
            </div>
          </div>
          <div class="detailed-metrics" v-if="model.metrics && model.metrics.classification_report">
            <h3>Métricas por clase</h3>
            <div class="table-responsive">
              <table class="metrics-table">
                <thead>
                  <tr>
                    <th>Clase</th>
                    <th>Precisión</th>
                    <th>Sensibilidad</th>
                    <th>F1-score</th>
                    <th>Muestras</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(classData, className) in getClassesData()" :key="className">
                    <td>{{ className }}</td>
                    <td>{{ formatPercentage(classData.precision) }}</td>
                    <td>{{ formatPercentage(classData.recall) }}</td>
                    <td>{{ formatPercentage(classData.f1) }}</td>
                    <td>{{ classData.support }}</td>
                  </tr>
                  <tr class="average-row">
                    <td><strong>Promedio (macro)</strong></td>
                    <td>{{ formatPercentage(model.metrics.precision_macro) }}</td>
                    <td>{{ formatPercentage(model.metrics.recall_macro) }}</td>
                    <td>{{ formatPercentage(model.metrics.f1_macro) }}</td>
                    <td>{{ getTotalSamples() }}</td>
                  </tr>
                  <tr class="average-row">
                    <td><strong>Promedio (ponderado)</strong></td>
                    <td>{{ formatPercentage(model.metrics.precision_weighted) }}</td>
                    <td>{{ formatPercentage(model.metrics.recall_weighted) }}</td>
                    <td>{{ formatPercentage(model.metrics.f1_weighted) }}</td>
                    <td>{{ getTotalSamples() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="metrics-explanation">
              <h4>Explicación de las métricas:</h4>
              <ul>
                <li><strong>Precisión:</strong> Proporción de predicciones positivas correctas.</li>
                <li><strong>Sensibilidad (Recall):</strong> Proporción de casos positivos reales identificados correctamente.</li>
                <li><strong>F1-Score:</strong> Media armónica entre precisión y sensibilidad. Equilibra ambas métricas.</li>
                <li><strong>Muestras:</strong> Número de imágenes en la validación para cada clase.</li>
              </ul>
            </div>
          </div>
          <div v-if="!model.metrics || !model.metrics.classification_report" class="empty-metrics">
            <font-awesome-icon :icon="['fas', 'chart-bar']" />
            <p>No hay métricas disponibles para este modelo.</p>
          </div>
        </div>
        <div v-else-if="model.status === 'failed'" class="metrics-container error-metrics">
          <div class="error-message">
            <font-awesome-icon :icon="['fas', 'exclamation-circle']" />
            <p>{{ getErrorMessage(model.metrics) }}</p>
          </div>
        </div>
        <div v-else class="metrics-container">
          <p class="metrics-placeholder not-available">
            Las métricas no están disponibles para este modelo
          </p>
        </div>
      </div>
    </div>
    <PredictionModal 
      :isOpen="showPredictionModal"
      :modelId="model ? model.id : ''"
      :modelName="model ? model.name : ''"
      @close="closePredictionModal"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

import { notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import HelpTooltip from '@/components/utils/HelpTooltip.vue';
import PredictionModal from '@/components/models/PredictionModal.vue';

const showPredictionModal = ref(false);

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const model = ref(null);
const datasetName = ref(null);
const isLoading = ref(true);
const error = ref(null);

const getStatusTextClass = (status) => {
  switch(status) {
    case 'trained':
      return 'status-text-verified';
    case 'training':
      return 'status-text-training';
    case 'failed':
      return 'status-text-failed';
    case 'not_trained':
    default:
      return 'status-text-not-trained';
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const calculateTrainingTime = (startDate, endDate) => {
  if (!startDate || !endDate) return 'No disponible';
  
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffMs = end - start;
  
  const diffMins = Math.floor(diffMs / 60000);
  const diffSecs = Math.floor((diffMs % 60000) / 1000);
  
  if (diffMins < 60) {
    return `${diffMins} min ${diffSecs} s`;
  } else {
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    return `${hours} h ${mins} min ${diffSecs} s`;
  }
};

const getStatusClass = (status) => {
  switch(status) {
    case 'trained':
      return 'status-badge verified';
    case 'training':
      return 'status-badge training';
    case 'failed':
      return 'status-badge failed';
    case 'not_trained':
    default:
      return 'status-badge not-trained';
  }
};

const getStatusLabel = (status) => {
  switch(status) {
    case 'trained':
      return 'Entrenado';
    case 'training':
      return 'Entrenando';
    case 'failed':
      return 'Fallido';
    case 'not_trained':
    default:
      return 'No entrenado';
  }
};

const getStatusIcon = (status) => {
  switch(status) {
    case 'trained':
      return ['fas', 'check-circle'];
    case 'training':
      return ['fas', 'spinner'];
    case 'failed':
      return ['fas', 'exclamation-circle'];
    case 'not_trained':
    default:
      return ['fas', 'circle'];
  }
};

const getArchitectureLabel = (architecture) => {
  const architectureLabels = {
    'xception_mini': 'Xception Mini',
    'resnet50': 'ResNet-50',
    'efficientnetb3': 'EfficientNet-B3',
  };
  
  return architectureLabels[architecture] || architecture;
};

const formatLearningRate = (value) => {
  if (value === undefined || value === null) return 'No disponible';
  
  // Primero convertir a string con suficientes decimales.
  let strValue = value.toFixed(8);
  
  // Eliminar ceros a la derecha.
  strValue = strValue.replace(/\.?0+$/, '');
  
  // Si termina con punto, eliminar.
  if (strValue.endsWith('.')) {
    strValue = strValue.slice(0, -1);
  }
  
  return strValue;
};

const getErrorMessage = (metrics) => {
  if (!metrics || !metrics.error_message) {
    return 'Error desconocido durante el entrenamiento';
  }
  return metrics.error_message;
};

const predictWithModel = () => {
  showPredictionModal.value = true;
};

const closePredictionModal = () => {
  showPredictionModal.value = false;
};

const downloadModel = async () => {
  try {
    const response = await axios({
      url: `/classifiers/${model.value.id}/download`,
      method: 'GET',
      responseType: 'blob',
    });
    
    // Crear un blob y enlace de descarga.
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    // Configurar el nombre del archivo de descarga.
    link.setAttribute('download', `model.zip`);

    // Agregar el enlace al DOM y hacer clic en él para iniciar la descarga.
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 100);
  } catch (error) {
    console.error('Error downloading model: ', error);
    
    if (error.response) {
      const { status } = error.response;
      
      // Para manejar respuestas de error con responseType: 'blob'.
      if (error.response.data instanceof Blob) {
        // Convertir el Blob a texto para leer el mensaje de error JSON.
        const errorText = await error.response.data.text();
        try {
          const errorData = JSON.parse(errorText);
          
          switch (status) {
            case 403:
              if (errorData.detail && errorData.detail.includes("credentials")) {
                notifyInfo("Sesión expirada", 
                "Por favor, inicia sesión de nuevo.");
                authStore.logout();
                router.push('/');
              } else {
                notifyError("Acceso denegado", 
                "No tienes permisos suficientes para realizar esta acción.");
              }
              break;
            case 404:
              notifyError("Modelo no disponible",
              "El modelo no está disponible para descargar o no se ha encontrado");
              break;
            default:
              notifyError("Error en la descarga",
              "No se pudo descargar el modelo. Por favor, inténtalo de nuevo más tarde.");
              break;
          }
        } catch (jsonError) {
          notifyError("Error inesperado",
          "Ha ocurrido un problema.");
        }
      } else {
        // Respuesta JSON.
        const { data } = error.response;
        
        switch (status) {
          case 403:
            if (data && data.detail && data.detail.includes("credentials")) {
              notifyInfo("Sesión expirada", 
              "Por favor, inicia sesión de nuevo.");
              authStore.logout();
              router.push('/');
            } else {
              notifyError("Acceso denegado", 
              "No tienes permisos suficientes para realizar esta acción.");
            }
            break;
          case 404:
            notifyError("Modelo no disponible",
            "El modelo no está disponible para descargar o no se ha encontrado");
            break;
          default:
            notifyError("Error en la descarga",
            "No se pudo descargar el modelo. Por favor, inténtalo de nuevo más tarde.");
            break;
        }
      }
    } else {
      notifyError("Error de conexión",
      "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
    }
  }
};

// Carga de datos.
const fetchModelData = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabezera.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken) {
      authStore.setAuthHeader();
    }

    const modelId = route.params.id;
    const response = await axios.get(`/classifiers/${modelId}/detail`);
    model.value = response.data;
    
    // Si el modelo tiene un dataset_id, intentar obtener su nombre.
    if (model.value.dataset_id) {
      await fetchDatasetName(model.value.dataset_id);
    }
  } catch (err) {
    console.error('Error while loading model data: ', err);
    handleApiError(err);
  } finally {
    isLoading.value = false;
  }
};

const fetchDatasetName = async (datasetId) => {
  try {
    const response = await axios.get(`/datasets/${datasetId}`);
    datasetName.value = response.data.name;
  } catch (err) {
    console.error('Error fetching dataset name: ', err);
    datasetName.value = null;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    
    console.error("Error response: ", data);
    
    switch (status) { 
      case 401:
        router.push('/');
        break;
      case 403:
        if (data && data.detail && typeof data.detail === 'string' && data.detail.includes("credentials")) {
          notifyInfo("Sesión expirada", 
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else {
          notifyError("Acceso denegado", 
          "No tienes permisos suficientes para realizar esta acción.");
        }
        break;
      case 404:
        notifyError("Modelo no encontrado",
        "El modelo solicitado no existe o ha sido eliminado.");
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
    "Ha ocurrido un problema al cargar los datos del modelo.");
  }
};

// Funcinalidad para mostrar las métricas.
const getClassName = (index) => {
  if (!model.value || !model.value.metrics) return `Clase ${index}`;
  
  const classMapping = model.value.metrics.classification_report ? 
    Object.keys(model.value.metrics.classification_report).filter(k => 
      !['accuracy', 'macro avg', 'weighted avg'].includes(k)
    ) : [];
    
  return classMapping[index] || `Clase ${index}`;
};

const formatPercentage = (value) => {
  if (value === undefined || value === null) return 'N/A';
  return `${(value * 100).toFixed(2)}%`;
};

const getClassesData = () => {
  if (!model.value?.metrics?.classification_report) return {};
  
  const report = model.value.metrics.classification_report;
  const classData = {};
  
  Object.entries(report).forEach(([key, value]) => {
    if (!['accuracy', 'macro avg', 'weighted avg'].includes(key)) {
      classData[key] = {
        precision: value.precision,
        recall: value.recall,
        f1: value.f1score || value['f1-score'],
        support: value.support
      };
    }
  });
  
  return classData;
};

const getTotalSamples = () => {
  if (!model.value?.metrics?.num_samples_per_class) return 0;
  
  return Object.values(model.value.metrics.num_samples_per_class)
    .reduce((sum, count) => sum + count, 0);
};

// Cargar datos al montar el componente.
onMounted(() => {
  fetchModelData();
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped>
/* Layout general */
.model-detail-view {
  padding: 20px;
  max-width: 1100px;
  margin: 0 auto;
  padding-top: 80px;
  padding-bottom: 30px;
}

/* Botón de retorno */
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

/* Estados de carga y errores */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 30px;
  color: #666;
}

.loading-container svg,
.error-container svg {
  margin-bottom: 10px;
  font-size: 1.5rem;
}

/* Contenido principal */
.model-content {
  padding: 0;
}

/* Encabezado del modelo */
.model-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.model-header h1 {
  margin: 0;
  color: #333;
  font-size: 1.6rem;
  font-weight: 600;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.model-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #666;
  font-size: 0.85rem;
}

/* Badges de estado */
.model-status {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-badge.verified {
  background-color: #e6fff2;
  color: #00b368;
}

.status-badge.training {
  background-color: #e6f7ff;
  color: #0099cc;
}

.status-badge.failed {
  background-color: #ffe6e6;
  color: #cc0000;
}

.status-badge.not-trained {
  background-color: #f8f9fa;
  color: #6c757d;
}

.model-date {
  display: flex;
  align-items: center;
  gap: 5px;
}

/* Texto de estado */
.model-status-text {
  font-weight: 500;
}

.status-text-verified {
  color: #00b368;
}

.status-text-training {
  color: #0099cc;
}

.status-text-failed {
  color: #cc0000;
}

.status-text-not-trained {
  color: #6c757d;
}

/* Acciones del modelo */
.model-actions {
  display: flex;
  gap: 15px;
  margin-top: 15px;
  margin-bottom: 20px;
  justify-content: center;
  margin-bottom: 30px;
  padding-bottom: 30px;
  border-bottom: 1px solid #eee;
}

.prediction-button,
.download-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.button-icon {
  margin-right: 10px; /* Separación entre el icono y el texto */
  font-size: 1.1em;
}

/* Descripción del modelo */
.model-description {
  margin-bottom: 20px;
  padding: 0 0 15px 0;
  border-bottom: 1px solid #eee;
}

.model-description h2 {
  font-size: 1.1rem;
  margin: 0 0 10px 0;
  color: #444;
  font-weight: 600;
}

.model-description p {
  color: #666;
  line-height: 1.4;
  margin: 0;
  text-align: justify;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* Información general */
.model-info {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.model-info h2 {
  font-size: 1.1rem;
  margin: 0 0 15px 0;
  color: #444;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  grid-auto-columns: minmax(0, 1fr);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  overflow: hidden;
  max-width: 100%;
}

.info-label {
  font-size: 0.85rem;
  color: #777;
  font-weight: 500;
}

.info-value {
  font-size: 0.95rem;
  color: #333;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  white-space: normal;
  min-height: 1.5em;
}

.dataset-link {
  color: rgb(34, 134, 141);
  text-decoration: none;
  transition: color 0.2s;
  display: inline;
  word-break: break-word;
}

.dataset-link:hover {
  text-decoration: underline;
}

.not-available {
  color: #999;
  font-style: italic;
}

/* Parámetros del modelo */
.model-parameters {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.model-parameters h2 {
  font-size: 1.1rem;
  margin: 0 0 15px 0;
  color: #444;
  font-weight: 600;
}

.parameters-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.parameter-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.parameter-label {
  font-size: 0.85rem;
  color: #777;
  font-weight: 500;
}

.parameter-value {
  font-size: 0.95rem;
  color: #333;
}

/* Métricas de entrenamiento */
.model-metrics {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.model-metrics h2 {
  font-size: 1.1rem;
  margin: 0 0 15px 0;
  color: #444;
  font-weight: 600;
}

.metrics-container {
  border-radius: 6px;
  padding: 20px;
}

.metrics-placeholder {
  text-align: center;
  color: #666;
}

.error-metrics {
  background-color: #fff0f0;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #cc0000;
}

.error-message svg {
  margin-top: 3px;
}

.error-message p {
  margin: 0;
  line-height: 1.5;
}

/* Sección de métricas básicas */
.basic-metrics {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.basic-metrics h3,
.confusion-matrix-section h3,
.detailed-metrics h3 {
  font-size: 1rem;
  margin: 0 0 15px 0;
  color: #555;
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.metric-item {
  background-color: #f1eadc;
  border-radius: 6px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric-label {
  font-size: 0.85rem;
  color: #666;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

/* Matriz de confusión */
.confusion-matrix-section {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.confusion-matrix-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.confusion-matrix-wrapper {
  overflow-x: auto;
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.confusion-matrix {
  width: 100%;
  border-collapse: collapse;
  min-width: max-content;
}

.confusion-matrix th,
.confusion-matrix td {
  padding: 10px;
  text-align: center;
  border: 1px solid #eee;
  font-size: 0.9rem;
}

.confusion-matrix thead th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #444;
}

.confusion-matrix tbody th {
  background-color: #f8f9fa;
  font-weight: 600;
  text-align: right;
  color: #444;
}

.confusion-matrix td.diagonal {
  background-color: rgba(46, 204, 113, 0.25);
  font-weight: bold;
}

.confusion-matrix td.non-diagonal {
  background-color: rgba(231, 76, 60, 0.15);
}

.confusion-matrix td.zero-value {
  background-color: #ffffff;
}

.confusion-matrix-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 3px;
}

.legend-color.diagonal {
  background-color: rgba(46, 204, 113, 0.25);
}

.legend-color.non-diagonal {
  background-color: rgba(231, 76, 60, 0.15);
}

.legend-color.zero-value {
  background-color: #ffffff;
  border: 1px solid #ddd;
}

.legend-text {
  font-size: 0.85rem;
  color: #666;
}

/* Métricas detalladas */
.detailed-metrics {
  margin-bottom: 25px;
}

.table-responsive {
  overflow-x: auto;
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
  min-width: max-content;
}

.metrics-table th,
.metrics-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.metrics-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #444;
  font-size: 0.9rem;
}

.metrics-table tr:last-child td {
  border-bottom: none;
}

.metrics-table tr:hover td {
  background-color: #f9f9f9;
}

.metrics-table tr.average-row {
  background-color: #fafafa;
}

.metrics-table tr.average-row td {
  font-weight: 500;
}

.metrics-explanation {
  margin-top: 20px;
  border-radius: 6px;
  padding: 15px;
}

.metrics-explanation h4 {
  margin: 0 0 10px 0;
  font-size: 0.95rem;
  color: #555;
}

.metrics-explanation ul {
  margin: 0;
  padding-left: 20px;
}

.metrics-explanation li {
  margin-bottom: 5px;
  font-size: 0.9rem;
  color: #666;
}

.empty-metrics {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  color: #999;
  gap: 10px;
  text-align: center;
}

.empty-metrics svg {
  font-size: 2rem;
  opacity: 0.5;
}

/* Ajustes para la integración de tooltips */
.metric-label, h3 {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Responsividad */
@media (max-width: 768px) {
  .model-detail-view {
    padding: 15px;
    padding-top: 70px;
  }
  
  .info-grid,
  .parameters-grid {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .model-actions {
    flex-direction: column;
  }
  
  .confusion-matrix th,
  .confusion-matrix td,
  .metrics-table th,
  .metrics-table td {
    padding: 8px;
    font-size: 0.85rem;
  }
  
  .metrics-explanation h4 {
    font-size: 0.9rem;
  }
  
  .metrics-explanation li {
    font-size: 0.85rem;
  }
  
  .metric-value {
    font-size: 1.2rem;
  }
}

@media (max-width: 480px) {
  .confusion-matrix-legend {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .metrics-table th,
  .metrics-table td {
    padding: 6px;
    font-size: 0.8rem;
  }
}
</style>