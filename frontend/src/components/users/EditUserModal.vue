<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal edit-user-modal">
        <h1>Editar usuario</h1>
        <button class="close-modal-button" @click="closeModal">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <div v-if="isLoadingUser" class="loading-container">
          <font-awesome-icon :icon="['fas', 'circle-notch']" spin size="2x" />
          <p>Cargando datos del usuario...</p>
        </div>
        <form v-else class="signup-body" @submit.prevent="handleEditUser">
          <div class="auth-modal-form">
            <FullNameField
              placeholder="Nombre completo"
              v-model="fullName"
              :error="fullNameError"
              @input="validateFullName"
              ref="fullNameFieldRef"
            />
            <UsernameField
              placeholder="Nombre de usuario"
              label="Nombre de usuario"
              v-model="username"
              :error="usernameError"
              @input="validateUsername"
            />
            <EmailField
              placeholder="Correo electrónico"
              label="Correo electrónico"
              v-model="email"
              :error="emailError"
              @input="validateEmail"
            />
            <PasswordField 
              placeholder="Contraseña"
              label="Contraseña"
              v-model="password"
              :error="passwordError"
              @input="validatePassword"
            />
            <div class="admin-options">
              <div class="admin-option-item">
                <input type="checkbox" id="is_active_edit" v-model="isActive" />
                <label for="is_active_edit">Cuenta activa</label>
              </div>
              <div class="admin-option-item">
                <input type="checkbox" id="is_verified_edit" v-model="isVerified" />
                <label for="is_verified_edit">Cuenta verificada</label>
              </div>
              <div class="admin-option-item">
                <input type="checkbox" id="is_admin_edit" v-model="isAdmin" />
                <label for="is_admin_edit">Administrador</label>
              </div>
            </div>
            <button type="submit" class="app-button" :disabled="isSaving || !hasValidChanges">
              <span v-if="!isSaving">Guardar cambios</span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'spinner']" spin />
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifyError, notifySuccess, notifyInfo } from '@/utils/notifications';
import { userValidationRegex } from '@/utils/validations.js';
import { useAuthStore } from '@/stores/authStore';
import FullNameField from '@/components/users/FullNameField.vue';
import UsernameField from '@/components/users/UsernameField.vue';
import EmailField from '@/components/users/EmailField.vue';
import PasswordField from '@/components/users/PasswordField.vue';


const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  userId: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['close', 'userUpdated']);

const router = useRouter();
const fullName = ref('');
const username = ref('');
const email = ref('');
const password = ref('');
const isAdmin = ref(false);
const isActive = ref(true);
const isVerified = ref(true);
const fullNameFieldRef = ref(null);

const fullNameError = ref('');
const usernameError = ref('');
const emailError = ref('');
const passwordError = ref('');

const isLoadingUser = ref(false);
const isSaving = ref(false);
const authStore = useAuthStore();
const originalUserData = ref(null);
const isFirstOpen = ref(true);
let isModalInitialized = false;

const hasValidChanges = computed(() => {
  if (fullNameError.value || usernameError.value || emailError.value || passwordError.value) {
    return false;
  }
  
  // Si no hay datos originales, no se puede comparar.
  if (!originalUserData.value) return false;
  
  // Verificar si hay algún cambio en los campos.
  const hasFullNameChanged = fullName.value !== (originalUserData.value.full_name || '');
  const hasUsernameChanged = username.value !== originalUserData.value.username;
  const hasEmailChanged = email.value !== originalUserData.value.email;
  const hasPasswordChanged = password.value !== ''; // Si hay algo en password, es un cambio (ya que esta no se muestra en el formulario).
  const hasAdminChanged = isAdmin.value !== originalUserData.value.is_admin;
  const hasActiveChanged = isActive.value !== originalUserData.value.is_active;
  const hasVerifiedChanged = isVerified.value !== originalUserData.value.is_verified;
  
  return hasFullNameChanged || hasUsernameChanged || hasEmailChanged || 
         hasPasswordChanged || hasAdminChanged || hasActiveChanged || hasVerifiedChanged;
});

const isEditingSelf = () => {
  const currentUser = authStore.getUser;
  return currentUser && currentUser.id === props.userId;
};

