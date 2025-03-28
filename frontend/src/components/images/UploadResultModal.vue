<template>
  <div v-if="show" class="modal-overlay">
    <div class="auth-modal result-modal">
      <h1>Resultados de la subida</h1>
      <button class="close-modal-button" @click="onClose">
        <font-awesome-icon :icon="['fas', 'xmark']" />
      </button>
      <div class="content-container">
        <div v-if="currentView === 'summary'" class="summary-view">
          <div class="stats-container success-stats">
            <div class="stat-item success">
              <div class="stat-icon">
                <font-awesome-icon :icon="['fas', 'check-circle']" />
              </div>
              <div class="stat-value">{{ stats.processed_images || 0 }}</div>
              <div class="stat-label">Imágenes añadidas</div>
            </div>
            <div class="stat-item info">
              <div class="stat-icon">
                <font-awesome-icon :icon="['fas', 'tag']" />
              </div>
              <div class="stat-value">{{ stats.labels_applied }}</div>
              <div class="stat-label">Etiquetas aplicadas</div>
            </div>
          </div>
          <div class="result-message">
            <div class="message-card success" v-if="stats.processed_images > 0">
              <font-awesome-icon :icon="['fas', 'check-circle']" />
              <p>¡Subida completada! Se han añadido <strong>{{ stats.processed_images }}</strong> imágenes al conjunto de datos.</p>
            </div>
            <div class="message-card error" v-else>
              <font-awesome-icon :icon="['fas', 'exclamation-circle']" />
              <p>No se ha añadido ninguna imagen.</p>
            </div>
          </div>
          <div v-if="hasIssues" class="issues-section">
            <div class="issues-header">
              <h3>Incidencias</h3>
              <p class="issues-description">Se han encontrado algunos problemas durante la subida.</p>
            </div>
            <div class="issues-container">
              <div 
                v-if="stats.skipped_images > 0" 
                class="issue-item warning clickable" 
                @click="goToDetails('duplicated')"
              >
                <div class="issue-icon">
                  <font-awesome-icon :icon="['fas', 'copy']" />
                </div>
                <div class="issue-content">
                  <div class="issue-title">
                    Imágenes omitidas: <span>{{ stats.skipped_images }}</span>
                  </div>
                  <div class="issue-action">Ver detalles</div>
                </div>
                <div class="issue-arrow">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" />
                </div>
              </div>
              <div 
                v-if="stats.invalid_images > 0" 
                class="issue-item error clickable" 
                @click="goToDetails('invalid')"
              >
                <div class="issue-icon">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" />
                </div>
                <div class="issue-content">
                  <div class="issue-title">
                    Imágenes inválidas: <span>{{ stats.invalid_images }}</span>
                  </div>
                  <div class="issue-action">Ver detalles</div>
                </div>
                <div class="issue-arrow">
                  <font-awesome-icon :icon="['fas', 'chevron-right']" />
                </div>
              </div>
              <div 
                v-if="stats.labels_skipped > 0" 
                class="issue-item warning clickable" 
                @click="goToDetails('labels')"
              >
                <div class="issue-icon">
                  <font-awesome-icon :icon="['fas', 'exclamation-circle']" />
                </div>
                <div class="issue-content">
                  <div class="issue-title">
                    Etiquetas no aplicadas: <span>{{ stats.labels_skipped }}</span>
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
        <div v-else-if="currentView === 'duplicated'" class="detail-view">
          <div class="back-button" @click="currentView = 'summary'">
            <font-awesome-icon :icon="['fas', 'arrow-left']" />
            <span>Volver al resumen</span>
          </div>
          <h2 class="detail-title">Imágenes omitidas</h2>
          <p class="section-description">
            Ya hay imágenes con estos nombres en el conjunto, por lo que estas no se han vuelto a añadir.
            Para poder añadirlas, deben tener nombres únicos.
          </p>
          <div v-if="duplicatedImages.length" class="detail-list">
            <div v-for="(image, index) in duplicatedImages" :key="index" class="detail-item">
              <font-awesome-icon :icon="['fas', 'file-image']" />
              <span class="item-path">{{ image }}</span>
            </div>
          </div>
          <div v-else class="empty-message">
            <p>No hay información detallada disponible sobre las imágenes omitidas.</p>
          </div>
        </div>
        <div v-else-if="currentView === 'invalid'" class="detail-view">
          <div class="back-button" @click="currentView = 'summary'">
            <font-awesome-icon :icon="['fas', 'arrow-left']" />
            <span>Volver al resumen</span>
          </div>
          <h2 class="detail-title">Imágenes inválidas</h2>
          <p class="section-description">
            Estas imágenes no pudieron ser procesadas debido a formatos no soportados o archivos corruptos.
          </p>
          <div v-if="invalidImages.length" class="detail-list">
            <div v-for="(image, index) in invalidImages" :key="index" class="detail-item">
              <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="error-icon" />
              <span class="item-path">{{ image }}</span>
            </div>
          </div>
          <div v-else class="empty-message">
            <p>No hay detalles disponibles sobre las imágenes inválidas.</p>
          </div>
        </div>
        <div v-else-if="currentView === 'labels'" class="detail-view">
          <div class="back-button" @click="currentView = 'summary'">
            <font-awesome-icon :icon="['fas', 'arrow-left']" />
            <span>Volver al resumen</span>
          </div>
          <h2 class="detail-title">Etiquetas no aplicadas</h2>
          <p class="section-description">
            Estas etiquetas del CSV no pudieron ser aplicadas porque los nombres de archivo no coinciden con ninguna imagen subida.
          </p>
          <div v-if="csvLabels.length" class="detail-list">
            <div v-for="(label, index) in csvLabels" :key="index" class="detail-item">
              <font-awesome-icon :icon="['fas', 'tag']" />
              <span class="item-path">{{ label }}</span>
            </div>
          </div>
          <div v-else class="empty-message">
            <p>No hay detalles disponibles sobre las etiquetas no aplicadas.</p>
          </div>
        </div>
      </div>
      <div class="modal-actions" v-if="currentView === 'summary'">
        <button class="app-button" @click="onClose">Aceptar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  stats: {
    type: Object,
    default: () => ({
      processed_images: 0,
      skipped_images: 0,
      invalid_images: 0,
      labels_applied: 0,
      labels_skipped: 0
    })
  },
  invalidImageDetails: {
    type: Array,
    default: () => []
  },
  duplicatedImageDetails: {
    type: Array,
    default: () => []
  },
  skippedLabelDetails: {
    type: Array, 
    default: () => []
  }
});

