<template>
    <div class="user-dropdown-container">
        <div class="dropdown-links" @click="emit('close')">
            <router-link to="/my-models">
                <span class="icon-container">
                    <font-awesome-icon :icon="['fas', 'robot']" fixed-width />
                </span>
                Mis modelos
            </router-link>
            <router-link to="/my-datasets">
                <span class="icon-container">
                    <font-awesome-icon :icon="['fas', 'database']" fixed-width />
                </span>
                Mis conjuntos de imágenes
            </router-link>
            <hr>
            <router-link v-if="isAdmin" to="/admin">
                <span class="icon-container">
                    <font-awesome-icon :icon="['fas', 'shield-alt']" fixed-width />
                </span>
                Panel de administración
            </router-link>
            <hr v-if="isAdmin">
            <router-link to="/account">
                <span class="icon-container">
                    <font-awesome-icon :icon="['fas', 'user-cog']" fixed-width />
                </span>
                Mi cuenta
            </router-link>
            <hr>
            <router-link @click.prevent="logout" to="/">
                <span class="icon-container">
                    <font-awesome-icon :icon="['fas', 'sign-out-alt']" fixed-width />
                </span>
                Cerrar sesión
            </router-link>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

import { useAuthStore } from '@/stores/authStore';


const authStore = useAuthStore();
const emit = defineEmits(['close']);
const router = useRouter();

const isAdmin = computed(() => {
  return authStore.user && authStore.user.is_admin === true;
});

const logout = () => {
  authStore.logout();
  emit('close');
  router.push('/');
};
</script>

<style scoped>
.user-dropdown-container {
  display: block;
  text-align: left;
  position: absolute;
  width: 280px;
  top: 38px;
  right: 5px;
  background-color: #555;
  border-radius: 8px;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
  border: 1px solid #666;
  z-index: 1000;
}

.dropdown-links {
  display: block;
  text-align: left;
  padding: 10px;
  font-size: 14px;
}

.dropdown-links a {
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 4px;
  transition: background-color 0.2s;
}

.dropdown-links a:hover {
  text-decoration: none;
  background-color: #444;
}

.icon-container {
  display: inline-block;
  width: 20px;
  margin-right: 10px;
  text-align: center;
}

hr {
  border: 0;
  border-top: 1px solid #666;
  margin: 8px 0;
}
</style>