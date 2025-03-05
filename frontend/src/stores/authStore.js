import { defineStore } from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    user: null,
    isAuthenticated: false
  }),
  
  getters: {
    getToken: (state) => state.token,
    getUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated
  },
  
  actions: {
    setToken(token) {
      this.token = token;
      this.isAuthenticated = !!token;
      
      // Configurar axios para incluir el token en las cabeceras
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } else {
        delete axios.defaults.headers.common['Authorization'];
      }
    },
    
    setUser(user) {
      this.user = user;
    },
    
    login(token) {
      this.setToken(token);
    },
    
    logout() {
      this.setToken(null);
      this.setUser(null);
      this.isAuthenticated = false;
    },
    
    initializeAuth() {
      const token = this.token;
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
    }
  },
  /*
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'auth',
        storage: localStorage,
        paths: ['token', 'user', 'isAuthenticated']
      }
    ]
  }
    */
  
  persist: {
    enabled: true,
    storage: window.sessionStorage,
    key: 'auth-store',
    paths: ['token', 'user', 'isAuthenticated']
  }
});