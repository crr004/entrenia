<template>
    <footer>
        <div class="footer">
            <div class="footer-links">
                <router-link to="/help" class="footer-link">Ayuda</router-link>
            </div>
            <p class="copyright">&copy; 2025 EntrenIA</p>
        </div>
    </footer>
</template>

<script setup>
</script>

<style scoped>
.footer-links {
    margin-bottom: 12px;
}

.footer-link {
    color: #838383;
    text-decoration: none;
    font-size: 0.95rem;
    transition: color 0.3s ease;
}

.footer-link:hover {
    color: rgb(34, 134, 141);
}

.separator {
    margin: 0 10px;
    color: #8a8a8a;
}

.copyright {
    color: #8a8a8a;
    font-size: 0.9rem;
}
</style>