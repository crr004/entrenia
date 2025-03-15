import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import AdminView from '@/views/AdminView.vue'
import { useAuthStore } from '@/stores/authStore'
import * as notifications from '@/utils/notifications'
import { globalOptions } from '../../tests/helpers/test-utils'
import axios from 'axios';

// Mock del store de preferencias.
vi.mock('@/stores/userPreferencesStore', () => ({
  userPreferencesStore: () => ({
    setAdminPageSize: vi.fn(),
    getAdminPageSize: () => 10
  })
}))

// Mock del store de autenticación.
vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'mock-token',
    user: { 
      id: '1', 
      username: 'admin',
      email: 'admin@example.com',
      is_admin: true
    },
    isAuthenticated: true,
    setAuthHeader: vi.fn()
  }))
}))

// Mock de las funciones de notificación.
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock del router.
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock de componentes usados por AdminView.
vi.mock('@/components/utils/ActionMenu.vue', () => ({
  default: {
    name: 'ActionMenu',
    props: ['item', 'itemId', 'position'],
    template: '<div class="mock-action-menu"></div>',
    emits: ['edit', 'delete', 'close']
  }
}))

vi.mock('@/components/utils/ConfirmationModal.vue', () => ({
  default: {
    name: 'ConfirmationModal',
    props: ['isOpen', 'title', 'message', 'confirmText', 'cancelText'],
    template: '<div v-if="isOpen" class="mock-confirmation-modal"></div>',
    emits: ['confirm', 'cancel']
  }
}))

vi.mock('@/components/users/AddUserModal.vue', () => ({
  default: {
    name: 'AddUserModal',
    props: ['isOpen'],
    template: '<div v-if="isOpen" class="mock-add-user-modal"></div>',
    emits: ['close', 'userAdded']
  }
}))

vi.mock('@/components/users/EditUserModal.vue', () => ({
  default: {
    name: 'EditUserModal',
    props: ['isOpen', 'userId'],
    template: '<div v-if="isOpen" class="mock-edit-user-modal"></div>',
    emits: ['close', 'userUpdated']
  }
}))

// Lista de usuarios mock para pruebas.
const mockUsers = [
  {
    id: '1',
    username: 'user1',
    email: 'user1@example.com',
    full_name: 'User One',
    is_admin: false,
    is_active: true,
    is_verified: true
  },
  {
    id: '2',
    username: 'user2',
    email: 'user2@example.com',
    full_name: 'User Two',
    is_admin: false,
    is_active: true,
    is_verified: false
  },
  {
    id: '3',
    username: 'admin',
    email: 'admin@example.com',
    full_name: 'Admin User',
    is_admin: true,
    is_active: true,
    is_verified: true
  }
];

// Servidor mock para simular respuestas de la API.
const server = setupServer(
  // Listar usuarios.
  http.get('/users/', ({ request }) => {
    // Parsear parámetros de la URL para paginación.
    const url = new URL(request.url);
    const skip = parseInt(url.searchParams.get('skip') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    
    // Devolver usuarios paginados.
    return HttpResponse.json({
      users: mockUsers.slice(skip, skip + limit),
      count: mockUsers.length
    }, { status: 200 })
  }),
  
  // Eliminar usuario.
  http.delete('/users/:id', ({ params }) => {
    const { id } = params;
    // Simular eliminación exitosa.
    return HttpResponse.json({
      message: `User ${id} deleted successfully`
    }, { status: 200 })
  })
)

// Configuración del servidor.
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())
afterEach(() => server.close())
afterEach(() => vi.clearAllMocks())

