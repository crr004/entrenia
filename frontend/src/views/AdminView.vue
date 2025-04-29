<template>
  <div class="admin-view">
    <div class="admin-header">
      <h1>Panel de administración</h1>
      <button class="app-button add-user-button" @click="showAddUserModal">
        <font-awesome-icon :icon="['fas', 'user-plus']" class="button-icon" />
        Añadir usuario
      </button>
    </div>
    <div class="search-container">
      <div class="search-box">
        <font-awesome-icon :icon="['fas', 'search']" class="search-icon" />
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Buscar por correo, nombre o usuario..."
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
    <div class="admin-content">
      <div class="table-wrapper">
        <div class="table-container users-table-container">
          <div v-if="isLoading || isSearchTransitioning" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando usuarios...</p>
          </div>
          <div v-else-if="users.length === 0" class="empty-state">
            <template v-if="searchQuery.trim()">
              <font-awesome-icon :icon="['fas', 'search']" size="2x" />
              <p>No se encontraron usuarios para "<span class="search-term">{{ searchQuery }}</span>"</p>
            </template>
            <template v-else>
              <font-awesome-icon :icon="['fas', 'users-slash']" size="2x" />
              <p>No hay usuarios en el sistema</p>
            </template>
          </div>
          <div v-else>
            <table class="data-table users-table">
              <thead>
                <tr>
                  <th @click="setSortField('email')" class="sortable-header">
                    <span class="header-text">Correo</span>
                    <SortIcon 
                      fieldName="email"
                      :currentSort="sortBy"
                      :currentOrder="sortOrder"
                    />
                  </th>
                  <th @click="setSortField('full_name')" class="sortable-header">
                    <span class="header-text">Nombre</span>
                    <SortIcon 
                      fieldName="full_name"
                      :currentSort="sortBy"
                      :currentOrder="sortOrder"
                    />
                  </th>
                  <th @click="setSortField('username')" class="sortable-header">
                    <span class="header-text">Usuario</span>
                    <SortIcon 
                      fieldName="username"
                      :currentSort="sortBy"
                      :currentOrder="sortOrder"
                    />
                  </th>
                  <th @click="setSortField('is_admin')" class="sortable-header">
                    <span class="header-text">Admin</span>
                    <SortIcon 
                      fieldName="is_admin"
                      :currentSort="sortBy"
                      :currentOrder="sortOrder"
                    />
                  </th>
                  <th @click="setSortField('is_active')" class="sortable-header">
                    <span class="header-text">Estado</span>
                    <SortIcon 
                      fieldName="is_active"
                      :currentSort="sortBy"
                      :currentOrder="sortOrder"
                    />
                  </th>
                  <th  @click="setSortField('is_verified')" class="sortable-header">
                    <span class="header-text">Verificado</span>
                    <SortIcon 
                      fieldName="is_verified"
                      :currentSort="sortBy"
                      :currentOrder="sortOrder"
                    />
                  </th>
                  <th class="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id" :class="{ 'inactive-row': !user.is_active }">
                  <td>
                    <span class="truncate" :title="user.email">
                      {{ truncateText(user.email, 31) }}
                    </span>
                  </td>
                  <td>
                    <span class="truncate" :title="user.full_name || '-'">
                      {{ truncateText(user.full_name, 20) || '-' }}
                    </span>
                  </td>
                  <td>
                    <span class="truncate" :title="user.username">
                      {{ truncateText(user.username, 20) }}
                    </span>
                  </td>
                  <td class="center-column">
                    <span v-if="user.is_admin" class="admin-badge" title="Administrador">
                      <font-awesome-icon :icon="['fas', 'crown']" />
                    </span>
                    <span v-else>-</span>
                  </td>
                  <td class="center-column">
                    <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                      {{ user.is_active ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td class="center-column">
                    <span :class="['status-badge', user.is_verified ? 'verified' : 'unverified']">
                      {{ user.is_verified ? 'Verificado' : 'No verificado' }}
                    </span>
                  </td>
                  <td class="actions-column">
                    <div class="actions-menu">
                      <button 
                        class="action-button" 
                        @click="toggleActionsMenu(user.id)"
                        :data-active="activeActionsMenu === user.id ? 'true' : 'false'"
                        :data-item-id="user.id"
                      >
                        <font-awesome-icon :icon="['fas', 'ellipsis-vertical']" />
                      </button>
                      <ActionMenu 
                        v-if="activeActionsMenu === user.id"
                        :item="user"
                        :itemId="user.id"
                        :position="getMenuPosition(user.id)"
                        @edit="editUser"
                        @delete="confirmDeleteUser"
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
                  :disabled="currentPage === 1 || totalPages <= 1" 
                  @click="changePage(currentPage - 1)"
                >
                  <font-awesome-icon :icon="['fas', 'chevron-left']" class="pagination-icon" />
                </button>
                <div class="pagination-info">
                  Página {{ currentPage }} de {{ totalPages || 1 }} ({{ totalUsers }} usuarios)
                </div>
                <button 
                  class="pagination-button" 
                  :disabled="currentPage === totalPages || totalPages <= 1" 
                  @click="changePage(currentPage + 1)"
                >
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="pagination-icon" />
                </button>
              </div>
              <div class="page-size-selector">
                <label for="page-size">Mostrar:</label>
                <select 
                  id="page-size" 
                  v-model="pageSize" 
                  @change="handlePageSizeChange"
                  class="page-size-select"
                >
                  <option v-for="size in pageSizeOptions" :key="size" :value="size">
                    {{ size }} usuarios
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
      :title="`Eliminar usuario: ${userToDelete?.username || ''}`"
      :message="deleteModalMessage"
      confirmText="Eliminar"
      cancelText="Cancelar"
      @confirm="deleteUser"
      @cancel="cancelDelete"
    />
    <AddUserModal 
      :isOpen="isAddUserModalOpen"
      @close="isAddUserModalOpen = false"
      @userAdded="handleUserAdded"
    />
    <EditUserModal 
      :isOpen="isEditUserModalOpen"
      :userId="userToEdit"
      @close="closeEditUserModal"
      @userUpdated="handleUserUpdated"
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
import AddUserModal from '@/components/users/AddUserModal.vue';
import EditUserModal from '@/components/users/EditUserModal.vue';

const router = useRouter();
const route = useRoute();
const users = ref([]);
const isLoading = ref(true);
const activeActionsMenu = ref(null);
const isDeleteModalOpen = ref(false);
const userToDelete = ref(null);
const deleteModalMessage = ref('');
const isAddUserModalOpen = ref(false);
const isEditUserModalOpen = ref(false);
const userToEdit = ref(null);

const preferencesStore = userPreferencesStore();
const authStore = useAuthStore();

const currentPage = ref(1);
const pageSize = ref(5);
const totalUsers = ref(0);
const totalPages = computed(() => Math.ceil(totalUsers.value / pageSize.value) || 1);

const pageSizeOptions = [5, 10, 25, 50, 100];

const searchQuery = ref('');
const searchTimeout = ref(null);

const isSearchTransitioning = ref(false);

const sortBy = ref('created_at');
const sortOrder = ref('desc');

const handlePageSizeChange = async () => {
  try {
    // Activar estado de transición para evitar parpadeos.
    isSearchTransitioning.value = true;
    
    // Guardar el nuevo tamaño de página en las preferencias del usuario.
    preferencesStore.setAdminPageSize(pageSize.value);
    
    // Calcular la primera entrada de la página actual con el tamaño actual.
    const currentSize = pageSize.value;
    const firstItemIndex = (currentPage.value - 1) * currentSize;
    
    // Calcular qué página mostrará esa primera entrada con el nuevo tamaño.
    const newPage = Math.floor(firstItemIndex / currentSize) + 1;
    currentPage.value = newPage;
    
    // Asegurar que no exceda el número total de páginas.
    const newTotalPages = Math.ceil(totalUsers.value / currentSize) || 1;
    if (currentPage.value > newTotalPages) {
      currentPage.value = newTotalPages;
    }
    
    // Recargar datos con el nuevo tamaño de página.
    await fetchUsers();
  } catch (error) {
    console.error("Error while changing page size: ", error);
  } finally {
    // Desactivar el estado de transición en el siguiente tick.
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
    // Si es un nuevo campo, establecerlo y dirección por defecto.
    sortBy.value = field;
    // Por defecto ordenar descendentemente (excepto para campos de texto).
    sortOrder.value = (field === 'email' || field === 'username' || field === 'full_name') ? 'asc' : 'desc';
  }
  
  // Recargar datos con la nueva ordenación.
  await fetchUsers();
};

// Manejar la búsqueda con debounce.
const handleSearch = () => {
  // Activar estado de carga inmediatamente al escribir.
  isSearchTransitioning.value = true;
  
  // Limpiar el timeout anterior si existe.
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  // Esperar a que el usuario termine de escribir.
  searchTimeout.value = setTimeout(async () => {
    // Resetear a la página 1 al hacer una búsqueda.
    currentPage.value = 1;
    
    // Obtener los usuarios que coincidan con la búsqueda.
    await fetchUsers();
  }, 300);
};

const clearSearch = async () => {
  // Activar estado de transición para evitar mensaje intermedio (parpadeo).
  isSearchTransitioning.value = true;
  isLoading.value = true;
  
  // Limpiar la búsqueda.
  searchQuery.value = '';
  
  // Resetear a la página 1.
  currentPage.value = 1;
  
  // Obtener todos los usuarios.
  await fetchUsers();
};

const fetchUsers = async () => {
  isLoading.value = true;
  closeActionsMenu();
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    

    const skip = (currentPage.value - 1) * pageSize.value;
    
    // Construir parámetros de la consulta.
    const params = {
      skip,
      limit: pageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    };
    
    // Añadir parámetro de búsqueda si existe.
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim();
    }
    
    const response = await axios.get('/users/', { params });
    
    // Procesar la respuesta.
    if (response.data && Array.isArray(response.data.users)) {
      users.value = response.data.users;
      totalUsers.value = response.data.count || users.value.length;
    } else {
      users.value = [];
      totalUsers.value = 0;
    }
  } catch (error) {
    console.error('Error fetching users: ', error);
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
    await fetchUsers();
  } catch (error) {
    console.error('Error while changing pages: ', error);
  } finally {
    isSearchTransitioning.value = false;
  }
};

