<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">¡Ups! Página no encontrada</h2>
      <p class="error-description">La página que estás buscando parece que no existe o ha sido movida.</p>
      <router-link to="/" class="home-button">
        Volver al inicio
      </router-link>
    </div>
  </div>
</template>

<style scoped>

.not-found-content {
  text-align: center;
}

.error-code {
  font-size: 8rem;
  font-weight: 700;
  color: #ff7043;
  margin: 0;
  line-height: 1;
}

.error-title {
  font-size: 2rem;
  color: #333;
  margin: 1rem 0;
}

.error-description {
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 2rem;
}

.home-button {
  display: inline-block;
  background-color: rgb(34, 134, 141);
  color: white;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  text-decoration: none;
  transition: background-color 0.3s ease;
}

.home-button:hover {
  background-color: #3da59b; /* Versión ligeramente más oscura */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

</style>