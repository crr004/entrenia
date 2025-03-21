<template>
  <div class="account-view">
    <h1 class="account-title">Mi Cuenta</h1>
    <div class="account-content">
      <div class="sidebar">
        <div 
          :class="['sidebar-tab', { active: activeTab === 'profile' }]" 
          @click="activeTab = 'profile'"
        >
          <font-awesome-icon :icon="['fas', 'user']" fixed-width />
          <span class="tab-text">Mis datos</span>
        </div>
        <div 
          :class="['sidebar-tab', { active: activeTab === 'password' }]" 
          @click="activeTab = 'password'"
        >
          <font-awesome-icon :icon="['fas', 'key']" fixed-width />
          <span class="tab-text">Mi contraseña</span>
        </div>
        <div 
          :class="['sidebar-tab danger-tab', { active: activeTab === 'danger' }]" 
          @click="activeTab = 'danger'"
        >
          <font-awesome-icon :icon="['fas', 'exclamation-triangle']" fixed-width />
          <span class="tab-text">Zona de peligro</span>
        </div>
      </div>
      <div class="main-content">
        <div v-if="activeTab === 'profile'" class="tab-content profile-tab">
          <h2>Mis datos personales</h2>
          <p>Aquí puedes ver y actualizar la información de tu cuenta.</p>
          <div class="profile-form">
            <EmailField
              label="Correo electrónico"
              v-model="email"
              :error="emailError"
              id="email"
              placeholder=""
              :disabled="true"
              hint="El correo electrónico no se puede modificar."
            />
            <FullNameField
              placeholder="Aún no has indicado tu nombre completo"
              v-model="fullName"
              :error="fullNameError"
              @input="validateFullName"
            />
            <UsernameField
              label="Nombre de usuario"
              placeholder=""
              v-model="username"
              :error="usernameError"
              @input="validateUsername"
            />
            <div class="button-container">
              <button class="app-button" @click="updateProfile" :disabled="isLoading || !hasProfileChanges">
                <font-awesome-icon v-if="isLoading" :icon="['fas', 'circle-notch']" spin class="button-icon" />
                Guardar cambios
              </button>
            </div>
          </div>
        </div>
        <div v-if="activeTab === 'password'" class="tab-content password-tab">
          <h2>Cambiar mi contraseña</h2>
          <p>Aquí puedes modificar tu contraseña de acceso.</p>
          <div class="password-form">
            <PasswordField
              id="current-password"
              label="Contraseña actual"
              placeholder="Introduce tu contraseña actual"
              v-model="currentPassword"
              :error="currentPasswordError"
              @input="validateCurrentPassword"
            />
            <PasswordField
              id="new-password"
              label="Nueva contraseña"
              placeholder="Introduce tu nueva contraseña"
              hint="La contraseña debe tener al menos 8 caracteres."
              v-model="newPassword"
              :error="newPasswordError"
              @input="validateNewPassword"
            />
            <PasswordField
              id="confirm-new-password"
              label="Confirmar nueva contraseña"
              placeholder="Repite tu nueva contraseña"
              v-model="confirmNewPassword"
              :error="confirmPasswordError"
              @input="validateConfirmPassword"
            />
            <div class="button-container">
              <button class="app-button" @click="changePassword" :disabled="isLoading">
                <font-awesome-icon v-if="isLoading" :icon="['fas', 'circle-notch']" spin class="button-icon" />
                Cambiar contraseña
              </button>
            </div>
          </div>
        </div>
        <div v-if="activeTab === 'danger'" class="tab-content danger-tab">
          <h2>Zona de peligro</h2>
          <p>Esta sección contiene acciones irreversibles que pueden eliminar tus datos permanentemente.</p>
          <div class="danger-box">
            <h3>Eliminar mi cuenta</h3>
            <p>
              Al eliminar tu cuenta, perderás permanentemente todos tus datos, incluyendo:
            </p>
            <ul class="danger-list">
              <li>Tu perfil y preferencias personales</li>
              <li>Todo tu historial y registros</li>
              <li>Cualquier contenido que hayas creado</li>
            </ul>
            <p class="warning-text">Esta acción no se puede deshacer.</p>
            <div v-if="!showDeleteConfirmation" class="danger-action">
              <button class="delete-button" @click="showDeleteConfirmation = true">
                <font-awesome-icon :icon="['fas', 'trash-alt']" class="button-icon" />
                Eliminar mi cuenta
              </button>
            </div>
            <div v-else class="delete-confirmation">
              <p><strong>Confirma que deseas eliminar tu cuenta</strong></p>
              <p>Para confirmar, escribe "ELIMINAR" en el campo de abajo:</p>
              <div class="form-field">
                <label for="delete-confirmation">Confirmación</label>
                <div class="input-container">
                  <div class="input-icon danger-icon">
                    <font-awesome-icon :icon="['fas', 'exclamation-triangle']" />
                  </div>
                  <input
                    type="text"
                    id="delete-confirmation"
                    v-model="deleteConfirmationText"
                    placeholder="Escribe ELIMINAR"
                    class="text-input has-icon"
                  />
                </div>
                <span class="hint danger-hint">Debes escribir exactamente "ELIMINAR" para confirmar.</span>
              </div>
              <div class="confirmation-actions">
                <button class="cancel-button" @click="cancelDeleteAccount">
                  Cancelar
                </button>
                <button 
                  class="delete-button" 
                  :disabled="deleteConfirmationText !== 'ELIMINAR'"
                  @click="deleteAccount"
                >
                  <font-awesome-icon v-if="isLoading" :icon="['fas', 'circle-notch']" spin class="button-icon" />
                  Confirmar eliminación
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifyError, notifySuccess, notifyInfo } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import { userValidationRegex } from '@/utils/validations.js';
import EmailField from '@/components/users/EmailField.vue';
import UsernameField from '@/components/users/UsernameField.vue';
import FullNameField from '@/components/users/FullNameField.vue';
import PasswordField from '@/components/users/PasswordField.vue';