watch(() => props.isOpen, async (newValue) => {
  if (newValue && props.userId && !isLoadingUser.value) {
    if (isEditingSelf()) {
      notifyInfo("Modificación de cuenta propia",
      "Los administradores deben modificar sus propios datos desde la sección 'Mi cuenta'.");
      emit('close');
      return;
    }
    
    await loadUserData();
    
    // Foco en el campo de nombre completo al abrir el modal.
    await nextTick();
    const inputElement = fullNameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
});

const loadUserData = async () => {
  if (!props.userId) return;
  
  isLoadingUser.value = true;
  resetForm();
  
  try {
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    authStore.setAuthHeader();

    const response = await axios.get(`/users/${props.userId}`);
    const userData = response.data;
    
    // Almacenar los datos originales para comparar cambios.
    originalUserData.value = { ...userData };
    
    // Llenar el formulario con los datos originales.
    fullName.value = userData.full_name || '';
    username.value = userData.username || '';
    email.value = userData.email || '';
    isAdmin.value = !!userData.is_admin;
    isActive.value = !!userData.is_active;
    isVerified.value = !!userData.is_verified;
    
    // La contraseña siempre vacía.
    password.value = '';
    
  } catch (error) {
    handleApiError(error);
    emit('close');
  } finally {
    isLoadingUser.value = false;
  }
};

const validateFullName = () => {
  // Como el nombre completo es opcional, es válido si está vacío.
  if (!fullName.value.trim()) {
    fullNameError.value = '';
    return true;
  }
  
  const nameRegex = userValidationRegex.fullname;

  if (!nameRegex.test(fullName.value)) {
    fullNameError.value = 'El nombre completo contiene caracteres inválidos.';
    return false;
  } else if(fullName.value.length > 170) {
    fullNameError.value = 'El nombre completo no puede tener más de 170 caracteres.';
    return false;
  } else {
    fullNameError.value = '';
    return true;
  }
};

const validateUsername = () => {
  const usernameRegex = userValidationRegex.username;
  
  if (!username.value) {
    usernameError.value = 'El nombre de usuario es obligatorio.';
    return false;
  } else if (!usernameRegex.test(username.value)) {
    usernameError.value = 'Solo letras minúsculas, números y guiones bajos. Debe contener al menos 3 letras.';
    return false;
  } else if (username.value.length > 20) {
    usernameError.value = 'El nombre de usuario no puede tener más de 20 caracteres.';
    return false;
  } else {
    usernameError.value = '';
    return true;
  }
};

const validateEmail = () => {
  const emailRegex = userValidationRegex.email;
  
  if (!email.value) {
    emailError.value = 'El correo electrónico es obligatorio.';
    return false;
  } else if (!emailRegex.test(email.value)) {
    emailError.value = 'Introduce un correo electrónico válido.';
    return false;
  } else {
    emailError.value = '';
    return true;
  }
};

const validatePassword = () => {
  // La contraseña es opcional al editar.
  if (!password.value) {
    passwordError.value = '';
    return true;
  }
  
  if (password.value.length < 9) {
    passwordError.value = 'La contraseña debe tener al menos 9 caracteres.';
    return false;
  } else if(password.value.length > 50) {
    passwordError.value = 'La contraseña no puede tener más de 50 caracteres.';
    return false;
  } else {
    passwordError.value = '';
    return true;
  }
};

const resetForm = () => {
  fullName.value = '';
  username.value = '';
  email.value = '';
  password.value = '';
  isAdmin.value = false;
  isActive.value = true;
  isVerified.value = true;
  
  fullNameError.value = '';
  usernameError.value = '';
  emailError.value = '';
  passwordError.value = '';
};

const closeModal = () => {
  emit('close');
  resetForm();
  isFirstOpen.value = true;
};

const handleEditUser = async () => {
  
  const isValidFullName = validateFullName();
  const isValidUsername = validateUsername();
  const isValidEmail = validateEmail();
  const isValidPassword = validatePassword();
  
  if (!isValidFullName || !isValidUsername || !isValidEmail || !isValidPassword) {
    return;
  }
  
  try {
    isSaving.value = true;
    
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    // Crear objeto para la actualización siguiendo el formato de la API.
    const updateData = {
      email: email.value,
      username: username.value,
      full_name: fullName.value.trim() || null,
      is_active: isActive.value,
      is_admin: isAdmin.value,
      is_verified: isVerified.value
    };
    
    // Solo se incluye la contraseña si se ha proporcionado (para no sobrescribirla con un valor vacío).
    if (password.value) {
      updateData.password = password.value;
    }
    
    const response = await axios.patch(`/users/${props.userId}`, updateData);
    
    notifySuccess("Usuario actualizado", 
    `Se ha actualizado el usuario "${username.value}" con éxito.`);
    
    emit('userUpdated', response.data);
    closeModal();
    
  } catch (error) {
    console.error('Error while editing user: ', error);
    handleApiError(error);
  } finally {
    isSaving.value = false;
  }
};

const handleApiError = (error) => {
  
  if (error.response) {
    const status = error.response.status;
    const detail = error.response.data.detail || "Unknown error";
    
    console.error('Error response: ', error.response.data);
    
    switch (status) {
      case 400:
        if (detail.includes("username")) {
          usernameError.value = "El nombre de usuario solo puede contener letras minúsculas, números y guiones bajos, y debe tener al menos 3 letras.";
        } else if (detail.includes("full name")) {
          fullNameError.value = "El nombre completo contiene caracteres no válidos.";
        } else {
          notifyError("Error de validación", 
          "Ha ocurrido un error de validación.");
        }
        break;
        
      case 403:
        if (detail.includes("credentials")) {
          notifyInfo("Sesión expirada", 
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else if (detail.includes("privileges")) {
          notifyError("Acceso denegado", 
          "No tienes permisos suficientes para realizar esta acción.");
          router.push('/');
        } else {
          notifyError("Acceso denegado", 
          "No tienes permisos suficientes para realizar esta acción.");
        }
        break;
        
      case 404:
        notifyError("Usuario no encontrado", 
        "El usuario que intentas editar no existe en el sistema.");
        break;
        
      case 409:
        if (detail.includes("username")) {
          usernameError.value = "Este nombre de usuario ya está en uso.";
        } else if (detail.includes("email")) {
          emailError.value = "Este correo electrónico ya está registrado en el sistema.";
        } else {
          notifyError("Conflicto", 
          "Los datos ya existen en el sistema.");
        }
        break;
        
      case 422:
        notifyError("Error de validación", 
        "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada.");
        break;
        
      default:
        notifyError("Error en el servidor", 
        "No se pudo completar la actualización del usuario. Por favor, inténtalo de nuevo más tarde.");
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", 
    "Ha ocurrido un problema al actualizar el usuario.");
  }
};
</script>

<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/buttons.css"></style>