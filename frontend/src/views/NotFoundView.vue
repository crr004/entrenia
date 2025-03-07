<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">¡Ups! Página no encontrada</h2>
      <p class="error-description">La página que estás buscando parece que no existe o ha sido movida.</p>
      <router-link to="/" class="app-button" id="home-button">
        Volver al inicio
      </router-link>
    </div>
  </div>
</template>

<style scoped src="@/assets/styles/buttons.css"></style>

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

#home-button {
  display: inline-block;
  text-decoration: none;
  width: 10rem;
}

</style>