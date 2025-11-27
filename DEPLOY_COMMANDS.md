# 🚀 Comandos para Deploy Post-Limpieza

## Resumen de Limpieza

✅ **Archivos eliminados**: 16 archivos/carpetas obsoletos relacionados con PostgreSQL  
✅ **Archivos actualizados**: app.py, Dockerfile, requirements.txt, README.md  
✅ **Backups creados**: 3 archivos movidos a `/backups`  
✅ **Documentación**: CLEANUP_LOG.md creado

---

## 📦 Commit y Push (Ejecutar en orden)

### Opción 1: Commit Todo de una Vez (Recomendado)

```bash
cd c:\Users\alean\Desktop\Geofeedback\Demo

# Agregar todos los cambios
git add -A

# Commit con mensaje descriptivo
git commit -m "chore: Limpieza completa del proyecto - eliminación de dependencias PostgreSQL

- Eliminados 16 archivos/carpetas obsoletos relacionados con BD
- Simplificado api/app.py (539 → 250 líneas)
- Optimizado Dockerfile (71 → 18 líneas)  
- Reducidas dependencias (7 → 3 packages)
- Creados backups de versiones anteriores
- Actualizado README con arquitectura simplificada
- Agregado CLEANUP_LOG.md con detalles de limpieza"

# Push a Railway (auto-deploya)
git push origin main
```

### Opción 2: Commits Separados (Para mejor historial)

```bash
cd c:\Users\alean\Desktop\Geofeedback\Demo

# 1. Commit de archivos eliminados
git add -u
git commit -m "chore: Eliminar archivos obsoletos de PostgreSQL/PostGIS"

# 2. Commit de archivos nuevos (backups, docs)
git add backups/ CLEANUP_LOG.md
git commit -m "docs: Agregar backups y documentación de limpieza"

# 3. Commit de archivos actualizados
git add README.md
git commit -m "docs: Actualizar README con arquitectura simplificada"

# 4. Push todo
git push origin main
```

---

## ✅ Verificación Post-Deploy

Una vez que hagas push, Railway desplegará automáticamente (~1.5 minutos).

### URLs para verificar:

```bash
# 1. Landing page
https://demogeofeedback-production.up.railway.app/

# 2. Health check
https://demogeofeedback-production.up.railway.app/api/v1/health

# 3. Estadísticas
https://demogeofeedback-production.up.railway.app/api/v1/stats

# 4 Infraestructura
https://demogeofeedback-production.up.railway.app/api/v1/infrastructure
```

### Checklist de Verificación:

- [ ] Build exitoso en Railway (sin errores)
- [ ] Landing page carga correctamente
- [ ] `/api/v1/health` retorna `{"status": "healthy"}`
- [ ] `/api/v1/stats` muestra 20 instalaciones
- [ ] `/api/v1/infrastructure` devuelve lista de 5 instalaciones
- [ ] Logs de Railway no muestran errores
- [ ] Consumo de RAM < 100 MB

---

## 🎉 Próximos Pasos

Después de verificar que todo funciona:

1. ✅ **Limpieza completada**
2. ✅ **Deploy mínimo funcionando**
3. ⏩ **Preparar para próxima fase de desarrollo**

---

*Creado: 26 de noviembre de 2025*
