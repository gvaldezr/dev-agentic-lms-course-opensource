// ============================================================
// Mini Sitio — Comunidades Virtuales · UADY
// SPA con hash routing + progreso + whimsy (Ruta del Jaguar Digital)
// ============================================================
import { ASSETS } from './assets.js';
import { CONTENT } from './content.js';
import { LECTURAS } from './lecturas.js';

// ---- Metadatos de las 5 ADAs (de outline_curso.json + visual_narrative.md) ----
const ADAS = [
  { n: 1, acto: 'I · Observar',  emoji: '📡', titulo: 'Perfil Profesional del CM',
    producto: 'Infografía Interactiva: Radiografía del Community Manager 2026',
    corto: 'Radiografía del CM', bloom: 'Comprender / Aplicar', sesiones: 'Sesiones 1–6', nSes: 6,
    bridge: 'Ya sabes cómo se ve el ecosistema. Ahora aprende a defenderlo.' },
  { n: 2, acto: 'II · Proteger', emoji: '🛡️', titulo: 'Estrategia de Atención y Tráfico Digital',
    producto: 'Manual de Gestión de Comunidad Digital con Protocolo de Atención y Conversión',
    corto: 'Gestión Digital', bloom: 'Aplicar / Analizar', sesiones: 'Sesiones 7–12', nSes: 6,
    bridge: 'Tu comunidad está segura. Es momento de darle una identidad inolvidable.' },
  { n: 3, acto: 'III · Marcar',  emoji: '🎨', titulo: 'Identidad de Marca y Comunicación Estratégica',
    producto: 'Brand Book Digital con Guía de Voz, Tono y Dinamización para Redes Sociales',
    corto: 'Brand Book', bloom: 'Analizar / Evaluar', sesiones: 'Sesiones 13–18', nSes: 6,
    bridge: 'Tu marca tiene alma. Llena el mundo con su contenido.' },
  { n: 4, acto: 'IV · Cazar',    emoji: '🚀', titulo: 'Plan de Media y Contenidos',
    producto: 'Plan de Contenidos Multiplataforma con Estrategia de Influencers y Monitoreo en Tiempo Real',
    corto: 'Plan de Contenidos', bloom: 'Evaluar / Crear', sesiones: 'Sesiones 19–23', nSes: 5,
    bridge: 'El plan está en marcha. ¿Pero está funcionando? Mide, optimiza, domina.' },
  { n: 5, acto: 'V · Reinar',    emoji: '👑', titulo: 'Analítica y Optimización Estratégica',
    producto: 'Dashboard de Social Media con Informe Ejecutivo de ROI y Plan de Optimización',
    corto: 'Dashboard ROI', bloom: 'Crear / Sintetizar', sesiones: 'Sesiones 24–28', nSes: 5,
    bridge: 'Has completado la Ruta del Jaguar Digital. Ahora eres Community Manager.' },
];
const COMPETENCIA = 'Diseñar un proyecto de acción estratégico de community manager en una organización o empresa, para la toma de decisiones de manera eficaz y eficiente.';

// Metadatos de presentaciones ("El Mirador") por ADA
const PRES = {
  1: { slides: 12, mins: 15, title: 'Perfil Profesional del Community Manager', intro: 'Antes de recorrer el sendero, sube al mirador. En 12 vistas observarás todo el paisaje del CM profesional en 2026 — plataformas, funciones, herramientas y mercado laboral.', topics: ['Ecosistema Digital','5 Pilares del CM','Herramientas','Caso Duolingo'] },
  2: { slides: 12, mins: 15, title: 'Estrategia de Atención y Tráfico Digital', intro: 'Desde este punto alto verás cómo funciona el flujo de atención digital — del primer contacto a la conversión. Frameworks, protocolos y armas de defensa para tu comunidad.', topics: ['Funnel','WhatsApp Business','Buyer Persona','Copywriting'] },
  3: { slides: 11, mins: 12, title: 'Identidad de Marca y Comunicación Estratégica', intro: 'La vista desde aquí es color puro. Observa cómo las marcas memorables construyen su personalidad, su voz y su identidad visual. Después, crearás la tuya.', topics: ['Brand Voice','Arquetipos','UGC','Branding Local'] },
  4: { slides: 11, mins: 12, title: 'Plan de Media y Contenidos', intro: 'Desde este mirador se ve el campo de batalla del contenido. Calendarios, formatos, influencers, IA y pauta — todo el arsenal del CM ejecutivo en una panorámica.', topics: ['Calendario Editorial','Video Corto','Influencers','IA','Meta Ads'] },
  5: { slides: 12, mins: 15, title: 'Analítica y Optimización Estratégica', intro: 'El mirador más alto de la Ruta. Desde aquí se ven los números — KPIs, ROI, dashboards, optimización. Solo los estrategas llegan hasta aquí.', topics: ['KPIs','Insights','ROI','A/B Testing','Caso Yucatán'] },
};
// Introducción narrativa del "Sendero de inscripciones" por ADA
const SENDERO_INTRO = {
  1: 'Cuatro estelas te esperan en este primer sendero. Descifra cada una — al final, tendrás el mapa completo del ecosistema.',
  2: 'Cuatro estelas te enseñarán a convertir extraños en aliados, proteger tu comunidad y responder con la velocidad de un jaguar.',
  3: 'Aquí las inscripciones no solo informan — inspiran. Cuatro estelas sobre el arte de crear identidades memorables.',
  4: 'Cinco estelas para el cazador estratégico. Cada inscripción es una técnica profesional — de calendarios a campañas pagadas.',
  5: 'Las últimas cinco estelas son las más poderosas. Aquí se inscribe el lenguaje de los datos, las métricas y la optimización.',
};

// ---- utilidades ----
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const esc = (s) => String(s).replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));

