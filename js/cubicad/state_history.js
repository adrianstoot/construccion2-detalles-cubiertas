/**
 * =============================================================================
 * CubiCAD · Constructor CAD/BIM de Cubiertas
 * Motor de Estado Paramétrico, Historial CAD (Ctrl+Z / Ctrl+Mayús+Z),
 * Portapapeles (Ctrl+C / Ctrl+V) y Selección Múltiple / Zona
 * =============================================================================
 */

export const TYPOLOGY_PRESETS = {
  tejado: {
    id: 'tejado',
    name: 'Tejado Inclinado',
    buildingLabel: 'Vivienda Unifamiliar Aislada (2 Plantas)',
    variants: [
      { id: 'dos_aguas', label: 'Dos Aguas (Cumbrera central)', desc: 'Faldones simétricos con hastiales y canalón en ambos aleros' },
      { id: 'cuatro_aguas', label: 'Cuatro Aguas (4 Limatesas)', desc: 'Cubierta a cuatro vertientes con limatesas a 45°' },
      { id: 'planta_L', label: 'Planta en L (Limahoya y Limatesa)', desc: 'Volumen compuesto en L con encuentro real de limahoya y doble cumbrera' },
      { id: 'asimetrica', label: 'Asimétrica (Cumbrera desplazable)', desc: 'Faldones de distinta longitud editables en vivo desde la cumbrera' },
    ],
    defaultState: {
      typology: 'tejado',
      variant: 'dos_aguas',
      geometry: {
        lengthM: 10.4,
        widthM: 8.2,
        slopePct: 32,
        eaveOverhangM: 0.45,
        ridgeOffsetRatio: 0.0, // -0.25 a +0.25 para variante asimétrica
        wastePct: 5,
        customBattenStepMm: null,
        parapetTurnupMm: 200,
      },
      layersEnabled: {
        support: true,
        membrane: true,
        waterproofing: false,
        insulation: true,
        battens: true,
        covering: true,
        drainage: true,
      },
      products: {
        supportPanelId: 'THERMOCHIP-TAH-80',
        battenSystemId: 'ROTHOBLAAS-RASTREL-3050',
        coveringId: 'BORJA-C5021',
        fastenerId: 'SFS-CLIP-TEJA-INOX',
        gutterId: 'VMZINC-CANALON-333',
        insulationId: 'URSA-XPS-NIIIL-60',
        waterproofingId: 'DANOSA-ESTERDAN40P',
        separatorBotId: 'DANOSA-DANOFELT-PY200',
        plotsId: 'PEYGRAN-XSP5-PRO',
        pavementId: 'GRESARAGON-ORDESA-6060',
        greenRoofId: 'OPTIGRUN-FKD25',
        drainUnitId: 'JIMTEN-S77-110',
      },
      cadLines: [],
    },
  },

  azotea: {
    id: 'azotea',
    name: 'Azotea Plana',
    buildingLabel: 'Edificio Residencial Urbano (4 Plantas)',
    variants: [
      { id: 'invertida_plots', label: 'Invertida sobre Plots Regulables', desc: 'Impermeabilización + Geotextil + URSA XPS + Plots Peygran + Gres Aragón 20mm' },
      { id: 'convencional_fija', label: 'Convencional Pavimento Fijo', desc: 'Aislamiento inferior + Impermeabilización + Capa separadora + Pavimento recibido' },
      { id: 'ajardinada', label: 'Cubierta Ajardinada Extensiva', desc: 'Membrana antirraíces + Geotextil + XPS + Optigrün FKD 25 + Sustrato Sedum' },
    ],
    defaultState: {
      typology: 'azotea',
      variant: 'invertida_plots',
      geometry: {
        lengthM: 12.0,
        widthM: 9.6,
        slopePct: 2.0,
        parapetHeightM: 1.05,
        parapetTurnupMm: 220,
        wastePct: 5,
        drainPosX: -3.2,
        drainPosZ: -2.4,
      },
      layersEnabled: {
        support: true,
        membrane: true,
        waterproofing: true,
        insulation: true,
        battens: true, // En azotea representa Plots / Drenaje
        covering: true, // Pavimento Gres Aragón o Sedum Optigrün
        drainage: true, // Cazoleta Sifónica Jimten S-77
      },
      products: {
        supportPanelId: 'THERMOCHIP-TAH-80',
        battenSystemId: 'ROTHOBLAAS-RASTREL-3050',
        coveringId: 'BORJA-C5021',
        fastenerId: 'SFS-CLIP-TEJA-INOX',
        gutterId: 'VMZINC-CANALON-333',
        waterproofingId: 'DANOSA-ESTERDAN40P',
        separatorBotId: 'DANOSA-DANOFELT-PY200',
        insulationId: 'URSA-XPS-NIIIL-60',
        plotsId: 'PEYGRAN-XSP5-PRO',
        pavementId: 'GRESARAGON-ORDESA-6060',
        greenRoofId: 'OPTIGRUN-FKD25',
        drainUnitId: 'JIMTEN-S77-110',
      },
      cadLines: [],
    },
  },

  metalica: {
    id: 'metalica',
    name: 'Cubierta Metálica',
    buildingLabel: 'Pabellón Deportivo / Nave Industrial (Gran Luz)',
    variants: [
      { id: 'nave_dos_aguas', label: 'Nave Industrial (Dos Aguas Gran Luz)', desc: 'Pórticos metálicos IPE + Correas Z + Panel sándwich o Zinc junta alzada' },
      { id: 'club_un_agua', label: 'Pabellón Deportivo (Un Agua / Gran Vuelo)', desc: 'Cubierta inclinada contemporánea de largo faldón continuo en zinc o panel' },
      { id: 'diente_sierra', label: 'Nave Diente de Sierra (Shed Lucernario)', desc: 'Módulos repetidos con orientación norte acristalada y canalón intermedio' },
    ],
    defaultState: {
      typology: 'metalica',
      variant: 'nave_dos_aguas',
      geometry: {
        lengthM: 18.0,
        widthM: 12.6,
        slopePct: 12,
        eaveOverhangM: 0.55,
        ridgeOffsetRatio: 0.0,
        wastePct: 4,
        customBattenStepMm: null,
        parapetTurnupMm: 200,
      },
      layersEnabled: {
        support: true, // Correas / Entarimado metálico-madera
        membrane: true,
        waterproofing: false,
        insulation: true,
        battens: true, // Correas / Rastrelado de fijación
        covering: true, // VMZINC Junta Alzada / Kingspan KS1000 RW / Euronit
        drainage: true, // Canalón industrial + Patas inox
      },
      products: {
        supportPanelId: 'THERMOCHIP-TAH-80',
        battenSystemId: 'ROTHOBLAAS-RASTREL-3050',
        coveringId: 'VMZINC-JUNTA-ALZADA-500',
        fastenerId: 'VMZINC-PATAS-INOX',
        gutterId: 'VMZINC-CANALON-333',
        insulationId: 'URSA-XPS-NIIIL-60',
        waterproofingId: 'DANOSA-ESTERDAN40P',
        separatorBotId: 'DANOSA-DANOFELT-PY200',
        plotsId: 'PEYGRAN-XSP5-PRO',
        pavementId: 'GRESARAGON-ORDESA-6060',
        greenRoofId: 'OPTIGRUN-FKD25',
        drainUnitId: 'JIMTEN-S77-110',
      },
      cadLines: [],
    },
  },
};

