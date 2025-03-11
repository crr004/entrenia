<template>
  <div class="admin-view">
    <div class="admin-header">
      <h1>Panel de administración</h1>
      <button class="app-button add-user-button" @click="showAddUserModal">
        <font-awesome-icon :icon="['fas', 'user-plus']" class="button-icon" />
        Añadir usuario
      </button>
    </div>

    <!-- Búsqueda fuera del admin-content -->
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
        <div class="users-table-container">
          <div v-if="isLoading || isSearchTransitioning" class="loading-container">
            <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
            <p>Cargando usuarios...</p>
          </div>
          
          <!-- Condición modificada para diferenciar entre búsqueda sin resultados y sistema sin usuarios -->
          <div v-else-if="(searchQuery.trim() && paginatedResults.length === 0) || (!searchQuery.trim() && users.length === 0)" class="empty-state">
            <template v-if="searchQuery.trim()">
              <font-awesome-icon :icon="['fas', 'search']" size="2x" />
              <p>No se encontraron usuarios para "<span class="search-term">{{ searchQuery }}</span>"</p>
            </template>
            <template v-else>
              <font-awesome-icon :icon="['fas', 'users-slash']" size="2x" />
              <p>No hay usuarios en el sistema</p>
            </template>
          </div>
          
          <div v-else-if="paginatedResults.length > 0">
            <table class="users-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Nombre</th>
                  <th>Usuario</th>
                  <th class="center-column">Admin</th>
                  <th class="center-column">Estado</th>
                  <th class="center-column">Verificado</th>
                  <th class="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedResults" :key="user.id" :class="{ 'inactive-user': !user.is_active }">
                  <td>{{ user.email }}</td>
                  <td>{{ user.full_name || '-' }}</td>
                  <td>{{ user.username || '-' }}</td>
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
                        <font-awesome-icon :icon="['fas', 'ellipsis-v']" />
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
            
            <!-- Controles de paginación -->
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
    
              <!-- Selector de tamaño de página (siempre visible) -->
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
import { ref, onMounted, computed, watch } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';
import ActionMenu from '@/components/ActionMenu.vue';
import { useAuthStore } from '@/stores/authStore';
import ConfirmationModal from '@/components/ConfirmationModal.vue';
import AddUserModal from '@/components/AddUserModal.vue';
import EditUserModal from '@/components/EditUserModal.vue';

const router = useRouter();
const users = ref([]);
const isLoading = ref(true);
const activeActionsMenu = ref(null);
const isDeleteModalOpen = ref(false);
const userToDelete = ref(null);
const deleteModalMessage = ref('');
const isAddUserModalOpen = ref(false);
const isEditUserModalOpen = ref(false);
const userToEdit = ref(null);

// Nuevas variables para la paginación
const currentPage = ref(1);
const pageSize = ref(10);
const totalUsers = ref(0);
const totalPages = computed(() => Math.ceil(totalUsers.value / pageSize.value));

// Opciones para el tamaño de página
const pageSizeOptions = [10, 25, 50, 100];

// Método para manejar el cambio de tamaño de página
const handlePageSizeChange = () => {
  // Activamos el estado de carga para evitar mostrar mensajes incorrectos durante la transición
  isLoading.value = true;
  
  // Guardar la preferencia del usuario
  localStorage.setItem('adminPageSize', pageSize.value);
  
  // Primero reseteamos a la página 1
  currentPage.value = 1;
  
  // Si estamos en una búsqueda, actualizar los resultados paginados
  if (searchQuery.value.trim()) {
    // No llamar a fetchUsers, sino actualizar los resultados de búsqueda paginados
    setTimeout(() => {
      updateDisplayedUsers(); 
      isLoading.value = false;
    }, 100);
  } else {
    // Para la vista normal, obtener nuevos datos
    fetchUsers();
  }
};

const authStore = useAuthStore();

// Variables para la búsqueda
const searchQuery = ref('');
const searchTimeout = ref(null);

// Variable para controlar el estado intermedio entre borrar búsqueda y cargar resultados
const isSearchTransitioning = ref(false);