// ---- Progreso (localStorage) ----
const STORAGE_KEY = 'cv_progress_v1';
const ProgressManager = {
  state: null, listeners: [],
  load() {
    try { const s = localStorage.getItem(STORAGE_KEY); this.state = s ? JSON.parse(s) : this._default(); }
    catch { this.state = this._default(); }
    return this.state;
  },
  _default() {
    const adas = {}; for (let i=1;i<=5;i++) adas[i] = { status:'pending', startedAt:null, completedAt:null };
    return { version:1, adas, lastVisited:null };
  },
  save() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state)); } catch{} this.emit(); },
  markVisited(n) { const a=this.state.adas[n]; if(a.status==='pending'){ a.status='in_progress'; a.startedAt=new Date().toISOString(); } this.state.lastVisited=n; this.save(); },
  markCompleted(n) { const a=this.state.adas[n]; a.status='completed'; a.completedAt=new Date().toISOString(); this.save(); },
  _ensure() { if (!this.state) this.load(); return this.state; },
  status(n) { return this._ensure().adas[n]?.status || 'pending'; },
  completedCount() { return Object.values(this._ensure().adas).filter(a=>a.status==='completed').length; },
  percentage() { return Math.round((this.completedCount()/5)*100); },
  allCompleted() { return this.completedCount() === 5; },
  reset() { this.state = this._default(); this.save(); },
  on(fn){ this.listeners.push(fn); }, emit(){ this.listeners.forEach(fn=>fn(this.state)); },
};

// ---- Vistas ----
function renderHome() {
  const nodes = ADAS.map((a,i) => `
    ${i>0 ? '<div class="journey-connector" aria-hidden="true"></div>' : ''}
    <a class="journey-node" data-ada="${a.n}" href="#/ada-${a.n}" aria-label="ADA ${a.n}: ${esc(a.corto)}">
      <span class="journey-node__circle" aria-hidden="true">${a.emoji}</span>
      <span class="journey-node__label">ADA ${a.n}</span>
      <span class="journey-node__act">${esc(a.acto.split('·')[1].trim())}</span>
    </a>`).join('');
  return `
  <div class="view-enter">
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero__pattern" role="presentation" style="background-image:url('${ASSETS.patronAzul}')"></div>
      <div class="hero__container">
        <div class="hero__content">
          <p class="hero__tagline scroll-reveal">De observador a estratega. Tu camino como Community Manager comienza aquí.</p>
          <div class="hero__badges scroll-reveal" style="--i:1">
            <span class="badge badge--outline">Período 1</span>
            <span class="badge badge--outline">28 sesiones</span>
            <span class="badge badge--outline">5 ADAs</span>
          </div>
          <h1 class="hero__title scroll-reveal" style="--i:2" id="hero-title">Comunidades Virtuales</h1>
          <div class="hero__accent-line scroll-reveal" style="--i:3" aria-hidden="true"></div>
          <p class="hero__subtitle scroll-reveal" style="--i:4">${esc(COMPETENCIA)}</p>
          <div class="hero__frameworks scroll-reveal" style="--i:5">
            <span class="badge badge--gold">DUA</span>
            <span class="badge badge--gold">MEFI</span>
            <span class="badge badge--gold">Bloom Revisada</span>
          </div>
          <div class="hero__actions scroll-reveal" style="--i:6">
            <a class="btn btn--gold btn--lg" href="#/adas">Explorar las 5 ADAs →</a>
            <a class="btn btn--ghost-light btn--lg" href="#competencia">Ver competencia</a>
          </div>
        </div>
        <div class="hero__visual" aria-hidden="true">
          <div class="bloom-spiral">
            <div class="bloom-node" data-level="1">📡 Observar</div>
            <div class="bloom-node" data-level="2">🛡️ Proteger</div>
            <div class="bloom-node" data-level="3">🎨 Marcar</div>
            <div class="bloom-node" data-level="4">🚀 Cazar</div>
            <div class="bloom-node" data-level="5">👑 Reinar</div>
          </div>
        </div>
      </div>
    </section>

    <section class="section" aria-labelledby="ruta-title">
      <h2 class="section__title scroll-reveal" id="ruta-title">Tu ruta en 5 territorios</h2>
      <p class="section__subtitle scroll-reveal">Cada ADA es un territorio que conquistas con escalamiento cognitivo progresivo.</p>
      <nav class="journey-map scroll-reveal" aria-label="Mapa de la ruta del jaguar">${nodes}</nav>
    </section>

    <section class="section section--alt" aria-labelledby="logros-title">
      <div class="container">
        <h2 class="section__title scroll-reveal" id="logros-title">¿Qué vas a lograr?</h2>
        <p class="section__subtitle scroll-reveal">Al final del recorrido tendrás un portafolio profesional real.</p>
        <div class="value-grid">
          <div class="value-card scroll-reveal"><div class="value-card__icon" aria-hidden="true">🏢</div><h3>Portafolio real</h3><p>5 piezas profesionales listas para mostrar a un empleador.</p></div>
          <div class="value-card scroll-reveal" style="--i:1"><div class="value-card__icon" aria-hidden="true">📊</div><h3>Skills 2026</h3><p>Las competencias que las empresas piden a un Community Manager hoy.</p></div>
          <div class="value-card scroll-reveal" style="--i:2"><div class="value-card__icon" aria-hidden="true">🌐</div><h3>Red profesional</h3><p>Tu primer proyecto estratégico desde la Preparatoria.</p></div>
        </div>
      </div>
    </section>

    <section class="section" id="competencia" aria-labelledby="comp-title">
      <div class="competencia-card scroll-reveal">
        <h2 id="comp-title">Competencia del curso</h2>
        <p>"${esc(COMPETENCIA)}"</p>
        <span class="badge badge--gold" style="margin-top:1rem">Preparatoria Uno · UADY · 2026</span>
      </div>
    </section>
  </div>`;
}

function statusLabel(s){ return s==='completed'?'Completada':s==='in_progress'?'En progreso':'Sin iniciar'; }
function statusPct(s){ return s==='completed'?100:s==='in_progress'?50:0; }

function renderAdas() {
  const cards = ADAS.map(a => {
    const st = ProgressManager.status(a.n);
    return `
    <article class="ada-card" data-ada="${a.n}">
      <a class="ada-card__link" href="#/ada-${a.n}" aria-labelledby="ada-${a.n}-title">
        <div class="ada-card__body">
          <div class="ada-card__header">
            <span class="ada-card__badge" aria-hidden="true">${a.n}</span>
            <div class="ada-card__meta">
              <span class="badge badge--gold">${esc(a.bloom)}</span>
              <span class="ada-card__sessions">${esc(a.sesiones)}</span>
              <span class="ada-card__status-chip" data-status="${st}">${statusLabel(st)}</span>
            </div>
          </div>
          <p class="ada-card__act">${esc(a.acto)}</p>
          <h3 class="ada-card__title" id="ada-${a.n}-title">${esc(a.titulo)}</h3>
          <p class="ada-card__description">${esc(a.producto)}</p>
          <div class="ada-card__product"><span aria-hidden="true">⭐</span><span>Producto integrador</span></div>
          <div class="ada-card__progress">
            <div class="progress-bar progress-bar--sm"><div class="progress-bar__fill" style="width:${statusPct(st)}%" role="progressbar" aria-valuenow="${statusPct(st)}" aria-valuemin="0" aria-valuemax="100" aria-label="Progreso ADA ${a.n}"></div></div>
            <span class="ada-card__progress-label">${statusLabel(st)}</span>
          </div>
        </div>
        <div class="ada-card__footer">
          <span class="ada-card__cta">Ver actividad</span><span aria-hidden="true">→</span>
        </div>
      </a>
    </article>`;
  }).join('');
  return `
  <div class="view-enter ada-view">
    <nav class="breadcrumb" aria-label="Ubicación"><ol class="breadcrumb__list"><li><a href="#/">Inicio</a></li><li aria-current="page">ADAs</li></ol></nav>
    <h1 class="section__title" style="text-align:left">Actividades de Aprendizaje</h1>
    <p class="section__subtitle" style="text-align:left">5 productos integradores con escalamiento cognitivo progresivo.</p>
    <div class="adas-grid__cards">${cards}</div>
  </div>`;
}

