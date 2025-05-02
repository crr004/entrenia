<template>
  <div class="explore-view">
    <div class="page-header">
      <h1>¡Explora conjuntos de imágenes!</h1>
      <div class="page-description">
        <p>Descubre conjuntos de imágenes compartidos por otros usuarios de EntrenIA.</p>
      </div>
    </div>
    <div class="search-container">
      <div class="search-box">
        <font-awesome-icon 
          :icon="['fas', 'search']" 
          class="search-icon" 
          @click="executeSearch"
        />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Buscar por usuario, nombre o descripción..." 
          class="search-input"
          @keyup.enter="executeSearch"
        />
        <button 
          v-if="searchQuery" 
          class="clear-search-button" 
          @click="clearSearch"
          title="Limpiar búsqueda"
        >
          <font-awesome-icon :icon="['fas', 'times']" />
        </button>
      </div>
    </div>
    <div class="page-size-container">
      <div class="page-size-selector">
        <label for="pageSize">Mostrar:</label>
        <select id="pageSize" v-model="pageSize" @change="resetPagination">
          <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}</option>
        </select>
      </div>
    </div>
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner">
        <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="3x" />
      </div>
      <p>Cargando conjuntos de imágenes públicos...</p>
    </div>
    <div v-else-if="datasets.length === 0" class="no-results">
      <font-awesome-icon :icon="['fas', 'search']" class="no-results-icon" />
      <h3>No se encontraron resultados</h3>
      <p v-if="searchQuery">No hay conjuntos compartidos que coincidan con tu búsqueda.</p>
      <p v-else>No hay conjuntos compartidos disponibles en este momento.</p>
    </div>
    <div v-else class="dataset-cards">
      <div v-for="dataset in datasets" :key="dataset.id" class="dataset-card" @click="viewDataset(dataset)">
        <div class="card-header">
          <h3 class="dataset-name">{{ dataset.name }}</h3>
          <div class="dataset-user">
            <font-awesome-icon :icon="['fas', 'user']" />
            <span>{{ dataset.username }}</span>
          </div>
        </div>
        <div class="card-body">
          <div class="description-container">
            {{ formatDescription(dataset.description || 'Sin descripción') }}
          </div>
        </div>
        <div class="card-footer">
          <div class="dataset-stats">
            <div class="stat-item">
              <font-awesome-icon :icon="['fas', 'image']" />
              <span>{{ dataset.image_count }} imágenes</span>
            </div>
            <div class="stat-item">
              <font-awesome-icon :icon="['fas', 'tags']" />
              <span>{{ dataset.category_count }} categorías</span>
            </div>
            <div class="stat-item">
              <font-awesome-icon :icon="['fas', 'calendar-alt']" />
              <span>{{ formatDate(dataset.created_at) }}</span>
            </div>
          </div>
          <button 
            v-if="isAuthenticated" 
            class="app-button clone-button"
            @click.stop="showCloneConfirmation(dataset, $event)"
          >
            <font-awesome-icon :icon="['fas', 'plus-circle']" />
            Clonar conjunto de imágenes
          </button>
        </div>
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
    <div v-if="totalPages > 1" class="pagination">
      <button 
        class="pagination-button"
        @click="goToFirstPage"
        :disabled="currentPage === 1"
        title="Primera página"
      >
        <font-awesome-icon :icon="['fas', 'angle-double-left']" />
      </button>
      <button 
        class="pagination-button"
        @click="goToPreviousPage"
        :disabled="currentPage === 1"
        title="Página anterior"
      >
        <font-awesome-icon :icon="['fas', 'angle-left']" />
      </button>
      <span class="pagination-info">{{ currentPage }} de {{ totalPages }}</span>
      <button 
        class="pagination-button"
        @click="goToNextPage"
        :disabled="currentPage === totalPages"
        title="Página siguiente"
      >
        <font-awesome-icon :icon="['fas', 'angle-right']" />
      </button>
      <button 
        class="pagination-button"
        @click="goToLastPage"
        :disabled="currentPage === totalPages"
        title="Última página"
      >
        <font-awesome-icon :icon="['fas', 'angle-double-right']" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

import { notifyError, notifySuccess, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import ConfirmationModal from '@/components/utils/ConfirmationModal.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const isAuthenticated = computed(() => authStore.isAuthenticated);

const datasets = ref([]);
const isLoading = ref(true);
const totalCount = ref(0);
const currentPage = ref(1);
const pageSize = ref(5);
const pageSizeOptions = [5, 10, 25, 50, 100];
const searchQuery = ref('');

const showCloneModal = ref(false);
const selectedDataset = ref(null);
const isCloning = ref(false);

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value));
const skip = computed(() => (currentPage.value - 1) * pageSize.value);