/**
 * Gestor reactivo del estado del proyecto CubiCAD con soporte completo CAD:
 * Undo (Ctrl+Z), Redo (Ctrl+Mayús+Z), Copy/Paste (Ctrl+C/V) y Multiselección (Shift / Marquesina).
 */
export class CubiCADStateManager {
  constructor() {
    this.state = this._clone(TYPOLOGY_PRESETS.tejado.defaultState);
    this.undoStack = [];
    this.redoStack = [];
    this.maxHistory = 60;

    // Estado transitorio de herramientas CAD
    this.activeTool = 'select'; // 'select' | 'marquee' | 'move' | 'draw_line'
    this.activeLineType = 'cumbrera'; // 'cumbrera' | 'limatesa' | 'limahoya' | 'contorno'
    this.selectedIds = new Set(); // IDs de piezas 3D o líneas CAD seleccionadas
    this.selectedItemsMeta = []; // Metadatos completos de selección
    this.clipboard = null;

    this.listeners = [];
  }

  _clone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  subscribe(fn) {
    this.listeners.push(fn);
  }

  _emit(reason = 'update') {
    this.listeners.forEach((fn) => fn(this.state, reason));
  }

  /**
   * Guarda instantánea en historial antes de mutar el proyecto.
   */
  commit(mutatorFn, label = 'Cambio CAD') {
    this.undoStack.push({
      label,
      snapshot: this._clone(this.state),
    });
    if (this.undoStack.length > this.maxHistory) {
      this.undoStack.shift();
    }
    this.redoStack = [];
    mutatorFn(this.state);
    this._emit('commit');
  }

