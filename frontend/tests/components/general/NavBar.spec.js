import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import NavBar from '@/components/general/NavBar.vue'
import { useAuthStore } from '@/stores/authStore'
import { globalOptions } from '../../../tests/helpers/test-utils'

// Mock del router.
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock del store.
vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn()
}))

// Mock de componentes.
vi.mock('@/components/users/SignupModal.vue', () => ({
  default: {
    name: 'SignupModal',
    template: '<div class="mock-signup-modal"></div>'
  }
}))

vi.mock('@/components/users/LoginModal.vue', () => ({
  default: {
    name: 'LoginModal',
    template: '<div class="mock-login-modal"></div>'
  }
}))

vi.mock('@/components/users/EnterEmailModal.vue', () => ({
  default: {
    name: 'EnterEmailModal',
    template: '<div class="mock-enter-email-modal"></div>'
  }
}))

vi.mock('@/components/general/UserDropdown.vue', () => ({
  default: {
    name: 'UserDropdown',
    template: '<div class="mock-user-dropdown"></div>',
    emits: ['close']
  }
}))

// Mock para FontAwesome.
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

describe('NavBar.vue', () => {
  // Test 1: Visualización para usuarios no autenticados.
  it('muestra enlaces de inicio de sesión y registro cuando no está autenticado', () => {
    // Configurar el store para simular usuario no autenticado.
    useAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: vi.fn()
    })
    
    const wrapper = mount(NavBar, {
      global: globalOptions
    })
    
    // Verificar que se muestran los enlaces de autenticación.
    expect(wrapper.text()).toContain('Iniciar sesión')
    expect(wrapper.text()).toContain('Registrarse')
    expect(wrapper.find('#register-button').exists()).toBe(true)
  })
  
  // Test 2: Visualización para usuarios autenticados.
  it('muestra el nombre de usuario y opciones cuando está autenticado', () => {
    // Configurar el store para simular usuario autenticado.
    useAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { 
        username: 'testuser',
        is_admin: false
      },
      logout: vi.fn()
    })
    
    const wrapper = mount(NavBar, {
      global: globalOptions
    })
    
    // Verificar que se muestra el nombre de usuario.
    expect(wrapper.find('.username-text').text()).toBe('testuser')
    expect(wrapper.find('#register-button').exists()).toBe(false)
  })
  
  // Test 3: Indicador de administrador.
  it('muestra indicador de administrador para usuarios admin', () => {
    // Configurar el store para simular usuario administrador.
    useAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { 
        username: 'adminuser',
        is_admin: true
      },
      logout: vi.fn()
    })
    
    const wrapper = mount(NavBar, {
      global: globalOptions
    })
    
    // Verificar que se muestra el indicador de admin.
    expect(wrapper.find('.admin-badge').exists()).toBe(true)
  })
  
  // Test 4: Apertura del modal de login.
  it('abre el modal de login al hacer clic en iniciar sesión', async () => {
    useAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: vi.fn()
    })
    
    const wrapper = mount(NavBar, {
      global: globalOptions
    })
    
    // Hacer clic en iniciar sesión.
    await wrapper.find('.navbar-username').trigger('click')
    
    // Verificar que se abre el modal (isLoginModalOpen se convierte en true).
    expect(wrapper.vm.isLoginModalOpen).toBe(true)
  })
  
  // Test 5: Funcionalidad de logout.
  it('realiza logout cuando el usuario autenticado llama a handleLogout', async () => {
    const logoutMock = vi.fn()
    
    useAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { 
        username: 'testuser',
        is_admin: false 
      },
      logout: logoutMock
    })
    
    const wrapper = mount(NavBar, {
      global: globalOptions
    })
    
    await wrapper.vm.handleLogout()
    
    // Verificar que se llamó al método logout del store.
    expect(logoutMock).toHaveBeenCalled()
  })
})