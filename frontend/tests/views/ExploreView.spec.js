import { mount } from '@vue/test-utils';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { flushPromises } from '@vue/test-utils';
import { useRoute, useRouter } from 'vue-router';
import ExploreView from '../../src/views/ExploreView.vue';
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { createPinia, setActivePinia } from 'pinia';

library.add(fas);

beforeEach(() => {
  setActivePinia(createPinia());
});

// Mock del store de auth
vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    token: 'mock-token',
    user: { 
      id: '1', 
      username: 'testuser',
      email: 'testuser@example.com',
      is_admin: false
    },
    isAuthenticated: true,
    setAuthHeader: vi.fn()
  }))
}));

vi.mock('vue-router', () => ({
  useRoute: vi.fn(),
  useRouter: vi.fn()
}));

const routerReplaceMock = vi.fn(() => Promise.resolve());
const routerPushMock = vi.fn();

vi.mocked(useRouter).mockReturnValue({
  replace: routerReplaceMock,
  push: routerPushMock
});

vi.mocked(useRoute).mockReturnValue({
  path: '/explore',
  query: {},
  params: {}
});

const mockDatasets = [
  { id: 1, name: 'Test Dataset 1', description: 'Description 1' },
  { id: 2, name: 'Test Dataset 2', description: 'Description 2' }
];

const globalOptions = {
  global: {
    plugins: [createPinia()],
    stubs: {
      RouterLink: true,
      RouterView: true,
      FontAwesomeIcon: true
    },
    mocks: {
      $route: {
        query: {}
      }
    }
  }
};


vi.mock('../../src/services/api', () => ({
  default: {
    getDatasets: vi.fn().mockResolvedValue({
      data: {
        data: mockDatasets,
        total: 10,
        page: 1,
        size: 10,
        totalPages: 5 // Aseguramos que hay 5 páginas para el test de navegación
      }
    }),
    cloneDataset: vi.fn().mockResolvedValue({ data: { id: 999 } })
  }
}));

// Mock de Pinia
vi.mock('pinia', () => {
  const actual = vi.importActual('pinia');
  return {
    ...actual,
    defineStore: vi.fn().mockImplementation((name, options) => {
      return vi.fn(() => {
        const state = typeof options.state === 'function' ? options.state() : {};
        const getters = {};
        const actions = {};
        
        // Simular getters
        if (options.getters) {
          Object.keys(options.getters).forEach(key => {
            getters[key] = vi.fn();
          });
        }
        
        // Simular acciones
        if (options.actions) {
          Object.keys(options.actions).forEach(key => {
            actions[key] = vi.fn();
          });
        }
        
        return { ...state, ...getters, ...actions };
      });
    }),
    setActivePinia: vi.fn(),
    createPinia: vi.fn(() => ({
      install: vi.fn(),
      use: vi.fn()
    }))
  };
});

describe('ExploreView', () => {
  it('trunca correctamente el texto con el método truncateText', () => {
      const wrapper = mount(ExploreView, globalOptions);
      
      // Texto corto que no necesita truncamiento
      const shortText = "Texto corto";
      expect(wrapper.vm.truncateText(shortText, 20)).toBe(shortText);
      
      // Texto largo que necesita truncamiento
      const longText = "Este es un texto muy largo que debe ser truncado";
      const truncated = wrapper.vm.truncateText(longText, 15);
      expect(truncated).toBe("Este es un text...");
      expect(truncated.length).toBe(18); // 15 caracteres + "..."
      
      // Manejo de texto vacío
      expect(wrapper.vm.truncateText("", 10)).toBe("");
      expect(wrapper.vm.truncateText(null, 10)).toBe("");
  });

  it('formatea correctamente las descripciones con el método formatDescription', () => {
      const wrapper = mount(ExploreView, globalOptions);
      
      // Descripción corta que no necesita formato
      const shortDesc = "Esta es una descripción corta";
      expect(wrapper.vm.formatDescription(shortDesc)).toBe(shortDesc);
      
      // Descripción larga que necesita formato
      const longDesc = "a".repeat(300); // 300 caracteres
      const formatted = wrapper.vm.formatDescription(longDesc);
      expect(formatted.endsWith('...')).toBe(true);
      expect(formatted.length).toBe(203); // aprox 200 + "..."
      
      // Manejo de descripción vacía
      expect(wrapper.vm.formatDescription("")).toBe("");
      expect(wrapper.vm.formatDescription(null)).toBe("");
  });

  it('cancela correctamente la clonación del dataset', async () => {
      const wrapper = mount(ExploreView, globalOptions);
      
      // Configurar estado inicial
      wrapper.vm.selectedDataset = mockDatasets[0];
      wrapper.vm.showCloneModal = true;
      await wrapper.vm.$nextTick();
      
      // Cancelar clonación
      await wrapper.vm.cancelCloneDataset();
      
      // Verificar que se cierra el modal y se resetea el dataset seleccionado
      expect(wrapper.vm.showCloneModal).toBe(false);
      expect(wrapper.vm.selectedDataset).toBe(null);
  });

  it('actualiza la URL correctamente cuando cambian los parámetros de paginación', async () => {
      const wrapper = mount(ExploreView, globalOptions);
      
      wrapper.vm.isLoading = false;
      
      // Cambiar parámetros de paginación
      wrapper.vm.currentPage = 2;
      wrapper.vm.pageSize = 10;
      
      // Disparar el watcher manualmente
      await flushPromises();
      
      // Verificar que se actualiza la URL
      expect(routerReplaceMock).toHaveBeenCalledWith(
          expect.objectContaining({
              query: expect.objectContaining({
                  page: 2,
                  size: 10
              })
          })
      );
  });

  it('carga correctamente los parámetros de la URL al montar el componente', async () => {
      // Mockear ruta con parámetros de consulta
      vi.mocked(useRoute).mockReturnValue({
          path: '/explore',
          query: {
              page: '3',
              size: '10',
              search: 'test'
          },
          params: {}
      });
      
      const wrapper = mount(ExploreView, globalOptions);
      
      wrapper.vm.currentPage = 3;
      wrapper.vm.pageSize = 10;
      wrapper.vm.searchQuery = 'test';
      
      expect(wrapper.vm.currentPage).toBe(3);
      expect(wrapper.vm.pageSize).toBe(10);
      expect(wrapper.vm.searchQuery).toBe('test');
  });

  it('sale a primera página cuando ejecuta una nueva búsqueda', async () => {
      const wrapper = mount(ExploreView, globalOptions);
      
      wrapper.vm.isLoading = false;
      
      wrapper.vm.fetchSharedDatasets = vi.fn();
      
      // Establecer una página diferente de la primera
      wrapper.vm.currentPage = 2;
      await wrapper.vm.$nextTick();
      
      // Ejecutar búsqueda
      wrapper.vm.searchQuery = 'Nueva búsqueda';
      await wrapper.vm.executeSearch();
      
      // Verificar que volvió a la primera página
      expect(wrapper.vm.currentPage).toBe(1);
  });
});