function renderAda(n) {
  const a = ADAS.find(x => x.n === n);
  if (!a) return renderHome();
  const c = CONTENT[String(n)];
  const prev = ADAS.find(x => x.n === n-1);
  const next = ADAS.find(x => x.n === n+1);
  const st = ProgressManager.status(n);
  const nLect = (LECTURAS[String(n)]||[]).length;
  const prevLink = prev
    ? `<a class="ada-nav__prev" href="#/ada-${prev.n}"><span aria-hidden="true">←</span><span>Anterior: ${esc(prev.corto)}</span></a>`
    : `<a class="ada-nav__prev ada-nav__prev--disabled" aria-disabled="true"><span aria-hidden="true">←</span><span>Anterior</span></a>`;
  const nextLink = next
    ? `<a class="ada-nav__next" href="#/ada-${next.n}"><span><span class="ada-nav__teaser">${esc(a.bridge)}</span>Siguiente: ${esc(next.corto)}</span><span aria-hidden="true">→</span></a>`
    : `<a class="ada-nav__next" href="#/complete"><span><span class="ada-nav__teaser">${esc(a.bridge)}</span>Ver tu logro final</span><span aria-hidden="true">🏆</span></a>`;
  const completeBtn = st === 'completed'
    ? `<span class="badge badge--success">✓ ADA completada</span>`
    : `<button class="btn btn--gold" data-complete-ada="${n}">Marcar ADA como completada</button>`;

  return `
  <article class="view-enter ada-view" data-ada="${n}">
    <nav class="breadcrumb" aria-label="Ubicación"><ol class="breadcrumb__list"><li><a href="#/">Inicio</a></li><li><a href="#/adas">ADAs</a></li><li aria-current="page">ADA ${n}</li></ol></nav>
    <header class="ada-view__header">
      <div class="ada-view__eyebrow">
        <span class="ada-view__badge" aria-hidden="true">${n}</span>
        <span class="ada-view__act">${esc(a.acto)}</span>
      </div>
      <div class="ada-view__badges">
        <span class="badge badge--gold">${esc(a.bloom)}</span>
        <span class="badge badge--primary">${esc(a.sesiones)}</span>
        <span class="badge">${a.nSes} sesiones</span>
      </div>
      <h1 class="ada-view__title">ACTIVIDAD No. ${n} — ${esc(a.titulo)}</h1>
      <p class="ada-view__product-name"><span aria-hidden="true">⭐</span> Producto Integrador: ${esc(a.producto)}</p>
    </header>

    <div class="tabs" role="tablist" aria-label="Secciones de la ADA">
      <button class="tabs__tab tabs__tab--active" role="tab" aria-selected="true" aria-controls="panel-contenido" id="tab-contenido" data-short="Contenido"><span class="tabs__icon" aria-hidden="true">📖</span><span class="tabs__label">Contenido</span></button>
      <button class="tabs__tab" role="tab" aria-selected="false" tabindex="-1" aria-controls="panel-lecturas" id="tab-lecturas" data-short="Lecturas"><span class="tabs__icon" aria-hidden="true">📚</span><span class="tabs__label">Lecturas</span><span class="tabs__count" aria-label="${nLect} lecturas disponibles">${nLect}</span></button>
      <button class="tabs__tab" role="tab" aria-selected="false" tabindex="-1" aria-controls="panel-presentacion" id="tab-presentacion" data-short="Mirador"><span class="tabs__icon" aria-hidden="true">🗿</span><span class="tabs__label">Presentación</span></button>
      <button class="tabs__tab" role="tab" aria-selected="false" tabindex="-1" aria-controls="panel-producto" id="tab-producto" data-short="Producto"><span class="tabs__icon" aria-hidden="true">📄</span><span class="tabs__label">Producto</span></button>
      <button class="tabs__tab" role="tab" aria-selected="false" tabindex="-1" aria-controls="panel-rubrica" id="tab-rubrica" data-short="Rúbrica"><span class="tabs__icon" aria-hidden="true">📋</span><span class="tabs__label">Rúbrica</span></button>
    </div>

    <section class="tab-panel" role="tabpanel" id="panel-contenido" aria-labelledby="tab-contenido">
      <div class="content-renderer">${c.contenido}</div>
    </section>
    <section class="tab-panel" role="tabpanel" id="panel-lecturas" aria-labelledby="tab-lecturas" hidden>
      ${renderLecturasPanel(n)}
    </section>
    <section class="tab-panel" role="tabpanel" id="panel-presentacion" aria-labelledby="tab-presentacion" hidden>
      ${renderPresentacionPanel(n)}
    </section>
    <section class="tab-panel" role="tabpanel" id="panel-producto" aria-labelledby="tab-producto" hidden>
      <div class="md-content">${c.producto}</div>
    </section>
    <section class="tab-panel" role="tabpanel" id="panel-rubrica" aria-labelledby="tab-rubrica" hidden>
      <div class="rubrica">
        <div class="rubrica__legend" aria-label="Niveles de evaluación">
          <span class="rubrica__level-chip"><span class="rubrica__level-dot rubrica__level-dot--4"></span>Excelente (4)</span>
          <span class="rubrica__level-chip"><span class="rubrica__level-dot rubrica__level-dot--3"></span>Satisfactorio (3)</span>
          <span class="rubrica__level-chip"><span class="rubrica__level-dot rubrica__level-dot--2"></span>En desarrollo (2)</span>
          <span class="rubrica__level-chip"><span class="rubrica__level-dot rubrica__level-dot--1"></span>Inicial (1)</span>
        </div>
        <div class="md-content">${c.rubrica}</div>
      </div>
    </section>

    <div class="ada-complete-cta">${completeBtn}</div>
    <p class="ada-bridge">"${esc(a.bridge)}" <span class="jag-term" title="Jag, tu CM guía">— Jag 🐆</span></p>
    <nav class="ada-nav" aria-label="Navegación entre actividades">${prevLink}${nextLink}</nav>
  </article>`;
}

