import os
import re

def main():
    print("Iniciando refactorización completa...")
    
    app_path = 'app.py'
    template_path = 'templates/index.html'
    
    # 1. Leer app.py
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 2. Extraer LANDING_HTML
    start_marker = "LANDING_HTML = '''"
    end_marker = "'''"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("ERROR: No se encontró LANDING_HTML")
        return
        
    start_content = start_idx + len(start_marker)
    # Buscar el final starting search from start_content
    end_idx = content.find(end_marker, start_content)
    
    if end_idx == -1:
        print("ERROR: No se encontró el final de LANDING_HTML")
        return
        
    html = content[start_content:end_idx]
    print(f"HTML extraído: {len(html)} caracteres")
    
    # 3. Inyección de Fire-Risk (Defensivo)
    
    # Check JS approaches
    if '"fire-risk": {' not in html:
        print("Inyectando objeto JS fire-risk...")
        js_insertion_point = 'var approaches = {'
        fire_risk_js = """
            "fire-risk": {
                name: "Riesgo de Incendio Forestal",
                icon: "fire",
                indices: [
                    { name: "Vegetacion Seca (NDVI)", api: "Sentinel-2", desc: "Areas con baja humedad vegetal.", color: "#dc2626" },
                    { name: "Humedad Vegetacion (NDMI)", api: "Sentinel-2", desc: "Contenido de agua en plantas.", color: "#f97316" },
                    { name: "Pendiente", api: "Elevation", desc: "Dificultad de acceso para combate.", color: "#95a5a6" }
                ]
            },"""
        html = html.replace(js_insertion_point, js_insertion_point + fire_risk_js)
    else:
        print("Objeto JS fire-risk ya existe.")

    # Check Select Option
    if 'value="fire-risk"' not in html:
        print("Inyectando opción select fire-risk...")
        # Intentar insertar en el grupo de Analisis General o al final
        if '<optgroup label="Analisis General">' in html:
            html = html.replace('<optgroup label="Analisis General">', 
                                '<optgroup label="Analisis General">\n                                <option value="fire-risk">Riesgo de Incendio Forestal</option>')
        else:
            # Fallback a insertarlo antes del cierre del select si no encuentra optgroup
            html = html.replace('</select>', '<option value="fire-risk">Riesgo de Incendio Forestal</option>\n                        </select>')
    else:
        print("Opción select fire-risk ya existe.")

    # Check JS functions addMapLegend
    if 'function addMapLegend()' not in html:
        print("Inyectando funciones de leyenda...")
        legend_js = """
        function addMapLegend() {
            removeMapLegend();
            var legendDiv = document.createElement('div');
            legendDiv.id = 'fire-risk-legend';
            legendDiv.style.cssText = 'position:absolute; bottom:30px; left:10px; background:rgba(255,255,255,0.95); padding:12px 16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.25); font-family:Inter,sans-serif; z-index:1000; max-width:200px;';
            
            var title = document.createElement('div');
            title.textContent = 'Riesgo de Incendio';
            title.style.cssText = 'font-weight:600; font-size:0.85rem; margin-bottom:8px; color:#1e3a5f;';
            legendDiv.appendChild(title);
            
            var scale = [
                { color: '#22c55e', label: 'Bajo' },
                { color: '#84cc16', label: 'Moderado' },
                { color: '#eab308', label: 'Alto' },
                { color: '#f97316', label: 'Muy Alto' },
                { color: '#dc2626', label: 'Extremo' }
            ];
            
            for (var i = 0; i < scale.length; i++) {
                var item = document.createElement('div');
                item.style.cssText = 'display:flex; align-items:center; margin:4px 0; font-size:0.75rem;';
                var colorBox = document.createElement('div');
                colorBox.style.cssText = 'width:20px; height:14px; background:' + scale[i].color + '; border-radius:3px; margin-right:8px;';
                var label = document.createElement('span');
                label.textContent = scale[i].label;
                label.style.color = '#374151';
                item.appendChild(colorBox);
                item.appendChild(label);
                legendDiv.appendChild(item);
            }
            document.getElementById('demo-map').appendChild(legendDiv);
        }
        function removeMapLegend() {
            var existing = document.getElementById('fire-risk-legend');
            if (existing) { existing.remove(); }
        }
        """
        # Insertar antes de analyzeterritory
        if 'function analyzeTerritory()' in html:
             html = html.replace('function analyzeTerritory()', legend_js + '\n        function analyzeTerritory()')
        else:
             # Insertar al final del script si no encuentra anchor
             html = html.replace('</script>', legend_js + '\n    </script>')
             
    # 3.1 Fix GEE Layer logic to call addMapLegend
    # Buscar donde se añade la capa GEE y asegurar que llame a la leyenda
    if "if (selectedApproach === 'fire-risk') {" not in html:
        print("Actualizando lógica de capa GEE para leyenda...")
        chunk_to_find = 'console.log("Capa GEE agregada: " + data.map_layer.url);'
        replacement_chunk = """console.log("Capa GEE agregada: " + data.map_layer.url);
                        
                        if (selectedApproach === 'fire-risk') {
                            addMapLegend();
                        } else {
                            removeMapLegend();
                        }"""
        html = html.replace(chunk_to_find, replacement_chunk)


    # 4. Corregir Sintaxis JS
    html = html.replace(r'\u003c', '<').replace(r'\u003e', '>')

    # 5. Reordenar Secciones
    print("Reordenando secciones...")
    
    # Helper getters
    def get_block(pattern, text):
        m = re.search(pattern, text, re.DOTALL)
        return m.group(0) if m else ""

    # Extraer bloques (Ids y clases conocidas)
    header = html[:html.find('<section')] # Todo hasta el primer section
    
    # Buscar footer (asumiendo que está al final, fuera de sections o es el ultimo tag)
    # Buscamos el último </footer> y tomamos desde ahí hacia atrás hasta que empiece
    # Mejor estrategia: Footer suele estar despues del ultimo section.
    
    # Identificar sections
    hero = get_block(r'<section class="hero">.*?</section>', html)
    if not hero: hero = get_block(r'<section id="hero".*?</section>', html)
    
    problema = get_block(r'<section id="problema".*?</section>', html)
    solucion = get_block(r'<section id="solucion".*?</section>', html)
    indices = get_block(r'<section id="indices".*?</section>', html)
    
    # Demo necesita modificacion de estilo para padding
    demo_raw = get_block(r'<section id="demo".*?</section>', html)
    demo = demo_raw.replace('class="demo-section"', 'class="demo-section" style="padding-top: 8rem;"')
    
    servicios = get_block(r'<section id="servicios".*?</section>', html)
    
    # Equipo - busqueda agresiva
    equipo = get_block(r'<section class="team-section".*?</section>', html)
    if not equipo: 
        equipo = get_block(r'<section.*?>.*?Nuestro Equipo.*?</section>', html)
    
    contacto = get_block(r'<section class="contact-section".*?</section>', html)
    
    # Footer y scripts
    # Asumimos que contacto es la ultima seccion.
    if contacto:
        last_idx = html.find(contacto) + len(contacto)
        footer_scripts = html[last_idx:]
    else:
        # Fallback si no encuentra contacto
        footer_scripts = html[html.rfind('</footer>')-7:] # Aprox
    
    # Verificar que tenemos todo
    missing = []
    if not demo: missing.append("demo")
    if not equipo: missing.append("equipo")
    if not hero: missing.append("hero")
    
    if missing:
        print(f"ERROR CRITICO: No se encontraron secciones clave: {missing}. Abortando reordenamiento, guardando HTML sin reordenar pero con inyecciones.")
        final_html = html # Fallback safe
    else:
        # Construir nuevo orden
        # Nav -> Demo -> Equipo -> Hero -> Problema -> Solución -> Índices -> Servicios -> Contacto -> Footer
        
        # Ojo: header contiene el Navbar
        
        final_html = (
            header + "\n" +
            demo + "\n" +
            equipo + "\n" +
            hero + "\n" +
            problema + "\n" +
            solucion + "\n" +
            indices + "\n" +
            servicios + "\n" +
            contacto + "\n" +
            footer_scripts
        )

    # 6. Guardar Template
    os.makedirs('templates', exist_ok=True)
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Template guardado en {template_path}")

    # 7. Modificar app.py (Solo cambiar la funcion landing)
    # Vamos a usar replace de string simple
    new_landing_func = """@app.route('/')
def landing():
    google_maps_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    if not google_maps_key:
        print("WARNING: GOOGLE_MAPS_API_KEY not found in environment variables.")
    else:
        print(f"INFO: GOOGLE_MAPS_API_KEY found (length: {len(google_maps_key)})")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return html.replace('GOOGLE_MAPS_KEY_PLACEHOLDER', google_maps_key)
    except Exception as e:
        print(f"Error template: {e}")
        return LANDING_HTML.replace('GOOGLE_MAPS_KEY_PLACEHOLDER', google_maps_key)
"""
    
    # Buscar la funcion landing actual y reemplazarla
    # Es dificil reemplazar bloque exacto con regex si cambio.
    # Pero sabemos que empieza con @app.route('/') y termina antes de @app.route('/api/v1/health')
    
    start_route = "@app.route('/')"
    next_route = "@app.route('/api/v1/health')"
    
    idx_start = content.find(start_route)
    idx_end = content.find(next_route)
    
    if idx_start != -1 and idx_end != -1:
        prefix = content[:idx_start]
        suffix = content[idx_end:]
        new_app_content = prefix + new_landing_func + "\n" + suffix
        
        # Eliminar LANDING_HTML para limpiar? No, dejemoslo como fallback por seguridad y el usuario lo pidio limpiar despues.
        # El user dijo "actualiza la documentacion", no especificamente borrar LANDING_HTML ahora.
        # Pero para que sea "complete implementation", mejor dejarlo limpio? 
        # No, el riesgo de romper app.py eliminando la variable gigante es alto. Mejor dejarla y solo cambiar la ruta.
        
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_app_content)
        print("app.py actualizado exitosamente.")
    else:
        print("Error al localizar funcion landing en app.py")

if __name__ == "__main__":
    main()
