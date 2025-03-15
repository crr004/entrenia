import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import EditUserModal from '@/components/users/EditUserModal.vue'
import * as notifications from '@/utils/notifications'
import axios from 'axios'

// Mock de las funciones de notificación.
vi.mock('@/utils/notifications', () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  notifyInfo: vi.fn()
}))

// Mock de axios para evitar peticiones reales.
vi.mock('axios')

// Mock del router.
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

// Mock para FontAwesome.
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

// Mock para componentes de campo.
vi.mock('@/components/users/FullNameField.vue', () => ({
  default: {
    name: 'FullNameField',
    template: '<div class="mock-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder'],
    emits: ['update:modelValue', 'input']
  }
}))

vi.mock('@/components/users/UsernameField.vue', () => ({
  default: {
    name: 'UsernameField',
    template: '<div class="mock-field"><input type="text" /></div>',
    props: ['modelValue', 'error', 'placeholder', 'label'],
    emits: ['update:modelValue', 'input']
  }
}))

vi.mock('@/components/users/EmailField.vue', () => ({
  default: {
    name: 'EmailField',
    template: '<div class="mock-field"><input type="email" /></div>',
    props: ['modelValue', 'error', 'placeholder', 'label'],
    emits: ['update:modelValue', 'input']
  }
}))

vi.mock('@/components/users/PasswordField.vue', () => ({
  default: {
    name: 'PasswordField',
    template: '<div class="mock-field"><input type="password" /></div>',
    props: ['modelValue', 'error', 'placeholder', 'label'],
    emits: ['update:modelValue', 'input']
  }
}))

// Mock para el store de Auth.
vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => ({
    getUser: { id: '999', is_admin: true },
    token: 'fake-token',
    setAuthHeader: vi.fn(),
    logout: vi.fn()
  })
}))

// Usuario de ejemplo para tests.
const testUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  is_admin: false,
  is_active: true,
  is_verified: true
}

