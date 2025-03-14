<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal add-user-modal">
        <h1>Añadir nuevo usuario</h1>
        <button class="close-modal-button" @click="closeModal">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="signup-body" @submit.prevent="handleAddUser">
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
              v-model="username"
              :error="usernameError"
              @input="validateUsername"
            />
            <EmailField
              placeholder="Correo electrónico"
              v-model="email"
              :error="emailError"
              @input="validateEmail"
            />
            <PasswordField
              placeholder="Contraseña"
              v-model="password"
              :error="passwordError"
              @input="validatePassword"
            />
            <div class="admin-options">
              <div class="admin-option-item">
                <input type="checkbox" id="is_active" v-model="isActive" />
                <label for="is_active">Cuenta activa</label>
              </div>
              <div class="admin-option-item">
                <input type="checkbox" id="is_admin" v-model="isAdmin" />
                <label for="is_admin">Administrador</label>
              </div>
              <div class="admin-option-item">
                <input type="checkbox" id="is_verified" v-model="isVerified" />
                <label for="is_verified">Cuenta verificada</label>
              </div>
            </div>
            <button type="submit" class="app-button" :disabled="isLoading">
              <span v-if="!isLoading">Añadir usuario</span>
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
import { ref, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifyError, notifySuccess, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import FullNameField from '@/components/users/FullNameField.vue';
import UsernameField from '@/components/users/UsernameField.vue';
import EmailField from '@/components/users/EmailField.vue';
import PasswordField from '@/components/users/PasswordField.vue';


const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'userAdded']);

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

const isLoading = ref(false);
const authStore = useAuthStore();

// Foco en el campo de nombre completo al abrir el modal.
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await nextTick();
    const inputElement = fullNameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
});

const validateFullName = () => {
  // Como el nombre completo es opcional, es válido si está vacío.
  if (!fullName.value.trim()) {
    fullNameError.value = '';
    return true;
  }
  
  const nameRegex = /^[A-Za-zÁ-ÿà-ÿ]+(?:[ '-][A-Za-zÁ-ÿà-ÿ]+)*$/;

  if (!nameRegex.test(fullName.value)) {
    fullNameError.value = 'El nombre completo contiene caracteres inválidos.';
    return false;
  } else {
    fullNameError.value = '';
    return true;
  }
};

const validateUsername = () => {
  const usernameRegex = /^(?=(?:.*[a-z]){3})[a-z0-9_]+$/;
  
  if (!username.value) {
    usernameError.value = 'El nombre de usuario es obligatorio.';
    return false;
  } else if (!usernameRegex.test(username.value)) {
    usernameError.value = 'Solo letras minúsculas, números y guiones bajos. Debe contener al menos 3 letras.';
    return false;
  } else {
    usernameError.value = '';
    return true;
  }
};

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
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
  if (!password.value) {
    passwordError.value = 'La contraseña es obligatoria.';
    return false;
  } else if (password.value.length < 9) {
    passwordError.value = 'La contraseña debe tener al menos 9 caracteres.';
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
};

const handleAddUser = async () => {
  const isValidFullName = validateFullName();
  const isValidUsername = validateUsername();
  const isValidEmail = validateEmail();
  const isValidPassword = validatePassword();
  
  if (!isValidFullName || !isValidUsername || !isValidEmail || !isValidPassword) {
    return;
  }
  
  try {
    isLoading.value = true;
    
    // Asegurar que el token de autenticación esté configurado en la cabecera de la petición.
    const hasToken = !!localStorage.getItem('token') || !!authStore.token;
    if(hasToken){
      authStore.setAuthHeader();
    }
    
    const userData = {
      full_name: fullName.value || null,
      username: username.value,
      email: email.value,
      password: password.value,
      is_admin: isAdmin.value,
      is_active: isActive.value,
      is_verified: isVerified.value
    };
    
    const response = await axios.post('/users/', userData);
    
    notifySuccess(
      "Usuario creado", 
      `Se ha creado el usuario ${username.value} con éxito.`
    );
    
    emit('userAdded', response.data);
    closeModal();
    
  } catch (error) {
    console.error('Error while creating user: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
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
          "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada."
        );
        break;
        
      default:
        notifyError("Error en el servidor", 
          "No se pudo completar la creación del usuario. Por favor, inténtalo de nuevo más tarde."
        );
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
      "No se pudo conectar con el servidor. Verifica tu conexión a internet."
    );
  } else {
    notifyError("Error inesperado", 
      "Ha ocurrido un problema al crear el usuario."
    );
  }
};
</script>

<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/buttons.css"></style>