function renderComplete() {
  if (!ProgressManager.allCompleted()) {
    const done = ProgressManager.completedCount();
    return `
    <div class="view-enter ada-view">
      <div class="completion__locked">
        <img class="completion__jaguar" src="${ASSETS.jaguar}" alt="Jaguar institucional UADY">
        <h1>Aún no completas la ruta</h1>
        <p>Has conquistado <strong>${done} de 5</strong> territorios. Completa todas las ADAs para desbloquear tu coronación.</p>
        <div class="completion__actions"><a class="btn btn--primary btn--lg" href="#/adas">Volver a las ADAs</a></div>
      </div>
    </div>`;
  }
  const terr = ADAS.map(a => `<li>✅ ${a.emoji} ${esc(a.acto.split('·')[1].trim())} — ${esc(a.corto)}</li>`).join('');
  return `
  <div class="view-enter">
    <section class="completion" aria-labelledby="complete-title">
      <div class="completion__pattern" role="presentation" style="background-image:url('${ASSETS.patronDorado}')"></div>
      <div class="completion__inner">
        <img class="completion__jaguar" src="${ASSETS.jaguar}" alt="Jaguar institucional UADY con corona de logro">
        <h1 id="complete-title">🏆 Ruta Completada</h1>
        <p class="completion__subtitle">Ahora eres Community Manager.</p>
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-card__num" data-count="5">0</div><div class="stat-card__label">ADAs</div></div>
          <div class="stat-card"><div class="stat-card__num" data-count="28">0</div><div class="stat-card__label">Sesiones</div></div>
          <div class="stat-card"><div class="stat-card__num" data-count="5">0</div><div class="stat-card__label">Productos</div></div>
          <div class="stat-card"><div class="stat-card__num" data-count="1">0</div><div class="stat-card__label">Portafolio</div></div>
        </div>
        <h2 style="color:#fff">Tus territorios conquistados</h2>
        <ul class="completion__territories">${terr}</ul>
        <p class="completion__quote">"Un Community Manager no nace. Se construye con estrategia, creatividad y datos."</p>
        <div class="completion__actions">
          <a class="btn btn--gold btn--lg" href="#/adas">Revisar mis ADAs</a>
          <a class="btn btn--ghost-light btn--lg" href="#/">Volver al inicio</a>
        </div>
      </div>
    </section>
  </div>`;
}

// ---- Sidebar progress tracker ----
function renderSidebar() {
  const pct = ProgressManager.percentage();
  const steps = ADAS.map(a => {
    const st = ProgressManager.status(a.n);
    const cls = st==='completed' ? 'progress-step--completed' : st==='in_progress' ? 'progress-step--active' : 'progress-step--pending';
    const ind = st==='completed' ? '✓' : String(a.n);
    const nl = (LECTURAS[String(a.n)]||[]).length;
    const rd = LecturaProgress.readCount(a.n);
    const lread = nl ? `<span class="progress-step__status">📚 ${rd}/${nl} estelas</span>` : '';
    const status = (st==='in_progress' ? '<span class="progress-step__status">En progreso</span>' : '') + lread;
    const aria = st==='in_progress' ? ' aria-current="step"' : '';
    return `<li class="progress-step ${cls}"${aria}>
      <span class="progress-step__indicator" aria-hidden="true">${ind}</span>
      <a class="progress-step__link" href="#/ada-${a.n}">
        <span class="progress-step__number">ADA ${a.n}</span>
        <span class="progress-step__name">${esc(a.corto)}</span>${status}
      </a></li>`;
  }).join('');
  return `
  <nav class="progress-tracker" aria-label="Progreso del curso">
    <div class="progress-tracker__header">
      <h4 class="progress-tracker__title">Ruta del Jaguar</h4>
      <span class="progress-tracker__summary">${ProgressManager.completedCount()} de 5 completadas</span>
    </div>
    <div class="progress-tracker__bar">
      <div class="progress-bar"><div class="progress-bar__fill" style="width:${pct}%" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100" aria-label="${pct}% del curso completado"></div></div>
      <span class="progress-tracker__percentage">${pct}%</span>
    </div>
    <ol class="progress-tracker__steps">${steps}</ol>
    <div class="progress-tracker__reset"><button type="button" data-reset-progress>Reiniciar progreso</button></div>
  </nav>`;
}

function updateMobileProgress() {
  const dots = ADAS.map(a => {
    const st = ProgressManager.status(a.n);
    const cls = st==='completed'?'progress-dot--completed':st==='in_progress'?'progress-dot--active':'';
    return `<span class="progress-dot ${cls}" title="ADA ${a.n}: ${statusLabel(st)}"></span>`;
  }).join('');
  const el = $('#progress-mobile');
  if (el) el.innerHTML = `<div class="progress-tracker-mobile__dots">${dots}</div><span class="progress-tracker-mobile__label">${ProgressManager.completedCount()}/5 ADAs</span>`;
}

// ==================== FASE 2: LECTURAS Y PRESENTACIONES ====================

// Progreso de lecturas (localStorage)
const LREAD_KEY = 'cv_lecturas_v1';
const LecturaProgress = {
  load() { try { return JSON.parse(localStorage.getItem(LREAD_KEY)) || {}; } catch { return {}; } },
  isRead(ada, li) { const s = this.load(); return !!(s[`${ada}-${li}`]?.completed); },
  pct(ada, li) { const s = this.load(); return s[`${ada}-${li}`]?.pct || 0; },
  setPct(ada, li, pct) { const s = this.load(); const k=`${ada}-${li}`; s[k]=s[k]||{}; s[k].pct=Math.max(s[k].pct||0,pct); if(pct>=98) s[k].completed=true; localStorage.setItem(LREAD_KEY, JSON.stringify(s)); },
  markRead(ada, li) { const s = this.load(); const k=`${ada}-${li}`; s[k]=s[k]||{}; s[k].completed=true; s[k].pct=100; localStorage.setItem(LREAD_KEY, JSON.stringify(s)); },
  readCount(ada) { const list = LECTURAS[String(ada)]||[]; return list.filter((_,i)=>this.isRead(ada,i+1)).length; },
  allRead(ada) { const list = LECTURAS[String(ada)]||[]; return list.length>0 && list.every((_,i)=>this.isRead(ada,i+1)); },
  badgeSeen(ada) { const s=this.load(); return !!s[`badge-${ada}`]; },
  setBadgeSeen(ada) { const s=this.load(); s[`badge-${ada}`]=true; localStorage.setItem(LREAD_KEY, JSON.stringify(s)); },
};

