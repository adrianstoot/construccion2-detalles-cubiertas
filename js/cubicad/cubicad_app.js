/**
 * =============================================================================
 * CubiCAD · Constructor CAD/BIM de Cubiertas (ETSIE · UPV)
 * Controlador Principal de la Aplicación
 * =============================================================================
 */

import {
  BIM_FAMILIES,
  BIM_MANUFACTURERS,
  VERIFICATION_BADGES,
  BIMCatalogStore,
} from '../bim/catalog_db.js';
import {
  BIMReplanteoCalculator,
  BIMCompatibilityEngine,
} from '../bim/compatibility_replanteo.js';
import { ICONS } from './icons.js';
import { TYPOLOGY_PRESETS, CubiCADStateManager } from './state_history.js';
import { CubiCADBuilder3D } from './builder_3d.js';
import { CubiCADLiveDetail2D } from './live_detail_2d.js';
import { CUBICAD_TUTORIALS } from './tutorials.js';

const ATLAS_DETAILS_META = [
  { id: 'detalle1', code: 'DET-01', name: 'Azotea Convencional · Peto', svg: 'planos_2d/detalle1_ive_peto.svg', render: 'renders/detalle1_hero.png', pdf: 'planos_2d/detalle1_ive_peto.pdf', glb: 'models/detalle1_ive_peto.glb' },
  { id: 'detalle2_qat16', code: 'DET-02A', name: 'Encuentro Cazoleta QAT-16', svg: 'planos_2d/detalle2_nte_qat16_cazoleta.svg', render: 'renders/detalle2_qat16_hero.png', pdf: 'planos_2d/detalle2_nte_qat16_cazoleta.pdf', glb: 'models/detalle2_nte_qat16_cazoleta.glb' },
  { id: 'detalle2_qat17', code: 'DET-02B', name: 'Canalón Cinc QAT-17', svg: 'planos_2d/detalle2_nte_qat17_canalon.svg', render: 'renders/detalle2_qat17_hero.png', pdf: 'planos_2d/detalle2_nte_qat17_canalon.pdf', glb: 'models/detalle2_nte_qat17_canalon.glb' },
  { id: 'detalle3', code: 'DET-03', name: 'Cazoleta Sifónica Diap. 21', svg: 'planos_2d/detalle3_cazoleta_sifonica.svg', render: 'renders/detalle3_hero.png', pdf: 'planos_2d/detalle3_cazoleta_sifonica.pdf', glb: 'models/detalle3_cazoleta_sifonica.glb' },
  { id: 'detalle4_plots', code: 'DET-04', name: 'Azotea Invertida sobre Plots', svg: 'planos_2d/detalle4_invertida_plots.svg', render: 'renders/detalle4_hero.png', pdf: 'planos_2d/detalle4_invertida_plots.pdf', glb: 'models/detalle4_invertida_plots.glb' },
  { id: 'detalle5_alero_teja', code: 'DET-05', name: 'Teja Curva · Alero y Canalón', svg: 'planos_2d/detalle5_alero_teja_curva.svg', render: 'renders/detalle5_hero.png', pdf: 'planos_2d/detalle5_alero_teja_curva.pdf', glb: 'models/detalle5_alero_teja_curva.glb' },
  { id: 'detalle6_cumbrera_teja', code: 'DET-06', name: 'Cumbrera Ventilada en Seco', svg: 'planos_2d/detalle6_cumbrera_teja_ventilada.svg', render: 'renders/detalle6_hero.png', pdf: 'planos_2d/detalle6_cumbrera_teja_ventilada.pdf', glb: 'models/detalle6_cumbrera_teja_ventilada.glb' },
  { id: 'detalle7_teja_mixta', code: 'DET-07', name: 'Teja Mixta · Doble Rastrel', svg: 'planos_2d/detalle7_teja_mixta_paramento.svg', render: 'renders/detalle7_hero.png', pdf: 'planos_2d/detalle7_teja_mixta_paramento.pdf', glb: 'models/detalle7_teja_mixta_paramento.glb' },
  { id: 'detalle8_pizarra', code: 'DET-08', name: 'Pizarra Natural QTP-14', svg: 'planos_2d/detalle8_pizarra_alero_qtp14.svg', render: 'renders/detalle8_hero.png', pdf: 'planos_2d/detalle8_pizarra_alero_qtp14.pdf', glb: 'models/detalle8_pizarra_alero_qtp14.glb' },
  { id: 'detalle9_zinc', code: 'DET-09', name: 'Zinc VMZ Junta Alzada', svg: 'planos_2d/detalle9_zinc_junta_alzada.svg', render: 'renders/detalle9_hero.png', pdf: 'planos_2d/detalle9_zinc_junta_alzada.pdf', glb: 'models/detalle9_zinc_junta_alzada.glb' },
];

class CubiCADApp {
  constructor() {
    this.store = new BIMCatalogStore();
    this.stateManager = new CubiCADStateManager();
    this.builder3D = null;

    this.activeMainTab = 'builder'; // 'builder' | 'manufacturers' | 'hydro' | 'details2d' | 'render'
    this.activeFlyout = null; // ID del flyout abierto junto a la paleta izquierda
    this.liveDetail2DOpen = false;
    this.inspectorOpen = true;
    this.theme = 'light'; // Apple Blanco/Negro limpio por defecto

    this.currentReplanteo = null;
    this.currentCompatibility = null;
    this.capturedRenders = [];
    this.activeDetail2DSubTab = 'live'; // 'live' | 'atlas'
    this.activeAtlasId = 'detalle1';
    this.atlasManifest = null;

    // Filtros de Fabricantes y Comparador
    this.catalogFilter = { familyId: 'ALL', manufacturerId: 'ALL', search: '' };
    this.compareQueue = ['BORJA-C5021', 'BORJA-TB12', 'BMI-COBERT-GREDOS', 'CUPA-4-3222'];

    // Estado del Tutorial Interactivo
    this.activeTutorialId = null;
    this.activeTutorialStep = 0;

    this._init();
  }

  async _init() {
    this._renderStaticIcons();
    this._bindGlobalNavigation();
    this._bindKeyboardShortcuts();
    this._init3DBuilder();

    this.stateManager.subscribe((state, reason) => {
      this._recomputeAndSyncAll(reason);
    });

    this._recomputeAndSyncAll('init');

    // Cargar manifiesto de los 10 detalles de referencia en segundo plano
    try {
      const res = await fetch('data/details_manifest.json');
      if (res.ok) this.atlasManifest = await res.json();
    } catch (e) {
      console.warn('No se pudo cargar manifest del atlas:', e);
    }

    // Mostrar bienvenida / selector de tutorial de primer uso si es la primera visita
    const seen = localStorage.getItem('CUBICAD_ONBOARDING_SEEN_V1');
    if (!seen) {
      this.openTutorialLauncherModal();
    }
  }

