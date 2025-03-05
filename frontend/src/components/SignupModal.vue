<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal">
        <h1>¡Crea tu cuenta!</h1>
        <button class="close-button" @click="closeSignup">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <div class="signup-body">
          <div class="login-link">
            ¿Ya tienes cuenta? <a class="ref-link" href="#" @click.prevent="switchToLogin">Inicia sesión</a>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped src="@/assets/styles/auth.css"></style>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close', 'switchToLogin', 'signup']);

const closeSignup = () => {
  emit('close');
  //resetForm();
};

const switchToLogin = () => {
  emit('switchToLogin');
  //resetForm();
};
</script>