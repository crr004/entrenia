import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ModelsView from '@/views/ModelsView.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Sobre EntrenIA' }
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/ResetPasswordView.vue'),
    meta: { showNav: false, showFooter: false, title: 'EntrenIA - Restablecer contraseña' }
  },
  {
    path: '/account',
    name: 'account',
    component: () => import('../views/AccountView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Mi cuenta' }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/AdminView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Panel de administración' }
  },
  {
    path: '/my-datasets',
    name: 'my-datasets',
    component: () => import('../views/DatasetsView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Mis conjuntos de imágenes' }
  },
  {
    path: '/dataset/:id',
    name: 'dataset-detail',
    component: () => import('../views/DatasetDetailView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Detalles del conjunto de imágenes' }
  },
  {
    path: '/explore',
    name: 'explore',
    component: () => import('../views/ExploreView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Explorar conjuntos de imágenes' }
  },
  {
    path: '/explore/:id',
    name: 'public-dataset-detail',
    component: () => import('../views/PublicDatasetDetailView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Detalles del conjunto de imágenes' }
  },
  {
    path: '/my-models',
    name: 'my-models',
    component: ModelsView,
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Mis modelos de clasificación de imágenes' }
  },
  {
    path: '/train-model',
    name: 'train-model',
    component: () => import('../views/TrainModelView.vue'),
    meta: { showNav: true, showFooter: true, title: 'EntrenIA - Entrenar nuevo modelo' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
    meta: { showNav: false, showFooter: false, title: 'EntrenIA - Página no encontrada' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Actualizar título de la página cuando cambia la ruta.
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'EntrenIA';
  next();
});

export default router