// Variables para manejar la paginación de búsqueda
const allSearchResults = ref([]);  // Almacena todos los resultados de la búsqueda
const paginatedResults = computed(() => {
  if (!searchQuery.value.trim()) return users.value;
  
  // Calcular el rango de usuarios a mostrar en la página actual
  const startIndex = (currentPage.value - 1) * pageSize.value;
  const endIndex = Math.min(startIndex + pageSize.value, allSearchResults.value.length);
  
  // Devolver solo los usuarios de la página actual
  return allSearchResults.value.slice(startIndex, endIndex);
});

// Función para manejar la búsqueda con debounce
const handleSearch = () => {
  // Activar estado de carga inmediatamente al escribir
  // Esto mostrará el spinner mientras se completa el debounce
  isSearchTransitioning.value = true;
  
  // Limpiamos el timeout anterior si existe
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  
  // Esperamos a que el usuario termine de escribir
  searchTimeout.value = setTimeout(() => {
    // Si la búsqueda está vacía, volver a cargar todos los usuarios
    if (!searchQuery.value || searchQuery.value.trim() === '') {
      isLoading.value = true;
      fetchUsers();
    } else {
      // Realizar búsqueda local siempre, incluso si la búsqueda anterior no dio resultados
      performLocalSearch();
    }
  }, 300);
};

// Función para realizar búsqueda local con mejoras
const performLocalSearch = async () => {
  isLoading.value = true;
  closeActionsMenu();

  try {
    const query = searchQuery.value.trim().toLowerCase();
    
    // Si la búsqueda está vacía, cargar todos los usuarios
    if (!query) {
      fetchUsers();
      return;
    }
    
    // Cargar todos los usuarios para la búsqueda local
    const response = await axios.get(`users/?skip=0&limit=500`);
    
    if (response.data && Array.isArray(response.data.users)) {
      const allUsers = response.data.users;
      
      // Filtrar los usuarios según el criterio de búsqueda
      const filteredUsers = allUsers.filter(user => 
        (user.email && user.email.toLowerCase().includes(query)) ||
        (user.username && user.username.toLowerCase().includes(query)) ||
        (user.full_name && user.full_name.toLowerCase().includes(query))
      );
      
      // Guardar todos los resultados de la búsqueda
      allSearchResults.value = filteredUsers;
      totalUsers.value = filteredUsers.length;
      
      // Resetear la página actual
      currentPage.value = 1;
      
      // Actualizar los usuarios mostrados con paginación
      updateDisplayedUsers();
    }
  } catch (error) {
    console.error('Error in search:', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
    // Desactivar el estado de transición cuando finaliza la búsqueda
    isSearchTransitioning.value = false;
  }
};

// Nueva función para actualizar los usuarios mostrados según la paginación
const updateDisplayedUsers = () => {
  if (!searchQuery.value.trim() || allSearchResults.value.length === 0) {
    return;
  }
  
  // Asegurarse que currentPage es válida para el nuevo tamaño de página
  const maxPossiblePage = Math.ceil(allSearchResults.value.length / pageSize.value);
  if (currentPage.value > maxPossiblePage) {
    currentPage.value = Math.max(1, maxPossiblePage);
  }
  
  const startIndex = (currentPage.value - 1) * pageSize.value;
  const endIndex = Math.min(startIndex + pageSize.value, allSearchResults.value.length);
  
  // Actualizar los usuarios mostrados basado en la página actual
  users.value = allSearchResults.value.slice(startIndex, endIndex);
};

// Limpiar la búsqueda
const clearSearch = () => {
  // Activar estado de transición para evitar mensaje intermedio
  isSearchTransitioning.value = true;
  isLoading.value = true;
  
  // Limpiar los resultados de búsqueda
  allSearchResults.value = [];
  
  // Luego limpia la búsqueda
  searchQuery.value = '';
  
  // Después carga los usuarios
  fetchUsers();
};

// Modificar fetchUsers para que no interfiera con búsqueda activa
const fetchUsers = async () => {
  // Si hay una búsqueda activa pero se ha limpiado, no hacemos nada especial
  isLoading.value = true;
  closeActionsMenu();
  
  try {
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }

    const skip = (currentPage.value - 1) * pageSize.value;
    const response = await axios.get(`/users/?skip=${skip}&limit=${pageSize.value}`);
    
    // Procesamos la respuesta normal
    if (response.data && Array.isArray(response.data.users)) {
      users.value = response.data.users;
      totalUsers.value = response.data.count || users.value.length;
    } else if (Array.isArray(response.data)) {
      users.value = response.data;
      totalUsers.value = response.data.length;
    } else {
      users.value = [];
      totalUsers.value = 0;
    }
    
    // Restablecer estado de transición
    isSearchTransitioning.value = false;
    
  } catch (error) {
    console.error('Error fetching users:', error);
    handleApiError(error);
    isSearchTransitioning.value = false; // Asegurarse de restablecer en caso de error
  } finally {
    isLoading.value = false;
  }
};

