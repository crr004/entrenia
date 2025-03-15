import { defineStore } from 'pinia';

export const userPreferencesStore = defineStore('preferences', {
  state: () => ({
    adminPageSize: 10
  }),
  
  getters: {
    getAdminPageSize: (state) => state.adminPageSize
  },
  
  actions: {
    setAdminPageSize(size) {
      this.adminPageSize = size;
    },
    
    resetPreferences() {
      this.adminPageSize = 10;
    }
  },
  
  /*
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user-preferences',
        storage: localStorage,
        paths: ['adminPageSize']
      }
    ]
  }
    */
  persist: {
    enabled: true,
    storage: window.sessionStorage,
    key: 'preferences-store',
    paths: ['adminPageSize']
  }
});