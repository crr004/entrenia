<template>
  <div class="form-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="label.endsWith('*')" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div class="input-icon">
        <font-awesome-icon :icon="['fas', 'lock']" />
      </div>
      <input
        :type="showPassword ? 'text' : 'password'"
        :id="id"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :placeholder="placeholder"
        class="password-input has-icon"
      />
      <button
        type="button"
        class="visibility-toggle"
        @click="showPassword = !showPassword"
        aria-label="Mostrar/ocultar contraseña"
      >
        <font-awesome-icon :icon="showPassword ? ['fas', 'eye-slash'] : ['fas', 'eye']" />
      </button>
    </div>
    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  modelValue: String,
  label: {
    type: String,
    default: 'Contraseña*'
  },
  placeholder: {
    type: String,
    default: 'Introduce tu contraseña'
  },
  id: {
    type: String,
    default: 'password'
  },
  error: String
});

defineEmits(['update:modelValue']);

const showPassword = ref(false);
</script>

<style scoped src="@/assets/styles/form_fields.css"></style>