// Modificar changePage para manejar resultados de búsqueda
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  
  if (searchQuery.value.trim()) {
    // Si hay búsqueda activa, actualizar los usuarios mostrados en lugar de hacer una nueva solicitud
    updateDisplayedUsers();
  } else {
    fetchUsers();
  }
};

// Toggle actions menu for a user
const toggleActionsMenu = (userId) => {
  // Primero, cerrar cualquier menú activo
  if (activeActionsMenu.value !== null) {
    // Resetear el botón anterior
    const prevButton = document.querySelector(`.action-button[data-item-id="${activeActionsMenu.value}"]`);
    if (prevButton) {
      prevButton.setAttribute('data-active', 'false');
    }
  }

  // Si se hace clic en el mismo botón, cerrar el menú
  if (activeActionsMenu.value === userId) {
    activeActionsMenu.value = null;
  } else {
    // Activar el nuevo botón y menú
    activeActionsMenu.value = userId;
    const newButton = document.querySelector(`.action-button[data-item-id="${userId}"]`);
    if (newButton) {
      newButton.setAttribute('data-active', 'true');
    }
  }
};

// Close all action menus
const closeActionsMenu = () => {
  activeActionsMenu.value = null;
  // Limpiar cualquier botón activo
  const activeButtons = document.querySelectorAll('.action-button[data-active="true"]');
  activeButtons.forEach(button => {
    button.setAttribute('data-active', 'false');
  });
};

// Modifica la función getMenuPosition
const getMenuPosition = (userId) => {
  // Siempre queremos que el menú aparezca arriba y ligeramente desplazado a la izquierda
  return { 
    top: true,   // Siempre arriba del botón
    right: false // Siempre alineado a la izquierda del botón
  };
};

// Show modal to add a new user
const showAddUserModal = () => {
  isAddUserModalOpen.value = true;
};

// Añadir función para manejar cuando se agrega un usuario
const handleUserAdded = (newUser) => {
  // Resetear a la página 1
  currentPage.value = 1;
  
  // Si hay una búsqueda activa, verificar si el nuevo usuario coincide con la búsqueda
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase();
    
    // Verificar si el nuevo usuario coincide con la búsqueda
    const matches = 
      (newUser.email && newUser.email.toLowerCase().includes(query)) ||
      (newUser.username && newUser.username.toLowerCase().includes(query)) ||
      (newUser.full_name && newUser.full_name.toLowerCase().includes(query));
    
    if (matches) {
      // Agregar el nuevo usuario a allSearchResults
      allSearchResults.value.unshift(newUser);
      totalUsers.value = allSearchResults.value.length;
      
      // Actualizar la vista
      updateDisplayedUsers();
    }
  } else {
    // Si no hay búsqueda activa, comportamiento normal
    fetchUsers();
  }
};

// Edit user handler
const editUser = (user) => {
  closeActionsMenu();
  userToEdit.value = user.id;
  isEditUserModalOpen.value = true;
};

// Añadir funciones para manejar la edición
const closeEditUserModal = () => {
  isEditUserModalOpen.value = false;
  userToEdit.value = null;
};

