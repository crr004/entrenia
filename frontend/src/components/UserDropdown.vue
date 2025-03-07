<template>
    <div class="user-dropdown-container">
        <div class="dropdown-links" @click="emit('close')">
            <router-link to="/">Home</router-link>
            <router-link to="/about">About</router-link>
            <hr>
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
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const emit = defineEmits(['close']);

const router = useRouter();

const logout = () => {
    try {
        authStore.logout();
        emit('close');
        router.push('/');
    } catch (error) {
        console.error('Logout failed:', error);
        emit('close');

    }
};
</script>

<style scoped>
.user-dropdown-container {
  display: block;
  text-align: left;
  position: absolute;
  width: 200px;
  top: 50px;
  right: 10px;
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