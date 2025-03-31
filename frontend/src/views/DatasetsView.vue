<template>
  <div class="datasets-view">
    <div class="datasets-header">
      <h1>Mis conjuntos de imágenes</h1>
      <button class="app-button add-dataset-button" @click="showAddDatasetModal">
        <font-awesome-icon :icon="['fas', 'plus']" class="button-icon" />
        Crear conjunto de imágenes
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
    <div class="datasets-content">
      <div class="table-wrapper">
        <div class="table-container datasets-table-container">
          <div v-if="isLoading || isSearchTransitioning" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando conjuntos de imágenes...</p>
          </div>
          <div v-else-if="datasets.length === 0" class="empty-state">
            <template v-if="searchQuery.trim()">
              <font-awesome-icon :icon="['fas', 'search']" size="2x" />
              <p>No se encontraron conjuntos de imágenes para "<span class="search-term">{{ searchQuery }}</span>"</p>
            </template>
            <template v-else>
              <font-awesome-icon :icon="['fas', 'database']" size="2x" />
              <p>Aún no tienes ningún conjunto de imágenes.</p>
            </template>
          </div>
          <div v-else>
            <table class="data-table datasets-table">
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
                  <th @click="setSortField('image_count')" class="center-column sortable-header">
                    <span class="header-text">Imágenes</span>
                    <SortIcon :fieldName="'image_count'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('category_count')" class="center-column sortable-header">
                    <span class="header-text">Categorías</span>
                    <SortIcon :fieldName="'category_count'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('created_at')" class="sortable-header">
                    <span class="header-text">Fecha de creación</span>
                    <SortIcon :fieldName="'created_at'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th @click="setSortField('is_public')" class="center-column sortable-header">
                    <span class="header-text">Compartido</span>
                    <SortIcon :fieldName="'is_public'" :currentSort="sortBy" :currentOrder="sortOrder" />
                  </th>
                  <th class="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="dataset in datasets" :key="dataset.id" 
                    @click="viewDataset(dataset)" 
                    class="dataset-row">
                  <td v-if="isAdmin">
                    <span class="truncate" :title="dataset.username || '-'">
                      {{ truncateText(dataset.username, 20) || '-' }}
                    </span>
                  </td>
                  <td>
                    <span class="truncate" :title="dataset.name">
                      {{ truncateText(dataset.name, 40) }}
                    </span>
                  </td>
                  <td>
                    <span class="truncate" :title="dataset.description || '-'">
                      {{ dataset.description ? truncateText(dataset.description, isAdmin ? 20 : 30) : '-' }}
                    </span>
                  </td>
                  <td class="center-column">{{ dataset.image_count }}</td>
                  <td class="center-column">{{ dataset.category_count }}</td>
                  <td>{{ formatDate(dataset.created_at) }}</td>
                  <td class="center-column">
                    <font-awesome-icon 
                      :icon="['fas', dataset.is_public ? 'globe' : 'lock']" 
                      :class="dataset.is_public ? 'text-public' : 'text-private'"
                      :title="dataset.is_public ? 'Compartido' : 'Privado'"
                    />
                  </td>
                  <td class="actions-column">
                    <div class="actions-menu">
                      <button 
                        class="action-button" 
                        @click="(event) => toggleActionsMenu(dataset.id, event)"
                        :data-item-id="dataset.id"
                        :data-active="activeActionsMenu === dataset.id"
                      >
                        <font-awesome-icon :icon="['fas', 'ellipsis-vertical']" />
                      </button>
                      <ActionMenu
                        v-if="activeActionsMenu === dataset.id" 
                        :item="dataset" 
                        :itemId="dataset.id"
                        :position="getMenuPosition(dataset.id)"
                        :actions="getDatasetMenuActions(dataset)"
                        @view="viewDataset"
                        @edit="editDataset"
                        @delete="confirmDeleteDataset"
                        @publish="confirmPublishDataset"
                        @unpublish="confirmUnpublishDataset"
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
                  <span class="total-info">({{ totalDatasets }} conjuntos)</span>
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
                    {{ size }} conjuntos
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
      :title="`Eliminar conjunto de imágenes`"
      :message="deleteModalMessage"
      confirmText="Eliminar"
      cancelText="Cancelar"
      buttonType="danger"
      @confirm="deleteDataset"
      @cancel="cancelDelete"
    />
    <ConfirmationModal
      :isOpen="isShareModalOpen"
      :title="shareModalTitle"
      :message="shareModalMessage"
      :confirmText="shareModalAction === 'publish' ? 'Compartir' : 'Privatizar'"
      cancelText="Cancelar"
      buttonType="success"
      @confirm="processShareAction"
      @cancel="cancelShareAction"
    />
    <AddDatasetModal
      :isOpen="isAddDatasetModalOpen"
      @close="closeAddDatasetModal"
      @dataset-added="onDatasetAdded"
    />
    <EditDatasetModal
      :isOpen="isEditDatasetModalOpen"
      :dataset="datasetToEdit"
      @close="closeEditDatasetModal"
      @dataset-updated="onDatasetUpdated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import { userPreferencesStore } from '@/stores/userPreferencesStore.js';