function renderLecturasPanel(n) {
  const list = LECTURAS[String(n)] || [];
  const readN = LecturaProgress.readCount(n);
  // tracker de estelas
  const nodes = list.map((_, i) => {
    const li = i+1; const read = LecturaProgress.isRead(n, li);
    const cls = read ? 'completed' : (LecturaProgress.pct(n,li)>0 ? 'current' : '');
    const conn = i>0 ? '<span class="estela-connector" aria-hidden="true"></span>' : '';
    return `${conn}<span class="estela-node ${cls}" aria-hidden="true"></span>`;
  }).join('');
  const dots = list.map((_, i) => `<span class="reading-dot ${LecturaProgress.isRead(n,i+1)?'completed':''}"></span>`).join('');
  const cards = list.map((l, i) => {
    const li = i+1; const read = LecturaProgress.isRead(n, li); const pct = LecturaProgress.pct(n, li);
    return `
    <article class="lectura-card ${read?'lectura-card--completed':''}" data-ada="${n}" data-lectura="${li}">
      ${read?'<span class="lectura-card__completed-badge" aria-label="Lectura completada">✓</span>':''}
      <div class="lectura-card__header">
        <span class="lectura-card__number" aria-label="Estela ${li}">${String(li).padStart(2,'0')}</span>
        <span class="lectura-card__badge lectura-card__badge--${l.eje}">${esc(l.ejeLabel)}</span>
      </div>
      <div class="lectura-card__body">
        <h3 class="lectura-card__title"><a class="lectura-card__link" href="#/ada-${n}/lectura-${li}">${esc(l.title)}</a></h3>
        <p class="lectura-card__excerpt">${esc(l.excerpt)}</p>
      </div>
      <div class="lectura-card__footer">
        <div class="lectura-card__meta">
          <span class="lectura-card__time"><span aria-hidden="true">🕐</span> ${l.mins} min</span>
          <span class="lectura-card__words"><span aria-hidden="true">📄</span> ~${l.words} palabras</span>
        </div>
        <div class="lectura-card__progress" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100" aria-label="Progreso de lectura ${li}"><div class="lectura-card__progress-fill" style="width:${pct}%"></div></div>
      </div>
    </article>`;
  }).join('');
  return `
    <div class="lecturas-panel__intro">
      <h2 class="lecturas-panel__intro-title"><span aria-hidden="true">🐾</span> Sendero de Inscripciones</h2>
      <p>${esc(SENDERO_INTRO[n] || '')}</p>
    </div>
    <div class="estela-tracker" role="progressbar" aria-valuenow="${readN}" aria-valuemin="0" aria-valuemax="${list.length}" aria-label="${readN} de ${list.length} estelas descifradas">
      <span aria-hidden="true" style="margin-right:8px">🐾</span>${nodes}
      <span class="reading-streak" aria-hidden="true">${dots}</span>
    </div>
    <div class="lecturas-grid">${cards}</div>`;
}

function renderPresentacionPanel(n) {
  const p = PRES[n]; const a = ADAS.find(x=>x.n===n);
  const topics = p.topics.map(t=>`<span class="badge badge--gold">${esc(t)}</span>`).join('');
  return `
    <div class="presentacion-preview">
      <div class="presentacion-preview__intro">
        <h2 class="presentacion-preview__intro-title"><span aria-hidden="true">🗿</span> El Mirador del Territorio ${n}</h2>
        <p>${esc(p.intro)}</p>
      </div>
      <button class="presentacion-preview__thumbnail" data-open-presentacion="${n}" aria-label="Abrir presentación de la ADA ${n} en pantalla completa">
        <span class="presentacion-preview__slide-mock">
          <span class="presentacion-preview__slide-title">${a.emoji} ${esc(p.title)}</span>
          <span class="presentacion-preview__slide-subtitle">ADA ${n} — Comunidades Virtuales</span>
        </span>
        <span class="presentacion-preview__overlay"><span class="presentacion-preview__play"><span aria-hidden="true" style="font-size:2rem">▶</span><span>Subir al Mirador</span></span></span>
      </button>
      <div class="presentacion-preview__info">
        <span><span aria-hidden="true">🖼️</span> ${p.slides} vistas</span>
        <span><span aria-hidden="true">🕐</span> ~${p.mins} min</span>
        <span><span aria-hidden="true">🖥️</span> Interactivo · HTML5</span>
      </div>
      <h3 class="presentacion-preview__title">Presentación: ${esc(p.title)}</h3>
      <div class="presentacion-preview__topics">${topics}</div>
      <button class="btn btn--primary btn--lg presentacion-preview__cta" data-open-presentacion="${n}"><span aria-hidden="true">🖥️</span> Abrir Presentación Completa</button>
      <p class="presentacion-preview__tip"><span aria-hidden="true">💡</span> Usa ← → del teclado o desliza en pantalla táctil para navegar entre vistas.</p>
    </div>`;
}

