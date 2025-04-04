import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UploadResultModal from '@/components/images/UploadResultModal.vue'

// Mock para FontAwesome
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

describe('UploadResultModal.vue', () => {
  // Datos de prueba para los tests
  const testStats = {
    processed_images: 5,
    skipped_images: 2,
    invalid_images: 1,
    labels_applied: 3,
    labels_skipped: 2
  }
  
  const testInvalidImages = ['imagen1.txt', 'imagen2.doc']
  const testDuplicatedImages = ['duplicado1.jpg', 'duplicado2.png']
  const testSkippedLabels = ['imagen_no_subida.jpg,gato', 'otra_imagen.png,perro']

  // Test 1: El modal se muestra correctamente cuando show es true
  it('se muestra cuando la propiedad show es true', () => {
    const wrapper = mount(UploadResultModal, {
      props: {
        show: true,
        stats: testStats
      }
    })
    
    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.result-modal').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toContain('Resultados de la subida')
  })
  
  // Test 2: El modal no se muestra cuando show es false
  it('no se muestra cuando la propiedad show es false', () => {
    const wrapper = mount(UploadResultModal, {
      props: {
        show: false,
        stats: testStats
      }
    })
    
    expect(wrapper.find('.modal-overlay').exists()).toBe(false)
  })
  
  // Test 3: Muestra correctamente las estadísticas de subida
  it('muestra correctamente las estadísticas de la subida', () => {
    const wrapper = mount(UploadResultModal, {
      props: {
        show: true,
        stats: testStats
      }
    })
    
    // Verificar estadísticas de imágenes procesadas
    const statValues = wrapper.findAll('.stat-value')
    expect(statValues[0].text()).toBe('5') // processed_images
    expect(statValues[1].text()).toBe('3') // labels_applied
    
    // Verificar mensaje de éxito
    expect(wrapper.find('.message-card.success').exists()).toBe(true)
    expect(wrapper.find('.message-card.success p').text()).toContain('Se han añadido 5 imágenes')
  })
  
  // Test 4: Muestra correctamente las incidencias cuando existen
  it('muestra las incidencias cuando hay problemas en la subida', () => {
    const wrapper = mount(UploadResultModal, {
      props: {
        show: true,
        stats: testStats,
        invalidImageDetails: testInvalidImages,
        duplicatedImageDetails: testDuplicatedImages,
        skippedLabelDetails: testSkippedLabels
      }
    })
    
    // Verificar sección de incidencias
    expect(wrapper.find('.issues-section').exists()).toBe(true)
    
    // Verificar que se muestran los tres tipos de incidencias
    const issueItems = wrapper.findAll('.issue-item')
    expect(issueItems.length).toBe(3)
    
    // Verificar texto de incidencias
    expect(issueItems[0].text()).toContain('Imágenes omitidas: 2')
    expect(issueItems[1].text()).toContain('Imágenes inválidas: 1')
    expect(issueItems[2].text()).toContain('Etiquetas no aplicadas: 2')
  })
  
  // Test 5: Cambia de vista al hacer clic en una incidencia y vuelve al resumen
  it('navega entre la vista de resumen y los detalles de incidencias', async () => {
    const wrapper = mount(UploadResultModal, {
      props: {
        show: true,
        stats: testStats,
        invalidImageDetails: testInvalidImages,
        duplicatedImageDetails: testDuplicatedImages,
        skippedLabelDetails: testSkippedLabels
      }
    })
    
    // Verificar que inicia en la vista de resumen
    expect(wrapper.find('.summary-view').exists()).toBe(true)
    
    // Hacer clic en ver detalles de imágenes duplicadas
    await wrapper.findAll('.issue-item')[0].trigger('click')
    
    // Verificar que cambia a la vista de detalles
    expect(wrapper.find('.summary-view').exists()).toBe(false)
    expect(wrapper.find('.detail-view').exists()).toBe(true)
    expect(wrapper.find('.detail-title').text()).toBe('Imágenes omitidas')
    
    // Verificar que se muestran las imágenes duplicadas
    const detailItems = wrapper.findAll('.detail-item')
    expect(detailItems.length).toBe(2)
    expect(detailItems[0].text()).toContain('duplicado1.jpg')
    
    // Volver al resumen
    await wrapper.find('.back-button').trigger('click')
    
    // Verificar que vuelve a la vista de resumen
    expect(wrapper.find('.summary-view').exists()).toBe(true)
  })
})