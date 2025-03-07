<template>
  <div class="fullname-field">
    <label v-if="label" :for="id">
      {{ label.endsWith('*') ? label.slice(0, -1) : label }}
      <span v-if="label.endsWith('*')" class="required-asterisk">*</span>
    </label>
    <div class="input-container">
      <div v-if="icon" class="input-icon">
        <font-awesome-icon :icon="['fas', icon]" />
      </div>
      <input
        type="text"
        :id="id"
        :value="modelValue"
        @input="handleInput"
        :placeholder="placeholder"
        class="text-input"
        :class="{ 'has-icon': icon }"
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
    default: 'Nombre completo*'
  },
  placeholder: {
    type: String,
    default: 'Introduce tu nombre completo'
  },
  id: {
    type: String,
    default: 'fullname'
  },
  required: {
    type: Boolean,
    default: true
  },
  error: String,
  hint: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: 'user'
  }
});

const emit = defineEmits(['update:modelValue', 'input']);

const handleInput = (event) => {
  const value = event.target.value;
  emit('update:modelValue', value);
  emit('input', value);
};
</script>

<style scoped>
.fullname-field {
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

.required-asterisk {
  color: #ff7043;
  margin-left: 2px;
  font-weight: bold;
}

.input-container {
  position: relative;
  width: 100%;
}

.text-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 16px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  background-color: #f9f9f9;
  color: black;
}

.text-input.has-icon {
  padding-left: 40px;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #777;
  font-size: 16px;
}

.error {
  display: block;
  color: #e53935;
  font-size: 14px;
  margin-top: 6px;
  text-align: left;
  transition: all 0.2s ease;
}

.hint {
  display: block;
  color: #757575;
  font-size: 12px;
  margin-top: 6px;
  text-align: left;
}

.text-input::placeholder {
  color: #8b8b8b;
  opacity: 0.7;
}
</style>