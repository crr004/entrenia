<template>
  <div class="images-table-component">
    <div class="search-container">
      <div class="search-box">
        <font-awesome-icon :icon="['fas', 'search']" class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Buscar por nombre o etiqueta..."
          class="search-input" 
          @input="handleSearch"
        />
        <button 
          v-if="searchQuery" 
          @click="clearSearch" 
          class="clear-search-button"
        >
          <font-awesome-icon :icon="['fas', 'times']" />
        </button>
      </div>
    </div>
    <div class="datasets-content">
      <div class="table-wrapper">
        <div class="table-container images-table-container">
          <div v-if="isLoading || isSearchTransitioning" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando imágenes...</p>
          </div>
          <div v-else-if="images.length === 0" class="empty-state">
            <template v-if="searchQuery.trim()">
              <font-awesome-icon :icon="['fas', 'search']" size="2x" />
              <p>No se encontraron imágenes para "<span class="search-term">{{ searchQuery }}</span>"</p>
            </template>
            <template v-else>
              <font-awesome-icon :icon="['fas', 'images']" size="2x" />
              <p>Este conjunto aún no tiene imágenes.</p>
            </template>
          </div>
          <div v-else>
            <table class="data-table images-table">
              <thead>
                <tr>
                  <th class="thumbnail-column">Imagen</th>
                  <th @click="setSortField('name')" class="sortable-header">
                    <span class="header-text">Nombre</span>
                    <SortIcon :fieldName="'name'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('label')" class="sortable-header">
                    <span class="header-text">Etiqueta</span>
                    <SortIcon :fieldName="'label'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('created_at')" class="sortable-header">
                    <span class="header-text">Fecha de subida</span>
                    <SortIcon :fieldName="'created_at'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="image in images" :key="image.id" class="image-row">
                  <td class="thumbnail-column">
                    <div class="thumbnail-container">
                      <img :src="`data:image/png;base64,${image.thumbnail}`" :alt="image.name" class="image-thumbnail" />
                    </div>
                  </td>
                  <td>
                    <span class="truncate" :title="image.name">
                      {{ truncateText(image.name, 40) }}
                    </span>
                  </td>
                  <td>
                    <span v-if="image.label" class="truncate" :title="image.label">
                      {{ truncateText(image.label, 30) }}
                    </span>
                    <span v-else class="no-label">Sin etiqueta</span>
                  </td>
                  <td>{{ formatDate(image.created_at) }}</td>
                </tr>
              </tbody>
            </table>
            <div class="pagination-controls">
              <div class="pagination-actions">
                <button 
                  class="pagination-button" 
                  @click="changePage(currentPage - 1)"
                  :disabled="currentPage === 1"
                >
                  <font-awesome-icon :icon="['fas', 'chevron-left']" class="pagination-icon" />
                </button>
                <div class="pagination-info">
                  Página {{ currentPage }} de {{ totalPages }}
                  <span class="total-info">({{ totalImages }} imágenes)</span>
                </div>
                <button 
                  class="pagination-button" 
                  @click="changePage(currentPage + 1)"
                  :disabled="currentPage >= totalPages"
                >
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="pagination-icon" />
                </button>
              </div>
              <div class="page-size-selector">
                <label for="page-size">Mostrar:</label>
                <select 
                  id="page-size" 
                  v-model="pageSize" 
                  class="page-size-select"
                  @change="handlePageSizeChange"
                >
                  <option v-for="size in pageSizeOptions" :key="size" :value="size">
                    {{ size }} imágenes
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import axios from 'axios';
import { notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import { userPreferencesStore } from '@/stores/userPreferencesStore.js';
import SortIcon from '@/components/utils/SortIcon.vue';

const props = defineProps({
  datasetId: {
    type: String,
    required: true
  }
});

const images = ref([]);
const isLoading = ref(true);
const scrollPosition = ref(0);

const currentPage = ref(1);
const pageSize = ref(5);
const totalImages = ref(0);
const sortBy = ref('created_at');
const sortOrder = ref('desc');
const pageSizeOptions = [5, 10, 25, 50, 100];
const isSearchTransitioning = ref(false);

const searchQuery = ref('');
const searchTimeout = ref(null);

const preferencesStore = userPreferencesStore();
const authStore = useAuthStore();

const totalPages = computed(() => Math.ceil(totalImages.value / pageSize.value) || 1);

const saveScrollPosition = () => {
  scrollPosition.value = window.scrollY;
};

const restoreScrollPosition = () => {
  nextTick(() => {
    setTimeout(() => {
      window.scrollTo({
        top: scrollPosition.value,
        behavior: 'instant'
      });
    }, 10);
  });
};

const fetchImages = async (maintainScrollPosition = false) => {
  if (maintainScrollPosition) {
    saveScrollPosition();
  }
  
  isLoading.value = true;
  
  try {
    // Configurar headers según si el usuario está autenticado o no.
    const headers = {};
    if (authStore.isAuthenticated) {
      const token = authStore.token || localStorage.getItem('token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const skip = (currentPage.value - 1) * pageSize.value;
    let url = `/images/public-dataset/${props.datasetId}?skip=${skip}&limit=${pageSize.value}&sort_by=${sortBy.value}&sort_order=${sortOrder.value}`;
    
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`;
    }
    
    const response = await axios.get(url, { headers });
    
    if (response.data && Array.isArray(response.data.images)) {
      images.value = response.data.images;
      totalImages.value = response.data.count || images.value.length;
    } else {
      images.value = [];
      totalImages.value = 0;
      notifyInfo("Sin datos",
      "No se encontraron imágenes para mostrar.");
    }
    
    if (maintainScrollPosition) {
      restoreScrollPosition();
    }
    
    return response;
  } catch (error) {
    console.error('Error while fetching images: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
    isSearchTransitioning.value = false;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    console.error("Error response: ", data);
    
    if (status === 404) {
      notifyError("Conjunto no encontrado", 
      "El conjunto solicitado no existe o no está disponible.");
    } else if (status === 400) {
      notifyError("Error en la solicitud",
      "La solicitud de búsqueda o filtrado contiene errores.");
    } else {
      notifyError("Error al cargar imágenes", 
      "No se pudieron cargar las imágenes de este conjunto.");
    }
  } else if (error.request) {
    notifyError("Error de conexión",
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado",
    "Ha ocurrido un problema al cargar los datos.");
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(date);
};

const truncateText = (text, maxLength) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

const changePage = async (page) => {
  saveScrollPosition();
  isSearchTransitioning.value = true;
  
  if (page < 1 || page > totalPages.value) {
    isSearchTransitioning.value = false;
    return;
  }
  
  currentPage.value = page;
  
  try {
    await fetchImages(true);
  } catch (error) {
    console.error('Error while changing pages: ', error);
  } finally {
    isSearchTransitioning.value = false;
  }
};

const handlePageSizeChange = async () => {
  try {
    isSearchTransitioning.value = true;
    saveScrollPosition();
    
    // Guardar preferencia de tamaño de página solo si el usuario está autenticado.
    if (authStore.isAuthenticated) {
      preferencesStore.setImagePageSize(pageSize.value);
    }

    const currentSize = pageSize.value;
    const firstItemIndex = (currentPage.value - 1) * currentSize;
    
    const newPage = Math.floor(firstItemIndex / currentSize) + 1;
    currentPage.value = newPage;
    
    const newTotalPages = Math.ceil(totalImages.value / currentSize) || 1;
    if (currentPage.value > newTotalPages) {
      currentPage.value = newTotalPages;
    }
    
    await fetchImages(true);
  } catch (error) {
    console.error("Error while changing page size: ", error);
  } finally {
    setTimeout(() => {
      isSearchTransitioning.value = false;
    }, 0);
  }
};

const setSortField = async (field) => {
  saveScrollPosition();
  isSearchTransitioning.value = true;
  
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = field;
    sortOrder.value = (field === 'name') ? 'asc' : 'desc';
  }
  
  await fetchImages(true);
};

const handleSearch = () => {
  saveScrollPosition();
  isSearchTransitioning.value = true;
  
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  searchTimeout.value = setTimeout(async () => {
    currentPage.value = 1;
    await fetchImages(true);
  }, 300);
};

const clearSearch = async () => {
  saveScrollPosition();
  isSearchTransitioning.value = true;
  searchQuery.value = '';
  await fetchImages(true);
};

onMounted(async () => {
  try {
    isSearchTransitioning.value = true;
    isLoading.value = true;
    
    if (authStore.isAuthenticated) {
      const savedPageSize = preferencesStore.imagePageSize;
      if (savedPageSize && pageSizeOptions.includes(parseInt(savedPageSize))) {
        pageSize.value = parseInt(savedPageSize);
      }
    }
    
    await fetchImages(false);
  } catch (error) {
    console.error("Error while initializing: ", error);
  } finally {
    isLoading.value = false;
    isSearchTransitioning.value = false;
  }
});

watch(() => props.datasetId, async (newId, oldId) => {
  if (newId !== oldId) {
    currentPage.value = 1;
    await fetchImages(false);
  }
});
</script>

<style scoped src="@/assets/styles/search.css"></style>
<style scoped src="@/assets/styles/table.css"></style>
<style scoped>
.images-table-component {
  margin-top: 25px;
}

.datasets-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: relative;
  margin-top: 15px;
  overflow-x: auto;
}

.images-table-container {
  width: 100%;
}

.thumbnail-column {
  width: 100px;
  text-align: center;
}

.thumbnail-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60px;
  width: 100%;
}

.image-thumbnail {
  max-height: 50px;
  max-width: 80px;
  object-fit: contain;
  border-radius: 4px;
  border: 1px solid #eee;
}

.no-label {
  color: #999;
  font-style: italic;
}

.sortable-header {
  cursor: pointer;
  position: relative;
  user-select: none;
  padding-right: 28px;
}

.data-table thead tr th.sortable-header {
  padding-right: 28px;
}

.header-text {
  display: inline-block;
  vertical-align: middle;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sortable-header:hover {
  background-color: #f8f9fa;
}

.images-table th:nth-child(2), 
.images-table td:nth-child(2) {
  max-width: 200px;
}

.images-table th:nth-child(3), 
.images-table td:nth-child(3) {
  max-width: 150px;
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.empty-hint {
  font-size: 0.85rem;
  color: #999;
  margin-top: 5px;
}

@media (max-width: 768px) {
  .thumbnail-column {
    width: 80px;
  }
  
  .thumbnail-container {
    height: 50px;
  }
  
  .image-thumbnail {
    max-height: 40px;
    max-width: 60px;
  }
  
  .images-table th:nth-child(2),
  .images-table td:nth-child(2) {
    max-width: 120px;
  }
  
  .images-table th:nth-child(3),
  .images-table td:nth-child(3) {
    max-width: 80px;
  }
}
</style>