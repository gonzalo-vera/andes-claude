# PRD — Andes Construcción Web (reconstrucción técnica)
**Versión:** 2.0  
**Fecha:** Mayo 2026  
**Autor:** Gonzalo Vera (asistido por Claude)  
**Estado:** Activo — producción en Vercel (HTML estático)

---

## 1. Resumen ejecutivo

Andes Construcción es una empresa chilena con más de 20 años de trayectoria en impermeabilización, obras civiles y construcción, con 1.000.000 m² ejecutados. Este PRD define el sitio **oficial en código**: HTML5 semántico, CSS3 sin frameworks, JavaScript vanilla, desplegado en **Vercel**, con enfoque B2B (administradores de edificios, ingeniería, mandantes corporativos), conversión a cotización y medición con **Google Tag Manager (GTM)**, **GA4** y **Microsoft Clarity**.

---

## 2. Problema

| Problema | Impacto |
|---|---|
| Sitio previo genérico y poco diferenciado | No refleja escala ni especialización en impermeabilización y obra |
| Navegación y CTAs débiles | Menos solicitudes de cotización calificadas |
| Prueba social visual limitada | Ingenieros y comités exigen credibilidad rápida (marcas, casos, datos) |
| Falta de páginas por servicio | SEO long-tail y páginas de aterrizaje por especialidad insuficientes |

---

## 3. Objetivos

1. **Aumentar conversiones** — más envíos de formulario y contacto WhatsApp calificado.
2. **Autoridad en &lt; 5 s** — hero, estadísticas, Trust Bar y casos B2B visibles temprano.
3. **Mobile-first** — experiencia impecable desde 320px.
4. **Medición end-to-end** — eventos y funnels vía GTM + GA4; comportamiento con Clarity.

---

## 4. Usuarios objetivo y mensajes

| Segmento | Qué busca | Mensaje clave |
|---|---|---|
| Administradores / comités | Garantía, plazos, menos riesgo de filtraciones | Especialistas en impermeabilización con obra trazable |
| Constructores / mandantes B2B | Capacidad, normativa, coordinación | Equipo técnico, superficie ejecutada, casos verificables |
| Facility / operaciones | Intervención mínima, informes, continuidad | Diagnóstico, propuesta y cierre con documentación |

**Copy:** textos reales en español chileno, **sin Lorem Ipsum**. Tono profesional, preciso, orientado a riesgo y plazo.

---

## 5. Stack técnico (inquebrantable)