function renderLectura(n, li) {
  const list = LECTURAS[String(n)] || [];
  const l = list[li-1];
  if (!l) return renderAda(n);
  const a = ADAS.find(x=>x.n===n);
  const prev = li>1 ? list[li-2] : null;
  const next = li<list.length ? list[li] : null;
  const conceptos = l.conceptos.map(([t,d])=>`<dt>${esc(t)}</dt><dd>${esc(d)}</dd>`).join('');
  const recursos = l.recursos.map(r=>`<li>${r}</li>`).join('');
  const fuentes = l.fuentes.map(f=>`<li>${f}</li>`).join('');
  const prevLink = prev
    ? `<a class="lectura-nav__prev" href="#/ada-${n}/lectura-${li-1}"><span aria-hidden="true">←</span><span class="lectura-nav__info"><span class="lectura-nav__label">Anterior</span><span class="lectura-nav__title">${esc(prev.title)}</span></span></a>`
    : `<a class="lectura-nav__prev lectura-nav__prev--disabled" aria-disabled="true"><span aria-hidden="true">←</span><span class="lectura-nav__info"><span class="lectura-nav__label">Anterior</span><span class="lectura-nav__title">—</span></span></a>`;
  const nextLink = next
    ? `<a class="lectura-nav__next" href="#/ada-${n}/lectura-${li+1}"><span class="lectura-nav__info"><span class="lectura-nav__label">Siguiente estela</span><span class="lectura-nav__title">${esc(next.title)}</span></span><span aria-hidden="true">→</span></a>`
    : `<a class="lectura-nav__next" href="#/ada-${n}"><span class="lectura-nav__info"><span class="lectura-nav__label">Volver al</span><span class="lectura-nav__title">Sendero completo 🐾</span></span><span aria-hidden="true">→</span></a>`;
  const quiz = (l.quiz && l.quiz.length) ? '' : ''; // quiz opcional (no incluido en datos)
  return `
  <div class="lectura-view" data-ada="${n}" data-lectura="${li}">
    <div class="lectura-progress" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" aria-label="Progreso de lectura"><div class="lectura-progress__bar" id="lectura-progress-bar"></div></div>
    <div class="lectura-view__toolbar">
      <a class="lectura-view__back" href="#/ada-${n}"><span aria-hidden="true">←</span><span>Volver al Sendero</span></a>
      <div class="lectura-view__toolbar-meta">
        <span>${l.mins} min de lectura</span>
        <span class="lectura-view__progress-text" id="lectura-progress-text" aria-live="polite">0% descifrado</span>
      </div>
    </div>
    <article class="lectura-content" aria-labelledby="lectura-title">
      <header class="lectura-content__header">
        <div class="lectura-content__meta">
          <span class="badge badge--primary">ADA ${n}</span>
          <span class="lectura-card__badge lectura-card__badge--${l.eje}">${esc(l.ejeLabel)}</span>
          <span class="lectura-content__number">Estela ${li} de ${list.length}</span>
        </div>
        <h1 class="lectura-content__title" id="lectura-title">${esc(l.title)}</h1>
        ${l.subtitle?`<p class="lectura-content__subtitle">${esc(l.subtitle)}</p>`:''}
      </header>
      ${conceptos?`<aside class="lectura-conceptos" aria-label="Conceptos clave">
        <button class="lectura-conceptos__toggle" aria-expanded="true" aria-controls="conceptos-${n}-${li}"><span aria-hidden="true">💡</span> Glifos que descifrarás <span class="lectura-conceptos__chevron" aria-hidden="true">▾</span></button>
        <div class="lectura-conceptos__content" id="conceptos-${n}-${li}"><dl class="lectura-conceptos__list">${conceptos}</dl></div>
      </aside>`:''}
      <div class="lectura-body" id="lectura-body">${l.texto}</div>
      ${l.conexion?`<aside class="lectura-conexion" aria-label="Conexión con tu producto">
        <div class="lectura-conexion__icon" aria-hidden="true">🔗</div>
        <div class="lectura-conexion__content"><h3 class="lectura-conexion__title">Conexión con tu producto integrador</h3>${l.conexion}</div>
      </aside>`:''}
      ${recursos?`<section class="lectura-dua" aria-label="Recursos complementarios">
        <h2 class="lectura-dua__title"><span aria-hidden="true">♿</span> Recursos complementarios (DUA)</h2>
        <p class="lectura-dua__subtitle">Múltiples representaciones del contenido para distintos estilos de aprendizaje.</p>
        <ul class="lectura-dua__list">${recursos}</ul>
      </section>`:''}
      ${fuentes?`<footer class="lectura-fuentes"><details><summary><span aria-hidden="true">📖</span> Fuentes y referencias (${l.fuentes.length})</summary><ol>${fuentes}</ol></details></footer>`:''}
    </article>
    <nav class="lectura-nav" aria-label="Navegación entre estelas">${prevLink}${nextLink}</nav>
  </div>`;
}


// ---- Whimsy ----
function toast(msg) {
  let c = $('#toast-container');
  if (!c) { c = document.createElement('div'); c.id='toast-container'; c.className='toast-container'; c.setAttribute('aria-live','polite'); document.body.appendChild(c); }
  const t = document.createElement('div'); t.className='toast'; t.textContent = msg; c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

function confetti() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const parts = ['✦','🐾','#','♥','◆','⭐'];
  const cont = document.createElement('div'); cont.className='confeti-container'; cont.setAttribute('aria-hidden','true');
  document.body.appendChild(cont);
  for (let i=0;i<34;i++){
    const p = document.createElement('span'); p.className='confeti-particle';
    p.textContent = parts[Math.floor(Math.random()*parts.length)];
    p.style.setProperty('--x', `${Math.random()*100}vw`);
    p.style.setProperty('--delay', `${Math.random()*0.6}s`);
    p.style.setProperty('--rotation', `${Math.random()*720-360}deg`);
    cont.appendChild(p);
  }
  setTimeout(() => cont.remove(), 3400);
}

