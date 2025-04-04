<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay">
      <div class="auth-modal labeling-method-modal">
        <button class="close-modal-button" @click="close">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <h2>¡Etiqueta tus imágenes!</h2>
        <div class="modal-content">
          <p class="intro-text">
            Selecciona cómo quieres etiquetar las {{ unlabeledCount }} imágenes sin etiquetar de este conjunto.
          </p>
          <div class="method-options">
            <div class="method-card" @click="selectMethod('manual')">
              <div class="method-icon">
                <font-awesome-icon :icon="['fas', 'tag']" />
              </div>
              <div class="method-info">
                <h3>Etiquetado manual</h3>
                <p>Revisa y etiqueta las imágenes una por una.</p>
              </div>
            </div>
            <div class="method-card" @click="selectMethod('csv')">
              <div class="method-icon">
                <font-awesome-icon :icon="['fas', 'file-csv']" />
              </div>
              <div class="method-info">
                <h3>Importar desde CSV</h3>
                <p>Sube un archivo CSV con nombres y etiquetas.</p>
                <span class="info-note">También permite reetiquetar imágenes ya etiquetadas.</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="cancel-button" @click="close">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  unlabeledCount: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['close', 'select-method']);

const close = () => {
  emit('close');
};

const selectMethod = (method) => {
  emit('select-method', method);
  close();
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped>
.labeling-method-modal {
  width: 520px;
  max-width: 95%;
  max-height: 80vh;
  padding: 25px;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.info-note {
  display: block;
  font-size: 0.8rem;
  color: #777;
  margin-top: 3px;
  font-style: italic;
}


.intro-text {
  text-align: center;
  margin-bottom: 20px;
  color: #555;
  font-size: 0.95rem;
}

.method-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 15px;
}

.method-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background-color: #f9f9f9;
  cursor: pointer;
  transition: all 0.2s ease;
}

.method-card:hover {
  background-color: rgba(34, 134, 141, 0.1);
  border-color: rgb(34, 134, 141);
  transform: translateY(-2px);
}

.method-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  color: #999;
  font-size: 1rem;
}

.method-info {
  flex: 1;
}

.method-info h3 {
  margin: 0 0 4px 0;
  font-size: 1rem;
  color: #333;
}

.method-info p {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
  padding-top: 15px;
}

/* Responsive */
@media (max-width: 480px) {
  .method-card {
    padding: 10px;
    gap: 10px;
  }
  
  .method-icon {
    width: 36px;
    height: 36px;
    font-size: 0.9rem;
  }
  
  .method-info h3 {
    font-size: 0.95rem;
  }
  
  .method-info p {
    font-size: 0.8rem;
  }
  
  .modal-actions button {
    width: 100%;
  }
}
</style>