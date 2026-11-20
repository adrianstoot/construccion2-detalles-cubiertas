/**
 * =============================================================================
 * CubiCAD · Constructor CAD/BIM de Cubiertas
 * Generador Instantáneo de Detalle Constructivo 2D Acotado (SVG Vectorial E 1:5)
 * =============================================================================
 * Genera en tiempo real la sección constructiva milimétrica de las capas
 * activas en el Constructor 3D, con rayados técnicos UNE, cotas en mm y
 * referencias comerciales oficiales de cada fabricante.
 */

export class CubiCADLiveDetail2D {
  /**
   * Devuelve el SVG completo (vectorial de resolución infinita) de la sección constructiva actual.
   */
  static buildSectionSVG(state, replanteo, darkMode = false) {
    const bg = darkMode ? '#0d1118' : '#ffffff';
    const ink = darkMode ? '#f1f5f9' : '#111827';
    const muted = darkMode ? '#94a3b8' : '#4b5563';
    const lineCol = darkMode ? '#334155' : '#cbd5e1';
    const accent = '#0071e3';

    const layers = this._collectOrderedLayers(state, replanteo);
    const totalThickMm = layers.reduce((acc, l) => acc + l.thickMm, 0);

    const W = 920;
    const H = 560;
    const isSloped = state.typology === 'tejado' || state.typology === 'metalica';
    const slopePct = state.geometry.slopePct || (isSloped ? 32 : 2);
    const slopeDeg = ((Math.atan(slopePct / 100) * 180) / Math.PI).toFixed(1);

    // Patrones técnicos normalizados UNE (rayados arquitectónicos)
    const defs = `
      <defs>
        <pattern id="hatch-conc" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="12" stroke="${muted}" stroke-width="0.9" opacity="0.55"/>
          <circle cx="6" cy="6" r="1.1" fill="${muted}" opacity="0.45"/>
        </pattern>
        <pattern id="hatch-xps" width="14" height="14" patternUnits="userSpaceOnUse">
          <path d="M0 7 Q3.5 1, 7 7 T14 7" fill="none" stroke="#b45309" stroke-width="1.1" opacity="0.7"/>
        </pattern>
        <pattern id="hatch-wood" width="16" height="8" patternUnits="userSpaceOnUse">
          <line x1="0" y1="4" x2="16" y2="4" stroke="#92400e" stroke-width="0.8" opacity="0.45"/>
          <path d="M2 2 Q8 6 14 2" fill="none" stroke="#92400e" stroke-width="0.6" opacity="0.35"/>
        </pattern>
        <pattern id="hatch-clay" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke="#9a3412" stroke-width="1" opacity="0.55"/>
        </pattern>
        <pattern id="hatch-metal" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="8" stroke="#475569" stroke-width="1.2" opacity="0.65"/>
        </pattern>
        <marker id="dim-arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 2 L 10 5 L 0 8 z" fill="${accent}"/>
        </marker>
      </defs>
    `;

    const titleText =
      state.typology === 'azotea'
        ? `SECCIÓN CONSTRUCTIVA 2D EN VIVO · AZOTEA (${state.variant.replace('_', ' ').toUpperCase()})`
        : state.typology === 'metalica'
        ? `SECCIÓN CONSTRUCTIVA 2D EN VIVO · CUBIERTA METÁLICA (${state.variant.replace('_', ' ').toUpperCase()})`
        : `SECCIÓN CONSTRUCTIVA 2D EN VIVO · TEJADO INCLINADO (${state.variant.replace('_', ' ').toUpperCase()})`;

    // Dibujar paquete de capas escalado limpiamente a la izquierda (x: 90..465) y leyendas acotadas a la derecha (x: 520..900)
    const x0 = 95;
    const secW = 360;
    const yBottom = 455;
    const maxDrawH = 310;
    const minLayerH = 16;

    // Calculamos alturas visuales proporcionales asegurando legibilidad incluso en láminas de 2-3 mm
    const rawTotal = layers.reduce((acc, l) => acc + Math.max(24, l.thickMm), 0) || 1;
    const scaleY = Math.min(1.45, maxDrawH / rawTotal);

    let cursorY = yBottom;
    let layersSvg = '';
    let calloutsSvg = '';

    // Base estructural resistente fija del edificio (Forjado / Pórtico)
    const baseH = 44;
    layersSvg += `
      <rect x="${x0}" y="${cursorY}" width="${secW}" height="${baseH}" fill="${darkMode ? '#1e293b' : '#e5e7eb'}" stroke="${ink}" stroke-width="1.6"/>
      <rect x="${x0}" y="${cursorY}" width="${secW}" height="${baseH}" fill="url(#hatch-conc)"/>
      <text x="${x0 + secW / 2}" y="${cursorY + 26}" text-anchor="middle" fill="${ink}" font-size="11" font-weight="700" font-family="monospace">
        SOPORTE RESISTENTE DEL EDIFICIO (HA-25 / PÓRTICO)
      </text>
    `;

    // En Azotea, dibujamos también el peto vertical a la izquierda con el remonte de la impermeabilización
    if (state.typology === 'azotea') {
      const petoW = 48;
      const petoH = 310;
      layersSvg += `
        <rect x="${x0 - petoW}" y="${yBottom - petoH + baseH}" width="${petoW}" height="${petoH}" fill="${darkMode ? '#1e293b' : '#e2e8f0'}" stroke="${ink}" stroke-width="1.6"/>
        <rect x="${x0 - petoW}" y="${yBottom - petoH + baseH}" width="${petoW}" height="${petoH}" fill="url(#hatch-conc)"/>
        <rect x="${x0 - petoW - 5}" y="${yBottom - petoH + baseH - 14}" width="${petoW + 10}" height="14" fill="${darkMode ? '#334155' : '#cbd5e1'}" stroke="${ink}" stroke-width="1.4"/>
        <text x="${x0 - petoW / 2}" y="${yBottom - petoH + baseH + 145}" text-anchor="middle" fill="${muted}" font-size="9.5" font-weight="700" transform="rotate(-90 ${x0 - petoW / 2} ${yBottom - petoH + baseH + 145})">
          PETO PERIMETRAL (h=${Math.round((state.geometry.parapetHeightM || 1.05) * 100)} cm)
        </text>
      `;
    }

    const activeCount = layers.length;
    if (activeCount === 0) {
      layersSvg += `
        <rect x="${x0 + 20}" y="${yBottom - 120}" width="${secW - 40}" height="74" rx="8" fill="${darkMode ? '#162032' : '#f1f5f9'}" stroke="${accent}" stroke-dasharray="6 4" stroke-width="1.5"/>
        <text x="${x0 + secW / 2}" y="${yBottom - 88}" text-anchor="middle" fill="${accent}" font-size="13" font-weight="700">
          Cubierta vacía sobre el soporte resistente
        </text>
        <text x="${x0 + secW / 2}" y="${yBottom - 68}" text-anchor="middle" fill="${muted}" font-size="11">
          Activa capas desde la paleta izquierda o inicia el Tutorial Guiado
        </text>
      `;
    } else {
      const calloutTopStart = 96;
      const calloutStepY = Math.min(62, 370 / Math.max(1, activeCount));

      layers.forEach((l, idx) => {
        const drawH = Math.max(minLayerH, Math.round(Math.max(24, l.thickMm) * scaleY));
        const yTop = cursorY - drawH;
        const yMid = yTop + drawH / 2;

        // Renderizado arquitectónico según el tipo constructivo de capa
        if (l.visualKind === 'plots') {
          // Dibujar 3 soportes regulables Peygran en sección + cámara de aire
          layersSvg += `<rect x="${x0}" y="${yTop}" width="${secW}" height="${drawH}" fill="${darkMode ? 'rgba(56,189,248,0.06)' : 'rgba(0,113,227,0.04)'}" stroke="${lineCol}" stroke-dasharray="4 3"/>`;
          [x0 + 48, x0 + secW / 2, x0 + secW - 48].forEach((px) => {
            layersSvg += `
              <rect x="${px - 22}" y="${cursorY - 5}" width="44" height="5" fill="#1f2937"/>
              <rect x="${px - 9}" y="${yTop + 5}" width="18" height="${Math.max(6, drawH - 10)}" fill="#334155" stroke="${ink}" stroke-width="1"/>
              <rect x="${px - 17}" y="${yTop}" width="34" height="5" fill="#16a34a"/>
            `;
          });
        } else if (l.visualKind === 'battens') {
          // Cámara ventilada + rastreles 30×50 mm
          layersSvg += `<rect x="${x0}" y="${yTop}" width="${secW}" height="${drawH}" fill="${darkMode ? 'rgba(251,191,36,0.06)' : 'rgba(251,191,36,0.08)'}" stroke="${lineCol}" stroke-dasharray="3 3"/>`;
          [x0 + 36, x0 + 135, x0 + 235, x0 + 325].forEach((bx) => {
            layersSvg += `<rect x="${bx - 14}" y="${yTop + 2}" width="28" height="${drawH - 4}" fill="#d9a05b" stroke="#78350f" stroke-width="1.2"/>
              <line x1="${bx - 14}" y1="${yTop + 2}" x2="${bx + 14}" y2="${cursorY - 2}" stroke="#78350f" stroke-width="0.9"/>
              <line x1="${bx + 14}" y1="${yTop + 2}" x2="${bx - 14}" y2="${cursorY - 2}" stroke="#78350f" stroke-width="0.9"/>`;
          });
        } else if (l.visualKind === 'tiles') {
          // Perfil ondulado / escalonado de tejas o cobertura
          let pathD = `M ${x0} ${cursorY}`;
          const segs = 6;
          const sw = secW / segs;
          for (let s = 0; s < segs; s++) {
            const sx = x0 + s * sw;
            pathD += ` Q ${sx + sw * 0.5} ${yTop - 6}, ${sx + sw} ${cursorY - drawH * 0.45}`;
          }
          pathD += ` L ${x0 + secW} ${cursorY} Z`;
          layersSvg += `<path d="${pathD}" fill="${l.fillColor}" stroke="${ink}" stroke-width="1.5"/>`;
        } else if (l.visualKind === 'pavers') {
          // Baldosas porcelánicas con juntas abiertas de 4 mm
          const nTiles = 3;
          const tw = (secW - 16) / nTiles;
          for (let t = 0; t < nTiles; t++) {
            const tx = x0 + 4 + t * (tw + 4);
            layersSvg += `<rect x="${tx}" y="${yTop}" width="${tw}" height="${drawH}" fill="${l.fillColor}" stroke="${ink}" stroke-width="1.4"/>`;
          }
        } else {
          layersSvg += `<rect x="${x0}" y="${yTop}" width="${secW}" height="${drawH}" fill="${l.fillColor}" stroke="${ink}" stroke-width="1.4"/>`;
          if (l.patternId) {
            layersSvg += `<rect x="${x0}" y="${yTop}" width="${secW}" height="${drawH}" fill="url(#${l.patternId})"/>`;
          }
        }

        // Si es impermeabilización en azotea, dibujar el remonte vertical contra el peto
        if (state.typology === 'azotea' && l.visualKind === 'waterproof') {
          const turnH = Math.min(110, (state.geometry.parapetTurnupMm || 200) * 0.45);
          layersSvg += `
            <polyline points="${x0},${yMid} ${x0 + 3},${yMid} ${x0 + 3},${yMid - turnH}" fill="none" stroke="#ef4444" stroke-width="3.2"/>
            <text x="${x0 + 10}" y="${yMid - turnH + 12}" fill="#ef4444" font-size="9.5" font-weight="700" font-family="monospace">
              REMONTE h=${state.geometry.parapetTurnupMm} mm (CTE ≥200)
            </text>
          `;
        }

        // Cota de espesor individual a la derecha inmediata de la sección
        const dimX = x0 + secW + 14;
        layersSvg += `
          <line x1="${dimX - 4}" y1="${yTop}" x2="${dimX + 4}" y2="${yTop}" stroke="${accent}" stroke-width="1"/>
          <line x1="${dimX - 4}" y1="${cursorY}" x2="${dimX + 4}" y2="${cursorY}" stroke="${accent}" stroke-width="1"/>
          <line x1="${dimX}" y1="${yTop}" x2="${dimX}" y2="${cursorY}" stroke="${accent}" stroke-width="1.1"/>
          <text x="${dimX + 7}" y="${yMid + 3}" fill="${accent}" font-size="9.5" font-weight="700" font-family="monospace">${l.thickLabel}</text>
        `;

        // Línea líder y caja de especificación comercial a la derecha
        const revIdx = activeCount - 1 - idx;
        const callY = calloutTopStart + revIdx * calloutStepY;
        const leaderX = x0 + secW + 66;
        calloutsSvg += `
          <circle cx="${x0 + secW - 12}" cy="${yMid}" r="3.2" fill="${accent}"/>
          <polyline points="${x0 + secW - 12},${yMid} ${leaderX - 8},${yMid} ${leaderX + 12},${callY + 14}" fill="none" stroke="${lineCol}" stroke-width="1.2"/>
          <rect x="${leaderX + 12}" y="${callY}" width="368" height="${Math.max(44, calloutStepY - 7)}" rx="6" fill="${darkMode ? '#141b26' : '#f8fafc'}" stroke="${lineCol}" stroke-width="1"/>
          <rect x="${leaderX + 12}" y="${callY}" width="5" height="${Math.max(44, calloutStepY - 7)}" rx="2" fill="${l.badgeColor}"/>
          <text x="${leaderX + 25}" y="${callY + 15}" fill="${ink}" font-size="11" font-weight="700">
            ${idx + 1}. ${this._esc(l.title)}
          </text>
          <text x="${leaderX + 25}" y="${callY + 29}" fill="${accent}" font-size="10" font-weight="600">
            ${this._esc(l.commercialLine)}
          </text>
          <text x="${leaderX + 25}" y="${callY + 41}" fill="${muted}" font-size="9" font-family="monospace">
            ${this._esc(l.techSpec)}
          </text>
        `;

        cursorY = yTop;
      });

      // Cota total del paquete constructivo en el margen izquierdo
      const totDimX = state.typology === 'azotea' ? 24 : 58;
      layersSvg += `
        <line x1="${totDimX}" y1="${cursorY}" x2="${totDimX}" y2="${yBottom}" stroke="${accent}" stroke-width="1.5" marker-start="url(#dim-arrow)" marker-end="url(#dim-arrow)"/>
        <line x1="${totDimX - 6}" y1="${cursorY}" x2="${x0 - 4}" y2="${cursorY}" stroke="${lineCol}" stroke-dasharray="3 3"/>
        <line x1="${totDimX - 6}" y1="${yBottom}" x2="${x0 - 4}" y2="${yBottom}" stroke="${lineCol}" stroke-dasharray="3 3"/>
        <text x="${totDimX - 6}" y="${(cursorY + yBottom) / 2}" text-anchor="middle" fill="${accent}" font-size="10.5" font-weight="700" font-family="monospace" transform="rotate(-90 ${totDimX - 6} ${(cursorY + yBottom) / 2})">
          ESPESOR TOTAL PAQUETE = ${Math.round(totalThickMm)} mm
        </text>
      `;
    }

    // Símbolo de pendiente en la parte superior del corte
    const slopeArrowSvg = `
      <g transform="translate(${x0 + 20}, 76)">
        <line x1="0" y1="0" x2="145" y2="${isSloped ? 22 : 5}" stroke="${ink}" stroke-width="1.6" marker-end="url(#dim-arrow)"/>
        <text x="0" y="-6" fill="${ink}" font-size="10.5" font-weight="700" font-family="monospace">
          PENDIENTE DE DISEÑO: ${slopePct}% (${slopeDeg}°) · PESO: ${replanteo.summary.weightPerM2Kg} kg/m² · U = ${replanteo.summary.uValueWmk} W/m²K
        </text>
      </g>
    `;

    // Cajetín técnico inferior estilo plano de arquitectura CAD
    const titleBlock = `
      <rect x="16" y="${H - 42}" width="${W - 32}" height="28" rx="4" fill="${darkMode ? '#141b26' : '#f1f5f9'}" stroke="${lineCol}" stroke-width="1"/>
      <text x="28" y="${H - 24}" fill="${ink}" font-size="10.5" font-weight="700" font-family="monospace">
        CubiCAD · CONSTRUCTOR CAD/BIM DE CUBIERTAS · UPV ETSIE
      </text>
      <text x="${W - 28}" y="${H - 24}" text-anchor="end" fill="${muted}" font-size="10" font-family="monospace">
        ESCALA GRÁFICA 1:5 · ${activeCount} CAPAS ACTIVAS · ESPESOR ${Math.round(totalThickMm)} mm · NORMATIVA CTE DB-HS 1 / HE 1
      </text>
    `;

    return `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="100%" height="100%" style="background:${bg};display:block;">
        ${defs}
        <rect x="8" y="8" width="${W - 16}" height="${H - 16}" rx="6" fill="none" stroke="${lineCol}" stroke-width="1.2"/>
        <text x="24" y="34" fill="${ink}" font-size="13.5" font-weight="800" font-family="-apple-system, Inter, sans-serif">${titleText}</text>
        <text x="24" y="50" fill="${muted}" font-size="10.5">Sincronizado en vivo con los fabricantes, espesores y variantes oficiales del modelo 3D</text>
        ${slopeArrowSvg}
        ${layersSvg}
        ${calloutsSvg}
        ${titleBlock}
      </svg>
    `;
  }