const toggleActionsMenu = (userId) => {
  // Primero, cerrar cualquier menú activo.
  if (activeActionsMenu.value !== null) {
    const prevButton = document.querySelector(`.action-button[data-item-id="${activeActionsMenu.value}"]`);
    if (prevButton) {
      prevButton.setAttribute('data-active', 'false');
    }
  }

  // Si se hace clic en el mismo botón, cerrar el menú.
  if (activeActionsMenu.value === userId) {
    activeActionsMenu.value = null;
  } else {
    // Activar el menú.
    activeActionsMenu.value = userId;
    const newButton = document.querySelector(`.action-button[data-item-id="${userId}"]`);
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

const getMenuPosition = (userId) => {
  return { 
    top: true,
    right: false
  };
};

const showAddUserModal = () => {
  isAddUserModalOpen.value = true;
  closeActionsMenu();
};

const handleUserAdded = async (newUser) => {
  // Resetear a la página 1 y recargar datos.
  currentPage.value = 1;
  await fetchUsers();
};

const editUser = (user) => {
  closeActionsMenu();
  userToEdit.value = user.id;
  isEditUserModalOpen.value = true;
};

const closeEditUserModal = () => {
  isEditUserModalOpen.value = false;
  userToEdit.value = null;
};

const handleUserUpdated = async (updatedUser) => {
  // Verificar si hay búsqueda activa o si el campo actualizado afecta a la ordenación.
  if (
    searchQuery.value.trim() || 
    (sortBy.value !== 'created_at' && updatedUser.hasOwnProperty(sortBy.value))
  ) {
    const paginaActual = currentPage.value;
    
    // Recargar la tabla completa.
    await fetchUsers();
    
    // Si después de recargar no hay usuarios en la página actual pero hay usuarios en total,
    // retroceder a la página anterior.
    if (users.value.length === 0 && totalUsers.value > 0 && paginaActual > 1) {
      currentPage.value = paginaActual - 1;
      await fetchUsers();
    }
  } else {
    // Si no hay búsqueda ni actualización de campos de orden, simplemente
    // actualizar el usuario en la lista local si es posible.
    const index = users.value.findIndex(u => u.id === updatedUser.id);
    if (index !== -1) {
      users.value[index] = updatedUser;
    } else {
      // Si no se encuentra el usuario, recargar todo.
      await fetchUsers();
    }
  }
};

const confirmDeleteUser = (user) => {
  closeActionsMenu();
  userToDelete.value = user;
  
  if (user.is_admin) {
    deleteModalMessage.value = `Estás a punto de eliminar un usuario administrador. Esta acción no se puede deshacer.`;
  } else {
    deleteModalMessage.value = `Estás a punto de eliminar el usuario ${user.username}. Esta acción no se puede deshacer.`;
  }
  
  isDeleteModalOpen.value = true;
};

const cancelDelete = () => {
  isDeleteModalOpen.value = false;
  userToDelete.value = null;
  activeActionsMenu.value = null;
  
  // Dar un pequeño tiempo antes de permitir abrir menús de nuevo.
  setTimeout(() => {
    const activeButtons = document.querySelectorAll('.action-button[data-active="true"]');
    activeButtons.forEach(button => {
      button.setAttribute('data-active', 'false');
    });
  }, 100);
};

const deleteUser = async () => {
  if (!userToDelete.value) return;
  
  try {
    await axios.delete(`/users/${userToDelete.value.id}`);
    
    // Verificar si se debe cambiar de página después de eliminar.
    if (users.value.length === 1 && currentPage.value > 1) {
      currentPage.value--; // Retroceder si era el último elemento de la página.
    }
    
    // Refrescar la lista.
    await fetchUsers();
    
    notifySuccess("Usuario eliminado", 
      `Se ha eliminado el usuario "${userToDelete.value.username}" con éxito.`);
  } catch (error) {
    console.error('Error deleting user:', error);
    handleApiError(error);
  } finally {
    isDeleteModalOpen.value = false;
    userToDelete.value = null;
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
        if (data.detail && data.detail.includes("Admins")) {
          notifyError("Acción denegada", 
          "Los administradores no pueden eliminarse a sí mismos.");
        } else if (data.detail && data.detail.includes("credentials")) {
          notifyInfo("Sesión expirada", 
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else if (data.detail && data.detail.includes("privileges")) {
          router.push('/');
        } else {
          notifyError("Acceso denegado", 
          "No tienes permiso para realizar esta acción.");
        }
        break;
      case 404:
        notifyError("Usuario no encontrado", 
        "El usuario no existe en el sistema.");
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
    "Ha ocurrido un problema.");
  }
};

// Truncar campos de texto largos.
const truncateText = (text, maxLength) => {
  if (!text) return null;
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

const handleScroll = () => {
  if (activeActionsMenu.value !== null) {
    closeActionsMenu();
  }
};

// Actualizar la URL cuando cambian los parámetros relevantes.
watch([currentPage, sortBy, sortOrder, searchQuery], () => {
  const query = {
    page: currentPage.value,
    sort: sortBy.value,
    order: sortOrder.value
  };
  
  // Solo incluir el parámetro de búsqueda si tiene contenido.
  if (searchQuery.value.trim()) {
    query.search = searchQuery.value.trim();
  }
  
  // Actualizar la URL usando Vue Router sin recargar la página.
  router.replace({ 
    path: route.path, 
    query 
  });
});

onMounted(async () => {
  try {
    isSearchTransitioning.value = true;
    isLoading.value = true;
    
    // Restaurar preferencias del usuario.
    const savedPageSize = preferencesStore.adminPageSize;
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
    
    if (urlSort && ['email', 'username', 'full_name', 'is_admin', 'is_active', 'is_verified', 'created_at'].includes(urlSort)) {
      sortBy.value = urlSort;
    }
    
    if (urlOrder && ['asc', 'desc'].includes(urlOrder)) {
      sortOrder.value = urlOrder;
    }
    
    if (urlSearch) {
      searchQuery.value = urlSearch;
    }
    
    await fetchUsers();
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
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/search.css"></style>
<style scoped src="@/assets/styles/table.css"></style>
<style scoped>
.admin-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 90px; 
  padding-bottom: 40px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.admin-header h1 {
  color: #333;
  margin: 0;
  font-size: 1.8rem;
}

.admin-view .admin-header .add-user-button {
  width: auto;
  margin-top: 0;
  padding: 10px 20px;
}

.button-icon {
  margin-right: 8px;
}

.admin-content {
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

/* Estilos específicos para la tabla de usuarios */
.users-table th:nth-child(1), 
.users-table td:nth-child(1) {
  max-width: 205px; /* Correo */
}

.users-table th:nth-child(2), 
.users-table td:nth-child(2) {
  max-width: 180px; /* Nombre */
}

.users-table th:nth-child(3), 
.users-table td:nth-child(3) {
  max-width: 150px; /* Usuario */
}


.admin-badge {
  color: gold;
  background-color: rgba(0, 0, 0, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

/* Responsive */
@media (max-width: 768px) {
  .admin-view {
    padding: 10px;
  }
  
  .admin-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .admin-view .admin-header .add-user-button {
    width: 100%;
  }
}
</style>
