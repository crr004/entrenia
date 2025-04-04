<template>
  <Teleport to="body">
    <div 
      class="action-menu-portal" 
      :style="menuStyle"
      ref="actionMenuRef"
      v-show="isVisible"
    >
      <div class="menu-items">
        <button 
          v-for="(action, index) in actions"
          :key="index"
          class="menu-item" 
          :class="action.class" 
          @click="handleAction(action.event)"
        >
          <font-awesome-icon :icon="action.icon" fixed-width />
          {{ action.label }}
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted, ref, reactive, watch } from 'vue';

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  itemId: {
    type: String,
    required: true
  },
  position: {
    type: Object,
    default: () => ({ top: true, right: true })
  },
  actions: {
    type: Array,
    default: () => [
      { 
        label: 'Editar', 
        event: 'edit', 
        icon: ['fas', 'edit'], 
        class: 'edit' 
      },
      { 
        label: 'Eliminar', 
        event: 'delete', 
        icon: ['fas', 'trash-alt'], 
        class: 'delete' 
      }
    ]
  }
});

// Definir emisiones para todos los posibles eventos.
const emit = defineEmits(['edit', 'delete', 'view', 'share', 'download']);

// Función para manejar cualquier acción de las que haya en el menú.
const handleAction = (eventName) => {
  emit(eventName, props.item);
};

const actionMenuRef = ref(null);
const isVisible = ref(false);

// Calcular la posición del menú basándose en el elemento que lo abre.
const menuStyle = reactive({
  position: 'fixed',
  top: '0px',
  left: '0px',
  zIndex: 9999,
  opacity: 0, // Inicialmente invisible (para el cálculo de dimensiones).
});

// Posicionar el menú según en el botón que lo activó.
const updateMenuPosition = () => {
  isVisible.value = false;
  
  // Pequeño timeout para asegurar que esté oculto primero.
  setTimeout(() => {
    // Usar itemId para identificar el botón que lo activó.
    const actionButton = document.querySelector(`.action-button[data-item-id="${props.itemId}"][data-active="true"]`);
    if (!actionButton) {
      console.warn('Button not found: ', props.itemId);
      return;
    }
    
    const buttonRect = actionButton.getBoundingClientRect();
    const menuElement = actionMenuRef.value;
    if (!menuElement) return;
    
    // Calcular posición con el menú invisible pero en el DOM.
    menuStyle.opacity = '0';
    
    // Precalcular el tamaño del menú sin esperar a que sea visible.
    const precalculatedHeight = menuElement.offsetHeight || 100;
    const precalculatedWidth = menuElement.offsetWidth || 150;
    
    // Calcular ajuste vertical basado en número de elementos.
    const itemHeight = 35; // Altura aproximada de cada elemento del menú.
    const numberOfItems = props.actions.length;
    const verticalAdjustment = numberOfItems > 2 ? (itemHeight * (numberOfItems - 2)) : 0;
    
    if (props.position.top) {
      menuStyle.top = `${buttonRect.top - precalculatedHeight + 20 - verticalAdjustment}px`;
    } else {
      menuStyle.top = `${buttonRect.bottom + 20}px`;
    }
    
    if (props.position.right) {
      menuStyle.left = `${buttonRect.right - precalculatedWidth}px`;
    } else {
      menuStyle.left = `${buttonRect.left - 30}px`;
    }
    
    // Ajustar si el menú se sale de la pantalla.
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Ajuste horizontal
    if (parseFloat(menuStyle.left) + precalculatedWidth > viewportWidth) {
      menuStyle.left = `${viewportWidth - precalculatedWidth - 10}px`;
    }
    
    if (parseFloat(menuStyle.left) < 10) {
      menuStyle.left = '10px';
    }
    
    // Ajuste vertical
    if (parseFloat(menuStyle.top) + precalculatedHeight > viewportHeight) {
      menuStyle.top = `${buttonRect.top - precalculatedHeight - 5}px`;
    }
    
    if (parseFloat(menuStyle.top) < 10) {
      menuStyle.top = `${buttonRect.bottom + 5}px`;
    }
    
    // Hacer visible el menú una vez posicionado.
    menuStyle.opacity = '1';
    isVisible.value = true;
  }, 5);
};

// Cerrar el menú cuando se hace clic fuera de él.
const handleClickOutside = (event) => {

  // Sin esto, se cerraría al hacer clic en el botón de acción (osea, se cierra en cuanto se abre).
  if (event.target.closest('.action-button')) {
    return;
  }
  
  if (actionMenuRef.value && !actionMenuRef.value.contains(event.target)) {
    emit('close');
  }
};

// Observar cambios en las props para reposicionar el menú si es necesario (responsive).
watch(() => props.position, () => {
  updateMenuPosition();
}, { deep: true });

watch(() => props.itemId, () => {
  updateMenuPosition();
});

onMounted(() => {
  document.addEventListener('click', handleClickOutside);

  // Pequeño retraso para dar tiempo a que el DOM se actualice.
  setTimeout(updateMenuPosition, 5);
  
  // Añadir listener para redimensionamiento de ventana (responsive).
  window.addEventListener('resize', updateMenuPosition);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', updateMenuPosition);
});
</script>

<style scoped>
.action-menu-portal {
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  min-width: 150px;
  border: 1px solid #eee;
  transition: opacity 0.1s ease-in-out;
}

.menu-items {
  display: flex;
  flex-direction: column;
}

.menu-item {
  background: none;
  border: none;
  padding: 10px 15px;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: #f5f5f5;
}

.menu-item svg {
  margin-right: 8px;
}

.menu-item {
  color: black;
}

.menu-item.delete {
  color: #e74c3c;
}
</style>