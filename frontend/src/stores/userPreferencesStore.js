import { defineStore } from 'pinia';

export const userPreferencesStore = defineStore('preferences', {
  state: () => ({
    adminPageSize: 5,
    datasetPageSize: 5,
    imagePageSize: 5,
    modelPageSize: 5,
  }),
  
  getters: {
    getAdminPageSize: (state) => state.adminPageSize,
    getDatasetPageSize: (state) => state.datasetPageSize,
    getImagePageSize: (state) => state.imagePageSize,
    getModelPageSize: (state) => state.modelPageSize,
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

    setModelPageSize(size) {
      this.modelPageSize = size;
    },
    
    resetPreferences() {
      this.adminPageSize = 5;
      this.datasetPageSize = 5;
      this.imagePageSize = 5;
      this.modelPageSize = 5;
    }
  },

   /*
  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user-preferences',
        storage: localStorage,
        paths: ['adminPageSize', 'datasetPageSize', 'imagePageSize', 'modelPageSize']
      }
    ]
  }
    */
  
  persist: {
    enabled: true,
    storage: window.sessionStorage,
    key: 'preferences-store',
    paths: ['adminPageSize', 'datasetPageSize', 'imagePageSize', 'modelPageSize']
  }
});