<template>
  <div class="form-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="required" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div class="input-icon">
        <font-awesome-icon :icon="['fas', 'image']" />
      </div>
      <input
        type="text"
        :id="id"
        :value="modelValue"
        @input="handleInput"
        :placeholder="placeholder"
        class="text-input has-icon"
        :class="{ 'input-error': error }"
        :maxlength="maxLength"
      />
    </div>
    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>

<script setup>
defineProps({
  modelValue: String,
  error: String,
  label: {
    type: String,
    default: 'Nombre'
  },
  placeholder: {
    type: String,
    default: 'Introduce un nombre para la imagen'
  },
  id: {
    type: String,
    default: 'image-name'
  },
  required: {
    type: Boolean,
    default: true
  },
  maxLength: {
    type: Number,
    default: 255
  }
});

const emit = defineEmits(['update:modelValue', 'input']);

const handleInput = (event) => {
  const value = event.target.value;
  emit('update:modelValue', value);
  emit('input', value);
};
</script>

<style scoped src="@/assets/styles/form_fields.css"></style>