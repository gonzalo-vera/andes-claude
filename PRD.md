# PRD — Andes Construcción Web Redesign
**Versión:** 1.0  
**Fecha:** Mayo 2026  
**Autor:** Gonzalo Vera (asistido por Claude)  
**Estado:** Borrador

---

## 1. Resumen ejecutivo

Andes Construcción es una empresa chilena con más de 20 años de trayectoria en impermeabilización, remodelación y construcción, con 1.000.000 m² ejecutados. Su sitio actual (andesconstruccion.com) cumple funciones básicas pero no refleja el nivel de expertise ni la escala de la empresa. Este documento define los requisitos para una versión moderna del sitio que genere más leads, transmita confianza y se posicione competitivamente en el mercado chileno.

---

## 2. Problema

| Problema | Impacto |
|---|---|
| Diseño visual genérico (azul + gris sin identidad) | No diferencia a Andes de la competencia |
| Navegación con ítem "Aprende" poco intuitivo | Confunde a visitantes, reduce exploración |
| Menú oculto en "Más ▼" | Secciones importantes invisibles en primera vista |
| Sin CTA prominente en el menú | Reduce conversión a cotizaciones |
| Hero con imagen única poco impactante | Primera impresión débil |
| Logos de clientes con blur | Elimina el efecto de credibilidad |
| Sin cifras con animación | Stats de impacto pasan desapercibidas |
| Tipografía por defecto de Wix | Sin personalidad ni jerarquía visual clara |

---

## 3. Objetivos

1. **Aumentar conversiones** — incrementar el número de solicitudes de cotización en un 30% en los primeros 3 meses post-lanzamiento.
2. **Transmitir autoridad** — que un visitante nuevo perciba en menos de 5 segundos que Andes es una empresa grande y experimentada.
3. **Reducir tasa de rebote** — mejorar la experiencia de navegación para que los usuarios exploren más de 2 secciones por visita.
4. **Mobile-first** — al menos el 60% del tráfico en Chile viene de móvil; el sitio debe verse perfecto en smartphones.

---

## 4. Usuarios objetivo

| Segmento | Descripción | Qué busca |
|---|---|---|
| **Administradores de edificios** | Condominos, comités de edificios | Impermeabilización confiable, garantía, precio |
| **Empresas constructoras** | Subcontratación de trabajos especializados | Capacidad, certificaciones, experiencia |
| **Particulares** | Propietarios de casas y departamentos | Remodelación, precio transparente, referencias |
| **Empresas con oficinas** | Gerentes de operaciones | Remodelación, rapidez, profesionalismo |

---

## 5. Sitio actual vs. propuesta

### 5.1 Navegación

| Actual | Propuesta | Razón |
|---|---|---|
| Inicio, Servicios, Proyectos, Clientes, Aprende, Contacto, [Más ▼] | Inicio, Servicios, Proyectos, Nosotros, Contacto + botón "Solicitar Cotización" | Menos ítems = más claridad; CTA visible genera conversión |
| Navbar siempre transparente | Navbar transparente → sólida navy al hacer scroll | Mejora legibilidad y sensación de profundidad |
| Sin CTA en menú | Botón naranja "Solicitar Cotización" siempre visible | Punto de conversión disponible en todo momento |

### 5.2 Hero section

| Actual | Propuesta |
|---|---|
| Foto estática de trabajador impermeabilizando | Foto de gran formato de proyecto terminado de alto impacto |
| Texto genérico | Headline fuerte: "Construimos con experiencia y precisión" |
| Sin subtítulo con datos | "Más de 20 años · 1.000.000 m² · 500+ proyectos" |
| Sin doble CTA | "Ver Proyectos" (primario) + "Conocer Servicios" (secundario) |

### 5.3 Paleta de colores

| Actual | Propuesta | Razón |
|---|---|---|
| Azul genérico + gris | Navy `#1A2B4A` + Naranja `#E8821A` | Más distintivo, transmite autoridad + energía |
| Sin jerarquía clara | Blanco `#FFFFFF` para fondos, gris `#F5F5F5` para secciones alternas | Estructura visual clara y respirable |

### 5.4 Tipografía