| Capa | Tecnología |
|---|---|
| Marcado | HTML5 semántico (`header`, `nav`, `main`, `section`, `article`, `footer`) |
| Estilo | CSS3 puro — custom properties, sin Tailwind/Bootstrap |
| Comportamiento | Vanilla JS (sin bundler obligatorio para el sitio) |
| Imágenes | WebP/JPG optimizado bajo `assets/img/`; logos cliente SVG bajo `assets/logos/` |
| Formularios | [FormSubmit](https://formsubmit.co) — `action`, `_subject`, `_next`, plantilla tabla, honeypot opcional |
| Hosting | **Vercel** — proyecto conectado al repo `gonzalo-vera/andes-claude` |
| Dominio | Producción recomendada: `andesconstruccion.com` (configuración DNS en Vercel) |

### 5.1 Paleta corporativa

| Rol | Hex |
|---|---|
| Navy | `#1A2B4A` |
| Azul corporativo | `#164D7F` |
| Naranja conversión | `#E8821A` |
| Blanco | `#FFFFFF` |
| Gris claro | `#E8E6E6` |

Los tokens viven en `:root` en `styles.css`. No introducir otros colores primarios sin actualizar este PRD.

### 5.2 Analítica y privacidad

- **GTM:** contenedor único en `<head>` y `<body>` según documentación Google.
- **GA4:** configurado vía GTM (o snippet directo si el contenedor lo exige).
- **Microsoft Clarity:** vía GTM o script dedicado según política del sitio.
- **Chile (Ley 19.628):** el sitio debe enlazar política de privacidad / cookies cuando se despliegue trazabilidad de terceros; avisar cookies si se usan tags que lo requieran.

IDs de contenedores **no** se versionan en el PRD; se configuran en el HTML o variables de entorno de despliegue según procedimiento del equipo.

---

## 6. Arquitectura de información y rutas

### 6.1 Árbol publicado

```
/                          → index.html (home)
/servicios/impermeabilizacion.html
/servicios/construccion.html
/servicios/remodelacion.html
/assets/img/               → fotografía comprimida
/assets/logos/             → SVG monocromático Trust Bar
/styles.css
/main.js
```

### 6.2 Rutas relativas (obligatorio)

| Ubicación | `styles.css` | `main.js` | Imágenes |
|---|---|---|---|
| Raíz (`index.html`) | `styles.css` | `main.js` | `assets/img/...` |
| `servicios/*.html` | `../styles.css` | `../main.js` | `../assets/img/...` |

Enlaces internos desde subpáginas al home: `../index.html#seccion`.

### 6.3 FormSubmit — `_next`

La URL de agradecimiento debe incluir `?enviado=1` para que `main.js` muestre el estado de éxito. En despliegues multi-entorno, `_next` puede establecerse dinámicamente con `window.location.origin` (ver implementación en `main.js`).

---

## 7. Requerimientos de producto (home y plantillas)

### RF-01 — Navbar sticky
Transparente sobre hero; fondo navy al superar ~60px de scroll; menú móvil full-screen.

### RF-02 — Estadísticas animadas
Contadores al entrar en viewport (ya implementados); fondo navy.

### RF-03 — Trust Bar
Carrusel **infinito** de logos **monocromáticos** (SVG). Pausa o respeta `prefers-reduced-motion`.

### RF-04 — Servicios
Resumen en home con enlaces a páginas dedicadas en `/servicios/`.

### RF-05 — Casos de éxito B2B
Tarjetas blancas elevadas (reutilización de patrones tipo testimonio/card existentes): cliente/contexto, métrica o alcance, resultado, CTA a contacto.

### RF-06 — Proyectos / galería
Filtros por categoría sin recarga; grid responsivo.

### RF-07 — Testimonios
Citas con rol B2B visible.

### RF-08 — Contacto + WhatsApp
Formulario validado; botón flotante WhatsApp.

### RF-09 — Páginas de servicio
Una por línea de negocio: hero breve, problemas típicos, proceso, diferenciación, CTA, enlaces cruzados. Meta `title` / `description` únicos.

---

## 8. Requerimientos no funcionales

| Área | Criterio |
|---|---|
| Performance | Objetivo Lighthouse mobile ≥ 90; imágenes con peso controlado |
| Accesibilidad | WCAG 2.1 AA — contraste, `alt`, foco teclado, `aria` en nav |
| SEO | `meta description`, canonical, Open Graph, JSON-LD `LocalBusiness` / afín en páginas clave |
| Seguridad | FormSubmit honeypot; no exponer secretos en repo |

---

## 9. Protocolo Git (obligatorio para este proyecto)

Tras modificar archivos con éxito:

```bash
git add .
git commit -m "Descripción clara atómica"
git push origin main
```

El mensaje debe reflejar un cambio lógico coherente (puede agrupar archivos de una misma tarea si el equipo lo acuerda).

---

## 10. Backlog posterior (fuera del alcance mínimo)

- Blog/recursos técnicos SEO.
- Video hero optimizado.
- Calculadora de estimación validada comercialmente.
- Integración CRM / Zapier desde FormSubmit.

---

## 11. KPIs

| Métrica | Meta orientativa |
|---|---|
| Conversión visita → envío formulario | Medir baseline con GA4; mejorar vs. período previo |
| Tiempo en sitio / scroll depth | Segmentar por tráfico orgánico/paid |
| Clarity | Revisar dead clicks y rage clicks en formulario |

---

*Documento vivo. Cambios de negocio o compliance deben reflejarse aquí antes de cambiar contratos visuales o de tracking.*
