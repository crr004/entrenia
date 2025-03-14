<template>
  <div class="form-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="label.endsWith('*')" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div class="input-icon">
        <font-awesome-icon :icon="['fas', 'envelope']" />
      </div>
      <input
        type="text"
        inputmode="email"
        autocomplete="email"
        :id="id"
        :value="modelValue"
        @input="handleInput"
        :placeholder="placeholder"
        aria-label="Email address"
        class="text-input has-icon"
        :disabled="disabled"
        :class="['text-input has-icon', { 'disabled': disabled }]"
      />
    </div>
    <span v-if="error" class="error">{{ error }}</span>
    <span v-if="hint" class="hint">{{ hint }}</span>
  </div>
</template>

<script setup>
defineProps({
  modelValue: String,
  label: {
    type: String,
    default: 'Correo electrónico*'
  },
  placeholder: {
    type: String,
    default: 'Introduce tu correo electrónico'
  },
  id: {
    type: String,
    default: 'email'
  },
  hint: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
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