| Actual | Propuesta |
|---|---|
| Fuente por defecto Wix | **Montserrat 800** para títulos — fuerte, moderna, constructiva |
| Sin jerarquía consistente | **Open Sans 400/600** para cuerpo — legible, profesional |

---

## 6. Requerimientos funcionales

### RF-01: Navbar sticky con cambio de estado
- Transparente sobre el hero
- Fondo navy sólido al superar 60px de scroll
- En mobile: menú hamburguesa que despliega pantalla completa

### RF-02: Sección de estadísticas animadas
- 4 cifras: 20+ años, 1.000.000 m², 500+ proyectos, 100% satisfacción
- Contador animado que se activa al entrar en viewport
- Fondo navy para contraste fuerte

### RF-03: Galería de proyectos con filtros
- Categorías: Todos / Impermeabilización / Construcción / Remodelación
- Filtro por JS sin recarga de página
- Hover overlay con nombre y categoría del proyecto
- Grid responsivo (3 col desktop → 2 col tablet → 1 col mobile)

### RF-04: Formulario de contacto
- Campos: Nombre, Email, Teléfono, Tipo de proyecto (select), Mensaje
- Validación HTML5 nativa
- Feedback visual en submit ("¡Mensaje enviado! ✓")
- Integración con servicio de email (ver mejoras pendientes)

### RF-05: Botón flotante de WhatsApp
- Fijo en esquina inferior derecha
- Enlace directo a WhatsApp con número de la empresa
- Animación sutil de pulso para llamar la atención

### RF-06: Scroll animations
- Elementos aparecen con fade-in + translateY al entrar en viewport
- Delay escalonado en grids (80ms entre items)
- Sin animaciones si el usuario prefiere `prefers-reduced-motion`

---

## 7. Requerimientos no funcionales

| Requisito | Criterio de aceptación |
|---|---|
| **Performance** | Lighthouse score ≥ 90 en mobile |
| **Accesibilidad** | WCAG 2.1 AA — contraste ≥ 4.5:1, alt en imágenes, navegación por teclado |
| **SEO** | Meta tags, Open Graph, datos estructurados Schema.org para LocalBusiness |
| **Mobile** | Sin scroll horizontal en pantallas de 320px+ |
| **Velocidad de carga** | First Contentful Paint < 2.5s en 4G |

---

## 8. Mejoras pendientes (backlog priorizado)

### 🔴 Alta prioridad

#### M-01: Integrar formulario con backend real
**Problema:** El formulario actual solo tiene feedback visual, no envía emails.  
**Solución:** Conectar con Formspree, EmailJS o un endpoint propio.  
**Esfuerzo:** 2h  
**Impacto:** Alto — sin esto no llegan los leads

#### M-02: Reemplazar imágenes de Unsplash con fotos reales
**Problema:** Las imágenes son genéricas y no muestran el trabajo real de Andes.  
**Solución:** Sesión fotográfica de 2-3 proyectos reales + reemplazar en el código.  
**Esfuerzo:** 1 sesión fotográfica + 1h de integración  
**Impacto:** Alto — las fotos propias generan mucha más confianza

#### M-03: SEO básico
**Problema:** No hay meta description, Open Graph ni Schema.org.  
**Solución:** Agregar en `<head>`:
```html
<meta name="description" content="Empresa de construcción e impermeabilización en Chile con más de 20 años de experiencia. Cotiza gratis." />
<meta property="og:title" content="Andes Construcción" />
<meta property="og:image" content="URL_imagen_preview" />
```
Y agregar Schema.org `LocalBusiness`.  
**Esfuerzo:** 1h  
**Impacto:** Alto — afecta directamente el posicionamiento en Google

#### M-04: Google Analytics / Tag Manager
**Problema:** Sin métricas no se puede medir el éxito del rediseño.  
**Solución:** Instalar GA4 o GTM.  
**Esfuerzo:** 30min  
**Impacto:** Alto — necesario para tomar decisiones basadas en datos

---

### 🟡 Media prioridad

#### M-05: Página de Servicios individual
**Problema:** Cada servicio merece su propia página con más detalle para SEO y conversión.  
**Solución:** Crear `servicios/impermeabilizacion.html`, `servicios/construccion.html`, `servicios/remodelacion.html` con proceso, materiales, galería específica y CTA.  
**Esfuerzo:** 6h  
**Impacto:** Medio-alto — mejora SEO long-tail y conversión por servicio

