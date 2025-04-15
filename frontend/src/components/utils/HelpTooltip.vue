<template>
  <div class="help-tooltip-container">
    <font-awesome-icon 
      :icon="['fas', 'circle-question']" 
      class="help-icon" 
      @mouseenter="showTooltip = true"
      @mouseleave="showTooltip = false"
      :aria-label="`Ayuda sobre ${label}`"
      role="img"
      tabindex="0"
      @focus="showTooltip = true"
      @blur="showTooltip = false"
    />
    <div 
      v-if="showTooltip" 
      class="tooltip-content"
      :class="{ 'tooltip-visible': showTooltip }"
      ref="tooltipRef"
    >
      <div class="tooltip-arrow"></div>
      <div class="tooltip-text">{{ text }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

const props = defineProps({
  text: {
    type: String,
    required: true
  },
  label: {
    type: String,
    default: 'este parámetro'
  }
});

const showTooltip = ref(false);
const helpIconRef = ref(null);
const tooltipRef = ref(null);

const toggleTooltip = () => {
  showTooltip.value = !showTooltip.value;
};

const closeTooltipOnClickOutside = (event) => {
  if (showTooltip.value && 
      helpIconRef.value && 
      !helpIconRef.value.contains(event.target) && 
      tooltipRef.value && 
      !tooltipRef.value.contains(event.target)) {
    showTooltip.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', closeTooltipOnClickOutside);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && showTooltip.value) {
      showTooltip.value = false;
    }
  });
});

onBeforeUnmount(() => {
  document.removeEventListener('click', closeTooltipOnClickOutside);
});
</script>

<style scoped>
.help-tooltip-container {
  position: relative;
  display: inline-block;
  margin-left: 4px;
  vertical-align: text-top;
}

.help-icon {
  color: rgb(73, 124, 255);
  font-size: 0.85rem;
  cursor: help;
  transition: color 0.2s;
}

.help-icon:hover {
  color: rgb(50, 96, 230);
}

.tooltip-content {
  position: absolute;
  z-index: 100;
  width: 250px;
  background-color: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  padding: 12px;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.85rem;
  color: #444;
  line-height: 1.4;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
  pointer-events: none;
}

.tooltip-visible {
  opacity: 1;
  visibility: visible;
}

.tooltip-arrow {
  position: absolute;
  width: 10px;
  height: 10px;
  background-color: white;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  box-shadow: 2px 2px 3px rgba(0, 0, 0, 0.1);
}

.tooltip-text {
  position: relative;
  z-index: 1;
}
</style>