watch(searchQuery, (newValue, oldValue) => {
  // Si el campo tenía contenido y ahora está vacío, ejecutar clearSearch.
  if (oldValue && !newValue) {
    clearSearch();
  }
});

// Obtener conjuntos de imágenes compartidos.
const fetchSharedDatasets = async () => {
  isLoading.value = true;
  
  try {
    const headers = {};
    
    // Añadir token de autenticación solo si el usuario está logueado.
    if (authStore.isAuthenticated) {
      const token = authStore.token || localStorage.getItem('token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }
    
    // Construir parámetros para la consulta.
    const params = {
      skip: skip.value,
      limit: pageSize.value,
      search: searchQuery.value.trim(),
    };
    
    // Realizar la petición para obtener datasets públicos.
    const response = await axios.get('/datasets/public', { 
      params,
      headers
    });
    
    datasets.value = response.data.datasets || [];
    totalCount.value = response.data.count || 0;
    
  } catch (error) {
    console.error('Error fetching shared datasets: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

const truncateText = (text, maxLength) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

const formatDescription = (text) => {
  if (!text) return '';
  
  const approxLength = 200;
  
  return text.length > approxLength ? text.substring(0, approxLength) + '...' : text;
};

const formatDate = (dateString) => {
  try {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date);
  } catch (error) {
    return dateString || '-';
  }
};

const executeSearch = () => {
  currentPage.value = 1;
  fetchSharedDatasets();
};

const clearSearch = () => {
  searchQuery.value = '';
  currentPage.value = 1;
  fetchSharedDatasets();
};

// Funciones de paginación...
const resetPagination = () => {
  currentPage.value = 1;
  fetchSharedDatasets();
};

const goToFirstPage = () => {
  currentPage.value = 1;
  fetchSharedDatasets();
};

const goToPreviousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchSharedDatasets();
  }
};

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    fetchSharedDatasets();
  }
};

const goToLastPage = () => {
  currentPage.value = totalPages.value;
  fetchSharedDatasets();
};

// Cuando pulsamos en un dataset, redirigir a la vista de detalle pública.
const viewDataset = (dataset) => {
  router.push({ name: 'public-dataset-detail', params: { id: dataset.id } });
};

// Mostrar confirmación antes de clonar.
const showCloneConfirmation = (dataset, e) => {
  e.stopPropagation();
  
  // Si el usuario no está autenticado, redirigir a la página de login.
  // Esto no debería suceder, ya que si no está autenticado, no le sale el botón de añadir.
  if (!isAuthenticated.value) {
    notifyInfo("Inicia sesión para continuar", 
    "Debes iniciar sesión para añadir conjuntos a tu biblioteca personal.");
    router.push('/');
    return;
  }
  
  selectedDataset.value = dataset;
  showCloneModal.value = true;
};

const cancelCloneDataset = () => {
  showCloneModal.value = false;
  selectedDataset.value = null;
};

// Confirmar clonación (en el modal de confirmación).
const confirmCloneDataset = async () => {
  if (!selectedDataset.value) return;
  
  try {
    isCloning.value = true;

    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    // Llamar al endpoint para clonar el dataset.
    const response = await axios.post(`/datasets/${selectedDataset.value.id}/clone`);
    
    // Cerrar el modal.
    showCloneModal.value = false;
    
    // Notificar éxito.
    notifySuccess("Conjunto de imágenes clonado",
    "Se ha clonado el conjunto de imágenes con éxito.");
    
    // Redirigir al usuario a la vista de detalle del dataset clonado, ya en su biblioteca personal.
    router.push({ name: 'dataset-detail', params: { id: response.data.id } });
    
  } catch (error) {
    console.error('Error cloning dataset: ', error);
    handleApiError(error);
  } finally {
    isCloning.value = false;
    selectedDataset.value = null;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data, headers } = error.response;

    console.error('Error response: ', data);
    
    // Si el usuario es el propietario, redireccionar a su propio dataset en la vista personal.
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
    } else if(status == 400 || status == 500) {
      notifyError("Error del servidor al clonar el conjunto",
      `Detalle: ${data.detail || "No se pudo clonar el conjunto."}`);
    } else {
      notifyError("Error al cargar los conjuntos compartidos",
      "Ha ocurrido un problema al obtener los datos. Por favor, inténtalo de nuevo.");
    }
  } else if (error.request) {
    notifyError("Error de conexión",
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError(
    "Error inesperado",
    "Ha ocurrido un problema al cargar los conjuntos compartidos.");
  }
};