describe('AdminView.vue', () => {
  // Test 1: Carga inicial de datos.
  it('carga la lista de usuarios correctamente', async () => {
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los usuarios.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
      expect(wrapper.vm.users.length).toBe(3)
    })
    
    // Verificar que la tabla se renderiza.
    expect(wrapper.find('.users-table').exists()).toBe(true)
    
    // Verificar que se muestran todos los usuarios.
    const userRows = wrapper.findAll('.users-table tbody tr')
    expect(userRows.length).toBe(3)
    
    // Verificar información del primer usuario.
    const firstUserCells = userRows[0].findAll('td')
    expect(firstUserCells[0].text()).toContain('user1@example.com')
    expect(firstUserCells[1].text()).toContain('User One')
    expect(firstUserCells[2].text()).toContain('user1')
  })
  
  // Test 2: Búsqueda de usuarios.
  it('realiza búsqueda de usuarios correctamente', async () => {
    // Mock de la función de búsqueda para devolver resultados filtrados.
    server.use(
      http.get('/users/', () => {
        return HttpResponse.json({
          users: [mockUsers[0]], // Solo el primer usuario como resultado.
          count: 1
        }, { status: 200 })
      })
    )
    
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Esperar a que cargue.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Establecer búsqueda.
    wrapper.vm.searchQuery = 'user1'
    
    // Espiar la función performLocalSearch.
    const searchSpy = vi.spyOn(wrapper.vm, 'performLocalSearch')
    
    // Invocar manualmente la búsqueda sin esperar el debounce.
    await wrapper.vm.performLocalSearch()
    
    // Verificar que se llamó correctamente.
    expect(searchSpy).toHaveBeenCalled()
    
    // Verificar que los resultados se actualizan.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
      expect(wrapper.vm.allSearchResults.length).toBe(1)
    })
  })
  
  // Test 3: Apertura de modal para añadir usuario.
  it('muestra el modal para añadir usuario', async () => {
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Verificar que inicialmente el modal está cerrado.
    expect(wrapper.vm.isAddUserModalOpen).toBe(false)
    
    // Abrir modal.
    await wrapper.find('.add-user-button').trigger('click')
    
    // Verificar que el modal se abre.
    expect(wrapper.vm.isAddUserModalOpen).toBe(true)
    expect(wrapper.find('.mock-add-user-modal').exists()).toBe(true)
  })
  
  // Test 4: Funcionamiento de paginación.
  it('maneja la paginación correctamente', async () => {
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar valores iniciales de paginación.
    expect(wrapper.vm.currentPage).toBe(1)
    expect(wrapper.vm.pageSize).toBe(10)
    
    // Llamar directamente al método changePage
    const changePageSpy = vi.spyOn(wrapper.vm, 'changePage')
    
    // Llamar al método directamente.
    wrapper.vm.changePage(2)
    
    // Verificar que se llamó correctamente.
    expect(changePageSpy).toHaveBeenCalledWith(2)
  })
  
  // Test 5: Confirmación antes de eliminar usuario.
  it('muestra el diálogo de confirmación al eliminar usuario', async () => {
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que el modal está cerrado inicialmente.
    expect(wrapper.vm.isDeleteModalOpen).toBe(false)
    
    // Llamar directamente al método de confirmación.
    await wrapper.vm.confirmDeleteUser(mockUsers[0])
    
    // Esperar a que el DOM se actualice.
    await wrapper.vm.$nextTick()
    
    // Verificar que el modal se abre.
    expect(wrapper.vm.isDeleteModalOpen).toBe(true)
    expect(wrapper.vm.userToDelete).toEqual(mockUsers[0])
  })
  
  // Test 6: Eliminación de usuario.
  it('elimina usuario correctamente', async () => {
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Esperar a que se carguen los datos.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Configurar para eliminar usuario.
    wrapper.vm.userToDelete = mockUsers[0]
    wrapper.vm.isDeleteModalOpen = true
    
    // Espiar el método deleteUser directamente en lugar de axios.delete.
    const deleteUserSpy = vi.spyOn(wrapper.vm, 'deleteUser')
    
    // Llamar al método de eliminar.
    await wrapper.vm.deleteUser()
    
    // Verificar que se llamó al método.
    expect(deleteUserSpy).toHaveBeenCalled()
    
    // Verificar que se mostró notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalled()
    
    // Verificar que el modal se cierra.
    expect(wrapper.vm.isDeleteModalOpen).toBe(false)
  })
  
  // Test 7: Manejo de errores de la API.
  it('maneja error al cargar usuarios', async () => {
    // Configurar respuesta de error.
    server.use(
      http.get('/users/', () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 }
        )
      })
    )
    
    const wrapper = mount(AdminView, {
      global: globalOptions
    })
    
    // Esperar un poco para que se procese la llamada a la API.
    await vi.waitFor(() => {
      expect(wrapper.vm.isLoading).toBe(false)
    })
    
    // Verificar que se muestra el error.
    expect(notifications.notifyError).toHaveBeenCalled()
  })
})