<template>
  <div v-if="isOpen" class="modal-overlay">
    <div class="auth-modal modal-container">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="close-confirmation-button" @click="$emit('cancel')">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
      </div>
      <div class="modal-body">
        <p>{{ message }}</p>
      </div>
      <div class="modal-footer">
        <button class="cancel-button" @click="$emit('cancel')">{{ cancelText }}</button>
        <button class="delete-button" @click="$emit('confirm')">
          <font-awesome-icon v-if="isLoading" :icon="['fas', 'circle-notch']" spin class="button-icon" />
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped src="@/assets/styles/buttons.css"></style>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  title: {
    type: String,
    default: 'Confirmar acción',
  },
  message: {
    type: String,
    default: '¿Estás seguro de que quieres realizar esta acción?',
  },
  confirmText: {
    type: String,
    default: 'Confirmar',
  },
  cancelText: {
    type: String,
    default: 'Cancelar',
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['confirm', 'cancel']);
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background-color: white;
  border-radius: 8px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  margin: 0 20px;
}

.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.button-icon {
  margin-right: 8px;
}

.close-confirmation-button {
  background: none;
  border: none;
  font-size: 25px;
  cursor: pointer;
  color: black;
  transition: color 0.2s;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-confirmation-button:hover {
    color: red;
    transform: scale(1.2);
}
</style>