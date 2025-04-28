<template>
  <nav class="navbar">
    <div class="navbar-title">
      <router-link to="/">EntrenIA</router-link>
    </div>
    <div class="burger-menu" @click="toggleBurgerMenu">
      <div :class="['bar', {'active': burgerMenuOpen}]"></div>
      <div :class="['bar', {'active': burgerMenuOpen}]"></div>
      <div :class="['bar', {'active': burgerMenuOpen}]"></div>
    </div>
    <div :class="['nav-content', {'active': burgerMenuOpen}]">
      <div class="navbar-links">
        <router-link to="/" @click="closeBurgerMenu">Inicio</router-link>
        <span id="nav-separator" class="desktop-only"> | </span>
        <router-link to="/explore" @click="closeBurgerMenu">Explorar</router-link>
        <span id="nav-separator" class="desktop-only"> | </span>
        <router-link to="/about" @click="closeBurgerMenu">Sobre EntrenIA</router-link>
      </div>
      <div class="navbar-personal" v-if="!authStore.isAuthenticated">
        <span class="navbar-username" @click="handleLoginClick">Iniciar sesión</span>
        <span id="nav-separator" class="desktop-only"></span>
        <span class="navbar-username" id="register-button" @click="handleSignupClick">Registrarse</span>
      </div>
      <div class="navbar-personal" v-else>
        <div class="desktop-only user-container">
          <span class="navbar-username user-profile" @click="toggleUserDropdown">
            <font-awesome-icon :icon="['fas', 'user']" class="user-icon" />
            <span class="username-text">{{ displayName }}</span>
            <span v-if="isAdmin" class="admin-badge" title="Administrador">
              <font-awesome-icon :icon="['fas', 'crown']" />
            </span>
          </span>
          <UserDropdown v-if="isUserDropdownOpen" @close="closeUserDropdown" />
        </div>
        <div class="burger-only user-menu-burger">
          <hr>
          <div class="user-greeting-burger">
            <span class="username-burger">
              {{ displayName }}
              <span v-if="isAdmin" class="admin-badge-mobile">
                <font-awesome-icon :icon="['fas', 'crown']" /> Admin
              </span>
            </span>
          </div>
          <div class="user-links-burger">
            <router-link to="/my-models" @click="closeBurgerMenu" class="user-link-burger">
              <font-awesome-icon :icon="['fas', 'robot']" class="link-icon" fixed-width />
              Mis modelos
            </router-link>
            <router-link to="/my-datasets" @click="closeBurgerMenu" class="user-link-burger">
              <font-awesome-icon :icon="['fas', 'database']" class="link-icon" fixed-width />
              Mis conjuntos de imágenes
            </router-link>
            <router-link 
              v-if="isAdmin"
              to="/admin" 
              @click="closeBurgerMenu" 
              class="user-link-burger admin-link-mobile"
            >
              <font-awesome-icon :icon="['fas', 'shield-alt']" class="link-icon" fixed-width />
              Panel de administración
            </router-link>
            <router-link to="/account" @click="closeBurgerMenu" class="user-link-burger">
              <font-awesome-icon :icon="['fas', 'user-cog']" class="link-icon" fixed-width />
              Mi cuenta
            </router-link>
            <a href="#" @click.prevent="handleLogout" class="user-link-burger logout-link">
              <font-awesome-icon :icon="['fas', 'sign-out-alt']" class="link-icon" fixed-width />
              Cerrar sesión
            </a>
          </div>
        </div>
      </div>
    </div>
    <SignupModal 
      :isOpen="isSignupModalOpen"
      @close="closeSignupModal"
      @switchToLogin="switchToLogin"
    />
    <LoginModal 
      :isOpen="isLoginModalOpen"
      @close="closeLoginModal"
      @switchToSignup="switchToSignup"
      @switchToEnterEmailModal="switchToEnterEmailModal"
      @loginSuccess="loginSuccess"
    />
    <EnterEmailModal 
      :isOpen="isEnterEmailModalOpen"
      @close="closeEnterEmailModal"
    />
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

import { notifyError } from '@/utils/notifications';
import { useAuthStore } from '@/stores/authStore';
import SignupModal from '@/components/users/SignupModal.vue';
import LoginModal from '@/components/users/LoginModal.vue';
import EnterEmailModal from '@/components/users/EnterEmailModal.vue';
import UserDropdown from '@/components/general/UserDropdown.vue';


const router = useRouter();
const isSignupModalOpen = ref(false);
const isLoginModalOpen = ref(false);
const isEnterEmailModalOpen = ref(false);
const isUserDropdownOpen = ref(false);
const burgerMenuOpen = ref(false);
const authStore = useAuthStore();

const toggleBurgerMenu = () => {
  burgerMenuOpen.value = !burgerMenuOpen.value;
  
  if (!burgerMenuOpen.value) {
    isUserDropdownOpen.value = false;
  }
};

