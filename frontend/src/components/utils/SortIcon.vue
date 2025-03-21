<template>
  <span class="sort-icon" :class="{ 'active': currentSort === fieldName }">
    <font-awesome-icon :icon="['fas', currentSort === fieldName ? (currentOrder === 'asc' ? 'sort-up' : 'sort-down') : 'sort']" />
  </span>
</template>

<script setup>
defineProps({
  fieldName: {
    type: String,
    required: true
  },
  currentSort: {
    type: String,
    required: true
  },
  currentOrder: {
    type: String,
    required: true
  }
});
</script>

<style scoped>
.sort-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.8em;
  position: relative;
  top: 2px;
  margin-left: 5px;
  color: #ccc;
}

.sort-icon.active {
  color: #3498db;
}
</style>