#### M-06: Sección de certificaciones y garantías
**Problema:** Se menciona "garantía certificada" pero no se muestra ningún certificado o logo de certificación.  
**Solución:** Agregar logos de certificaciones (ISO, SEC, etc.) y descripción de la garantía.  
**Esfuerzo:** 2h  
**Impacto:** Medio — aumenta credibilidad

#### M-07: Chat en vivo o WhatsApp widget mejorado
**Problema:** El botón de WhatsApp es básico.  
**Solución:** Usar un widget de WhatsApp Business con mensaje pre-cargado ("Hola, me interesa una cotización para...").  
**Esfuerzo:** 1h  
**Impacto:** Medio — reduce fricción de contacto

#### M-08: Testimonios con fotos reales y reseñas de Google
**Problema:** Los testimonios actuales son texto genérico sin cara visible.  
**Solución:** Integrar Google Reviews widget o agregar fotos reales de clientes con su permiso.  
**Esfuerzo:** 2h  
**Impacto:** Medio — social proof más creíble

---

### 🟢 Baja prioridad

#### M-09: Blog / Artículos de construcción
**Problema:** La app de Blog de Wix existe pero no hay contenido.  
**Solución:** Crear 5-10 artículos sobre temas que los clientes buscan ("cómo impermeabilizar una terraza", "cuánto cuesta remodelar una cocina").  
**Esfuerzo:** 2-3h por artículo  
**Impacto:** Medio (largo plazo) — genera tráfico orgánico sostenido

#### M-10: Video corporativo en el Hero
**Problema:** El hero con imagen estática tiene menos impacto que un video.  
**Solución:** Grabar video de 30-60s de obras en proceso y terminadas, usarlo como background del hero con autoplay/muted.  
**Esfuerzo:** 1 día de grabación + edición  
**Impacto:** Bajo-medio — mejora impresión pero no es esencial

#### M-11: Calculadora de presupuesto estimado
**Problema:** Los clientes quieren una idea de precio antes de contactar.  
**Solución:** Formulario interactivo con sliders (m², tipo de proyecto) que estima un rango de precio.  
**Esfuerzo:** 8h  
**Impacto:** Alto en conversión, pero requiere validación con el equipo comercial

---

## 9. Arquitectura de información propuesta

```
andesconstruccion.com/
├── / (Home)
│   ├── Hero
│   ├── Estadísticas
│   ├── Servicios (resumen)
│   ├── Por qué elegirnos
│   ├── Proyectos destacados
│   ├── Testimonios
│   └── Contacto (mini)
├── /servicios
│   ├── /impermeabilizacion
│   ├── /construccion
│   └── /remodelacion
├── /proyectos
├── /nosotros
├── /blog
│   └── /[slug]
└── /contacto
```

---

## 10. KPIs de éxito

| Métrica | Baseline actual | Meta 3 meses |
|---|---|---|
| Tasa de conversión (visitas → formulario) | Desconocida | ≥ 3% |
| Tiempo en sitio | Desconocido | ≥ 2:30 min |
| Tasa de rebote | Desconocida | ≤ 55% |
| Posición Google "impermeabilización Santiago" | Desconocida | Top 10 |
| Leads mensuales vía web | Desconocido | +30% vs. baseline |

---

## 11. Stack técnico actual (prototipo)

| Capa | Tecnología |
|---|---|
| HTML | HTML5 semántico |
| CSS | CSS puro con custom properties, sin framework |
| JS | Vanilla JS (sin dependencias) |
| Fuentes | Google Fonts (Montserrat + Open Sans) |
| Imágenes | Unsplash (temporal — reemplazar con fotos reales) |
| Hosting | GitHub Pages (temporal) / Wix (producción) |

**Nota sobre Wix:** El prototipo actual es HTML estático. Para producción, el diseño debe trasladarse al editor de Wix para mantener la capacidad de edición sin código por parte del equipo de Andes. Alternativamente, migrar a un hosting propio si se quiere más control técnico.

---

*Este documento es un borrador vivo. Actualizar con feedback del equipo de Andes Construcción.*
