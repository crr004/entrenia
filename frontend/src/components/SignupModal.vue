<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal">
        <h1>¡Crea tu cuenta!</h1>
        <button class="close-button" @click="closeSignup">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="signup-body" @submit.prevent="handleSignup">
          <div class="auth-modal-form">
            <FullNameField
              v-model="fullName"
              label="Nombre completo"
              :error="fullNameError"
              @input="validateFullName"
              ref="fullNameFieldRef"
            />
            <UsernameField
              v-model="username"
              :error="usernameError"
              @input="validateUsername"
            />
            <EmailField
              v-model="email"
              :error="emailError"
              @input="validateEmail"
            />
            <PasswordField 
              v-model="password"
              label="Contraseña*"
              placeholder="Introduce tu contraseña"
              :error="passwordError"
              hint="La contraseña debe tener al menos 9 caracteres."
              id="signup-password"
              @input="validatePassword"
            />
            <button type="submit" class="submit-button" :disabled="isLoading">
              <span v-if="!isLoading">Registrarse</span>
              <span v-else>
                <font-awesome-icon icon="spinner" spin />
              </span>
          </button>
          </div>
          <div class="login-link">
            ¿Ya tienes cuenta? <a class="ref-link" href="#" @click.prevent="switchToLogin">Inicia sesión</a>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped src="@/assets/styles/auth.css"></style>

<script setup>
import { ref, watch, nextTick } from 'vue';
import FullNameField from '@/components/FullNameField.vue';
import UsernameField from '@/components/UsernameField.vue';
import EmailField from '@/components/EmailField.vue';
import PasswordField from '@/components/PasswordField.vue';
import axios from 'axios';
import { notifyError, notifySuccess } from '@/utils/notifications';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'switchToLogin']);

// Campos del formulario
const fullName = ref('');
const username = ref('');
const email = ref('');
const password = ref('');
const fullNameFieldRef = ref(null);

// Mensajes de error
const fullNameError = ref('');
const usernameError = ref('');
const emailError = ref('');
const passwordError = ref('');

const isLoading = ref(false);

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
  const usernameRegex = /^(?=.*[a-z]{3})[a-z0-9_]+$/;
  
  if (!username.value) {
    usernameError.value = 'El nombre de usuario es obligatorio.';
    return false;
  } else if (!usernameRegex.test(username.value)) {
    usernameError.value = 'Solo letras, números y guiones bajos. Debe contener al menos 3 letras.';
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
  
  fullNameError.value = '';
  usernameError.value = '';
  emailError.value = '';
  passwordError.value = '';
};

const closeSignup = () => {
  emit('close');
  resetForm();
};

const switchToLogin = () => {
  emit('switchToLogin');
  resetForm();
};

const handleSignup = async () => {
  const isValidFullName = true;
  if(!(fullName.value.trim()=="")){
    const isValidFullName = validateFullName();
  }
  const isValidUsername = validateUsername();
  const isValidEmail = validateEmail();
  const isValidPassword = validatePassword();
  if (!isValidFullName || !isValidUsername || !isValidEmail || !isValidPassword) {
    return;
  }
  
  try {
    isLoading.value = true;
    
    const userData = {
      full_name: fullName.value,
      username: username.value,
      email: email.value,
      password: password.value
    };
    
    const response = await axios.post('/signup', userData);
    
    notifySuccess(
      "Cuenta creada correctamente", 
      "Revisa tu correo para verificar tu identidad antes de poder iniciar sesión."
    );
  
    closeSignup();
  } catch (error) {
    console.error('Error durante el registro:', error);
    
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data.detail || "Error desconocido";
      
      switch (status) {
        case 400:
          // Errores de validación específicos
          if (detail.includes("username")) {
            usernameError.value = "El nombre de usuario solo puede contener letras minúsculas, números y guiones bajos, y debe tener al menos 3 letras.";
          } else if (detail.includes("full name")) {
            fullNameError.value = "El nombre completo contiene caracteres no permitidos.";
          } else {
            notifyError("Error de validación", detail);
          }
          break;
          
        case 409:
          // Conflictos con recursos existentes
          if (detail.includes("username")) {
            usernameError.value = "Este nombre de usuario ya está en uso.";
          } else if (detail.includes("email")) {
            emailError.value = "Este correo electrónico ya está registrado en el sistema.";
          } else {
            notifyError("Error de registro", detail);
          }
          break;
          
        case 422:
          notifyError(
            "Error de validación", 
            "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada."
          );
          break;
          
        default:
          notifyError(
            "Error en el servidor", 
            "No se pudo completar el registro. Por favor, inténtalo de nuevo más tarde."
          );
      }
    } else if (error.request) {
      // La petición fue realizada pero no se recibe respuesta
      notifyError(
        "Error de conexión", 
        "No se pudo conectar con el servidor. Verifica tu conexión a internet."
      );
    } else {
      // Error al configurar la petición
      notifyError(
        "Error", 
        "Ha ocurrido un problema al procesar tu solicitud."
      );
    }
  } finally {
    isLoading.value = false;
  }
};
</script>