function setupScrollReveal(root) {
  const items = $$('.scroll-reveal', root);
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { items.forEach(i=>i.classList.add('is-visible')); return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
  items.forEach(i => io.observe(i));
}

function animateCounters(root) {
  $$('[data-count]', root).forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = target; return; }
    const start = performance.now(), dur = 1400;
    const step = (now) => { const p = Math.min((now-start)/dur, 1); const eased = 1-Math.pow(1-p,3);
      el.textContent = Math.floor(eased*target); if (p<1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
}

const JAG_TIPS = {
  home: '¡Bienvenido! Soy Jag, tu CM guía. Explora la ruta a tu ritmo.',
  adas: 'Cada territorio suma a tu portafolio. Empieza por donde quieras.',
  ada: 'Lee el contenido, revisa el producto y la rúbrica antes de entregar.',
  complete: 'Lo lograste. Un CM no nace, se construye. 🐆',
};
function showJag(context) {
  const bubble = $('#jag-bubble');
  if (!bubble) return;
  const tip = JAG_TIPS[context] || JAG_TIPS.ada;
  bubble.innerHTML = `${esc(tip)}<span class="sig">— Jag</span>`;
  bubble.classList.add('is-visible');
  clearTimeout(showJag._t);
  showJag._t = setTimeout(() => bubble.classList.remove('is-visible'), 6000);
}


// ==================== Reading progress + checkpoints + Jag ====================
let _readingCleanup = null;
function setupLecturaReading(root, ada, li) {
  const bar = root.querySelector('#lectura-progress-bar');
  const text = root.querySelector('#lectura-progress-text');
  const body = root.querySelector('#lectura-body');
  const barWrap = root.querySelector('.lectura-progress');
  if (!bar || !body) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const checkpoints = { 25:false, 50:false, 75:false, 100:false };
  const CP_MSG = {
    25: 'Vas bien, no te distraigas con el cel 📱',
    50: 'Mitad de camino. Ni un influencer lee tan rápido 🔥',
    75: '¡Falta poco! Ya le ganaste al 60% del salón 📈',
    100: 'Lectura completada. Tu cerebro hizo un update 🧠✨',
  };
  let completed = false;
  function update() {
    const rect = body.getBoundingClientRect();
    const top = rect.top + window.scrollY;
    const h = rect.height;
    const scrolled = window.scrollY - top + window.innerHeight * 0.6;
    const pct = Math.min(Math.max((scrolled / h) * 100, 0), 100);
    bar.style.width = pct + '%';
    text.textContent = Math.round(pct) + '% descifrado';
    if (barWrap) barWrap.setAttribute('aria-valuenow', Math.round(pct));
    if (pct > 3) LecturaProgress.setPct(ada, li, Math.round(pct));
    [25,50,75,100].forEach(cp => {
      if (!checkpoints[cp] && pct >= cp) {
        checkpoints[cp] = true;
        if (cp === 100) {
          if (!completed) {
            completed = true;
            bar.classList.add('is-complete');
            LecturaProgress.markRead(ada, li);
            confetti();
            toast('✓ Estela descifrada. +15 XP 🎉');
            checkReadingBadge(ada);
          }
        } else {
          toast(CP_MSG[cp]);
          showJagMsg(CP_MSG[cp]);
        }
      }
    });
  }
  const onScroll = () => { if (!reduced) requestAnimationFrame(update); else update(); };
  window.addEventListener('scroll', onScroll, { passive: true });
  _readingCleanup = () => window.removeEventListener('scroll', onScroll);
  update();

  // conceptos toggle
  const toggle = root.querySelector('.lectura-conceptos__toggle');
  if (toggle) {
    const content = root.querySelector('#'+toggle.getAttribute('aria-controls'));
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      if (content) content.hidden = open;
    });
  }
}

function checkReadingBadge(ada) {
  if (LecturaProgress.allRead(ada) && !LecturaProgress.badgeSeen(ada)) {
    LecturaProgress.setBadgeSeen(ada);
    const names = {1:'Descifrador del Ecosistema',2:'Descifrador de Protocolos',3:'Descifrador de Identidades',4:'Descifrador de Estrategias',5:'Descifrador del Dominio'};
    setTimeout(() => { confetti(); toast(`📜 Insignia desbloqueada: ${names[ada]}`); }, 1000);
  }
}

function showJagMsg(msg) {
  const bubble = document.getElementById('jag-bubble');
  if (!bubble) return;
  bubble.innerHTML = `${esc(msg)}<span class="sig">— Jag</span>`;
  bubble.classList.add('is-visible');
  clearTimeout(showJagMsg._t);
  showJagMsg._t = setTimeout(() => bubble.classList.remove('is-visible'), 5000);
}

// ==================== Presentación modal ====================
const PresModal = {
  el: null, iframe: null, counter: null, progress: null, prevFocus: null,
  init() {
    this.el = document.getElementById('presentacion-modal');
    if (!this.el) return;
    this.iframe = this.el.querySelector('.presentacion-modal__iframe');
    this.counter = this.el.querySelector('.presentacion-modal__slide-counter');
    this.progress = this.el.querySelector('.presentacion-modal__progress-bar');
    this.el.querySelectorAll('[data-close-presentacion]').forEach(b => b.addEventListener('click', () => this.close()));
    this.el.querySelector('[data-slide-prev]')?.addEventListener('click', () => this.msg('prevSlide'));
    this.el.querySelector('[data-slide-next]')?.addEventListener('click', () => this.msg('nextSlide'));
    document.addEventListener('keydown', (e) => { if (!this.el.hidden && e.key === 'Escape') this.close(); });
    window.addEventListener('message', (e) => {
      if (e.data && e.data.type === 'slideChange') this.updateCounter(e.data.current, e.data.total);
    });
  },
  msg(action) { try { this.iframe.contentWindow.postMessage({ action }, '*'); } catch {} },
  open(ada) {
    this.prevFocus = document.activeElement;
    this.iframe.src = `presentaciones/ada_${ada}_presentacion.html`;
    const title = this.el.querySelector('.presentacion-modal__title');
    if (title) title.textContent = `ADA ${ada} — Mirador: ${PRES[ada].title}`;
    this.el.hidden = false;
    document.body.style.overflow = 'hidden';
    this.el.querySelector('.presentacion-modal__close').focus();
  },
  close() {
    this.el.classList.add('is-closing');
    setTimeout(() => {
      this.el.hidden = true; this.el.classList.remove('is-closing');
      this.iframe.src = ''; document.body.style.overflow = '';
      if (this.prevFocus) this.prevFocus.focus();
    }, 200);
  },
  updateCounter(cur, total) {
    if (this.counter) this.counter.textContent = `Vista ${cur} / ${total}`;
    if (this.progress) this.progress.style.width = `${(cur/total)*100}%`;
  },
};

function setupTabs(root) {
  const tablist = $('.tabs', root);
  if (!tablist) return;
  const tabs = $$('[role="tab"]', tablist);
  const panels = tabs.map(t => document.getElementById(t.getAttribute('aria-controls')));
  const activate = (idx) => {
    tabs.forEach((t,i) => { const sel = i===idx; t.setAttribute('aria-selected', sel); t.classList.toggle('tabs__tab--active', sel); t.tabIndex = sel?0:-1; panels[i].hidden = !sel; });
    tabs[idx].focus();
  };
  tabs.forEach((t,i) => {
    t.addEventListener('click', () => activate(i));
    t.addEventListener('keydown', (e) => {
      let ni;
      if (e.key==='ArrowRight') ni=(i+1)%tabs.length;
      else if (e.key==='ArrowLeft') ni=(i-1+tabs.length)%tabs.length;
      else if (e.key==='Home') ni=0; else if (e.key==='End') ni=tabs.length-1; else return;
      e.preventDefault(); activate(ni);
    });
  });
}

