<template>
  <div class="dataset-detail-view">
    <div class="back-link">
      <router-link to="/my-datasets" class="back-button">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
        <span>Volver a Mis conjuntos de imágenes</span>
      </router-link>
    </div>
    <div v-if="isLoading" class="loading-container">
      <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
      <p>Cargando detalles del conjunto de imágenes...</p>
    </div>
    <div v-else-if="dataset" class="dataset-content">
      <div class="dataset-header">
        <h1>{{ dataset.name }}</h1>
        <div class="dataset-meta">
          <span class="dataset-visibility" :class="dataset.is_public ? 'public' : 'private'">
            <font-awesome-icon :icon="['fas', dataset.is_public ? 'globe' : 'lock']" />
            {{ dataset.is_public ? 'Compartido' : 'Privado' }}
          </span>
          <span class="dataset-date">
            <font-awesome-icon :icon="['fas', 'calendar-alt']" />
            Creado: {{ formatDate(dataset.created_at) }}
          </span>
        </div>
      </div>
      <div class="dataset-description" v-if="dataset.description">
        <h2>Descripción</h2>
        <p>{{ dataset.description }}</p>
      </div>
      <div class="dataset-stats">
        <div class="stat-item">
          <div class="stat-icon">
            <font-awesome-icon :icon="['fas', 'images']" />
          </div>
          <div class="stat-data">
            <span class="stat-value">{{ dataset.image_count }}</span>
            <span class="stat-label">Imágenes</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <font-awesome-icon :icon="['fas', 'check-circle']" />
          </div>
          <div class="stat-data">
            <span class="stat-value">{{ labelDetails?.labeled_images || 0 }}</span>
            <span class="stat-label">Etiquetadas</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <font-awesome-icon :icon="['fas', 'question-circle']" />
          </div>
          <div class="stat-data">
            <span class="stat-value">{{ labelDetails?.unlabeled_images || 0 }}</span>
            <span class="stat-label">Sin etiquetar</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon">
            <font-awesome-icon :icon="['fas', 'tags']" />
          </div>
          <div class="stat-data">
            <span class="stat-value">{{ dataset.category_count }}</span>
            <span class="stat-label">Categorías</span>
          </div>
        </div>
      </div>
      <div class="categories-content">
        <h2>Categorías</h2>
        <div v-if="labelDetails && labelDetails.categories.length > 0" class="categories-data">
          <div class="categories-table-wrapper">
            <table class="categories-table">
              <thead>
                <tr>
                  <th>Categoría</th>
                  <th>Imágenes</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="category in labelDetails.categories" :key="category.name">
                  <td>{{ category.name }}</td>
                  <td>{{ category.image_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="categories-chart">
            <canvas ref="pieChart"></canvas>
          </div>
        </div>
        <div v-else-if="labelDetails && labelDetails.categories.length === 0" class="empty-state">
          <font-awesome-icon :icon="['fas', 'tags']" />
          <p>Este conjunto aún no tiene categorías definidas.</p>
          <p class="empty-hint">Añade imágenes y etiquétalas para crear categorías.</p>
        </div>
      </div>
      <div class="images-section">
        <div class="section-header">
          <h2>Imágenes</h2>
          <div class="action-buttons">
            <button 
              class="app-button" 
              @click="handleLabelImages"
              :disabled="!labelDetails?.unlabeled_images || labelDetails.unlabeled_images === 0"
            >
              <font-awesome-icon :icon="['fas', 'tags']" />
              <span>Etiquetar imágenes</span>
            </button>
            <button class="app-button" @click="handleUploadImages">
              <font-awesome-icon :icon="['fas', 'upload']" />
              <span>Subir imágenes</span>
            </button>
          </div>
        </div>
        <ImagesTable 
          v-if="dataset.id" 
          :datasetId="dataset.id"
          @refresh-dataset-stats="fetchData(true)"
          ref="imagesTableRef"
        />
      </div>
      <UploadImagesModal 
        :isOpen="isUploadModalOpen" 
        :datasetId="dataset?.id"
        @close="closeUploadModal"
        @images-uploaded="handleImagesUploaded"
      />
      <UploadResultModal
        :show="showResultModal"
        :stats="uploadStats"
        :invalidImageDetails="invalidImageDetails"
        :duplicatedImageDetails="duplicatedImageDetails"
        :skippedLabelDetails="skippedLabelDetails"
        @close="handleCloseResultModal"
        @view-images="handleViewImages"
      />
      <LabelingMethodModal
        :isOpen="isLabelingMethodModalOpen"
        :unlabeledCount="labelDetails?.unlabeled_images || 0"
        @close="closeLabelingMethodModal"
        @select-method="handleSelectLabelingMethod"
      />
      <ManualLabelingModal
        :isOpen="isManualLabelingModalOpen"
        :datasetId="dataset?.id"
        @close="closeManualLabelingModal"
        @images-labeled="handleImagesLabeled"
      />
      <CsvLabelingModal
        :isOpen="isCsvLabelingModalOpen"
        :datasetId="dataset?.id"
        @close="closeCsvLabelingModal"
        @images-labeled="handleImagesLabeled"
      />
      <LabelingResultsModal
        :isOpen="isLabelingResultModalOpen"
        :result="labelingResultData"
        @close="closeLabelingResultModal"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import Chart from 'chart.js/auto';

import { notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ImagesTable from '@/components/images/ImagesTable.vue';
import UploadImagesModal from '@/components/images/UploadImagesModal.vue';
import UploadResultModal from '@/components/images/UploadResultModal.vue';
import LabelingMethodModal from '@/components/images/LabelingMethodModal.vue';
import ManualLabelingModal from '@/components/images/ManualLabelingModal.vue';
import CsvLabelingModal from '@/components/images/CsvLabelingModal.vue';
import LabelingResultsModal from '@/components/images/LabelingResultsModal.vue';

const isLabelingMethodModalOpen = ref(false);
const isManualLabelingModalOpen = ref(false);
const isCsvLabelingModalOpen = ref(false);
const isLabelingResultModalOpen = ref(false);

const labelingResultData = ref({
  labeledCount: 0,
  notFoundCount: 0,
  notFoundDetails: []
});

const imagesTableRef = ref(null);

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const pieChart = ref(null);
const chartInstance = ref(null);
const dataset = ref(null);
const labelDetails = ref(null);
const isLoading = ref(true);

const viewScrollPosition = ref(0);

const saveViewScrollPosition = () => {
  viewScrollPosition.value = window.scrollY;
};

const restoreViewScrollPosition = () => {
  nextTick(() => {
    setTimeout(() => {
      window.scrollTo({
        top: viewScrollPosition.value,
        behavior: 'instant'
      });
    }, 10);
  });
};

const isUploadModalOpen = ref(false);
const showResultModal = ref(false);
const uploadStats = ref({
  processed_images: 0,
  skipped_images: 0,
  invalid_images: 0,
  csv_labels_found: 0
});

// Detalles del modal de resultados.
const invalidImageDetails = ref([]);
const duplicatedImageDetails = ref([]);
const skippedLabelDetails = ref([]);

const totalLabeledImages = computed(() => {
  if (!labelDetails.value || !labelDetails.value.categories) return 0;
  return labelDetails.value.categories.reduce((sum, category) => sum + category.image_count, 0);
});

const fetchData = async (maintainScrollPosition = false) => {
  if (maintainScrollPosition) {
    saveViewScrollPosition();
  }
  
  if (!maintainScrollPosition) {
    isLoading.value = true;
  }
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    const datasetId = route.params.id;
    
    // Cargar datos básicos del dataset y detalles de etiquetas en paralelo.
    const [datasetResponse, labelDetailsResponse] = await Promise.all([
      axios.get(`/datasets/${datasetId}`),
      axios.get(`/datasets/${datasetId}/label-details`)
    ]);
    
    dataset.value = datasetResponse.data;
    labelDetails.value = labelDetailsResponse.data;
    
    // Crear gráfico después de que los datos estén disponibles.
    // El timeout de 0ms espera al siguiente tick del event loop para asegurarse de que el DOM esté listo.
    setTimeout(() => {
      createChart();
    }, 0);
    
    if (maintainScrollPosition) {
      restoreViewScrollPosition();
    }
    
  } catch (error) {
    console.error('Error while loading dataset data: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
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
        "El conjunto solicitado no existe o ha sido eliminado.");
        router.push('/my-datasets');
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
    "Ha ocurrido un problema al cargar los datos del conjunto de imágenes.");
  }
};

const createChart = () => {
  if (!labelDetails.value || !labelDetails.value.categories || labelDetails.value.categories.length === 0) {
    return;
  }
  
  // Destruir gráfico anterior si existe.
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
  
  // Preparar datos para el gráfico.
  const labels = labelDetails.value.categories.map(cat => cat.name);
  const data = labelDetails.value.categories.map(cat => cat.image_count);
  
  const baseColors = [
    '#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
    '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
  ];
  
  // Generar colores adicionales si hay más categorías que colores base.
  let backgroundColors = [...baseColors];
  if (labels.length > baseColors.length) {
    for (let i = 0; i < labels.length - baseColors.length; i++) {
      const hue = (i * 137.5) % 360; // Espaciado de colores en el círculo de color HSL.
      backgroundColors.push(`hsl(${hue}, 70%, 60%)`);
    }
  }
  
  backgroundColors = backgroundColors.slice(0, labels.length);
  
  // Crear el gráfico de pastel.
  const ctx = pieChart.value.getContext('2d');
  chartInstance.value = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: backgroundColors,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          left: 0,
          right: 0,
          top: 5,
          bottom: 5
        }
      },
      plugins: {
        legend: {
          position: 'right',
          align: 'center',
          labels: {
            boxWidth: 12,
            font: {
              size: 11
            },
            padding: 8,
            usePointStyle: true,
          },
          maxWidth: 170,
          maxHeight: 260
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.raw;
              const percentage = ((value / totalLabeledImages.value) * 100).toFixed(1);
              return `${context.label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
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

// Recargar datos al cambiar el ID del dataset en la URL.
watch(() => route.params.id, async (newId, oldId) => {
  if (newId !== oldId) {
    await fetchData();
  }
});

// Cargar datos al montar el componente.
onMounted(async () => {
  await fetchData();
});

const handleLabelImages = () => {
  if (!labelDetails.value?.unlabeled_images || labelDetails.value.unlabeled_images === 0) {
    notifyInfo("No hay imágenes sin etiquetar", 
    "Todas las imágenes en este conjunto ya tienen etiquetas.");
    return;
  }
  
  // Abrir el modal de selección de método de etiquetado.
  isLabelingMethodModalOpen.value = true;
};

const handleUploadImages = () => {
  isUploadModalOpen.value = true;
};

const closeUploadModal = () => {
  isUploadModalOpen.value = false;
};

const handleImagesUploaded = (result) => {
  // Cerrar explícitamente el modal de carga.
  isUploadModalOpen.value = false;
  
  // Actualizar estadísticas de carga.
  uploadStats.value = {
    processed_images: result.processed_images || 0,
    skipped_images: result.skipped_images || 0,
    invalid_images: result.invalid_images || 0,
    labels_applied: result.labels_applied || 0,
    labels_skipped: result.labels_skipped || 0
  };
  
  // Actualizar detalles disponibles.
  invalidImageDetails.value = result.invalid_image_details || [];
  duplicatedImageDetails.value = result.duplicated_image_details || [];
  skippedLabelDetails.value = result.skipped_label_details || [];
  
  // Mostrar el modal de resultados.
  showResultModal.value = true;
  
  // Recargar datos del dataset (datos de la vista de detalle en la que está el ususario).
  fetchData();
};

const handleCloseResultModal = () => {
  showResultModal.value = false;

  const imagesSection = document.querySelector('.images-section');
  if (imagesSection) {
    imagesSection.scrollIntoView({ behavior: 'smooth' });
  }
};

// Desplazar a la sección de imágenes después de cerrar el modal de resultados.
const handleViewImages = () => {
  showResultModal.value = false;
  const imagesSection = document.querySelector('.images-section');
  if (imagesSection) {
    imagesSection.scrollIntoView({ behavior: 'smooth' });
  }
};

const closeLabelingMethodModal = () => {
  isLabelingMethodModalOpen.value = false;
};

const handleSelectLabelingMethod = (method) => {
  // Cerrar el modal de método de etiquetado.
  isLabelingMethodModalOpen.value = false;
  
  // Abrir el modal correspondiente según el método seleccionado.
  if (method === 'manual') {
    isManualLabelingModalOpen.value = true;
  } else if (method === 'csv') {
    isCsvLabelingModalOpen.value = true;
  }
};

const closeManualLabelingModal = () => {
  isManualLabelingModalOpen.value = false;
};

const closeCsvLabelingModal = () => {
  isCsvLabelingModalOpen.value = false;
};

const closeLabelingResultModal = () => {
  isLabelingResultModalOpen.value = false;
  
  const imagesSection = document.querySelector('.images-section');
  if (imagesSection) {
    imagesSection.scrollIntoView({ behavior: 'smooth' });
  }
};

const handleImagesLabeled = (result) => {
  
  labelingResultData.value = {
    labeledCount: result.labeledCount || 0,
    notFoundCount: result.notFoundCount || 0,
    notFoundDetails: result.notFoundDetails || []
  };
  
  // Cerrar el modal de etiquetado (tanto manual como CSV).
  isManualLabelingModalOpen.value = false;
  isCsvLabelingModalOpen.value = false;
  
  // Mostrar el modal de resultados.
  isLabelingResultModalOpen.value = true;
  
  // Actualizar datos del dataset.
  fetchData();
  
  // Actualizar la tabla de imágenes.
  nextTick(() => {
    if (imagesTableRef.value && typeof imagesTableRef.value.fetchImages === 'function') {
      imagesTableRef.value.fetchImages(true);
    }
  });
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped>
.dataset-detail-view {
  padding: 20px;
  max-width: 1100px;
  margin: 0 auto;
  padding-top: 80px;
  padding-bottom: 30px;
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

/* Estados de carga y errores */
.loading-container,
.error-container,
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 30px;
  color: #666;
}

.loading-container svg,
.error-container svg,
.not-found-container svg {
  margin-bottom: 10px;
  font-size: 1.5rem;
}

.dataset-content {
  padding: 0;
}

/* Encabezado del dataset */
.dataset-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.dataset-header h1 {
  margin: 0;
  color: #333;
  font-size: 1.6rem;
  font-weight: 600;
}

.dataset-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #666;
  font-size: 0.85rem;
}

/* Indicadores de visibilidad */
.dataset-visibility {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.dataset-visibility.public {
  background-color: #e6f3ff;
  color: #0066cc;
}

.dataset-visibility.private {
  background-color: #f8f9fa;
  color: #495057;
}

.dataset-date {
  display: flex;
  align-items: center;
  gap: 5px;
}

/* Descripción del dataset */
.dataset-description {
  margin-bottom: 20px;
  padding: 0 0 15px 0;
  border-bottom: 1px solid #eee;
}

.dataset-description h2 {
  font-size: 1.1rem;
  margin: 0 0 10px 0;
  color: #444;
  font-weight: 600;
}

.dataset-description p {
  color: #666;
  line-height: 1.4;
  margin: 0;
  text-align: justify;
}

/* Estadísticas del dataset */
.dataset-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.stat-item {
  flex: 1;
  min-width: 120px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e3dacc;
  color: #c0a370;
  border-radius: 50%;
  font-size: 1.1rem;
}

.stat-data {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 0.8rem;
  color: #666;
}

/* Sección de categorías */
.categories-content {
  margin-bottom: 20px;
}

.categories-content h2 {
  font-size: 1.1rem;
  margin: 0 0 15px 0;
  color: #444;
  font-weight: 600;
}

.categories-data {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  align-items: start;
}

/* Tabla de categorías */
.categories-table-wrapper {
  border: 1px solid #eee;
  border-radius: 6px;
  overflow: hidden;
  max-height: 300px;
  overflow-y: auto;
  background-color: #fff;
  display: inline-block;
  min-width: 280px;
  max-width: 100%;
}

.categories-table {
  width: 100%;
  border-collapse: collapse;
}

.categories-table th,
.categories-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
  white-space: nowrap;
}

.categories-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #555;
  font-size: 0.9rem;
}

.categories-table td {
  font-size: 0.9rem;
}

.categories-table th:last-child,
.categories-table td:last-child {
  text-align: right;
  padding-left: 30px;
}

/* Gráfico de categorías */
.categories-chart {
  height: 280px;
  position: relative;
  width: 100%;
  max-width: 420px;
  margin-left: auto;
  margin-right: 10px;
}

/* Estado vacío */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  border-radius: 6px;
  color: #666;
  text-align: center;
}

.empty-state svg {
  margin-bottom: 10px;
  font-size: 1.5rem;
  color: #aaa;
}

.empty-hint {
  font-size: 0.85rem;
  color: #999;
  margin-top: 5px;
}

/* Sección de imágenes */
.images-section {
  margin-top: 30px;
}

.images-section h2 {
  font-size: 1.1rem;
  color: #444;
  font-weight: 600;
  margin-bottom: 15px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.action-buttons .app-button {
  margin-top: 0;
  padding: 8px 12px;
  font-size: 0.9rem;
  width: auto;
}

.action-buttons .app-button svg {
  margin-right: 8px;
}

/* Estilos responsive */
@media (max-width: 1100px) {
  .categories-chart {
    margin-left: 0;
    margin-right: 0;
  }
}

@media (max-width: 1000px) {
  .categories-data {
    gap: 10px;
  }
  
  .categories-chart {
    max-width: 380px;
  }
}

@media (max-width: 900px) {
  .categories-data {
    grid-template-columns: 1fr;
    justify-items: start;
  }
  
  .categories-chart {
    display: none;
  }
  
  .categories-table-wrapper {
    width: auto;
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .dataset-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .dataset-detail-view {
    padding: 15px;
    padding-top: 70px;
  }
  
  .dataset-header h1 {
    font-size: 1.4rem;
  }
  
  .stat-icon {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
  
  .stat-value {
    font-size: 1.1rem;
  }
  
  .stat-label {
    font-size: 0.75rem;
  }
  
  .categories-table-wrapper {
    max-height: 200px;
  }
  
  .categories-table th,
  .categories-table td {
    padding: 8px;
    font-size: 0.85rem;
  }
}

@media (max-width: 640px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .action-buttons {
    width: 100%;
  }
  
  .action-buttons .app-button {
    flex: 1;
  }
}
</style>