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
      
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } else {
        delete axios.defaults.headers.common['Authorization'];
      }
    },

    setAuthHeader(){
      const token = this.token;
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
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
    },
    updateUserData(userData) {
    this.user = userData;
    
    if (userData) {
      const currentAuthData = JSON.parse(localStorage.getItem('auth') || '{}');
      const updatedAuthData = {
        ...currentAuthData,
        user: userData
      };
      localStorage.setItem('auth', JSON.stringify(updatedAuthData));
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