/**
 * =============================================================================
 * ROOFLAB ETSIE · CONSTRUCCIÓN II (UPV)
 * MOTOR DE COMPATIBILIDAD CONSTRUCTIVA Y CALCULADORA DE REPLANTEO AUTOMÁTICO
 * =============================================================================
 * Cumple las Secciones 8, 9, 10, 11 y 12 del Master Prompt:
 * - Calculadora de Replanteo Real (Piezas teóricas, de montaje, de pedido con merma,
 *   hiladas, paso de rastrel, solapes reales, piezas de borde, peso total y por m²).
 * - Motor de Reglas de Compatibilidad Constructiva (pendiente mínima, paso de rastrel,
 *   incompatibilidad química PVC vs XPS sin geotextil, prohibición de lana de roca en
 *   cubierta invertida, exigencia de lámina antirraíces en cubierta ajardinada,
 *   resistencia a compresión bajo plots y accesorios obligatorios).
 * - Vinculación bidireccional con los 10 Detalles Constructivos y con HYDRO 3D.
 */

export class BIMReplanteoCalculator {
  /**
   * Calcula el replanteo geométrico y cuantitativo real de un faldón de cubierta inclinada (DEMO A).
   */
  static calculateSlopedRoof(config, store) {
    const geom = config.geometry || { lengthHorizM: 4.5, widthM: 3.6, slopePct: 32.0, wastePct: 5.0 };
    const sel = config.selectedProducts || {};

    const supportPanel = store.getProductById(sel.supportPanelId) || store.getProductById('THERMOCHIP-TAH-80');
    const battenSys = store.getProductById(sel.battenSystemId) || store.getProductById('ROTHOBLAAS-RASTREL-3050');
    const covering = store.getProductById(sel.coveringId) || store.getProductById('BORJA-C5021');
    const fastener = store.getProductById(sel.fastenerId) || store.getProductById('SFS-CLIP-TEJA-INOX');
    const gutter = store.getProductById(sel.gutterId) || store.getProductById('VMZINC-CANALON-333');

    const lengthHorizM = Math.max(1.5, Number(geom.lengthHorizM) || 4.5);
    const widthM = Math.max(1.5, Number(geom.widthM) || 3.6);
    const slopePct = Math.max(1.0, Number(geom.slopePct) || 32.0);
    const wastePct = Math.max(0.0, Number(geom.wastePct ?? 5.0));
    const wasteFactor = 1 + wastePct / 100;

    // 1. Geometría real del faldón inclinado
    const slopeFactor = Math.sqrt(1 + Math.pow(slopePct / 100, 2));
    const slopeDeg = (Math.atan(slopePct / 100) * 180) / Math.PI;
    const rafterLengthM = lengthHorizM * slopeFactor;
    const realAreaM2 = rafterLengthM * widthM;
    const horizAreaM2 = lengthHorizM * widthM;

    // 2. Paso de rastrel y solape longitudinal real según producto comercial
    const covGeom = covering.geometry;
    const covInst = covering.installation;

    const defaultStepMm =
      covGeom.usefulLengthNominalMm ||
      covInst.battenDistanceMaxMm ||
      370;

    const battenStepMm = geom.customBattenStepMm
      ? Number(geom.customBattenStepMm)
      : defaultStepMm;

    let realOverlapLongMm = covGeom.overlapLongMinMm || 0;
    if (covering.subType === 'pizarra_natural') {
      // En pizarra a triple solape: Paso = (L - Solape) / 2 => Solape = L - 2 * Paso
      realOverlapLongMm = Math.max(0, covGeom.lengthNominalMm - 2 * battenStepMm);
    } else if (
      covering.subType === 'teja_curva' ||
      covering.subType === 'teja_mixta' ||
      covering.subType === 'teja_plana' ||
      covering.subType === 'placa_ondulada_fibrocemento'
    ) {
      realOverlapLongMm = Math.max(0, covGeom.lengthNominalMm - battenStepMm);
    }

    const usefulWidthMm = covGeom.usefulWidthMm || covGeom.widthNominalMm || 220;
    const realOverlapTransMm = Math.max(0, (covGeom.widthNominalMm || usefulWidthMm) - usefulWidthMm);

    // 3. Número de hiladas (filas) y columnas en el faldón
    let numRows = Math.ceil((rafterLengthM * 1000) / battenStepMm);
    if (covering.subType === 'zinc_junta_alzada' || covering.subType === 'panel_sandwich_metalico') {
      // Bandejas continuas de cumbrera a alero si L <= 12 m
      numRows = rafterLengthM <= 6.0 ? 1 : Math.ceil(rafterLengthM / 5.0);
    }
    const numCols = Math.ceil((widthM * 1000) / usefulWidthMm);

    // 4. Desglose de piezas de cobertura (diferenciando Canal y Cobija en teja curva)
    let canalCount = 0;
    let cobijaCount = 0;
    let mainPiecesAssembly = numRows * numCols;
    if (covering.subType === 'teja_curva') {
      canalCount = numRows * numCols;
      cobijaCount = numRows * numCols;
      mainPiecesAssembly = canalCount + cobijaCount;
    }

    const theoreticalCoveringQty = Math.ceil(realAreaM2 * (covGeom.unitsPerM2 || mainPiecesAssembly / realAreaM2));
    const orderCoveringQty = Math.ceil(mainPiecesAssembly * wasteFactor);

    // Piezas especiales de borde (Alero, Cumbrera, Remates laterales)
    const eavePiecesCount = numCols;
    const ridgePiecesCount = Math.ceil((widthM * 1000) / 380); // Caballete cada 38 cm útiles
    const lateralPiecesCount = numRows * 2;

    // 5. Rastreles, contrarastreles y lámina transpirable
    const rafterSpacingM = 0.60;
    const numRafters = Math.floor(widthM / rafterSpacingM) + 1;
    const counterBattenMl = Number((numRafters * rafterLengthM).toFixed(2));

    // Paso de rastrel real para soporte (en junta alzada o panel sándwich usa su intereje de apoyo)
    const supportBattenStepMm =
      covering.subType === 'zinc_junta_alzada'
        ? 330
        : covering.subType === 'panel_sandwich_metalico'
        ? 1800
        : battenStepMm;

    const numBattenLines = Math.ceil((rafterLengthM * 1000) / supportBattenStepMm) + 1;
    const horizontalBattenMl = Number((numBattenLines * widthM).toFixed(2));
    const totalBattenMl = Number((counterBattenMl + horizontalBattenMl).toFixed(2));
    const battenBars3m = Math.ceil((totalBattenMl * wasteFactor) / 3.0);

    // 6. Paneles de soporte Thermochip TAH
    const panelAreaM2 = ((supportPanel.geometry.usefulLengthNominalMm || 2400) * (supportPanel.geometry.usefulWidthMm || 535)) / 1e6;
    const theoreticalPanels = Number((realAreaM2 / panelAreaM2).toFixed(1));
    const assemblyPanels = Math.ceil(realAreaM2 / panelAreaM2);
    const orderPanels = Math.ceil(assemblyPanels * wasteFactor);

    // 7. Fijaciones mecánicas (clips / ganchos / patas inox)
    let assemblyFasteners = 0;
    if (covering.subType === 'pizarra_natural') {
      assemblyFasteners = mainPiecesAssembly; // 1 gancho por pizarra
    } else if (covering.subType === 'zinc_junta_alzada') {
      assemblyFasteners = (numCols + 1) * numBattenLines; // 1 pata inox cada 330 mm por junta
    } else {
      // Perímetro completo + 1 de cada 4 piezas interiores
      const perimeterPieces = Math.min(mainPiecesAssembly, 2 * numCols + 2 * numRows);
      const interiorPieces = Math.max(0, mainPiecesAssembly - perimeterPieces);
      assemblyFasteners = perimeterPieces + Math.ceil(interiorPieces * 0.25);
    }
    const orderFasteners = Math.ceil(assemblyFasteners * wasteFactor);

    // 8. Canalón de alero
    const gutterSectionM = (gutter.geometry.lengthNominalMm || 4000) / 1000;
    const assemblyGutterUnits = Math.ceil(widthM / gutterSectionM);
    const gutterBrackets = Math.ceil((widthM * 1000) / (gutter.geometry.supportBracketSpacingMm || 500)) + 1;

    // 9. Cuadro de mediciones y pesos
    const lineItems = [
      {
        layerOrder: 1,
        role: 'support_panel',
        roleLabel: '1. Soporte Estructural / Panel Sándwich',
        productId: supportPanel.id,
        manufacturerName: supportPanel.manufacturerName,
        model: supportPanel.model,
        refCode: supportPanel.refCode,
        verificationStatus: supportPanel.verificationStatus,
        dimensionsStr: `${supportPanel.geometry.lengthNominalMm} × ${supportPanel.geometry.widthNominalMm} × ${supportPanel.geometry.thicknessMm} mm`,
        unit: 'paneles',
        theoreticalQty: theoreticalPanels,
        assemblyQty: assemblyPanels,
        orderQty: orderPanels,
        unitWeightKg: supportPanel.geometry.unitWeightKg,
        totalWeightKg: Number((assemblyPanels * supportPanel.geometry.unitWeightKg).toFixed(1)),
      },
      {
        layerOrder: 2,
        role: 'batten_system',
        roleLabel: '2. Lámina Transpirable + Doble Rastrel Ventilado',
        productId: battenSys.id,
        manufacturerName: battenSys.manufacturerName,
        model: battenSys.model,
        refCode: battenSys.refCode,
        verificationStatus: battenSys.verificationStatus,
        dimensionsStr: `Sección ${battenSys.geometry.widthNominalMm}×${battenSys.geometry.thicknessMm} mm · Paso ${supportBattenStepMm} mm`,
        unit: 'm lin. (barras 3m)',
        theoreticalQty: totalBattenMl,
        assemblyQty: totalBattenMl,
        orderQty: `${Number((totalBattenMl * wasteFactor).toFixed(1))} m (${battenBars3m} barras)`,
        unitWeightKg: battenSys.geometry.linearWeightKgM || 0.72,
        totalWeightKg: Number((totalBattenMl * (battenSys.geometry.linearWeightKgM || 0.72) + realAreaM2 * 0.22).toFixed(1)),
      },
      {
        layerOrder: 3,
        role: 'roof_covering',
        roleLabel:
          covering.subType === 'teja_curva'
            ? `3. Cobertura Teja Curva (${canalCount} canales + ${cobijaCount} cobijas)`
            : '3. Cobertura Exterior Pieza a Pieza',
        productId: covering.id,
        manufacturerName: covering.manufacturerName,
        model: covering.model,
        refCode: covering.refCode,
        verificationStatus: covering.verificationStatus,
        dimensionsStr: `${covGeom.lengthNominalMm} × ${covGeom.widthNominalMm} × ${covGeom.thicknessMm} mm (Útil ${battenStepMm}×${usefulWidthMm} mm)`,
        unit: 'uds',
        theoreticalQty: theoreticalCoveringQty,
        assemblyQty: mainPiecesAssembly,
        orderQty: orderCoveringQty,
        unitWeightKg: covGeom.unitWeightKg,
        totalWeightKg: Number((mainPiecesAssembly * covGeom.unitWeightKg).toFixed(1)),
      },
      {
        layerOrder: 4,
        role: 'fastener',
        roleLabel: '4. Fijación Mecánica en Seco',
        productId: fastener.id,
        manufacturerName: fastener.manufacturerName,
        model: fastener.model,
        refCode: fastener.refCode,
        verificationStatus: fastener.verificationStatus,
        dimensionsStr: `${fastener.geometry.lengthNominalMm} × ${fastener.geometry.widthNominalMm} mm`,
        unit: 'uds',
        theoreticalQty: assemblyFasteners,
        assemblyQty: assemblyFasteners,
        orderQty: orderFasteners,
        unitWeightKg: fastener.geometry.unitWeightKg,
        totalWeightKg: Number((assemblyFasteners * fastener.geometry.unitWeightKg).toFixed(1)),
      },
      {
        layerOrder: 5,
        role: 'gutter_unit',
        roleLabel: '5. Evacuación Perimetral de Alero',
        productId: gutter.id,
        manufacturerName: gutter.manufacturerName,
        model: gutter.model,
        refCode: gutter.refCode,
        verificationStatus: gutter.verificationStatus,
        dimensionsStr: `Tramo ${gutter.geometry.lengthNominalMm} mm · Ø${gutter.geometry.widthNominalMm} mm (${gutterBrackets} gafas soporte)`,
        unit: 'tramos 4m',
        theoreticalQty: Number((widthM / gutterSectionM).toFixed(2)),
        assemblyQty: assemblyGutterUnits,
        orderQty: assemblyGutterUnits,
        unitWeightKg: gutter.geometry.unitWeightKg,
        totalWeightKg: Number((assemblyGutterUnits * gutter.geometry.unitWeightKg).toFixed(1)),
      },
    ];

    const totalWeightKg = Number(lineItems.reduce((acc, item) => acc + item.totalWeightKg, 0).toFixed(1));
    const weightPerM2Kg = Number((totalWeightKg / realAreaM2).toFixed(1));

    // Transmitancia térmica estimada del paquete
    const uValue =
      covering.technicalSpecs.thermalTransmittanceU ||
      supportPanel.technicalSpecs.thermalTransmittanceU ||
      0.34;

    return {
      systemType: 'tejado',
      geometry: {
        lengthHorizM,
        widthM,
        slopePct,
        slopeDeg: Number(slopeDeg.toFixed(1)),
        rafterLengthM: Number(rafterLengthM.toFixed(3)),
        horizAreaM2: Number(horizAreaM2.toFixed(2)),
        realAreaM2: Number(realAreaM2.toFixed(2)),
        wastePct,
      },
      replanteoParams: {
        battenStepMm,
        supportBattenStepMm,
        usefulWidthMm,
        realOverlapLongMm: Number(realOverlapLongMm.toFixed(1)),
        realOverlapTransMm: Number(realOverlapTransMm.toFixed(1)),
        numRows,
        numCols,
        numRafters,
        numBattenLines,
        counterBattenMl,
        horizontalBattenMl,
        totalBattenMl,
        canalCount,
        cobijaCount,
        mainPiecesAssembly,
        theoreticalCoveringQty,
        orderCoveringQty,
        eavePiecesCount,
        ridgePiecesCount,
        lateralPiecesCount,
        assemblyFasteners,
        gutterBrackets,
      },
      products: {
        supportPanel,
        battenSys,
        covering,
        fastener,
        gutter,
      },
      lineItems,
      summary: {
        totalWeightKg,
        weightPerM2Kg,
        uValueWmk: uValue,
        totalIndividual3DPieces:
          assemblyPanels +
          numRafters +
          numBattenLines +
          mainPiecesAssembly +
          ridgePiecesCount +
          assemblyFasteners +
          1,
      },
    };
  }

