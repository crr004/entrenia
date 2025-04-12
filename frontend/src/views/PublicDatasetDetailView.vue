<template>
  <div class="dataset-detail-view">
    <div class="back-link">
      <router-link to="/explore" class="back-button">
        <font-awesome-icon :icon="['fas', 'arrow-left']" />
        <span>Volver a Explorar</span>
      </router-link>
    </div>
    <div v-if="isLoading" class="loading-container">
      <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
      <p>Cargando detalles del conjunto de imágenes...</p>
    </div>
    <div v-else-if="error" class="error-container">
      <font-awesome-icon :icon="['fas', 'exclamation-circle']" size="2x" />
      <h3>{{ error.title }}</h3>
      <p>{{ error.message }}</p>
    </div>
    <div v-else-if="dataset" class="dataset-content">
      <div class="dataset-header">
        <h1>{{ dataset.name }}</h1>
        <div class="dataset-meta">
          <span class="dataset-visibility public">
            <font-awesome-icon :icon="['fas', 'globe']" />
            <span>Compartido</span>
          </span>
          <span class="dataset-user">
            <font-awesome-icon :icon="['fas', 'user']" />
            <span>{{ dataset.username }}</span>
          </span>
          <span class="dataset-date">
            <font-awesome-icon :icon="['fas', 'calendar-alt']" />
            <span>Creado: {{ formatDate(dataset.created_at) }}</span>
          </span>
        </div>
      </div>
      <div v-if="isAuthenticated" class="dataset-actions">
        <button 
            class="app-button clone-button"
            @click="showCloneConfirmation"
          >
            <font-awesome-icon :icon="['fas', 'plus-circle']" />
            Clonar conjunto de imágenes
        </button>
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
        </div>
      </div>
      <div class="images-section">
        <h2>Imágenes</h2>
        <ReadOnlyImagesTable 
          v-if="dataset && dataset.id" 
          :datasetId="dataset.id"
        />
      </div>
    </div>
    <ConfirmationModal
      :is-open="showCloneModal"
      title="Clonar conjunto de imágenes"
      :message="`Se guardará una copia del conjunto de imágenes en tu biblioteca personal. ¿Deseas continuar?`"
      confirm-text="Clonar conjunto"
      cancel-text="Cancelar"
      button-type="success"
      :is-loading="isCloning"
      @confirm="confirmCloneDataset"
      @cancel="cancelCloneDataset"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import Chart from 'chart.js/auto';

import { notifyError, notifySuccess, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ConfirmationModal from '@/components/utils/ConfirmationModal.vue';
import ReadOnlyImagesTable from '@/components/images/ReadOnlyImagesTable.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const isAuthenticated = computed(() => authStore.isAuthenticated);
const userId = computed(() => {
  if (!isAuthenticated.value || !authStore.user) return null;
  return authStore.user.id;
});

const dataset = ref(null);
const labelDetails = ref(null);
const isLoading = ref(true);
const error = ref(null);
const pieChart = ref(null);
const chartInstance = ref(null);

const showCloneModal = ref(false);
const isCloning = ref(false);

const totalLabeledImages = computed(() => {
  if (!labelDetails.value || !labelDetails.value.categories) return 0;
  return labelDetails.value.categories.reduce((sum, category) => sum + category.image_count, 0);
});

const fetchData = async () => {
  isLoading.value = true;
  error.value = null;
  
  try {
    const datasetId = route.params.id;
    
    const headers = {};
    
    // Añadir token de autenticación solo si el usuario está logueado.
    if (authStore.isAuthenticated) {
      const token = authStore.token || localStorage.getItem('token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }
    
    // Cargar datos básicos del dataset y detalles de etiquetas en paralelo.
    const [datasetResponse, labelDetailsResponse] = await Promise.all([
      axios.get(`/datasets/public/${datasetId}`, { headers }),
      axios.get(`/datasets/public/${datasetId}/label-details`, { headers })
    ]);
    
    dataset.value = datasetResponse.data;
    labelDetails.value = labelDetailsResponse.data;
    
    if (isAuthenticated.value && userId.value && dataset.value.user_id === userId.value) {
      // Si el usuario es el propietario del dataset, redirigir a la vista personal.
      router.replace({ name: 'dataset-detail', params: { id: datasetId }});
      return;
    }
    
    // Crear gráfico después de que los datos estén disponibles.
    setTimeout(() => {
      createChart();
    }, 0);
    
  } catch (error) {
    console.error('Error while loading dataset data: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
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
  }).format(date);
};

const showCloneConfirmation = () => {
  if (!isAuthenticated.value) {
    notifyInfo("Inicia sesión para continuar", 
    "Debes iniciar sesión para añadir conjuntos a tu biblioteca.");
    router.push('/');
    return;
  }
  
  showCloneModal.value = true;
};

const cancelCloneDataset = () => {
  showCloneModal.value = false;
};

const confirmCloneDataset = async () => {
  try {
    isCloning.value = true;
    
    // Llamar al endpoint para clonar el dataset.
    const response = await axios.post(`/datasets/${dataset.value.id}/clone`);
    
    // Cerrar el modal.
    showCloneModal.value = false;
    
    // Notificar éxito.
    notifySuccess("Conjunto de imágenes añadido",
    "Se ha añadido el conjunto de imágenes con éxito.");
    
    // Redirigir al usuario a la vista de detalle del dataset clonado, ya en su biblioteca personal.
    router.push({ name: 'dataset-detail', params: { id: response.data.id } });
    
  } catch (error) {
    console.error('Error cloning dataset: ', error);
    handleApiError(error);
  } finally {
    isCloning.value = false;
  }
};


const handleApiError = (error) => {
  if (error.response) {
    const { status, data, headers } = error.response;
    
    console.error("Error response: ", data);
    
    if (status === 409 && headers['x-dataset-id']) {
      showCloneModal.value = false;
      router.push({ name: 'dataset-detail', params: { id: headers['x-dataset-id'] } });
      return;
    }
    
    if (status === 401) {
      // Es normal que no esté autenticado, ya que la página es pública.
      // Este error no debería ocurrir.
      authStore.logout();
      router.push('/');
    } else if (status === 403) {
      if (data.detail && data.detail.includes("credentials")) {
        notifyInfo("Sesión expirada",
        "Por favor, inicia sesión de nuevo.");
        authStore.logout();
        router.push('/');
      } else {
        notifyError("Acceso denegado", 
        "Este conjunto no es público y no puede ser añadido a tu biblioteca.");
      }
    } else if (status === 404) {
      notifyError("Conjunto no encontrado", 
      "El conjunto solicitado ya no existe o ha sido eliminado.");
    } else if (status === 400 || status === 500) {
      notifyError("Error del servidor al clonar el conjunto",
      `Detalle: ${data.detail || "No se pudo clonar el conjunto."}`);
    } else {
      notifyError("Error inesperado", 
      "Ha ocurrido un problema al cargar los datos del conjunto de imágenes.");
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", 
    "Ha ocurrido un problema al cargar los datos del conjunto de imágenes.");
  }
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
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/dataset-detail.css"></style>
<style scoped>
/* Ajustes específicos para este componente */
.dataset-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #666;
  font-size: 0.85rem;
  align-items: center;
}

.dataset-meta > span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.dataset-user, .dataset-date {
  display: flex;
  align-items: center;
  gap: 5px;
}

.images-section h2 {
  font-size: 1.1rem;
  color: #444;
  font-weight: 600;
  margin-bottom: 15px;
}
</style>