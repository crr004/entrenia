<template>
  <div class="modal-overlay">
    <div class="auth-modal reset-password-card">
      <h1>Restablecer contraseña</h1>
      
      <div v-if="isLoading" class="loading-state">
        <font-awesome-icon :icon="['fas', 'spinner']" spin class="spinner" />
        <p>Verificando tu solicitud...</p>
      </div>
      
      <div v-else-if="tokenStatus === 'invalid'" class="error-state">
        <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="error-icon" />
        <h2>Enlace inválido o expirado</h2>
        <p>El enlace que has utilizado no es válido o ha expirado. Por favor, solicita un nuevo enlace para restablecer tu contraseña.</p>
        <button @click="goToHome" class="app-button">Volver al inicio</button>
      </div>
      
      <div v-else-if="tokenStatus === 'success'" class="success-state">
        <font-awesome-icon :icon="['fas', 'check-circle']" class="success-icon" />
        <h2>¡Contraseña actualizada!</h2>
        <p>Tu contraseña ha sido actualizada correctamente. Ahora puedes iniciar sesión con tu nueva contraseña.</p>
        <button @click="goToHome" class="app-button">Volver al inicio</button>
      </div>
      
      <form v-else-if="tokenStatus === 'valid'" class="auth-modal-form reset-password-form" @submit.prevent="handleSubmit">
        <p class="form-description">Por favor, introduce tu nueva contraseña.</p>
        
        <PasswordField 
          v-model="password"
          label="Nueva contraseña*"
          placeholder="Introduce tu nueva contraseña"
          :error="passwordError"
          @input="validatePassword"
        />
        
        <PasswordField 
          v-model="confirmPassword"
          label="Confirmar contraseña*"
          placeholder="Confirma tu nueva contraseña"
          :error="confirmPasswordError"
          @input="validateConfirmPassword"
        />
        
        <button type="submit" class="app-button" :disabled="isSubmitting">
          <span v-if="!isSubmitting">Restablecer contraseña</span>
          <font-awesome-icon v-else :icon="['fas', 'spinner']" spin />
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import PasswordField from '@/components/PasswordField.vue';
import { notifySuccess, notifyError } from '@/utils/notifications';

const router = useRouter();
const route = useRoute();

const tokenStatus = ref('pending'); // 'pending', 'valid', 'invalid', 'success'
const isLoading = ref(true);
const isSubmitting = ref(false);

const password = ref('');
const confirmPassword = ref('');
const passwordError = ref('');
const confirmPasswordError = ref('');
const token = ref('');

const validatePassword = () => {
  if (!password.value) {
    passwordError.value = 'La contraseña es obligatoria.';
    return false;
  } else if (password.value.length < 9) {
    passwordError.value = 'La contraseña debe tener al menos 9 caracteres.';
    return false;
  } else {
    passwordError.value = '';
    if (confirmPassword.value) {
      validateConfirmPassword();
    }
    return true;
  }
};

const validateConfirmPassword = () => {
  if (!confirmPassword.value) {
    confirmPasswordError.value = 'Confirma tu contraseña.';
    return false;
  } else if (confirmPassword.value !== password.value) {
    confirmPasswordError.value = 'Las contraseñas no coinciden.';
    return false;
  } else {
    confirmPasswordError.value = '';
    return true;
  }
};

const goToHome = () => {
  router.push('/');
};

onMounted(async () => {

  token.value = route.query.token;
  
  if (!token.value) {
    tokenStatus.value = 'invalid';
    isLoading.value = false;
    return;
  }
  try {
    tokenStatus.value = 'valid';
    isLoading.value = false;
  } catch (error) {
    tokenStatus.value = 'invalid';
    console.error('Error validando token:', error);
    isLoading.value = false;
  }
});

const handleSubmit = async () => {
  const isPasswordValid = validatePassword();
  const isConfirmPasswordValid = validateConfirmPassword();
  
  if (!isPasswordValid || !isConfirmPasswordValid) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    await axios.post('/login/password-reset/', {
      token: token.value,
      new_password: password.value
    });
    
    tokenStatus.value = 'success';
    notifySuccess(
      'Contraseña actualizada',
      'Tu contraseña ha sido cambiada exitosamente.'
    );
  } catch (error) {
    console.error('Error al restablecer contraseña:', error);
    
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data.detail || 'Error desconocido';
      
      switch (status) {
        case 400:
          if (detail.includes("You cannot reuse")) {
            passwordError.value = 'No puedes reutilizar tu contraseña anterior.';
          } else {
            notifyError('Error', 'El token es inválido o ha expirado.');
            tokenStatus.value = 'invalid';
          }
          break;
        case 403:
          notifyError('Error', 'Esta cuenta está desactivada. Contacta con soporte.');
          tokenStatus.value = 'invalid';
          break;
        case 404:
          notifyError('Error', 'No se encontró un usuario asociado a este token.');
          tokenStatus.value = 'invalid';
          break;
        default:
          notifyError('Error', 'No se pudo restablecer tu contraseña. Por favor, inténtalo de nuevo.');
      }
    } else {
      notifyError(
        'Error de conexión',
        'No se pudo conectar con el servidor. Verifica tu conexión a internet.'
      );
    }
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/buttons.css"></style>

<style scoped>
.reset-password-card {
  transform: none;
  max-width: 500px;
}

.reset-password-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-description {
  color: #666;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.loading-state,
.error-state,
.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}

.spinner {
  font-size: 3rem;
  color: rgb(34, 134, 141);
  margin-bottom: 1.5rem;
}

.error-icon {
  font-size: 3rem;
  color: #f44336;
  margin-bottom: 1.5rem;
}

.success-icon {
  font-size: 3rem;
  color: #4caf50;
  margin-bottom: 1.5rem;
}

.loading-state p,
.error-state p,
.success-state p {
  color: #666;
  margin-bottom: 1.5rem;
  text-align: center;
}

.error-state h2,
.success-state h2 {
  color: #333;
  margin-bottom: 1rem;
}
</style>