# GeoFeedback Frontend (React 19 + TypeScript + Vite)

Módulo frontend del sistema **GeoFeedback Chile**. Construido con **React 19**, **TypeScript**, **Vite**, **Tailwind CSS / DaisyUI**, **Google Maps JavaScript API** y **Playwright**.

> 📚 **Documentación Técnica Completa:** Para acceder a la arquitectura completa, guía del marco multi-capa de QA (Playwright, WCAG 2.1 AA, Lighthouse CI), componentes e integración con GeoBot, consulte el documento principal [DOCS.md](../DOCS.md).

---

## 🚀 Inicio Rápido Local

### 1. Instalación
```bash
cd frontend
npm install
```

### 2. Servidor de Desarrollo
```bash
npm run dev
```

### 3. Build de Producción
```bash
npm run build
```

---

## 🧪 Pruebas E2E y QA
```bash
# Ejecutar suite completa de pruebas Playwright (Visual Regression, Layout, Accessibility)
npm run test:e2e

# Actualizar capturas de referencia (Snapshots)
npm run test:e2e:update-snapshots
```

---

_Última actualización: Julio de 2026_
