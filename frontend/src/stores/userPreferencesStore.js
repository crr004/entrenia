import { defineStore } from 'pinia';

export const userPreferencesStore = defineStore('preferences', {
  state: () => ({
    adminPageSize: 10,
    datasetPageSize: 5 
  }),
  
  getters: {
    getAdminPageSize: (state) => state.adminPageSize,
    getDatasetPageSize: (state) => state.datasetPageSize
  },
  
  actions: {
    setAdminPageSize(size) {
      this.adminPageSize = size;
    },
    
    setDatasetPageSize(size) {
      this.datasetPageSize = size;
    },
    
    resetPreferences() {
      this.adminPageSize = 10;
      this.datasetPageSize = 5;
    }
  },

  /*
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user-preferences',
        storage: localStorage,
        paths: ['adminPageSize', 'datasetPageSize']
      }
    ]
  }
    */
  
  persist: {
    enabled: true,
    storage: window.sessionStorage,
    key: 'preferences-store',
    paths: ['adminPageSize', 'datasetPageSize']
  }
});