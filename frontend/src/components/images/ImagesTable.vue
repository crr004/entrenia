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
                  <th class="actions-column">Acciones</th>
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
                  <td class="actions-column">
                    <div class="actions-menu">
                      <button 
                        class="action-button" 
                        @click="(event) => toggleActionsMenu(image.id, event)"
                        :data-item-id="image.id"
                        :data-active="activeActionsMenu === image.id"
                      >
                        <font-awesome-icon :icon="['fas', 'ellipsis-vertical']" />
                      </button>
                      <ActionMenu
                        v-if="activeActionsMenu === image.id" 
                        :item="image" 
                        :itemId="image.id"
                        :position="getMenuPosition(image.id)"
                        :actions="imageMenuActions"
                        @edit="editImage"
                        @delete="confirmDeleteImage"
                        @close="closeActionsMenu"
                      />
                    </div>
                  </td>
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
    <ConfirmationModal
      :isOpen="isDeleteModalOpen"
      :title="`Eliminar imagen`"
      :message="deleteModalMessage"
      confirmText="Eliminar"
      cancelText="Cancelar"
      @confirm="deleteImage"
      @cancel="cancelDelete"
    />
    <EditImageModal
      v-if="isEditModalOpen"
      :isOpen="isEditModalOpen"
      :image="imageToEdit"
      @close="closeEditModal"
      @image-updated="onImageUpdated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import { userPreferencesStore } from '@/stores/userPreferencesStore.js';
import ActionMenu from '@/components/utils/ActionMenu.vue';
import ConfirmationModal from '@/components/utils/ConfirmationModal.vue';
import SortIcon from '@/components/utils/SortIcon.vue';
import EditImageModal from '@/components/images/EditImageModal.vue';