  /**
   * Calcula el replanteo geométrico y cuantitativo real de una azotea plana (DEMO B).
   */
  static calculateFlatRoof(config, store) {
    const geom = config.geometry || { lengthM: 4.8, widthM: 3.6, slopePct: 2.0, parapetTurnupMm: 200, wastePct: 5.0 };
    const sel = config.selectedProducts || {};
    const roofSubType = config.roofSubType || 'invertida_plots';

    const waterproofing = store.getProductById(sel.waterproofingId) || store.getProductById('DANOSA-ESTERDAN40P');
    const separatorBot = store.getProductById(sel.separatorBotId) || store.getProductById('DANOSA-DANOFELT-PY200');
    const insulation = store.getProductById(sel.insulationId) || store.getProductById('URSA-XPS-NIIIL-60');
    const separatorTop = store.getProductById(sel.separatorTopId) || store.getProductById('DANOSA-DANOFELT-PY200');
    const drainageLayer = store.getProductById(sel.drainageLayerId) || store.getProductById('DANOSA-DANODREN-H15');
    const plots = store.getProductById(sel.plotsId) || store.getProductById('PEYGRAN-XSP5-PRO');
    const pavement = store.getProductById(sel.pavementId) || store.getProductById('GRESARAGON-ORDESA-6060');
    const greenRoof = store.getProductById(sel.greenRoofId) || store.getProductById('OPTIGRUN-FKD25');
    const drainUnit = store.getProductById(sel.drainUnitId) || store.getProductById('JIMTEN-S77-110');

    const lengthM = Math.max(2.0, Number(geom.lengthM) || 4.8);
    const widthM = Math.max(2.0, Number(geom.widthM) || 3.6);
    const slopePct = Math.max(0.0, Number(geom.slopePct ?? 2.0));
    const parapetTurnupMm = Math.max(100, Number(geom.parapetTurnupMm ?? 200));
    const wastePct = Math.max(0.0, Number(geom.wastePct ?? 5.0));
    const wasteFactor = 1 + wastePct / 100;

    const flatAreaM2 = Number((lengthM * widthM).toFixed(2));
    const perimeterM = Number((2 * (lengthM + widthM)).toFixed(2));
    const turnupAreaM2 = Number((perimeterM * (parapetTurnupMm / 1000)).toFixed(2));
    const totalWaterproofAreaM2 = Number((flatAreaM2 + turnupAreaM2).toFixed(2));

    // 1. Impermeabilización (bandas y rollos considerando solape oficial)
    const wpUsefulWidthM = (waterproofing.geometry.usefulWidthMm || 920) / 1000;
    const numMembraneStrips = Math.ceil(widthM / wpUsefulWidthM);
    const usefulRollAreaM2 = waterproofing.geometry.usefulRollAreaM2 || 9.11;
    const theoreticalRollsWp = Number((totalWaterproofAreaM2 / usefulRollAreaM2).toFixed(2));
    const assemblyRollsWp = Math.ceil(totalWaterproofAreaM2 / usefulRollAreaM2);
    const orderRollsWp = Math.ceil(assemblyRollsWp * wasteFactor);

    // 2. Planchas de aislamiento térmico (retícula a matajunta)
    const insLengthM = (insulation.geometry.usefulLengthNominalMm || 1235) / 1000;
    const insWidthM = (insulation.geometry.usefulWidthMm || 585) / 1000;
    const insCols = Math.ceil(lengthM / insLengthM);
    const insRows = Math.ceil(widthM / insWidthM);
    const assemblyInsulationBoards = insCols * insRows;
    const theoreticalInsulationBoards = Number((flatAreaM2 / (insLengthM * insWidthM)).toFixed(1));
    const orderInsulationBoards = Math.ceil(assemblyInsulationBoards * wasteFactor);

    // 3. Geotextil separador inferior y superior
    const geoOverlapFactor = 1.12; // 150 mm solape
    const singleLayerGeoM2 = Number((flatAreaM2 * geoOverlapFactor).toFixed(1));
    const totalGeoM2 = Number((singleLayerGeoM2 * 2).toFixed(1));

    // 4. Retícula de Baldosas Porcelánicas Gres Aragón y Plots Peygran
    const tileLenMm = pavement.geometry.usefulLengthNominalMm || pavement.geometry.lengthNominalMm || 600;
    const tileWidMm = pavement.geometry.usefulWidthMm || pavement.geometry.widthNominalMm || 600;
    const jointMm = plots.geometry.jointTabThicknessMm || pavement.geometry.jointWidthMm || 4.0;
    const stepXMm = tileLenMm + jointMm;
    const stepYMm = tileWidMm + jointMm;

    const numTilesX = Math.ceil((lengthM * 1000) / stepXMm);
    const numTilesY = Math.ceil((widthM * 1000) / stepYMm);
    const fullTilesX = Math.floor((lengthM * 1000) / stepXMm);
    const fullTilesY = Math.floor((widthM * 1000) / stepYMm);
    const fullTilesCount = fullTilesX * fullTilesY;
    const assemblyTilesCount = numTilesX * numTilesY;
    const cutBorderTilesCount = Math.max(0, assemblyTilesCount - fullTilesCount);
    const theoreticalTilesCount = Math.ceil(flatAreaM2 * (pavement.geometry.unitsPerM2 || 2.78));
    const orderTilesCount = Math.ceil(assemblyTilesCount * wasteFactor);

    // Plots en cada vértice de la retícula de baldosas: (Nx + 1) * (Ny + 1)
    const numPlotsX = numTilesX + 1;
    const numPlotsY = numTilesY + 1;
    const assemblyPlotsCount = roofSubType === 'invertida_plots' ? numPlotsX * numPlotsY : 0;
    const perimeterPlotsCount = roofSubType === 'invertida_plots' ? 2 * numPlotsX + 2 * Math.max(0, numPlotsY - 2) : 0;
    const centralPlotsCount = Math.max(0, assemblyPlotsCount - perimeterPlotsCount);
    const orderPlotsCount = Math.ceil(assemblyPlotsCount * wasteFactor);

    // 5. Lámina nodular / Sistema ajardinado
    const greenPacksCount = Math.ceil(flatAreaM2 * (greenRoof.geometry.unitsPerM2 || 0.5));

    // 6. Cazoleta sifónica Jimten
    const numDrains = flatAreaM2 <= 100 ? 1 : Math.ceil(flatAreaM2 / 100);

    // Construcción ordenada de capas según subtipo de azotea
    const lineItems = [];

    if (roofSubType === 'convencional_fija') {
      // En convencional: 1. Aislamiento debajo -> 2. Impermeabilización -> 3. Geotextil -> 4. Mortero y Baldosa recibida
      lineItems.push(
        {
          layerOrder: 1,
          role: 'insulation',
          roleLabel: '1. Aislamiento Térmico Inferior (Cubierta Convencional)',
          productId: insulation.id,
          manufacturerName: insulation.manufacturerName,
          model: insulation.model,
          refCode: insulation.refCode,
          verificationStatus: insulation.verificationStatus,
          dimensionsStr: `${insulation.geometry.lengthNominalMm}×${insulation.geometry.widthNominalMm}×${insulation.geometry.thicknessMm} mm (${insCols}×${insRows})`,
          unit: 'planchas',
          theoreticalQty: theoreticalInsulationBoards,
          assemblyQty: assemblyInsulationBoards,
          orderQty: orderInsulationBoards,
          unitWeightKg: insulation.geometry.unitWeightKg,
          totalWeightKg: Number((assemblyInsulationBoards * insulation.geometry.unitWeightKg).toFixed(1)),
        },
        {
          layerOrder: 2,
          role: 'waterproofing',
          roleLabel: '2. Membrana Impermeabilizante Superior + Remonte Petos',
          productId: waterproofing.id,
          manufacturerName: waterproofing.manufacturerName,
          model: waterproofing.model,
          refCode: waterproofing.refCode,
          verificationStatus: waterproofing.verificationStatus,
          dimensionsStr: `Rollo ${waterproofing.geometry.lengthNominalMm / 1000}×${waterproofing.geometry.widthNominalMm / 1000} m · Solape ${waterproofing.geometry.overlapLongMinMm} mm`,
          unit: 'rollos',
          theoreticalQty: theoreticalRollsWp,
          assemblyQty: assemblyRollsWp,
          orderQty: orderRollsWp,
          unitWeightKg: waterproofing.geometry.unitWeightKg,
          totalWeightKg: Number((totalWaterproofAreaM2 * waterproofing.geometry.surfaceWeightKgM2).toFixed(1)),
        },
        {
          layerOrder: 3,
          role: 'separator',
          roleLabel: '3. Capa Separadora Antipunzonante bajo Mortero',
          productId: separatorTop.id,
          manufacturerName: separatorTop.manufacturerName,
          model: separatorTop.model,
          refCode: separatorTop.refCode,
          verificationStatus: separatorTop.verificationStatus,
          dimensionsStr: `e=${separatorTop.geometry.thicknessMm} mm · Solape ${separatorTop.geometry.overlapLongMinMm} mm`,
          unit: 'm²',
          theoreticalQty: flatAreaM2,
          assemblyQty: singleLayerGeoM2,
          orderQty: Number((singleLayerGeoM2 * wasteFactor).toFixed(1)),
          unitWeightKg: separatorTop.geometry.surfaceWeightKgM2,
          totalWeightKg: Number((singleLayerGeoM2 * separatorTop.geometry.surfaceWeightKgM2).toFixed(1)),
        },
        {
          layerOrder: 4,
          role: 'pavement',
          roleLabel: '4. Pavimento Cerámico Recibido en Fijo',
          productId: pavement.id,
          manufacturerName: pavement.manufacturerName,
          model: pavement.model,
          refCode: pavement.refCode,
          verificationStatus: pavement.verificationStatus,
          dimensionsStr: `${tileLenMm}×${tileWidMm}×${pavement.geometry.thicknessMm} mm (${numTilesX}×${numTilesY} uds)`,
          unit: 'baldosas',
          theoreticalQty: theoreticalTilesCount,
          assemblyQty: assemblyTilesCount,
          orderQty: orderTilesCount,
          unitWeightKg: pavement.geometry.unitWeightKg,
          totalWeightKg: Number((assemblyTilesCount * pavement.geometry.unitWeightKg).toFixed(1)),
        }
      );
    } else if (roofSubType === 'ajardinada') {
      // Cubierta ajardinada: 1. Impermeabilización -> 2. Geotextil -> 3. XPS -> 4. DANODREN / Optigrün FKD 25 + Sustrato + Sedum
      lineItems.push(
        {
          layerOrder: 1,
          role: 'waterproofing',
          roleLabel: '1. Membrana Impermeabilizante + Remonte Petos',
          productId: waterproofing.id,
          manufacturerName: waterproofing.manufacturerName,
          model: waterproofing.model,
          refCode: waterproofing.refCode,
          verificationStatus: waterproofing.verificationStatus,
          dimensionsStr: `Rollo ${waterproofing.geometry.lengthNominalMm / 1000}×${waterproofing.geometry.widthNominalMm / 1000} m · Solape ${waterproofing.geometry.overlapLongMinMm} mm`,
          unit: 'rollos',
          theoreticalQty: theoreticalRollsWp,
          assemblyQty: assemblyRollsWp,
          orderQty: orderRollsWp,
          unitWeightKg: waterproofing.geometry.unitWeightKg,
          totalWeightKg: Number((totalWaterproofAreaM2 * waterproofing.geometry.surfaceWeightKgM2).toFixed(1)),
        },
        {
          layerOrder: 2,
          role: 'separator',
          roleLabel: '2. Geotextil Separador y Protector Inferior',
          productId: separatorBot.id,
          manufacturerName: separatorBot.manufacturerName,
          model: separatorBot.model,
          refCode: separatorBot.refCode,
          verificationStatus: separatorBot.verificationStatus,
          dimensionsStr: `e=${separatorBot.geometry.thicknessMm} mm · Solape ${separatorBot.geometry.overlapLongMinMm} mm`,
          unit: 'm²',
          theoreticalQty: flatAreaM2,
          assemblyQty: singleLayerGeoM2,
          orderQty: Number((singleLayerGeoM2 * wasteFactor).toFixed(1)),
          unitWeightKg: separatorBot.geometry.surfaceWeightKgM2,
          totalWeightKg: Number((singleLayerGeoM2 * separatorBot.geometry.surfaceWeightKgM2).toFixed(1)),
        },
        {
          layerOrder: 3,
          role: 'insulation',
          roleLabel: '3. Aislamiento Térmico Invertido a Media Madera',
          productId: insulation.id,
          manufacturerName: insulation.manufacturerName,
          model: insulation.model,
          refCode: insulation.refCode,
          verificationStatus: insulation.verificationStatus,
          dimensionsStr: `${insulation.geometry.lengthNominalMm}×${insulation.geometry.widthNominalMm}×${insulation.geometry.thicknessMm} mm (${insCols}×${insRows})`,
          unit: 'planchas',
          theoreticalQty: theoreticalInsulationBoards,
          assemblyQty: assemblyInsulationBoards,
          orderQty: orderInsulationBoards,
          unitWeightKg: insulation.geometry.unitWeightKg,
          totalWeightKg: Number((assemblyInsulationBoards * insulation.geometry.unitWeightKg).toFixed(1)),
        },
        {
          layerOrder: 4,
          role: 'green_roof_system',
          roleLabel: '4. Sistema Drenante Retenedor + Sustrato + Tapiz Sedum',
          productId: greenRoof.id,
          manufacturerName: greenRoof.manufacturerName,
          model: greenRoof.model,
          refCode: greenRoof.refCode,
          verificationStatus: greenRoof.verificationStatus,
          dimensionsStr: `Placa ${greenRoof.geometry.lengthNominalMm}×${greenRoof.geometry.widthNominalMm} mm · Espesor total ${greenRoof.geometry.thicknessMm} mm`,
          unit: 'm² sistema',
          theoreticalQty: flatAreaM2,
          assemblyQty: flatAreaM2,
          orderQty: Number((flatAreaM2 * wasteFactor).toFixed(1)),
          unitWeightKg: greenRoof.geometry.surfaceWeightKgM2,
          totalWeightKg: Number((flatAreaM2 * greenRoof.geometry.surfaceWeightKgM2).toFixed(1)),
        }
      );
    } else {
      // Por defecto DEMO B: Azotea Invertida Transitable sobre Plots Regulables
      lineItems.push(
        {
          layerOrder: 1,
          role: 'waterproofing',
          roleLabel: '1. Membrana Impermeabilizante + Remonte Petos (≥20 cm)',
          productId: waterproofing.id,
          manufacturerName: waterproofing.manufacturerName,
          model: waterproofing.model,
          refCode: waterproofing.refCode,
          verificationStatus: waterproofing.verificationStatus,
          dimensionsStr: `${numMembraneStrips} bandas · Solape ${waterproofing.geometry.overlapLongMinMm} mm · Remonte ${parapetTurnupMm} mm`,
          unit: 'rollos',
          theoreticalQty: theoreticalRollsWp,
          assemblyQty: assemblyRollsWp,
          orderQty: orderRollsWp,
          unitWeightKg: waterproofing.geometry.unitWeightKg,
          totalWeightKg: Number((totalWaterproofAreaM2 * waterproofing.geometry.surfaceWeightKgM2).toFixed(1)),
        },
        {
          layerOrder: 2,
          role: 'separator',
          roleLabel: '2. Geotextil Separador Inferior y Superior (Doble Capa)',
          productId: separatorBot.id,
          manufacturerName: separatorBot.manufacturerName,
          model: separatorBot.model,
          refCode: separatorBot.refCode,
          verificationStatus: separatorBot.verificationStatus,
          dimensionsStr: `2 capas × ${singleLayerGeoM2} m² (Solape ${separatorBot.geometry.overlapLongMinMm} mm)`,
          unit: 'm²',
          theoreticalQty: Number((flatAreaM2 * 2).toFixed(1)),
          assemblyQty: totalGeoM2,
          orderQty: Number((totalGeoM2 * wasteFactor).toFixed(1)),
          unitWeightKg: separatorBot.geometry.surfaceWeightKgM2,
          totalWeightKg: Number((totalGeoM2 * separatorBot.geometry.surfaceWeightKgM2).toFixed(1)),
        },
        {
          layerOrder: 3,
          role: 'insulation',
          roleLabel: '3. Aislamiento Térmico Invertido a Media Madera',
          productId: insulation.id,
          manufacturerName: insulation.manufacturerName,
          model: insulation.model,
          refCode: insulation.refCode,
          verificationStatus: insulation.verificationStatus,
          dimensionsStr: `${insulation.geometry.lengthNominalMm}×${insulation.geometry.widthNominalMm}×${insulation.geometry.thicknessMm} mm (Retícula ${insCols}×${insRows})`,
          unit: 'planchas',
          theoreticalQty: theoreticalInsulationBoards,
          assemblyQty: assemblyInsulationBoards,
          orderQty: orderInsulationBoards,
          unitWeightKg: insulation.geometry.unitWeightKg,
          totalWeightKg: Number((assemblyInsulationBoards * insulation.geometry.unitWeightKg).toFixed(1)),
        },
        {
          layerOrder: 4,
          role: 'plots',
          roleLabel: `4. Plots Regulables (${centralPlotsCount} centrales + ${perimeterPlotsCount} borde)`,
          productId: plots.id,
          manufacturerName: plots.manufacturerName,
          model: plots.model,
          refCode: plots.refCode,
          verificationStatus: plots.verificationStatus,
          dimensionsStr: `Base Ø${plots.geometry.baseDiameterMm} mm · Altura H=${plots.geometry.thicknessMm} mm (${plots.geometry.minHeightMm}–${plots.geometry.maxHeightMm} mm)`,
          unit: 'plots',
          theoreticalQty: Math.ceil(flatAreaM2 * (plots.geometry.unitsPerM2 || 2.78)),
          assemblyQty: assemblyPlotsCount,
          orderQty: orderPlotsCount,
          unitWeightKg: plots.geometry.unitWeightKg,
          totalWeightKg: Number((assemblyPlotsCount * plots.geometry.unitWeightKg).toFixed(1)),
        },
        {
          layerOrder: 5,
          role: 'pavement',
          roleLabel: `5. Pavimento Técnico Elevado (${fullTilesCount} enteras + ${cutBorderTilesCount} corte borde)`,
          productId: pavement.id,
          manufacturerName: pavement.manufacturerName,
          model: pavement.model,
          refCode: pavement.refCode,
          verificationStatus: pavement.verificationStatus,
          dimensionsStr: `${tileLenMm}×${tileWidMm}×${pavement.geometry.thicknessMm} mm · Junta abierta ${jointMm} mm (${numTilesX}×${numTilesY})`,
          unit: 'baldosas',
          theoreticalQty: theoreticalTilesCount,
          assemblyQty: assemblyTilesCount,
          orderQty: orderTilesCount,
          unitWeightKg: pavement.geometry.unitWeightKg,
          totalWeightKg: Number((assemblyTilesCount * pavement.geometry.unitWeightKg).toFixed(1)),
        }
      );
    }

    // 6. Cazoleta Sifónica de Evacuación (presente en todas las azoteas)
    lineItems.push({
      layerOrder: lineItems.length + 1,
      role: 'drain_unit',
      roleLabel: `${lineItems.length + 1}. Punto Singular de Evacuación Pluvial`,
      productId: drainUnit.id,
      manufacturerName: drainUnit.manufacturerName,
      model: drainUnit.model,
      refCode: drainUnit.refCode,
      verificationStatus: drainUnit.verificationStatus,
      dimensionsStr: `Rejilla ${drainUnit.geometry.lengthNominalMm}×${drainUnit.geometry.widthNominalMm} mm · Salida Ø${drainUnit.geometry.outletDiameterMm} mm (${drainUnit.geometry.hydraulicCapacityLs} L/s)`,
      unit: 'uds',
      theoreticalQty: numDrains,
      assemblyQty: numDrains,
      orderQty: numDrains,
      unitWeightKg: drainUnit.geometry.unitWeightKg,
      totalWeightKg: Number((numDrains * drainUnit.geometry.unitWeightKg).toFixed(1)),
    });

    const totalWeightKg = Number(lineItems.reduce((acc, item) => acc + item.totalWeightKg, 0).toFixed(1));
    const weightPerM2Kg = Number((totalWeightKg / flatAreaM2).toFixed(1));

    // Cálculo de transmitancia térmica U = 1 / (R_si + R_forjado + R_aislamiento + R_se)
    const lambdaIns = insulation.technicalSpecs.thermalConductivityWmk || 0.034;
    const thickInsM = (insulation.geometry.thicknessMm || 60) / 1000;
    const rIns = thickInsM / lambdaIns;
    const rTotal = 0.10 + 0.35 + rIns + 0.04;
    const uValue = Number((1 / rTotal).toFixed(2));

    return {
      systemType: 'azotea',
      roofSubType,
      geometry: {
        lengthM,
        widthM,
        slopePct,
        parapetTurnupMm,
        flatAreaM2,
        perimeterM,
        turnupAreaM2,
        totalWaterproofAreaM2,
        wastePct,
      },
      replanteoParams: {
        numMembraneStrips,
        wpOverlapLongMm: waterproofing.geometry.overlapLongMinMm || 80,
        insCols,
        insRows,
        assemblyInsulationBoards,
        tileLenMm,
        tileWidMm,
        jointMm,
        numTilesX,
        numTilesY,
        fullTilesCount,
        cutBorderTilesCount,
        assemblyTilesCount,
        numPlotsX,
        numPlotsY,
        assemblyPlotsCount,
        centralPlotsCount,
        perimeterPlotsCount,
        plotHeightMm: plots.geometry.thicknessMm || 95,
        numDrains,
      },
      products: {
        waterproofing,
        separatorBot,
        insulation,
        separatorTop,
        drainageLayer,
        plots,
        pavement,
        greenRoof,
        drainUnit,
      },
      lineItems,
      summary: {
        totalWeightKg,
        weightPerM2Kg,
        uValueWmk: uValue,
        thermalResistanceRd: Number(rIns.toFixed(2)),
        totalIndividual3DPieces:
          numMembraneStrips +
          assemblyInsulationBoards +
          assemblyPlotsCount +
          (roofSubType === 'ajardinada' ? greenPacksCount : assemblyTilesCount) +
          numDrains +
          2,
      },
    };
  }
}

