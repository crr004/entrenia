<template>
  <div class="form-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="label.endsWith('*')" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div class="input-icon">
        <font-awesome-icon :icon="['fas', 'user']" />
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
    default: 'Nombre completo'
  },
  placeholder: {
    type: String,
    default: 'Introduce tu nombre completo'
  },
  id: {
    type: String,
    default: 'fullname'
  },
  error: String,
});

const emit = defineEmits(['update:modelValue', 'input']);

const handleInput = (event) => {
  const value = event.target.value;
  emit('update:modelValue', value);
  emit('input', value);
};
</script>

<style scoped src="@/assets/styles/form_fields.css"></style>