const props = defineProps({
  datasetId: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['refresh-dataset-stats']);

const images = ref([]);
const isLoading = ref(true);
const activeActionsMenu = ref(null);
const isDeleteModalOpen = ref(false);
const imageToDelete = ref(null);
const deleteModalMessage = ref('');
const isEditModalOpen = ref(false);
const imageToEdit = ref(null);
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

const router = useRouter();

const imageMenuActions = [
  { label: 'Editar', event: 'edit', icon: ['fas', 'edit'], class: 'edit' },
  { label: 'Eliminar', event: 'delete', icon: ['fas', 'trash-alt'], class: 'delete' }
];

const totalPages = computed(() => Math.ceil(totalImages.value / pageSize.value) || 1);

const saveScrollPosition = () => {
  scrollPosition.value = window.scrollY;
  //console.log('Saved scroll position: ', scrollPosition.value);
};

const restoreScrollPosition = () => {
  nextTick(() => {
    setTimeout(() => {
      window.scrollTo({
        top: scrollPosition.value,
        behavior: 'instant'
      });
      //console.log('Restored scroll position: ', scrollPosition.value);
    }, 10); // Pequeño retraso para asegurar que el DOM esté actualizado.
  });
};

const fetchImages = async (maintainScrollPosition = false) => {
  if (maintainScrollPosition) {
    saveScrollPosition();
  }
  
  isLoading.value = true;
  closeActionsMenu();
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    const skip = (currentPage.value - 1) * pageSize.value;
    let url = `/images/dataset/${props.datasetId}?skip=${skip}&limit=${pageSize.value}&sort_by=${sortBy.value}&sort_order=${sortOrder.value}`;
    
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`;
    }
    
    const response = await axios.get(url);
    
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
    
    switch (status) {
      case 400:
        if (data.detail && (data.detail.includes("sort_order") || data.detail.includes("sort_by"))) {
          notifyError("Error de ordenación",
          "Los parámetros de ordenación no son válidos.");
        } else {
          notifyError("Error en la solicitud",
          "La solicitud contiene errores.");
        }
        break; 
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
          notifyError("Acceso denegado", 
          "No tienes permisos para realizar esta acción.");
        } else {
          notifyError("Acceso denegado", 
            "No tienes permiso para realizar esta acción.");
        }
        break;
      case 404:
        notifyError("Recurso no encontrado",
        "El recurso solicitado no existe o ha sido eliminado.");
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
    "Ha ocurrido un problema al cargar los datos.");
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
    // Activar el estado de transición para evitar parpadeos.
    isSearchTransitioning.value = true;
    saveScrollPosition();
    
    // Guardar el nuevo tamaño de página en el store de preferencias del usuario.
    preferencesStore.setImagePageSize(pageSize.value);

    // Calcular la primera entrada de la página actual con el tamaño antiguo.
    const currentSize = pageSize.value;
    const firstItemIndex = (currentPage.value - 1) * currentSize;
    
    // Calcular qué página mostrará esa primera entrada con el nuevo tamaño.
    const newPage = Math.floor(firstItemIndex / currentSize) + 1;
    currentPage.value = newPage;
    
    // Asegurar que no exceda el número total de páginas.
    const newTotalPages = Math.ceil(totalImages.value / currentSize) || 1;
    if (currentPage.value > newTotalPages) {
      currentPage.value = newTotalPages;
    }
    
    // Recargar datos con el nuevo tamaño de página.
    await fetchImages(true);
  } catch (error) {
    console.error("Error while changing page size: ", error);
  } finally {
    // En el siguiente tick, se desactiva el estado de transición.
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

// Búsqueda con debounce.
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

const toggleActionsMenu = (imageId, event) => {
  if (event) {
    event.stopPropagation();
  }
  
  if (activeActionsMenu.value !== null) {
    const prevButton = document.querySelector(`.action-button[data-item-id="${activeActionsMenu.value}"]`);
    if (prevButton) {
      prevButton.setAttribute('data-active', 'false');
    }
  }

  if (activeActionsMenu.value === imageId) {
    activeActionsMenu.value = null;
  } else {
    activeActionsMenu.value = imageId;
    const newButton = document.querySelector(`.action-button[data-item-id="${imageId}"]`);
    if (newButton) {
      newButton.setAttribute('data-active', 'true');
    }
  }
};

const closeActionsMenu = () => {
  activeActionsMenu.value = null;
  const activeButtons = document.querySelectorAll('.action-button[data-active="true"]');
  activeButtons.forEach(button => {
    button.setAttribute('data-active', 'false');
  });
};

const getMenuPosition = (imageId) => {
  return { 
    top: true,
    right: true 
  };
};

const editImage = (image) => {
  closeActionsMenu();
  imageToEdit.value = image;
  isEditModalOpen.value = true;
};

const closeEditModal = () => {
  isEditModalOpen.value = false;
  imageToEdit.value = null;
};

const onImageUpdated = async (updatedImage) => {
  saveScrollPosition();
  
  try {
    // Si hay búsqueda o la ordenación está basada en un campo actualizado.
    if (searchQuery.value.trim() || (sortBy.value !== 'created_at' && updatedImage.hasOwnProperty(sortBy.value))) {
      const paginaActual = currentPage.value;
      
      // Recargar datos con la nueva búsqueda.
      await fetchImages(true);
      
      // Si después de recargar no hay imágenes en la página actual pero hay imágenes en total,
      // retroceder a la página anterior.
      if (images.value.length === 0 && totalImages.value > 0 && paginaActual > 1) {
        currentPage.value = paginaActual - 1;
        await fetchImages(true);
      }
    } else {
      // Sin búsqueda activa y sin cambios en el campo de ordenación,
      // se puede actualizar sólo la imagen en la lista local.
      const index = images.value.findIndex(img => img.id === updatedImage.id);
      if (index !== -1) {
        images.value[index] = updatedImage;
        restoreScrollPosition();
      } else {
        // Si no se encuentra la imagen, recargamos todo.
        await fetchImages(true);
      }
    }
    
    // Informar al componente padre que se han actualizado los datos.
    emit('refresh-dataset-stats');
  } catch (error) {
    console.error('Error while processing the image update: ', error);
  }
};

const confirmDeleteImage = (image) => {
  closeActionsMenu();
  imageToDelete.value = image;
  deleteModalMessage.value = `Estás a punto de eliminar la imagen. Esta acción no se puede deshacer.`;
  isDeleteModalOpen.value = true;
};

const cancelDelete = () => {
  isDeleteModalOpen.value = false;
  imageToDelete.value = null;
  activeActionsMenu.value = null;
};

const deleteImage = async () => {
  if (!imageToDelete.value) return;
  
  saveScrollPosition();
  
  try {
    await axios.delete(`/images/${imageToDelete.value.id}`);
    
    if (images.value.length === 1 && currentPage.value > 1) {
      currentPage.value--;
    }
    
    await fetchImages(true);
    
    if (images.value.length === 0 && totalImages.value > 0) {
      const maxPage = Math.ceil(totalImages.value / pageSize.value);
      if (currentPage.value > maxPage) {
        currentPage.value = maxPage;
        await fetchImages(true);
      }
    }
    
    notifySuccess("Imagen eliminada",
    `Se ha eliminado la imagen ${imageToDelete.value.name} con éxito.`);
    
    // Informar al componente padre que se han actualizado los datos.
    emit('refresh-dataset-stats');
  } catch (error) {
    console.error('Error al eliminar la imagen:', error);
    handleApiError(error);
  } finally {
    isDeleteModalOpen.value = false;
    imageToDelete.value = null;
  }
};

const handleScroll = () => {
  if (activeActionsMenu.value !== null) {
    closeActionsMenu();
  }
};

onMounted(async () => {
  try {
    isSearchTransitioning.value = true;
    isLoading.value = true;
    

    const savedPageSize = preferencesStore.imagePageSize;
    if (savedPageSize && pageSizeOptions.includes(parseInt(savedPageSize))) {
      pageSize.value = parseInt(savedPageSize);
    }
    
    window.addEventListener('scroll', handleScroll, true);
    
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

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll, true);
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

/* Encabezados de tabla y ordenación */
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

/* Anchura de columnas y truncamiento de texto */
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

/* Responsive */
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