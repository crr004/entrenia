<template>
  <div class="models-view">
    <div class="models-header">
      <h1>Mis modelos de clasificación de imágenes</h1>
      <button class="app-button add-model-button" @click="showAddModel">
        <font-awesome-icon :icon="['fas', 'plus']" class="button-icon" />
        Entrenar un modelo
      </button>
    </div>
    <div class="search-container">
      <div class="search-box">
        <font-awesome-icon :icon="['fas', 'search']" class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery" 
          :placeholder="isAdmin ? 'Buscar por usuario, nombre o descripción...' : 'Buscar por nombre o descripción...'"
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
    <div class="models-content">
      <div class="table-wrapper">
        <div class="table-container models-table-container">
          <div v-if="isLoading || isSearchTransitioning" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando modelos...</p>
          </div>
          <div v-else-if="models.length === 0" class="empty-state">
            <template v-if="searchQuery.trim()">
              <font-awesome-icon :icon="['fas', 'search']" size="2x" />
              <p>No se encontraron modelos para "<span class="search-term">{{ searchQuery }}</span>"</p>
            </template>
            <template v-else>
              <font-awesome-icon :icon="['fas', 'robot']" size="2x" />
              <p>Aún no tienes ningún modelo entrenado.</p>
            </template>
          </div>
          <div v-else>
            <table class="data-table models-table">
              <thead>
                <tr>
                  <th v-if="isAdmin" @click="setSortField('username')" class="sortable-header">
                    <span class="header-text">Usuario</span>
                    <SortIcon :fieldName="'username'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('name')" class="sortable-header">
                    <span class="header-text">Nombre</span>
                    <SortIcon :fieldName="'name'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th>Descripción</th>
                  <th @click="setSortField('status')" class="center-column sortable-header">
                    <span class="header-text">Estado</span>
                    <SortIcon :fieldName="'status'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('created_at')" class="sortable-header">
                    <span class="header-text">Fecha de creación</span>
                    <SortIcon :fieldName="'created_at'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th class="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="model in models" :key="model.id" 
                    @click="viewModel(model)" 
                    class="model-row">
                  <td v-if="isAdmin">
                    <span class="truncate" :title="model.username || '-'">
                      {{ truncateText(model.username, 20) || '-' }}
                    </span>
                  </td>
                  <td>
                    <span class="truncate" :title="model.name">
                      {{ truncateText(model.name, 40) }}
                    </span>
                  </td>
                  <td>
                    <span class="truncate" :title="model.description || '-'">
                      {{ model.description ? truncateText(model.description, isAdmin ? 20 : 30) : '-' }}
                    </span>
                  </td>
                  <td class="center-column">
                    <span :class="getStatusClass(model.status)">
                      {{ getStatusLabel(model.status) }}
                    </span>
                  </td>
                  <td>{{ formatDate(model.created_at) }}</td>
                  <td class="actions-column">
                    <div class="actions-menu">
                      <button 
                        class="action-button" 
                        @click="(event) => toggleActionsMenu(model.id, event)"
                        :data-item-id="model.id"
                        :data-active="activeActionsMenu === model.id"
                      >
                        <font-awesome-icon :icon="['fas', 'ellipsis-vertical']" />
                      </button>
                      <ActionMenu
                        v-if="activeActionsMenu === model.id" 
                        :item="model" 
                        :itemId="model.id"
                        :position="getMenuPosition(model.id)"
                        :actions="getModelMenuActions(model)"
                        @view="viewModel"
                        @edit="editModel"
                        @delete="confirmDeleteModel"
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
                  <span class="total-info">({{ totalModels }} modelos)</span>
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
                    {{ size }} modelos
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
      :title="`Eliminar modelo`"
      :message="deleteModalMessage"
      confirmText="Eliminar"
      cancelText="Cancelar"
      buttonType="danger"
      @confirm="deleteModel"
      @cancel="cancelDelete"
    />
    <AddModelModal
      v-if="isAddModelModalOpen"
      @close="closeAddModelModal"
      @model-added="onModelAdded"
    />
    <EditModelModal
      :isOpen="isEditModelModalOpen"
      :model="modelToEdit"
      @close="closeEditModelModal"
      @model-updated="onModelUpdated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import { userPreferencesStore } from '@/stores/userPreferencesStore.js';
