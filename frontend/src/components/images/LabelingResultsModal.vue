<template>
  <div v-if="isOpen" class="modal-overlay">
    <div class="auth-modal result-modal">
      <h1>Resumen del etiquetado</h1>
      <button class="close-modal-button" @click="handleClose">
        <font-awesome-icon :icon="['fas', 'xmark']" />
      </button>
      <div class="content-container">
        <div v-if="currentView === 'summary'" class="summary-view">
          <div class="stats-container success-stats">
            <div class="stat-item success">
              <div class="stat-icon">
                <font-awesome-icon :icon="['fas', 'check-circle']" />
              </div>
              <div class="stat-value">{{ normalizedResult.labeledCount }}</div>
              <div class="stat-label">Etiquetas aplicadas</div>
            </div>
            <div class="stat-item warning">
              <div class="stat-icon">
                <font-awesome-icon :icon="['fas', 'exclamation-circle']" />
              </div>
              <div class="stat-value">{{ normalizedResult.notFoundCount }}</div>
              <div class="stat-label">No aplicadas</div>
            </div>
          </div>
          <div class="result-message">
            <div class="message-card success" v-if="normalizedResult.labeledCount > 0">
              <font-awesome-icon :icon="['fas', 'check-circle']" />
              <p>¡Etiquetado completado! Se han aplicado <strong>{{ normalizedResult.labeledCount }}</strong> etiquetas correctamente.</p>
            </div>
            <div class="message-card error" v-else>
              <font-awesome-icon :icon="['fas', 'exclamation-circle']" />
              <p>No se ha podido aplicar ninguna etiqueta.</p>
            </div>
          </div>
          <div v-if="normalizedResult.notFoundCount > 0 && notFoundDetails.length > 0" class="issues-section">
            <div class="issues-header">
              <h3>Incidencias</h3>
              <p class="issues-description">Se han encontrado algunos problemas durante el etiquetado.</p>
            </div>
            <div class="issues-container">
              <div 
                class="issue-item warning clickable" 
                @click="goToDetails('notFound')"
              >
                <div class="issue-icon">
                  <font-awesome-icon :icon="['fas', 'exclamation-circle']" />
                </div>
                <div class="issue-content">
                  <div class="issue-title">
                    Etiquetas no aplicadas: <span>{{ normalizedResult.notFoundCount }}</span>
                  </div>
                  <div class="issue-action">Ver detalles</div>
                </div>
                <div class="issue-arrow">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="currentView === 'notFound'" class="detail-view">
          <div class="back-button" @click="currentView = 'summary'">
            <font-awesome-icon :icon="['fas', 'arrow-left']" />
            <span>Volver al resumen</span>
          </div>
          <h2 class="detail-title">Etiquetas no aplicadas</h2>
          <p class="section-description">
            Estas etiquetas no pudieron ser aplicadas porque los nombres de archivo no coinciden con ninguna imagen del conjunto.
          </p>
          <div v-if="notFoundDetails.length" class="detail-list">
            <div v-for="(detail, index) in notFoundDetails" :key="index" class="detail-item">
              <font-awesome-icon :icon="['fas', 'tag']" />
              <span class="item-path">{{ detail }}</span>
            </div>
          </div>
          <div v-else class="empty-message">
            <p>No hay información detallada disponible sobre las etiquetas no aplicadas.</p>
          </div>
        </div>
      </div>
      <div class="modal-actions" v-if="currentView === 'summary'">
        <button class="app-button" @click="handleClose">Aceptar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  result: {
    type: Object,
    required: true,
    default: () => ({
      labeledCount: 0,
      notFoundCount: 0,
      notFoundDetails: []
    })
  }
});

const emit = defineEmits(['close']);

const currentView = ref('summary');

// Normalizar nombres de propiedades para compatibilidad con respuesta del backend.
const normalizedResult = computed(() => {
  const result = {
    labeledCount: props.result.labeled_count || props.result.labeledCount || 0,
    notFoundCount: props.result.not_found_count || props.result.notFoundCount || 0,
    notFoundDetails: props.result.not_found_details || props.result.notFoundDetails || []
  };
  return result;
});

const notFoundDetails = computed(() => {
  return normalizedResult.value.notFoundDetails;
});

// Navegar a la vista de detalles.
const goToDetails = (view) => {
  if (view === 'notFound' && notFoundDetails.value.length > 0) {
    currentView.value = 'notFound';
  }
};

const handleClose = () => {
  currentView.value = 'summary'; // Restablecer a la vista de resumen.
  emit('close');
};

// Restablecer la vista cuando se abre el modal.
watch(() => props.isOpen, (newValue) => {
  if (newValue) {
    currentView.value = 'summary';
  }
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/results.css"></style>