import ActionMenu from '@/components/utils/ActionMenu.vue';
import ConfirmationModal from '@/components/utils/ConfirmationModal.vue';
import SortIcon from '@/components/utils/SortIcon.vue';
import AddDatasetModal from '@/components/datasets/AddDatasetModal.vue';
import EditDatasetModal from '@/components/datasets/EditDatasetModal.vue';

const router = useRouter();
const datasets = ref([]);
const isLoading = ref(true);
const activeActionsMenu = ref(null);
const isDeleteModalOpen = ref(false);
const datasetToDelete = ref(null);
const deleteModalMessage = ref('');
const isAddDatasetModalOpen = ref(false);
const isEditDatasetModalOpen = ref(false);
const datasetToEdit = ref(null);

const isSearchTransitioning = ref(false);

const isShareModalOpen = ref(false);
const datasetToShare = ref(null);
const shareModalAction = ref(''); // 'publish' o 'unpublish'.
const shareModalMessage = ref('');
const shareModalTitle = ref('');

const preferencesStore = userPreferencesStore();
const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.is_admin || false);

const currentPage = ref(1);
const pageSize = ref(5);
const totalDatasets = ref(0);
const totalPages = computed(() => Math.ceil(totalDatasets.value / pageSize.value) || 1);
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
    preferencesStore.setDatasetPageSize(pageSize.value);
    
    // Calcular la primera entrada de la página actual con el tamaño antiguo.
    const currentSize = pageSize.value; // Guardar el tamaño actual.
    const firstItemIndex = (currentPage.value - 1) * currentSize;
    
    // Calcular qué página mostrará esa primera entrada con el nuevo tamaño.
    const newPage = Math.floor(firstItemIndex / currentSize) + 1;
    currentPage.value = newPage;
    
    // Asegurar que no exceda el número total de páginas.
    const newTotalPages = Math.ceil(totalDatasets.value / currentSize) || 1;
    if (currentPage.value > newTotalPages) {
      currentPage.value = newTotalPages;
    }
    
    // Recargar datos con el nuevo tamaño de página.
    await fetchDatasets();
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
    // Por defecto ordenar descendentemente (excepto para nombre).
    sortOrder.value = (field === 'name' || field === 'username') ? 'asc' : 'desc';
  }
  
  // Recargar datos con la nueva ordenación.
  await fetchDatasets();
};

// Manejar la búsqueda con debounce.
const handleSearch = () => {

  isSearchTransitioning.value = true;
  
  // Limpiar el timeout anterior si existe.
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  // Esperar a que el usuario termine de escribir.
  searchTimeout.value = setTimeout( async () => {
    // Resetear a la página 1 al buscar.
    currentPage.value = 1;
    
    // Recargar datos con la nueva búsqueda.
    await fetchDatasets();
  }, 300);
};