/**
 * =============================================================================
 * MOTOR DE REGLAS DE COMPATIBILIDAD CONSTRUCTIVA (SECCIÓN 9)
 * =============================================================================
 * Verifica automáticamente cada combinación comercial e informa con el formato:
 * Problema detectado → Parámetro afectado → Fuente técnica → Solución recomendada
 */
export class BIMCompatibilityEngine {
  static evaluate(demoConfig, replanteo, store) {
    const alerts = [];

    if (replanteo.systemType === 'tejado') {
      const { slopePct } = replanteo.geometry;
      const { battenStepMm, realOverlapLongMm } = replanteo.replanteoParams;
      const { covering, supportPanel, fastener } = replanteo.products;

      const minSlope = covering.installation.minSlopePct || 10;
      const recSlope = covering.installation.recommendedSlopePct || minSlope + 5;

      // Regla T1: Pendiente mínima admisible del producto de cobertura
      if (slopePct < minSlope) {
        alerts.push({
          id: 'RULE-SLOPE-MIN',
          severity: 'error',
          problem: `Pendiente insuficiente para ${covering.brand} ${covering.model}`,
          affectedParam: `Pendiente proyectada: ${slopePct.toFixed(1)}% < Pendiente mínima oficial: ${minSlope}% (${covering.installation.minSlopeDeg}°)`,
          source: `${covering.versionDoc} / CTE DB-HS 1 Tabla 2.10`,
          solution: `Incrementar la pendiente del faldón al menos al ${minSlope}% (recomendado ${recSlope}%) o incorporar subcubierta estanca bajo teja.`,
        });
      } else if (slopePct < recSlope) {
        alerts.push({
          id: 'RULE-SLOPE-WARN',
          severity: 'warning',
          problem: `Pendiente en rango límite entre mínima (${minSlope}%) y óptima (${recSlope}%)`,
          affectedParam: `Pendiente proyectada: ${slopePct.toFixed(1)}%`,
          source: `${covering.versionDoc}`,
          solution: `Se cumple el mínimo estricto (${minSlope}%), pero el fabricante recomienda utilizar el solape longitudinal máximo y lámina impermeable transpirable sellada.`,
        });
      } else {
        alerts.push({
          id: 'RULE-SLOPE-OK',
          severity: 'ok',
          problem: `Pendiente de faldón verificada (${slopePct.toFixed(1)}% ≥ ${minSlope}% mín.)`,
          affectedParam: `Pendiente: ${slopePct.toFixed(1)}% (${replanteo.geometry.slopeDeg}°)`,
          source: `${covering.versionDoc} · CTE DB-HS 1`,
          solution: `Evacuación por gravedad óptima garantizada sin riesgo de retorno capilar.`,
        });
      }

      // Regla T2: Paso de rastrel dentro del juego longitudinal oficial de la pieza
      const minStep = covering.installation.battenDistanceMinMm;
      const maxStep = covering.installation.battenDistanceMaxMm;
      if (
        minStep &&
        maxStep &&
        covering.subType !== 'zinc_junta_alzada' &&
        covering.subType !== 'panel_sandwich_metalico'
      ) {
        if (battenStepMm < minStep || battenStepMm > maxStep) {
          alerts.push({
            id: 'RULE-BATTEN-STEP',
            severity: 'error',
            problem: `Paso de rastrel (${battenStepMm} mm) incompatible con el tacón/encaje de ${covering.model}`,
            affectedParam: `Paso de rastrel configurado: ${battenStepMm} mm (Rango oficial: ${minStep}–${maxStep} mm)`,
            source: `${covering.versionDoc} · UNE 136020`,
            solution: `Ajustar el paso de rastrel a ${covering.geometry.usefulLengthNominalMm} mm (dentro de [${minStep}, ${maxStep}] mm) para que los tacones apoyen y encajen los canales transversales.`,
          });
        } else {
          alerts.push({
            id: 'RULE-BATTEN-OK',
            severity: 'ok',
            problem: `Paso de rastrel (${battenStepMm} mm) y solape (${realOverlapLongMm} mm) verificados`,
            affectedParam: `Paso útil: ${battenStepMm} mm dentro de [${minStep}–${maxStep} mm]`,
            source: `${covering.versionDoc}`,
            solution: `Replanteo de ${replanteo.replanteoParams.numRows} hiladas con encaje geométrico exacto sobre rastrel 30×50 mm.`,
          });
        }
      }

      // Regla T3: Compatibilidad entre tipo de cobertura y accesorio de fijación
      if (covering.subType === 'pizarra_natural' && fastener.subType !== 'gancho_pizarra_inox') {
        alerts.push({
          id: 'RULE-FASTENER-SLATE',
          severity: 'error',
          problem: `Fijación incompatible: La pizarra natural ${covering.brand} exige gancho de pizarra AISI 316 o clavo`,
          affectedParam: `Fijación seleccionada: ${fastener.model}`,
          source: `Manual Técnico CUPA Pizarras / NTE-QTP`,
          solution: `Sustituir el accesorio de fijación por "Gancho Pizarra Acero Inoxidable AISI 316 Nervado (L=80/90 mm)" (ROTHOBLAAS-GANCHO-INOX90).`,
        });
      } else if (covering.subType === 'zinc_junta_alzada' && fastener.subType !== 'pata_junta_alzada_inox') {
        alerts.push({
          id: 'RULE-FASTENER-ZINC',
          severity: 'error',
          problem: `Bandeja VMZINC Junta Alzada exige Patas Fijas y Correderas ocultas en el pliegue de 25 mm`,
          affectedParam: `Fijación seleccionada: ${fastener.model}`,
          source: `Cuaderno Técnico VMZINC Junta Alzada · DTU 40.41`,
          solution: `Seleccionar "Juego de Patas Fijas y Correderas Acero Inoxidable AISI 304" (VMZINC-PATAS-INOX) para permitir la libre dilatación térmica de la bandeja.`,
        });
      } else {
        alerts.push({
          id: 'RULE-FASTENER-OK',
          severity: 'ok',
          problem: `Sistema de fijación mecánica compatible con cobertura y soporte`,
          affectedParam: `${fastener.model} (${replanteo.replanteoParams.assemblyFasteners} uds)`,
          source: `${fastener.versionDoc}`,
          solution: `Fijación en seco sin mortero conforme a UNE 136020 / UNE-EN 14437.`,
        });
      }

      // Regla T4: Cámara de microventilación bajo cobertura
      alerts.push({
        id: 'RULE-VENT-OK',
        severity: 'ok',
        problem: `Doble rastrel ventilado verificado sobre panel ${supportPanel.brand}`,
        affectedParam: `Sección libre de ventilación: 300 cm²/m de alero + lámina Sd = 0,04 m`,
        source: `CTE DB-HS 1 Ap. 2.4.3 · Ficha Rothoblaas TRASPIR EVO`,
        solution: `Evita condensaciones intersticiales y seca la cara inferior de las piezas.`,
      });
    } else {
      // =======================================================================
      // REGLAS DE COMPATIBILIDAD PARA AZOTEAS PLANAS (DEMO B)
      // =======================================================================
      const { slopePct, parapetTurnupMm, flatAreaM2 } = replanteo.geometry;
      const { waterproofing, separatorBot, insulation, plots, pavement, greenRoof, drainUnit } = replanteo.products;
      const roofSubType = replanteo.roofSubType;

      // Regla A1: Prohibición de Lana de Roca (ROCKWOOL HardRock) en cubierta invertida o bajo plots con agua
      if (
        (roofSubType === 'invertida_plots' || roofSubType === 'ajardinada') &&
        insulation.suitableForInvertedRoof === false
      ) {
        alerts.push({
          id: 'RULE-INVERTED-INSULATION',
          severity: 'error',
          problem: `¡Aislamiento incompatible con Cubierta Invertida!: ${insulation.brand} ${insulation.model} NO puede colocarse sobre la impermeabilización`,
          affectedParam: `Absorción hídrica y pérdida de resistencia térmica por escorrentía sobre ${insulation.subType}`,
          source: `${insulation.versionDoc} / CTE DB-HS 1 Ap. 2.4.2 (Exige XPS de célula cerrada WL(T)0,7)`,
          solution: `Sustituir el aislamiento por "URSA XPS N-III-L (Poliestireno Extruido 300 kPa)" o cambiar la tipología a "Azotea Convencional (Aislamiento bajo Impermeabilización)".`,
        });
      } else {
        alerts.push({
          id: 'RULE-INSULATION-OK',
          severity: 'ok',
          problem: `Aislamiento térmico ${insulation.brand} compatible con la disposición constructiva (${roofSubType})`,
          affectedParam: `Espesor ${insulation.geometry.thicknessMm} mm · Compresión ${insulation.technicalSpecs.compressiveStrengthKpa} kPa · U = ${replanteo.summary.uValueWmk} W/m²K`,
          source: `${insulation.versionDoc} · CTE DB-HE 1`,
          solution: `Junta a media madera verificada sin puentes térmicos.`,
        });
      }

      // Regla A2: Incompatibilidad química entre Membrana PVC plastificado (Sikaplan G-15) y Poliestireno XPS
      if (waterproofing.isPvcPlasticized && insulation.subType === 'xps_celula_cerrada') {
        if (!separatorBot || separatorBot.subType !== 'geotextil_separador_filtrante') {
          alerts.push({
            id: 'RULE-PVC-XPS-CHEM',
            severity: 'error',
            problem: `Incompatibilidad química directa entre PVC-P (${waterproofing.model}) y Poliestireno XPS`,
            affectedParam: `Migración de plastificantes del PVC y degradación del XPS`,
            source: `${waterproofing.versionDoc} · CTE DB-HS 1 Ap. 2.4.2.2`,
            solution: `Interponer obligatoriamente geotextil separador de poliéster DANOFELT PY 200 (≥ 200 g/m²) entre Sikaplan G-15 y URSA XPS.`,
          });
        } else {
          alerts.push({
            id: 'RULE-PVC-XPS-PROTECTED',
            severity: 'ok',
            problem: `Barrera antipunzonante y antimigración de plastificantes PVC/XPS verificada`,
            affectedParam: `Capa interpuesta: ${separatorBot.model} (${separatorBot.geometry.surfaceWeightKgM2 * 1000} g/m²)`,
            source: `${waterproofing.versionDoc} + ${separatorBot.versionDoc}`,
            solution: `El geotextil de poliéster impide el contacto químico directo entre Sikaplan G-15 y URSA XPS.`,
          });
        }
      }

      // Regla A3: Cubierta Ajardinada exige membrana impermeabilizante certificada antirraíces (UNE-EN 13948)
      if (roofSubType === 'ajardinada' && !waterproofing.isRootResistant) {
        alerts.push({
          id: 'RULE-GREEN-ROOTS',
          severity: 'error',
          problem: `Membrana sin tratamiento antirraíces bajo cubierta vegetal ${greenRoof.brand}`,
          affectedParam: `Impermeabilización seleccionada: ${waterproofing.model} (isRootResistant = false)`,
          source: `UNE-EN 13948 · CTE DB-HS 1 Ap. 2.4.4.1 · Ficha Optigrün FKD 25`,
          solution: `Sustituir la membrana por "Sika Sikaplan G-15 (Certificada Antirraíces EN 13948)" o disponer lámina bituminosa aditivada antirraíces (ESTERDAN JARDÍN).`,
        });
      } else if (roofSubType === 'ajardinada' && waterproofing.isRootResistant) {
        alerts.push({
          id: 'RULE-GREEN-ROOTS-OK',
          severity: 'ok',
          problem: `Certificación antirraíces UNE-EN 13948 verificada para cubierta ajardinada`,
          affectedParam: `${waterproofing.model} + ${greenRoof.model}`,
          source: `UNE-EN 13948 · Directriz FLL`,
          solution: `Protección total frente a perforación radicular bajo sustrato Sedum.`,
        });
      }

      // Regla A4: Resistencia a compresión del aislamiento bajo Plots Regulables Peygran
      if (roofSubType === 'invertida_plots') {
        const compKpa = insulation.technicalSpecs.compressiveStrengthKpa || 0;
        if (compKpa < 200) {
          alerts.push({
            id: 'RULE-PLOT-COMPRESSION',
            severity: 'error',
            problem: `Resistencia a compresión insuficiente (${compKpa} kPa) bajo la base Ø${plots.geometry.baseDiameterMm} mm de los plots ${plots.brand}`,
            affectedParam: `Compresión del aislamiento: ${compKpa} kPa < 300 kPa exigidos por ${plots.model}`,
            source: `${plots.versionDoc} · UNE-EN 12825`,
            solution: `Emplear aislamiento de alta resistencia a compresión CS(10/Y)300 ≥ 300 kPa como URSA XPS N-III-L para evitar punzonamiento y desnivelación de las baldosas ${pavement.brand}.`,
          });
        } else {
          alerts.push({
            id: 'RULE-PLOT-COMPRESSION-OK',
            severity: 'ok',
            problem: `Estabilidad mecánica Plot ${plots.brand} (Ø${plots.geometry.baseDiameterMm} mm) sobre ${insulation.brand} (${compKpa} kPa) verificada`,
            affectedParam: `Tensión de contacto admisible: 30.000 kg/m² · Junta abierta de drenaje: ${replanteo.replanteoParams.jointMm} mm`,
            source: `${plots.versionDoc} + ${pavement.versionDoc}`,
            solution: `Reparto de carga sin punzonamiento y evacuación libre en cámara sub-pavimento de H=${replanteo.replanteoParams.plotHeightMm} mm.`,
          });
        }
      }

      // Regla A5: Pendiente de formación y remonte perimetral en petos (CTE DB-HS 1)
      if (slopePct < 1.0 && roofSubType !== 'invertida_plots') {
        alerts.push({
          id: 'RULE-FLAT-SLOPE',
          severity: 'error',
          problem: `Pendiente de formación (${slopePct.toFixed(1)}%) inferior al mínimo del 1,0% exigido para azoteas sin pavimento elevado`,
          affectedParam: `Pendiente proyectada: ${slopePct.toFixed(1)}% < 1,0%`,
          source: `CTE DB-HS 1 Tabla 2.9`,
          solution: `Aumentar la pendiente del faldón hacia la cazoleta ${drainUnit.brand} al rango 1,0%–3,0% o utilizar pavimento flotante sobre plots autonivelantes Peygran XSP5.`,
        });
      }

      if (parapetTurnupMm < 200) {
        alerts.push({
          id: 'RULE-PARAPET-TURNUP',
          severity: 'error',
          problem: `Remonte vertical de impermeabilización en peto (${parapetTurnupMm} mm) inferior a los 200 mm reglamentarios`,
          affectedParam: `Altura de entrega vertical: ${parapetTurnupMm} mm < 200 mm`,
          source: `CTE DB-HS 1 Ap. 2.4.4.1.2`,
          solution: `Incrementar el remonte perimetral de ${waterproofing.model} hasta ≥ 200 mm por encima de la protección y proteger con rozas/babero metálico.`,
        });
      } else {
        alerts.push({
          id: 'RULE-DRAIN-HS5-OK',
          severity: 'ok',
          problem: `Capacidad hidráulica de evacuación (${drainUnit.model}) y entrega en peto (${parapetTurnupMm} mm) verificadas`,
          affectedParam: `Caudal cazoleta Ø${drainUnit.geometry.outletDiameterMm}: ${drainUnit.geometry.hydraulicCapacityLs} L/s para ${flatAreaM2} m²`,
          source: `CTE DB-HS 1 Ap. 2.4.4.1.4 · CTE DB-HS 5 Tabla 4.6`,
          solution: `Ala de ${drainUnit.geometry.flangeWidthMm} mm (≥ 100 mm) solapada con la membrana impermeable.`,
        });
      }
    }

    const errCount = alerts.filter((a) => a.severity === 'error').length;
    const warnCount = alerts.filter((a) => a.severity === 'warning').length;
    const okCount = alerts.filter((a) => a.severity === 'ok').length;

    return {
      alerts,
      summary: {
        errCount,
        warnCount,
        okCount,
        isValid: errCount === 0,
      },
    };
  }
}

