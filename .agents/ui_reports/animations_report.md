# Guía de Microinteracciones y Rendimiento de Animaciones

## Principios de Animación de Interfaz
1. **Transiciones Suaves:** Limitar duraciones a 150ms-250ms para respuestas inmediatas a clics y hovers.
2. **Propiedades Performantes:** Animar exclusivamente `transform` y `opacity` para evitar gatillar operaciones de Reflow o Repaint en el navegador.

## Ejemplo de Optimización de Microinteracciones

```css
/* Recomendado: Animación por Hardware Acceleration */
.btn-geo-action {
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.2s ease;
  will-change: transform;
}

.btn-geo-action:hover {
  transform: translateY(-2px);
}
```