const handleUserUpdated = (updatedUser) => {
  // Si hay una búsqueda activa, actualizar también allSearchResults
  if (searchQuery.value.trim()) {
    // Actualizar el usuario en los resultados de búsqueda
    const searchIndex = allSearchResults.value.findIndex(u => u.id === updatedUser.id);
    if (searchIndex !== -1) {
      allSearchResults.value[searchIndex] = updatedUser;
      
      // Actualizar también los usuarios mostrados en pantalla
      updateDisplayedUsers();
    }
  } else {
    // Actualizar el usuario en la lista si existe (comportamiento actual)
    const index = users.value.findIndex(u => u.id === updatedUser.id);
    if (index !== -1) {
      users.value[index] = updatedUser;
    }
  }
};

// Show confirmation modal for user deletion
const confirmDeleteUser = (user) => {
  closeActionsMenu();
  userToDelete.value = user;
  
  // Create different messages for admin users vs regular users
  if (user.is_admin) {
    deleteModalMessage.value = `Estás a punto de eliminar un usuario administrador. Esta acción no se puede deshacer.`;
  } else {
    deleteModalMessage.value = `Estás a punto de eliminar el usuario ${user.username}. Esta acción no se puede deshacer.`;
  }
  
  isDeleteModalOpen.value = true;
};

// Cancel user deletion
const cancelDelete = () => {
  isDeleteModalOpen.value = false;
  userToDelete.value = null;
  // Asegurarse de que se resetea el menú de acciones
  activeActionsMenu.value = null;
  
  // Dar un pequeño tiempo antes de permitir abrir menús de nuevo
  setTimeout(() => {
    // Esto ayuda a evitar problemas con los clicks residuales
    const activeButtons = document.querySelectorAll('.action-button[data-active="true"]');
    activeButtons.forEach(button => {
      button.setAttribute('data-active', 'false');
    });
  }, 100);
};

// Delete user
const deleteUser = async () => {
  if (!userToDelete.value) return;
  
  try {
    await axios.delete(`/users/${userToDelete.value.id}`);
    
    // Si hay una búsqueda activa, actualizar allSearchResults
    if (searchQuery.value.trim()) {
      // Eliminar usuario de los resultados de búsqueda
      allSearchResults.value = allSearchResults.value.filter(u => u.id !== userToDelete.value.id);
      totalUsers.value = allSearchResults.value.length;
      
      // Verificar si debemos cambiar de página después de eliminar
      const maxPossiblePage = Math.max(1, Math.ceil(allSearchResults.value.length / pageSize.value));
      if (currentPage.value > maxPossiblePage) {
        currentPage.value = maxPossiblePage;
      }
      
      // Actualizar los usuarios mostrados
      updateDisplayedUsers();
    } else {
      // Verificar si debemos cambiar de página después de eliminar (comportamiento actual)
      if (users.value.length === 1 && currentPage.value > 1) {
        currentPage.value--; // Retroceder si era el último elemento de la página
      }
      
      // Refrescamos la lista completa para ver el cambio en la paginación
      fetchUsers();
    }
    
    notifySuccess('Usuario eliminado', 
    `Se ha eliminado el usuario ${userToDelete.value.username} con éxito.`);
  } catch (error) {
    console.error('Error deleting user:', error);
    handleApiError(error);
  } finally {
    isDeleteModalOpen.value = false;
    userToDelete.value = null;
  }
};

// Error handling
const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 401:
        router.push('/');
        break;
      case 400:
        notifyError("Error de validación", "Los datos proporcionados no son válidos.");
        break;
        
      case 403:
        if (data.detail && data.detail.includes("Admins")) {
          notifyError("Acción denegada", "Los administradores no pueden eliminarse a sí mismos.");
        } else if (data.detail && data.detail.includes("credentials")) {
          notifyInfo("Sesión expirada", "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else if (data.detail && data.detail.includes("privileges")) {
          router.push('/');
        } else {
          notifyError("Acceso denegado", "No tienes permiso para realizar esta acción.");
        }
        break;
        
      case 404:
        notifyError("Usuario no encontrado", "El usuario no existe en el sistema.");
        break;
        
      default:
        notifyError("Error en el servidor", "No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.");
        break;
    }
  } else if (error.request) {
    notifyError("Error de conexión", "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", "Ha ocurrido un problema.");
  }
};