const emit = defineEmits(['close']);
const currentView = ref('summary');

const invalidImages = computed(() => props.invalidImageDetails);

const duplicatedImages = computed(() => props.duplicatedImageDetails);

// Detalles de etiquetas no aplicadas.
const csvLabels = computed(() => {
  if (!props.skippedLabelDetails || props.skippedLabelDetails.length === 0) {
    return [];
  }
  
  return props.skippedLabelDetails.map(label => {
    if (typeof label === 'string') {
      if (label.includes('=')) {
        return label.replace('=', ',');
      }
      return label;
    } 

    if (label.name && label.value) {
      return `${label.name},${label.value}`;
    }
    return label.toString();
  });
});


const goToDetails = (view) => {
  // Solo navegar si hay datos para mostrar.
  if (view === 'duplicated' && props.duplicatedImageDetails.length > 0) {
    currentView.value = 'duplicated';
  } else if (view === 'invalid' && props.invalidImageDetails.length > 0) {
    currentView.value = 'invalid';
  } else if (view === 'labels' && props.skippedLabelDetails.length > 0) {
    currentView.value = 'labels';
  }
};

const onClose = () => {
  currentView.value = 'summary'; // Volver a la vista por defecto.
  emit('close');
};

const hasIssues = computed(() => {
  return props.stats.skipped_images > 0 || props.stats.invalid_images > 0 || props.stats.labels_skipped > 0;
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/auth.css"></style>
<style scoped src="@/assets/styles/results.css"></style>