// Easter egg: Konami del CM (c-m-2-0-2-6)
function setupKonami() {
  const seq = ['c','m','2','0','2','6']; let buf = [];
  document.addEventListener('keydown', (e) => {
    buf.push((e.key||'').toLowerCase()); buf = buf.slice(-6);
    if (buf.join('') === seq.join('')) { toast('🌙 Modo CM nocturno: como todo buen CM, aquí trabajamos a las 11pm.'); confetti(); }
  });
}
// Easter egg: consola cochinita
function consoleCochinita() {
  try {
    console.log('%c🌮 COCHINITA DEBUG', 'font-size:20px;color:#C89211;font-weight:bold;');
    console.log('%cSi estás aquí, ya vas un paso adelante como CM. — @uady_oficial', 'color:#192E4C;');
  } catch {}
}

// ---- Router ----
const main = () => $('#main-content');

function parseHash() {
  let h = location.hash.replace(/^#\/?/, '');
  if (h === '' || h === 'home') return { view:'home' };
  if (h === 'adas') return { view:'adas' };
  if (h === 'complete') return { view:'complete' };
  const ml = h.match(/^ada-([1-5])\/lectura-(\d+)$/);
  if (ml) return { view:'lectura', n: parseInt(ml[1],10), li: parseInt(ml[2],10) };
  const m = h.match(/^ada-([1-5])$/);
  if (m) return { view:'ada', n: parseInt(m[1],10) };
  return { view:'home', unknown:true };
}

function updateNavActive(route) {
  $$('.navbar__link[data-route]').forEach(l => {
    const r = l.dataset.route;
    const active = (r==='home'&&route.view==='home') || (r==='adas'&&(route.view==='adas'||route.view==='ada'));
    l.classList.toggle('is-active', active);
    if (active) l.setAttribute('aria-current','page'); else l.removeAttribute('aria-current');
  });
}

function renderRoute() {
  if (_readingCleanup) { _readingCleanup(); _readingCleanup = null; }
  const route = parseHash();
  let htmlStr;
  if (route.view==='home') htmlStr = renderHome();
  else if (route.view==='adas') htmlStr = renderAdas();
  else if (route.view==='ada') { ProgressManager.markVisited(route.n); htmlStr = renderAda(route.n); }
  else if (route.view==='lectura') { ProgressManager.markVisited(route.n); htmlStr = renderLectura(route.n, route.li); }
  else if (route.view==='complete') htmlStr = renderComplete();
  main().innerHTML = htmlStr;

  updateNavActive(route);
  if (route.unknown) toast('Página no encontrada. Te llevamos al inicio.');
  if (route.view==='ada') setupTabs(main());
  if (route.view==='lectura') setupLecturaReading(main(), route.n, route.li);
  animateCounters(main());
  setupScrollReveal(main());
  window.scrollTo({ top: 0, behavior: 'smooth' });
  main().focus({ preventScroll: true });
  showJag(route.view);
  closeMobileMenu();
}

// ---- Mobile menu ----
function openMobileMenu() {
  const sb = $('#sidebar'), ov = $('#overlay'), btn = $('#hamburger');
  if (!sb) return;
  sb.classList.add('is-open'); ov.classList.add('is-visible');
  btn.setAttribute('aria-expanded','true'); document.body.style.overflow='hidden';
}
function closeMobileMenu() {
  const sb = $('#sidebar'), ov = $('#overlay'), btn = $('#hamburger');
  if (!sb) return;
  sb.classList.remove('is-open'); ov.classList.remove('is-visible');
  btn.setAttribute('aria-expanded','false'); document.body.style.overflow='';
}

// ---- Dropdown ----
function setupDropdown() {
  const trigger = $('#ada-dropdown-trigger'); const menu = $('#ada-dropdown');
  if (!trigger || !menu) return;
  const toggle = (open) => { menu.classList.toggle('is-open', open); trigger.setAttribute('aria-expanded', String(open)); };
  trigger.addEventListener('click', (e)=>{ e.stopPropagation(); toggle(!menu.classList.contains('is-open')); });
  document.addEventListener('click', (e)=>{ if(!trigger.contains(e.target)&&!menu.contains(e.target)) toggle(false); });
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') toggle(false); });
  menu.addEventListener('click', ()=> toggle(false));
}

// ---- Sidebar refresh on progress change ----
function refreshSidebar() { const el = $('#sidebar-progress'); if (el) el.innerHTML = renderSidebar(); updateMobileProgress(); }

// ---- Global event delegation ----
function setupGlobalEvents() {
  document.addEventListener('click', (e) => {
    const completeBtn = e.target.closest('[data-complete-ada]');
    if (completeBtn) {
      const n = parseInt(completeBtn.dataset.completeAda, 10);
      ProgressManager.markCompleted(n);
      confetti(); toast(`¡Bombaa! ADA ${n} completada. Jag está orgulloso. 🐆`);
      const a = ADAS.find(x=>x.n===n);
      completeBtn.outerHTML = `<span class="badge badge--success">✓ ADA completada</span>`;
      if (ProgressManager.allCompleted()) setTimeout(()=>{ location.hash = '#/complete'; }, 900);
      return;
    }
    const reset = e.target.closest('[data-reset-progress]');
    if (reset) { if(confirm('¿Reiniciar tu progreso? Esta acción no se puede deshacer.')){ ProgressManager.reset(); toast('Progreso reiniciado.'); if(parseHash().view!=='home') location.hash='#/'; else renderRoute(); } return; }
    const openP = e.target.closest('[data-open-presentacion]');
    if (openP) { PresModal.open(parseInt(openP.dataset.openPresentacion, 10)); return; }
  });

  $('#hamburger')?.addEventListener('click', () => {
    const open = $('#sidebar').classList.contains('is-open'); open ? closeMobileMenu() : openMobileMenu();
  });
  $('#overlay')?.addEventListener('click', closeMobileMenu);
  document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') closeMobileMenu(); });
  window.addEventListener('resize', ()=>{ if(window.innerWidth>=1024) closeMobileMenu(); });


  let lastY = 0;
  window.addEventListener('scroll', ()=>{ const nb=$('.navbar'); if(nb) nb.classList.toggle('navbar--scrolled', window.scrollY>10); lastY=window.scrollY; }, { passive:true });

  $('#jag-avatar')?.addEventListener('click', ()=> showJag(parseHash().view));
}

// ---- Init ----
function init() {
  ProgressManager.load();
  ProgressManager.on(refreshSidebar);
  refreshSidebar();
  setupDropdown();
  setupGlobalEvents();
  setupKonami();
  consoleCochinita();
  PresModal.init();
  window.addEventListener('hashchange', renderRoute);
  renderRoute();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
