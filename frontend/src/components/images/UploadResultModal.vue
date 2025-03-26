<template>
  <div v-if="show" class="modal-overlay">
    <div class="auth-modal upload-result-modal">
      <h1>Resumen de la subida</h1>
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
<style scoped>
.upload-result-modal {
  width: 500px;
  max-width: 95%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  padding-bottom: 20px;
}

.upload-result-modal {
  width: 500px;
  max-width: 95%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  padding-bottom: 20px;
}

.upload-result-modal h1 {
  text-align: center;
  color: #333;
  font-size: 1.5rem;
  margin: 0 0 20px 0;
}

.content-container {
  flex: 1;
  overflow-y: auto;
  padding: 0 10px;
  padding-top: 6px;
}

/* Tarjetas de estadísticas */
.stats-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px; 
  padding: 4px;
}

.success-stats {
  justify-content: center;
}

.stat-item {
  text-align: center;
  padding: 16px;
  border-radius: 10px;
  min-width: 110px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s;
}

.stat-item.issue-card {
  padding-bottom: 30px;
  position: relative;
  border: 1px dashed rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 20px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 13px;
  margin-top: 4px;
}

.view-details {
  position: absolute;
  bottom: 8px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 11px;
  color: inherit;
  opacity: 0.8;
  text-decoration: underline;
}

.stat-item.clickable {
  cursor: pointer;
}

.stat-item.clickable:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

/* Separador visual */
.stats-divider {
  width: 100%;
  text-align: center;
  margin: 15px 0 10px 0;
  position: relative;
}

.stats-divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: #e0e0e0;
  z-index: 1;
}

.stats-divider span {
  background-color: white;
  padding: 0 15px;
  position: relative;
  z-index: 2;
  color: #666;
  font-size: 0.85rem;
  font-weight: 500;
}

/* Mensajes de resultado */
.result-message {
  margin-bottom: 20px;
}

.message-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
}

.message-card p {
  margin: 0;
  line-height: 1.5;
  color: #333;
}

.message-card strong {
  font-weight: 600;
}

/* Sección de incidencias */
.issues-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.issues-header {
  margin-bottom: 12px;
}

.issues-header h3 {
  font-size: 1rem;
  color: #555;
  margin: 0 0 5px 0;
}

.issues-description {
  font-size: 0.85rem;
  color: #777;
  margin: 0;
}

.issues-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-radius: 8px;
  background-color: white;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.issue-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.issue-icon {
  margin-right: 12px;
  font-size: 16px;
  min-width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.issue-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.issue-title {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.issue-title span {
  font-weight: 600;
}

.issue-action {
  font-size: 0.75rem;
  color: #666;
  margin-top: 2px;
}

.issue-arrow {
  color: #999;
  font-size: 0.8rem;
}

/* Vista de detalles */
.detail-view {
  margin-bottom: 20px;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #555;
  cursor: pointer;
  margin-bottom: 16px;
  padding: 8px 0;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.back-button:hover {
  color: rgb(34, 134, 141);
}

.detail-title {
  font-size: 1.2rem;
  color: #333;
  margin: 0 0 8px 0;
  text-align: center;
}

.section-description {
  color: #666;
  margin: 0 0 15px 0;
  font-size: 0.9rem;
  line-height: 1.4;
  text-align: left;
}

.detail-list {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 8px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #eee;
}

.detail-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  font-size: 0.9rem;
  color: #333;
  text-align: left;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item svg {
  margin-right: 10px;
  min-width: 16px;
  color: #666;
}

.item-path {
  word-break: break-all;
  text-align: left;
}

.empty-message {
  text-align: center;
  padding: 20px;
  color: #666;
}

/* Colores y variantes */
.success { 
  background: #e6f7e9; 
  color: #2e7d32; 
  border: 1px solid rgba(46, 125, 50, 0.1);
}

.message-card.success {
  background-color: #f0f9f1;
  border-left: 4px solid #4caf50;
}

.info { 
  background: #e3f2fd; 
  color: #1565c0; 
  border: 1px solid rgba(21, 101, 192, 0.1);
}

.warning { 
  background: #fff8e1; 
  color: #f57f17;
}

.issue-item.warning {
  border-left: 4px solid #f57f17;
  background-color: rgba(255, 248, 225, 0.4);
}

.issue-item.warning .issue-icon {
  color: #f57f17;
}

.error { 
  background: #fbe9e7; 
  color: #c62828;
}

.message-card.error {
  background-color: #feeceb;
  border-left: 4px solid #f44336;
}

.issue-item.error {
  border-left: 4px solid #c62828;
  background-color: rgba(251, 233, 231, 0.4);
}

.issue-item.error .issue-icon {
  color: #c62828;
}

.error-icon {
  color: #f44336;
}

/* Botones */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  padding: 0 10px;
}

.modal-actions .app-button {
  max-width: 120px;
  margin-top: 0;
}

/* Responsive */
@media (max-width: 600px) {
  .stat-item {
    min-width: calc(50% - 12px);
    padding: 12px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .detail-title {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .issue-item {
    padding: 10px 12px;
  }
  
  .issue-title {
    font-size: 0.85rem;
  }
}
</style>