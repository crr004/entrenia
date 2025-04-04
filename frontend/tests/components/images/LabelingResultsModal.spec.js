import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LabelingResultsModal from '@/components/images/LabelingResultsModal.vue'

// Mock para FontAwesome
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

describe('LabelingResultsModal.vue', () => {
  // Datos de prueba para los tests
  const successResult = {
    labeled_count: 10,
    not_found_count: 2,
    not_found_details: ['imagen1.jpg', 'imagen2.jpg']
  }
  
  const emptyResult = {
    labeled_count: 0,
    not_found_count: 0,
    not_found_details: []
  }

  // Test 1: Visualización del modal
  it('muestra el modal cuando isOpen es true', () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: successResult
      }
    })
    
    // Verificar que el modal está visible
    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.result-modal').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toBe('Resumen del etiquetado')
  })
  
  // Test 2: Ocultamiento del modal
  it('no muestra el modal cuando isOpen es false', () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: false,
        result: successResult
      }
    })
    
    // Verificar que el modal no está visible
    expect(wrapper.find('.modal-overlay').exists()).toBe(false)
  })
  
  // Test 3: Normalización de resultados
  it('normaliza correctamente los resultados con diferentes formatos de nombres de propiedades', () => {
    const snakeCaseResult = {
      labeled_count: 10,
      not_found_count: 2,
      not_found_details: ['imagen1.jpg', 'imagen2.jpg']
    }
    
    const camelCaseResult = {
      labeledCount: 10,
      notFoundCount: 2,
      notFoundDetails: ['imagen1.jpg', 'imagen2.jpg']
    }
    
    // Test con snake_case
    const wrapperSnake = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: snakeCaseResult
      }
    })
    
    // Test con camelCase
    const wrapperCamel = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: camelCaseResult
      }
    })
    
    // Verificar que ambos formatos se normalizan correctamente
    expect(wrapperSnake.find('.stat-value').text()).toBe('10') // labeled_count
    expect(wrapperCamel.find('.stat-value').text()).toBe('10') // labeledCount
  })
  
  // Test 4: Muestra mensaje de éxito cuando hay etiquetas aplicadas
  it('muestra mensaje de éxito cuando hay etiquetas aplicadas', () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: successResult
      }
    })
    
    // Verificar que se muestra el mensaje de éxito
    expect(wrapper.find('.message-card.success').exists()).toBe(true)
    expect(wrapper.find('.message-card.success p').text()).toContain('¡Etiquetado completado!')
    expect(wrapper.find('.message-card.success p').text()).toContain('10')
  })
  
  // Test 5: Muestra mensaje de error cuando no hay etiquetas aplicadas
  it('muestra mensaje de error cuando no hay etiquetas aplicadas', () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: emptyResult
      }
    })
    
    // Verificar que se muestra el mensaje de error
    expect(wrapper.find('.message-card.error').exists()).toBe(true)
    expect(wrapper.find('.message-card.error p').text()).toContain('No se ha podido aplicar ninguna etiqueta')
  })
  
  // Test 6: Navega entre vistas de resumen y detalle
  it('navega entre la vista de resumen y detalle', async () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: successResult
      }
    })
    
    // Verificar que inicia en la vista de resumen
    expect(wrapper.find('.summary-view').exists()).toBe(true)
    
    // Hacer clic en "Ver detalles" para ver las etiquetas no aplicadas
    await wrapper.find('.issue-item').trigger('click')
    
    // Verificar que cambia a la vista de detalle
    expect(wrapper.find('.summary-view').exists()).toBe(false)
    expect(wrapper.find('.detail-view').exists()).toBe(true)
    expect(wrapper.find('.detail-title').text()).toBe('Etiquetas no aplicadas')
    
    // Verificar que se muestran los detalles correctos
    const detailItems = wrapper.findAll('.detail-item')
    expect(detailItems.length).toBe(2)
    expect(detailItems[0].text()).toContain('imagen1.jpg')
    
    // Volver al resumen
    await wrapper.find('.back-button').trigger('click')
    
    // Verificar que vuelve a la vista de resumen
    expect(wrapper.find('.summary-view').exists()).toBe(true)
    expect(wrapper.find('.detail-view').exists()).toBe(false)
  })
  
  // Test 7: Cierra el modal al hacer clic en el botón Aceptar
  it('emite evento close al hacer clic en el botón Aceptar', async () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: successResult
      }
    })
    
    // Hacer clic en el botón Aceptar
    await wrapper.find('.app-button').trigger('click')
    
    // Verificar que se emitió el evento close
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 8: Cierra el modal al hacer clic en el botón X
  it('emite evento close al hacer clic en el botón de cierre', async () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: successResult
      }
    })
    
    // Hacer clic en el botón de cierre
    await wrapper.find('.close-modal-button').trigger('click')
    
    // Verificar que se emitió el evento close
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 9: Restablece la vista al abrir el modal
  it('restablece la vista a summary cuando el modal se abre', async () => {
    const wrapper = mount(LabelingResultsModal, {
      props: {
        isOpen: true,
        result: successResult
      }
    })
    
    // Cambiar a la vista de detalle
    await wrapper.find('.issue-item').trigger('click')
    expect(wrapper.find('.detail-view').exists()).toBe(true)
    
    // Cerrar el modal
    await wrapper.setProps({ isOpen: false })
    
    // Volver a abrir el modal
    await wrapper.setProps({ isOpen: true })
    
    // Verificar que se restablece a la vista de resumen
    expect(wrapper.find('.summary-view').exists()).toBe(true)
    expect(wrapper.find('.detail-view').exists()).toBe(false)
  })
})