  static _collectOrderedLayers(state, rep) {
    const out = [];
    const en = state.layersEnabled;

    if (state.typology === 'azotea') {
      const { waterproofing, separatorBot, insulation, plots, pavement, greenRoof } = rep.products;
      if (en.support) {
        out.push({
          title: 'Formación de Pendientes',
          commercialLine: 'Hormigón celular ligero aligerado (350 kg/m³)',
          techSpec: `Pendiente ${state.geometry.slopePct}% hacia cazoleta · Espesor medio 80 mm`,
          thickMm: 80,
          thickLabel: '80 mm',
          fillColor: '#e2e8f0',
          badgeColor: '#64748b',
          patternId: 'hatch-conc',
          visualKind: 'solid',
        });
      }

      const pushWp = () => {
        if (!en.waterproofing) return;
        out.push({
          title: 'Membrana Impermeabilizante',
          commercialLine: `${waterproofing.manufacturerName} · ${waterproofing.model}`,
          techSpec: `Ref: ${waterproofing.refCode} · Solape ${waterproofing.geometry.overlapLongMinMm} mm · Remonte ${state.geometry.parapetTurnupMm} mm`,
          thickMm: waterproofing.geometry.thicknessMm || 3.3,
          thickLabel: `${waterproofing.geometry.thicknessMm} mm`,
          fillColor: waterproofing.isPvcPlasticized ? '#64748b' : '#1e293b',
          badgeColor: '#ef4444',
          visualKind: 'waterproof',
        });
      };

      const pushGeo = () => {
        if (!en.membrane) return;
        out.push({
          title: 'Geotextil Separador y Antipunzonante',
          commercialLine: `${separatorBot.manufacturerName} · ${separatorBot.model}`,
          techSpec: `Ref: ${separatorBot.refCode} · 200 g/m² · Solape 150 mm`,
          thickMm: separatorBot.geometry.thicknessMm || 2.1,
          thickLabel: `${separatorBot.geometry.thicknessMm} mm`,
          fillColor: '#dbeafe',
          badgeColor: '#38bdf8',
          visualKind: 'solid',
        });
      };

      const pushIns = () => {
        if (!en.insulation) return;
        out.push({
          title: 'Aislamiento Térmico',
          commercialLine: `${insulation.manufacturerName} · ${insulation.model}`,
          techSpec: `Ref: ${insulation.refCode} · λ=${insulation.technicalSpecs.thermalConductivityWmk} W/mK · ${insulation.technicalSpecs.compressiveStrengthKpa} kPa`,
          thickMm: insulation.geometry.thicknessMm || 60,
          thickLabel: `${insulation.geometry.thicknessMm} mm`,
          fillColor: '#fef08a',
          badgeColor: '#eab308',
          patternId: 'hatch-xps',
          visualKind: 'solid',
        });
      };

      if (state.variant === 'convencional_fija') {
        pushIns();
        pushWp();
        pushGeo();
      } else {
        pushWp();
        pushGeo();
        pushIns();
      }

      if (en.battens) {
        if (state.variant === 'invertida_plots') {
          out.push({
            title: 'Cámara de Drenaje y Plots Regulables',
            commercialLine: `${plots.manufacturerName} · ${plots.model}`,
            techSpec: `Ref: ${plots.refCode} · Base Ø${plots.geometry.baseDiameterMm} mm · Cruceta 4 mm`,
            thickMm: plots.geometry.thicknessMm || 95,
            thickLabel: `${plots.geometry.thicknessMm} mm`,
            fillColor: '#e2e8f0',
            badgeColor: '#16a34a',
            visualKind: 'plots',
          });
        } else if (state.variant === 'ajardinada') {
          out.push({
            title: 'Placa Drenante y Retenedora Hídrica',
            commercialLine: `${greenRoof.manufacturerName} · Placa FKD 25 + Filtro Fil 105`,
            techSpec: `Retención 5,0 L/m² · Compresión > 200 kPa`,
            thickMm: 25,
            thickLabel: '25 mm',
            fillColor: '#334155',
            badgeColor: '#0ea5e9',
            visualKind: 'solid',
          });
        }
      }

      if (en.covering) {
        if (state.variant === 'ajardinada') {
          out.push({
            title: 'Sustrato Mineral Extensivo y Tapiz Sedum',
            commercialLine: `${greenRoof.manufacturerName} · ${greenRoof.model}`,
            techSpec: `Ref: ${greenRoof.refCode} · Peso saturado ${greenRoof.geometry.surfaceWeightKgM2} kg/m²`,
            thickMm: (greenRoof.geometry.thicknessMm || 108) - 25,
            thickLabel: `${(greenRoof.geometry.thicknessMm || 108) - 25} mm`,
            fillColor: '#86efac',
            badgeColor: '#16a34a',
            visualKind: 'solid',
          });
        } else {
          out.push({
            title: 'Pavimento Técnico Porcelánico Exterior',
            commercialLine: `${pavement.manufacturerName} · ${pavement.model}`,
            techSpec: `Ref: ${pavement.refCode} · ${pavement.geometry.lengthNominalMm}×${pavement.geometry.widthNominalMm}×${pavement.geometry.thicknessMm} mm · R11`,
            thickMm: pavement.geometry.thicknessMm || 20,
            thickLabel: `${pavement.geometry.thicknessMm} mm`,
            fillColor: '#d98a6c',
            badgeColor: '#b45309',
            patternId: 'hatch-clay',
            visualKind: 'pavers',
          });
        }
      }
      return out;
    }

    // Tejado Inclinado o Cubierta Metálica
    const { supportPanel, battenSys, covering } = rep.products;
    if (en.support) {
      out.push({
        title: state.typology === 'metalica' ? 'Correas Metálicas Z + Entarimado Ventilado' : 'Panel Sándwich Estructural y Aislamiento',
        commercialLine: `${supportPanel.manufacturerName} · ${supportPanel.model}`,
        techSpec: `Ref: ${supportPanel.refCode} · U=${supportPanel.technicalSpecs.thermalTransmittanceU || 0.34} W/m²K`,
        thickMm: supportPanel.geometry.thicknessMm || 109,
        thickLabel: `${supportPanel.geometry.thicknessMm} mm`,
        fillColor: '#fde68a',
        badgeColor: '#d97706',
        patternId: 'hatch-xps',
        visualKind: 'solid',
      });
    }
    if (en.membrane) {
      out.push({
        title: 'Lámina Impermeable Transpirable',
        commercialLine: `${battenSys.manufacturerName} · TRASPIR EVO 210`,
        techSpec: `Sd = 0,04 m · Solape autoadhesivo sellado 100 mm`,
        thickMm: 2,
        thickLabel: '1 mm',
        fillColor: '#334155',
        badgeColor: '#0284c7',
        visualKind: 'solid',
      });
    }
    if (en.battens) {
      out.push({
        title: 'Doble Rastrel Ventilado (Cámara Microventilada)',
        commercialLine: `${battenSys.manufacturerName} · ${battenSys.model}`,
        techSpec: `Paso exacto = ${rep.replanteoParams.supportBattenStepMm} mm · Cámara libre 30 mm`,
        thickMm: 60,
        thickLabel: '30+30 mm',
        fillColor: '#f3e8d2',
        badgeColor: '#b45309',
        patternId: 'hatch-wood',
        visualKind: 'battens',
      });
    }
    if (en.covering) {
      out.push({
        title: 'Cobertura Exterior Pieza a Pieza',
        commercialLine: `${covering.manufacturerName} · ${covering.model}`,
        techSpec: `Ref: ${covering.refCode} · Paso ${rep.replanteoParams.battenStepMm} mm · Solape ${rep.replanteoParams.realOverlapLongMm} mm · ${covering.geometry.surfaceWeightKgM2} kg/m²`,
        thickMm: Math.max(18, covering.geometry.thicknessMm || 25),
        thickLabel: `${covering.geometry.thicknessMm} mm`,
        fillColor: covering.colorHex || '#c86446',
        badgeColor: '#dc2626',
        patternId: covering.subType === 'zinc_junta_alzada' ? 'hatch-metal' : 'hatch-clay',
        visualKind: covering.subType === 'teja_curva' || covering.subType === 'teja_mixta' || covering.subType === 'teja_hormigon' ? 'tiles' : 'solid',
      });
    }
    return out;
  }

  static _esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
}
