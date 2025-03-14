<template>
  <div class="form-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="label.endsWith('*')" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div class="input-icon">
        <font-awesome-icon :icon="['fas', 'at']" />
      </div>
      <input
        type="text"
        :id="id"
        :value="modelValue"
        @input="handleInput"
        :placeholder="placeholder"
        class="text-input has-icon"
      />
    </div>
    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>

<script setup>
defineProps({
  modelValue: String,
  label: {
    type: String,
    default: 'Nombre de usuario*'
  },
  placeholder: {
    type: String,
    default: 'Elige un nombre de usuario'
  },
  id: {
    type: String,
    default: 'username'
  },
  error: String,
});

const emit = defineEmits(['update:modelValue', 'input']);

const handleInput = (event) => {
  const valueWithoutSpaces = event.target.value.replace(/\s/g, '');
  
  if (event.target.value !== valueWithoutSpaces) {
    event.target.value = valueWithoutSpaces;
  }
  emit('update:modelValue', valueWithoutSpaces);
  emit('input', valueWithoutSpaces);
};
</script>

<style scoped src="@/assets/styles/form_fields.css"></style>