  canUndo() {
    return this.undoStack.length > 0;
  }

  canRedo() {
    return this.redoStack.length > 0;
  }

  undo() {
    if (!this.canUndo()) return false;
    const prev = this.undoStack.pop();
    this.redoStack.push({
      label: prev.label,
      snapshot: this._clone(this.state),
    });
    this.state = prev.snapshot;
    this.clearSelection();
    this._emit('undo');
    return true;
  }

  redo() {
    if (!this.canRedo()) return false;
    const next = this.redoStack.pop();
    this.undoStack.push({
      label: next.label,
      snapshot: this._clone(this.state),
    });
    this.state = next.snapshot;
    this.clearSelection();
    this._emit('redo');
    return true;
  }

  switchTypology(typologyId, startEmptyForTutorial = false) {
    const preset = TYPOLOGY_PRESETS[typologyId];
    if (!preset) return;
    this.commit((st) => {
      const fresh = this._clone(preset.defaultState);
      if (startEmptyForTutorial) {
        Object.keys(fresh.layersEnabled).forEach((k) => {
          fresh.layersEnabled[k] = false;
        });
      }
      Object.assign(st, fresh);
    }, `Cambiar tipología a ${preset.name}`);
    this.clearSelection();
  }

  /**
   * Vacía todas las capas de la cubierta actual para construir desde cero sobre el edificio base.
   */
  clearAllRoofLayers() {
    this.commit((st) => {
      Object.keys(st.layersEnabled).forEach((k) => {
        st.layersEnabled[k] = false;
      });
      st.cadLines = [];
    }, 'Limpiar capas para construir desde cero');
  }

  addCadLine(lineObj) {
    this.commit((st) => {
      const id = `CAD-${lineObj.type.toUpperCase()}-${st.cadLines.length + 1}`;
      st.cadLines.push({
        id,
        type: lineObj.type || this.activeLineType,
        p1: lineObj.p1,
        p2: lineObj.p2,
      });
    }, `Trazar ${lineObj.type}`);
  }

  setSelection(itemsMeta, appendWithShift = false) {
    if (!appendWithShift) {
      this.selectedIds.clear();
      this.selectedItemsMeta = [];
    }
    itemsMeta.forEach((meta) => {
      const key = meta.pieceCode || meta.id;
      if (!key) return;
      if (appendWithShift && this.selectedIds.has(key)) {
        this.selectedIds.delete(key);
        this.selectedItemsMeta = this.selectedItemsMeta.filter((m) => (m.pieceCode || m.id) !== key);
      } else if (!this.selectedIds.has(key)) {
        this.selectedIds.add(key);
        this.selectedItemsMeta.push(meta);
      }
    });
    this._emit('selection');
  }

  clearSelection() {
    this.selectedIds.clear();
    this.selectedItemsMeta = [];
    this._emit('selection');
  }

