<template>
    <div>
        <h1>EntrenIA</h1>
        <p>Texto de inicio.</p>
    </div>
</template>

<style scoped src="@/assets/styles/info.css"></style>

<script setup>
import { onMounted } from 'vue';
import axios from 'axios';
import { notifySuccess, notifyError, notifyInfo } from '@/utils/notifications';

onMounted(async () => {
  try {
    const queryParams = new URLSearchParams(window.location.search);
    const token = queryParams.get('token');
    
    if (token) {
      try {

        await axios.post(`/signup/account-verification?token=${token}`, {});
        
        notifySuccess(
          'Cuenta verificada', 
          'Tu cuenta ha sido verificada con éxito. Ahora puedes iniciar sesión.'
        );
        
        
      } catch (error) {
        if (error.response) {
          const status = error.response.status;
          const detail = error.response.data.detail || 'Error desconocido';
          
          if (status === 400) {
            notifyError('Error de verificación', 
            'El token de verificación no es válido o ha expirado.');
          } else if (status === 404) {
            notifyError('Error de verificación', 
            'No se encontró ninguna cuenta asociada.');
          } else if (status === 409) {
            notifyInfo('Cuenta verificada anteriormente', 
            'Tu identidad ya ha sido verificada anteriormente. Puedes iniciar sesión.');
          } else {
            notifyError('Error de verificación', 
            "Ha ocurrido un error de verificación.");
          }
        } else {
          notifyError('Error de conexión', 
          'No se pudo conectar con el servidor. Verifica tu conexión a internet.');
        }
      } finally {
        // Limpiar el token de la URL sin recargar la página
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  } catch (e) {
    console.error('Error while processing the verification: ', e);
  }
});
</script>