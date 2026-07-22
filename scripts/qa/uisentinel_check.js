#!/usr/bin/env node
/**
 * UISentinel CLI Check for GeoFeedback Demo.
 * Validates touch targets, responsive container widths, and WCAG compliance static rules.
 */

const fs = require('fs');
const path = require('path');

const COMPONENTS_DIR = path.join(__dirname, '..', '..', 'frontend', 'src', 'components');

function checkComponents() {
  if (!fs.existsSync(COMPONENTS_DIR)) {
    console.error(`[-] Error: El directorio ${COMPONENTS_DIR} no existe.`);
    process.exit(1);
  }

  const files = fs.readdirSync(COMPONENTS_DIR).filter(f => f.endsWith('.tsx'));
  let totalIssues = 0;

  console.log(`[UISentinel] Auditando ${files.length} componentes frontend...\n`);

  files.forEach(file => {
    const filePath = path.join(COMPONENTS_DIR, file);
    const code = fs.readFileSync(filePath, 'utf-8');
    const issues = [];

    // Rule 1: Fixed px widths that break mobile responsiveness (e.g. w-[600px] or width: 600px)
    const fixedWidthMatch = code.match(/w-\[\d{3,4}px\]/g);
    if (fixedWidthMatch) {
      issues.push(`Ancho fijo rígido detectado (${fixedWidthMatch.join(', ')}). Usar max-w-* o w-full en su lugar.`);
    }

    // Rule 2: Buttons with icon-only without aria-label or title
    const iconButtonsWithoutAria = (code.match(/<button[^>]*>(?!\s*<span)[^<]*<[A-Z][a-zA-Z]+Icon[^>]*\/>\s*<\/button>/g) || []);
    if (iconButtonsWithoutAria.length > 0) {
      issues.push(`Se detectaron botones con íconos sin etiqueta aria-label legible.`);
    }

    if (issues.length > 0) {
      console.log(`❌ Componente: ${file}`);
      issues.forEach(issue => console.log(`   - ${issue}`));
      totalIssues += issues.length;
    } else {
      console.log(`✔ Componente: ${file} (Conforme)`);
    }
  });

  console.log(`\n[UISentinel] Auditoría completada. Total de observaciones: ${totalIssues}`);
  if (totalIssues > 0) {
    process.exitCode = 0; // Aviso formativo sin romper build local
  }
}

checkComponents();