const router = useRouter();
const authStore = useAuthStore();

const activeTab = ref('profile');

const email = ref('');
const fullName = ref('');
const username = ref('');

const emailError = ref('');
const fullNameError = ref('');
const usernameError = ref('');

const currentPassword = ref('');
const newPassword = ref('');
const confirmNewPassword = ref('');

const currentPasswordError = ref('');
const newPasswordError = ref('');
const confirmPasswordError = ref('');

const showDeleteConfirmation = ref(false);
const deleteConfirmationText = ref('');

const isLoading = ref(false);

const originalFullName = ref('');
const originalUsername = ref('');

const hasProfileChanges = computed(() => {
  return fullName.value !== originalFullName.value || 
         username.value !== originalUsername.value;
});

const validateFullName = () => {
  // El nombre completo es opcional, por lo que es válido si está vacío.
  if (!fullName.value) {
    fullNameError.value = '';
    return;
  }
  
  const nameRegex = userValidationRegex.fullname;
  if (!nameRegex.test(fullName.value)) {
    fullNameError.value = 'El nombre completo contiene caracteres inválidos.';
    return false;
  } else if(fullName.value.length > 75) {
    fullNameError.value = 'El nombre completo no puede tener más de 75 caracteres.';
    return false;
  }
  
  fullNameError.value = '';
  return true;
};

const validateUsername = () => {
  if (!username.value) {
    usernameError.value = 'El nombre de usuario es obligatorio.';
    return false;
  }
  
  const usernameRegex = userValidationRegex.username;
  if (!usernameRegex.test(username.value)) {
    usernameError.value = 'Solo letras minúsculas, números y guiones bajos. Debe contener al menos 3 letras.';
    return false;
  } else if (username.value.length > 20) {
    usernameError.value = 'El nombre de usuario no puede tener más de 20 caracteres.';
    return false;
  }
  
  usernameError.value = '';
  return true;
};

const validateCurrentPassword = () => {
  if (!currentPassword.value) {
    currentPasswordError.value = 'Debes introducir tu contraseña actual.';
    return false;
  }
  currentPasswordError.value = '';
  return true;
};

const validateNewPassword = () => {
  if (!newPassword.value) {
    newPasswordError.value = 'Debes introducir una nueva contraseña.';
    return false;
  }
  
  if (newPassword.value.length < 9) {
    newPasswordError.value = 'La contraseña debe tener al menos 9 caracteres.';
    return false;
  } else if(newPassword.value.length > 50) {
    newPasswordError.value = 'La contraseña no puede tener más de 50 caracteres.';
    return false;
  } 
  
  if (newPassword.value === currentPassword.value) {
    newPasswordError.value = 'La nueva contraseña no puede ser igual a la actual.';
    return false;
  }
  
  newPasswordError.value = '';
  return true;
};

const validateConfirmPassword = () => {
  if (!confirmNewPassword.value) {
    confirmPasswordError.value = 'Debes confirmar tu nueva contraseña.';
    return false;
  }
  
  if (confirmNewPassword.value !== newPassword.value) {
    confirmPasswordError.value = 'Las contraseñas no coinciden.';
    return false;
  }
  
  confirmPasswordError.value = '';
  return true;
};

