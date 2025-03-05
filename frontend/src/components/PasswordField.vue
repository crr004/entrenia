<template>
  <div class="password-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="label.endsWith('*')" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div v-if="true" class="input-icon">
        <font-awesome-icon :icon="['fas', 'lock']" />
      </div>
      <input
        :type="showPassword ? 'text' : 'password'"
        :id="id"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :placeholder="placeholder"
        :required="required"
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
  label: String,
  placeholder: String,
  id: {
    type: String,
    default: 'password'
  },
  required: {
    type: Boolean,
    default: false
  },
  error: String
});

defineEmits(['update:modelValue']);

const showPassword = ref(false);
</script>

<style scoped>
.password-field {
  margin-bottom: 20px;
  width: 100%;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  text-align: left;
  color: #333;
  transition: color 0.2s ease;
}

.input-container {
  position: relative;
  width: 100%;
}

.password-input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 16px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  background-color: #f9f9f9;
  color: black;
}

.password-input.has-icon {
  padding-left: 40px;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #777;
  font-size: 16px;
  z-index: 1;
}

.visibility-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #777;
  padding: 5px;
  font-size: 16px;
  transition: color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error {
  display: block;
  color: #e53935;
  font-size: 14px;
  margin-top: 6px;
  text-align: left;
  transition: all 0.2s ease;
}

.password-input::placeholder {
  color: #8b8b8b;
  opacity: 0.7;
}

.required-asterisk {
  color: #ff7043;
  margin-left: 2px;
  font-weight: bold;
}
</style>