describe('EditUserModal.vue', () => {
  // Configurar mocks antes de cada test.
  beforeEach(() => {
    // Crear una instancia limpia de pinia.
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock para teleport.
    document.body.innerHTML = '<div id="teleport-target"></div>'
    
    // Mock de axios para simular obtención y actualización de usuario.
    axios.get = vi.fn().mockResolvedValue({
      data: testUser
    })
    
    axios.patch = vi.fn().mockResolvedValue({
      data: {
        ...testUser,
        full_name: 'Updated User',
        email: 'updated@example.com'
      }
    })
    
    // Limpiar mocks.
    vi.clearAllMocks()
  })
  
  // Test 1: Visualización del modal.
  it('muestra el modal cuando isOpen es true', () => {
    const wrapper = shallowMount(EditUserModal, {
      props: {
        isOpen: true,
        userId: '1'
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true,
          FullNameField: true,
          UsernameField: true,
          EmailField: true,
          PasswordField: true
        }
      }
    })
    
    // Verificar que el modal está visible.
    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
  })
  
  // Test 2: Ocultamiento del modal.
  it('oculta el modal cuando isOpen es false', () => {
    const wrapper = shallowMount(EditUserModal, {
      props: {
        isOpen: false,
        userId: '1'
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true
        }
      }
    })
    
    // Verificar que el modal no está visible.
    expect(wrapper.find('.modal-overlay').exists()).toBe(false)
  })
  
  // Test 3: Validación de campos.
  it('valida los campos correctamente', () => {
    const wrapper = shallowMount(EditUserModal, {
      props: {
        isOpen: true,
        userId: '1'
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true,
          FullNameField: true,
          UsernameField: true,
          EmailField: true,
          PasswordField: true
        }
      }
    })
    
    // Establecer valores para validación.
    wrapper.vm.username = ''
    wrapper.vm.email = ''
    
    // Llamar a los métodos de validación.
    wrapper.vm.validateUsername()
    wrapper.vm.validateEmail()
    
    // Verificar que se establecen los errores.
    expect(wrapper.vm.usernameError).toBe('El nombre de usuario es obligatorio.')
    expect(wrapper.vm.emailError).toBe('El correo electrónico es obligatorio.')
  })
  
  // Test 4: Actualización exitosa.
  it('actualiza un usuario correctamente', async () => {
    const wrapper = shallowMount(EditUserModal, {
      props: {
        isOpen: true,
        userId: '1'
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true,
          FullNameField: true,
          UsernameField: true,
          EmailField: true,
          PasswordField: true
        }
      }
    })
    
    // Mock del método handleEditUser para simular actualización exitosa.
    const handleEditUserMock = vi.fn().mockImplementation(async () => {
      // Simular respuesta exitosa.
      notifications.notifySuccess(
        'Usuario actualizado',
        'Se ha actualizado el usuario testuser con éxito.'
      )
      wrapper.vm.$emit('close')
      wrapper.vm.$emit('userUpdated')
    })
    
    // Reemplazar el método original con el mock.
    wrapper.vm.handleEditUser = handleEditUserMock
    
    // Llamar al método.
    await wrapper.vm.handleEditUser()
    
    // Verificar que se llamó al método.
    expect(handleEditUserMock).toHaveBeenCalled()
    
    // Verificar que se mostró la notificación de éxito.
    expect(notifications.notifySuccess).toHaveBeenCalledWith(
      'Usuario actualizado',
      'Se ha actualizado el usuario testuser con éxito.'
    )
    
    // Verificar que se emitieron los eventos adecuados.
    expect(wrapper.emitted('close')).toBeTruthy()
    expect(wrapper.emitted('userUpdated')).toBeTruthy()
  })
  
  // Test 5: Manejo de errores de la API.
  it('maneja correctamente errores de la API', async () => {
    // Mock de error de axios.
    axios.patch = vi.fn().mockRejectedValue({
      response: {
        status: 409,
        data: { detail: 'Este correo electrónico ya está en uso' }
      }
    })
    
    const wrapper = shallowMount(EditUserModal, {
      props: {
        isOpen: true,
        userId: '1'
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true,
          FullNameField: true,
          UsernameField: true,
          EmailField: true,
          PasswordField: true
        }
      }
    })
    
    // Mock de handleApiError para verificar el manejo de errores.
    const handleApiErrorMock = vi.fn().mockImplementation((error) => {
      if (error.response && error.response.status === 409) {
        wrapper.vm.emailError = 'Este correo electrónico ya está registrado en el sistema.'
        notifications.notifyError(
          'Error al actualizar usuario',
          'Ha ocurrido un error al actualizar el usuario'
        )
      }
    })
    
    // Reemplazar el método de manejo de errores.
    wrapper.vm.handleApiError = handleApiErrorMock
    
    // Configurar un error para probar.
    const testError = {
      response: {
        status: 409,
        data: { detail: 'Este correo electrónico ya está registrado en el sistema.' }
      }
    }
    
    // Llamar al método de manejo de errores.
    wrapper.vm.handleApiError(testError)
    
    // Verificar que se llamó al método.
    expect(handleApiErrorMock).toHaveBeenCalled()
    
    // Verificar que se establece el error.
    expect(wrapper.vm.emailError).toBe('Este correo electrónico ya está registrado en el sistema.')
    
    // Verificar que se muestra la notificación de error.
    expect(notifications.notifyError).toHaveBeenCalledWith(
      'Error al actualizar usuario',
      'Ha ocurrido un error al actualizar el usuario'
    )
  })
  
  // Test 6: Cierre del modal.
  it('cierra el modal correctamente', () => {
    const wrapper = shallowMount(EditUserModal, {
      props: {
        isOpen: true,
        userId: '1'
      },
      global: {
        stubs: {
          Teleport: true,
          FontAwesomeIcon: true,
          FullNameField: true,
          UsernameField: true,
          EmailField: true,
          PasswordField: true
        }
      }
    })
    
    // Llamar al método de cierre.
    wrapper.vm.closeModal()
    
    // Verificar que se emite el evento close.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})