// Observar cambios en el tamaño de página para reiniciar búsquedas
watch(pageSize, () => {
  if (searchQuery.value.trim()) {
    // Si hay búsqueda activa, actualizar la visualización
    updateDisplayedUsers();
  } else {
    fetchUsers();
  }
});

// Fetch users when component is mounted
onMounted(() => {
  // Restaurar preferencia de tamaño de página si existe
  const savedPageSize = localStorage.getItem('adminPageSize');
  if (savedPageSize && pageSizeOptions.includes(parseInt(savedPageSize))) {
    pageSize.value = parseInt(savedPageSize);
  }
  
  fetchUsers();
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>

<style scoped>
.admin-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 90px; 
  padding-bottom: 40px;
}

/* Estilos existentes... */

/* Estilos para el buscador - Fondo transparente */
.search-container {
  padding: 15px;
  /* Eliminado: border-bottom: 1px solid #eee; */
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  max-width: 600px;
  margin: 0 auto;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #888;
  cursor: pointer;
  z-index: 1; /* Asegurar que el icono esté por encima del input */
}

.search-input {
  width: 100%;
  padding: 10px 36px 10px 40px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  background-color: white; /* Aseguramos fondo blanco */
  color: #333; /* Color de texto oscuro para mejor contraste */
}

.search-input:focus {
  outline: none;
  border-color: #aaa;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.05);
  background-color: white; /* Mantener fondo blanco al enfocar */
}

.clear-search-button {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 5px;
  border-radius: 5%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1; /* Asegurar que el botón esté por encima del input */
}

/* Estilos para resultados de búsqueda */
.search-highlight {
  background-color: rgba(255, 235, 59, 0.3);
  padding: 0 2px;
  border-radius: 2px;
}

/* Ajustes responsivos para la búsqueda */
@media (max-width: 768px) {
  .search-container {
    padding: 10px;
  }
  
  .search-input {
    font-size: 0.9rem;
    padding: 8px 32px 8px 36px;
  }
  
  .search-icon {
    left: 10px;
  }
}

/* Estilos para la paginación */
.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0; /* Eliminado el espacio entre tabla y paginación */
  padding: 10px 15px;
  background-color: #f9f9f9;
  border-radius: 0 0 8px 8px;
  border-top: 1px solid #eee;
  width: 100%; /* Asegura que ocupa todo el ancho disponible */
  box-sizing: border-box; /* Incluye padding en el cálculo del ancho */
  table-layout: fixed; /* Mantiene un ancho consistente */
  position: sticky; /* Hace que la paginación se mantenga visible */
  bottom: 0; /* Pegada al fondo */
}

.pagination-actions {
  display: flex;
  align-items: center;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #333; /* Color más oscuro para el texto */
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  font-size: 0.9rem;
  cursor: pointer;
  color: #333; /* Color más oscuro para el texto en el select */
}

.page-size-select option {
  color: #333; /* Color más oscuro para las opciones */
  background-color: white;
}

.page-size-select:focus {
  outline: none;
  border-color: #aaa;
}

.pagination-button {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 12px;
  margin: 0 5px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.pagination-button:hover:not(:disabled) {
  background-color: #f0f0f0;
}

.pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Iconos de paginación más oscuros */
.pagination-icon {
  color: #333; /* Color más oscuro para las flechas */
}

.pagination-info {
  font-size: 0.9rem;
  color: #666;
  margin: 0 12px;
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

/* Estilo específico para el botón de añadir usuario */
.add-user-button {
  width: auto !important;
  margin-top: 0 !important;
  padding: 10px 20px !important;
}

.button-icon {
  margin-right: 8px;
}

/* Separar la sección de búsqueda del contenido principal */
.admin-content {
  display: flex;
  flex-direction: column;
  gap: 15px; /* Espacio entre la búsqueda y la tabla */
  background-color: transparent; /* Fondo transparente para el contenedor principal */
}

/* Contenedor de búsqueda con fondo transparente */
.search-container {
  padding: 15px;
  background-color: transparent;
  z-index: 1;
}

/* Contenedor de tabla con fondo blanco */
.table-wrapper {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  min-width: 100%;
  overflow-x: auto;
  display: table;
  width: 100%;
}

.admin-content {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: relative;
  overflow-x: auto; /* Añadir desplazamiento horizontal al contenedor principal */
  margin-top: 15px;
}

.users-table-container {
  width: 100%;
  min-width: 100%; /* Asegura que ocupe al menos el 100% del contenedor */
  display: flex;
  flex-direction: column;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  margin-bottom: 0; /* Elimina el margen inferior de la tabla */
  min-width: max-content; /* Mantiene el ancho mínimo para que quepa todo el contenido */
}

/* Estilo para un contenedor que envuelve la tabla y la paginación */
.table-wrapper {
  min-width: 100%;
  overflow-x: auto; /* Permite desplazamiento horizontal si necesario */
  display: table; /* Comportamiento de tabla para mantener alineación */
  width: 100%;
}

/* Estilos para la paginación */
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 0;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 0 0 8px 8px;
  border-top: 1px solid #eee;
  box-sizing: border-box;
  width: 100%;
  table-layout: fixed; /* Mantiene un ancho consistente */
  position: sticky; /* Hace que la paginación se mantenga visible */
  bottom: 0; /* Pegada al fondo */
}

.users-table th,
.users-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #ddd;
}

