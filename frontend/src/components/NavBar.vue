<template>
  <nav class="navbar">
    <div class="navbar-title">
      <router-link to="/">EntrenIA</router-link>
    </div>
    <div class="navbar-links">
      <router-link to="/">Inicio</router-link>
      <span id="nav-separator"> | </span>
      <router-link to="/about">Sobre EntrenIA</router-link>
    </div>
    <div class="navbar-personal" v-if="!authStore.isAuthenticated">
      <span class="navbar-username" @click="toggleLoginModal">Iniciar sesión</span>
      <span id="nav-separator"></span>
      <span class="navbar-username" id="register-button" @click="toggleSignupModal">Registrarse</span>
    </div>
    <div class="navbar-personal" v-else>
      <span class="navbar-username user-profile">
        <font-awesome-icon :icon="['fas', 'user']" class="user-icon" />
        {{ displayName }}
      </span>
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
      @loginSuccess="loginSuccess"
    />
  </nav>
  
</template>

<script setup>
import { ref, computed } from 'vue';
import SignupModal from './SignupModal.vue';
import LoginModal from './LoginModal.vue';
import { useAuthStore } from '@/stores/authStore';
import axios from 'axios';

const isSignupModalOpen = ref(false);
const isLoginModalOpen = ref(false);
const authStore = useAuthStore();

const toggleSignupModal = () => {
  isSignupModalOpen.value = true;
  isLoginModalOpen.value = false; 
};

const toggleLoginModal = () => {
  isLoginModalOpen.value = true;
  isSignupModalOpen.value = false; 
};

const closeSignupModal = () => {
  isSignupModalOpen.value = false;
};

const closeLoginModal = () => {
  isLoginModalOpen.value = false;
};

const switchToLogin = () => {
  isSignupModalOpen.value = false;
  isLoginModalOpen.value = true;
};

const switchToSignup = () => {
  isLoginModalOpen.value = false;
  isSignupModalOpen.value = true;
};

const loginSuccess = async () => {
  try{
    const apiUrl = 'http://localhost:8000/api/users/own';

    const response = await axios.get(apiUrl);

    const user = response.data;
    authStore.setUser(user);
  } catch (error) {
    console.error('Error fetching user data:', error);
  }
};

const displayName = computed(() => {
  const user = authStore.user;
  if (!user) return 'Usuario';
  
  if (user.full_name) {
    return `${user.full_name}`;
  }
  
  return user.username || 'Usuario';
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
}

.navbar-title a{
  margin-left: 10px;
  color: black;
  font-weight: bold;
  text-decoration: none;
  font-size: 2em;
}

.navbar-title a:hover {
  color: black;
  text-shadow: 0 0 10px rgba(77, 182, 172, 0.8);
  transform: scale(1.05);
}

.navbar-links {
  justify-content: center;
  margin-left: 30px;
}

.navbar-links a {
  color: black;
  margin: 0 5px;
  text-decoration: none;
  padding: 2px 5px;
  font-size: 1.15em;
  font-weight: 500;
}

.navbar-links a:hover {
  background-color: rgba(245, 235, 204, 0.4);
  padding: 2px 5px;
  border-radius: 4px;
  margin: 0 5px;
}

.navbar-links a.router-link-exact-active {
  color: rgb(34, 134, 141);
}

.navbar-personal {
  margin-left: auto;
  margin-right: 10px;
}

.navbar-username {
  color: white;
  background-color: #555;
  padding: 5px;
  border-radius: 5px;
  text-decoration: none;
  font-size: 1.3em;
  transition: transform 0.2s ease;
  display: inline-block;
}

.navbar-username:hover {
  cursor: pointer;
  transform: scale(1.05);
}

#register-button{
  background-color: #1877F2;
}

#nav-separator {
  margin: 0 7px;
  color: #b4b4b4;
}

/* Responsive Styles */
@media (max-width: 768px) {
  .navbar {
    padding: 10px;
  }
  
  .navbar-title a {
    margin-left: 0;
    font-size: 1.2em;
  }
  
  .navbar-links {
    margin-left: 10px;
  }
  
  .navbar-username {
    padding: 6px;
    font-size: 13px;
  }
  
  #nav-separator {
    margin: 0 5px;
  }
}
</style>
