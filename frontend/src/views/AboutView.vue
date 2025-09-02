<template>
    <div class="about-container">
        <section class="hero-section">
            <h1>Sobre EntrenIA</h1>
            <p class="subtitle"></p>
        </section>
        <section class="info-section">
            <h2>El proyecto</h2>
            <p>
                EntrenIA es una plataforma web que permite a cualquier persona crear, entrenar y utilizar 
                modelos de inteligencia artificial para clasificación de imágenes sin necesidad de escribir 
                código. Este proyecto nace como Trabajo Fin de Grado de Carlos Rodríguez Romo para la 
                titulación del Grado en Ingeniería Informática de la Universidad de Salamanca.
            </p>
            <p>
                El objetivo principal de EntrenIA es permitir a todo tipo de usuarios, sin importar sus conocimientos, 
                acceder al mundo de la clasificación de imágenes, pudiendo crear conjuntos de imágenes y entrenar modelos de clasificación que se utilicen en escenarios reales.
                Todo ello de una forma sencilla.
            </p>
        </section>
        <section class="features-section">
            <h2>Características principales de la aplicación</h2>
            <div class="feature">
                <h3><font-awesome-icon :icon="['fas', 'database']" class="feature-icon" /> Gestión completa de conjuntos de imágenes</h3>
                <p>
                    EntrenIA permite crear y gestionar conjuntos de imágenes de forma sencilla. 
                    Puedes subir tus propias imágenes, organizarlas en categorías y etiquetarlas 
                    fácilmente a través de una interfaz visual e intuitiva. También puedes importar etiquetas 
                    mediante archivos CSV para agilizar el proceso.
                </p>
            </div>
            <div class="feature">
                <h3><font-awesome-icon :icon="['fas', 'robot']" class="feature-icon" /> Entrenamiento de modelos</h3>
                <p>
                    Con EntrenIA, entrenar un modelo de inteligencia artificial es tan sencillo como 
                    seleccionar un conjunto de imágenes y elegir una arquitectura. La plataforma ofrece arquitecturas de redes neuronales 
                    modernas como EfficientNet y ResNet.
                </p>
            </div>
            <div class="feature">
                <h3><font-awesome-icon :icon="['fas', 'chart-bar']" class="feature-icon" /> Análisis visual de resultados</h3>
                <p>
                    Visualiza el rendimiento de tus modelos mediante matrices 
                    de confusión y métricas de precisión. EntrenIA presenta los resultados de forma 
                    clara y comprensible, permitiéndote evaluar la eficacia de tus modelos sin 
                    necesidad de conocimientos avanzados en estadística.
                </p>
            </div>
            <div class="feature">
                <h3><font-awesome-icon :icon="['fas', 'magic']" class="feature-icon" /> Inferencia y aplicación práctica</h3>
                <p>
                    Una vez entrenado tu modelo, puedes utilizarlo para clasificar nuevas imágenes 
                    directamente desde la plataforma. Sube imágenes individuales o en lotes y obtén 
                    predicciones en tiempo real. También puedes descargar tus modelos entrenados para 
                    utilizarlos en otras aplicaciones.
                </p>
            </div>
            <div class="feature">
                <h3><font-awesome-icon :icon="['fas', 'users']" class="feature-icon" /> Comunidad colaborativa</h3>
                <p>
                    EntrenIA fomenta la colaboración entre usuarios, permitiéndote compartir tus 
                    conjuntos de imágenes con la comunidad. Explora recursos creados por otros usuarios 
                    y aprende de sus proyectos para mejorar tus propios modelos.
                </p>
            </div>
        </section>
        <section class="author-section">
            <h2>Sobre el autor</h2>
            <h3>Carlos Rodríguez Romo</h3>
            <p>
                Estudiante de Ingeniería Informática en la Universidad de Salamanca. 
                Apasionado por la inteligencia artificial y el desarrollo de software, ha creado 
                EntrenIA como su Trabajo de Fin de Grado.
            </p>
            <p>
                El proyecto ha sido supervisado por el profesor Guillermo Hernández González,
                del Departamento de Informática y Automática de la Universidad de Salamanca.
            </p>
        </section>
    </div>
</template>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped>
.about-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 90px 20px 40px;
    line-height: 1.6;
    color: #4e4e4e;
}

.hero-section {
    text-align: center;
    padding: 40px 0;
    margin-bottom: 30px;
}

.hero-section h1 {
    font-size: 2.6rem;
    color: #3a3a3a;
    margin-bottom: 20px;
}

.subtitle {
    font-size: 1.4rem;
    color: #706f6c;
}

.info-section,
.features-section,
.author-section {
    margin-bottom: 60px;
}

h2 {
    font-size: 2rem;
    color: #3a3a3a;
    margin-bottom: 25px;
    padding-bottom: 10px;
    border-bottom: 2px solid #d4c19c;
}

h3 {
    font-size: 1.4rem;
    color: #3a3a3a;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
}

p {
    margin-bottom: 20px;
    font-size: 1.1rem;
    text-align: justify;
}

.feature-icon {
    font-size: 1.4rem;
    color: #d4c19c;
    margin-right: 12px;
    width: 24px;
    display: inline-flex;
    justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
    .hero-section h1 {
        font-size: 2.2rem;
    }
    
    .subtitle {
        font-size: 1.2rem;
    }
    
    h2 {
        font-size: 1.8rem;
    }
    
    h3 {
        font-size: 1.3rem;
    }
}
</style>
