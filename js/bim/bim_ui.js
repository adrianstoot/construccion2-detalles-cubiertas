/**
 * =============================================================================
 * ROOFLAB ETSIE · CONSTRUCCIÓN II (UPV)
 * CONTROLADOR DE INTERFAZ DE LA BIBLIOTECA BIM DE PRODUCTOS REALES
 * =============================================================================
 * Integra todas las funcionalidades del Master Prompt dentro de la aplicación:
 * 1. Selector visual jerárquico: MATERIALES -> FAMILIA -> FABRICANTE -> MODELO -> CONFIGURACIÓN
 * 2. Ensamblador 3D Pieza a Pieza (DEMO A: Tejado) y Capa a Capa (DEMO B: Azotea)
 * 3. Plano CAD 2D de Replanteo sincronizado con el modelo 3D
 * 4. Ficha Técnica Digital Oficial (Sección 3.1 a 3.5) + Variantes Oficiales
 * 5. Comparador Técnico de Productos Comerciales
 * 6. Motor de Compatibilidad Constructiva en tiempo real
 * 7. Administrador del Catálogo con Historial de Versiones (Sección 14)
 * 8. Generador de Documentación (Informe PDF/Impresión, CSV Excel y JSON BIM)
 * 9. Vinculación con los 10 Detalles Constructivos existentes y con HYDRO 3D
 */

import {
  BIM_FAMILIES,
  BIM_MANUFACTURERS,
  BIM_DEMOS,
  VERIFICATION_BADGES,
  BIMCatalogStore,
} from './catalog_db.js';
import {
  BIMReplanteoCalculator,
  BIMCompatibilityEngine,
  DEFAULT_DETAIL_PRODUCT_LINKS,
} from './compatibility_replanteo.js';
import { BIMAssembler3D, BIMReplanteo2DRenderer } from './bim_assembler_3d.js';

export class BIMLibraryController {
  constructor() {
    this.store = new BIMCatalogStore();
    this.activeDemoId = 'demoA_tejado';
    this.demoConfigs = JSON.parse(JSON.stringify(BIM_DEMOS));
    this.detailProductLinks = this._loadDetailProductLinks();

    this.assembler3D = null;
    this.currentReplanteo = null;
    this.currentCompatibility = null;
    this.selectedPieceMeta = null;

    // Estado del Explorador de Catálogo y Comparador
    this.catalogFilter = {
      familyId: 'ALL',
      manufacturerId: 'ALL',
      search: '',
      maxMinSlope: 100,
    };
    this.compareQueue = ['BORJA-C5021', 'BORJA-TB12', 'BORJA-FLAT10'];

    this._injectModals();
  }

  _loadDetailProductLinks() {
    try {
      const saved = localStorage.getItem('ETSIE_C2_DETAIL_BIM_LINKS_V1');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn(e);
    }
    return JSON.parse(JSON.stringify(DEFAULT_DETAIL_PRODUCT_LINKS));
  }

  _saveDetailProductLinks() {
    try {
      localStorage.setItem('ETSIE_C2_DETAIL_BIM_LINKS_V1', JSON.stringify(this.detailProductLinks));
    } catch (e) {
      console.warn(e);
    }
  }

  /**
   * Inicializa el entorno 3D y 2D dentro de #pane-bim cuando se activa la pestaña o al arrancar.
   */
  initWorkspace() {
    const container = document.getElementById('pane-bim');
    if (!container) return;

    if (!container.dataset.initialized) {
      container.dataset.initialized = 'true';
      this._renderWorkspaceLayout(container);
      this._bindToolbarControls();
    }

    const canvas3D = document.getElementById('bim-assembler-canvas');
    if (canvas3D && !this.assembler3D) {
      this.assembler3D = new BIMAssembler3D(canvas3D, (pieceMeta) => {
        this.selectedPieceMeta = pieceMeta;
        this._renderSelectedPieceInspector(pieceMeta);
        const canvas2D = document.getElementById('bim-replanteo-2d-canvas');
        if (canvas2D && this.currentReplanteo) {
          BIMReplanteo2DRenderer.draw(canvas2D, this.currentReplanteo, pieceMeta);
        }
      });
    }

    this.recalculateAndRenderAll();
    setTimeout(() => {
      if (this.assembler3D) this.assembler3D.resize();
      const canvas2D = document.getElementById('bim-replanteo-2d-canvas');
      if (canvas2D && this.currentReplanteo) {
        BIMReplanteo2DRenderer.draw(canvas2D, this.currentReplanteo, this.selectedPieceMeta);
      }
    }, 60);
  }