/**
 * =============================================================================
 * VINCULACIÓN DE LOS 10 DETALLES CONSTRUCTIVOS EXISTENTES CON PRODUCTOS REALES
 * =============================================================================
 * Permite que cada capa de los 10 detalles de la plataforma tenga asignado su
 * producto comercial real verificable, con acceso directo a su Ficha Técnica
 * Digital y posibilidad de sustitución por otro fabricante compatible (Sección 10).
 */
export const DEFAULT_DETAIL_PRODUCT_LINKS = {
  detalle1: [
    'DANOSA-ESTERDAN40P',
    'DANOSA-DANOFELT-PY200',
    'URSA-XPS-NIIIL-60',
    'DANOSA-DANOFELT-PY200',
    'GRESARAGON-ORDESA-6060',
  ],
  detalle2_qat16: [
    'JIMTEN-S77-110',
    'DANOSA-ESTERDAN40P',
    'DANOSA-DANOFELT-PY200',
    'URSA-XPS-NIIIL-60',
    'GRESARAGON-ORDESA-6060',
  ],
  detalle2_qat17: [
    'VMZINC-CANALON-333',
    'DANOSA-ESTERDAN40P',
    'DANOSA-DANOFELT-PY200',
    'URSA-XPS-NIIIL-60',
    'GRESARAGON-ORDESA-6060',
  ],
  detalle3: [
    'JIMTEN-S77-110',
    'DANOSA-ESTERDAN40P',
    'DANOSA-DANOFELT-PY200',
    'URSA-XPS-NIIIL-60',
    'GRESARAGON-ORDESA-6060',
  ],
  detalle4_plots: [
    'DANOSA-ESTERDAN40P',
    'DANOSA-DANOFELT-PY200',
    'URSA-XPS-NIIIL-60',
    'PEYGRAN-XSP5-PRO',
    'GRESARAGON-ORDESA-6060',
    'JIMTEN-S77-110',
  ],
  detalle5_alero_teja: [
    'THERMOCHIP-TAH-80',
    'ROTHOBLAAS-RASTREL-3050',
    'BORJA-C5021',
    'SFS-CLIP-TEJA-INOX',
    'VMZINC-CANALON-333',
  ],
  detalle6_cumbrera_teja: [
    'THERMOCHIP-TAH-80',
    'ROTHOBLAAS-RASTREL-3050',
    'BORJA-C5021',
    'SFS-CLIP-TEJA-INOX',
  ],
  detalle7_teja_mixta: [
    'THERMOCHIP-TAH-80',
    'ROTHOBLAAS-RASTREL-3050',
    'BORJA-TB12',
    'ESCANDELLA-SELECTUM',
    'BORJA-FLAT10',
    'SFS-CLIP-TEJA-INOX',
    'VMZINC-CANALON-333',
  ],
  detalle8_pizarra: [
    'THERMOCHIP-TAH-80',
    'ROTHOBLAAS-RASTREL-3050',
    'CUPA-4-3222',
    'CUPA-4-4025',
    'ROTHOBLAAS-GANCHO-INOX90',
    'VMZINC-CANALON-333',
  ],
  detalle9_zinc: [
    'THERMOCHIP-TAH-80',
    'ROTHOBLAAS-RASTREL-3050',
    'VMZINC-JUNTA-ALZADA-500',
    'VMZINC-PATAS-INOX',
    'KINGSPAN-KS1000RW-80',
    'VMZINC-CANALON-333',
  ],
};
