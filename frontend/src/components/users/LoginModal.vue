<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal" id="login-modal">
        <h1>¡Hola!</h1>
        <button class="close-modal-button" @click="closeLogin">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="login-body" @submit.prevent="handleLogin">
          <div class="auth-modal-form">
            <LoginNameField
              v-model="username"
              :error="usernameError"
              @input="removeSpaces"
              ref="usernameFieldRef"
              label="Nombre de usuario o correo electrónico"
            />
            <PasswordField 
              v-model="password"
              :error="passwordError"
              label="Contraseña"
            />
            <div class="reset-password-link">
              ¿Has olvidado tu contraseña? <a class="ref-link" href="#" @click.prevent="switchToEnterEmailModal">Restablécela</a>
            </div>
            <button type="submit" class="app-button" :disabled="isLoading">
              <span v-if="!isLoading">Iniciar sesión</span>
              <span v-else>
                <font-awesome-icon icon="spinner" spin />
              </span>
          </button>
          </div>
          <div class="singup-link">
            ¿No tienes cuenta? <a class="ref-link" href="#" @click.prevent="switchToSignup">Regístrate</a>
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

import { notifyError } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import PasswordField from '@/components/users/PasswordField.vue';
import LoginNameField from '@/components/users/LoginNameField.vue';

const password = ref('');
const passwordError = ref('');
const username = ref(''); // Nombre de usuario o correo electrónico.
const usernameError = ref('');
const usernameFieldRef = ref(null);
const isLoading = ref(false);
const authStore = useAuthStore();
const router = useRouter();

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'switchToSignup', 'switchToEnterEmailModal', 'loginSuccess']);

// Foco en el campo de nombre/correo al abrir el modal.
watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await nextTick();
    const inputElement = usernameFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
});

const removeSpaces = (event) => {
  username.value = username.value.replace(/\s/g, '');
};

const resetForm = () => {
  username.value = '';
  usernameError.value = '';
  password.value = '';
  passwordError.value = '';
  isLoading.value = false;
};

const closeLogin = () => {
  emit('close');
  resetForm();
};

const switchToSignup = () => {
  emit('switchToSignup');
  resetForm();
};

const switchToEnterEmailModal = () => {
  emit('switchToEnterEmailModal');
  resetForm();
};

const validateUsername = () => {
  if (!username.value.trim()) {
    usernameError.value = 'Por favor, introduce tu nombre de usuario o correo electrónico.';
    return false;
  } 
  
  // Comprobar si es un email (contiene @) o un nombre de usuario.
  if (username.value.includes('@')) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(username.value)) {
      usernameError.value = 'Por favor, introduce un correo electrónico válido.';
      return false;
    }
  } else {
    const usernameRegex = /^(?=(?:.*[a-z]){3})[a-z0-9_]+$/;
    if (!usernameRegex.test(username.value)) {
      usernameError.value = 'Por favor, introduce un nombre de usuario válido.';
      return false;
    }
  }
  
  usernameError.value = '';
  return true;
};

const validatePassword = () => {
  const passwordRegex = /^.{9,}$/;
  if (!password.value) {
    passwordError.value = 'Por favor, introduce tu contraseña.';
    return false;
  } else if (!passwordRegex.test(password.value)) {
    passwordError.value = 'Por favor, introduce una contraseña válida.';
    return false;
  } else {
    passwordError.value = '';
    return true;
  }
};

const handleLogin = async () => {
  const isValidUsername = validateUsername();
  const isValidPassword = validatePassword();
  
  if (!isValidUsername || !isValidPassword) {
    return;
  }
  
  try {
    isLoading.value = true;
    
    const formData = new URLSearchParams();
    formData.append('username', username.value);
    formData.append('password', password.value);

    const response = await axios.post('/login/', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    if (response.data.access_token) {
      try {
        await authStore.login(response.data.access_token);
        
        emit('loginSuccess');
        closeLogin();
      } catch (storeError) {
        console.error('Error while saving the token: ', storeError);
        notifyError("Error de autenticación",
        "No se pudo completar el inicio de sesión.");
      }
    } else {
      console.error('Access token not found in response: ', response.data);
      notifyError("Error de autenticación",
      "La respuesta del servidor no contiene la información necesaria.");
    }
  } catch (error) {
    console.error('Error: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const status = error.response.status;
    const detail = error.response.data.detail || 'Unknown error';

    console.error('Error response: ', error.response.data);
    
    switch (status) {
      case 401:
        notifyError("Error de autenticación", 
        "El nombre de usuario/correo electrónico o la contraseña son incorrectos.");
        break;
        
      case 403:
        if (detail.includes("Inactive")) {
          notifyError("Cuenta desactivada", 
          "Tu cuenta está desactivada. Por favor, contacta con soporte.");
        } else if (detail.includes("Unverified")) {
          notifyError("Cuenta sin verificar", 
          "Debes verificar tu identidad para poder acceder. Por favor, revisa tu correo electrónico.");
        } else {
          notifyError("Acceso denegado", 
          "No tienes permiso para realizar esta acción.");
        }
        break;
        
      case 422:
        notifyError("Error de validación", 
        "Los datos proporcionados no son válidos.");
        break;
        
      default:
        notifyError("Error en el servidor", 
        "No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.");
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", 
    "Ha ocurrido un problema.");
  }
};
</script>

<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/buttons.css"></style>

