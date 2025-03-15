<template>
  <div id="app">
    <NavBar v-if="$route.meta.showNav !== false" />
    <main class="content">
      <RouterView />
    </main>
    <Footer v-if="$route.meta.showFooter !== false" />
  </div>
</template>

<script setup>
import NavBar from './components/general/NavBar.vue';
import Footer from './components/general/Footer.vue';
</script>