/* Clases específicas para centrar columnas */
.center-column {
  text-align: center !important;
  width: 100px;
}

.actions-column {
  text-align: center !important;
  width: 80px;
}

.users-table thead th {
  background-color: #f4f4f4;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.users-table tbody tr:last-child td {
  border-bottom: none; /* Elimina el borde de la última fila */
}

.users-table tbody tr:hover {
  background-color: #f9f9f9;
}

.inactive-user {
  opacity: 0.7;
}

.actions-menu {
  position: relative;
  display: flex;
  justify-content: center;
}

.action-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  color: #555;
}

.action-button:hover {
  background-color: #f0f0f0;
}

.admin-badge {
  color: gold;
  background-color: rgba(0, 0, 0, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
}

.status-badge.verified,
.status-badge.active {
  background-color: #e6f7e6;
  color: #2d862d;
}

.status-badge.inactive {
  background-color: #f7e6e6;
  color: #b30000;
}

.status-badge.unverified {
  background-color: #fff3e0;
  color: #e65100;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #666;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #666;
  gap: 10px; /* Espacio entre los elementos */
}

/* Ajustar el ancho de las columnas para que quepan todas */
@media (max-width: 992px) {
  .center-column {
    width: 90px;
  }
  
  .users-table th,
  .users-table td {
    padding: 10px 8px;
    font-size: 0.9em;
  }
  
  .status-badge {
    font-size: 0.75em;
    padding: 2px 6px;
  }
}

@media (max-width: 768px) {
  .admin-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .add-user-button {
    width: 100% !important;
  }
  
  .users-table th,
  .users-table td {
    padding: 8px;
    font-size: 0.9em;
  }
  
  .admin-view {
    padding: 10px;
    min-height: calc(100vh - 140px);
  }
  
  .center-column {
    width: 65px;
  }
  
  .status-badge {
    font-size: 0.7em;
    padding: 2px 4px;
  }
  
  /* Ocultar el texto y mostrar solo el icono en móviles */
  .status-badge .status-text {
    display: none;
  }
  
  /* Ajustes para la paginación en móviles */
  .pagination-info {
    font-size: 0.8rem;
    margin: 0 5px;
  }
  
  .pagination-button {
    padding: 4px 8px;
    margin: 0 3px;
  }
  
  .pagination-controls {
    width: 100%; /* Reiterar ancho completo en pantallas pequeñas */
    min-width: max-content; /* Mantener ancho mínimo igual que la tabla */
    overflow-x: auto; /* Permitir desplazamiento si es necesario */
  }
  
  /* Asegurar que la paginación sea al menos tan ancha como la tabla */
  .users-table-container > * {
    min-width: max-content;
  }
  
  .pagination-controls,
  .users-table {
    min-width: max-content; /* Asegura que ambos tengan al menos el mismo ancho mínimo */
    width: 100%;
  }
}

/* Estilos específicos para el mensaje de búsqueda sin resultados */
.search-term {
  font-weight: bold;
  font-style: italic;
}
</style>