const closeBurgerMenu = () => {
  burgerMenuOpen.value = false;
};

const handleLoginClick = () => {
  toggleLoginModal();
  closeBurgerMenu();
};

const handleSignupClick = () => {
  toggleSignupModal();
  closeBurgerMenu();
};

const toggleSignupModal = () => {
  isSignupModalOpen.value = true;
  isLoginModalOpen.value = false; 
};

const toggleLoginModal = () => {
  isLoginModalOpen.value = true;
  isSignupModalOpen.value = false; 
};

const toggleUserDropdown = () => {
  isUserDropdownOpen.value = !isUserDropdownOpen.value;
};

const closeSignupModal = () => {
  isSignupModalOpen.value = false;
};

const closeLoginModal = () => {
  isLoginModalOpen.value = false;
};

const closeEnterEmailModal = () => {
  isEnterEmailModalOpen.value = false;
};

const closeUserDropdown = () => {
  isUserDropdownOpen.value = false;
};

const switchToLogin = () => {
  isSignupModalOpen.value = false;
  isLoginModalOpen.value = true;
};

const switchToSignup = () => {
  isLoginModalOpen.value = false;
  isSignupModalOpen.value = true;
};

const switchToEnterEmailModal = () => {
  isLoginModalOpen.value = false;
  isEnterEmailModalOpen.value = true;
};

// Función llamada cuando hay un inicio de sesión exitoso en el Login Modal.
// Esta función se encarga de obtener los datos del usuario autenticado y almacenarlos en el store de autenticación.
const loginSuccess = async () => {
  try{
    const response = await axios.get('/users/own');
    const user = response.data;
    authStore.setUser(user);
  } catch (error) {
    authStore.isAuthenticated = false;
    console.error('Error fetching user data after login: ', error);
    notifyError("Error inesperado", 
    "Ha ocurrido un error al iniciar sesión. Por favor, inténtalo de nuevo más tarde.");
  }
};

// Muestra el nombre del usuario/nombre completo en la barra de navegación.
const displayName = computed(() => {
  const user = authStore.user;
  if (!user) return 'Usuario';
  
  let name = user.full_name || user.username || 'Usuario';
  
  if (name.length > 40) {
    name = name.substring(0, 40) + '...';
  }
  
  return name;
});


// Esconder menús cuando se hace clic fuera de ellos.
// Los menús son: el menú desplegable de usuario y el menú de hamburguesa (este último solo aparece cuando la ventana es pequeña).
const handleClickOutside = (event) => {
  const profileElement = document.querySelector('.user-profile');
  const dropdownElement = document.querySelector('.user-dropdown-container');
  const burgerMenu = document.querySelector('.burger-menu');
  
  if (
    isUserDropdownOpen.value &&
    (!profileElement || !profileElement.contains(event.target)) &&
    (!dropdownElement || !dropdownElement.contains(event.target))
  ) {
    isUserDropdownOpen.value = false;
  }
  
  if (
    burgerMenuOpen.value &&
    (!burgerMenu || !burgerMenu.contains(event.target)) &&
    event.target.closest('.nav-content') === null
  ) {
    burgerMenuOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

// El cierre de sesión elimina el usuario del store de autenticación y redirige a la página de inicio.
const handleLogout = () => {
  authStore.logout();
  closeBurgerMenu();
  router.push('/');
};

const isAdmin = computed(() => {
  return authStore.user && authStore.user.is_admin === true;
});
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100vw;
  max-height: 70px;
  box-sizing: border-box;
  border-bottom: 1px solid #b4b4b4;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  background-color: #FFFDF5;
  z-index: 100;
}

.navbar-title a {
  margin-left: 10px;
  color: black;
  font-weight: bold;
  text-decoration: none;
  font-size: 2em;
}

.navbar-title a:hover {
  text-shadow: 0 0 10px rgba(77, 182, 172, 0.8);
  transform: scale(1.05);
}

.nav-content {
  display: flex;
  align-items: center;
  flex-grow: 1;
  justify-content: space-between;
}

.navbar-links {
  justify-content: center;
  margin-left: 30px;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.navbar-links a {
  color: black;
  margin: 0 5px;
  text-decoration: none;
  padding: 2px 5px;
  font-size: 1.15em;
  font-weight: 500;
}

.navbar-links a.router-link-exact-active {
  color: rgb(34, 134, 141);
}


.navbar-personal {
  margin-left: auto;
  margin-right: 10px;
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.navbar-username {
  color: white;
  background-color: #555;
  padding: 5px 10px;
  border-radius: 5px;
  text-decoration: none;
  font-size: 1.3em;
  display: flex;
  align-items: center;
  cursor: pointer;
  margin: 0 5px;
}

.username-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 350px;
}

#register-button {
  background-color: rgb(34, 134, 141);
}

#nav-separator {
  margin: 0 7px;
  color: #b4b4b4;
}

