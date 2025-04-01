import { defineStore } from 'pinia';

export const userPreferencesStore = defineStore('preferences', {
  state: () => ({
    adminPageSize: 5,
    datasetPageSize: 5,
    imagePageSize: 5,
  }),
  
  getters: {
    getAdminPageSize: (state) => state.adminPageSize,
    getDatasetPageSize: (state) => state.datasetPageSize,
    getImagePageSize: (state) => state.imagePageSize,
  },
  
  actions: {
    setAdminPageSize(size) {
      this.adminPageSize = size;
    },
    
    setDatasetPageSize(size) {
      this.datasetPageSize = size;
    },
    
    setImagePageSize(size) {
      this.imagePageSize = size;
    },
    
    resetPreferences() {
      this.adminPageSize = 5;
      this.datasetPageSize = 5;
      this.imagePageSize = 5;
    }
  },

   /*
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user-preferences',
        storage: localStorage,
        paths: ['adminPageSize', 'datasetPageSize', 'imagePageSize']
      }
    ]
  }
    */
  
  persist: {
    enabled: true,
    storage: window.sessionStorage,
    key: 'preferences-store',
    paths: ['adminPageSize', 'datasetPageSize', 'imagePageSize']
  }
});