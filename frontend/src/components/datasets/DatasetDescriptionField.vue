<template>
  <div class="form-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="required" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <textarea
        :id="id"
        :value="modelValue"
        @input="handleInput"
        :placeholder="placeholder"
        :maxlength="maxLength"
        class="text-input textarea"
        :class="{ 'input-error': error }"
        rows="4"
      ></textarea>
    </div>
    <div class="field-footer">
      <span v-if="error" class="error">{{ error }}</span>
      <div v-else class="description-info">
        <span class="char-counter">{{ (modelValue || '').length }}/{{ maxLength }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: String,
  error: String,
  label: {
    type: String,
    default: 'Descripción'
  },
  placeholder: {
    type: String,
    default: 'Describe el contenido y propósito de este conjunto de imágenes...'
  },
  id: {
    type: String,
    default: 'dataset-description'
  },
  maxLength: {
    type: Number,
    default: 1000
  },
  required: {
    type: Boolean,
    default: false
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
<style scoped>
.field-footer {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 5px;
}

.description-info {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.char-counter {
  color: #6c757d;
  font-size: 0.8rem;
  text-align: right;
}

.textarea {
  resize: vertical;
  min-height: 100px;
  padding-top: 8px;
  line-height: 1.5;
  font-family: inherit;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 15px;
  color: #6c757d;
}

.input-container {
  position: relative;
  width: 100%;
}
</style>