onMounted(() => {
  // Leer parámetros de la URL.
  const urlParams = route.query;
  
  if (urlParams.page && !isNaN(parseInt(urlParams.page))) {
    currentPage.value = parseInt(urlParams.page);
  }
  
  if (urlParams.size && pageSizeOptions.includes(parseInt(urlParams.size))) {
    pageSize.value = parseInt(urlParams.size);
  }
  
  if (urlParams.search) {
    searchQuery.value = urlParams.search;
  }
  
  // Cargar datos.
  fetchSharedDatasets();
});

watch([currentPage, pageSize], () => {
  // Construir objeto query para la URL.
  const query = {};
  
  if (currentPage.value > 1) {
    query.page = currentPage.value;
  }
  
  if (pageSize.value !== 5) {
    query.size = pageSize.value;
  }
  
  if (searchQuery.value.trim()) {
    query.search = searchQuery.value.trim();
  }
  
  // Resetear la paginación si cambia el tamaño de página.
  if (pageSize.value !== 5) {
    currentPage.value = 1;
  }
  
  // Actualizar la URL usando Vue Router.
  router.replace({ 
    path: route.path, 
    query 
  }).then(() => {
    // Cargar datos después de actualizar la URL.
    fetchSharedDatasets();
  }).catch(err => {
    console.error('Error updating URL: ', err);
    // Se intenta cargar datos si falla la actualización de URL.
    fetchSharedDatasets();
  });
}, { flush: 'post' });
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/search.css"></style>
<style scoped>
.explore-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  padding-top: 90px;
  padding-bottom: 40px;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  font-size: 2.2em;
  color: #333;
  margin-bottom: 10px;
}

.page-description {
  color: #666;
  font-size: 1.1em;
  max-width: 800px;
  margin: 0 auto;
}

/* Personalización de búsqueda */
.search-input:focus {
  outline: none;
  border-color: #e3dacc;
  box-shadow: 0 0 0 2px rgba(227, 218, 204, 0.3);
  background-color: white;
}

/* Selector de tamaño de página */
.page-size-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-selector label {
  color: #555;
}

.page-size-selector select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  font-size: 14px;
  border-color: #e3dacc;
  color: #665e53;
}

/* Estados de carga y sin resultados */
.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  color: #666;
}

.loading-spinner {
  color: #d6cdbf;
  margin-bottom: 20px;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
  color: #666;
}

.no-results-icon {
  font-size: 3em;
  color: #d6cdbf;
  margin-bottom: 15px;
}

/* Tarjetas de datasets */
.dataset-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

.dataset-card {
  display: flex;
  flex-direction: column;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  box-shadow: 0 3px 12px rgba(227, 218, 204, 0.35);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  overflow: hidden;
  border: 1px solid rgba(227, 218, 204, 0.5);
  height: auto;
}

.dataset-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(227, 218, 204, 0.7);
  border-color: #d6cdbf;
}

/* Cabecera de las tarjetas */
.card-header {
  padding: 18px 20px;
  border-bottom: 2px solid #e3dacc;
  background-color: rgba(227, 218, 204, 0.15);
}

.dataset-name {
  margin: 0;
  font-size: 1.4em;
  color: #665e53;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dataset-user {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.95em;
  color: #666;
}

/* Cuerpo de las tarjetas */
.card-body {
  padding: 20px;
  flex-grow: 1;
}

.description-container {
  margin: 0;
  color: #555;
  font-size: 1em;
  line-height: 1.6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.description-container::after {
  content: none;
}

/* Pie de las tarjetas */
.card-footer {
  padding: 18px 20px;
  border-top: 1px solid rgba(227, 218, 204, 0.5);
  background-color: rgba(227, 218, 204, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

/* Estadísticas del dataset */
.dataset-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.95em;
  color: #666;
  white-space: nowrap;
}

.stat-item .svg-inline--fa {
  color: #d6cdbf;
}

/* Botón de clonar */
.clone-button {
  padding: 8px 15px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-left: auto;
}

/* Controles de paginación */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 25px;
}

.pagination-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(227, 218, 204, 0.5);
  border-radius: 8px;
  background-color: white;
  color: #665e53;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.pagination-button:not(:disabled):hover {
  background-color: #e3dacc;
  color: #4a443c;
  border-color: #d6cdbf;
}

.pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 0.95em;
  color: #666;
  padding: 0 12px;
}

/* Búsqueda */
.search-icon {
  cursor: pointer;
}

/* Responsive */
@media (max-width: 768px) {
  .explore-view {
    padding: 15px;
    padding-top: 80px;
  }
  
  .page-header h1 {
    font-size: 1.8em;
  }
  
  .page-size-container {
    justify-content: center;
  }
  
  .card-footer {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .clone-button {
    margin-left: 0;
    width: 100%;
  }
}
</style>