  copySelection() {
    if (this.selectedItemsMeta.length > 0) {
      // Si hay líneas CAD seleccionadas, copiarlas; si son capas, copiar su especificación comercial
      const selectedLineIds = new Set(
        this.selectedItemsMeta.filter((m) => m.isCadLine).map((m) => m.id)
      );
      if (selectedLineIds.size > 0) {
        const lines = this.state.cadLines.filter((l) => selectedLineIds.has(l.id));
        this.clipboard = { kind: 'cadLines', data: this._clone(lines) };
        return `Copiadas ${lines.length} línea(s) CAD`;
      }
      const first = this.selectedItemsMeta[0];
      this.clipboard = {
        kind: 'layerConfig',
        data: {
          layerKey: first.layerKey,
          productId: first.productId,
          products: this._clone(this.state.products),
          geometry: this._clone(this.state.geometry),
        },
      };
      return `Copiada configuración de ${first.layerName || first.pieceCode}`;
    }
    // Por defecto copiar paquete constructivo completo
    this.clipboard = {
      kind: 'fullRoofPack',
      data: {
        products: this._clone(this.state.products),
        layersEnabled: this._clone(this.state.layersEnabled),
      },
    };
    return 'Copiado paquete constructivo actual';
  }

  pasteClipboard() {
    if (!this.clipboard) return null;
    if (this.clipboard.kind === 'cadLines') {
      const copies = this.clipboard.data;
      this.commit((st) => {
        copies.forEach((ln) => {
          const id = `CAD-${ln.type.toUpperCase()}-${st.cadLines.length + 1}`;
          st.cadLines.push({
            id,
            type: ln.type,
            p1: { x: Number((ln.p1.x + 0.6).toFixed(2)), y: ln.p1.y, z: Number((ln.p1.z + 0.6).toFixed(2)) },
            p2: { x: Number((ln.p2.x + 0.6).toFixed(2)), y: ln.p2.y, z: Number((ln.p2.z + 0.6).toFixed(2)) },
          });
        });
      }, 'Pegar líneas CAD');
      return `Pegadas ${copies.length} línea(s) CAD (+0,60 m)`;
    }
    if (this.clipboard.kind === 'fullRoofPack' || this.clipboard.kind === 'layerConfig') {
      const pack = this.clipboard.data;
      this.commit((st) => {
        if (pack.products) st.products = { ...st.products, ...this._clone(pack.products) };
        if (pack.layersEnabled) st.layersEnabled = { ...st.layersEnabled, ...this._clone(pack.layersEnabled) };
      }, 'Pegar paquete constructivo');
      return 'Pegada especificación comercial en la cubierta';
    }
    return null;
  }

  deleteSelection() {
    if (this.selectedItemsMeta.length === 0) return false;
    const lineIds = new Set(this.selectedItemsMeta.filter((m) => m.isCadLine).map((m) => m.id));
    if (lineIds.size > 0) {
      this.commit((st) => {
        st.cadLines = st.cadLines.filter((l) => !lineIds.has(l.id));
      }, 'Eliminar líneas CAD');
      this.clearSelection();
      return true;
    }
    // Si selecciona una capa constructiva, la desactiva limpiamente (reversible con Ctrl+Z)
    const layerSlotMap = {
      L1_SOPORTE: 'support',
      L2_LAMINA: 'membrane',
      L3_IMPERMEABILIZACION: 'waterproofing',
      L4_AISLAMIENTO: 'insulation',
      L5_RASTRELES_PLOTS: 'battens',
      L6_COBERTURA: 'covering',
      L7_EVACUACION: 'drainage',
    };
    const slotsToTurnOff = new Set();
    this.selectedItemsMeta.forEach((m) => {
      if (m.layerKey && layerSlotMap[m.layerKey]) {
        slotsToTurnOff.add(layerSlotMap[m.layerKey]);
      }
    });
    if (slotsToTurnOff.size > 0) {
      this.commit((st) => {
        slotsToTurnOff.forEach((slot) => {
          st.layersEnabled[slot] = false;
        });
      }, 'Retirar capa seleccionada');
      this.clearSelection();
      return true;
    }
    return false;
  }
}
