<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal" id="login-modal">
        <h1>¡Hola!</h1>
        <button class="close-button" @click="closeLogin">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="signup-body" @submit.prevent="handleLogin">
          <div class="auth-modal-form">
            <LoginNameField
              ref="usernameFieldRef"
              v-model="username"
              label="Nombre de usuario o correo electrónico*"
              placeholder="Introduce tu nombre o correo"
              :error="usernameError"
              icon="user"
              @input="removeSpaces"
            />
            <PasswordField 
              v-model="password"
              label="Contraseña*"
              placeholder="Introduce tu contraseña"
              :error="passwordError"
              hint="La contraseña debe tener al menos 9 caracteres."
              id="signup-password"
            />
            <div class="reset-password-link">
              ¿Has olvidado tu contraseña? <a class="ref-link">Restablécela</a>
            </div>
            <button type="submit" class="submit-button">
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

<style scoped src="@/assets/styles/auth.css"></style>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { notifyError } from '@/utils/notifications';
import PasswordField from '@/components/PasswordField.vue';
import LoginNameField from '@/components/LoginNameField.vue';
import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const password = ref('');
const passwordError = ref('');
const username = ref('');
const usernameError = ref('');
const usernameFieldRef = ref(null);
const isLoading = ref(false);
const authStore = useAuthStore();

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'switchToSignup', 'loginSuccess']);

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

const handleLogin = async () => {

  let isValid = true;
  
  if (!username.value.trim()) {
    usernameError.value = 'Por favor, introduce tu nombre de usuario o correo electrónico.';
    isValid = false;
  } else {
    // Comprobar si es un email (contiene @) o un nombre de usuario
    if (username.value.includes('@')) {
      // Validación para correo electrónico
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(username.value)) {
        usernameError.value = 'Por favor, introduce un correo electrónico válido.';
        isValid = false;
      } else {
        usernameError.value = '';
      }
    } else {
      // Validación para nombre de usuario: al menos 3 letras minúsculas y solo puede contener letras minúsculas, números y guiones bajos
      const usernameRegex = /^(?=.*[a-z]{3})[a-z0-9_]+$/;
      if (!usernameRegex.test(username.value)) {
        usernameError.value = 'Por favor, introduce un nombre de usuario válido.';
        isValid = false;
      } else {
        usernameError.value = '';
      }
    }
  }
  
  const passwordRegex = /^.{9,}$/;
  if (!password.value) {
    passwordError.value = 'Por favor, introduce tu contraseña.';
    isValid = false;
  } else if (!passwordRegex.test(password.value)) {
    passwordError.value = 'Por favor, introduce una contraseña válida.';
    isValid = false;
  } else {
    passwordError.value = '';
  }
  
  if (isValid) {
    try {
      isLoading.value = true;
      
      const formData = new URLSearchParams();
      formData.append('username', username.value);
      formData.append('password', password.value);
      
      const apiUrl = 'http://localhost:8000/api/login';

      const response = await axios.post(apiUrl, formData, {
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
          console.error('Error while saving the token:', storeError);
          notifyError(
            "Error de autenticación",
            "No se pudo completar el inicio de sesión."
          );
        }
      } else {
        throw new Error('Acces token not found in response');
      }
    } catch (error) {
      console.error('Complete error:', error);
      isLoading.value = false;
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data.detail || 'Error desconocido';
        
        switch (status) {
          case 401:
            notifyError(
              "Error de autenticación", 
              "El nombre de usuario/correo electrónico o la contraseña son incorrectos."
            );
            break;
            
          case 403:
            if (detail.includes("Inactive")) {
              notifyError(
                "Cuenta desactivada", 
                "Tu cuenta está desactivada. Por favor, contacta con soporte."
              );
            } else if (detail.includes("Unverified")) {
              notifyError(
                "Cuenta sin verificar", 
                "Debes verificar tu identidad para poder acceder. Por favor, revisa tu correo electrónico."
              );
            } else {
              notifyError("Acceso denegado", detail);
            }
            break;
            
          case 422:
            notifyError(
              "Error de validación", 
              "Los datos proporcionados no son válidos."
            );
            break;
            
          default:
            notifyError(
              "Error inesperado", 
              "Ha ocurrido un error al iniciar sesión. Por favor, inténtalo de nuevo más tarde."
            );
        }
      } else if (error.request) {
        // La petición fue realizada pero no se recibió respuesta
        notifyError(
          "Error de conexión", 
          "No se pudo conectar con el servidor. Verifica tu conexión a internet."
        );
      } else {
        // Error al configurar la petición
        notifyError(
          "Error", 
          "Los datos de acceso son incorrectos."
        );
      }
    }
  }
};
</script>

