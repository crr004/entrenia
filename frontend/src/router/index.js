import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

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
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/ResetPasswordView.vue'),
    meta: { showNav: false, showFooter: false }
  },
  {
    path: '/account',
    name: 'account',
    component: () => import('../views/AccountView.vue'),
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/AdminView.vue'),
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/my-datasets',
    name: 'my-datasets',
    component: () => import('../views/DatasetsView.vue'),
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/dataset/:id',
    name: 'dataset-detail',
    component: () => import('../views/DatasetDetailView.vue'),
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/explore',
    name: 'explore',
    component: () => import('../views/ExploreView.vue'),
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/explore/:id',
    name: 'public-dataset-detail',
    component: () => import('../views/PublicDatasetDetailView.vue'),
    meta: { showNav: true, showFooter: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
    meta: { showNav: false, showFooter: false }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router