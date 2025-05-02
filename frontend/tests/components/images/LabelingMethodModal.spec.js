import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LabelingMethodModal from '@/components/images/LabelingMethodModal.vue'

// Mock para FontAwesome.
vi.mock('@fortawesome/vue-fontawesome', () => ({
  FontAwesomeIcon: {
    name: 'FontAwesomeIcon',
    template: '<span class="mock-icon"></span>'
  }
}))

// Mock para Teleport.
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    Teleport: {
      name: 'Teleport',
      template: '<div><slot /></div>'
    }
  }
})

describe('LabelingMethodModal.vue', () => {
  // Test 1: Visualización del modal.
  it('muestra el modal cuando isOpen es true', () => {
    const wrapper = mount(LabelingMethodModal, {
      props: {
        isOpen: true,
        unlabeledCount: 10
      }
    })
    
    // Verificar que el componente existe.
    expect(wrapper.exists()).toBe(true)
    
    // Verificar que el modal está visible.
    expect(wrapper.find('.labeling-method-modal').exists()).toBe(true)
    
    // Verificar que muestra el número correcto de imágenes sin etiquetar.
    // Comparamos con el texto específico que debe contener.
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('imágenes sin etiquetar')
  })
  
  // Test 2: Ocultamiento del modal.
  it('oculta el modal cuando isOpen es false', () => {
    const wrapper = mount(LabelingMethodModal, {
      props: {
        isOpen: false,
        unlabeledCount: 10
      }
    })
    
    // Verificar que el modal no está visible.
    expect(wrapper.find('.modal-overlay').exists()).toBe(false)
  })
  
  // Test 3: Emite evento close al hacer clic en el botón de cierre.
  it('emite evento close al hacer clic en el botón de cierre', async () => {
    const wrapper = mount(LabelingMethodModal, {
      props: {
        isOpen: true,
        unlabeledCount: 10
      }
    })
    
    // Verificar que el botón existe antes de hacer clic.
    const closeButton = wrapper.find('.close-modal-button')
    expect(closeButton.exists()).toBe(true)
    
    // Hacer clic en el botón de cierre.
    await closeButton.trigger('click')
    
    // Verificar que se emite el evento close.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 4: Emite evento select-method con 'manual' al seleccionar etiquetado manual.
  it('emite evento select-method con valor "manual" al seleccionar etiquetado manual', async () => {
    const wrapper = mount(LabelingMethodModal, {
      props: {
        isOpen: true,
        unlabeledCount: 10
      }
    })
    
    // Encontrar todas las tarjetas de método.
    const cards = wrapper.findAll('.method-card')
    expect(cards.length).toBeGreaterThan(0) // Verificar que hay tarjetas.
    
    // Hacer clic en la primera tarjeta (etiquetado manual).
    await cards[0].trigger('click')
    
    // Verificar que se emitió el evento con el valor correcto.
    expect(wrapper.emitted('select-method')).toBeTruthy()
    expect(wrapper.emitted('select-method')[0][0]).toBe('manual')
    
    // Verificar que también se emitió el evento close.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
  
  // Test 5: Emite evento select-method con 'csv' al seleccionar importar CSV.
  it('emite evento select-method con valor "csv" al seleccionar importar CSV', async () => {
    const wrapper = mount(LabelingMethodModal, {
      props: {
        isOpen: true,
        unlabeledCount: 10
      }
    })
    
    // Encontrar todas las tarjetas de método.
    const cards = wrapper.findAll('.method-card')
    expect(cards.length).toBeGreaterThan(1) // Verificar que hay al menos 2 tarjetas.
    
    // Hacer clic en la segunda tarjeta (importar CSV).
    await cards[1].trigger('click')
    
    // Verificar que se emitió el evento con el valor correcto.
    expect(wrapper.emitted('select-method')).toBeTruthy()
    expect(wrapper.emitted('select-method')[0][0]).toBe('csv')
    
    // Verificar que también se emitió el evento close.
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})