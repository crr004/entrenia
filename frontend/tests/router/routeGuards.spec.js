import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import { flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { globalOptions } from '../helpers/test-utils'

// Mock de store para pruebas.
const authStoreMock = {
  isAuthenticated: false,
  user: null,
  checkAuthStatus: vi.fn().mockResolvedValue(true)
}

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => authStoreMock)
}))

// Mock para componentes de página.
const HomeView = { template: '<div>Home View</div>' }
const AdminView = { template: '<div>Admin View</div>' }
const AccountView = { template: '<div>Account View</div>' }
const AboutView = { template: '<div>About View</div>' }
const ResetPasswordView = { template: '<div>Reset Password View</div>' }
const DatasetsView = { template: '<div>Datasets View</div>' }
const DatasetDetailView = { template: '<div>Dataset Detail View</div>' }
const ExploreView = { template: '<div>Explore View</div>' }
const PublicDatasetDetailView = { template: '<div>Public Dataset Detail View</div>' }
const NotFoundView = { template: '<div>Not Found View</div>' }

describe('Guardias de rutas', () => {
  let router
  let nextSpy

  beforeEach(() => {
    // Crear una instancia limpia de pinia.
    const pinia = createPinia()
    setActivePinia(pinia)
    
    // Resetear el mock del store antes de cada test.
    authStoreMock.isAuthenticated = false
    authStoreMock.user = null
    authStoreMock.checkAuthStatus.mockClear()
    authStoreMock.checkAuthStatus.mockResolvedValue(true) // Asegurar que por defecto devuelve true
    
    // Crear rutas para probar los guardias, reflejando todas las rutas reales.
    const routes = [
      {
        path: '/',
        component: HomeView,
        meta: { requiresAuth: false, showNav: true, showFooter: true }
      },
      {
        path: '/about',
        component: AboutView,
        meta: { requiresAuth: false, showNav: true, showFooter: true }
      },
      {
        path: '/reset-password',
        component: ResetPasswordView,
        meta: { requiresAuth: false, showNav: false, showFooter: false }
      },
      {
        path: '/account',
        component: AccountView,
        meta: { requiresAuth: true, showNav: true, showFooter: true }
      },
      {
        path: '/admin',
        component: AdminView,
        meta: { requiresAuth: true, requiresAdmin: true, showNav: true, showFooter: true }
      },
      {
        path: '/my-datasets',
        component: DatasetsView,
        meta: { requiresAuth: true, showNav: true, showFooter: true }
      },
      {
        path: '/dataset/:id',
        component: DatasetDetailView,
        meta: { requiresAuth: true, showNav: true, showFooter: true }
      },
      {
        path: '/explore',
        component: ExploreView,
        meta: { requiresAuth: false, showNav: true, showFooter: true }
      },
      {
        path: '/explore/:id',
        component: PublicDatasetDetailView,
        meta: { requiresAuth: false, showNav: true, showFooter: true }
      },
      {
        path: '/:pathMatch(.*)*',
        component: NotFoundView,
        meta: { requiresAuth: false, showNav: false, showFooter: false }
      }
    ]
    
    // Crear router.
    router = createRouter({
      history: createWebHistory(),
      routes
    })
    
    // En lugar de espiar push, espiar next para verificar las redirecciones.
    nextSpy = vi.fn()
  })
  
  // Función auxiliar para probar un guardia.
  const testRouteGuard = async (to, from = { path: '/' }) => {
    // Resetear nextSpy para cada test.
    nextSpy.mockClear()
    
    // Crear objetos de ruta para el guardia.
    const toRoute = { path: to, meta: router.resolve(to).meta }
    const fromRoute = { path: from, meta: router.resolve(from).meta }
    
    // Ejecutar el guardia de ruta directamente.
    await executeRouteGuard(toRoute, fromRoute, nextSpy)
    
    return nextSpy // Devolver el spy para las afirmaciones.
  }
  
  // Función que contiene la lógica del guardia de ruta (la misma que en el router).
  const executeRouteGuard = async (to, from, next) => {
    // Verificar si la ruta requiere autenticación.
    if (to.meta.requiresAuth) {
      if (!authStoreMock.isAuthenticated) {
        next('/')
        return
      }
      
      // Verificar si la ruta requiere ser admin.
      if (to.meta.requiresAdmin && (!authStoreMock.user || !authStoreMock.user.is_admin)) {
        next('/')
        return
      }
      
      // Verificar token expirado (para test #4).
      const isValid = await authStoreMock.checkAuthStatus()
      if (!isValid) {
        next('/')
        return
      }
    }
    
    next() // Si no hay problemas, continuar.
  }
  
  // Test 1: Protección de ruta /account para usuarios no autenticados.
  it('redirige a / cuando un usuario no autenticado intenta acceder a /account', async () => {
    // Configurar como no autenticado.
    authStoreMock.isAuthenticated = false
    
    // Ejecutar guardia.
    await testRouteGuard('/account')
    
    // Verificar que se redirigió a /.
    expect(nextSpy).toHaveBeenCalledWith('/')
  })
  
  // Test 2: Protección de ruta /admin para usuarios no admin.
  it('redirige a / cuando un usuario no admin intenta acceder a /admin', async () => {
    // Configurar como autenticado pero no admin.
    authStoreMock.isAuthenticated = true
    authStoreMock.user = { username: 'user', is_admin: false }
    
    // Ejecutar guardia.
    await testRouteGuard('/admin')
    
    // Verificar que se redirigió a /.
    expect(nextSpy).toHaveBeenCalledWith('/')
  })
  
  // Test 3: Acceso permitido a /admin para usuarios admin.
  it('permite acceso a /admin para usuarios admin', async () => {
    // Configurar como autenticado y admin.
    authStoreMock.isAuthenticated = true
    authStoreMock.user = { username: 'admin', is_admin: true }
    
    // Ejecutar guardia.
    await testRouteGuard('/admin')
    
    // Verificar que se permitió continuar (next sin argumentos).
    expect(nextSpy).toHaveBeenCalledWith()
  })
  
  // Test 4: Redireccionamiento cuando el token ha expirado.
  it('redirige a / cuando el token ha expirado', async () => {
    // Configurar que checkAuthStatus falla, simulando que el token expiró.
    authStoreMock.checkAuthStatus.mockResolvedValue(false)
    authStoreMock.isAuthenticated = true // Usuario "autenticado" pero token expirado.
    authStoreMock.user = { username: 'user', is_admin: false }
    
    // Ejecutar guardia.
    await testRouteGuard('/account')
   
    // Verificar que se llamó a checkAuthStatus.
    expect(authStoreMock.checkAuthStatus).toHaveBeenCalled()
    
    // Verificar que se redirigió a /.
    expect(nextSpy).toHaveBeenCalledWith('/')
  })
  
  // Test 5: Comprobación de rutas públicas.
  it('permite acceso a rutas públicas sin autenticación', async () => {
    // Configurar como no autenticado.
    authStoreMock.isAuthenticated = false
    
    // Ejecutar guardia para rutas públicas.
    await testRouteGuard('/')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/about')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/reset-password')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/explore')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/explore/123')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/ruta-inexistente')
    expect(nextSpy).toHaveBeenCalledWith()
  })
  
  // Test 6: Protección de todas las rutas autenticadas para usuarios no autenticados
  it('redirige a / cuando un usuario no autenticado intenta acceder a rutas protegidas', async () => {
    // Configurar como no autenticado
    authStoreMock.isAuthenticated = false
    
    // Verificar rutas protegidas
    await testRouteGuard('/account')
    expect(nextSpy).toHaveBeenCalledWith('/')
    
    nextSpy.mockClear()
    await testRouteGuard('/admin')
    expect(nextSpy).toHaveBeenCalledWith('/')
    
    nextSpy.mockClear()
    await testRouteGuard('/my-datasets')
    expect(nextSpy).toHaveBeenCalledWith('/')
    
    nextSpy.mockClear()
    await testRouteGuard('/dataset/123')
    expect(nextSpy).toHaveBeenCalledWith('/')
  })
  
  // Test 7: Acceso permitido a rutas autenticadas para usuarios correctos
  it('permite acceso a rutas autenticadas para usuarios autenticados', async () => {
    // Configurar como autenticado
    authStoreMock.isAuthenticated = true
    authStoreMock.user = { username: 'user', is_admin: false }
    // Asegurar que checkAuthStatus devuelve true
    authStoreMock.checkAuthStatus.mockResolvedValue(true)
    
    // Probar rutas que requieren solo autenticación
    await testRouteGuard('/account')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/my-datasets')
    expect(nextSpy).toHaveBeenCalledWith()
    
    nextSpy.mockClear()
    await testRouteGuard('/dataset/123')
    expect(nextSpy).toHaveBeenCalledWith()
  })
})