const fetchUserData = async () => {
  isLoading.value = true;
  
  const hasToken = !!localStorage.getItem('token') || !!authStore.token;
  if(hasToken){
    authStore.setAuthHeader();
  }
  
  try {
    const response = await axios.get('/users/own');
    email.value = response.data.email;
    fullName.value = response.data.full_name || '';
    username.value = response.data.username;
    
    originalFullName.value = fullName.value;
    originalUsername.value = username.value;
  } catch (error) {
    console.error('Error while loading user data: ', error);
    
    if (error.response && error.response.status === 401) {
      if (hasToken) {
        handleApiError(error);
      } else {
        console.error('Unauthorized access, redirecting to home page...');
        router.push('/');
        return;
      }
    } else {
      handleApiError(error);
    }
  } finally {
    isLoading.value = false;
  }
};

const updateProfile = async () => {
  if (!hasProfileChanges.value) {
    return;
  }
  
  validateFullName();
  validateUsername();
  
  if (fullNameError.value || usernameError.value) {
    return;
  }
  
  const userData = {};
  if (fullName.value !== originalFullName.value) userData.full_name = fullName.value;
  if (username.value !== originalUsername.value) userData.username = username.value;
  
  isLoading.value = true;
  try {
    const response = await axios.patch('/users/own', userData);
    fullName.value = response.data.full_name || '';
    username.value = response.data.username;
    
    originalFullName.value = fullName.value;
    originalUsername.value = username.value;
    
    const currentUser = authStore.user ? { ...authStore.user } : {};
    const updatedUser = {
      ...currentUser,
      full_name: fullName.value,
      username: username.value
    };
    authStore.setUser(updatedUser);
    
    notifySuccess("Datos actualizados", 
    "Tus datos se han actualizado con éxito.");
  } catch (error) {
    console.error('Error while updating data: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

const changePassword = async () => {
  const isCurrentValid = validateCurrentPassword();
  const isNewValid = validateNewPassword();
  const isConfirmValid = validateConfirmPassword();
  
  if (!isCurrentValid || !isNewValid || !isConfirmValid) {
    return;
  }
  
  isLoading.value = true;
  try {
    await axios.patch('/users/own/password', {
      current_password: currentPassword.value,
      new_password: newPassword.value
    });
    
    currentPassword.value = '';
    newPassword.value = '';
    confirmNewPassword.value = '';
    
    notifySuccess("Contraseña modificada", 
    "Tu contraseña se ha modificado con éxito.");
  } catch (error) {
    console.error('Error while changing password: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

const cancelDeleteAccount = () => {
  showDeleteConfirmation.value = false;
  deleteConfirmationText.value = '';
};

const deleteAccount = async () => {
  if (deleteConfirmationText.value !== 'ELIMINAR') {
    return;
  }
  
  isLoading.value = true;
  try {
    await axios.delete('/users/own');
    
    authStore.logout();
    
    notifySuccess("Cuenta eliminada", 
    "Tu cuenta ha sido eliminada permanentemente.");
    router.push('/');
  } catch (error) {
    console.error('Error while deleting account: ', error);
    handleApiError(error);
  } finally {
    isLoading.value = false;
  }
};

const handleApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;

    console.error("Error response: ", data);
    
    switch (status) {
      case 400:
        if (data.detail === 'Incorrect password') {
          currentPasswordError.value = 'La contraseña actual es incorrecta.';
        } else if (data.detail === 'New password cannot be the same as the current one') {
          newPasswordError.value = 'La nueva contraseña no puede ser igual a la actual.';
        } else if (data.detail === 'The full name field has invalid characters') {
          fullNameError.value = 'El nombre completo contiene caracteres no válidos.';
        } else if (data.detail.includes('username can only contain')) {
          usernameError.value = 'El nombre de usuario solo puede contener letras minúsculas, números y guiones bajos, y debe tener al menos 3 letras.';
        } else {
          notifyError("Error de validación", 
          "Ha ocurrido un error de validación.");
        }
        break;
        
      case 409:
        if (data.detail.includes('username already exists')) {
          usernameError.value = 'Este nombre de usuario ya está en uso.';
        } else {
          notifyError("Conflicto", 
          "Los datos ya existen en el sistema.");
        }
        break;
        
      case 403:
        if(data.detail.includes("Admins")){
          notifyError("Acción denegada", 
          "Los administradores no pueden eliminarse a sí mismos.");
        } else if(data.detail.includes("credentials")){
          notifyInfo("Sesión expirada", 
          "Por favor, inicia sesión de nuevo.");
          authStore.logout();
          router.push('/');
        } else{
          notifyError("Acceso denegado", 
          "No tienes permiso para realizar esta acción.");
        }
        break;
      
      case 422:
        notifyError("Error de validación", 
        "Los datos proporcionados no son válidos. Por favor, verifica la información ingresada.");
        break;
        
      case 404:
        notifyError("Usuario no encontrado", 
        "El usuario no existe en el sistema.");
        authStore.logout();
        router.push('/');
        break;
        
      default:
        notifyError("Error en el servidor", 
        "No se pudo procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.");
        break;
    }
  } else if (error.request) {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  } else {
    notifyError("Error inesperado", 
    "Ha ocurrido un problema.");
  }
};

// Cargar datos del usuario al montar el componente.
onMounted(async () => {
  await fetchUserData();
});
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped src="@/assets/styles/form_fields.css"></style>
<style scoped>
.account-view {
  padding: 20px 40px;
  max-width: 1200px; 
  margin: 0 auto; 
  padding-top: 90px; 
  padding-bottom: 40px;
}

.account-title {
  margin-bottom: 30px;
  font-size: 28px;
  font-weight: 600;
  color: black;
}

.account-content {
  display: flex;
  gap: 30px;
  height: auto;
}

.sidebar {
  min-width: 220px;
  width: 220px;
  height: fit-content;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-tab {
  padding: 14px 16px;
  cursor: pointer;
  transition: transform 0.15s ease;
  display: flex;
  align-items: center;
  border-radius: 6px;
  background-color: #f0eee6;
  position: relative;
  overflow: hidden;
}

.sidebar-tab:hover {
  background-color: #f0eee6;
  transform: translateX(3px);
}

.sidebar-tab.active {
  background-color: #f0eee6;
  font-weight: 500;
  border-left: 4px solid #4db6ac;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.sidebar-tab.active, 
.sidebar-tab {
  will-change: transform, font-weight, border-left;
}

.tab-text {
  margin-left: 12px;
}

.danger-tab {
  color: #d32f2f;
}

.main-content {
  flex: 1;
  max-width: calc(100% - 250px);
  background-color: #FFFDF5;
  border-radius: 8px;
  padding: 25px 30px;
}

.tab-content {
  max-width: 100%;
}

.tab-content h2 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #333;
  font-size: 22px;
  border-bottom: 1px solid #eaeaea;
  padding-bottom: 10px;
}

.tab-content p {
  color: #666;
  margin-bottom: 20px;
}

.profile-form,
.password-form {
  max-width: 500px;
}

.button-icon {
  margin-right: 8px;
}

.button-container {
  margin-top: 50px;
}

.danger-box {
  border: 1px solid #ffcdd2;
  background-color: rgba(255, 235, 238, 0.5);
  border-radius: 8px;
  padding: 24px;
  margin-top: 20px;
  max-width: 600px;
}

.danger-box h3 {
  color: #d32f2f;
  margin-top: 0;
  font-size: 18px;
  font-weight: 600;
}

.danger-list {
  margin: 16px 0;
  padding-left: 20px;
}

.danger-list li {
  margin-bottom: 8px;
  color: #555;
}

.warning-text {
  color: #d32f2f;
  font-weight: 500;
  margin: 20px 0;
}

.delete-confirmation {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ffcdd2;
}

.confirmation-actions {
  display: flex;
  margin-top: 20px;
}

.danger-icon {
  color: #d32f2f;
}

.danger-input {
  border-color: #ffcdd2;
}

.danger-input:focus {
  border-color: #d32f2f;
}

.danger-hint {
  color: #d32f2f;
  font-weight: 500;
}

.form-field input.has-icon:focus {
  border-color: #d32f2f;
  box-shadow: 0 0 0 1px rgba(211, 47, 47, 0.25);
}

/* Responsive */
@media (max-width: 768px) {
  .account-view {
    padding: 15px;
    padding-top: 80px;
  }
  
  .main-content {
    max-width: 100%;
  }
  
  .account-title {
    font-size: 24px;
    margin-bottom: 20px;
  }
  
  .account-content {
    flex-direction: column;
    gap: 15px;
  }
  
  .sidebar {
    width: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 8px;
  }
  
  .sidebar-tab {
    flex: 1 0 auto;
    min-width: 110px;
    padding: 10px;
    text-align: center;
    justify-content: center;
  }
  
  .sidebar-tab.active {
    border-left: none;
    border-bottom: 3px solid #4db6ac;
  }
  
  .tab-text {
    font-size: 0.9rem;
  }
  
  .main-content {
    padding: 15px 20px;
  }
}

/* Para pantallas/ventanas pequeñas */
@media (max-width: 480px) {
  .sidebar {
    flex-direction: column;
  }
  
  .sidebar-tab {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>