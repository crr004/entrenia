<template>
  <div class="home-content">
    <section class="hero-section">
      <h1>Entrena modelos de IA sin escribir código</h1>
      <p class="subtitle">Una plataforma intuitiva para crear clasificadores de imágenes de forma fácil y directa</p>
      <p class="intro-text">
        Crea tus propios conjuntos de imágenes o 
        <router-link to="/explore" class="highlight-link">explora</router-link> 
        los de otros usuarios.
      </p>
    </section>
    <section class="features-section">
      <h2>¿Qué puedes hacer con EntrenIA?</h2>
      <div class="feature-cards">
        <div class="feature-card">
          <div class="feature-icon">
            <font-awesome-icon :icon="['fas', 'database']" />
          </div>
          <h3>Gestionar datasets</h3>
          <p>Crea y edita tus conjuntos de imágenes. Sube tus imágenes y etiquétalas de forma sencilla.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <font-awesome-icon :icon="['fas', 'robot']" />
          </div>
          <h3>Entrenar modelos</h3>
          <p>Entrena modelos de IA con tus conjuntos de imágenes en pocos clics. Elige un conjunto de imágenes y una arquitectura, y nostros nos encargamos del resto.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <font-awesome-icon :icon="['fas', 'chart-bar']" />
          </div>
          <h3>Analizar resultados</h3>
          <p>Visualiza métricas de rendimiento, matrices de confusión y evalúa la precisión de tus modelos con gráficos.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <font-awesome-icon :icon="['fas', 'magic']" />
          </div>
          <h3>Clasificar nuevas imágenes</h3>
          <p>Utiliza tus modelos entrenados para clasificar nuevas imágenes. Exporta tus modelos para usarlos en otras plataformas.</p>
        </div>
      </div>
    </section>
    <section class="workflow-section">
      <h2>Cómo funciona</h2>
      <div class="workflow-steps">
        <div class="step">
          <div class="step-number">1</div>
          <h3>Crea un conjunto de imágenes</h3>
          <p>Sube tus imágenes y organízalas en categorías. EntrenIA te permite etiquetar y preparar tus datos fácilmente.</p>
        </div>
        <div class="step">
          <div class="step-number">2</div>
          <h3>Entrena un modelo de IA</h3>
          <p>Selecciona una arquitectura y personaliza los parámetros de entrenamiento según tus necesidades.</p>
        </div>
        <div class="step">
          <div class="step-number">3</div>
          <h3>Analiza</h3>
          <p>Evalúa el rendimiento de tu modelo con métricas detalladas.</p>
        </div>
        <div class="step">
          <div class="step-number">4</div>
          <h3>Aplica tu modelo</h3>
          <p>Utiliza tu modelo entrenado para clasificar nuevas imágenes o descárgalo para usarlo en otras aplicaciones.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import axios from 'axios';

import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';

onMounted(async () => {
  try {
    // Obtener el token de la URL.
    const queryParams = new URLSearchParams(window.location.search);
    const token = queryParams.get('token');
    
    // Si el token existe en la URL, proceder con la verificación.
    // Si no existe, no se hace nada.
    if (token) {
      try {
        await axios.post(`/signup/account-verification?token=${token}`, {});
        
        notifySuccess("Cuenta verificada", 
        "Tu cuenta ha sido verificada con éxito. Ahora puedes iniciar sesión.");
      } catch (error) {
        console.error('Error during verification: ', error);
        handleApiError(error);
      } finally {
        // Limpiar el token de la URL sin recargar la página.
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  } catch (e) {
    console.error('Error while processing the verification: ', e);
  }
});

const handleApiError = (error) => {
  if (error.response) {
    const status = error.response.status;
    const detail = error.response.data.detail || 'Error desconocido';

    console.error('Error response: ', error.response.data);
    
    if (status === 400) {
      notifyError("Error de verificación", 
      "El token de verificación no es válido o ha expirado.");
    } else if (status === 404) {
      notifyError("Error de verificación", 
      "No se encontró ninguna cuenta asociada.");
    } else if (status === 409) {
      notifyInfo("Cuenta verificada anteriormente", 
      "Tu identidad ya ha sido verificada anteriormente. Puedes iniciar sesión.");
    } else {
      notifyError("Error de verificación", 
      "Ha ocurrido un error de verificación.");
    }
  } else {
    notifyError("Error de conexión", 
    "No se pudo conectar con el servidor. Verifica tu conexión a internet.");
  }
};
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped>
.home-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  line-height: 1.6;
  color: #4e4e4e;
}

.hero-section {
  text-align: center;
  padding: 60px 0;
}

.hero-section h1 {
  font-size: 2.6rem;
  color: #3a3a3a;
  margin-bottom: 20px;
}

.subtitle {
  font-size: 1.4rem;
  color: #706f6c;
  margin-bottom: 20px;
}

.intro-text {
  font-size: 1.2rem;
  margin-top: 30px;
  color: #4e4e4e;
  line-height: 1.8;
}

.highlight-link {
  color: rgb(34, 134, 141);
  font-weight: 600;
  text-decoration: none;
  position: relative;
  transition: all 0.3s ease;
}

.highlight-link:hover {
  color: #3da59b;
  text-shadow: 0 0 8px rgba(34, 134, 141, 0.3);
}

.highlight-link:after {
  content: '';
  position: absolute;
  width: 100%;
  height: 2px;
  bottom: -2px;
  left: 0;
  background-color: rgb(34, 134, 141);
  transform: scaleX(0);
  transform-origin: bottom right;
  transition: transform 0.3s ease;
}

.highlight-link:hover:after {
  transform: scaleX(1);
  transform-origin: bottom left;
}

.features-section, 
.workflow-section {
  padding: 60px 0;
  text-align: center;
}

h2 {
  font-size: 2rem;
  color: #3a3a3a;
  margin-bottom: 40px;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 25px;
  margin-top: 30px;
}

.feature-card {
  background-color: #f5f1e4;
  border-radius: 10px;
  padding: 30px 20px;
  box-shadow: 0px 3px 15px rgba(0,0,0,0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0px 5px 20px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 20px;
  color: #d4c19c;
}

.feature-card h3 {
  font-size: 1.4rem;
  margin-bottom: 15px;
  color: #3a3a3a;
}

.workflow-steps {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
  margin-top: 40px;
}

.step {
  flex: 1;
  min-width: 220px;
  max-width: 280px;
  background-color: #f5f1e4;
  border-radius: 10px;
  padding: 30px 20px;
  position: relative;
  box-shadow: 0px 3px 15px rgba(0,0,0,0.05);
}

.step-number {
  width: 40px;
  height: 40px;
  background-color: #d4c19c;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: bold;
  margin: 0 auto 20px;
}

.step h3 {
  font-size: 1.3rem;
  margin-bottom: 15px;
  color: #3a3a3a;
}

.button-icon {
  margin-right: 10px;
}

/* Responsive */
@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1.2rem;
  }
  
  .workflow-steps {
    flex-direction: column;
    align-items: center;
  }
  
  .step {
    width: 100%;
    max-width: 320px;
  }
}
</style>