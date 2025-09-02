<template>
    <div class="help-container">
        <section class="hero-section">
            <h1>Centro de ayuda</h1>
            <p class="subtitle">Encuentra respuestas y soluciones para EntrenIA</p>
        </section>
        <section class="support-section">
            <h2>Soporte técnico</h2>
            <p>
                Si tienes problemas o dudas cuya respuesta no encuentras aquí, 
                puedes contactar directamente con el administrador:
            </p>
            <div class="contact-card">
                <div class="contact-icon">
                    <font-awesome-icon :icon="['fas', 'envelope']" />
                </div>
                <div class="contact-info">
                    <h3>Correo electrónico</h3>
                    <a href="mailto:carlosrr@usal.es" class="highlight-link">carlosrr@usal.es</a>
                </div>
            </div>
        </section>
        <section class="faq-section">
            <h2>Preguntas frecuentes (FAQ)</h2>
            <div class="faq-item" v-for="(item, index) in faqItems" :key="index">
                <div 
                    class="faq-question" 
                    @click="toggleFaq(index)" 
                    :class="{'active': expandedFaq === index}"
                >
                    <h3>{{ item.question }}</h3>
                    <font-awesome-icon 
                        :icon="['fas', expandedFaq === index ? 'chevron-up' : 'chevron-down']" 
                        class="toggle-icon"
                    />
                </div>
                <div class="faq-answer" v-show="expandedFaq === index">
                    <p v-for="(paragraph, pIndex) in item.answer" :key="pIndex">
                        {{ paragraph }}
                    </p>
                </div>
            </div>
        </section>
        <section class="guides-section">
            <h2>Guías rápidas</h2>
            <div class="guide-cards">
                <div class="guide-card">
                    <div class="guide-icon">
                        <font-awesome-icon :icon="['fas', 'images']" />
                    </div>
                    <h3>Crear tu primer conjunto de imágenes</h3>
                    <ol>
                        <li>Inicia sesión con tu cuenta.</li>
                        <li>Navega a "Mis conjuntos de imágenes".</li>
                        <li>Haz clic en "Crear conjunto de imágenes".</li>
                        <li>Asigna a tu conjunto de imágenes un nombre y, si quieres, una descripción.</li>
                        <li>Sube tus imágenes y etiquétalas.</li>
                    </ol>
                </div>
                <div class="guide-card">
                    <div class="guide-icon">
                        <font-awesome-icon :icon="['fas', 'robot']" />
                    </div>
                    <h3>Entrenar tu primer modelo</h3>
                    <ol>
                        <li>Asegúrate de tener un conjunto de imágenes etiquetado.</li>
                        <li>Navega a "Mis modelos"</li>
                        <li>Haz clic en "Entrenar un modelo".</li>
                        <li>Asigna a tu modelo un nombre y, si quieres, una descripción.</li>
                        <li>Selecciona tu conjunto de imágenes.</li>
                        <li>Elige una arquitectura.</li>
                        <li>Ajusta los parámetros o usa los valores predeterminados.</li>
                        <li>Inicia el entrenamiento.</li>
                    </ol>
                </div>
                <div class="guide-card">
                    <div class="guide-icon">
                        <font-awesome-icon :icon="['fas', 'brain']" />
                    </div>
                    <h3>Clasificar nuevas imágenes</h3>
                    <ol>
                        <li>Navega a "Mis modelos".</li>
                        <li>Selecciona el modelo que deseas utilizar.</li>
                        <li>Haz clic en "Inferencia".</li>
                        <li>Sube la imagen o el conjunto de imágenes que quieres clasificar.</li>
                        <li>Revisa los resultados de la clasificación.</li>
                    </ol>
                </div>
            </div>
        </section>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const expandedFaq = ref(null);

const toggleFaq = (index) => {
    expandedFaq.value = expandedFaq.value === index ? null : index;
};

