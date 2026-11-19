import * as THREE from './vendor/three.module.min.js';
import { OrbitControls } from './vendor/OrbitControls.js';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { RoomEnvironment } from './vendor/RoomEnvironment.js';
import { BIMLibraryController } from './bim/bim_ui.js';

let bimController = null;

const DETAIL_FILES = {
  detalle1: {
    glb: 'models/detalle1_ive_peto.glb',
    blend: 'models/detalle1_ive_peto.blend',
    dxf: 'planos_2d/detalle1_ive_peto.dxf',
    pdf: 'planos_2d/detalle1_ive_peto.pdf',
    svg: 'planos_2d/detalle1_ive_peto.svg',
    png2d: 'planos_2d/detalle1_ive_peto.png',
    montaje_glb: 'models/detalle1_montaje_piezas.glb',
    montaje_blend: 'models/detalle1_montaje.blend',
    montaje_svg_live: 'planos_2d/detalle1_ive_montaje_live.svg',
    montaje_dxf: 'planos_2d/detalle1_ive_montaje.dxf',
    montaje_pdf: 'planos_2d/detalle1_ive_montaje.pdf',
    montaje_svg: 'planos_2d/detalle1_ive_montaje.svg',
    montaje_png: 'planos_2d/detalle1_ive_montaje.png',
    montaje_mp4: 'renders/detalle1_montaje_30s.mp4',
    renders: [
      { src: 'renders/detalle1_hero.png', title: 'Axonométrica Escalonada IVE (Cycles PBR)', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle1_closeup.png', title: 'Macro Encuentro Peto · Junta EPS · Rodapié', tag: 'MACRO DETALLE' },
      { src: 'renders/detalle1_section.png', title: 'Alzado de Sección Constructiva (Viguetas + LHD)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle2_qat16: {
    glb: 'models/detalle2_nte_qat16_cazoleta.glb',
    blend: 'models/detalle2_nte_qat16_cazoleta.blend',
    dxf: 'planos_2d/detalle2_nte_qat16_cazoleta.dxf',
    pdf: 'planos_2d/detalle2_nte_qat16_cazoleta.pdf',
    svg: 'planos_2d/detalle2_nte_qat16_cazoleta.svg',
    png2d: 'planos_2d/detalle2_nte_qat16_cazoleta.png',
    renders: [
      { src: 'renders/detalle2_qat16_hero.png', title: 'Corte 3D QAT-16 · Caja PTL-7 y Solape 10 cm', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle2_qat16_section.png', title: 'Sección Ortográfica QAT-16 (NTE)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle2_qat17: {
    glb: 'models/detalle2_nte_qat17_canalon.glb',
    blend: 'models/detalle2_nte_qat17_canalon.blend',
    dxf: 'planos_2d/detalle2_nte_qat17_canalon.dxf',
    pdf: 'planos_2d/detalle2_nte_qat17_canalon.pdf',
    svg: 'planos_2d/detalle2_nte_qat17_canalon.svg',
    png2d: 'planos_2d/detalle2_nte_qat17_canalon.png',
    renders: [
      { src: 'renders/detalle2_qat17_hero.png', title: 'Corte 3D QAT-17 · Roza PTL-2 y Canalón Cinc 35 cm', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle2_qat17_section.png', title: 'Sección Ortográfica QAT-17 (NTE)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle3: {
    glb: 'models/detalle3_cazoleta_sifonica.glb',
    blend: 'models/detalle3_cazoleta_sifonica.blend',
    dxf: 'planos_2d/detalle3_cazoleta_sifonica.dxf',
    pdf: 'planos_2d/detalle3_cazoleta_sifonica.pdf',
    svg: 'planos_2d/detalle3_cazoleta_sifonica.svg',
    png2d: 'planos_2d/detalle3_cazoleta_sifonica.png',
    renders: [
      { src: 'renders/detalle3_hero.png', title: 'Corte Constructivo Completo · Cazoleta Sifónica', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle3_closeup.png', title: 'Macro Sifón · Campana, Sello Hidráulico y Rejilla', tag: 'MACRO SIFÓN' },
      { src: 'renders/detalle3_section.png', title: 'Sección Ortográfica 1:1 (Diapositiva 21)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle4_plots: {
    glb: 'models/detalle4_invertida_plots.glb',
    blend: 'models/detalle4_invertida_plots.blend',
    dxf: 'planos_2d/detalle4_invertida_plots.dxf',
    pdf: 'planos_2d/detalle4_invertida_plots.pdf',
    svg: 'planos_2d/detalle4_invertida_plots.svg',
    png2d: 'planos_2d/detalle4_invertida_plots.png',
    renders: [
      { src: 'renders/detalle4_hero.png', title: 'Corte 3D Azotea Invertida · Pavimento Flotante sobre PLOTS', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle4_closeup.png', title: 'Macro Soportes Regulables (PLOTS) + XPS + Impermeabilización', tag: 'MACRO DETALLE' },
      { src: 'renders/detalle4_section.png', title: 'Sección Ortográfica 1:1 · Peto con Albardilla', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle5_alero_teja: {
    glb: 'models/detalle5_alero_teja_curva.glb',
    blend: 'models/detalle5_alero_teja_curva.blend',
    dxf: 'planos_2d/detalle5_alero_teja_curva.dxf',
    pdf: 'planos_2d/detalle5_alero_teja_curva.pdf',
    svg: 'planos_2d/detalle5_alero_teja_curva.svg',
    png2d: 'planos_2d/detalle5_alero_teja_curva.png',
    renders: [
      { src: 'renders/detalle5_hero.png', title: 'Tejado Teja Curva s/ Tabiquillos Palomeros · Alero + Canalón', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle5_closeup.png', title: 'Macro Alero QTT-14 · Vuelo 55 mm, Recalce M-2,5 y Canalón Zinc', tag: 'MACRO ALERO' },
      { src: 'renders/detalle5_section.png', title: 'Sección Ortográfica 1:1 · Palomeros Calados + Bardo', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle6_cumbrera_teja: {
    glb: 'models/detalle6_cumbrera_teja_ventilada.glb',
    blend: 'models/detalle6_cumbrera_teja_ventilada.blend',
    dxf: 'planos_2d/detalle6_cumbrera_teja_ventilada.dxf',
    pdf: 'planos_2d/detalle6_cumbrera_teja_ventilada.pdf',
    svg: 'planos_2d/detalle6_cumbrera_teja_ventilada.svg',
    png2d: 'planos_2d/detalle6_cumbrera_teja_ventilada.png',
    renders: [
      { src: 'renders/detalle6_hero.png', title: 'Cumbrera Ventilada en Seco · Teja Curva s/ Doble Rastrelado', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle6_closeup.png', title: 'Macro Caballete + Banda Ventilada + Clip Inox', tag: 'MACRO CUMBRERA' },
      { src: 'renders/detalle6_section.png', title: 'Sección Ortográfica Simétrica (32% ambas vertientes)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle7_teja_mixta: {
    glb: 'models/detalle7_teja_mixta_paramento.glb',
    blend: 'models/detalle7_teja_mixta_paramento.blend',
    dxf: 'planos_2d/detalle7_teja_mixta_paramento.dxf',
    pdf: 'planos_2d/detalle7_teja_mixta_paramento.pdf',
    svg: 'planos_2d/detalle7_teja_mixta_paramento.svg',
    png2d: 'planos_2d/detalle7_teja_mixta_paramento.png',
    renders: [
      { src: 'renders/detalle7_hero.png', title: 'Teja Mixta s/ Doble Rastrel · Encuentro con Paramento Vertical', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle7_closeup.png', title: 'Macro Babero Zinc ≥25 cm + Banda Autoadhesiva en Roza', tag: 'MACRO PARAMENTO' },
      { src: 'renders/detalle7_section.png', title: 'Sección Ortográfica 1:1 (Pend. 36% · Primer Rastrel +20 mm)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle8_pizarra: {
    glb: 'models/detalle8_pizarra_alero_qtp14.glb',
    blend: 'models/detalle8_pizarra_alero_qtp14.blend',
    dxf: 'planos_2d/detalle8_pizarra_alero_qtp14.dxf',
    pdf: 'planos_2d/detalle8_pizarra_alero_qtp14.pdf',
    svg: 'planos_2d/detalle8_pizarra_alero_qtp14.svg',
    png2d: 'planos_2d/detalle8_pizarra_alero_qtp14.png',
    renders: [
      { src: 'renders/detalle8_hero.png', title: 'Tejado Pizarra Natural QTP-14 · Emboble, Ganchos y Doble Rastrel', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle8_closeup.png', title: 'Macro Lajas Pizarra Biseladas + Ganchos AISI 316 + Chapa Goterón', tag: 'MACRO PIZARRA' },
      { src: 'renders/detalle8_section.png', title: 'Sección Ortográfica 1:1 (V=100 · R=100 · Pend. 56%)', tag: 'SECCIÓN ORTO' },
    ],
  },
  detalle9_zinc: {
    glb: 'models/detalle9_zinc_junta_alzada.glb',
    blend: 'models/detalle9_zinc_junta_alzada.blend',
    dxf: 'planos_2d/detalle9_zinc_junta_alzada.dxf',
    pdf: 'planos_2d/detalle9_zinc_junta_alzada.pdf',
    svg: 'planos_2d/detalle9_zinc_junta_alzada.svg',
    png2d: 'planos_2d/detalle9_zinc_junta_alzada.png',
    renders: [
      { src: 'renders/detalle9_hero.png', title: 'Cubierta Zinc VMZ en Junta Alzada · Bandejas 580 mm + Peto', tag: 'PERSPECTIVA 3D' },
      { src: 'renders/detalle9_closeup.png', title: 'Macro Doble Engatillado H=25 mm + Patas Fijas/Correderas Inox', tag: 'MACRO ZINC' },
      { src: 'renders/detalle9_section.png', title: 'Sección Ortográfica 1:1 · Entarimado Ventilado + Esterilla', tag: 'SECCIÓN ORTO' },
    ],
  },
};

let manifest = {};
let montajePhases = [];
let activeDetailId = 'detalle1';
let activeMode = 'montaje';
let selectedLayerCode = null;
let hiddenLayers = new Set();
let wireframeOn = false;
let explodeFactor = 0.0;
let cadShowMontajeSheet = false;

// CAD 2D Pan/Zoom state
let cadScale = 1.0;
let cadTx = 0;
let cadTy = 0;
let cadDragging = false;
let cadDragStart = { x: 0, y: 0 };

// General Three.js WebGL state
let threeInited = false;
let renderer, scene, camera, controls, gltfLoader;
let currentModelGroup = null;
let modelCenter = new THREE.Vector3();
let modelRadius = 1.0;
let meshToLayerMap = new Map();
let layerObjectsMap = new Map();
let originalPositions = new Map();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

// Montaje Piece-by-Piece Three.js + 2D Live state
let mntInited = false;
let mntRenderer, mntScene, mntCamera, mntControls;
let mntPieces = []; // { node, phase, tStart, tEnd, origPos, dropOffset }
let mntPlaying = false;
let mntTime = 30.0; // Start at 30.0s finished or play from 0 -> 30s
let mntLastTick = null;

async function init() {
  const [resM, resP] = await Promise.all([
    fetch('data/details_manifest.json'),
    fetch('data/montaje_phases.json'),
  ]);
  manifest = await resM.json();
  montajePhases = await resP.json();
  bimController = new BIMLibraryController();
  window.bimController = bimController;
  bindEvents();
  await initMontaje2DSVG();
  selectDetail('detalle1');
}

function bindEvents() {
  document.querySelectorAll('.cat-pill[data-cat]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.cat;
      document.querySelectorAll('.cat-pill[data-cat]').forEach((b) => b.classList.toggle('active', b === btn));
      const tabs = document.querySelectorAll('.detail-tab[data-detail]');
      let firstVisible = null;
      tabs.forEach((t) => {
        const match = (cat === 'all') || (t.dataset.cat === cat);
        t.classList.toggle('hidden-cat', !match);
        if (match && !firstVisible) firstVisible = t.dataset.detail;
      });
      const curTab = document.querySelector(`.detail-tab[data-detail="${activeDetailId}"]`);
      if (curTab && curTab.classList.contains('hidden-cat') && firstVisible) {
        selectDetail(firstVisible);
      }
    });
  });

  document.querySelectorAll('.detail-tab[data-detail]').forEach((btn) => {
    btn.addEventListener('click', () => selectDetail(btn.dataset.detail));
  });

  document.querySelectorAll('.mode-btn[data-mode]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const m = btn.dataset.mode;
      if ((m === 'montaje' || m === 'video') && activeDetailId !== 'detalle1') {
        selectDetail('detalle1');
      }
      setMode(m);
    });
  });

  const topPillBim = document.getElementById('top-pill-bim');
  if (topPillBim) {
    topPillBim.addEventListener('click', () => {
      setMode('bim');
    });
  }

  document.getElementById('btn-reset-layers').addEventListener('click', () => {
    hiddenLayers.clear();
    selectedLayerCode = null;
    applyLayerStates();
    renderSidebar();
  });

  // Montaje Controls
  document.getElementById('mnt-play').addEventListener('click', () => {
    if (mntTime >= 29.9) mntTime = 0.0;
    mntPlaying = !mntPlaying;
    mntLastTick = performance.now();
    updateMontajePlayButton();
  });
  document.getElementById('mnt-reset').addEventListener('click', () => {
    mntPlaying = false;
    mntTime = 0.0;
    updateMontajePlayButton();
    applyMontajeAtTime(mntTime);
  });
  document.getElementById('mnt-prev').addEventListener('click', () => {
    mntPlaying = false;
    updateMontajePlayButton();
    const cur = getMontajePhaseAtTime(mntTime);
    const prev = Math.max(1, cur - 1);
    jumpToMontajePhase(prev);
  });
  document.getElementById('mnt-next').addEventListener('click', () => {
    mntPlaying = false;
    updateMontajePlayButton();
    const cur = getMontajePhaseAtTime(mntTime);
    const nxt = Math.min(montajePhases.length || 12, cur + 1);
    jumpToMontajePhase(nxt);
  });
  document.getElementById('mnt-slider').addEventListener('input', (e) => {
    mntPlaying = false;
    updateMontajePlayButton();
    mntTime = (Number(e.target.value) / 300.0) * 30.0;
    applyMontajeAtTime(mntTime);
  });
  document.getElementById('mnt-toggle-2d-sheet').addEventListener('click', () => {
    cadShowMontajeSheet = true;
    setMode('cad2d');
    renderCad2D();
  });

  // WebGL controls
  document.querySelectorAll('[data-cam]').forEach((btn) => {
    btn.addEventListener('click', () => setCameraPreset(btn.dataset.cam));
  });
  document.getElementById('btn-wireframe').addEventListener('click', (e) => {
    wireframeOn = !wireframeOn;
    e.currentTarget.classList.toggle('active', wireframeOn);
    applyWireframe();
  });
  document.getElementById('explode-slider').addEventListener('input', (e) => {
    explodeFactor = Number(e.target.value) / 100.0;
    document.getElementById('explode-val').textContent = `${e.target.value}%`;
    applyExplode();
  });

  // 2D CAD controls
  const cadPane = document.getElementById('pane-cad2d');
  document.getElementById('cad-zoom-in').addEventListener('click', () => updateCadTransform(cadScale * 1.25));
  document.getElementById('cad-zoom-out').addEventListener('click', () => updateCadTransform(cadScale / 1.25));
  document.getElementById('cad-zoom-reset').addEventListener('click', () => {
    cadTx = 0;
    cadTy = 0;
    updateCadTransform(1.0);
  });
  document.getElementById('cad-toggle-montaje').addEventListener('click', () => {
    cadShowMontajeSheet = !cadShowMontajeSheet;
    renderCad2D();
  });

  cadPane.addEventListener('wheel', (e) => {
    if (activeMode !== 'cad2d') return;
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.14 : 0.88;
    updateCadTransform(cadScale * factor);
  }, { passive: false });

  cadPane.addEventListener('mousedown', (e) => {
    cadDragging = true;
    cadDragStart = { x: e.clientX - cadTx, y: e.clientY - cadTy };
  });
  window.addEventListener('mousemove', (e) => {
    if (!cadDragging) return;
    cadTx = e.clientX - cadDragStart.x;
    cadTy = e.clientY - cadDragStart.y;
    updateCadTransform(cadScale);
  });
  window.addEventListener('mouseup', () => { cadDragging = false; });

  const lb = document.getElementById('lightbox');
  lb.addEventListener('click', () => lb.classList.remove('open'));
}

function updateCadTransform(newScale) {
  cadScale = Math.max(0.5, Math.min(8.0, newScale));
  const stage = document.getElementById('cad-svg-stage');
  stage.style.transform = `translate(${cadTx}px, ${cadTy}px) scale(${cadScale})`;
  document.getElementById('cad-zoom-readout').textContent = `${Math.round(cadScale * 100)}%`;
}

function renderCad2D() {
  const f = DETAIL_FILES[activeDetailId];
  const d = manifest[activeDetailId];
  const isMnt = (activeDetailId === 'detalle1') && cadShowMontajeSheet;
  const svgUrl = isMnt ? f.montaje_svg : f.svg;
  const pngUrl = isMnt ? f.montaje_png : f.png2d;
  document.getElementById('cad-svg-stage').innerHTML = `<img src="${svgUrl}?v=${Date.now()}" alt="Plano Técnico 2D ${d.code}" />`;
  document.getElementById('split-2d-img').src = `${pngUrl}?v=${Date.now()}`;
  const tBtn = document.getElementById('cad-toggle-montaje');
  tBtn.style.display = activeDetailId === 'detalle1' ? 'inline-block' : 'none';
  tBtn.textContent = isMnt ? 'Ver Plano Capas IVE (P..SR)' : 'Ver Plano 2D Montaje (Fases 01–10)';
}

function selectDetail(detailId) {
  activeDetailId = detailId;
  selectedLayerCode = null;
  hiddenLayers.clear();
  explodeFactor = 0.0;
  document.getElementById('explode-slider').value = '0';
  document.getElementById('explode-val').textContent = '0%';

  if (detailId !== 'detalle1' && (activeMode === 'montaje' || activeMode === 'video')) {
    activeMode = 'renders';
  }

  document.querySelectorAll('.detail-tab').forEach((b) => {
    b.classList.toggle('active', b.dataset.detail === detailId);
  });

  // Show/hide Montaje & Video mode buttons cleanly (available for detalle1)
  document.querySelectorAll('.mode-btn').forEach((b) => {
    if (b.dataset.mode === 'montaje' || b.dataset.mode === 'video') {
      b.style.display = detailId === 'detalle1' ? 'inline-block' : 'none';
    }
  });

  const d = manifest[detailId];
  const f = DETAIL_FILES[detailId];

  document.getElementById('hero-code').textContent = d.code;
  document.getElementById('hero-slide').textContent = d.slide;
  document.getElementById('hero-scale').textContent = `Escala 2D ${d.scale_2d} · Precisión 1:1 mm`;
  document.getElementById('hero-normativa').textContent = d.normativa;
  document.getElementById('hero-title').textContent = d.title;
  document.getElementById('hero-subtitle').textContent = d.subtitle;

  const cadBtn = document.getElementById('mode-cad2d-btn');
  if (cadBtn) cadBtn.textContent = `Plano 2D Acabado (E ${d.scale_2d})`;
  const splitLbl = document.getElementById('split-2d-label');
  if (splitLbl) splitLbl.textContent = `SECCIÓN TÉCNICA 2D MILIMÉTRICA (E ${d.scale_2d})`;

  const b = d.bounds_mm;
  document.getElementById('bounds-readout').textContent =
    `Envolvente: ${Math.round(b.x_max - b.x_min)} × ${Math.round(b.y_max - b.y_min)} × ${Math.round(b.z_max - b.z_min)} mm`;

  // Renders grid
  const rGrid = document.getElementById('renders-grid');
  rGrid.innerHTML = '';
  f.renders.forEach((r) => {
    const card = document.createElement('div');
    card.className = 'render-card';
    card.innerHTML = `
      <img src="${r.src}?v=${Date.now()}" alt="${r.title}" loading="lazy" />
      <div class="render-caption">
        <span>${r.title}</span>
        <span class="tag">${r.tag}</span>
      </div>
    `;
    card.addEventListener('click', () => {
      document.getElementById('lightbox-img').src = `${r.src}?v=${Date.now()}`;
      document.getElementById('lightbox').classList.add('open');
    });
    rGrid.appendChild(card);
  });

  cadTx = 0;
  cadTy = 0;
  updateCadTransform(1.0);
  renderCad2D();
  document.getElementById('split-3d-img').src = `${f.renders[0].src}?v=${Date.now()}`;

  // Downloads
  const dl = document.getElementById('downloads-list');
  const dlItems = [
    { ext: '.GLB', label: 'Modelo 3D PBR Web/AR', href: f.glb },
    { ext: '.BLEND', label: 'Escena Blender 5.2 Cycles', href: f.blend },
    { ext: '.DXF', label: 'Plano AutoCAD 2D (1:1 mm)', href: f.dxf },
    { ext: '.PDF', label: `Lámina Vectorial A3 (${d.scale_2d})`, href: f.pdf },
    { ext: '.SVG', label: 'Plano Vectorial SVG', href: f.svg },
    { ext: '.PNG', label: 'Render Fotorrealista 3D', href: f.renders[0].src },
  ];
  if (detailId === 'detalle1') {
    dlItems.push(
      { ext: '.MP4', label: 'Vídeo Montaje 30s Full HD', href: f.montaje_mp4 },
      { ext: '2D+01-10', label: 'Lámina 2D Montaje (PDF A3)', href: f.montaje_pdf },
      { ext: 'DXF 01-10', label: 'CAD Montaje 2D (.dxf)', href: f.montaje_dxf },
      { ext: 'GLB PIEZAS', label: 'Modelo 3D 95 Piezas (.glb)', href: f.montaje_glb }
    );
  }
  dl.innerHTML = dlItems.map((it) => `
    <a class="dl-btn" href="${it.href}" download>
      <span class="dl-ext">${it.ext}</span>
      <span class="dl-label">${it.label}</span>
    </a>
  `).join('');

  setMode(activeMode);
  renderSidebar();
  renderSpecTable();

  if (threeInited) loadGLB(f.glb);
}

function setMode(mode) {
  activeMode = mode;
  document.querySelectorAll('.mode-btn[data-mode]').forEach((b) => {
    b.classList.toggle('active', b.dataset.mode === mode);
  });

  document.getElementById('pane-montaje').classList.toggle('active', mode === 'montaje');
  document.getElementById('pane-video').classList.toggle('active', mode === 'video');
  document.getElementById('pane-renders').classList.toggle('active', mode === 'renders');
  document.getElementById('pane-webgl').classList.toggle('active', mode === 'webgl');
  document.getElementById('pane-cad2d').classList.toggle('active', mode === 'cad2d');
  document.getElementById('pane-split').classList.toggle('active', mode === 'split');
  const paneBim = document.getElementById('pane-bim');
  if (paneBim) paneBim.classList.toggle('active', mode === 'bim');

  const studioGrid = document.getElementById('studio-grid');
  if (studioGrid) studioGrid.classList.toggle('bim-mode-active', mode === 'bim');

  document.getElementById('controls-montaje').style.display = mode === 'montaje' ? 'flex' : 'none';
  document.getElementById('controls-webgl').style.display = mode === 'webgl' ? 'flex' : 'none';
  document.getElementById('controls-cad2d').style.display = mode === 'cad2d' ? 'flex' : 'none';
  document.getElementById('controls-info').style.display = (mode === 'renders' || mode === 'split' || mode === 'video') ? 'flex' : 'none';
  document.getElementById('controls-reset-wrap').style.display = mode === 'webgl' ? 'flex' : 'none';
  const controlsBim = document.getElementById('controls-bim');
  if (controlsBim) controlsBim.style.display = mode === 'bim' ? 'flex' : 'none';

  if (mode !== 'montaje') {
    mntPlaying = false;
    updateMontajePlayButton();
  }
  if (mode !== 'video') {
    const vid = document.getElementById('montaje-video');
    if (vid && !vid.paused) vid.pause();
  }

  if (mode === 'webgl') {
    if (!threeInited) {
      initThree();
      loadGLB(DETAIL_FILES[activeDetailId].glb);
    } else {
      handleResize();
    }
  } else if (mode === 'montaje') {
    if (!mntInited) {
      initMontajeThree();
    } else {
      handleMontajeResize();
    }
  } else if (mode === 'bim' && bimController) {
    bimController.initWorkspace();
  }
  renderSidebar();
}

function renderSidebar() {
  const list = document.getElementById('layers-list');
  list.innerHTML = '';

  if (activeMode === 'montaje' || activeMode === 'video') {
    document.getElementById('sidebar-title').textContent = `Fases de Montaje (${montajePhases.length})`;
    document.getElementById('sidebar-hint').textContent = 'Clic para ir a fase';
    const curPh = getMontajePhaseAtTime(mntTime);
    const nPh = montajePhases.length || 12;
    const tEndAll = (montajePhases[nPh - 1] && montajePhases[nPh - 1].t_end) || 27.5;
    const finished = mntTime >= tEndAll;

    montajePhases.forEach((ph) => {
      const isCur = !finished && ph.phase === curPh;
      const isDone = finished || ph.phase < curPh;
      const div = document.createElement('div');
      div.className = 'layer-item' + (isCur ? ' selected' : '');
      div.innerHTML = `
        <div class="layer-top">
          <div class="layer-badge-wrap">
            <span class="layer-swatch" style="background:${ph.color};"></span>
            <span class="layer-code">FASE ${String(ph.phase).padStart(2, '0')} · ${ph.code}</span>
          </div>
          <span class="layer-thick">${isDone ? '✓ Montada' : (isCur ? '▶ Activa' : ph.thickness)}</span>
        </div>
        <div class="layer-name">${ph.title}</div>
        <div class="layer-spec">${ph.desc}</div>
      `;
      div.addEventListener('click', () => {
        if (activeMode === 'video') {
          const vid = document.getElementById('montaje-video');
          if (vid) { vid.currentTime = ph.t_start + 0.2; vid.play(); }
        } else {
          mntPlaying = false;
          updateMontajePlayButton();
          jumpToMontajePhase(ph.phase);
        }
      });
      list.appendChild(div);
    });
    if (bimController) bimController.renderDetailCommercialProductsBlock(activeDetailId);
    return;
  }

  const d = manifest[activeDetailId];
  document.getElementById('sidebar-title').textContent = `Capas Constructivas (${d.layers.length})`;
  document.getElementById('sidebar-hint').textContent = 'Clic para aislar / ver';

  d.layers.forEach((l) => {
    const div = document.createElement('div');
    div.className = 'layer-item' + (selectedLayerCode === l.code ? ' selected' : '');
    const isHidden = hiddenLayers.has(l.code);
    div.innerHTML = `
      <div class="layer-top">
        <div class="layer-badge-wrap">
          <span class="layer-swatch" style="background:${l.color};"></span>
          <span class="layer-code">${l.code}</span>
          <span class="layer-thick">${l.thickness_mm}</span>
        </div>
        <button class="layer-vis-btn ${isHidden ? 'hidden-layer' : ''}" title="Mostrar / ocultar capa">
          ${isHidden ? 'Oculta' : 'Visible'}
        </button>
      </div>
      <div class="layer-name">${l.name}</div>
      <div class="layer-spec">${l.spec}</div>
    `;
    div.querySelector('.layer-vis-btn').addEventListener('click', (ev) => {
      ev.stopPropagation();
      if (hiddenLayers.has(l.code)) hiddenLayers.delete(l.code);
      else hiddenLayers.add(l.code);
      applyLayerStates();
      renderSidebar();
    });
    div.addEventListener('click', () => {
      selectedLayerCode = selectedLayerCode === l.code ? null : l.code;
      applyLayerStates();
      renderSidebar();
    });
    list.appendChild(div);
  });
  if (bimController) bimController.renderDetailCommercialProductsBlock(activeDetailId);
}

function renderSpecTable() {
  const d = manifest[activeDetailId];
  const tbody = document.getElementById('spec-tbody');
  tbody.innerHTML = d.layers.map((l) => `
    <tr>
      <td><span class="pill" style="border-left:4px solid ${l.color};">${l.code}</span></td>
      <td><strong>${l.name}</strong></td>
      <td style="font-family:var(--font-mono); color:var(--accent-green); font-weight:600;">${l.thickness_mm}</td>
      <td style="color:var(--ink-secondary);">${l.spec}</td>
    </tr>
  `).join('');
}

// ==============================================================================
// Interactive Software de Montaje (95 Piezas GLB + Live 2D SVG Sync)
// ==============================================================================
async function initMontaje2DSVG() {
  const box = document.getElementById('montaje-2d-svg-box');
  try {
    const txt = await (await fetch(DETAIL_FILES.detalle1.montaje_svg_live)).text();
    box.innerHTML = txt;
  } catch (err) {
    box.innerHTML = `<img src="${DETAIL_FILES.detalle1.png2d}" alt="2D"/>`;
  }

  // Build bottom 10-step chips
  const strip = document.getElementById('montaje-stepper');
  strip.innerHTML = '';
  montajePhases.forEach((ph) => {
    const btn = document.createElement('button');
    btn.className = 'step-chip';
    btn.dataset.phase = String(ph.phase);
    btn.innerHTML = `<span class="sc-num">FASE ${String(ph.phase).padStart(2, '0')}</span><span class="sc-lbl">${ph.code}</span>`;
    btn.addEventListener('click', () => {
      mntPlaying = false;
      updateMontajePlayButton();
      jumpToMontajePhase(ph.phase);
    });
    strip.appendChild(btn);
  });
}

function initMontajeThree() {
  const wrap = document.getElementById('montaje-webgl-wrap');
  mntRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  mntRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  mntRenderer.setSize(wrap.clientWidth, wrap.clientHeight);
  mntRenderer.toneMapping = THREE.ACESFilmicToneMapping;
  mntRenderer.toneMappingExposure = 1.08;
  mntRenderer.shadowMap.enabled = true;
  wrap.appendChild(mntRenderer.domElement);

  mntScene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(mntRenderer);
  mntScene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  mntCamera = new THREE.PerspectiveCamera(42, wrap.clientWidth / wrap.clientHeight, 0.01, 50.0);
  mntControls = new OrbitControls(mntCamera, mntRenderer.domElement);
  mntControls.enableDamping = true;
  mntControls.dampingFactor = 0.06;

  mntScene.add(new THREE.HemisphereLight(0xf6f8fc, 0x3b352d, 0.55));
  const key = new THREE.DirectionalLight(0xfff5e8, 2.2);
  key.position.set(-2.5, 3.2, 2.6);
  key.castShadow = true;
  mntScene.add(key);
  const rim = new THREE.DirectionalLight(0xd9e8ff, 1.0);
  rim.position.set(2.4, 2.0, -2.2);
  mntScene.add(rim);

  const loader = new GLTFLoader();
  loader.load(`${DETAIL_FILES.detalle1.montaje_glb}?v=${Date.now()}`, (gltf) => {
    const root = gltf.scene;
    mntScene.add(root);

    const box = new THREE.Box3().setFromObject(root);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const rad = Math.max(size.x, size.y, size.z) * 0.68;

    mntControls.target.copy(center);
    mntCamera.position.set(center.x - rad * 1.35, center.y + rad * 0.85, center.z + rad * 1.45);
    mntControls.update();

    // Parse every piece PH01..PH12 with strict numeric ordering and in-situ animation mode
    const nPh = montajePhases.length || 12;
    const byPhase = new Map();
    for (let i = 1; i <= nPh; i++) byPhase.set(i, []);
    root.traverse((child) => {
      if (!child.isMesh) return;
      const rawName = (child.name && /^PH\d{2}_/.test(child.name)) ? child.name : ((child.parent && child.parent.name) || '');
      const m = rawName.match(/^PH(\d{2})_/);
      if (m) {
        const ph = Number(m[1]);
        if (byPhase.has(ph)) {
          child.userData.sortName = rawName;
          byPhase.get(ph).push(child);
        }
      }
    });

    mntPieces = [];
    const slopeAng = Math.atan(0.025);
    for (let ph = 1; ph <= nPh; ph++) {
      const phMeta = montajePhases[ph - 1];
      if (!phMeta) continue;
      const list = byPhase.get(ph).sort((a, b) =>
        (a.userData.sortName || a.name).localeCompare(b.userData.sortName || b.name, undefined, { numeric: true })
      );
      const span = (phMeta.t_end - phMeta.t_start) * 0.90;
      const pieceDur = Math.min(0.62, Math.max(0.24, span * 0.42));
      list.forEach((node, idx) => {
        const frac = list.length > 1 ? idx / (list.length - 1) : 0;
        const ts = phMeta.t_start + frac * Math.max(0.05, span - pieceDur);
        const te = ts + pieceDur;

        const sn = node.userData.sortName || node.name;
        let animType = 'PLACE';
        if (sn.includes('__POURZ') || sn.includes('__TROWELZ')) {
          animType = 'GROW_Y';
          node.geometry.computeBoundingBox();
          const minY = node.geometry.boundingBox.min.y;
          node.geometry.translate(0, -minY, 0);
          node.position.y += minY;
        } else if (sn.includes('__ROLLX')) {
          animType = 'ROLL_X';
          node.geometry.computeBoundingBox();
          const minX = node.geometry.boundingBox.min.x;
          const minY = node.geometry.boundingBox.min.y;
          node.geometry.translate(-minX, -minY, 0);
          node.geometry.rotateZ(-slopeAng);
          node.position.set(node.position.x + minX, node.position.y + minY, node.position.z);
          node.rotation.z = slopeAng;
        }

        mntPieces.push({
          node,
          phase: ph,
          animType,
          tStart: ts,
          tEnd: te,
          origPos: node.position.clone(),
          dropY: 0.045,
        });
      });
    }

    // Auto-start playback smoothly from 0 -> 30s if user clicks Secuencia Montaje!
    mntTime = 0.0;
    mntPlaying = true;
    mntLastTick = performance.now();
    updateMontajePlayButton();
    applyMontajeAtTime(mntTime);
  });

  window.addEventListener('resize', handleMontajeResize);
  mntInited = true;
  animateMontaje();
}

function handleMontajeResize() {
  if (!mntInited) return;
  const wrap = document.getElementById('montaje-webgl-wrap');
  if (!wrap || wrap.clientWidth === 0 || wrap.clientHeight === 0) return;
  mntCamera.aspect = wrap.clientWidth / wrap.clientHeight;
  mntCamera.updateProjectionMatrix();
  mntRenderer.setSize(wrap.clientWidth, wrap.clientHeight);
}

function getMontajePhaseAtTime(t) {
  for (const ph of montajePhases) {
    if (t >= ph.t_start && t < ph.t_end) return ph.phase;
  }
  return montajePhases.length || 12;
}

function jumpToMontajePhase(phNum) {
  const ph = montajePhases[phNum - 1];
  if (!ph) return;
  mntTime = ph.t_end - 0.02;
  applyMontajeAtTime(mntTime);
}

function updateMontajePlayButton() {
  const btn = document.getElementById('mnt-play');
  if (btn) btn.textContent = mntPlaying ? '⏸ Pausar' : '▶ Reproducir (30s)';
}

function easeOutCubic(x) {
  return 1 - Math.pow(1 - Math.max(0, Math.min(1, x)), 3);
}

function applyMontajeAtTime(t) {
  const nPh = montajePhases.length || 12;
  const activePh = getMontajePhaseAtTime(t);
  const tFinish = (montajePhases[nPh - 1] && montajePhases[nPh - 1].t_end) || 27.5;
  const finished = t >= tFinish;
  const phMeta = montajePhases[activePh - 1];

  // Update 3D pieces with physically grounded animation per type
  for (const p of mntPieces) {
    if (t < p.tStart) {
      p.node.visible = false;
    } else if (t >= p.tEnd) {
      p.node.visible = true;
      p.node.position.copy(p.origPos);
      p.node.scale.set(1, 1, 1);
    } else {
      p.node.visible = true;
      const u = easeOutCubic((t - p.tStart) / (p.tEnd - p.tStart));
      if (p.animType === 'GROW_Y') {
        p.node.position.copy(p.origPos);
        p.node.scale.set(1, 0.015 + 0.985 * u, 1);
      } else if (p.animType === 'ROLL_X') {
        p.node.position.copy(p.origPos);
        p.node.scale.set(0.012 + 0.988 * u, 1, 1);
      } else {
        p.node.scale.set(1, 1, 1);
        p.node.position.set(p.origPos.x, p.origPos.y + p.dropY * (1.0 - u), p.origPos.z);
      }
    }
  }

  // Update Live 2D SVG phases
  const svgBox = document.getElementById('montaje-2d-svg-box');
  if (svgBox) {
    for (let i = 1; i <= nPh; i++) {
      const g = svgBox.querySelector(`#phase_${i}`);
      if (g) {
        const show = finished ? true : (i <= activePh);
        g.style.display = show ? 'inline' : 'none';
        g.style.opacity = (!finished && i === activePh) ? '1.0' : '0.92';
      }
    }
  }

  // Update HUD text & slider
  document.getElementById('mnt-slider').value = String(Math.round((t / 30.0) * 300));
  document.getElementById('mnt-time-readout').textContent = `${t.toFixed(1)}s / 30.0s`;
  document.getElementById('mnt-phase-pill').textContent = finished ? `COMPLETADO ${nPh}/${nPh}` : `FASE ${String(activePh).padStart(2, '0')} / ${nPh}`;

  if (finished) {
    document.getElementById('mnt-card-code').textContent = `MONTAJE COMPLETADO · ${nPh} / ${nPh} FASES`;
    document.getElementById('mnt-card-title').textContent = 'Azotea Transitable · Detalle Constructivo Finalizado';
    document.getElementById('mnt-card-desc').textContent = 'Ejecución en orden real al 100%: viguetas, bovedillas cerámicas reales, ferralla + HA-25, fábrica LHD, enfoscados, EPS + FP 2,5%, BV, XPS, membrana SBS, geotextil, pavimento P y rodapié.';
    document.getElementById('mnt-2d-status').textContent = 'PLANO 2D ACABADO 100%';
  } else if (phMeta) {
    document.getElementById('mnt-card-code').textContent = `FASE ${String(activePh).padStart(2, '0')} · ${phMeta.code} (${phMeta.thickness})`;
    document.getElementById('mnt-card-title').textContent = phMeta.title;
    document.getElementById('mnt-card-desc').textContent = phMeta.desc;
    document.getElementById('mnt-2d-status').textContent = `PROGRESO 2D · FASE ${String(activePh).padStart(2, '0')}/${nPh}`;
  }

  document.querySelectorAll('.step-chip').forEach((chip) => {
    const pNum = Number(chip.dataset.phase);
    chip.classList.toggle('active', !finished && pNum === activePh);
    chip.classList.toggle('done', finished || pNum < activePh);
  });

  if (activeMode === 'montaje') renderSidebar();
}

function animateMontaje(now) {
  requestAnimationFrame(animateMontaje);
  if (activeMode !== 'montaje' || !mntInited) return;

  if (mntPlaying) {
    const dt = mntLastTick ? Math.min(0.1, (now - mntLastTick) / 1000.0) : 0.016;
    mntLastTick = now;
    mntTime += dt;
    if (mntTime >= 30.0) {
      mntTime = 30.0;
      mntPlaying = false;
      updateMontajePlayButton();
    }
    applyMontajeAtTime(mntTime);
  }
  mntControls.update();
  mntRenderer.render(mntScene, mntCamera);
}

// ==============================================================================
// Standard Three.js WebGL Studio (All 4 Models)
// ==============================================================================
function initThree() {
  const wrap = document.getElementById('webgl-canvas-wrap');
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(wrap.clientWidth, wrap.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  wrap.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  camera = new THREE.PerspectiveCamera(40, wrap.clientWidth / wrap.clientHeight, 0.01, 50.0);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;

  scene.add(new THREE.HemisphereLight(0xf6f8fc, 0x3b352d, 0.55));
  const key = new THREE.DirectionalLight(0xfff5e8, 2.2);
  key.position.set(-2.5, 3.2, 2.6);
  key.castShadow = true;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xd9e8ff, 1.1);
  rim.position.set(2.4, 2.0, -2.2);
  scene.add(rim);

  gltfLoader = new GLTFLoader();
  window.addEventListener('resize', handleResize);
  renderer.domElement.addEventListener('pointermove', onPointerMove);
  renderer.domElement.addEventListener('click', onPointerClick);

  threeInited = true;
  animate();
}

function handleResize() {
  if (!threeInited) return;
  const wrap = document.getElementById('webgl-canvas-wrap');
  if (wrap.clientWidth === 0 || wrap.clientHeight === 0) return;
  camera.aspect = wrap.clientWidth / wrap.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(wrap.clientWidth, wrap.clientHeight);
}

function findLayerForObject(obj, layers) {
  let cur = obj;
  while (cur && cur !== currentModelGroup) {
    const clean = (cur.name || '').replace(/\.\d+$/, '');
    for (const l of layers) {
      if (l.mesh_keys.some((k) => clean === k || clean.startsWith(k))) return l;
    }
    cur = cur.parent;
  }
  return null;
}

function loadGLB(url) {
  if (currentModelGroup) {
    scene.remove(currentModelGroup);
    currentModelGroup = null;
  }
  meshToLayerMap.clear();
  layerObjectsMap.clear();
  originalPositions.clear();

  const d = manifest[activeDetailId];
  gltfLoader.load(`${url}?v=${Date.now()}`, (gltf) => {
    currentModelGroup = gltf.scene;
    scene.add(currentModelGroup);

    const visitedNodes = new Set();
    currentModelGroup.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        if (child.material) {
          const mats = Array.isArray(child.material) ? child.material : [child.material];
          mats.forEach((m) => {
            if (m.name && m.name.includes('Agua')) {
              m.transparent = true;
              m.opacity = 0.62;
              m.roughness = 0.05;
              m.color.set('#46b8e8');
            }
            m.userData.origEmissive = m.emissive ? m.emissive.clone() : new THREE.Color(0);
          });
        }
        const layer = findLayerForObject(child, d.layers);
        if (layer) {
          meshToLayerMap.set(child, layer);
          if (!layerObjectsMap.has(layer.code)) layerObjectsMap.set(layer.code, []);
          let topNode = child;
          while (topNode.parent && topNode.parent !== currentModelGroup && findLayerForObject(topNode.parent, d.layers) === layer) {
            topNode = topNode.parent;
          }
          if (!visitedNodes.has(topNode)) {
            visitedNodes.add(topNode);
            layerObjectsMap.get(layer.code).push(topNode);
            originalPositions.set(topNode, topNode.position.clone());
          }
        }
      }
    });

    const box = new THREE.Box3().setFromObject(currentModelGroup);
    box.getCenter(modelCenter);
    const size = box.getSize(new THREE.Vector3());
    modelRadius = Math.max(size.x, size.y, size.z) * 0.65;

    setCameraPreset('iso');
    applyLayerStates();
    applyWireframe();
    applyExplode();
  });
}

function setCameraPreset(preset) {
  if (!threeInited) return;
  const dist = modelRadius * 2.45;
  controls.target.copy(modelCenter);
  if (preset === 'front') {
    camera.position.set(modelCenter.x, modelCenter.y + modelRadius * 0.15, modelCenter.z + dist * 1.15);
  } else if (preset === 'top') {
    camera.position.set(modelCenter.x, modelCenter.y + dist * 1.25, modelCenter.z + 0.05);
  } else {
    camera.position.set(modelCenter.x - dist * 0.72, modelCenter.y + dist * 0.56, modelCenter.z + dist * 0.86);
  }
  controls.update();
}

function applyExplode() {
  const d = manifest[activeDetailId];
  d.layers.forEach((l) => {
    const nodes = layerObjectsMap.get(l.code) || [];
    const offsetY = (l.explode_z || 0) * 0.001 * explodeFactor;
    nodes.forEach((node) => {
      const orig = originalPositions.get(node);
      if (orig) node.position.set(orig.x, orig.y + offsetY, orig.z);
    });
  });
}

function applyLayerStates() {
  if (!currentModelGroup) return;
  currentModelGroup.traverse((child) => {
    if (!child.isMesh) return;
    const layer = meshToLayerMap.get(child);
    if (!layer) return;
    child.visible = !hiddenLayers.has(layer.code);
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    mats.forEach((m) => {
      if (!m || !m.emissive) return;
      if (selectedLayerCode && selectedLayerCode === layer.code) {
        m.emissive.set('#b84a32');
        m.emissiveIntensity = 0.38;
      } else {
        m.emissive.copy(m.userData.origEmissive || new THREE.Color(0));
        m.emissiveIntensity = 1.0;
      }
    });
  });
}

function applyWireframe() {
  if (!currentModelGroup) return;
  currentModelGroup.traverse((child) => {
    if (child.isMesh && child.material) {
      const mats = Array.isArray(child.material) ? child.material : [child.material];
      mats.forEach((m) => { m.wireframe = wireframeOn; });
    }
  });
}

function pickLayerAtEvent(e) {
  if (!currentModelGroup) return null;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObject(currentModelGroup, true).filter((h) => h.object.visible);
  return hits.length ? (meshToLayerMap.get(hits[0].object) || null) : null;
}

function onPointerMove(e) {
  const hoverEl = document.getElementById('webgl-hover');
  const layer = pickLayerAtEvent(e);
  if (layer) {
    hoverEl.style.display = 'block';
    hoverEl.textContent = `${layer.code} · ${layer.name} (${layer.thickness_mm})`;
    renderer.domElement.style.cursor = 'pointer';
  } else {
    hoverEl.style.display = 'none';
    renderer.domElement.style.cursor = 'grab';
  }
}

function onPointerClick(e) {
  const layer = pickLayerAtEvent(e);
  if (layer) {
    selectedLayerCode = selectedLayerCode === layer.code ? null : layer.code;
    applyLayerStates();
    renderSidebar();
  }
}

function animate() {
  requestAnimationFrame(animate);
  if (activeMode === 'webgl' && renderer && scene && camera) {
    controls.update();
    renderer.render(scene, camera);
  }
}

init();