const clearSearch = async () => {
  // Activar estado de transición para evitar parpadeos.
  isSearchTransitioning.value = true;
  
  searchQuery.value = '';

  await fetchDatasets();
};

const fetchDatasets = async () => {
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
    let url = `/datasets/?skip=${skip}&limit=${pageSize.value}&sort_by=${sortBy.value}&sort_order=${sortOrder.value}`;
    
    // Añadir parámetro de búsqueda si se está buscando.
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`;
    }
    
    const response = await axios.get(url);
    
    // Procesar la respuesta
    if (response.data && Array.isArray(response.data.datasets)) {
      datasets.value = response.data.datasets;
      totalDatasets.value = response.data.count || datasets.value.length;
    } else {
      datasets.value = [];
      totalDatasets.value = 0;
      notifyInfo("Sin datos",
      "No se encontraron conjuntos de imágenes para mostrar.");
    }
    
    return response;
  } catch (error) {
    console.error('Error while fetching datasets: ', error);
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
    await fetchDatasets();
  } catch (error) {
    console.error('Error while changing pages: ', error);
  } finally {
    isSearchTransitioning.value = false;
  }
};

// Controlar menú de accione.
const toggleActionsMenu = (datasetId, event) => {
  // Detener la propagación del evento para evitar que se active viewDataset.
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
  if (activeActionsMenu.value === datasetId) {
    activeActionsMenu.value = null;
  } else {
    // Activar el menú.
    activeActionsMenu.value = datasetId;
    const newButton = document.querySelector(`.action-button[data-item-id="${datasetId}"]`);
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

const getMenuPosition = (datasetId) => {
  return { 
    top: true,
    right: false
  };
};

const showAddDatasetModal = () => {
  isAddDatasetModalOpen.value = true;
  closeActionsMenu();
};

const closeAddDatasetModal = () => {
  isAddDatasetModalOpen.value = false;
};

const onDatasetAdded = async (newDataset) => {
  await fetchDatasets();
};

const viewDataset = (dataset) => {
  closeActionsMenu();
  router.push(`/dataset/${dataset.id}`);
};

const editDataset = (dataset) => {
  closeActionsMenu();
  datasetToEdit.value = dataset;
  isEditDatasetModalOpen.value = true;
};

const closeEditDatasetModal = () => {
  isEditDatasetModalOpen.value = false;
  datasetToEdit.value = null;
};

const onDatasetUpdated = async (updatedDataset) => {
  // Se recarga en estos casos:
  // 1. Si hay una búsqueda activa.
  // 2. Si se modificó un campo que afecta a la ordenación actual.
  if (
    searchQuery.value.trim() || 
    // Verificar si el campo por el que se ordena se ha modificado.
    (updatedDataset.hasOwnProperty(sortBy.value) && 
     sortBy.value !== 'image_count' && 
     sortBy.value !== 'category_count')
  ) {
    // Recargar la tabla en ese caso.
    await fetchDatasets();
  } else {
    // Sin búsqueda activa y sin cambios en el campo de ordenación,
    // se puede actualizar sólo el dataset en la lista local.
    const index = datasets.value.findIndex(d => d.id === updatedDataset.id);
    if (index !== -1) {
      datasets.value[index] = updatedDataset;
    } else {
      // Si no se encuentra el dataset, recargamos todo.
      await fetchDatasets();
    }
  }
};

const confirmDeleteDataset = (dataset) => {
  closeActionsMenu();
  datasetToDelete.value = dataset;
  deleteModalMessage.value = `Estás a punto de eliminar el conjunto de imágenes. Esta acción eliminará todas las imágenes y etiquetas asociadas y no se puede deshacer.`;
  isDeleteModalOpen.value = true;
};

const cancelDelete = () => {
  isDeleteModalOpen.value = false;
  datasetToDelete.value = null;
  activeActionsMenu.value = null;
  
  setTimeout(() => {
    const activeButtons = document.querySelectorAll('.action-button[data-active="true"]');
    activeButtons.forEach(button => {
      button.setAttribute('data-active', 'false');
    });
  }, 100);
};

const deleteDataset = async () => {
  if (!datasetToDelete.value) return;
  
  try {
    await axios.delete(`/datasets/${datasetToDelete.value.id}`);
    
    // Si se está en una página con un solo elemento (el cuál se está eliminando)
    // y no es la primera página, se debe volver a la página anterior.
    if (datasets.value.length === 1 && currentPage.value > 1) {
      currentPage.value--;
    }
    
    // Actualizar la lista después de eliminar.
    await fetchDatasets();
    
    // Si después de actualizar no hay datasets en la página actual pero hay datasets en total,
    // puede que se necesite ajustar la página actual de nuevo.
    if (datasets.value.length === 0 && totalDatasets.value > 0) {
      // Calcular el número máximo de páginas después de la eliminación.
      const maxPage = Math.ceil(totalDatasets.value / pageSize.value);
      if (currentPage.value > maxPage) {
        currentPage.value = maxPage;
        await fetchDatasets();
      }
    }
    
    notifySuccess("Conjunto de imágenes eliminado", 
    `Se ha eliminado el conjunto ${datasetToDelete.value.name} con éxito.`);
  } catch (error) {
    console.error('Error while deleting dataset: ', error);
    handleApiError(error);
  } finally {
    isDeleteModalOpen.value = false;
    datasetToDelete.value = null;
  }
};

const confirmPublishDataset = (dataset) => {
  closeActionsMenu();
  datasetToShare.value = dataset;
  shareModalAction.value = 'publish';
  shareModalTitle.value = `Compartir conjunto de imágenes`;
  shareModalMessage.value = 'Al compartir este conjunto de imágenes, será visible para todos los usuarios de la plataforma. ¿Deseas continuar?';
  isShareModalOpen.value = true;
};

const confirmUnpublishDataset = (dataset) => {
  closeActionsMenu();
  datasetToShare.value = dataset;
  shareModalAction.value = 'unpublish';
  shareModalTitle.value = `Privatizar conjunto de imágenes`;
  shareModalMessage.value = 'Al dejar de compartir este conjunto de imágenes, ya no será visible para otros usuarios. ¿Deseas continuar?';
  isShareModalOpen.value = true;
};

const cancelShareAction = () => {
  isShareModalOpen.value = false;
  datasetToShare.value = null;
  shareModalAction.value = '';
};

const processShareAction = async () => {
  if (!datasetToShare.value) return;
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    // Preparar los datos según la acción (publicar o despublicar).
    const isPublic = shareModalAction.value === 'publish';
    
    // Actualizar el dataset.
    const response = await axios.patch(`/datasets/${datasetToShare.value.id}`, {
      is_public: isPublic
    });
    
    // Determinar si es necesario recargar toda la tabla.
    // Se recarga en estos casos:
    // 1. Si hay una búsqueda activa.
    // 2. Si se está ordenando por is_public (ya que el cambio afecta la ordenación).
    if (searchQuery.value.trim() || sortBy.value === 'is_public') {
      // Recargar todos los datos.
      await fetchDatasets();
    } else {
      // Solo actualizar el dataset en la lista local.
      const index = datasets.value.findIndex(d => d.id === datasetToShare.value.id);
      if (index !== -1) {
        datasets.value[index].is_public = isPublic;
      }
    }
    
    notifySuccess(isPublic ? "Conjunto compartido" : "Conjunto no compartido", 
    `El conjunto ${datasetToShare.value.name} ha sido ${isPublic ? "compartido" : "dejado de compartir"} con éxito.`);
  } catch (error) {
    console.error('Error while updating dataset sharing status: ', error);
    handleApiError(error);
  } finally {
    isShareModalOpen.value = false;
    datasetToShare.value = null;
    shareModalAction.value = '';
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
        notifyError("Conjunto de imágenes no encontrado",
        "El conjunto solicitado no existe o ha sido eliminado.");
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
    "Ha ocurrido un problema al cargar los datos de los conjuntos de imágenes.");
  }
};


const formatDate = (dateString) => {
  if (!dateString) return '';
  
  // Convertir UTC (como la almacena de base de datos) a hora local.
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

const truncateText = (text, maxLength) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

const handleScroll = () => {
  if (activeActionsMenu.value !== null) {
    closeActionsMenu();
  }
};

const getDatasetMenuActions = (dataset) => {
  // Acciones básicas que siempre estarán presentes.
  const baseActions = [
    { label: 'Abrir', event: 'view', icon: ['fas', 'folder-open'], class: 'view' },
    { label: 'Editar', event: 'edit', icon: ['fas', 'edit'], class: 'edit' }
  ];
  
  // Acción de compartir/no compartir según el estado actual.
  if (dataset.is_public) {
    baseActions.push({ 
      label: 'Privatizar', 
      event: 'unpublish', 
      icon: ['fas', 'lock'], 
      class: 'unpublish' 
    });
  } else {
    baseActions.push({ 
      label: 'Compartir', 
      event: 'publish', 
      icon: ['fas', 'globe'], 
      class: 'publish' 
    });
  }
  
  // Acción de eliminar (siempre al final).
  baseActions.push({ 
    label: 'Eliminar', 
    event: 'delete', 
    icon: ['fas', 'trash-alt'], 
    class: 'delete' 
  });
  
  return baseActions;
};

onMounted(async () => {
  try {
    isSearchTransitioning.value = true;
    isLoading.value = true;
    
    // Restaurar preferencia de tamaño de página si existe.
    const savedPageSize = preferencesStore.datasetPageSize;
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
    
    if (urlSort && ['name', 'created_at', 'image_count', 'category_count', 'is_public', 'username'].includes(urlSort)) {
      sortBy.value = urlSort;
    }
    
    if (urlOrder && ['asc', 'desc'].includes(urlOrder)) {
      sortOrder.value = urlOrder;
    }
    
    if (urlSearch) {
      searchQuery.value = urlSearch;
    }
    
    await fetchDatasets();
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
  const urlParams = new URLSearchParams();
  urlParams.set('page', currentPage.value);
  urlParams.set('sort', sortBy.value);
  urlParams.set('order', sortOrder.value);
  
  if (searchQuery.value.trim()) {
    urlParams.set('search', searchQuery.value);
  }
  
  // Actualizar la URL sin recargar la página.
  const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
  history.pushState({}, '', newUrl);
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/search.css"></style>
<style scoped src="@/assets/styles/table.css"></style>
<style scoped>
.datasets-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 90px; 
  padding-bottom: 40px;
}

.datasets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.datasets-header h1 {
  color: #333;
  margin: 0;
  font-size: 1.8rem;
}

.add-dataset-button {
  width: auto;
  margin-top: 0;
  padding: 10px 20px;
}

.button-icon {
  margin-right: 8px;
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

.dataset-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.dataset-row:hover {
  background-color: #f8f9fa;
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
/* Columna de usuario */
.datasets-table th:nth-child(1), 
.datasets-table td:nth-child(1) {
  max-width: 140px;
}

/* Columna de nombre */
.datasets-table th:nth-child(2), 
.datasets-table td:nth-child(2) {
  max-width: 180px;
}

/* Columna de descripción */
.datasets-table th:nth-child(3), 
.datasets-table td:nth-child(3) {
  max-width: 150px;
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

/* Columna de compartido */
.text-public {
  color: #0066cc;
}

.text-private {
  color: #495057;
}

/* Diseño responsive */
@media (max-width: 768px) {
  .datasets-view {
    padding: 10px;
  }
  
  .datasets-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .add-dataset-button {
    width: 100%;
  }
  
  .data-table thead tr th.sortable-header {
    padding-right: 24px;
  }
  
  .datasets-table th,
  .datasets-table td {
    padding: 8px 6px;
  }
  
  .datasets-table th:nth-child(2),
  .datasets-table td:nth-child(2) {
    max-width: 110px;
  }
  
  .datasets-table th:nth-child(3),
  .datasets-table td:nth-child(3) {
    max-width: 80px;
  }
}
</style>