const faqItems = [
    {
        question: "¿Qué tipo de imágenes puedo utilizar para entrenar modelos?",
        answer: [
            "Puedes utilizar cualquier tipo de imagen en alguno de los formatos permitidos (puedes consultarlos al subir una nueva imagen). Es importante que las imágenes sean representativas de las categorías que deseas clasificar.",
        ]
    },
    {
        question: "¿Cuánto tiempo tarda en entrenarse un modelo?",
        answer: [
            "El tiempo de entrenamiento depende de varios factores: la cantidad de imágenes, el número de categorías, la arquitectura seleccionada y la complejidad del problema de clasificación.",
            "En general, un entrenamiento básico puede durar entre 5 y 30 minutos. Los modelos más complejos o con más datos pueden tardar hasta varias horas."
        ]
    },
    {
        question: "¿Cómo puedo mejorar la precisión de mi modelo?",
        answer: [
            "Hay varias formas de mejorar la precisión de tus modelos:",
            "1. Aumenta la cantidad de imágenes de entrenamiento.",
            "2. Asegúrate de que tus imágenes sean diversas y representativas.",
            "3. Prueba diferentes arquitecturas.",
            "4. Ajusta los hiperparámetros de las arquitecturas.",
        ]
    },
    {
        question: "¿Puedo usar mi modelo entrenado fuera de EntrenIA?",
        answer: [
            "Sí, puedes descargar tus modelos entrenados en formato TensorFlow SavedModel, junto con sus metadatos.",
            "Simplemente, ve a la sección 'Mis modelos', selecciona el modelo que deseas descargar y haz clic en la opción de descarga.",
        ]
    },
    {
        question: "¿Es posible compartir mis conjuntos de imágenes con otros usuarios?",
        answer: [
            "Sí, EntrenIA te permite compartir tus conjuntos de imágenes con la comunidad. Para hacerlo, ve a la sección 'Mis conjuntos de imágenes', selecciona el conjunto de imágenes que deseas compartir y haz clic en la opción de compartir.",
            "Puedes volver a privatizar tus conjuntos de imágenes en cualquier momento si lo deseas, siguiendo los mismos pasos."
        ]
    },
    {
        question: "¿Cómo funciona el proceso de etiquetado de imágenes?",
        answer: [
            "EntrenIA ofrece varias formas de etiquetar tus imágenes:",
            "1. Etiquetado manual -> Entra en el conjunto de imágenes que deseas etiquetar, y selecciona la opción de etiquetado manual.",
            "2. Importación mediante CSV -> Entra en el conjunto de imágenes que deseas etiquetar, y selecciona la opción de etiquetado con CSV.",
        ]
    }
];
</script>

<style scoped src="@/assets/styles/buttons.css"></style>
<style scoped>
.help-container {
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

.support-section,
.faq-section,
.guides-section {
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
}

p {
    margin-bottom: 20px;
    font-size: 1.1rem;
}

.contact-card {
    display: flex;
    align-items: center;
    margin: 30px 0;
}

.contact-icon {
    font-size: 2rem;
    color: #d4c19c;
    margin-right: 20px;
}

.response-time {
    font-style: italic;
    color: #707070;
    font-size: 1rem;
}

.info-icon {
    margin-right: 8px;
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

.faq-item {
    margin-bottom: 10px;
}

.faq-question {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background-color: #f5f1e4;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.faq-question:hover {
    background-color: #efe9dc;
}

.faq-question.active {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
}

.faq-question h3 {
    margin: 0;
    font-size: 1.2rem;
}

.toggle-icon {
    color: #d4c19c;
}

.faq-answer {
    padding: 15px;
    background-color: #f9f7f2;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
    margin-top: -1px;
    text-align: justify;
}

.faq-answer p {
    margin-bottom: 10px;
}

.faq-answer p:last-child {
    margin-bottom: 0;
}

.guide-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 25px;
    margin-top: 30px;
}

.guide-card {
    padding: 25px;
}

.guide-icon {
    font-size: 2rem;
    color: #d4c19c;
    margin-bottom: 15px;
}

.guide-card h3 {
    margin-bottom: 20px;
}

.guide-card ol {
    padding-left: 20px;
    line-height: 1.7;
}

.guide-card li {
    margin-bottom: 10px;
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
    
    .contact-card {
        flex-direction: column;
        text-align: center;
    }
    
    .contact-icon {
        margin: 0 0 15px 0;
    }
}
</style>