<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal" id="login-modal">
        <h1>¡Restablece tu contraseña!</h1>
        <button class="close-modal-button" @click="closeEnterEmailModal">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <form class="login-body" @submit.prevent="handleResetPassword">
          <div class="auth-modal-form">
            <EmailField 
              v-model="email" 
              :error="emailError"
              @input="validateEmail" 
              ref="emailFieldRef"
            />
            
            <button type="submit" class="app-button" :disabled="isLoading || !email">
              <span v-if="!isLoading">Enviar instrucciones</span>
              <span v-else>
                <font-awesome-icon icon="spinner" spin />
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/buttons.css"></style>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { notifySuccess, notifyError } from '@/utils/notifications';
import EmailField from '@/components/EmailField.vue';
import axios from 'axios';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'switchToLogin']);

const email = ref('');
const emailError = ref('');
const emailFieldRef = ref(null);
const isLoading = ref(false);

watch(() => props.isOpen, async (newValue) => {
  if (newValue) {
    await nextTick();
    const inputElement = emailFieldRef.value?.$el.querySelector('input');
    if (inputElement) {
      inputElement.focus();
    }
  }
});

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

const resetForm = () => {
  email.value = '';
  emailError.value = '';
  isLoading.value = false;
};

const closeEnterEmailModal = () => {
  emit('close');
  resetForm();
};

const handleResetPassword = async () => {
  if (!validateEmail()) {
    return;
  }
  
  try {
    isLoading.value = true;
    
    await axios.post(`/login/password-recovery/${encodeURIComponent(email.value)}`);

    notifySuccess(
      'Operación exitosa', 
      'Te hemos enviado un correo con instrucciones para restablecer tu contraseña.'
    );
    
    closeEnterEmailModal();
    
  } catch (error) {
    console.error('Error al solicitar recuperación de contraseña:', error);
    
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data.detail || 'Error desconocido';
      
      switch (status) {
        case 404:
          // El email no existe en el sistema
          emailError.value = 'No existe ninguna cuenta con este correo electrónico.';
          break;
          
        case 403:
          // Según la API, 403 puede ser por usuario no verificado o inactivo
          if (detail.includes("Unverified")) {
            notifyError(
                "Cuenta sin verificar", 
                "Debes verificar tu identidad para poder restablecer tu contraseña. Por favor, revisa tu correo electrónico."
              );
          } else if (detail.includes("Inactive")) {
            notifyError(
                "Cuenta desactivada", 
                "Tu cuenta está desactivada. Por favor, contacta con soporte."
              );
          } else {
            notifyError("Acceso denegado", detail);
          }
          break;
        default:
          notifyError(
            'Error', 
            'No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.'
          );
      }
    } else if (error.request) {
      notifyError(
        'Error de conexión', 
        'No se pudo conectar con el servidor. Verifica tu conexión a internet.'
      );
    } else {
      notifyError(
        'Error', 
        'Ocurrió un error al procesar tu solicitud.'
      );
    }
  } finally {
    isLoading.value = false;
  }
};
</script>