  _renderStaticIcons() {
    const map = {
      'brand-logo-icon': ICONS.logo,
      'icon-tab-builder': ICONS.explode,
      'icon-tab-mfg': ICONS.catalog,
      'icon-tab-hydro': ICONS.water,
      'icon-tab-2d': ICONS.detail2d,
      'icon-tab-render': ICONS.render,
      'icon-typo-tejado': ICONS.typoTejado,
      'icon-typo-azotea': ICONS.typoAzotea,
      'icon-typo-metalica': ICONS.typoMetalica,
      'icon-undo': ICONS.undo,
      'icon-redo': ICONS.redo,
      'icon-copy': ICONS.copy,
      'icon-paste': ICONS.paste,
      'icon-delete': ICONS.trash,
      'icon-tutorial': ICONS.tutorial,
      'icon-theme': ICONS.moon,
      // Paleta izquierda CAD
      'ico-cad-select': ICONS.select,
      'ico-cad-marquee': ICONS.marquee,
      'ico-cad-move': ICONS.move,
      'ico-cad-draw': ICONS.drawLine,
      'ico-cad-explode': ICONS.explode,
      'ico-cad-detail2d': ICONS.detail2d,
      // Paleta izquierda Elementos Constructivos
      'ico-layer-building': ICONS.building,
      'ico-layer-support': ICONS.support,
      'ico-layer-membrane': ICONS.membrane,
      'ico-layer-waterproofing': ICONS.waterproof,
      'ico-layer-insulation': ICONS.insulation,
      'ico-layer-battens': ICONS.battens,
      'ico-layer-covering': ICONS.tile,
      'ico-layer-drainage': ICONS.drain,
    };
    Object.entries(map).forEach(([id, svg]) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = svg;
    });
  }

  _init3DBuilder() {
    const canvas = document.getElementById('cubicad-3d-canvas');
    if (!canvas) return;

    let liveDragThrottle = 0;
    this.builder3D = new CubiCADBuilder3D(canvas, {
      onSelectItems: (itemsMeta, shiftKey) => {
        this.stateManager.setSelection(itemsMeta, shiftKey);
      },
      onCadLineDrawn: (lineObj) => {
        this.stateManager.addCadLine(lineObj);
        this.showToast(`Trazada ${lineObj.type.toUpperCase()} en el modelo 3D.`);
      },
      onStatusHint: (msg) => {
        this._setStatusBarText(msg);
      },
      onGizmoDrag: (gizmoId, pt) => {
        const now = performance.now();
        if (now - liveDragThrottle < 45) return;
        liveDragThrottle = now;

        const st = this.stateManager.state;
        if (gizmoId === 'ridge_height') {
          const halfRun = Math.max(2.0, (st.geometry.widthM || 8) / 2);
          const rise = Math.max(0.4, pt.y - this.builder3D.roofSurfaceY);
          const newSlope = Math.round(Math.max(6, Math.min(75, (rise / halfRun) * 100)));
          st.geometry.slopePct = newSlope;
          if (st.variant === 'asimetrica') {
            st.geometry.ridgeOffsetRatio = Math.max(-0.24, Math.min(0.24, pt.z / st.geometry.widthM));
          }
          this._recomputeAndSyncAll('drag');
        } else if (gizmoId === 'eave_width') {
          st.geometry.lengthM = Number(Math.max(6.0, Math.min(20.0, Math.abs(pt.x) * 2)).toFixed(1));
          st.geometry.widthM = Number(Math.max(5.5, Math.min(16.0, Math.abs(pt.z) * 2)).toFixed(1));
          this._recomputeAndSyncAll('drag');
        } else if (gizmoId === 'drain_pos') {
          st.geometry.drainPosX = Number(pt.x.toFixed(2));
          st.geometry.drainPosZ = Number(pt.z.toFixed(2));
          this._recomputeAndSyncAll('drag');
        }
      },
      onGizmoDragEnd: () => {
        // Confirmar el cambio en historial Undo/Redo
        const snap = JSON.parse(JSON.stringify(this.stateManager.state));
        this.stateManager.commit((st) => {
          Object.assign(st.geometry, snap.geometry);
        }, 'Edición interactiva 3D');
        this.showToast('Geometría actualizada en vivo (Ctrl+Z para deshacer).');
      },
      onSequenceTick: (progress, isPlaying) => {
        this._syncSequenceControlsUI(progress, isPlaying);
      },
    });
  }

  _bindGlobalNavigation() {
    // 1. Pestañas principales superiores
    document.querySelectorAll('[data-maintab]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.setMainTab(btn.dataset.maintab);
      });
    });

    // 2. Selector de 3 tipologías en barra superior
    document.querySelectorAll('[data-typology]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.closeFlyout();
        this.stateManager.switchTypology(btn.dataset.typology, false);
        if (this.activeMainTab !== 'builder') this.setMainTab('builder');
      });
    });

    // 3. Acciones CAD de barra superior (Undo, Redo, Copy, Paste, Delete)
    document.getElementById('btn-cad-undo')?.addEventListener('click', () => {
      if (this.stateManager.undo()) this.showToast('Deshecho (Ctrl+Z)');
    });
    document.getElementById('btn-cad-redo')?.addEventListener('click', () => {
      if (this.stateManager.redo()) this.showToast('Rehecho (Ctrl+Mayús+Z)');
    });
    document.getElementById('btn-cad-copy')?.addEventListener('click', () => {
      const msg = this.stateManager.copySelection();
      if (msg) this.showToast(msg);
    });
    document.getElementById('btn-cad-paste')?.addEventListener('click', () => {
      const msg = this.stateManager.pasteClipboard();
      if (msg) this.showToast(msg);
    });
    document.getElementById('btn-cad-delete')?.addEventListener('click', () => {
      if (this.stateManager.deleteSelection()) this.showToast('Elemento retirado (Ctrl+Z para deshacer)');
    });

    // 4. Botón Tutorial Guiado y Modo Claro / Oscuro
    document.getElementById('btn-open-tutorial')?.addEventListener('click', () => {
      this.openTutorialLauncherModal();
    });
    document.getElementById('btn-toggle-theme')?.addEventListener('click', () => {
      this.toggleTheme();
    });

    // 5. Paleta lateral izquierda — Herramientas CAD
    document.getElementById('tool-cad-select')?.addEventListener('click', () => {
      this.closeFlyout();
      this._activateCadTool('select');
    });
    document.getElementById('tool-cad-marquee')?.addEventListener('click', () => {
      this.closeFlyout();
      this._activateCadTool('marquee');
      this.showToast('Arrastra un rectángulo sobre el visor 3D para seleccionar una zona.');
    });
    document.getElementById('tool-cad-move')?.addEventListener('click', () => {
      this.closeFlyout();
      this._activateCadTool('move');
      this.showToast('Arrastra los nodos azules/verdes 3D para modificar pendiente, dimensiones o sumidero en vivo.');
    });
    document.getElementById('tool-cad-draw')?.addEventListener('click', (e) => {
      this._activateCadTool('draw_line');
      this.toggleFlyout('draw_line', e.currentTarget);
    });
    document.getElementById('tool-cad-explode')?.addEventListener('click', (e) => {
      this.toggleFlyout('explode', e.currentTarget);
    });
    document.getElementById('tool-cad-detail2d')?.addEventListener('click', () => {
      this.closeFlyout();
      this.toggleLiveDetail2DPanel();
    });

    // 6. Paleta lateral izquierda — Elementos Constructivos Capa a Capa (Desplegables Flyout)
    const layerBtns = [
      'building',
      'support',
      'membrane',
      'waterproofing',
      'insulation',
      'battens',
      'covering',
      'drainage',
    ];
    layerBtns.forEach((slot) => {
      const btn = document.getElementById(`tool-layer-${slot}`);
      if (!btn) return;
      btn.addEventListener('click', () => {
        this.toggleFlyout(slot, btn);
      });
    });

    // 7. Vistas de cámara rápidas sobre el visor 3D
    document.querySelectorAll('[data-cam-preset]').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (this.builder3D) this.builder3D.setCameraPreset(btn.dataset.camPreset);
      });
    });

    // 8. Plegar / desplegar Inspector derecho
    document.getElementById('btn-toggle-inspector')?.addEventListener('click', () => {
      this.inspectorOpen = !this.inspectorOpen;
      document.getElementById('builder-layout')?.classList.toggle('inspector-collapsed', !this.inspectorOpen);
      setTimeout(() => this.builder3D?.resize(), 80);
    });

    // 9. Cerrar panel flotante de Detalle 2D Vivo
    document.getElementById('btn-close-live2d')?.addEventListener('click', () => {
      this.toggleLiveDetail2DPanel(false);
    });
    document.getElementById('btn-expand-live2d')?.addEventListener('click', () => {
      this.toggleLiveDetail2DPanel(false);
      this.activeDetail2DSubTab = 'live';
      this.setMainTab('details2d');
    });

    // 10. Cerrar modales globales
    document.querySelectorAll('[data-close-modal]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const m = document.getElementById(btn.dataset.closeModal);
        if (m) m.hidden = true;
      });
    });
    document.querySelectorAll('.cc-modal-backdrop').forEach((bd) => {
      bd.addEventListener('click', (e) => {
        if (e.target === bd) bd.hidden = true;
      });
    });

    // Cerrar flyout al clicar en el visor 3D
    document.getElementById('cubicad-3d-canvas')?.addEventListener('pointerdown', () => {
      if (this.activeFlyout && this.activeFlyout !== 'draw_line') {
        this.closeFlyout();
      }
    });
  }

  _bindKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      const tag = (e.target?.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

      const ctrl = e.ctrlKey || e.metaKey;
      const key = e.key.toLowerCase();

      if (ctrl && key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (this.stateManager.undo()) this.showToast('Deshecho (Ctrl+Z)');
      } else if ((ctrl && key === 'z' && e.shiftKey) || (ctrl && key === 'y')) {
        e.preventDefault();
        if (this.stateManager.redo()) this.showToast('Rehecho (Ctrl+Mayús+Z)');
      } else if (ctrl && key === 'c') {
        e.preventDefault();
        const msg = this.stateManager.copySelection();
        if (msg) this.showToast(msg);
      } else if (ctrl && key === 'v') {
        e.preventDefault();
        const msg = this.stateManager.pasteClipboard();
        if (msg) this.showToast(msg);
      } else if (key === 'delete' || key === 'backspace') {
        if (this.stateManager.deleteSelection()) {
          e.preventDefault();
          this.showToast('Elemento retirado');
        }
      } else if (key === 'escape') {
        this.closeFlyout();
        this._activateCadTool('select');
        this.stateManager.clearSelection();
      } else if (!ctrl && key === 'v') {
        this._activateCadTool('select');
      } else if (!ctrl && key === 'm') {
        this._activateCadTool('marquee');
      } else if (!ctrl && key === 'g') {
        this._activateCadTool('move');
      } else if (!ctrl && key === 'l') {
        this._activateCadTool('draw_line');
      } else if (!ctrl && key === '2') {
        this.toggleLiveDetail2DPanel();
      }
    });
  }

  toggleTheme() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.theme);
    const ico = document.getElementById('icon-theme');
    if (ico) ico.innerHTML = this.theme === 'light' ? ICONS.moon : ICONS.sun;
    if (this.builder3D) this.builder3D.setTheme(this.theme);
    this._refreshLiveDetail2D();
  }

  _activateCadTool(tool) {
    this.stateManager.activeTool = tool;
    if (this.builder3D) this.builder3D.setTool(tool, this.stateManager.activeLineType);
    document.querySelectorAll('.cc-tool-cad').forEach((b) => {
      b.classList.toggle('active', b.dataset.cadtool === tool);
    });
    const labels = {
      select: 'Herramienta Selección (V) · Clic simple o Shift+Clic para seleccionar varias piezas.',
      marquee: 'Selección por Zona (M) · Arrastra un rectángulo sobre el modelo 3D.',
      move: 'Mover / Editar en Vivo (G) · Arrastra los tiradores azules/verdes sobre la cubierta.',
      draw_line: `Trazado CAD (${this.stateManager.activeLineType.toUpperCase()}) · Haz 2 clics sobre la cubierta para dibujar.`,
    };
    this._setStatusBarText(labels[tool] || '');
  }

  // ===========================================================================
  // PESTAÑAS PRINCIPALES DE CubiCAD
  // ===========================================================================
  setMainTab(tabId) {
    this.activeMainTab = tabId;
    this.closeFlyout();

    document.querySelectorAll('[data-maintab]').forEach((b) => {
      b.classList.toggle('active', b.dataset.maintab === tabId);
    });
    document.querySelectorAll('.cc-main-view').forEach((v) => {
      v.classList.toggle('active', v.id === `view-${tabId}`);
    });

    if (tabId === 'builder') {
      // Asegurar que el canvas 3D vuelve al contenedor del Constructor
      this._mountCanvasIn('builder-viewport-host');
      setTimeout(() => this.builder3D?.resize(), 50);
    } else if (tabId === 'manufacturers') {
      this._renderManufacturersTab();
    } else if (tabId === 'hydro') {
      this._syncHydroAndMountIframe();
    } else if (tabId === 'details2d') {
      this._renderDetails2DTab();
    } else if (tabId === 'render') {
      this._renderStudioAndSequenceTab();
    }
  }

  _mountCanvasIn(targetHostId) {
    const host = document.getElementById(targetHostId);
    const canvasWrap = document.getElementById('cubicad-canvas-shell');
    if (host && canvasWrap && canvasWrap.parentElement !== host) {
      host.prepend(canvasWrap);
    }
    setTimeout(() => this.builder3D?.resize(), 40);
  }

  // ===========================================================================
  // CÁLCULO PARAMÉTRICO, COMPATIBILIDAD Y SINCRONIZACIÓN TOTAL
  // ===========================================================================
  _recomputeAndSyncAll(reason) {
    const st = this.stateManager.state;
    const calcInput = this._buildReplanteoInput(st);

    if (st.typology === 'azotea') {
      this.currentReplanteo = BIMReplanteoCalculator.calculateFlatRoof(calcInput, this.store);
    } else {
      this.currentReplanteo = BIMReplanteoCalculator.calculateSlopedRoof(calcInput, this.store);
    }
    this.currentCompatibility = BIMCompatibilityEngine.evaluate(
      calcInput,
      this.currentReplanteo,
      this.store
    );

    // Actualizar selector de tipología activo
    document.querySelectorAll('[data-typology]').forEach((b) => {
      b.classList.toggle('active', b.dataset.typology === st.typology);
    });

    // Actualizar indicadores activos en paleta izquierda de capas
    Object.entries(st.layersEnabled).forEach(([slot, enabled]) => {
      const btn = document.getElementById(`tool-layer-${slot}`);
      if (btn) btn.classList.toggle('layer-on', Boolean(enabled));
    });

    // Actualizar estado de botones Undo / Redo / Delete
    const undoBtn = document.getElementById('btn-cad-undo');
    const redoBtn = document.getElementById('btn-cad-redo');
    const delBtn = document.getElementById('btn-cad-delete');
    if (undoBtn) undoBtn.disabled = !this.stateManager.canUndo();
    if (redoBtn) redoBtn.disabled = !this.stateManager.canRedo();
    if (delBtn) delBtn.disabled = this.stateManager.selectedIds.size === 0;

    // Reconstruir escena 3D (si no fue solo cambio de selección)
    if (this.builder3D) {
      if (reason === 'selection') {
        this.builder3D.highlightSelectedCodes(this.stateManager.selectedIds);
      } else {
        this.builder3D.rebuild(st, this.currentReplanteo, this.stateManager.selectedIds);
      }
    }

    // Actualizar HUD superior del visor, Inspector derecho, Detalle 2D Vivo y Flyout abierto
    this._renderViewportHUD();
    this._renderRightInspector();
    this._refreshLiveDetail2D();
    if (this.activeFlyout && reason !== 'selection' && reason !== 'drag') {
      this._renderFlyoutContent(this.activeFlyout);
    }
  }

  _buildReplanteoInput(st) {
    if (st.typology === 'azotea') {
      return {
        systemType: 'azotea',
        roofSubType: st.variant,
        geometry: {
          lengthM: st.geometry.lengthM,
          widthM: st.geometry.widthM,
          slopePct: st.geometry.slopePct,
          parapetTurnupMm: st.geometry.parapetTurnupMm,
          wastePct: st.geometry.wastePct,
        },
        selectedProducts: st.products,
      };
    }
    return {
      systemType: 'tejado',
      geometry: {
        lengthHorizM: st.geometry.widthM / 2 + (st.geometry.eaveOverhangM || 0.45),
        widthM: st.geometry.lengthM + (st.geometry.eaveOverhangM || 0.45) * 2,
        slopePct: st.geometry.slopePct,
        wastePct: st.geometry.wastePct,
        customBattenStepMm: st.geometry.customBattenStepMm,
      },
      selectedProducts: st.products,
    };
  }

  _renderViewportHUD() {
    const st = this.stateManager.state;
    const preset = TYPOLOGY_PRESETS[st.typology];
    const variantObj = preset.variants.find((v) => v.id === st.variant);
    const activeCount = Object.values(st.layersEnabled).filter(Boolean).length;

    const titleEl = document.getElementById('hud-building-title');
    if (titleEl) {
      titleEl.innerHTML = `<strong>${preset.buildingLabel}</strong> · ${variantObj ? variantObj.label : st.variant}`;
    }
    const pillsEl = document.getElementById('hud-live-metrics');
    if (pillsEl && this.currentReplanteo) {
      const area = this.currentReplanteo.geometry.realAreaM2 || this.currentReplanteo.geometry.flatAreaM2;
      pillsEl.innerHTML = `
        <span>Capas activas: <strong>${activeCount}/7</strong></span>
        <span>Pendiente: <strong>${st.geometry.slopePct}%</strong></span>
        <span>Superficie: <strong>${area} m²</strong></span>
        <span>Peso: <strong>${this.currentReplanteo.summary.weightPerM2Kg} kg/m²</strong></span>
      `;
    }
  }

  // ===========================================================================
  // VENTANILLAS DESPLEGABLES (FLYOUTS) DESDE CADA BOTÓN DE LA PALETA IZQUIERDA
  // ===========================================================================
  toggleFlyout(flyoutId, anchorBtn) {
    const panel = document.getElementById('cubicad-flyout');
    if (!panel) return;
    if (this.activeFlyout === flyoutId && !panel.hidden) {
      this.closeFlyout();
      return;
    }
    this.activeFlyout = flyoutId;
    document.querySelectorAll('.cc-tool-layer').forEach((b) => b.classList.remove('flyout-open'));
    if (anchorBtn) {
      anchorBtn.classList.add('flyout-open');
      const rect = anchorBtn.getBoundingClientRect();
      const topPos = Math.max(68, Math.min(window.innerHeight - 430, rect.top - 10));
      panel.style.top = `${topPos}px`;
    }
    this._renderFlyoutContent(flyoutId);
    panel.hidden = false;
  }

  closeFlyout() {
    this.activeFlyout = null;
    const panel = document.getElementById('cubicad-flyout');
    if (panel) panel.hidden = true;
    document.querySelectorAll('.cc-tool-layer').forEach((b) => b.classList.remove('flyout-open'));
  }

  _renderFlyoutContent(flyoutId) {
    const panel = document.getElementById('cubicad-flyout');
    if (!panel) return;
    const st = this.stateManager.state;

    // 1. Flyout de Trazado CAD (Cumbrera / Limatesa / Limahoya / Contorno)
    if (flyoutId === 'draw_line') {
      panel.innerHTML = `
        <div class="cc-fly-head">
          <div>
            <span class="cc-fly-kicker">HERRAMIENTA CAD (L)</span>
            <h4>Trazado de Aristas y Líneas de Cubierta</h4>
          </div>
          <button class="cc-icon-close" id="fly-close">${ICONS.close}</button>
        </div>
        <div class="cc-fly-body">
          <p class="cc-fly-desc">Elige el tipo de línea estructural y haz 2 clics sobre el plano de la cubierta en el visor 3D.</p>
          <div class="cc-fly-grid-2">
            ${[
              { id: 'cumbrera', name: 'Cumbrera', color: '#ef4444', desc: 'Arista superior divisoria' },
              { id: 'limatesa', name: 'Limatesa', color: '#0071e3', desc: 'Encuentro convexo de faldones' },
              { id: 'limahoya', name: 'Limahoya', color: '#06b6d4', desc: 'Canal cóncavo de recogida' },
              { id: 'contorno', name: 'Contorno / Alero', color: '#111827', desc: 'Línea perimetral de replanteo' },
            ]
              .map(
                (lt) => `
              <button class="cc-fly-option ${this.stateManager.activeLineType === lt.id ? 'active' : ''}" data-linetype="${lt.id}">
                <span class="cc-dot" style="background:${lt.color}"></span>
                <div><strong>${lt.name}</strong><small>${lt.desc}</small></div>
              </button>
            `
              )
              .join('')}
          </div>
          <div class="cc-fly-footer-note">
            Líneas trazadas: <strong>${st.cadLines.length}</strong> · Usa <code>Ctrl+C / Ctrl+V</code> o <code>Supr</code> al seleccionarlas.
          </div>
        </div>
      `;
      panel.querySelector('#fly-close')?.addEventListener('click', () => this.closeFlyout());
      panel.querySelectorAll('[data-linetype]').forEach((b) => {
        b.addEventListener('click', () => {
          this.stateManager.activeLineType = b.dataset.linetype;
          this._activateCadTool('draw_line');
          this._renderFlyoutContent('draw_line');
        });
      });
      return;
    }

    // 2. Flyout de Levantar / Explosionar Capas Instantáneo
    if (flyoutId === 'explode') {
      const pct = Math.round((this.builder3D?.explodeFactor || 0) * 100);
      panel.innerHTML = `
        <div class="cc-fly-head">
          <div>
            <span class="cc-fly-kicker">DESPIECE INSTANTÁNEO (E)</span>
            <h4>Levantar Capas Constructivas</h4>
          </div>
          <button class="cc-icon-close" id="fly-close">${ICONS.close}</button>
        </div>
        <div class="cc-fly-body">
          <div class="cc-fly-slider-box">
            <label>Separación vertical de capas: <strong id="fly-exp-val">${pct}%</strong></label>
            <input type="range" min="0" max="100" value="${pct}" id="fly-exp-slider" />
          </div>
          <div class="cc-fly-btn-row">
            <button class="cc-btn-sec" data-expset="0">Armada (0%)</button>
            <button class="cc-btn-sec" data-expset="50">Despiece 50%</button>
            <button class="cc-btn-sec" data-expset="100">Abierta 100%</button>
          </div>
        </div>
      `;
      panel.querySelector('#fly-close')?.addEventListener('click', () => this.closeFlyout());
      panel.querySelector('#fly-exp-slider')?.addEventListener('input', (e) => {
        this.setExplodeUI(Number(e.target.value));
      });
      panel.querySelectorAll('[data-expset]').forEach((b) => {
        b.addEventListener('click', () => this.setExplodeUI(Number(b.dataset.expset)));
      });
      return;
    }

    // 3. Flyout de Edificio Base y Geometría (Variantes de vivienda, edificio 4 plantas o pabellón)
    if (flyoutId === 'building') {
      const preset = TYPOLOGY_PRESETS[st.typology];
      panel.innerHTML = `
        <div class="cc-fly-head">
          <div>
            <span class="cc-fly-kicker">EDIFICIO BASE Y GEOMETRÍA</span>
            <h4>${preset.buildingLabel}</h4>
          </div>
          <button class="cc-icon-close" id="fly-close">${ICONS.close}</button>
        </div>
        <div class="cc-fly-body">
          <label class="cc-fly-sublabel">Variante de Geometría de Cubierta</label>
          <div class="cc-fly-stack">
            ${preset.variants
              .map(
                (v) => `
              <button class="cc-fly-option ${st.variant === v.id ? 'active' : ''}" data-variant="${v.id}">
                <div><strong>${v.label}</strong><small>${v.desc}</small></div>
              </button>
            `
              )
              .join('')}
          </div>

          <div class="cc-fly-form-2">
            <label>Longitud X (m)
              <input type="number" step="0.4" min="6" max="24" id="fly-geo-len" value="${st.geometry.lengthM}">
            </label>
            <label>Anchura Z (m)
              <input type="number" step="0.4" min="5" max="18" id="fly-geo-wid" value="${st.geometry.widthM}">
            </label>
            <label>Pendiente (%)
              <input type="number" step="1" min="1" max="70" id="fly-geo-slope" value="${st.geometry.slopePct}">
            </label>
            <label>${st.typology === 'azotea' ? 'Remonte Peto (mm)' : 'Vuelo Alero (m)'}
              <input type="number" step="${st.typology === 'azotea' ? '10' : '0.05'}" id="fly-geo-extra" value="${st.typology === 'azotea' ? st.geometry.parapetTurnupMm : st.geometry.eaveOverhangM}">
            </label>
          </div>

          <div class="cc-fly-btn-row" style="margin-top:8px;">
            <button class="cc-btn-sec" id="fly-btn-empty-roof">Vaciar Capas (Montar desde 0)</button>
            <button class="cc-btn-pri" id="fly-btn-fill-roof">Cargar Todas las Capas</button>
          </div>
        </div>
      `;
      panel.querySelector('#fly-close')?.addEventListener('click', () => this.closeFlyout());
      panel.querySelectorAll('[data-variant]').forEach((b) => {
        b.addEventListener('click', () => {
          this.stateManager.commit((s) => {
            s.variant = b.dataset.variant;
            if (s.variant === 'ajardinada') {
              s.products.waterproofingId = 'SIKA-SIKAPLAN15G';
            }
          }, 'Cambiar variante geométrica');
        });
      });
      panel.querySelector('#fly-geo-len')?.addEventListener('change', (e) => {
        this.stateManager.commit((s) => { s.geometry.lengthM = Math.max(5, Number(e.target.value) || 10); }, 'Cambiar longitud');
      });
      panel.querySelector('#fly-geo-wid')?.addEventListener('change', (e) => {
        this.stateManager.commit((s) => { s.geometry.widthM = Math.max(5, Number(e.target.value) || 8); }, 'Cambiar anchura');
      });
      panel.querySelector('#fly-geo-slope')?.addEventListener('change', (e) => {
        this.stateManager.commit((s) => { s.geometry.slopePct = Math.max(0.5, Number(e.target.value) || 20); }, 'Cambiar pendiente');
      });
      panel.querySelector('#fly-geo-extra')?.addEventListener('change', (e) => {
        this.stateManager.commit((s) => {
          if (s.typology === 'azotea') s.geometry.parapetTurnupMm = Math.max(80, Number(e.target.value) || 200);
          else s.geometry.eaveOverhangM = Math.max(0.1, Number(e.target.value) || 0.45);
        }, 'Ajustar alero/remonte');
      });
      panel.querySelector('#fly-btn-empty-roof')?.addEventListener('click', () => {
        this.stateManager.clearAllRoofLayers();
        this.showToast('Cubierta vaciada. Activa capa a capa desde la paleta izquierda.');
      });
      panel.querySelector('#fly-btn-fill-roof')?.addEventListener('click', () => {
        this.stateManager.commit((s) => {
          Object.keys(s.layersEnabled).forEach((k) => {
            s.layersEnabled[k] = k === 'waterproofing' ? s.typology === 'azotea' : true;
          });
        }, 'Activar todas las capas');
      });
      return;
    }

    // 4. Flyouts de Elementos Constructivos Capa a Capa (con subtipos + fabricante directo + ficha oficial)
    const slotDefinitions = this._getLayerFlyoutMeta(flyoutId, st);
    if (!slotDefinitions) return;

    const isOn = Boolean(st.layersEnabled[flyoutId]);
    const currentProd = this.store.getProductById(st.products[slotDefinitions.prodKey]) || slotDefinitions.candidates[0];
    const vBadge = VERIFICATION_BADGES[currentProd.verificationStatus] || VERIFICATION_BADGES.VERIFICADO_OFICIAL;

    // Agrupar por subtipo (muy útil en Cobertura / Teja: Curva, Mixta, Plana, Hormigón, Pizarra, Zinc, Panel Sándwich, Fibrocemento)
    const subTypeChipsHtml = slotDefinitions.subTypeCards
      ? `
        <label class="cc-fly-sublabel">Tipo de Material / Pieza</label>
        <div class="cc-fly-grid-2">
          ${slotDefinitions.subTypeCards
            .map(
              (sc) => `
            <button class="cc-fly-option ${currentProd.id === sc.defaultProdId || currentProd.subType === sc.subType ? 'active' : ''}" data-pick-prod="${sc.defaultProdId}">
              <span class="cc-swatch" style="background:${sc.color}"></span>
              <div><strong>${sc.label}</strong><small>${sc.brandHint}</small></div>
            </button>
          `
            )
            .join('')}
        </div>
      `
      : '';

    const variantsHtml =
      Array.isArray(currentProd.variants) && currentProd.variants.length > 0
        ? `
        <label class="cc-fly-sublabel" style="margin-top:8px;">Variante Dimensional Oficial del Fabricante
          <select id="fly-variant-sel" class="cc-select">
            ${currentProd.variants
              .map((v) => `<option value="${v.id}" ${currentProd.selectedVariantId === v.id ? 'selected' : ''}>${v.label}</option>`)
              .join('')}
          </select>
        </label>
      `
        : '';

    panel.innerHTML = `
      <div class="cc-fly-head">
        <div>
          <span class="cc-fly-kicker">ELEMENTO CONSTRUCTIVO · CAPA</span>
          <h4>${slotDefinitions.title}</h4>
        </div>
        <button class="cc-icon-close" id="fly-close">${ICONS.close}</button>
      </div>
      <div class="cc-fly-body">
        <div class="cc-fly-toggle-bar">
          <span>Estado en la cubierta 3D: <strong>${isOn ? 'Activa (Montada)' : 'No instalada'}</strong></span>
          <button class="${isOn ? 'cc-btn-danger-sm' : 'cc-btn-pri-sm'}" id="fly-toggle-layer">
            ${isOn ? 'Retirar Capa' : '+ Añadir Capa'}
          </button>
        </div>

        ${subTypeChipsHtml}

        <label class="cc-fly-sublabel" style="margin-top:8px;">Fabricante y Producto Comercial Real
          <select id="fly-prod-sel" class="cc-select">
            ${slotDefinitions.candidates
              .map((p) => `<option value="${p.id}" ${p.id === currentProd.id ? 'selected' : ''}>[${p.manufacturerName}] ${p.model}</option>`)
              .join('')}
          </select>
        </label>

        ${variantsHtml}

        <div class="cc-fly-prod-summary">
          <div class="cc-fps-top">
            <span class="cc-verif" style="color:${vBadge.color};background:${vBadge.bg}">${vBadge.icon} ${vBadge.label}</span>
            <code>${currentProd.refCode}</code>
          </div>
          <div class="cc-fps-specs">
            <span>Medidas: <strong>${currentProd.geometry.lengthNominalMm}×${currentProd.geometry.widthNominalMm}×${currentProd.geometry.thicknessMm} mm</strong></span>
            <span>Peso: <strong>${currentProd.geometry.unitWeightKg} kg/ud</strong> ${currentProd.geometry.surfaceWeightKgM2 ? `(${currentProd.geometry.surfaceWeightKgM2} kg/m²)` : ''}</span>
            <span>Pendiente mín.: <strong>${currentProd.installation.minSlopePct ?? 0}%</strong></span>
          </div>
          <div class="cc-fly-btn-row" style="margin-top:8px;">
            <button class="cc-btn-sec" id="fly-open-datasheet">${ICONS.doc} Ficha Oficial</button>
            <button class="cc-btn-sec" id="fly-go-mfg">${ICONS.catalog} Ver Fabricantes</button>
          </div>
        </div>
      </div>
    `;

    panel.querySelector('#fly-close')?.addEventListener('click', () => this.closeFlyout());
    panel.querySelector('#fly-toggle-layer')?.addEventListener('click', () => {
      this.stateManager.commit((s) => {
        s.layersEnabled[flyoutId] = !s.layersEnabled[flyoutId];
      }, `${isOn ? 'Retirar' : 'Añadir'} ${slotDefinitions.title}`);
    });

    const applyProd = (pid) => {
      this.stateManager.commit((s) => {
        s.layersEnabled[flyoutId] = true;
        s.products[slotDefinitions.prodKey] = pid;
        if (slotDefinitions.prodKey === 'coveringId') {
          s.geometry.customBattenStepMm = null;
          const cov = this.store.getProductById(pid);
          if (cov?.subType === 'pizarra_natural') s.products.fastenerId = 'ROTHOBLAAS-GANCHO-INOX90';
          else if (cov?.subType === 'zinc_junta_alzada') s.products.fastenerId = 'VMZINC-PATAS-INOX';
          else s.products.fastenerId = 'SFS-CLIP-TEJA-INOX';
        }
      }, `Asignar producto ${pid}`);
    };

    panel.querySelectorAll('[data-pick-prod]').forEach((b) => {
      b.addEventListener('click', () => applyProd(b.dataset.pickProd));
    });
    panel.querySelector('#fly-prod-sel')?.addEventListener('change', (e) => {
      applyProd(e.target.value);
    });
    panel.querySelector('#fly-variant-sel')?.addEventListener('change', (e) => {
      this.store.applyOfficialVariant(currentProd.id, e.target.value);
      this.stateManager.commit((s) => {
        s.geometry.customBattenStepMm = null;
      }, 'Cambiar variante oficial');
    });
    panel.querySelector('#fly-open-datasheet')?.addEventListener('click', () => {
      this.openProductDatasheetModal(currentProd.id);
    });
    panel.querySelector('#fly-go-mfg')?.addEventListener('click', () => {
      this.catalogFilter.familyId = currentProd.familyId;
      this.setMainTab('manufacturers');
    });
  }

  _getLayerFlyoutMeta(slot, st) {
    const isAzotea = st.typology === 'azotea';
    if (slot === 'support') {
      return {
        title: isAzotea ? 'Soporte y Formación de Pendientes' : 'Soporte Resistente / Panel Sándwich',
        prodKey: 'supportPanelId',
        candidates: this.store.getProductsByRole('support_panel'),
      };
    }
    if (slot === 'membrane') {
      return {
        title: isAzotea ? 'Geotextil Separador Antipunzonante' : 'Lámina Impermeable Transpirable',
        prodKey: isAzotea ? 'separatorBotId' : 'battenSystemId',
        candidates: isAzotea
          ? this.store.getProductsByRole('separator')
          : this.store.getProductsByRole('batten_system'),
      };
    }
    if (slot === 'waterproofing') {
      return {
        title: 'Membrana Impermeabilizante (Bituminosa / PVC)',
        prodKey: 'waterproofingId',
        candidates: this.store.getProductsByRole('waterproofing'),
        subTypeCards: [
          { subType: 'lamina_bituminosa_sbs', defaultProdId: 'DANOSA-ESTERDAN40P', label: 'Bituminosa SBS', brandHint: 'DANOSA ESTERDAN', color: '#1e293b' },
          { subType: 'membrana_sintetica_pvc', defaultProdId: 'SIKA-SIKAPLAN15G', label: 'Sintética PVC Antirraíz', brandHint: 'Sika Sikaplan G-15', color: '#64748b' },
        ],
      };
    }
    if (slot === 'insulation') {
      return {
        title: 'Aislamiento Térmico (XPS / Lana de Roca)',
        prodKey: 'insulationId',
        candidates: this.store.getProductsByRole('insulation'),
        subTypeCards: [
          { subType: 'xps_celula_cerrada', defaultProdId: 'URSA-XPS-NIIIL-60', label: 'Poliestireno Extruido XPS', brandHint: 'URSA 300 kPa', color: '#eab308' },
          { subType: 'lana_mineral_roca', defaultProdId: 'ROCKWOOL-HARDROCK-80', label: 'Lana de Roca Incombustible', brandHint: 'ROCKWOOL HardRock', color: '#8c7a52' },
        ],
      };
    }
    if (slot === 'battens') {
      if (isAzotea) {
        return {
          title: 'Plots Regulables / Lámina Drenante',
          prodKey: 'plotsId',
          candidates: [
            ...this.store.getProductsByRole('plots'),
            ...this.store.getProductsByRole('drainage_layer'),
          ],
        };
      }
      return {
        title: 'Rastreles y Contrarastreles Ventilados',
        prodKey: 'battenSystemId',
        candidates: this.store.getProductsByRole('batten_system'),
      };
    }
    if (slot === 'covering') {
      if (isAzotea) {
        if (st.variant === 'ajardinada') {
          return {
            title: 'Sistema Ajardinado Extensivo (Sustrato + Sedum)',
            prodKey: 'greenRoofId',
            candidates: this.store.getProductsByRole('green_roof_system'),
          };
        }
        return {
          title: 'Pavimento Técnico Porcelánico Exterior',
          prodKey: 'pavementId',
          candidates: this.store.getProductsByRole('pavement'),
        };
      }
      if (st.typology === 'metalica') {
        return {
          title: 'Cobertura Metálica y Ligera de Gran Luz',
          prodKey: 'coveringId',
          candidates: this.store.getProductsByRole('roof_covering').filter((p) =>
            ['zinc_junta_alzada', 'panel_sandwich_metalico', 'placa_ondulada_fibrocemento'].includes(p.subType)
          ),
          subTypeCards: [
            { subType: 'zinc_junta_alzada', defaultProdId: 'VMZINC-JUNTA-ALZADA-500', label: 'Zinc Junta Alzada', brandHint: 'VMZINC 430/530 mm', color: '#7d8892' },
            { subType: 'panel_sandwich_metalico', defaultProdId: 'KINGSPAN-KS1000RW-80', label: 'Panel Sándwich 3 Grecas', brandHint: 'Kingspan KS1000 RW', color: '#475569' },
            { subType: 'placa_ondulada_fibrocemento', defaultProdId: 'EURONIT-GRANONDA', label: 'Fibrocemento Ondulado', brandHint: 'Euronit Granonda NT', color: '#9a5440' },
          ],
        };
      }
      // Tejado Inclinado: Teja Árabe, Mixta, Plana, Hormigón, Pizarra (exactamente como pidió el usuario)
      return {
        title: 'Cobertura Inclinada (Teja y Pizarra)',
        prodKey: 'coveringId',
        candidates: this.store.getProductsByRole('roof_covering'),
        subTypeCards: [
          { subType: 'teja_curva', defaultProdId: 'BORJA-C5021', label: 'Teja Árabe / Curva', brandHint: 'Tejas Borja C-50.21', color: '#c86446' },
          { subType: 'teja_mixta', defaultProdId: 'BORJA-TB12', label: 'Teja Mixta de Encaje', brandHint: 'Borja TB-12 / Escandella', color: '#b44f34' },
          { subType: 'teja_plana', defaultProdId: 'BORJA-FLAT10', label: 'Teja Plana Cerámica', brandHint: 'Tejas Borja FLAT-10', color: '#3b3e42' },
          { subType: 'teja_hormigon', defaultProdId: 'BMI-COBERT-GREDOS', label: 'Teja de Hormigón', brandHint: 'BMI Cobert Gredos', color: '#6c5a4f' },
          { subType: 'pizarra_natural', defaultProdId: 'CUPA-4-3222', label: 'Pizarra Natural', brandHint: 'CUPA Pizarras 4', color: '#2b323b' },
          { subType: 'zinc_junta_alzada', defaultProdId: 'VMZINC-JUNTA-ALZADA-500', label: 'Zinc Junta Alzada', brandHint: 'VMZINC QUARTZ-ZINC', color: '#7d8892' },
        ],
      };
    }
    if (slot === 'drainage') {
      if (isAzotea) {
        return {
          title: 'Sumidero / Cazoleta Sifónica de Evacuación',
          prodKey: 'drainUnitId',
          candidates: this.store.getProductsByRole('drain_unit'),
        };
      }
      return {
        title: 'Canalón Perimetral, Cumbrera y Fijaciones',
        prodKey: 'gutterId',
        candidates: this.store.getProductsByRole('gutter_unit'),
      };
    }
    return null;
  }

  setExplodeUI(pct) {
    const val = Math.max(0, Math.min(100, Number(pct) || 0));
    if (this.builder3D) this.builder3D.setExplodeFactor(val / 100);
    const lbl = document.getElementById('fly-exp-val');
    if (lbl) lbl.textContent = `${val}%`;
    const sl = document.getElementById('fly-exp-slider');
    if (sl) sl.value = String(val);
    const renSl = document.getElementById('render-explode-slider');
    if (renSl) renSl.value = String(val);
  }

  // ===========================================================================
  // INSPECTOR DERECHO COMPACTO (COMPATIBILIDAD CTE + SELECCIÓN + MEDICIONES)
  // ===========================================================================
  _renderRightInspector() {
    const rep = this.currentReplanteo;
    const compat = this.currentCompatibility;
    if (!rep || !compat) return;

    // 1. Selección CAD Activa
    const selBox = document.getElementById('insp-selection-box');
    if (selBox) {
      const items = this.stateManager.selectedItemsMeta;
      if (items.length === 0) {
        selBox.innerHTML = `<div class="cc-muted-note">Ningún elemento seleccionado · Clic en 3D, <code>Shift+clic</code> o herramienta <strong>Zona (M)</strong>.</div>`;
      } else {
        const first = items[0];
        selBox.innerHTML = `
          <div class="cc-sel-card">
            <div class="cc-sel-head">
              <span class="cc-sel-badge">${items.length} seleccionado(s)</span>
              <code>${first.pieceCode || first.id}</code>
            </div>
            <strong>${first.layerName}</strong>
            <div class="cc-sel-desc">${first.roleLabel || ''}</div>
            <div class="cc-sel-dims">${first.dimensionsMm || ''}</div>
            <div class="cc-fly-btn-row" style="margin-top:6px;">
              ${first.productId ? `<button class="cc-btn-sec-xs" id="insp-open-ds">Ficha Oficial</button>` : ''}
              <button class="cc-btn-danger-xs" id="insp-del-sel">Retirar (Supr)</button>
            </div>
          </div>
        `;
        selBox.querySelector('#insp-open-ds')?.addEventListener('click', () => {
          this.openProductDatasheetModal(first.productId);
        });
        selBox.querySelector('#insp-del-sel')?.addEventListener('click', () => {
          this.stateManager.deleteSelection();
        });
      }
    }

    // 2. Semáforo de Compatibilidad Constructiva CTE
    const compBox = document.getElementById('insp-compat-box');
    if (compBox) {
      const { alerts, summary } = compat;
      const cls = summary.errCount > 0 ? 'error' : summary.warnCount > 0 ? 'warning' : 'ok';
      const title =
        summary.errCount > 0
          ? `${summary.errCount} incompatibilidad(es) detectada(s)`
          : summary.warnCount > 0
          ? `Válido con ${summary.warnCount} advertencia(s)`
          : `Compatibilidad CTE verificada (${summary.okCount} reglas)`;
      compBox.innerHTML = `
        <div class="cc-compat-pill ${cls}">${title}</div>
        <div class="cc-compat-items">
          ${alerts
            .map(
              (a) => `
            <div class="cc-compat-row ${a.severity}">
              <strong>${a.problem}</strong>
              <span>${a.affectedParam}</span>
              <small>${a.solution}</small>
            </div>
          `
            )
            .join('')}
        </div>
      `;
    }

    // 3. Mediciones y Pesos (Resumen)
    const boqBox = document.getElementById('insp-boq-box');
    if (boqBox) {
      const area = rep.geometry.realAreaM2 || rep.geometry.flatAreaM2;
      boqBox.innerHTML = `
        <div class="cc-kpi-row">
          <div><span>Superficie</span><strong>${area} m²</strong></div>
          <div><span>Peso Sistema</span><strong>${rep.summary.weightPerM2Kg} kg/m²</strong></div>
          <div><span>Transmitancia</span><strong>U=${rep.summary.uValueWmk}</strong></div>
        </div>
        <div class="cc-boq-mini-list">
          ${rep.lineItems
            .map(
              (it) => `
            <div class="cc-boq-mini-item">
              <div><strong>${it.manufacturerName}</strong><span>${it.model}</span></div>
              <div class="cc-boq-qty"><strong>${it.orderQty}</strong><small>${it.unit} · ${it.totalWeightKg} kg</small></div>
            </div>
          `
            )
            .join('')}
        </div>
        <div class="cc-export-bar">
          <button class="cc-btn-sec-xs" id="btn-exp-pdf">Informe PDF</button>
          <button class="cc-btn-sec-xs" id="btn-exp-csv">Tabla CSV</button>
          <button class="cc-btn-sec-xs" id="btn-exp-json">BIM JSON</button>
        </div>
      `;
      boqBox.querySelector('#btn-exp-pdf')?.addEventListener('click', () => this.exportTechnicalReportPDF());
      boqBox.querySelector('#btn-exp-csv')?.addEventListener('click', () => this.exportBoqCSV());
      boqBox.querySelector('#btn-exp-json')?.addEventListener('click', () => this.exportProjectJSON());
    }
  }

  // ===========================================================================
  // DETALLE CONSTRUCTIVO 2D INSTANTÁNEO (FLOTANTE Y PESTAÑA DETALLES 2D)
  // ===========================================================================
  toggleLiveDetail2DPanel(forceState = null) {
    this.liveDetail2DOpen = forceState !== null ? forceState : !this.liveDetail2DOpen;
    const drawer = document.getElementById('live-detail2d-drawer');
    const btn = document.getElementById('tool-cad-detail2d');
    if (drawer) drawer.hidden = !this.liveDetail2DOpen;
    if (btn) btn.classList.toggle('active', this.liveDetail2DOpen);
    if (this.liveDetail2DOpen) this._refreshLiveDetail2D();
  }

  _refreshLiveDetail2D() {
    if (!this.currentReplanteo) return;
    const svgMarkup = CubiCADLiveDetail2D.buildSectionSVG(
      this.stateManager.state,
      this.currentReplanteo,
      this.theme === 'dark'
    );
    const miniBox = document.getElementById('live-detail2d-svg-mini');
    if (miniBox && this.liveDetail2DOpen) miniBox.innerHTML = svgMarkup;

    const fullBox = document.getElementById('tab-detail2d-live-svg');
    if (fullBox && this.activeMainTab === 'details2d' && this.activeDetail2DSubTab === 'live') {
      fullBox.innerHTML = svgMarkup;
    }
  }

  _renderDetails2DTab() {
    const view = document.getElementById('view-details2d');
    if (!view) return;

    view.innerHTML = `
      <div class="cc-subview-bar">
        <div class="cc-segmented">
          <button class="${this.activeDetail2DSubTab === 'live' ? 'active' : ''}" id="d2d-sub-live">
            Sección 2D Viva (Mi Diseño Actual)
          </button>
          <button class="${this.activeDetail2DSubTab === 'atlas' ? 'active' : ''}" id="d2d-sub-atlas">
            Biblioteca de 10 Detalles Constructivos (Atlas UPV)
          </button>
        </div>
        <div class="cc-subview-actions">
          ${
            this.activeDetail2DSubTab === 'live'
              ? `<button class="cc-btn-pri-sm" id="btn-dl-live2d-svg">${ICONS.download} Descargar Plano SVG Vectorial</button>`
              : ''
          }
          <button class="cc-btn-sec-sm" id="btn-d2d-back-builder">Volver al Constructor 3D</button>
        </div>
      </div>

      ${
        this.activeDetail2DSubTab === 'live'
          ? `<div class="cc-live2d-stage" id="tab-detail2d-live-svg"></div>`
          : this._buildAtlasDetailsHTML()
      }
    `;

    view.querySelector('#d2d-sub-live')?.addEventListener('click', () => {
      this.activeDetail2DSubTab = 'live';
      this._renderDetails2DTab();
    });
    view.querySelector('#d2d-sub-atlas')?.addEventListener('click', () => {
      this.activeDetail2DSubTab = 'atlas';
      this._renderDetails2DTab();
    });
    view.querySelector('#btn-d2d-back-builder')?.addEventListener('click', () => {
      this.setMainTab('builder');
    });
    view.querySelector('#btn-dl-live2d-svg')?.addEventListener('click', () => {
      const svg = CubiCADLiveDetail2D.buildSectionSVG(this.stateManager.state, this.currentReplanteo, false);
      const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CubiCAD_Seccion_2D_${this.stateManager.state.typology}.svg`;
      a.click();
      URL.revokeObjectURL(url);
    });

    if (this.activeDetail2DSubTab === 'live') {
      this._refreshLiveDetail2D();
    } else {
      view.querySelectorAll('[data-atlas-id]').forEach((b) => {
        b.addEventListener('click', () => {
          this.activeAtlasId = b.dataset.atlasId;
          this._renderDetails2DTab();
        });
      });
    }
  }

  _buildAtlasDetailsHTML() {
    const active = ATLAS_DETAILS_META.find((d) => d.id === this.activeAtlasId) || ATLAS_DETAILS_META[0];
    const mData = this.atlasManifest?.[active.id];

    return `
      <div class="cc-atlas-grid">
        <div class="cc-atlas-sidebar">
          ${ATLAS_DETAILS_META.map(
            (d) => `
            <button class="cc-atlas-item ${d.id === active.id ? 'active' : ''}" data-atlas-id="${d.id}">
              <span>${d.code}</span>
              <strong>${d.name}</strong>
            </button>
          `
          ).join('')}
        </div>
        <div class="cc-atlas-viewer">
          <div class="cc-atlas-head">
            <div>
              <strong>${mData ? mData.title : active.name}</strong>
              <small>${mData ? mData.subtitle : 'Plano técnico 2D milimétrico escala 1:5 · ETSIE UPV'}</small>
            </div>
            <div class="cc-subview-actions">
              <a class="cc-btn-sec-sm" href="${active.pdf}" download>PDF A3</a>
              <a class="cc-btn-sec-sm" href="${active.glb}" download>Modelo .GLB</a>
            </div>
          </div>
          <div class="cc-atlas-split">
            <div class="cc-atlas-pane"><img src="${active.svg}" alt="Plano 2D ${active.name}" /></div>
            <div class="cc-atlas-pane dark"><img src="${active.render}" alt="Render 3D ${active.name}" /></div>
          </div>
        </div>
      </div>
    `;
  }

  // ===========================================================================
  // PESTAÑA FABRICANTES (CATÁLOGO BIM COMPLETO + COMPARADOR + FICHAS OFICIALES)
  // ===========================================================================
  _renderManufacturersTab() {
    const view = document.getElementById('view-manufacturers');
    if (!view) return;
    const allProds = this.store.getAllProducts();
    const filtered = allProds.filter((p) => {
      if (this.catalogFilter.familyId !== 'ALL' && p.familyId !== this.catalogFilter.familyId) return false;
      if (this.catalogFilter.manufacturerId !== 'ALL' && p.manufacturerId !== this.catalogFilter.manufacturerId) return false;
      if (this.catalogFilter.search.trim()) {
        const q = this.catalogFilter.search.toLowerCase();
        return (
          p.model.toLowerCase().includes(q) ||
          p.manufacturerName.toLowerCase().includes(q) ||
          p.refCode.toLowerCase().includes(q) ||
          p.applicationSystem.toLowerCase().includes(q)
        );
      }
      return true;
    });

    view.innerHTML = `
      <div class="cc-mfg-wrap">
        <div class="cc-mfg-header">
          <div>
            <h2>Biblioteca Oficial de Fabricantes y Materiales BIM</h2>
            <p>Selecciona cualquier producto comercial verificado para cargarlo instantáneamente en el Constructor 3D o consultar su Ficha Técnica Oficial.</p>
          </div>
          <div class="cc-subview-actions">
            <button class="cc-btn-sec-sm" id="mfg-open-comparator">${ICONS.compare} Comparador (${this.compareQueue.length})</button>
            <button class="cc-btn-pri-sm" id="mfg-back-builder">Volver al Constructor</button>
          </div>
        </div>

        <div class="cc-mfg-filters">
          <input type="search" id="mfg-search" placeholder="Buscar fabricante, modelo, código o norma UNE-EN..." value="${this.catalogFilter.search}" />
          <select id="mfg-family">
            <option value="ALL">Todas las Familias (A–L · ${allProds.length} productos)</option>
            ${BIM_FAMILIES.map(
              (f) => `<option value="${f.id}" ${this.catalogFilter.familyId === f.id ? 'selected' : ''}>${f.name}</option>`
            ).join('')}
          </select>
          <select id="mfg-brand">
            <option value="ALL">Todos los Fabricantes (${Object.keys(BIM_MANUFACTURERS).length})</option>
            ${Object.values(BIM_MANUFACTURERS)
              .map(
                (m) => `<option value="${m.id}" ${this.catalogFilter.manufacturerId === m.id ? 'selected' : ''}>${m.name}</option>`
              )
              .join('')}
          </select>
        </div>

        <div class="cc-mfg-chips">
          ${Object.values(BIM_MANUFACTURERS)
            .map((m) => `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="cc-mfg-chip">${m.name} ↗</a>`)
            .join('')}
        </div>

        <div class="cc-mfg-grid">
          ${filtered
            .map((p) => {
              const vBadge = VERIFICATION_BADGES[p.verificationStatus] || VERIFICATION_BADGES.VERIFICADO_OFICIAL;
              const inCmp = this.compareQueue.includes(p.id);
              return `
                <article class="cc-prod-card">
                  <div class="cc-pc-top">
                    <span class="cc-pc-brand">${p.manufacturerName}</span>
                    <span class="cc-verif" style="color:${vBadge.color};background:${vBadge.bg}">${vBadge.icon} ${vBadge.label}</span>
                  </div>
                  <h3>${p.model}</h3>
                  <div class="cc-pc-meta">Ref: <code>${p.refCode}</code> · ${p.versionDoc}</div>
                  <div class="cc-pc-specs">
                    <span>${p.geometry.lengthNominalMm}×${p.geometry.widthNominalMm}×${p.geometry.thicknessMm} mm</span>
                    <span>${p.geometry.unitWeightKg} kg/ud</span>
                    <span>Pend. mín. ${p.installation.minSlopePct ?? 0}%</span>
                  </div>
                  <div class="cc-pc-actions">
                    <button class="cc-btn-sec-xs" data-ds="${p.id}">Ficha Oficial</button>
                    <button class="cc-btn-sec-xs ${inCmp ? 'active' : ''}" data-cmp="${p.id}">${inCmp ? 'En comparador' : 'Comparar'}</button>
                    <button class="cc-btn-pri-xs" data-load-prod="${p.id}">Cargar al 3D</button>
                  </div>
                </article>
              `;
            })
            .join('')}
        </div>
      </div>
    `;

    view.querySelector('#mfg-search')?.addEventListener('input', (e) => {
      this.catalogFilter.search = e.target.value;
      this._renderManufacturersTab();
      const inp = view.querySelector('#mfg-search');
      if (inp) { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); }
    });
    view.querySelector('#mfg-family')?.addEventListener('change', (e) => {
      this.catalogFilter.familyId = e.target.value;
      this._renderManufacturersTab();
    });
    view.querySelector('#mfg-brand')?.addEventListener('change', (e) => {
      this.catalogFilter.manufacturerId = e.target.value;
      this._renderManufacturersTab();
    });
    view.querySelector('#mfg-open-comparator')?.addEventListener('click', () => this.openComparatorModal());
    view.querySelector('#mfg-back-builder')?.addEventListener('click', () => this.setMainTab('builder'));

    view.querySelectorAll('[data-ds]').forEach((b) => {
      b.addEventListener('click', () => this.openProductDatasheetModal(b.dataset.ds));
    });
    view.querySelectorAll('[data-cmp]').forEach((b) => {
      b.addEventListener('click', () => {
        const id = b.dataset.cmp;
        if (this.compareQueue.includes(id)) this.compareQueue = this.compareQueue.filter((x) => x !== id);
        else {
          if (this.compareQueue.length >= 4) this.compareQueue.shift();
          this.compareQueue.push(id);
        }
        this._renderManufacturersTab();
      });
    });
    view.querySelectorAll('[data-load-prod]').forEach((b) => {
      b.addEventListener('click', () => this._loadCatalogProductIntoBuilder(b.dataset.loadProd));
    });
  }

  _loadCatalogProductIntoBuilder(productId) {
    const p = this.store.getProductById(productId);
    if (!p) return;
    const roleMap = {
      roof_covering: { typo: ['zinc_junta_alzada', 'panel_sandwich_metalico', 'placa_ondulada_fibrocemento'].includes(p.subType) ? 'metalica' : 'tejado', key: 'coveringId', layer: 'covering' },
      support_panel: { typo: 'tejado', key: 'supportPanelId', layer: 'support' },
      batten_system: { typo: 'tejado', key: 'battenSystemId', layer: 'battens' },
      gutter_unit: { typo: 'tejado', key: 'gutterId', layer: 'drainage' },
      waterproofing: { typo: 'azotea', key: 'waterproofingId', layer: 'waterproofing' },
      insulation: { typo: 'azotea', key: 'insulationId', layer: 'insulation' },
      separator: { typo: 'azotea', key: 'separatorBotId', layer: 'membrane' },
      plots: { typo: 'azotea', key: 'plotsId', layer: 'battens' },
      pavement: { typo: 'azotea', key: 'pavementId', layer: 'covering' },
      green_roof_system: { typo: 'azotea', key: 'greenRoofId', layer: 'covering' },
      drain_unit: { typo: 'azotea', key: 'drainUnitId', layer: 'drainage' },
    };
    const m = roleMap[p.role];
    if (m) {
      if (this.stateManager.state.typology !== m.typo) {
        this.stateManager.switchTypology(m.typo, false);
      }
      this.stateManager.commit((s) => {
        s.products[m.key] = p.id;
        s.layersEnabled[m.layer] = true;
        if (p.role === 'green_roof_system') s.variant = 'ajardinada';
      }, `Cargar ${p.model}`);
    }
    this.setMainTab('builder');
    this.showToast(`Cargado ${p.manufacturerName} · ${p.model} en el Constructor 3D.`);
  }

  // ===========================================================================
  // PESTAÑA SIMULADOR DE AGUA (HYDRO 3D SINCRONIZADO)
  // ===========================================================================
  _syncHydroAndMountIframe() {
    const st = this.stateManager.state;
    const flatRep = BIMReplanteoCalculator.calculateFlatRoof(
      {
        systemType: 'azotea',
        roofSubType: st.typology === 'azotea' ? st.variant : 'invertida_plots',
        geometry: {
          lengthM: st.geometry.lengthM,
          widthM: st.geometry.widthM,
          slopePct: st.typology === 'azotea' ? st.geometry.slopePct : 2.0,
          parapetTurnupMm: st.geometry.parapetTurnupMm || 200,
          wastePct: 5,
        },
        selectedProducts: st.products,
      },
      this.store
    );
    const payload = {
      syncedAt: new Date().toISOString(),
      roofSubType: st.typology === 'azotea' ? st.variant : 'invertida_plots',
      geometry: flatRep.geometry,
      products: {
        waterproofing: { id: flatRep.products.waterproofing.id, brand: flatRep.products.waterproofing.brand, model: flatRep.products.waterproofing.model },
        insulation: { id: flatRep.products.insulation.id, brand: flatRep.products.insulation.brand, model: flatRep.products.insulation.model, thicknessMm: flatRep.products.insulation.geometry.thicknessMm },
        plots: { id: flatRep.products.plots.id, brand: flatRep.products.plots.brand, model: flatRep.products.plots.model, heightMm: flatRep.products.plots.geometry.thicknessMm, jointWidthMm: flatRep.products.plots.geometry.jointTabThicknessMm || 4 },
        pavement: { id: flatRep.products.pavement.id, brand: flatRep.products.pavement.brand, model: flatRep.products.pavement.model, lengthMm: flatRep.products.pavement.geometry.lengthNominalMm, widthMm: flatRep.products.pavement.geometry.widthNominalMm, thicknessMm: flatRep.products.pavement.geometry.thicknessMm },
        drainUnit: { id: flatRep.products.drainUnit.id, brand: flatRep.products.drainUnit.brand, model: flatRep.products.drainUnit.model, outletDiameterMm: flatRep.products.drainUnit.geometry.outletDiameterMm, hydraulicCapacityLs: flatRep.products.drainUnit.geometry.hydraulicCapacityLs },
      },
    };
    try {
      localStorage.setItem('ETSIE_C2_ACTIVE_BIM_HYDRO_SPEC', JSON.stringify(payload));
    } catch (e) {
      console.warn(e);
    }

    const hydroUrl = window.CUBICAD_HYDRO_URL || './hydro3d.html?bimSync=1';
    const frame = document.getElementById('hydro-embed-frame');
    const extLink = document.getElementById('hydro-open-external');
    if (extLink) extLink.href = hydroUrl;
    if (frame && frame.dataset.loadedUrl !== hydroUrl) {
      frame.src = hydroUrl;
      frame.dataset.loadedUrl = hydroUrl;
    }
  }

  // ===========================================================================
  // PESTAÑA RENDER Y SECUENCIA (GENERADOR DE SECUENCIA EN VIVO + CAPTURAS HD)
  // ===========================================================================
  _renderStudioAndSequenceTab() {
    const host = document.getElementById('render-viewport-host');
    if (host) this._mountCanvasIn('render-viewport-host');

    const ctrl = document.getElementById('render-sequence-controls');
    if (!ctrl || ctrl.dataset.bound) return;
    ctrl.dataset.bound = 'true';

    document.getElementById('btn-seq-play')?.addEventListener('click', () => {
      this.startLiveSequencePlayback();
    });
    document.getElementById('render-seq-slider')?.addEventListener('input', (e) => {
      const p = Number(e.target.value) / 100;
      if (this.builder3D) {
        this.builder3D.isPlayingSequence = false;
        this.builder3D.setAssemblyProgress(p);
        this._syncSequenceControlsUI(p, false);
      }
    });
    document.getElementById('render-explode-slider')?.addEventListener('input', (e) => {
      this.setExplodeUI(Number(e.target.value));
    });
    document.getElementById('btn-capture-render-png')?.addEventListener('click', () => {
      if (!this.builder3D) return;
      const dataUrl = this.builder3D.captureHighResPNG();
      this.capturedRenders.unshift({
        url: dataUrl,
        label: `Render CubiCAD · ${TYPOLOGY_PRESETS[this.stateManager.state.typology].name} (${new Date().toLocaleTimeString('es-ES')})`,
      });
      this._renderCapturedGallery();
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `CubiCAD_Render_${this.stateManager.state.typology}_${Date.now()}.png`;
      a.click();
      this.showToast('Render PNG de alta resolución capturado y descargado.');
    });
    document.getElementById('btn-record-seq-webm')?.addEventListener('click', async () => {
      if (!this.builder3D) return;
      const btn = document.getElementById('btn-record-seq-webm');
      try {
        btn.disabled = true;
        btn.textContent = 'Grabando secuencia (6 s)...';
        const url = await this.builder3D.recordSequenceVideo(6000, (p) => {
          this._syncSequenceControlsUI(p, true);
        });
        const a = document.createElement('a');
        a.href = url;
        a.download = `CubiCAD_Secuencia_Montaje_${this.stateManager.state.typology}.webm`;
        a.click();
        this.showToast('Vídeo de secuencia de montaje (.webm) generado y descargado.');
      } catch (err) {
        this.showToast(err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `${ICONS.video} Grabar Vídeo Secuencia (.webm)`;
      }
    });

    this._renderCapturedGallery();
  }

  startLiveSequencePlayback() {
    if (!this.builder3D) return;
    const playing = this.builder3D.toggleSequencePlay();
    this._syncSequenceControlsUI(this.builder3D.assemblyProgress, playing);
  }

  _syncSequenceControlsUI(progress, isPlaying) {
    const pct = Math.round(progress * 100);
    const sl = document.getElementById('render-seq-slider');
    const lbl = document.getElementById('render-seq-pct');
    const btn = document.getElementById('btn-seq-play');
    if (sl) sl.value = String(pct);
    if (lbl) lbl.textContent = `${pct}%`;
    if (btn) btn.innerHTML = isPlaying ? `${ICONS.pause} Pausar Secuencia` : `${ICONS.play} Reproducir Secuencia`;
  }

  _renderCapturedGallery() {
    const gal = document.getElementById('render-captured-gallery');
    if (!gal) return;
    const refRenders = [
      { url: 'renders/detalle1_hero.png', label: 'Referencia Cycles PBR · Azotea Convencional' },
      { url: 'renders/detalle4_hero.png', label: 'Referencia Cycles PBR · Invertida sobre Plots' },
      { url: 'renders/detalle5_hero.png', label: 'Referencia Cycles PBR · Tejado Teja Curva' },
      { url: 'renders/detalle8_hero.png', label: 'Referencia Cycles PBR · Pizarra Natural' },
      { url: 'renders/detalle9_hero.png', label: 'Referencia Cycles PBR · Zinc Junta Alzada' },
    ];
    const items = [...this.capturedRenders, ...refRenders];
    gal.innerHTML = items
      .map(
        (it) => `
        <div class="cc-gal-card">
          <img src="${it.url}" alt="${it.label}" />
          <span>${it.label}</span>
        </div>
      `
      )
      .join('');
  }

  // ===========================================================================
  // TUTORIAL INTERACTIVO DE PRIMER USO (3 EJEMPLOS DESDE CERO)
  // ===========================================================================
  openTutorialLauncherModal() {
    const modal = document.getElementById('cc-tutorial-modal');
    const body = document.getElementById('cc-tutorial-modal-body');
    if (!modal || !body) return;

    body.innerHTML = `
      <p class="cc-tut-intro">
        Bienvenido a <strong>CubiCAD</strong>. Selecciona una tipología para seguir un recorrido guiado desde cero (edificio base → montaje capa a capa → Detalle 2D en vivo → secuencia de montaje y render).
      </p>
      <div class="cc-tut-cards">
        ${Object.values(CUBICAD_TUTORIALS)
          .map(
            (t) => `
          <div class="cc-tut-card">
            <span class="cc-tut-badge">${t.badge}</span>
            <h4>${t.title}</h4>
            <p>${t.subtitle}</p>
            <button class="cc-btn-pri" data-start-tut="${t.id}">Iniciar Tutorial Guiado →</button>
          </div>
        `
          )
          .join('')}
      </div>
      <div class="cc-tut-skip-row">
        <button class="cc-btn-sec" id="tut-skip-btn">Entrar directamente al Constructor libre</button>
      </div>
    `;

    body.querySelectorAll('[data-start-tut]').forEach((b) => {
      b.addEventListener('click', () => {
        localStorage.setItem('CUBICAD_ONBOARDING_SEEN_V1', '1');
        modal.hidden = true;
        this.startTutorial(b.dataset.startTut);
      });
    });
    body.querySelector('#tut-skip-btn')?.addEventListener('click', () => {
      localStorage.setItem('CUBICAD_ONBOARDING_SEEN_V1', '1');
      modal.hidden = true;
    });
    modal.hidden = false;
  }

  startTutorial(tutorialId) {
    this.activeTutorialId = tutorialId;
    this.activeTutorialStep = 0;
    this._renderActiveTutorialCoach();
  }

  _clearTutorialHighlight() {
    document.querySelectorAll('.cc-tut-pulse').forEach((el) => el.classList.remove('cc-tut-pulse'));
  }

  _renderActiveTutorialCoach() {
    this._clearTutorialHighlight();
    const box = document.getElementById('cc-tutorial-coach');
    if (!box) return;

    const tut = CUBICAD_TUTORIALS[this.activeTutorialId];
    if (!tut) {
      box.hidden = true;
      return;
    }

    const step = tut.steps[this.activeTutorialStep];
    const total = tut.steps.length;
    if (step.highlightSelector) {
      const target = document.querySelector(step.highlightSelector);
      if (target) target.classList.add('cc-tut-pulse');
    }

    box.innerHTML = `
      <div class="cc-coach-head">
        <span>${tut.badge} · PASO ${this.activeTutorialStep + 1} / ${total}</span>
        <button class="cc-icon-close" id="coach-close">${ICONS.close}</button>
      </div>
      <h4>${step.title}</h4>
      <p>${step.instruction}</p>
      <div class="cc-coach-actions">
        <button class="cc-btn-pri-sm" id="coach-exec">${step.actionLabel}</button>
        <div class="cc-coach-nav">
          <button class="cc-btn-sec-xs" id="coach-prev" ${this.activeTutorialStep === 0 ? 'disabled' : ''}>← Anterior</button>
          <button class="cc-btn-sec-xs" id="coach-next">${this.activeTutorialStep === total - 1 ? 'Finalizar ✓' : 'Siguiente →'}</button>
        </div>
      </div>
    `;
    box.hidden = false;

    box.querySelector('#coach-close')?.addEventListener('click', () => {
      this.activeTutorialId = null;
      this._clearTutorialHighlight();
      box.hidden = true;
    });
    box.querySelector('#coach-exec')?.addEventListener('click', () => {
      step.execute(this);
      if (this.activeTutorialStep < total - 1) {
        this.activeTutorialStep++;
        this._renderActiveTutorialCoach();
      } else {
        this.activeTutorialId = null;
        this._clearTutorialHighlight();
        box.hidden = true;
        this.showToast('¡Tutorial completado! Ya dominas el flujo completo de CubiCAD.');
      }
    });
    box.querySelector('#coach-prev')?.addEventListener('click', () => {
      if (this.activeTutorialStep > 0) {
        this.activeTutorialStep--;
        this._renderActiveTutorialCoach();
      }
    });
    box.querySelector('#coach-next')?.addEventListener('click', () => {
      if (this.activeTutorialStep < total - 1) {
        this.activeTutorialStep++;
        this._renderActiveTutorialCoach();
      } else {
        this.activeTutorialId = null;
        this._clearTutorialHighlight();
        box.hidden = true;
      }
    });
  }

  // ===========================================================================
  // MODALES DE FICHA TÉCNICA DIGITAL OFICIAL Y COMPARADOR
  // ===========================================================================
  openProductDatasheetModal(productId) {
    const p = this.store.getProductById(productId);
    if (!p) return;
    const modal = document.getElementById('cc-datasheet-modal');
    const titleEl = document.getElementById('cc-ds-title');
    const bodyEl = document.getElementById('cc-ds-body');
    if (!modal || !bodyEl) return;

    const vBadge = VERIFICATION_BADGES[p.verificationStatus] || VERIFICATION_BADGES.VERIFICADO_OFICIAL;
    titleEl.innerHTML = `<span class="cc-verif" style="color:${vBadge.color};background:${vBadge.bg}">${vBadge.icon} ${vBadge.label}</span> <strong>${p.manufacturerName} · ${p.model}</strong>`;

    bodyEl.innerHTML = `
      <div class="cc-ds-grid">
        <div class="cc-ds-sec">
          <h5>Identificación y Trazabilidad</h5>
          <table>
            <tr><th>Fabricante</th><td><strong>${p.manufacturerName}</strong> (${p.brand})</td></tr>
            <tr><th>Referencia</th><td><code>${p.refCode}</code></td></tr>
            <tr><th>Sistema</th><td>${p.applicationSystem}</td></tr>
            <tr><th>Documentación</th><td>${p.versionDoc} (${p.revisionDate})</td></tr>
          </table>
        </div>
        <div class="cc-ds-sec">
          <h5>Geometría Oficial</h5>
          <table>
            <tr><th>Nominal</th><td><strong>${p.geometry.lengthNominalMm} × ${p.geometry.widthNominalMm} × ${p.geometry.thicknessMm} mm</strong></td></tr>
            <tr><th>Dimensiones útiles</th><td>${p.geometry.usefulLengthNominalMm || '-'} × ${p.geometry.usefulWidthMm || '-'} mm</td></tr>
            <tr><th>Solapes</th><td>Long. ${p.geometry.overlapLongMinMm ?? '-'} mm · Transv. ${p.geometry.overlapTransMm ?? '-'} mm</td></tr>
            <tr><th>Peso</th><td><strong>${p.geometry.unitWeightKg} kg/ud</strong> ${p.geometry.surfaceWeightKgM2 ? `(${p.geometry.surfaceWeightKgM2} kg/m²)` : ''}</td></tr>
          </table>
        </div>
        <div class="cc-ds-sec">
          <h5>Prestaciones Técnicas</h5>
          <table>
            <tr><th>Material</th><td>${p.technicalSpecs.material}</td></tr>
            <tr><th>Mecánica</th><td>${p.technicalSpecs.mechanicalStrength || '-'}</td></tr>
            <tr><th>Fuego</th><td>${p.technicalSpecs.fireReaction || '-'}</td></tr>
            <tr><th>Normativa</th><td>${(p.technicalSpecs.standards || []).join(', ')}</td></tr>
          </table>
        </div>
        <div class="cc-ds-sec">
          <h5>Condiciones de Montaje</h5>
          <table>
            <tr><th>Pendiente mín.</th><td><strong>${p.installation.minSlopePct ?? 0}%</strong> (Recomendada ${p.installation.recommendedSlopePct ?? '-'}%)</td></tr>
            <tr><th>Paso rastrel</th><td>${p.installation.battenDistanceMinMm ? `${p.installation.battenDistanceMinMm}–${p.installation.battenDistanceMaxMm} mm` : 'Apoyo continuo'}</td></tr>
            <tr><th>Fijación</th><td>${p.installation.fixingSystem}</td></tr>
          </table>
        </div>
      </div>
      <div class="cc-ds-links">
        <a href="${p.documentation.productUrl}" target="_blank" rel="noopener noreferrer" class="cc-btn-pri-sm">Web Oficial (${p.manufacturerName}) ↗</a>
        <a href="${p.documentation.datasheetPdfUrl}" target="_blank" rel="noopener noreferrer" class="cc-btn-sec-sm">Ficha Técnica / DoP ↗</a>
      </div>
    `;
    modal.hidden = false;
  }

  openComparatorModal() {
    const modal = document.getElementById('cc-comparator-modal');
    const bodyEl = document.getElementById('cc-comp-body');
    if (!modal || !bodyEl) return;

    const prods = this.compareQueue.map((id) => this.store.getProductById(id)).filter(Boolean);
    bodyEl.innerHTML = `
      <div class="cc-comp-wrap">
        <table class="cc-comp-table">
          <thead>
            <tr>
              <th>Parámetro Técnico</th>
              ${prods.map((p) => `<th><span>${p.manufacturerName}</span><strong>${p.model}</strong></th>`).join('')}
            </tr>
          </thead>
          <tbody>
            <tr><th>Referencia</th>${prods.map((p) => `<td><code>${p.refCode}</code></td>`).join('')}</tr>
            <tr><th>Dimensiones</th>${prods.map((p) => `<td>${p.geometry.lengthNominalMm}×${p.geometry.widthNominalMm}×${p.geometry.thicknessMm} mm</td>`).join('')}</tr>
            <tr><th>Peso</th>${prods.map((p) => `<td>${p.geometry.unitWeightKg} kg/ud (${p.geometry.surfaceWeightKgM2 || '-'} kg/m²)</td>`).join('')}</tr>
            <tr><th>Pendiente mín.</th>${prods.map((p) => `<td><strong>${p.installation.minSlopePct ?? 0}%</strong></td>`).join('')}</tr>
            <tr><th>Paso rastrel</th>${prods.map((p) => `<td>${p.installation.battenDistanceMinMm ? `${p.installation.battenDistanceMinMm}–${p.installation.battenDistanceMaxMm} mm` : 'Continuo'}</td>`).join('')}</tr>
            <tr><th>Normativa</th>${prods.map((p) => `<td>${(p.technicalSpecs.standards || []).join(', ')}</td>`).join('')}</tr>
          </tbody>
        </table>
      </div>
    `;
    modal.hidden = false;
  }

  // ===========================================================================
  // EXPORTADORES (INFORME PDF, CSV EXCEL, BIM JSON) Y FEEDBACK VISUAL
  // ===========================================================================
  exportTechnicalReportPDF() {
    const rep = this.currentReplanteo;
    const compat = this.currentCompatibility;
    if (!rep || !compat) return;
    const win = window.open('', '_blank');
    if (!win) return;
    const svg2d = CubiCADLiveDetail2D.buildSectionSVG(this.stateManager.state, rep, false);

    win.document.write(`<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Informe Técnico CubiCAD</title>
      <style>body{font-family:-apple-system,Segoe UI,sans-serif;color:#111827;margin:28px;}h1{margin:0;font-size:20px;}table{width:100%;border-collapse:collapse;font-size:12px;margin-top:12px;}th,td{border:1px solid #cbd5e1;padding:7px;text-align:left;}th{background:#f1f5f9;}@media print{.no-print{display:none;}}</style></head><body>
      <div class="no-print" style="margin-bottom:14px;"><button onclick="window.print()" style="padding:8px 16px;background:#0071e3;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:700;">Imprimir / Guardar PDF</button></div>
      <h1>CubiCAD · Informe Técnico y Mediciones de Cubierta (ETSIE · UPV)</h1>
      <p>Tipología: <strong>${TYPOLOGY_PRESETS[this.stateManager.state.typology].name}</strong> (${this.stateManager.state.variant}) · Peso: <strong>${rep.summary.weightPerM2Kg} kg/m²</strong> · U = <strong>${rep.summary.uValueWmk} W/m²K</strong></p>
      <div style="border:1px solid #cbd5e1;border-radius:8px;overflow:hidden;margin:14px 0;">${svg2d}</div>
      <table><thead><tr><th>Capa</th><th>Fabricante y Modelo</th><th>Dimensiones</th><th>Pedido</th><th>Peso</th></tr></thead><tbody>
      ${rep.lineItems.map((it) => `<tr><td>${it.roleLabel}</td><td><strong>${it.manufacturerName}</strong> · ${it.model}</td><td>${it.dimensionsStr}</td><td><strong>${it.orderQty}</strong> ${it.unit}</td><td>${it.totalWeightKg} kg</td></tr>`).join('')}
      </tbody></table></body></html>`);
    win.document.close();
  }

  exportBoqCSV() {
    if (!this.currentReplanteo) return;
    const lines = ['Capa;Fabricante;Modelo;Referencia;Dimensiones;Unidad;Montaje;Pedido;Peso_kg'];
    this.currentReplanteo.lineItems.forEach((it) => {
      lines.push(`"${it.roleLabel}";"${it.manufacturerName}";"${it.model}";"${it.refCode}";"${it.dimensionsStr}";"${it.unit}";${it.assemblyQty};"${it.orderQty}";${it.totalWeightKg}`);
    });
    const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CubiCAD_Mediciones_${this.stateManager.state.typology}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  exportProjectJSON() {
    const data = {
      software: 'CubiCAD · Constructor CAD/BIM de Cubiertas',
      exportedAt: new Date().toISOString(),
      state: this.stateManager.state,
      replanteo: this.currentReplanteo,
      compatibility: this.currentCompatibility,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Proyecto_CubiCAD_${this.stateManager.state.typology}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  _setStatusBarText(text) {
    const el = document.getElementById('cubicad-status-text');
    if (el) el.textContent = text;
  }

  showToast(msg) {
    const t = document.getElementById('cubicad-toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('visible');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => t.classList.remove('visible'), 2800);
  }
}

window.cubicadApp = new CubiCADApp();