import ActionMenu from '@/components/utils/ActionMenu.vue';
import ConfirmationModal from '@/components/utils/ConfirmationModal.vue';
import SortIcon from '@/components/utils/SortIcon.vue';
import EditModelModal from '@/components/models/EditModelModal.vue';

const router = useRouter();
const route = useRoute();
const models = ref([]);
const isLoading = ref(true);
const activeActionsMenu = ref(null);
const isDeleteModalOpen = ref(false);
const modelToDelete = ref(null);
const deleteModalMessage = ref('');
const isAddModelModalOpen = ref(false);
const isEditModelModalOpen = ref(false);
const modelToEdit = ref(null);

const isSearchTransitioning = ref(false);

const preferencesStore = userPreferencesStore();
const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.is_admin || false);

const currentPage = ref(1);
const pageSize = ref(5);
const totalModels = ref(0);
const totalPages = computed(() => Math.ceil(totalModels.value / pageSize.value) || 1);
const sortBy = ref('created_at');
const sortOrder = ref('desc');

const pageSizeOptions = [5, 10, 25, 50, 100];

const searchQuery = ref('');
const searchTimeout = ref(null);

const handlePageSizeChange = async () => {
  try {
    // Activar el estado de transición para evitar parpadeos.
    isSearchTransitioning.value = true;
    
    // Guardar el nuevo tamaño de página en las preferencias del usuario.
    preferencesStore.setModelPageSize(pageSize.value);
    
    // Calcular la primera entrada de la página actual con el tamaño antiguo.
    const currentSize = pageSize.value; // Guardar el tamaño actual.
    const firstItemIndex = (currentPage.value - 1) * currentSize;
    
    // Calcular qué página mostrará esa primera entrada con el nuevo tamaño.
    const newPage = Math.floor(firstItemIndex / currentSize) + 1;
    currentPage.value = newPage;
    
    // Asegurar que no exceda el número total de páginas.
    const newTotalPages = Math.ceil(totalModels.value / currentSize) || 1;
    if (currentPage.value > newTotalPages) {
      currentPage.value = newTotalPages;
    }
    
    // Recargar datos con el nuevo tamaño de página.
    await fetchModels();
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
  isSearchTransitioning.value = true;
  
  if (sortBy.value === field) {
    // Si ya se está ordenando por este campo, invertir la dirección.
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    // Si no es el mismo campo, establecer el nuevo campo y la dirección por defecto.
    sortBy.value = field;
    // Por defecto ordenar descendentemente (excepto para nombres).
    sortOrder.value = (field === 'name' || field === 'username') ? 'asc' : 'desc';
  }
  
  // Recargar datos con la nueva ordenación.
  await fetchModels();
};

// Manejar la búsqueda con debounce.
const handleSearch = () => {
  isSearchTransitioning.value = true;
  
  // Limpiar el timeout anterior si existe.
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  // Esperar a que el usuario termine de escribir.
  searchTimeout.value = setTimeout(async () => {
    // Resetear a la página 1 al buscar.
    currentPage.value = 1;
    
    // Recargar datos con la nueva búsqueda.
    await fetchModels();
  }, 300);
};

const clearSearch = async () => {
  // Activar estado de transición para evitar parpadeos.
  isSearchTransitioning.value = true;
  
  searchQuery.value = '';

  await fetchModels();
};

const fetchModels = async () => {
  isLoading.value = true;
  closeActionsMenu();
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    const skip = (currentPage.value - 1) * pageSize.value;
    // Construir URL con todos los parámetros.
    let url = `/classifiers/?skip=${skip}&limit=${pageSize.value}&sort_by=${sortBy.value}&sort_order=${sortOrder.value}`;
    
    // Añadir parámetro de búsqueda si se está buscando.
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`;
    }
    
    const response = await axios.get(url);
    
    // Procesar la respuesta.
    if (response.data && Array.isArray(response.data.classifiers)) {
      models.value = response.data.classifiers;
      totalModels.value = response.data.count || models.value.length;
    } else {
      models.value = [];
      totalModels.value = 0;
      notifyInfo("Sin datos",
      "No se encontraron modelos para mostrar.");
    }
    
    return response;
  } catch (error) {
    console.error('Error while fetching models: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
    isSearchTransitioning.value = false;
  }
};

const changePage = async (page) => {
  isSearchTransitioning.value = true;
  
  if (page < 1 || page > totalPages.value) {
    isSearchTransitioning.value = false;
    return;
  }
  
  currentPage.value = page;
  
  try {
    await fetchModels();
  } catch (error) {
    console.error('Error while changing pages: ', error);
  } finally {
    isSearchTransitioning.value = false;
  }
};

const toggleActionsMenu = (modelId, event) => {
  if (event) {
    event.stopPropagation();
  }
  
  // Cerrar cualquier menú activo.
  if (activeActionsMenu.value !== null) {
    const prevButton = document.querySelector(`.action-button[data-item-id="${activeActionsMenu.value}"]`);
    if (prevButton) {
      prevButton.setAttribute('data-active', 'false');
    }
  }

  // Si se hace clic en el mismo botón, cerrar el menú.
  if (activeActionsMenu.value === modelId) {
    activeActionsMenu.value = null;
  } else {
    // Activar el menú.
    activeActionsMenu.value = modelId;
    const newButton = document.querySelector(`.action-button[data-item-id="${modelId}"]`);
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

const getMenuPosition = (modelId) => {
  return { 
    top: true,
    right: false
  };
};

const showAddModel = () => {
  isAddModelModalOpen.value = true;
  closeActionsMenu();
};

const closeAddModelModal = () => {
  isAddModelModalOpen.value = false;
};

const onModelAdded = async (newModel) => {
  await fetchModels();
};

const viewModel = (model) => {
  closeActionsMenu();
  router.push(`/model/${model.id}`);
};

const editModel = (model) => {
  closeActionsMenu();
  modelToEdit.value = model;
  isEditModelModalOpen.value = true;
};

const closeEditModelModal = () => {
  isEditModelModalOpen.value = false;
  modelToEdit.value = null;
};

const onModelUpdated = async (updatedModel) => {
  // Se recarga en estos casos:
  // 1. Si hay una búsqueda activa.
  // 2. Si se modificó un campo que afecta a la ordenación actual.
  if (
    searchQuery.value.trim() || 
    (updatedModel.hasOwnProperty(sortBy.value) && 
     sortBy.value !== 'status')
  ) {
    const paginaActual = currentPage.value;
    
    // Recargar la tabla en ese caso.
    await fetchModels();
    
    // Si después de recargar no hay modelos en la página actual pero hay modelos en total,
    // retroceder a la página anterior.
    if (models.value.length === 0 && totalModels.value > 0 && paginaActual > 1) {
      currentPage.value = paginaActual - 1;
      await fetchModels();
    }
  } else {
    // Sin búsqueda activa y sin cambios en el campo de ordenación,
    // se puede actualizar sólo el modelo en la lista local.
    const index = models.value.findIndex(m => m.id === updatedModel.id);
    if (index !== -1) {
      models.value[index] = updatedModel;
    } else {
      // Si no se encuentra el modelo, recargamos todo.
      await fetchModels();
    }
  }
};

const confirmDeleteModel = (model) => {
  closeActionsMenu();
  modelToDelete.value = model;
  deleteModalMessage.value = `Estás a punto de eliminar el modelo. Esta acción no se puede deshacer.`;
  isDeleteModalOpen.value = true;
};

const cancelDelete = () => {
  isDeleteModalOpen.value = false;
  modelToDelete.value = null;
  activeActionsMenu.value = null;
  
  setTimeout(() => {
    const activeButtons = document.querySelectorAll('.action-button[data-active="true"]');
    activeButtons.forEach(button => {
      button.setAttribute('data-active', 'false');
    });
  }, 100);
};

const deleteModel = async () => {
  if (!modelToDelete.value) return;
  
  try {
    await axios.delete(`/classifiers/${modelToDelete.value.id}`);
    
    // Si se está en una página con un solo elemento (el cuál se está eliminando)
    // y no es la primera página, se debe volver a la página anterior.
    if (models.value.length === 1 && currentPage.value > 1) {
      currentPage.value--;
    }
    
    // Actualizar la lista después de eliminar.
    await fetchModels();
    
    // Si después de actualizar no hay modelos en la página actual pero hay modelos en total,
    // puede que se necesite ajustar la página actual de nuevo.
    if (models.value.length === 0 && totalModels.value > 0) {
      // Calcular el número máximo de páginas después de la eliminación.
      const maxPage = Math.ceil(totalModels.value / pageSize.value);
      if (currentPage.value > maxPage) {
        currentPage.value = maxPage;
        await fetchModels();
      }
    }
    
    notifySuccess("Modelo eliminado", 
    `Se ha eliminado el modelo ${modelToDelete.value.name} con éxito.`);
  } catch (error) {
    console.error('Error while deleting model: ', error);
    handleApiError(error);
  } finally {
    isDeleteModalOpen.value = false;
    modelToDelete.value = null;
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
          "No tienes permisos suficientes para realizar esta acción.");
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
    "Ha ocurrido un problema al cargar los datos de los modelos.");
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  
  // Convertir UTC a fecha local.
  const date = new Date(dateString);
  
  // Formatear fecha: DD/MM/YYYY HH:MM.
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
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

const truncateText = (text, maxLength) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

const handleScroll = () => {
  if (activeActionsMenu.value !== null) {
    closeActionsMenu();
  }
};

const getModelMenuActions = (model) => {
  const baseActions = [
    { label: 'Abrir', event: 'view', icon: ['fas', 'folder-open'], class: 'view' },
    { label: 'Editar', event: 'edit', icon: ['fas', 'edit'], class: 'edit' },
    { label: 'Eliminar', event: 'delete', icon: ['fas', 'trash-alt'], class: 'delete' }
  ];
  
  return baseActions;
};

onMounted(async () => {
  try {
    isSearchTransitioning.value = true;
    isLoading.value = true;
    
    // Restaurar preferencia de tamaño de página si existe.
    const savedPageSize = preferencesStore.modelPageSize;
    if (savedPageSize && pageSizeOptions.includes(parseInt(savedPageSize))) {
      pageSize.value = parseInt(savedPageSize);
    }
    
    window.addEventListener('scroll', handleScroll, true);
    
    // Obtener parámetros de la URL si existen.
    const urlParams = new URLSearchParams(window.location.search);
    const urlPage = urlParams.get('page');
    const urlSort = urlParams.get('sort');
    const urlOrder = urlParams.get('order');
    const urlSearch = urlParams.get('search');
    
    // Aplicar parámetros de URL si existen.
    if (urlPage && !isNaN(parseInt(urlPage))) {
      currentPage.value = parseInt(urlPage);
    }
    
    if (urlSort && ['name', 'created_at', 'status', 'username'].includes(urlSort)) {
      sortBy.value = urlSort;
    }
    
    if (urlOrder && ['asc', 'desc'].includes(urlOrder)) {
      sortOrder.value = urlOrder;
    }
    
    if (urlSearch) {
      searchQuery.value = urlSearch;
    }
    
    await fetchModels();
  } catch (error) {
    console.error("Error while initializing: ", error);
  } finally {
    isLoading.value = false;
    isSearchTransitioning.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll, true);
});

// Actualizar la URL cuando cambian los parámetros de búsqueda/ordenación.
watch([currentPage, sortBy, sortOrder, searchQuery], () => {
  const query = {
    page: currentPage.value,
    sort: sortBy.value,
    order: sortOrder.value
  };
  
  if (searchQuery.value.trim()) {
    query.search = searchQuery.value.trim();
  }
  
  // Actualizar la URL usando Vue Router sin recargar la página.
  router.replace({ 
    path: route.path, 
    query 
  });
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/search.css"></style>
<style scoped src="@/assets/styles/table.css"></style>
<style scoped>
.models-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 90px; 
  padding-bottom: 40px;
}

.models-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.models-header h1 {
  color: #333;
  margin: 0;
  font-size: 1.8rem;
}

.add-model-button {
  width: auto;
  margin-top: 0;
  padding: 10px 20px;
}

.button-icon {
  margin-right: 8px;
}

.models-content {
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

.model-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.model-row:hover {
  background-color: #f8f9fa;
}

/* Anchura de columnas y truncamiento de texto */
/* Columna de usuario */
.models-table th:nth-child(1), 
.models-table td:nth-child(1) {
  max-width: 140px;
}

/* Columna de nombre */
.models-table th:nth-child(2), 
.models-table td:nth-child(2) {
  max-width: 180px;
}

/* Columna de descripción */
.models-table th:nth-child(3), 
.models-table td:nth-child(3) {
  max-width: 150px;
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

/* Responsive */
@media (max-width: 768px) {
  .models-view {
    padding: 10px;
  }
  
  .models-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .add-model-button {
    width: 100%;
  }
  
  .models-table th,
  .models-table td {
    padding: 8px 6px;
  }
  
  .models-table th:nth-child(2),
  .models-table td:nth-child(2) {
    max-width: 110px;
  }
  
  .models-table th:nth-child(3),
  .models-table td:nth-child(3) {
    max-width: 80px;
  }
}
</style>