  _renderWorkspaceLayout(container) {
    container.innerHTML = `
      <div class="bim-workspace-grid">
        <!-- COLUMNA IZQUIERDA: CONFIGURADOR JERÁRQUICO DE SISTEMA, PRODUCTOS Y GEOMETRÍA -->
        <aside class="bim-left-col">
          <div class="bim-card">
            <div class="bim-card-header">
              <span class="bim-badge-accent">SECCIÓN 5 & 15 · DEMOSTRACIONES REALES</span>
              <h3>Sistema Constructivo y Geometría</h3>
            </div>
            <div class="bim-demo-switcher">
              <button class="bim-demo-btn active" data-demo="demoA_tejado" id="btn-demo-a">
                <strong>DEMO A · Tejado Pieza a Pieza</strong>
                <span>Teja Borja / Escandella / Pizarra CUPA / VMZINC + Rastrel + Thermochip</span>
              </button>
              <button class="bim-demo-btn" data-demo="demoB_azotea" id="btn-demo-b">
                <strong>DEMO B · Azotea Capa a Capa</strong>
                <span>DANOSA / Sika + URSA XPS + Plots Peygran + Gres Aragón + Jimten</span>
              </button>
            </div>

            <div id="bim-geometry-inputs" class="bim-geom-form"></div>
          </div>

          <div class="bim-card">
            <div class="bim-card-header">
              <span class="bim-badge-accent">MATERIALES → FAMILIA → FABRICANTE → MODELO</span>
              <h3>Asignación Comercial y Variantes Oficiales</h3>
            </div>
            <div id="bim-product-selectors" class="bim-selectors-list"></div>
          </div>

          <div class="bim-card">
            <div class="bim-card-header">
              <span class="bim-badge-accent">SECCIÓN 7 · CAPAS Y COMPONENTES 3D</span>
              <h3>Control de Capas (Ocultar / Rayos X / Aislar)</h3>
            </div>
            <div id="bim-layers-control-list" class="bim-layers-list"></div>
          </div>
        </aside>

        <!-- COLUMNA CENTRAL: VISOR 3D PIEZA A PIEZA + INSPECTOR + PLANO CAD 2D DE REPLANTEO -->
        <section class="bim-center-col">
          <div class="bim-viewport-wrapper">
            <canvas id="bim-assembler-canvas"></canvas>

            <!-- HUD Superior del Visor 3D -->
            <div class="bim-viewport-hud-top">
              <div class="bim-hud-title" id="bim-hud-system-title">DEMO A — Tejado ventilado pieza a pieza</div>
              <div class="bim-hud-cam-bar">
                <button class="bim-cam-btn" data-cam="iso" title="Vista Axonométrica">Axonométrica</button>
                <button class="bim-cam-btn" data-cam="top" title="Planta de Replanteo">Planta</button>
                <button class="bim-cam-btn" data-cam="front" title="Alzado de Alero / Peto">Alzado</button>
                <button class="bim-cam-btn" data-cam="side" title="Sección Constructiva">Sección</button>
                <button class="bim-cam-btn" data-cam="detail" title="Zoom Encuentro Singular">Zoom Detalle</button>
              </div>
            </div>

            <!-- Inspector flotante de Pieza Individual 3D (Clic en cualquier teja, rastrel, plot o baldosa) -->
            <div class="bim-piece-inspector" id="bim-piece-inspector">
              <div class="bim-pi-hint">
                💡 <strong>Inspección Interactiva 3D:</strong> Haz clic sobre cualquier teja, canal, cobija, laja de pizarra, rastrel, plot Peygran, plancha XPS o baldosa para inspeccionar su código de pieza y abrir su Ficha Técnica Oficial.
              </div>
            </div>
          </div>

          <!-- Plano CAD 2D de Replanteo sincronizado con el modelo 3D -->
          <div class="bim-replanteo-2d-box">
            <div class="bim-rep2d-header">
              <div>
                <strong>📐 PLANO CAD 2D DE REPLANTEO AUTOMÁTICO</strong>
                <span id="bim-rep2d-subtitle">Sincronizado en tiempo real con las dimensiones útiles del fabricante</span>
              </div>
              <div class="bim-rep2d-legend">
                <span><i style="background:#b65338"></i> Pieza entera</span>
                <span><i style="background:#f59e0b"></i> Pieza de corte en borde</span>
                <span><i style="background:#fbbf24"></i> Línea de rastrel / Plot</span>
                <span><i style="background:#00e5ff"></i> Pieza seleccionada</span>
              </div>
            </div>
            <div class="bim-rep2d-canvas-wrap">
              <canvas id="bim-replanteo-2d-canvas"></canvas>
            </div>
          </div>
        </section>

        <!-- COLUMNA DERECHA: MOTOR DE COMPATIBILIDAD, CALCULADORA DE REPLANTEO Y EXPORTACIÓN -->
        <aside class="bim-right-col">
          <div class="bim-card">
            <div class="bim-card-header">
              <span class="bim-badge-accent">SECCIÓN 9 · REGLAS VERIFICABLES</span>
              <h3>Motor de Compatibilidad Constructiva</h3>
            </div>
            <div id="bim-compatibility-panel" class="bim-compat-list"></div>
          </div>

          <div class="bim-card">
            <div class="bim-card-header">
              <span class="bim-badge-accent">SECCIÓN 12 · MEDICIONES EXACTAS</span>
              <h3>Calculadora de Replanteo y Pesos</h3>
            </div>
            <div id="bim-replanteo-kpis" class="bim-kpi-grid"></div>
            <div class="bim-boq-table-wrap">
              <table class="bim-boq-table">
                <thead>
                  <tr>
                    <th>Componente / Producto Real</th>
                    <th>Teórica</th>
                    <th>Montaje</th>
                    <th>Pedido</th>
                    <th>Peso</th>
                  </tr>
                </thead>
                <tbody id="bim-boq-tbody"></tbody>
              </table>
            </div>
          </div>

          <div class="bim-card">
            <div class="bim-card-header">
              <span class="bim-badge-accent">SECCIÓN 10, 13 & 14 · DOCUMENTACIÓN Y GESTIÓN</span>
              <h3>Catálogo, Informes y Conexión HYDRO 3D</h3>
            </div>
            <div class="bim-actions-stack">
              <button class="bim-action-btn primary" id="btn-open-catalog-modal">
                📚 Explorar Catálogo Completo (12 Familias · 24 Fabricantes)
              </button>
              <button class="bim-action-btn" id="btn-open-comparator-modal">
                ⚖️ Comparador Técnico de Productos
              </button>
              <button class="bim-action-btn" id="btn-open-admin-modal">
                🛠️ Administrar Catálogo / Alta de Producto (Versiones)
              </button>
              <button class="bim-action-btn hydro-sync" id="btn-sync-hydro3d">
                🌊 Enviar Azotea Comercial a ROOFLAB HYDRO 3D
              </button>
              <div class="bim-export-row">
                <button class="bim-export-btn" id="btn-export-bim-pdf" title="Generar Informe Técnico Imprimible / PDF">📄 Informe PDF</button>
                <button class="bim-export-btn" id="btn-export-bim-csv" title="Descargar Mediciones en CSV Excel">📊 Tabla CSV</button>
                <button class="bim-export-btn" id="btn-export-bim-json" title="Exportar Especificación BIM JSON">📦 BIM JSON</button>
              </div>
            </div>
          </div>
        </aside>
      </div>
    `;

    // Eventos de cambio de DEMO A / DEMO B
    container.querySelectorAll('.bim-demo-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.bim-demo-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeDemoId = btn.dataset.demo;
        this.selectedPieceMeta = null;
        this.recalculateAndRenderAll();
      });
    });

    // Eventos de cámara 3D
    container.querySelectorAll('.bim-cam-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (this.assembler3D) this.assembler3D.setCameraPreset(btn.dataset.cam);
      });
    });

    // Botones de Modales y Exportación
    document.getElementById('btn-open-catalog-modal')?.addEventListener('click', () => {
      this.openCatalogExplorerModal();
    });
    document.getElementById('btn-open-comparator-modal')?.addEventListener('click', () => {
      this.openComparatorModal();
    });
    document.getElementById('btn-open-admin-modal')?.addEventListener('click', () => {
      this.openAdminProductModal();
    });
    document.getElementById('btn-sync-hydro3d')?.addEventListener('click', () => {
      this.syncAndOpenHydro3D();
    });
    document.getElementById('btn-export-bim-pdf')?.addEventListener('click', () => {
      this.exportTechnicalReportPDF();
    });
    document.getElementById('btn-export-bim-csv')?.addEventListener('click', () => {
      this.exportBoqCSV();
    });
    document.getElementById('btn-export-bim-json')?.addEventListener('click', () => {
      this.exportProjectJSON();
    });
  }

  _bindToolbarControls() {
    const playBtn = document.getElementById('bim-assembly-play');
    const progSlider = document.getElementById('bim-assembly-slider');
    const progLabel = document.getElementById('bim-assembly-pct');
    const expSlider = document.getElementById('bim-explode-slider');
    const catQuickBtn = document.getElementById('bim-quick-catalog-btn');

    if (playBtn) {
      playBtn.addEventListener('click', () => {
        if (!this.assembler3D) return;
        const playing = this.assembler3D.togglePlayAssembly((p, isPlaying) => {
          const pct = Math.round(p * 100);
          if (progSlider) progSlider.value = String(pct);
          if (progLabel) progLabel.textContent = `${pct}%`;
          playBtn.textContent = isPlaying ? '⏸ Pausar Montaje' : '▶ Montaje Pieza a Pieza';
        });
        playBtn.textContent = playing ? '⏸ Pausar Montaje' : '▶ Montaje Pieza a Pieza';
      });
    }

    if (progSlider) {
      progSlider.addEventListener('input', () => {
        const val = Number(progSlider.value) || 100;
        if (progLabel) progLabel.textContent = `${val}%`;
        if (this.assembler3D) {
          this.assembler3D.isPlayingAssembly = false;
          if (playBtn) playBtn.textContent = '▶ Montaje Pieza a Pieza';
          this.assembler3D.setAssemblyProgress(val / 100);
        }
      });
    }

    if (expSlider) {
      expSlider.addEventListener('input', () => {
        const val = Number(expSlider.value) || 0;
        if (this.assembler3D) {
          this.assembler3D.setExplodeFactor(val / 100);
        }
      });
    }

    if (catQuickBtn) {
      catQuickBtn.addEventListener('click', () => this.openCatalogExplorerModal());
    }
  }

  /**
   * Recalcula el replanteo geométrico, evalúa reglas de compatibilidad,
   * reconstruye el modelo 3D pieza a pieza y actualiza el plano 2D y tablas.
   */
  recalculateAndRenderAll() {
    const cfg = this.demoConfigs[this.activeDemoId];
    if (!cfg) return;

    if (cfg.systemType === 'tejado') {
      this.currentReplanteo = BIMReplanteoCalculator.calculateSlopedRoof(cfg, this.store);
    } else {
      this.currentReplanteo = BIMReplanteoCalculator.calculateFlatRoof(cfg, this.store);
    }

    this.currentCompatibility = BIMCompatibilityEngine.evaluate(
      cfg,
      this.currentReplanteo,
      this.store
    );

    const hudTitle = document.getElementById('bim-hud-system-title');
    if (hudTitle) {
      hudTitle.textContent =
        cfg.systemType === 'tejado'
          ? `DEMO A · ${this.currentReplanteo.products.covering.brand} (${this.currentReplanteo.replanteoParams.mainPiecesAssembly} piezas · Paso ${this.currentReplanteo.replanteoParams.battenStepMm} mm)`
          : `DEMO B · Azotea ${cfg.roofSubType.replace('_', ' ').toUpperCase()} (${this.currentReplanteo.products.waterproofing.brand} + ${this.currentReplanteo.products.insulation.brand})`;
    }

    this._renderGeometryInputs(cfg);
    this._renderProductSelectors(cfg);

    if (this.assembler3D) {
      this.assembler3D.buildFromReplanteo(this.currentReplanteo);
      this._renderLayerControls();
    }

    this._renderSelectedPieceInspector(this.selectedPieceMeta);

    const canvas2D = document.getElementById('bim-replanteo-2d-canvas');
    if (canvas2D) {
      BIMReplanteo2DRenderer.draw(canvas2D, this.currentReplanteo, this.selectedPieceMeta);
    }

    this._renderCompatibilityPanel();
    this._renderReplanteoBoQPanel();
  }

  _renderGeometryInputs(cfg) {
    const box = document.getElementById('bim-geometry-inputs');
    if (!box) return;

    if (cfg.systemType === 'tejado') {
      const cov = this.currentReplanteo.products.covering;
      const minStep = cov.installation.battenDistanceMinMm || 100;
      const maxStep = cov.installation.battenDistanceMaxMm || 450;
      const currStep = this.currentReplanteo.replanteoParams.battenStepMm;

      box.innerHTML = `
        <div class="bim-form-row">
          <label>Longitud horiz. faldón (m)
            <input type="number" step="0.2" min="2.0" max="15.0" id="bim-inp-len" value="${cfg.geometry.lengthHorizM}">
          </label>
          <label>Ancho de alero (m)
            <input type="number" step="0.2" min="2.0" max="15.0" id="bim-inp-wid" value="${cfg.geometry.widthM}">
          </label>
        </div>
        <div class="bim-form-row">
          <label>Pendiente faldón (%) [Mín. ${cov.installation.minSlopePct}%]
            <input type="number" step="1" min="2" max="120" id="bim-inp-slope" value="${cfg.geometry.slopePct}">
          </label>
          <label>Paso de rastrel (mm) [${minStep}–${maxStep}]
            <input type="number" step="2" min="80" max="2500" id="bim-inp-step" value="${currStep}">
          </label>
        </div>
        <div class="bim-form-row">
          <label>Merma de pedido (%)
            <input type="number" step="1" min="0" max="20" id="bim-inp-waste" value="${cfg.geometry.wastePct}">
          </label>
          <div class="bim-auto-step-wrap">
            <button class="bim-mini-btn" id="bim-btn-reset-step" title="Ajustar al paso nominal oficial de la ficha técnica">
              ↺ Paso Oficial (${cov.geometry.usefulLengthNominalMm} mm)
            </button>
          </div>
        </div>
      `;

      box.querySelector('#bim-inp-len')?.addEventListener('change', (e) => {
        cfg.geometry.lengthHorizM = Math.max(1.8, Number(e.target.value) || 4.5);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-wid')?.addEventListener('change', (e) => {
        cfg.geometry.widthM = Math.max(1.8, Number(e.target.value) || 3.6);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-slope')?.addEventListener('change', (e) => {
        cfg.geometry.slopePct = Math.max(1, Number(e.target.value) || 32);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-step')?.addEventListener('change', (e) => {
        cfg.geometry.customBattenStepMm = Number(e.target.value);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-waste')?.addEventListener('change', (e) => {
        cfg.geometry.wastePct = Math.max(0, Number(e.target.value) || 5);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-btn-reset-step')?.addEventListener('click', () => {
        delete cfg.geometry.customBattenStepMm;
        this.recalculateAndRenderAll();
      });
    } else {
      box.innerHTML = `
        <div class="bim-form-row full">
          <label>Subtipología Constructiva de Azotea
            <select id="bim-sel-roof-subtype">
              <option value="invertida_plots" ${cfg.roofSubType === 'invertida_plots' ? 'selected' : ''}>Azotea Invertida Transitable sobre Plots Regulables Peygran</option>
              <option value="convencional_fija" ${cfg.roofSubType === 'convencional_fija' ? 'selected' : ''}>Azotea Convencional (Aislamiento bajo Impermeabilización + Pavimento)</option>
              <option value="ajardinada" ${cfg.roofSubType === 'ajardinada' ? 'selected' : ''}>Cubierta Ajardinada Extensiva Ecológica (Optigrün FKD 25 + Sedum)</option>
            </select>
          </label>
        </div>
        <div class="bim-form-row">
          <label>Largo Azotea (m)
            <input type="number" step="0.2" min="2.4" max="20.0" id="bim-inp-flat-len" value="${cfg.geometry.lengthM}">
          </label>
          <label>Ancho Azotea (m)
            <input type="number" step="0.2" min="2.4" max="20.0" id="bim-inp-flat-wid" value="${cfg.geometry.widthM}">
          </label>
        </div>
        <div class="bim-form-row">
          <label>Pendiente Formación (%)
            <input type="number" step="0.2" min="0.0" max="8.0" id="bim-inp-flat-slope" value="${cfg.geometry.slopePct}">
          </label>
          <label>Remonte en Peto (mm) [CTE ≥200]
            <input type="number" step="10" min="100" max="500" id="bim-inp-flat-turnup" value="${cfg.geometry.parapetTurnupMm}">
          </label>
        </div>
      `;

      box.querySelector('#bim-sel-roof-subtype')?.addEventListener('change', (e) => {
        cfg.roofSubType = e.target.value;
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-flat-len')?.addEventListener('change', (e) => {
        cfg.geometry.lengthM = Math.max(2.0, Number(e.target.value) || 4.8);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-flat-wid')?.addEventListener('change', (e) => {
        cfg.geometry.widthM = Math.max(2.0, Number(e.target.value) || 3.6);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-flat-slope')?.addEventListener('change', (e) => {
        cfg.geometry.slopePct = Math.max(0, Number(e.target.value) || 2.0);
        this.recalculateAndRenderAll();
      });
      box.querySelector('#bim-inp-flat-turnup')?.addEventListener('change', (e) => {
        cfg.geometry.parapetTurnupMm = Math.max(80, Number(e.target.value) || 200);
        this.recalculateAndRenderAll();
      });
    }
  }

  /**
   * Renderiza los selectores de producto comercial y variantes dimensionales oficiales
   * para cada capa del sistema activo (Sección 5 y Sección 11).
   */
  _renderProductSelectors(cfg) {
    const container = document.getElementById('bim-product-selectors');
    if (!container) return;

    const slots =
      cfg.systemType === 'tejado'
        ? [
            { key: 'coveringId', label: '1. Cobertura Exterior (Teja / Pizarra / Zinc / Panel)', role: 'roof_covering' },
            { key: 'battenSystemId', label: '2. Rastreles, Contrarastreles y Lámina', role: 'batten_system' },
            { key: 'supportPanelId', label: '3. Panel Sándwich Estructural Bajo Teja', role: 'support_panel' },
            { key: 'fastenerId', label: '4. Fijación Mecánica (Clips / Ganchos / Patas Inox)', role: 'fastener' },
            { key: 'gutterId', label: '5. Canalón Perimetral de Alero', role: 'gutter_unit' },
          ]
        : [
            { key: 'waterproofingId', label: '1. Membrana Impermeabilizante (Bituminosa / PVC)', role: 'waterproofing' },
            { key: 'insulationId', label: '2. Aislamiento Térmico (XPS / Lana de Roca)', role: 'insulation' },
            { key: 'separatorBotId', label: '3. Geotextil Separador Antipunzonante', role: 'separator' },
            ...(cfg.roofSubType === 'ajardinada'
              ? [{ key: 'greenRoofId', label: '4. Sistema Cubierta Ajardinada Ecológica', role: 'green_roof_system' }]
              : [
                  { key: 'plotsId', label: '4. Plots Regulables Autonivelantes', role: 'plots' },
                  { key: 'pavementId', label: '5. Pavimento Técnico Porcelánico 20 mm', role: 'pavement' },
                ]),
            { key: 'drainUnitId', label: '6. Cazoleta Sifónica / Sumidero de Evacuación', role: 'drain_unit' },
          ];

    container.innerHTML = slots
      .map((slot) => {
        const candidates = this.store.getProductsByRole(slot.role);
        const currentId = cfg.selectedProducts[slot.key];
        const currentProd = this.store.getProductById(currentId) || candidates[0];
        const vBadge = VERIFICATION_BADGES[currentProd.verificationStatus] || VERIFICATION_BADGES.VERIFICADO_OFICIAL;

        const variantsHtml =
          Array.isArray(currentProd.variants) && currentProd.variants.length > 0
            ? `
          <div class="bim-variant-row">
            <span>Variante oficial:</span>
            <select class="bim-variant-select" data-prod-id="${currentProd.id}">
              ${currentProd.variants
                .map(
                  (v) =>
                    `<option value="${v.id}" ${currentProd.selectedVariantId === v.id ? 'selected' : ''}>${v.label}</option>`
                )
                .join('')}
            </select>
          </div>
        `
            : '';

        return `
          <div class="bim-slot-item">
            <div class="bim-slot-top">
              <span class="bim-slot-label">${slot.label}</span>
              <span class="bim-verif-pill" style="color:${vBadge.color};background:${vBadge.bg}">${vBadge.icon} ${vBadge.label}</span>
            </div>
            <div class="bim-slot-main">
              <select class="bim-prod-select" data-slot-key="${slot.key}">
                ${candidates
                  .map(
                    (p) =>
                      `<option value="${p.id}" ${p.id === currentProd.id ? 'selected' : ''}>[${p.manufacturerName}] ${p.model}</option>`
                  )
                  .join('')}
              </select>
              <button class="bim-btn-datasheet" data-datasheet-id="${currentProd.id}" title="Abrir Ficha Técnica Oficial de ${currentProd.model}">
                📄 Ficha
              </button>
            </div>
            ${variantsHtml}
          </div>
        `;
      })
      .join('');

    // Eventos de cambio de producto comercial
    container.querySelectorAll('.bim-prod-select').forEach((sel) => {
      sel.addEventListener('change', () => {
        const slotKey = sel.dataset.slotKey;
        const newProdId = sel.value;
        cfg.selectedProducts[slotKey] = newProdId;
        this.selectedPieceMeta = null;

        // Si en DEMO A cambia la cobertura, sincronizamos el paso de rastrel nominal oficial
        // y sugerimos la fijación compatible si el usuario no quiere forzar un error
        if (slotKey === 'coveringId') {
          delete cfg.geometry.customBattenStepMm;
          const cov = this.store.getProductById(newProdId);
          if (cov?.subType === 'pizarra_natural') {
            cfg.selectedProducts.fastenerId = 'ROTHOBLAAS-GANCHO-INOX90';
          } else if (cov?.subType === 'zinc_junta_alzada') {
            cfg.selectedProducts.fastenerId = 'VMZINC-PATAS-INOX';
          } else {
            cfg.selectedProducts.fastenerId = 'SFS-CLIP-TEJA-INOX';
          }
        }
        this.recalculateAndRenderAll();
      });
    });

    // Eventos de cambio de variante dimensional oficial (recalcula espesor, ancho útil, paso y 3D en tiempo real)
    container.querySelectorAll('.bim-variant-select').forEach((vSel) => {
      vSel.addEventListener('change', () => {
        const prodId = vSel.dataset.prodId;
        const variantId = vSel.value;
        this.store.applyOfficialVariant(prodId, variantId);
        this.selectedPieceMeta = null;
        delete cfg.geometry.customBattenStepMm;
        this.recalculateAndRenderAll();
      });
    });

    // Botones de Ficha Técnica Digital Oficial
    container.querySelectorAll('.bim-btn-datasheet').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.openProductDatasheetModal(btn.dataset.datasheetId);
      });
    });
  }

  _renderLayerControls() {
    const listEl = document.getElementById('bim-layers-control-list');
    if (!listEl || !this.assembler3D) return;
    const layers = this.assembler3D.getLayerDescriptors();

    listEl.innerHTML = layers
      .map(
        (l) => `
        <div class="bim-layer-ctrl-row">
          <div class="bim-lc-name" title="${l.productName}">
            <strong>${l.title}</strong>
          </div>
          <div class="bim-lc-actions">
            <button class="bim-lc-btn ${l.visible ? 'active' : ''}" data-action="vis" data-key="${l.key}" title="Mostrar / Ocultar Capa">
              ${l.visible ? '👁️' : '🚫'}
            </button>
            <button class="bim-lc-btn ${l.transparent ? 'active' : ''}" data-action="xray" data-key="${l.key}" title="Modo Transparente Rayos X">
              👻
            </button>
            <button class="bim-lc-btn" data-action="iso" data-key="${l.key}" title="Aislar solo esta capa">
              🎯
            </button>
            ${
              l.productId
                ? `<button class="bim-lc-btn" data-action="doc" data-prod="${l.productId}" title="Ver Ficha Técnica Oficial">📄</button>`
                : ''
            }
          </div>
        </div>
      `
      )
      .join('');

    listEl.querySelectorAll('.bim-lc-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const act = btn.dataset.action;
        const key = btn.dataset.key;
        if (act === 'vis') {
          const curr = this.assembler3D.layerStates[key]?.visible !== false;
          this.assembler3D.setLayerVisibility(key, !curr);
          this._renderLayerControls();
        } else if (act === 'xray') {
          const curr = Boolean(this.assembler3D.layerStates[key]?.transparent);
          this.assembler3D.setLayerTransparency(key, !curr);
          this._renderLayerControls();
        } else if (act === 'iso') {
          this.assembler3D.isolateLayer(key);
          this._renderLayerControls();
        } else if (act === 'doc') {
          this.openProductDatasheetModal(btn.dataset.prod);
        }
      });
    });
  }

  _renderSelectedPieceInspector(pieceMeta) {
    const box = document.getElementById('bim-piece-inspector');
    if (!box) return;

    if (!pieceMeta) {
      box.innerHTML = `
        <div class="bim-pi-hint">
          💡 <strong>Inspección Interactiva 3D:</strong> Haz clic sobre cualquier teja, canal, cobija, laja de pizarra, rastrel, plot Peygran, plancha XPS o baldosa para inspeccionar su código de pieza y abrir su Ficha Técnica Oficial.
        </div>
      `;
      return;
    }

    const prod = this.store.getProductById(pieceMeta.productId);
    box.innerHTML = `
      <div class="bim-pi-card">
        <div class="bim-pi-left">
          <span class="bim-pi-code">${pieceMeta.pieceCode}</span>
          <strong>${pieceMeta.layerName}</strong>
          <span class="bim-pi-role">${pieceMeta.roleLabel}</span>
          <span class="bim-pi-dims">📐 ${pieceMeta.dimensionsMm} · ⚖️ ${pieceMeta.weightKg} kg</span>
        </div>
        <div class="bim-pi-right">
          ${
            prod
              ? `<button class="bim-pi-doc-btn" id="btn-pi-open-doc">📄 Ficha Técnica (${prod.manufacturerName})</button>`
              : ''
          }
        </div>
      </div>
    `;

    box.querySelector('#btn-pi-open-doc')?.addEventListener('click', () => {
      this.openProductDatasheetModal(pieceMeta.productId);
    });
  }

  _renderCompatibilityPanel() {
    const panel = document.getElementById('bim-compatibility-panel');
    if (!panel || !this.currentCompatibility) return;

    const { alerts, summary } = this.currentCompatibility;
    const statusHeader =
      summary.errCount > 0
        ? `<div class="bim-compat-banner error">❌ ${summary.errCount} Incompatibilidad(es) Constructiva(s) Detectada(s)</div>`
        : summary.warnCount > 0
        ? `<div class="bim-compat-banner warning">⚠️ Diseño Válido con ${summary.warnCount} Advertencia(s) Técnica(s)</div>`
        : `<div class="bim-compat-banner ok">✅ Compatibilidad Constructiva 100% Verificada (${summary.okCount} reglas)</div>`;

    panel.innerHTML =
      statusHeader +
      alerts
        .map((a) => {
          const icon = a.severity === 'error' ? '❌' : a.severity === 'warning' ? '⚠️' : '✅';
          return `
            <div class="bim-alert-card ${a.severity}">
              <div class="bim-alert-title">${icon} ${a.problem}</div>
              <div class="bim-alert-row"><strong>Parámetro:</strong> ${a.affectedParam}</div>
              <div class="bim-alert-row"><strong>Fuente:</strong> ${a.source}</div>
              <div class="bim-alert-row"><strong>Solución:</strong> ${a.solution}</div>
            </div>
          `;
        })
        .join('');
  }

  _renderReplanteoBoQPanel() {
    const kpiBox = document.getElementById('bim-replanteo-kpis');
    const tbody = document.getElementById('bim-boq-tbody');
    if (!kpiBox || !tbody || !this.currentReplanteo) return;

    const rep = this.currentReplanteo;
    if (rep.systemType === 'tejado') {
      kpiBox.innerHTML = `
        <div class="bim-kpi">
          <span>Superficie Real Faldón</span>
          <strong>${rep.geometry.realAreaM2} m²</strong>
          <small>L=${rep.geometry.rafterLengthM} m (${rep.geometry.slopePct}% / ${rep.geometry.slopeDeg}°)</small>
        </div>
        <div class="bim-kpi">
          <span>Replanteo Cobertura</span>
          <strong>${rep.replanteoParams.mainPiecesAssembly} uds</strong>
          <small>${rep.replanteoParams.numRows} hiladas × ${rep.replanteoParams.numCols} cols</small>
        </div>
        <div class="bim-kpi">
          <span>Paso Rastrel / Solape</span>
          <strong>${rep.replanteoParams.battenStepMm} mm</strong>
          <small>Solape real: ${rep.replanteoParams.realOverlapLongMm} mm (${rep.replanteoParams.totalBattenMl} m lin.)</small>
        </div>
        <div class="bim-kpi">
          <span>Peso Total Cubierta</span>
          <strong>${rep.summary.totalWeightKg} kg</strong>
          <small>${rep.summary.weightPerM2Kg} kg/m² · U=${rep.summary.uValueWmk} W/m²K</small>
        </div>
      `;
    } else {
      kpiBox.innerHTML = `
        <div class="bim-kpi">
          <span>Superficie / Remonte</span>
          <strong>${rep.geometry.flatAreaM2} m²</strong>
          <small>+${rep.geometry.turnupAreaM2} m² petos (h=${rep.geometry.parapetTurnupMm} mm)</small>
        </div>
        <div class="bim-kpi">
          <span>Pavimento / Sustrato</span>
          <strong>${rep.roofSubType === 'ajardinada' ? `${rep.geometry.flatAreaM2} m²` : `${rep.replanteoParams.assemblyTilesCount} uds`}</strong>
          <small>${rep.roofSubType === 'ajardinada' ? 'Optigrün FKD 25 + Sedum' : `${rep.replanteoParams.fullTilesCount} enteras + ${rep.replanteoParams.cutBorderTilesCount} borde`}</small>
        </div>
        <div class="bim-kpi">
          <span>Plots / Planchas XPS</span>
          <strong>${rep.replanteoParams.assemblyPlotsCount} plots</strong>
          <small>${rep.replanteoParams.assemblyInsulationBoards} planchas aislantes</small>
        </div>
        <div class="bim-kpi">
          <span>Peso Total Sistema</span>
          <strong>${rep.summary.totalWeightKg} kg</strong>
          <small>${rep.summary.weightPerM2Kg} kg/m² · U=${rep.summary.uValueWmk} W/m²K</small>
        </div>
      `;
    }

    tbody.innerHTML = rep.lineItems
      .map(
        (item) => `
        <tr>
          <td>
            <div class="bim-boq-prod">
              <strong>${item.manufacturerName} · ${item.model}</strong>
              <span>${item.roleLabel} · ${item.dimensionsStr}</span>
            </div>
          </td>
          <td>${item.theoreticalQty} <small>${item.unit}</small></td>
          <td><strong>${item.assemblyQty}</strong></td>
          <td class="bim-boq-order">${item.orderQty}</td>
          <td>${item.totalWeightKg} kg</td>
        </tr>
      `
      )
      .join('');
  }

  // ===========================================================================
  // VINCULACIÓN CON LOS 10 DETALLES CONSTRUCTIVOS EXISTENTES (SECCIÓN 10)
  // ===========================================================================
  renderDetailCommercialProductsBlock(detailId) {
    const existingPanel = document.getElementById('detail-bim-commercial-box');
    const layersSidebar = document.getElementById('layers-list');
    if (!layersSidebar) return;

    const productIds = this.detailProductLinks[detailId] || DEFAULT_DETAIL_PRODUCT_LINKS[detailId] || [];
    const products = productIds
      .map((id) => this.store.getProductById(id))
      .filter(Boolean);

    const html = `
      <div class="detail-bim-header">
        <span>🏷️ PRODUCTOS COMERCIALES REALES ASIGNADOS</span>
        <button class="detail-bim-open-btn" id="btn-detail-go-bim">Abrir en Montaje BIM 3D →</button>
      </div>
      <div class="detail-bim-list">
        ${products
          .map(
            (p, idx) => `
          <div class="detail-bim-item">
            <div class="detail-bim-info">
              <strong>${p.manufacturerName} · ${p.brand}</strong>
              <span>${p.model}</span>
              <small>📐 ${p.geometry.lengthNominalMm}×${p.geometry.widthNominalMm}×${p.geometry.thicknessMm} mm · Ref: ${p.refCode}</small>
            </div>
            <div class="detail-bim-btns">
              <button class="detail-bim-doc-btn" data-doc-id="${p.id}" title="Ver Ficha Técnica Oficial">📄 Ficha</button>
              <button class="detail-bim-swap-btn" data-swap-idx="${idx}" data-role="${p.role}" title="Sustituir por otro fabricante compatible">⇄</button>
            </div>
          </div>
        `
          )
          .join('')}
      </div>
    `;

    let box = existingPanel;
    if (!box) {
      box = document.createElement('div');
      box.id = 'detail-bim-commercial-box';
      box.className = 'detail-bim-commercial-box';
      layersSidebar.parentElement.appendChild(box);
    }
    box.innerHTML = html;

    box.querySelectorAll('.detail-bim-doc-btn').forEach((btn) => {
      btn.addEventListener('click', () => this.openProductDatasheetModal(btn.dataset.docId));
    });

    box.querySelectorAll('.detail-bim-swap-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = Number(btn.dataset.swapIdx);
        const role = btn.dataset.role;
        const candidates = this.store.getProductsByRole(role);
        if (candidates.length <= 1) {
          this.openCatalogExplorerModal( null, role );
          return;
        }
        const currId = productIds[idx];
        const currPos = candidates.findIndex((c) => c.id === currId);
        const nextProd = candidates[(currPos + 1) % candidates.length];
        this.detailProductLinks[detailId][idx] = nextProd.id;
        this._saveDetailProductLinks();
        this.renderDetailCommercialProductsBlock(detailId);
      });
    });

    box.querySelector('#btn-detail-go-bim')?.addEventListener('click', () => {
      // Activa el modo BIM cargando la demo correspondiente (Tejado para detalles 5..9, Azotea para 1..4)
      const isSloped =
        detailId.startsWith('detalle5') ||
        detailId.startsWith('detalle6') ||
        detailId.startsWith('detalle7') ||
        detailId.startsWith('detalle8') ||
        detailId.startsWith('detalle9');
      this.activeDemoId = isSloped ? 'demoA_tejado' : 'demoB_azotea';
      if (detailId === 'detalle4_plots') {
        this.demoConfigs.demoB_azotea.roofSubType = 'invertida_plots';
      } else if (detailId === 'detalle1') {
        this.demoConfigs.demoB_azotea.roofSubType = 'convencional_fija';
      } else if (detailId === 'detalle5_alero_teja' || detailId === 'detalle6_cumbrera_teja') {
        this.demoConfigs.demoA_tejado.selectedProducts.coveringId = 'BORJA-C5021';
        this.demoConfigs.demoA_tejado.selectedProducts.fastenerId = 'SFS-CLIP-TEJA-INOX';
      } else if (detailId === 'detalle7_teja_mixta') {
        this.demoConfigs.demoA_tejado.selectedProducts.coveringId = 'BORJA-TB12';
        this.demoConfigs.demoA_tejado.selectedProducts.fastenerId = 'SFS-CLIP-TEJA-INOX';
      } else if (detailId === 'detalle8_pizarra') {
        this.demoConfigs.demoA_tejado.selectedProducts.coveringId = 'CUPA-4-3222';
        this.demoConfigs.demoA_tejado.selectedProducts.fastenerId = 'ROTHOBLAAS-GANCHO-INOX90';
      } else if (detailId === 'detalle9_zinc') {
        this.demoConfigs.demoA_tejado.selectedProducts.coveringId = 'VMZINC-JUNTA-ALZADA-500';
        this.demoConfigs.demoA_tejado.selectedProducts.fastenerId = 'VMZINC-PATAS-INOX';
      }
      const modeBimBtn = document.getElementById('mode-bim-btn');
      if (modeBimBtn) modeBimBtn.click();
    });
  }

  // ===========================================================================
  // SINCRONIZACIÓN DIRECTA CON EL SIMULADOR DE AGUA ROOFLAB HYDRO 3D (SECCIÓN 10)
  // ===========================================================================
  syncAndOpenHydro3D() {
    // Calculamos la configuración comercial de la DEMO B (Azotea) para enviarla a HYDRO 3D
    const flatCfg = this.demoConfigs.demoB_azotea;
    const flatRep = BIMReplanteoCalculator.calculateFlatRoof(flatCfg, this.store);
    const payload = {
      syncedAt: new Date().toISOString(),
      roofSubType: flatCfg.roofSubType,
      geometry: flatRep.geometry,
      products: {
        waterproofing: {
          id: flatRep.products.waterproofing.id,
          brand: flatRep.products.waterproofing.brand,
          model: flatRep.products.waterproofing.model,
        },
        insulation: {
          id: flatRep.products.insulation.id,
          brand: flatRep.products.insulation.brand,
          model: flatRep.products.insulation.model,
          thicknessMm: flatRep.products.insulation.geometry.thicknessMm,
        },
        plots: {
          id: flatRep.products.plots.id,
          brand: flatRep.products.plots.brand,
          model: flatRep.products.plots.model,
          heightMm: flatRep.products.plots.geometry.thicknessMm,
          jointWidthMm: flatRep.products.plots.geometry.jointTabThicknessMm || 4,
        },
        pavement: {
          id: flatRep.products.pavement.id,
          brand: flatRep.products.pavement.brand,
          model: flatRep.products.pavement.model,
          lengthMm: flatRep.products.pavement.geometry.lengthNominalMm,
          widthMm: flatRep.products.pavement.geometry.widthNominalMm,
          thicknessMm: flatRep.products.pavement.geometry.thicknessMm,
        },
        drainUnit: {
          id: flatRep.products.drainUnit.id,
          brand: flatRep.products.drainUnit.brand,
          model: flatRep.products.drainUnit.model,
          outletDiameterMm: flatRep.products.drainUnit.geometry.outletDiameterMm,
          hydraulicCapacityLs: flatRep.products.drainUnit.geometry.hydraulicCapacityLs,
        },
      },
    };
    try {
      localStorage.setItem('ETSIE_C2_ACTIVE_BIM_HYDRO_SPEC', JSON.stringify(payload));
    } catch (e) {
      console.warn(e);
    }
    window.location.href = './hydro3d.html?bimSync=1';
  }

  // ===========================================================================
  // MODALES: FICHA TÉCNICA DIGITAL, CATÁLOGO COMPLETO, COMPARADOR Y ADMIN
  // ===========================================================================
  _injectModals() {
    if (document.getElementById('bim-modals-root')) return;
    const root = document.createElement('div');
    root.id = 'bim-modals-root';
    root.innerHTML = `
      <!-- 1. MODAL DE FICHA TÉCNICA DIGITAL OFICIAL (SECCIÓN 3) -->
      <div class="bim-modal-backdrop" id="bim-datasheet-modal" hidden>
        <div class="bim-modal-dialog large">
          <div class="bim-modal-header">
            <div id="bim-ds-header-title">Ficha Técnica Digital Oficial</div>
            <button class="bim-modal-close" data-close-modal="bim-datasheet-modal">✕</button>
          </div>
          <div class="bim-modal-body" id="bim-ds-body"></div>
        </div>
      </div>

      <!-- 2. MODAL EXPLORADOR DEL CATÁLOGO GENERAL DE FABRICANTES (SECCIÓN 2 Y 5) -->
      <div class="bim-modal-backdrop" id="bim-catalog-modal" hidden>
        <div class="bim-modal-dialog xlarge">
          <div class="bim-modal-header">
            <div>
              <strong>📚 Catálogo BIM de Productos Comerciales Reales (12 Familias · 24 Fabricantes)</strong>
            </div>
            <button class="bim-modal-close" data-close-modal="bim-catalog-modal">✕</button>
          </div>
          <div class="bim-modal-body" id="bim-cat-body"></div>
        </div>
      </div>

      <!-- 3. MODAL COMPARADOR TÉCNICO DE PRODUCTOS (SECCIÓN 5) -->
      <div class="bim-modal-backdrop" id="bim-comparator-modal" hidden>
        <div class="bim-modal-dialog xlarge">
          <div class="bim-modal-header">
            <div><strong>⚖️ Comparador Técnico de Productos Comerciales</strong></div>
            <button class="bim-modal-close" data-close-modal="bim-comparator-modal">✕</button>
          </div>
          <div class="bim-modal-body" id="bim-comp-body"></div>
        </div>
      </div>

      <!-- 4. MODAL ADMINISTRADOR DEL CATÁLOGO Y CONTROL DE VERSIONES (SECCIÓN 14) -->
      <div class="bim-modal-backdrop" id="bim-admin-modal" hidden>
        <div class="bim-modal-dialog large">
          <div class="bim-modal-header">
            <div><strong>🛠️ Administración del Catálogo BIM y Versiones de Ficha Técnica</strong></div>
            <button class="bim-modal-close" data-close-modal="bim-admin-modal">✕</button>
          </div>
          <div class="bim-modal-body" id="bim-admin-body"></div>
        </div>
      </div>
    `;
    document.body.appendChild(root);

    root.querySelectorAll('[data-close-modal]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.closeModal;
        const el = document.getElementById(id);
        if (el) el.hidden = true;
      });
    });

    root.querySelectorAll('.bim-modal-backdrop').forEach((backdrop) => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) backdrop.hidden = true;
      });
    });
  }

  /**
   * Abre la Ficha Técnica Digital Oficial de un producto con sus 5 bloques reglamentarios (Sección 3).
   */
  openProductDatasheetModal(productId) {
    const p = this.store.getProductById(productId);
    if (!p) return;

    const modal = document.getElementById('bim-datasheet-modal');
    const titleEl = document.getElementById('bim-ds-header-title');
    const bodyEl = document.getElementById('bim-ds-body');
    if (!modal || !bodyEl) return;

    const fam = BIM_FAMILIES.find((f) => f.id === p.familyId);
    const vBadge = VERIFICATION_BADGES[p.verificationStatus] || VERIFICATION_BADGES.VERIFICADO_OFICIAL;

    titleEl.innerHTML = `
      <span class="bim-verif-pill" style="color:${vBadge.color};background:${vBadge.bg}">${vBadge.icon} ${vBadge.label}</span>
      <strong>${p.manufacturerName} · ${p.brand} — ${p.model}</strong>
    `;

    bodyEl.innerHTML = `
      <div class="bim-ds-grid">
        <!-- 3.1. IDENTIFICACIÓN -->
        <div class="bim-ds-section">
          <h4>3.1. Identificación Comercial y Trazabilidad</h4>
          <table class="bim-ds-table">
            <tr><th>Fabricante / Marca</th><td><strong>${p.manufacturerName}</strong> (${p.brand})</td></tr>
            <tr><th>Modelo Comercial</th><td>${p.model}</td></tr>
            <tr><th>Código / Referencia</th><td><code>${p.refCode}</code></td></tr>
            <tr><th>Familia Constructiva</th><td>Familia ${fam ? `${fam.code} — ${fam.name}` : p.familyId}</td></tr>
            <tr><th>Sistema Constructivo</th><td>${p.applicationSystem}</td></tr>
            <tr><th>País / Disponibilidad</th><td>${p.country} · ${p.availability}</td></tr>
            <tr><th>Documento y Revisión</th><td>${p.versionDoc} (Rev. ${p.revisionDate})</td></tr>
          </table>
        </div>

        <!-- 3.2. GEOMETRÍA -->
        <div class="bim-ds-section">
          <h4>3.2. Geometría Oficial y Parámetros Dimensionales</h4>
          <table class="bim-ds-table">
            <tr><th>Dimensiones Nominales</th><td><strong>${p.geometry.lengthNominalMm || '-'} × ${p.geometry.widthNominalMm || '-'} × ${p.geometry.thicknessMm || '-'} mm</strong></td></tr>
            <tr><th>Dimensiones Útiles</th><td>${p.geometry.usefulLengthNominalMm || p.geometry.lengthNominalMm || '-'} × ${p.geometry.usefulWidthMm || p.geometry.widthNominalMm || '-'} mm</td></tr>
            <tr><th>Solape Longitudinal / Transv.</th><td>Long.: ${p.geometry.overlapLongMinMm ?? '-'} mm ${p.geometry.overlapLongMaxMm ? `a ${p.geometry.overlapLongMaxMm} mm` : ''} · Transv.: ${p.geometry.overlapTransMm ?? '-'} mm</td></tr>
            <tr><th>Consumo / Rendimiento</th><td>${p.geometry.unitsPerM2 ? `${p.geometry.unitsPerM2} uds/m²` : p.geometry.rollAreaM2 ? `Rollo ${p.geometry.rollAreaM2} m² (Útil ${p.geometry.usefulRollAreaM2} m²)` : 'Según replanteo'}</td></tr>
            <tr><th>Peso Unitario y Superficial</th><td><strong>${p.geometry.unitWeightKg ?? '-'} kg/ud</strong> ${p.geometry.surfaceWeightKgM2 ? `(${p.geometry.surfaceWeightKgM2} kg/m²)` : ''}</td></tr>
            <tr><th>Geometría BIM 3D</th><td><code>${p.geometry.shape3D}</code></td></tr>
          </table>
        </div>

        <!-- 3.3. CARACTERÍSTICAS TÉCNICAS -->
        <div class="bim-ds-section">
          <h4>3.3. Características Técnicas y Normativa</h4>
          <table class="bim-ds-table">
            <tr><th>Composición / Material</th><td>${p.technicalSpecs.material}</td></tr>
            <tr><th>Conductividad / Resistencia Térmica</th><td>${p.technicalSpecs.thermalConductivityWmk ? `λ = ${p.technicalSpecs.thermalConductivityWmk} W/(m·K)` : 'N/A'} ${p.technicalSpecs.thermalResistanceRd ? `· Rd = ${p.technicalSpecs.thermalResistanceRd} m²K/W` : ''} ${p.technicalSpecs.thermalTransmittanceU ? `· U = ${p.technicalSpecs.thermalTransmittanceU} W/m²K` : ''}</td></tr>
            <tr><th>Resistencia Mecánica / Compresión</th><td>${p.technicalSpecs.mechanicalStrength || 'Ver ficha'} ${p.technicalSpecs.compressiveStrengthKpa ? `(${p.technicalSpecs.compressiveStrengthKpa} kPa)` : ''}</td></tr>
            <tr><th>Reacción al Fuego</th><td><strong>${p.technicalSpecs.fireReaction || 'N/A'}</strong></td></tr>
            <tr><th>Comportamiento al Agua</th><td>${p.technicalSpecs.waterAbsorptionPct || 'Ver ficha'}</td></tr>
            <tr><th>Permeabilidad al Vapor</th><td>${p.technicalSpecs.vaporPermeability || 'N/A'}</td></tr>
            <tr><th>Normativa aplicable</th><td>${(p.technicalSpecs.standards || []).map((s) => `<span class="bim-std-tag">${s}</span>`).join(' ')}</td></tr>
          </table>
        </div>

        <!-- 3.4. COLOCACIÓN -->
        <div class="bim-ds-section">
          <h4>3.4. Condiciones Oficiales de Colocación</h4>
          <table class="bim-ds-table">
            <tr><th>Pendiente Mínima / Recomendada</th><td><strong>Mínima: ${p.installation.minSlopePct ?? 0}% (${p.installation.minSlopeDeg ?? 0}°)</strong> · Recomendada: ${p.installation.recommendedSlopePct ?? '-'}%</td></tr>
            <tr><th>Paso entre Rastreles / Apoyos</th><td>${p.installation.battenDistanceMinMm ? `De ${p.installation.battenDistanceMinMm} a ${p.installation.battenDistanceMaxMm} mm` : 'Apoyo continuo / Según retícula'}</td></tr>
            <tr><th>Sistema de Fijación</th><td>${p.installation.fixingSystem}</td></tr>
            <tr><th>Tasa de Fijación</th><td>${p.installation.fixingsPerUnit || '-'}</td></tr>
            <tr><th>Reglas de Compatibilidad</th><td><ul class="bim-ds-list">${(p.installation.compatibilityRules || []).map((r) => `<li>${r}</li>`).join('')}</ul></td></tr>
            <tr><th>Instrucciones de Montaje</th><td>${p.installation.instructionsSummary || ''}</td></tr>
          </table>
        </div>
      </div>

      <!-- 3.5. DOCUMENTACIÓN Y ENLACES OFICIALES -->
      <div class="bim-ds-section" style="margin-top:14px;">
        <h4>3.5. Documentación Oficial, Enlaces Verificados y Formato BIM/CAD</h4>
        <div class="bim-ds-footer" style="margin-top:6px;padding-top:6px;border-top:none;">
          <div class="bim-ds-links">
            <a href="${p.documentation.productUrl}" target="_blank" rel="noopener noreferrer" class="bim-doc-link primary">
              🌐 Página Oficial del Producto (${p.manufacturerName})
            </a>
            <a href="${p.documentation.datasheetPdfUrl}" target="_blank" rel="noopener noreferrer" class="bim-doc-link">
              📄 Catálogo / Ficha Técnica Oficial
            </a>
            <a href="${p.documentation.installationGuideUrl}" target="_blank" rel="noopener noreferrer" class="bim-doc-link">
              🛠️ Manual de Instalación del Fabricante
            </a>
          </div>
          <div class="bim-ds-bimformat">
            Formato BIM/CAD: <strong>${p.documentation.bimCadFormat}</strong>
          </div>
        </div>
      </div>
    `;

    modal.hidden = false;
  }

  /**
   * Abre el Explorador del Catálogo General con filtros reales (Sección 2 y Sección 5).
   */
  openCatalogExplorerModal(preselectFamilyId = null, preselectRole = null) {
    const modal = document.getElementById('bim-catalog-modal');
    const bodyEl = document.getElementById('bim-cat-body');
    if (!modal || !bodyEl) return;

    if (preselectFamilyId) this.catalogFilter.familyId = preselectFamilyId;

    const renderCatalogContent = () => {
      const allProds = this.store.getAllProducts();
      const filtered = allProds.filter((p) => {
        if (preselectRole && p.role !== preselectRole) return false;
        if (this.catalogFilter.familyId !== 'ALL' && p.familyId !== this.catalogFilter.familyId) return false;
        if (this.catalogFilter.manufacturerId !== 'ALL' && p.manufacturerId !== this.catalogFilter.manufacturerId) return false;
        if (this.catalogFilter.search.trim()) {
          const q = this.catalogFilter.search.toLowerCase();
          const match =
            p.model.toLowerCase().includes(q) ||
            p.manufacturerName.toLowerCase().includes(q) ||
            p.brand.toLowerCase().includes(q) ||
            p.refCode.toLowerCase().includes(q) ||
            p.applicationSystem.toLowerCase().includes(q);
          if (!match) return false;
        }
        return true;
      });

      bodyEl.innerHTML = `
        <div class="bim-cat-filters">
          <input type="search" id="bim-cat-search" placeholder="🔍 Buscar por fabricante, modelo, código, norma UNE-EN..." value="${this.catalogFilter.search}">
          <select id="bim-cat-family">
            <option value="ALL">Todas las Familias (A–L · ${allProds.length} productos)</option>
            ${BIM_FAMILIES.map(
              (f) =>
                `<option value="${f.id}" ${this.catalogFilter.familyId === f.id ? 'selected' : ''}>Familia ${f.code}. ${f.name}</option>`
            ).join('')}
          </select>
          <select id="bim-cat-mfg">
            <option value="ALL">Todos los Fabricantes (${Object.keys(BIM_MANUFACTURERS).length})</option>
            ${Object.values(BIM_MANUFACTURERS)
              .map(
                (m) =>
                  `<option value="${m.id}" ${this.catalogFilter.manufacturerId === m.id ? 'selected' : ''}>${m.name} (${m.country})</option>`
              )
              .join('')}
          </select>
        </div>

        <div class="bim-cat-mfg-directory">
          <span>Directorio Oficial de Fabricantes Integrados:</span>
          <div class="bim-mfg-chips">
            ${Object.values(BIM_MANUFACTURERS)
              .map(
                (m) =>
                  `<a href="${m.url}" target="_blank" rel="noopener noreferrer" class="bim-mfg-chip" title="Abrir web oficial de ${m.name} (${m.url})">${m.name} ↗</a>`
              )
              .join('')}
          </div>
        </div>

        <div class="bim-cat-cards-grid">
          ${filtered
            .map((p) => {
              const vBadge = VERIFICATION_BADGES[p.verificationStatus] || VERIFICATION_BADGES.VERIFICADO_OFICIAL;
              const inCompare = this.compareQueue.includes(p.id);
              return `
                <div class="bim-prod-card">
                  <div class="bim-pc-top">
                    <span class="bim-pc-mfg">${p.manufacturerName}</span>
                    <span class="bim-verif-pill" style="color:${vBadge.color};background:${vBadge.bg}">${vBadge.icon} ${vBadge.label}</span>
                  </div>
                  <h4 class="bim-pc-title">${p.model}</h4>
                  <div class="bim-pc-ref">Ref: <code>${p.refCode}</code> · ${p.versionDoc}</div>
                  <div class="bim-pc-specs">
                    <span>📐 ${p.geometry.lengthNominalMm}×${p.geometry.widthNominalMm}×${p.geometry.thicknessMm} mm</span>
                    <span>⚖️ ${p.geometry.unitWeightKg} kg/ud ${p.geometry.surfaceWeightKgM2 ? `(${p.geometry.surfaceWeightKgM2} kg/m²)` : ''}</span>
                    <span>⛰️ Pend. mín: ${p.installation.minSlopePct ?? 0}%</span>
                  </div>
                  <div class="bim-pc-actions">
                    <button class="bim-pc-btn" data-open-ds="${p.id}">📄 Ficha Oficial</button>
                    <button class="bim-pc-btn ${inCompare ? 'active' : ''}" data-toggle-cmp="${p.id}">
                      ${inCompare ? '✓ En Comparador' : '⚖️ Comparar'}
                    </button>
                    <button class="bim-pc-btn primary" data-apply-model="${p.id}">✅ Usar en 3D</button>
                  </div>
                </div>
              `;
            })
            .join('')}
        </div>
      `;

      bodyEl.querySelector('#bim-cat-search')?.addEventListener('input', (e) => {
        this.catalogFilter.search = e.target.value;
        renderCatalogContent();
        const input = bodyEl.querySelector('#bim-cat-search');
        if (input) {
          input.focus();
          input.setSelectionRange(input.value.length, input.value.length);
        }
      });

      bodyEl.querySelector('#bim-cat-family')?.addEventListener('change', (e) => {
        this.catalogFilter.familyId = e.target.value;
        preselectRole = null;
        renderCatalogContent();
      });

      bodyEl.querySelector('#bim-cat-mfg')?.addEventListener('change', (e) => {
        this.catalogFilter.manufacturerId = e.target.value;
        preselectRole = null;
        renderCatalogContent();
      });

      bodyEl.querySelectorAll('[data-open-ds]').forEach((btn) => {
        btn.addEventListener('click', () => this.openProductDatasheetModal(btn.dataset.openDs));
      });

      bodyEl.querySelectorAll('[data-toggle-cmp]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const id = btn.dataset.toggleCmp;
          if (this.compareQueue.includes(id)) {
            this.compareQueue = this.compareQueue.filter((x) => x !== id);
          } else {
            if (this.compareQueue.length >= 4) this.compareQueue.shift();
            this.compareQueue.push(id);
          }
          renderCatalogContent();
        });
      });

      bodyEl.querySelectorAll('[data-apply-model]').forEach((btn) => {
        btn.addEventListener('click', () => {
          this._applyProductToActiveModel(btn.dataset.applyModel);
          modal.hidden = true;
        });
      });
    };

    renderCatalogContent();
    modal.hidden = false;
  }

  _applyProductToActiveModel(productId) {
    const p = this.store.getProductById(productId);
    if (!p) return;

    const slopedRoles = {
      roof_covering: 'coveringId',
      batten_system: 'battenSystemId',
      support_panel: 'supportPanelId',
      fastener: 'fastenerId',
      gutter_unit: 'gutterId',
    };
    const flatRoles = {
      waterproofing: 'waterproofingId',
      insulation: 'insulationId',
      separator: 'separatorBotId',
      drainage_layer: 'drainageLayerId',
      plots: 'plotsId',
      pavement: 'pavementId',
      green_roof_system: 'greenRoofId',
      drain_unit: 'drainUnitId',
    };

    if (p.role in slopedRoles) {
      this.activeDemoId = 'demoA_tejado';
      const slot = slopedRoles[p.role];
      this.demoConfigs.demoA_tejado.selectedProducts[slot] = p.id;
      if (slot === 'coveringId') {
        delete this.demoConfigs.demoA_tejado.geometry.customBattenStepMm;
      }
    } else if (p.role in flatRoles) {
      this.activeDemoId = 'demoB_azotea';
      const slot = flatRoles[p.role];
      this.demoConfigs.demoB_azotea.selectedProducts[slot] = p.id;
      if (p.role === 'green_roof_system') {
        this.demoConfigs.demoB_azotea.roofSubType = 'ajardinada';
      }
    }

    // Actualizar botones de demo en la interfaz
    document.querySelectorAll('.bim-demo-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.demo === this.activeDemoId);
    });
    this.recalculateAndRenderAll();
  }

  /**
   * Abre el Comparador Técnico lado a lado (Sección 5).
   */
  openComparatorModal() {
    const modal = document.getElementById('bim-comparator-modal');
    const bodyEl = document.getElementById('bim-comp-body');
    if (!modal || !bodyEl) return;

    const prods = this.compareQueue.map((id) => this.store.getProductById(id)).filter(Boolean);
    const allProds = this.store.getAllProducts();

    const renderComp = () => {
      bodyEl.innerHTML = `
        <div class="bim-comp-toolbar">
          <span>Añadir producto a la tabla comparativa (máx. 4):</span>
          <select id="bim-comp-add-sel">
            ${allProds
              .map((p) => `<option value="${p.id}">[${p.manufacturerName}] ${p.model}</option>`)
              .join('')}
          </select>
          <button class="bim-mini-btn" id="bim-comp-add-btn">+ Añadir a Comparación</button>
        </div>

        <div class="bim-comp-table-wrap">
          <table class="bim-comp-table">
            <thead>
              <tr>
                <th>Parámetro Técnico Verificado</th>
                ${prods
                  .map(
                    (p) => `
                  <th>
                    <div class="bim-ct-head">
                      <span>${p.manufacturerName}</span>
                      <strong>${p.model}</strong>
                      <button class="bim-ct-rm" data-rm-cmp="${p.id}">Quitar ✕</button>
                    </div>
                  </th>
                `
                  )
                  .join('')}
              </tr>
            </thead>
            <tbody>
              <tr><th>Referencia Comercial</th>${prods.map((p) => `<td><code>${p.refCode}</code></td>`).join('')}</tr>
              <tr><th>Sistema Constructivo</th>${prods.map((p) => `<td>${p.applicationSystem}</td>`).join('')}</tr>
              <tr><th>Dimensiones Nominales (mm)</th>${prods.map((p) => `<td><strong>${p.geometry.lengthNominalMm} × ${p.geometry.widthNominalMm} × ${p.geometry.thicknessMm} mm</strong></td>`).join('')}</tr>
              <tr><th>Dimensiones Útiles (mm)</th>${prods.map((p) => `<td>${p.geometry.usefulLengthNominalMm || '-'} × ${p.geometry.usefulWidthMm || '-'} mm</td>`).join('')}</tr>
              <tr><th>Solape Oficial (Long / Trans)</th>${prods.map((p) => `<td>${p.geometry.overlapLongMinMm ?? '-'} mm / ${p.geometry.overlapTransMm ?? '-'} mm</td>`).join('')}</tr>
              <tr><th>Peso Unitario / Superficial</th>${prods.map((p) => `<td>${p.geometry.unitWeightKg} kg/ud (${p.geometry.surfaceWeightKgM2 || '-'} kg/m²)</td>`).join('')}</tr>
              <tr><th>Pendiente Mínima / Recom.</th>${prods.map((p) => `<td><strong>${p.installation.minSlopePct ?? 0}%</strong> / ${p.installation.recommendedSlopePct ?? '-'}%</td>`).join('')}</tr>
              <tr><th>Paso de Rastrel Admisible</th>${prods.map((p) => `<td>${p.installation.battenDistanceMinMm ? `${p.installation.battenDistanceMinMm}–${p.installation.battenDistanceMaxMm} mm` : 'Apoyo continuo'}</td>`).join('')}</tr>
              <tr><th>Material y Composición</th>${prods.map((p) => `<td>${p.technicalSpecs.material}</td>`).join('')}</tr>
              <tr><th>Reacción al Fuego</th>${prods.map((p) => `<td>${p.technicalSpecs.fireReaction || '-'}</td>`).join('')}</tr>
              <tr><th>Normativa UNE / EN / CTE</th>${prods.map((p) => `<td>${(p.technicalSpecs.standards || []).join(', ')}</td>`).join('')}</tr>
              <tr><th>Documentación Oficial</th>${prods.map((p) => `<td><a href="${p.documentation.productUrl}" target="_blank" rel="noopener">Web Oficial ↗</a></td>`).join('')}</tr>
            </tbody>
          </table>
        </div>
      `;

      bodyEl.querySelector('#bim-comp-add-btn')?.addEventListener('click', () => {
        const selId = bodyEl.querySelector('#bim-comp-add-sel')?.value;
        if (selId && !this.compareQueue.includes(selId)) {
          if (this.compareQueue.length >= 4) this.compareQueue.shift();
          this.compareQueue.push(selId);
          this.openComparatorModal();
        }
      });

      bodyEl.querySelectorAll('[data-rm-cmp]').forEach((btn) => {
        btn.addEventListener('click', () => {
          this.compareQueue = this.compareQueue.filter((x) => x !== btn.dataset.rmCmp);
          this.openComparatorModal();
        });
      });
    };

    renderComp();
    modal.hidden = false;
  }

  /**
   * Abre el Administrador del Catálogo BIM para Alta/Edición de Productos y Control de Versiones (Sección 14).
   */
  openAdminProductModal() {
    const modal = document.getElementById('bim-admin-modal');
    const bodyEl = document.getElementById('bim-admin-body');
    if (!modal || !bodyEl) return;

    const allProds = this.store.getAllProducts();

    bodyEl.innerHTML = `
      <div class="bim-admin-grid">
        <div class="bim-admin-form-box">
          <h4>Alta o Actualización de Producto Comercial</h4>
          <p class="bim-admin-note">
            Todo producto incorporado registra su estado de verificación (<code>VERIFICADO_OFICIAL</code>, <code>CALCULADO_PARAMETRICO</code> o <code>PENDIENTE_DOCUMENTACION</code>) y conserva el historial de versiones de ficha técnica.
          </p>
          <div class="bim-form-row">
            <label>Cargar producto existente para editar:
              <select id="adm-load-existing">
                <option value="">-- Crear Nuevo Producto Comercial --</option>
                ${allProds.map((p) => `<option value="${p.id}">[${p.manufacturerName}] ${p.model} (${p.id})</option>`).join('')}
              </select>
            </label>
          </div>
          <div class="bim-form-row">
            <label>ID Único BIM
              <input type="text" id="adm-id" placeholder="Ej: TERREAL-TB10-2025">
            </label>
            <label>Familia Constructiva
              <select id="adm-family">
                ${BIM_FAMILIES.map((f) => `<option value="${f.id}">Familia ${f.code} — ${f.name}</option>`).join('')}
              </select>
            </label>
          </div>
          <div class="bim-form-row">
            <label>Fabricante
              <input type="text" id="adm-mfg" placeholder="Ej: Terreal / BMI Cobert">
            </label>
            <label>Modelo Comercial Oficial
              <input type="text" id="adm-model" placeholder="Ej: Teja Mixta Duna / Klinker">
            </label>
          </div>
          <div class="bim-form-row">
            <label>Código / Referencia
              <input type="text" id="adm-ref" placeholder="Ej: TR-DUNA-450">
            </label>
            <label>Rol en Ensamblador 3D
              <select id="adm-role">
                <option value="roof_covering">Cobertura de Tejado (roof_covering)</option>
                <option value="batten_system">Rastrel / Soporte (batten_system)</option>
                <option value="support_panel">Panel Sándwich Madera (support_panel)</option>
                <option value="waterproofing">Impermeabilización (waterproofing)</option>
                <option value="insulation">Aislamiento Térmico (insulation)</option>
                <option value="separator">Geotextil Separador (separator)</option>
                <option value="plots">Plots Regulables (plots)</option>
                <option value="pavement">Pavimento 20mm (pavement)</option>
                <option value="drain_unit">Cazoleta / Sumidero (drain_unit)</option>
              </select>
            </label>
          </div>
          <div class="bim-form-row">
            <label>Largo Nominal (mm)
              <input type="number" id="adm-len" value="450">
            </label>
            <label>Ancho Nominal (mm)
              <input type="number" id="adm-wid" value="280">
            </label>
            <label>Espesor / Altura (mm)
              <input type="number" step="0.5" id="adm-thick" value="15">
            </label>
          </div>
          <div class="bim-form-row">
            <label>Largo Útil / Paso Rastrel (mm)
              <input type="number" id="adm-ulen" value="375">
            </label>
            <label>Ancho Útil (mm)
              <input type="number" id="adm-uwid" value="235">
            </label>
            <label>Peso Unitario (kg)
              <input type="number" step="0.1" id="adm-weight" value="3.6">
            </label>
          </div>
          <div class="bim-form-row">
            <label>Pendiente Mínima (%)
              <input type="number" id="adm-slope" value="30">
            </label>
            <label>Estado de Verificación Documental
              <select id="adm-verif">
                <option value="VERIFICADO_OFICIAL">VERIFICADO_OFICIAL (Ficha técnica verificada)</option>
                <option value="CALCULADO_PARAMETRICO">CALCULADO_PARAMETRICO (Derivado geométricamente)</option>
                <option value="PENDIENTE_DOCUMENTACION">PENDIENTE_DOCUMENTACION (Pendiente de ficha PDF)</option>
              </select>
            </label>
          </div>
          <div class="bim-form-row">
            <label>Versión Ficha Técnica / DoP
              <input type="text" id="adm-docver" value="Ficha Técnica Oficial 2025">
            </label>
            <label>URL Oficial del Fabricante
              <input type="url" id="adm-url" value="https://www.terreal.com">
            </label>
          </div>
          <div class="bim-admin-actions">
            <button class="bim-action-btn primary" id="adm-save-btn">💾 Guardar Producto en Catálogo BIM</button>
            <span id="adm-save-feedback"></span>
          </div>
        </div>
      </div>
    `;

    const loadSel = bodyEl.querySelector('#adm-load-existing');
    loadSel?.addEventListener('change', () => {
      const p = this.store.getProductById(loadSel.value);
      if (!p) return;
      bodyEl.querySelector('#adm-id').value = p.id;
      bodyEl.querySelector('#adm-family').value = p.familyId;
      bodyEl.querySelector('#adm-mfg').value = p.manufacturerName;
      bodyEl.querySelector('#adm-model').value = p.model;
      bodyEl.querySelector('#adm-ref').value = p.refCode;
      bodyEl.querySelector('#adm-role').value = p.role;
      bodyEl.querySelector('#adm-len').value = p.geometry.lengthNominalMm || 450;
      bodyEl.querySelector('#adm-wid').value = p.geometry.widthNominalMm || 280;
      bodyEl.querySelector('#adm-thick').value = p.geometry.thicknessMm || 15;
      bodyEl.querySelector('#adm-ulen').value = p.geometry.usefulLengthNominalMm || 375;
      bodyEl.querySelector('#adm-uwid').value = p.geometry.usefulWidthMm || 235;
      bodyEl.querySelector('#adm-weight').value = p.geometry.unitWeightKg || 3.5;
      bodyEl.querySelector('#adm-slope').value = p.installation.minSlopePct || 25;
      bodyEl.querySelector('#adm-verif').value = p.verificationStatus;
      bodyEl.querySelector('#adm-docver').value = p.versionDoc;
      bodyEl.querySelector('#adm-url').value = p.documentation.productUrl;
    });

    bodyEl.querySelector('#adm-save-btn')?.addEventListener('click', () => {
      const id = bodyEl.querySelector('#adm-id').value.trim() || `CUSTOM-${Date.now()}`;
      const existing = this.store.getProductById(id);
      const len = Number(bodyEl.querySelector('#adm-len').value) || 450;
      const wid = Number(bodyEl.querySelector('#adm-wid').value) || 280;
      const thick = Number(bodyEl.querySelector('#adm-thick').value) || 15;
      const ulen = Number(bodyEl.querySelector('#adm-ulen').value) || len - 75;
      const uwid = Number(bodyEl.querySelector('#adm-uwid').value) || wid - 40;
      const weight = Number(bodyEl.querySelector('#adm-weight').value) || 3.5;
      const unitsM2 = Number((1e6 / (ulen * uwid)).toFixed(2));

      const newProd = {
        ...(existing || {}),
        id,
        familyId: bodyEl.querySelector('#adm-family').value,
        manufacturerId: 'CUSTOM',
        manufacturerName: bodyEl.querySelector('#adm-mfg').value.trim() || 'Fabricante Registrado',
        brand: bodyEl.querySelector('#adm-mfg').value.trim() || 'Marca Comercial',
        model: bodyEl.querySelector('#adm-model').value.trim() || 'Modelo Personalizado',
        refCode: bodyEl.querySelector('#adm-ref').value.trim() || id,
        role: bodyEl.querySelector('#adm-role').value,
        subType: existing?.subType || 'teja_mixta',
        applicationSystem: existing?.applicationSystem || 'Sistema constructivo de cubierta',
        country: existing?.country || 'España / UE',
        availability: 'En comercialización activa',
        verificationStatus: bodyEl.querySelector('#adm-verif').value,
        versionDoc: bodyEl.querySelector('#adm-docver').value.trim(),
        revisionDate: new Date().toISOString().slice(0, 7),
        colorHex: existing?.colorHex || '#c2593f',
        textureKey: existing?.textureKey || 'terracotta',
        geometry: {
          ...(existing?.geometry || {}),
          lengthNominalMm: len,
          widthNominalMm: wid,
          thicknessMm: thick,
          usefulLengthNominalMm: ulen,
          usefulWidthMm: uwid,
          overlapLongMinMm: Math.max(0, len - ulen),
          overlapTransMm: Math.max(0, wid - uwid),
          unitsPerM2: unitsM2,
          unitWeightKg: weight,
          surfaceWeightKgM2: Number((unitsM2 * weight).toFixed(1)),
          shape3D: existing?.geometry?.shape3D || 'mixed_interlocking_tile',
        },
        technicalSpecs: existing?.technicalSpecs || {
          material: 'Producto comercial registrado en catálogo BIM ETSIE',
          mechanicalStrength: 'Conforme a norma europea UNE-EN de producto',
          fireReaction: 'Euroclase A1 / Broof(t1)',
          standards: ['CTE DB-HS 1', 'Marcado CE'],
        },
        installation: {
          ...(existing?.installation || {}),
          minSlopePct: Number(bodyEl.querySelector('#adm-slope').value) || 25,
          minSlopeDeg: 14,
          recommendedSlopePct: (Number(bodyEl.querySelector('#adm-slope').value) || 25) + 5,
          battenDistanceMinMm: Math.max(50, ulen - 15),
          battenDistanceMaxMm: ulen + 10,
          fixingSystem: existing?.installation?.fixingSystem || 'Fijación mecánica según ficha técnica oficial',
          compatibilityRules: existing?.installation?.compatibilityRules || ['Respetar solapes y pendiente mínima del fabricante'],
        },
        documentation: {
          productUrl: bodyEl.querySelector('#adm-url').value.trim() || 'https://www.upv.es',
          datasheetPdfUrl: bodyEl.querySelector('#adm-url').value.trim() || 'https://www.upv.es',
          installationGuideUrl: bodyEl.querySelector('#adm-url').value.trim() || 'https://www.upv.es',
          bimCadFormat: 'Objeto Paramétrico 3D BIM ETSIE',
        },
      };

      this.store.upsertProduct(newProd);
      const fb = bodyEl.querySelector('#adm-save-feedback');
      if (fb) fb.textContent = `✅ Producto ${newProd.id} guardado correctamente con control de versión.`;
      this.recalculateAndRenderAll();
    });

    modal.hidden = false;
  }

  // ===========================================================================
  // GENERADOR DE DOCUMENTACIÓN TÉCNICA: INFORME PDF/IMPRESIÓN, CSV Y JSON (SECCIÓN 13)
  // ===========================================================================
  exportTechnicalReportPDF() {
    if (!this.currentReplanteo || !this.currentCompatibility) return;
    const rep = this.currentReplanteo;
    const compat = this.currentCompatibility;
    const win = window.open('', '_blank');
    if (!win) return;

    const rowsHtml = rep.lineItems
      .map(
        (item) => `
        <tr>
          <td><strong>${item.roleLabel}</strong></td>
          <td>${item.manufacturerName}<br><strong>${item.model}</strong><br><small>Ref: ${item.refCode}</small></td>
          <td>${item.dimensionsStr}</td>
          <td>${item.theoreticalQty} ${item.unit}</td>
          <td><strong>${item.assemblyQty}</strong></td>
          <td><strong>${item.orderQty}</strong></td>
          <td>${item.totalWeightKg} kg</td>
        </tr>
      `
      )
      .join('');

    const compatHtml = compat.alerts
      .map(
        (a) => `
        <div class="alert ${a.severity}">
          <strong>[${a.severity.toUpperCase()}] ${a.problem}</strong><br>
          <span>Parámetro: ${a.affectedParam} | Fuente: ${a.source}</span><br>
          <em>Acción / Verificación: ${a.solution}</em>
        </div>
      `
      )
      .join('');

    win.document.write(`
      <!DOCTYPE html>
      <html lang="es">
      <head>
        <meta charset="UTF-8">
        <title>Informe Técnico BIM — Construcción II ETSIE UPV</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; color: #1e293b; margin: 28px; line-height: 1.45; }
          .header { border-bottom: 3px solid #0284c7; padding-bottom: 12px; margin-bottom: 18px; display: flex; justify-content: space-between; }
          h1 { font-size: 20px; margin: 0 0 4px 0; color: #0f172a; }
          h2 { font-size: 15px; color: #0284c7; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 20px; }
          table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }
          th, td { border: 1px solid #cbd5e1; padding: 7px 9px; text-align: left; }
          th { background: #f1f5f9; }
          .kpis { display: flex; gap: 16px; margin: 12px 0; }
          .kpi { border: 1px solid #cbd5e1; padding: 10px 14px; border-radius: 6px; background: #f8fafc; flex: 1; }
          .alert { padding: 8px 12px; border-radius: 5px; margin-bottom: 8px; font-size: 12px; border-left: 4px solid #10b981; background: #f0fdf4; }
          .alert.error { border-left-color: #ef4444; background: #fef2f2; }
          .alert.warning { border-left-color: #f59e0b; background: #fffbeb; }
          @media print { .no-print { display: none; } }
        </style>
      </head>
      <body>
        <div class="no-print" style="margin-bottom:16px;">
          <button onclick="window.print()" style="padding:8px 16px;background:#0284c7;color:#fff;border:none;border-radius:4px;cursor:pointer;font-weight:bold;">
            🖨️ Imprimir o Guardar como PDF
          </button>
        </div>
        <div class="header">
          <div>
            <h1>UNIVERSITAT POLITÈCNICA DE VALÈNCIA · ETSIE</h1>
            <div>Construcción II — Informe Técnico de Especificación Comercial BIM y Replanteo de Cubierta</div>
          </div>
          <div style="text-align:right;font-size:12px;">
            Fecha: ${new Date().toLocaleDateString('es-ES')}<br>
            Sistema: <strong>${rep.systemType.toUpperCase()}</strong>
          </div>
        </div>

        <div class="kpis">
          <div class="kpi">
            <div>Superficie de Cálculo</div>
            <strong style="font-size:18px;">${rep.geometry.realAreaM2 || rep.geometry.flatAreaM2} m²</strong>
            <div>Pendiente: ${rep.geometry.slopePct}%</div>
          </div>
          <div class="kpi">
            <div>Peso Total de la Cubierta</div>
            <strong style="font-size:18px;">${rep.summary.totalWeightKg} kg</strong>
            <div>Carga superficial: ${rep.summary.weightPerM2Kg} kg/m²</div>
          </div>
          <div class="kpi">
            <div>Transmitancia Térmica Estimada</div>
            <strong style="font-size:18px;">U = ${rep.summary.uValueWmk} W/m²K</strong>
            <div>Merma considerada: ${rep.geometry.wastePct}%</div>
          </div>
        </div>

        <h2>1. Cuadro de Materiales, Fabricantes, Modelos y Mediciones de Replanteo</h2>
        <table>
          <thead>
            <tr>
              <th>Orden / Capa</th>
              <th>Fabricante y Modelo Oficial</th>
              <th>Dimensiones y Parámetros</th>
              <th>Cantidad Teórica</th>
              <th>Cantidad Montaje</th>
              <th>Pedido (+${rep.geometry.wastePct}%)</th>
              <th>Peso Total</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>

        <h2>2. Auditoría del Motor de Compatibilidad Constructiva y Normativa CTE</h2>
        ${compatHtml}

        <h2>3. Enlaces Oficiales a Fichas Técnicas de los Fabricantes Seleccionados</h2>
        <ul>
          ${Object.values(rep.products)
            .map(
              (p) =>
                `<li><strong>${p.manufacturerName} — ${p.model}</strong> (${p.versionDoc}): <a href="${p.documentation.productUrl}">${p.documentation.productUrl}</a></li>`
            )
            .join('')}
        </ul>
      </body>
      </html>
    `);
    win.document.close();
  }

  exportBoqCSV() {
    if (!this.currentReplanteo) return;
    const rep = this.currentReplanteo;
    const headers = [
      'Orden',
      'Funcion_Constructiva',
      'ID_BIM',
      'Fabricante',
      'Modelo_Comercial',
      'Referencia',
      'Dimensiones',
      'Unidad',
      'Cantidad_Teorica',
      'Cantidad_Montaje',
      'Cantidad_Pedido',
      'Peso_Unitario_kg',
      'Peso_Total_kg',
    ];
    const lines = [headers.join(';')];
    rep.lineItems.forEach((it) => {
      lines.push(
        [
          it.layerOrder,
          `"${it.roleLabel}"`,
          it.productId,
          `"${it.manufacturerName}"`,
          `"${it.model}"`,
          it.refCode,
          `"${it.dimensionsStr}"`,
          `"${it.unit}"`,
          it.theoreticalQty,
          it.assemblyQty,
          `"${it.orderQty}"`,
          it.unitWeightKg,
          it.totalWeightKg,
        ].join(';')
      );
    });
    const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Mediciones_BIM_${rep.systemType}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  exportProjectJSON() {
    if (!this.currentReplanteo) return;
    const data = {
      project: 'ROOFLAB ETSIE · BIBLIOTECA BIM DE PRODUCTOS REALES',
      exportedAt: new Date().toISOString(),
      activeDemoId: this.activeDemoId,
      replanteo: this.currentReplanteo,
      compatibility: this.currentCompatibility,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Proyecto_BIM_Cubierta_${this.activeDemoId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
