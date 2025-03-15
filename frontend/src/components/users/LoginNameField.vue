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
        @input="$emit('update:modelValue', $event.target.value)"
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
    default: 'Nombre de usuario o correo electrónico*'
  },
  placeholder: {
    type: String,
    default: 'Introduce tu nombre o correo'
  },
  id: {
    type: String,
    default: 'loginname'
  },
  error: String
});

defineEmits(['update:modelValue']);
</script>

<style scoped src="@/assets/styles/form_fields.css"></style>