.admin-badge {
  display: inline-flex;
  margin-left: 5px;
  color: gold;
  font-size: 0.8em;
  flex-shrink: 0;
}

.admin-badge-mobile {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  color: gold;
  font-size: 0.9em;
  background-color: rgba(0, 0, 0, 0.5);
  padding: 2px 6px;
  border-radius: 4px;
}

.user-icon {
  margin-right: 8px;
}

/* Menú hamburguesa */
.burger-menu {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 30px;
  height: 21px;
  cursor: pointer;
  z-index: 110;
}

.bar {
  height: 3px;
  width: 100%;
  background-color: #333;
  border-radius: 10px;
  transition: all 0.3s ease-in-out;
}

.burger-menu .bar.active:nth-child(1) {
  transform: translateY(9px) rotate(45deg);
}

.burger-menu .bar.active:nth-child(2) {
  opacity: 0;
}

.burger-menu .bar.active:nth-child(3) {
  transform: translateY(-9px) rotate(-45deg);
}

.user-menu-burger {
  width: 100%;
  display: flex;
  flex-direction: column;
  margin-top: 15px;
}

.user-greeting-burger {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 15px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.username-burger {
  color: black;
  font-size: 16px;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 10px;
}

.user-links-burger {
  display: flex;
  flex-direction: column;
  width: 100%;
  font-weight: 500;
  align-items: center;
}

.user-link-burger {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  margin-bottom: 8px;
  color: black;
  text-decoration: none;
  border-radius: 6px;
  font-size: 16px;
}

.user-link-burger:hover {
  background-color: rgba(245, 235, 204, 0.7);
}

.link-icon {
  margin-right: 10px;
  width: 20px;
  text-align: center;
}

hr {
  border: 0;
  border-top: 1px solid #666;
  margin: 8px 0;
}

/* Visibilidad */
.desktop-only {
  display: inline-block;
}

.burger-only {
  display: none;
}

/* Responsive */
@media (min-width: 769px) {
  .navbar-links a {
    transition: background-color 0.2s, color 0.2s;
  }

  .navbar-links a:hover {
    background-color: rgba(245, 235, 204, 0.4);
    border-radius: 4px;
  }

  .navbar-username {
    transition: transform 0.2s ease;
  }

  .navbar-username:hover {
    transform: scale(1.05);
  }
  
  .burger-only {
    display: none;
  }
}

/* Pantallas/Ventanas medianas */
@media (min-width: 769px) and (max-width: 1024px) {
  .navbar-username {
    font-size: 1em;
    max-width: 150px;
  }
  
  .username-text {
    max-width: 120px;
  }
  
  .navbar-links a {
    font-size: 1em;
  }
}

/* Pantallas/Ventanas pequeñas */
@media (max-width: 768px) {
  .navbar {
    padding: 10px;
    will-change: contents; 
  }
  
  .navbar-title a {
    margin-left: 0;
    font-size: 1.5em;
  }
  
  .burger-menu {
    display: flex;
  }
  
  .nav-content {
    position: fixed;
    top: 47px;
    left: 0;
    right: 0;
    background-color: #FFFDF5;
    flex-direction: column;
    align-items: stretch;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transform: translateY(-100vh);
    transition: transform 0.3s ease-in-out;
    z-index: 90;
    border-top: 1px solid #b4b4b4;
  }
  
  .nav-content.active {
    transform: translateY(0);
    height: auto;
    max-height: calc(100vh - 70px);
    overflow-y: auto;
  }
  
  .navbar-links {
    margin: 0 0 20px 0;
    flex-direction: column;
    align-items: center;
  }
  
  .navbar-links a {
    margin: 10px 0;
    font-size: 1.2em;
    width: 100%;
    text-align: center;
    padding: 10px;
    background-color: transparent;
  }
  
  .navbar-links a:hover {
    background-color: rgba(245, 235, 204, 0.7);
    border-radius: 4px;
  }
  
  .navbar-personal {
    margin: 0;
    flex-direction: column;
    width: 100%;
  }
  
  .navbar-username {
    margin: 5px 0;
    width: 100%;
    text-align: center;
    padding: 10px;
    max-width: none;
    display: flex;
    justify-content: center;
  }
  
  .navbar-username:hover {
    background-color: rgba(85, 85, 85, 0.9);
  }
  
  .desktop-only {
    display: none;
  }
  
  .burger-only {
    display: block;
  }
  
  .user-dropdown-container {
    position: fixed;
    top: auto;
    right: 0;
    left: 0;
    width: 100%;
    margin: 0;
    border-radius: 0;
  }

  #register-button:hover {
    background-color: #3da59b;
  }
}
</style>
