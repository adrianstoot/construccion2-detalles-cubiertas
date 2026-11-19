/**
 * =============================================================================
 * ROOFLAB ETSIE · CONSTRUCCIÓN II (UPV)
 * ENSAMBLADOR 3D PIEZA A PIEZA Y CAPA A CAPA + PLANO CAD 2D DE REPLANTEO
 * =============================================================================
 * Cumple las Secciones 6, 7, 8, 11, 12 y 15 del Master Prompt:
 * - Geometría tridimensional real para cada pieza individual (Prohibido usar un
 *   plano continuo texturizado para simular tejas, pizarras, bandejas o baldosas).
 * - DEMO A (Tejado): Pares estructurales, paneles Thermochip TAH individuales,
 *   lámina transpirable Rothoblaas, contrarastreles, rastreles horizontales
 *   separados exactamente al paso calculado (battenStepMm), tejas individuales
 *   diferenciando Canal y Cobija (C-50.21), mixtas (TB-12 / Selectum), planas
 *   (FLAT-10), lajas de pizarra a matajunta (CUPA 4), bandejas engatilladas
 *   (VMZINC Junta Alzada), paneles sándwich (Kingspan KS1000 RW) o placas
 *   onduladas (Euronit Granonda), más clips/ganchos inoxidables y canalón VMZINC.
 * - DEMO B (Azotea): Forjado y pendiente hacia caja PTL-7, cazoleta sifónica
 *   Jimten S-77 Ø110, bandas de impermeabilización DANOSA / Sikaplan con solapes
 *   de 80 mm y remonte de 200 mm en peto, geotextil DANOFELT PY 200, planchas
 *   individuales URSA XPS N-III-L a media madera (o ROCKWOOL HardRock), plots
 *   regulables individuales Peygran XSP5 Pro en cada encuentro de 4 baldosas,
 *   y baldosas individuales Gres Aragón Ordesa 20mm con junta abierta de 4 mm
 *   (o sistema ajardinado Optigrün FKD 25 + sustrato + Sedum).
 */

import * as THREE from '../vendor/three.module.min.js';
import { OrbitControls } from '../vendor/OrbitControls.js';
import { RoomEnvironment } from '../vendor/RoomEnvironment.js';

export class BIMAssembler3D {
  constructor(canvas, onPieceSelected) {
    this.canvas = canvas;
    this.onPieceSelected = onPieceSelected || (() => {});

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.rootGroup = null;
    this.highlightMesh = null;

    this.textures = {};
    this.layerGroups = [];
    this.layerStates = {}; // { [layerKey]: { visible: true, transparent: false } }
    this.interactivePieces = []; // Array de meshes o entradas instanciadas para raycasting y montaje pieza a pieza
    this.orderedPieceEntries = []; // Orden cronológico de montaje pieza a pieza (0..N-1)

    this.assemblyProgress = 1.0; // 0.0 a 1.0
    this.explodeFactor = 0.0;    // 0.0 a 1.0
    this.isPlayingAssembly = false;
    this.selectedPieceMeta = null;
    this.currentReplanteo = null;

    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this._pointerDownPos = { x: 0, y: 0 };
    this._animFrameId = null;

    this._initEngine();
  }

  _initEngine() {
    if (!this.canvas) return;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0b1017);

    const w = this.canvas.clientWidth || 900;
    const h = this.canvas.clientHeight || 560;

    this.camera = new THREE.PerspectiveCamera(38, w / h, 0.05, 120);
    this.camera.position.set(5.4, 4.2, 5.8);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: true,
    });
    this.renderer.setSize(w, h, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    // Iluminación IBL físicamente calibrada
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

    const hemiLight = new THREE.HemisphereLight(0xe2f1ff, 0x1e2630, 0.85);
    this.scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfff6e5, 2.2);
    sunLight.position.set(7.5, 11.0, 6.5);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.set(2048, 2048);
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 32;
    const d = 5.5;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    sunLight.shadow.bias = -0.0004;
    this.scene.add(sunLight);

    const rimLight = new THREE.DirectionalLight(0x7cc4ff, 0.65);
    rimLight.position.set(-6.0, 4.5, -5.0);
    this.scene.add(rimLight);

    // Suelo técnico de referencia
    const grid = new THREE.GridHelper(14, 28, 0x1e3a5f, 0x152232);
    grid.position.y = -0.55;
    this.scene.add(grid);

    this.rootGroup = new THREE.Group();
    this.scene.add(this.rootGroup);

    // Caja de resaltado para pieza seleccionada
    const hlGeo = new THREE.BoxGeometry(1, 1, 1);
    const hlMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      wireframe: true,
      transparent: true,
      opacity: 0.9,
    });
    this.highlightMesh = new THREE.Mesh(hlGeo, hlMat);
    this.highlightMesh.visible = false;
    this.scene.add(this.highlightMesh);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.07;
    this.controls.target.set(0, 0.35, 0);
    this.controls.maxDistance = 24;
    this.controls.minDistance = 0.7;

    this._loadTextures();
    this._bindEvents();
    this._startLoop();
  }

  _loadTextures() {
    const loader = new THREE.TextureLoader();
    const pbrSets = {
      concrete: 'structural_concrete',
      cellular_concrete: 'cellular_concrete',
      bitumen: 'bitumen',
      membrane_granule: 'membrane_granule',
      geotextile: 'geotextile',
      xps_foam: 'xps_foam',
      mortar: 'mortar',
      terracotta: 'terracotta',
      teja_curva: 'teja_curva',
      teja_mixta: 'teja_mixta',
      teja_plana: 'terracotta',
      wood_pine: 'wood_pine',
      slate_cupa: 'slate_pizarra',
      slate_pizarra: 'slate_pizarra',
      zinc_vmz: 'zinc_vmz',
      brushed_metal: 'brushed_metal',
      gravel: 'concrete_paver',
      fiberglass: 'fiberglass',
    };

    const loadedFiles = {};
    const loadMap = (fileBase, isColor = true) => {
      if (loadedFiles[fileBase]) return loadedFiles[fileBase];
      const tex = loader.load(`./textures/${fileBase}.png`);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      if (isColor) tex.colorSpace = THREE.SRGBColorSpace;
      loadedFiles[fileBase] = tex;
      return tex;
    };

    Object.entries(pbrSets).forEach(([key, filePrefix]) => {
      this.textures[key] = {
        albedo: loadMap(`${filePrefix}_albedo`, true),
        normal: loadMap(`${filePrefix}_normal`, false),
        rough: loadMap(`${filePrefix}_rough`, false),
      };
    });
  }

  _makeMaterial(opts = {}) {
    const matOpts = {
      color: opts.color || 0xcccccc,
      roughness: opts.roughness ?? 0.65,
      metalness: opts.metalness ?? 0.05,
      side: THREE.DoubleSide,
    };
    const pbr = opts.textureKey ? this.textures[opts.textureKey] : null;
    if (pbr && pbr.albedo) {
      matOpts.map = pbr.albedo;
      matOpts.normalMap = pbr.normal;
      matOpts.normalScale = new THREE.Vector2(0.55, 0.55);
      matOpts.roughnessMap = pbr.rough;
    }
    return new THREE.MeshStandardMaterial(matOpts);
  }

  _bindEvents() {
    const dom = this.renderer.domElement;
    dom.addEventListener('pointerdown', (e) => {
      this._pointerDownPos = { x: e.clientX, y: e.clientY };
    });

    dom.addEventListener('pointerup', (e) => {
      if (e.target !== dom) return;
      const dx = Math.abs(e.clientX - this._pointerDownPos.x);
      const dy = Math.abs(e.clientY - this._pointerDownPos.y);
      if (dx > 5 || dy > 5) return; // Fue arrastre de cámara
      this._pickPieceAtEvent(e);
    });

    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas || !this.renderer || !this.camera) return;
    const parent = this.canvas.parentElement;
    const w = (parent && parent.clientWidth) || this.canvas.clientWidth || 900;
    const h = (parent && parent.clientHeight) || this.canvas.clientHeight || 560;
    if (w < 40 || h < 40) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  }

  _startLoop() {
    const tick = () => {
      this._animFrameId = requestAnimationFrame(tick);
      if (this.isPlayingAssembly) {
        this.assemblyProgress += 0.0045;
        if (this.assemblyProgress >= 1.0) {
          this.assemblyProgress = 1.0;
          this.isPlayingAssembly = false;
          if (this.onProgressChange) this.onProgressChange(1.0, false);
        } else if (this.onProgressChange) {
          this.onProgressChange(this.assemblyProgress, true);
        }
        this._applyAssemblyProgress();
      }
      if (this.controls) this.controls.update();
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    };
    tick();
  }

  /**
   * Reconstruye por completo la escena 3D a partir del replanteo calculado (DEMO A o DEMO B).
   */
  buildFromReplanteo(replanteo) {
    this.currentReplanteo = replanteo;
    this._clearScene();

    if (replanteo.systemType === 'tejado') {
      this._buildSlopedRoof3D(replanteo);
    } else {
      this._buildFlatRoof3D(replanteo);
    }

    this._applyLayerStates();
    this._applyExplodeFactor();
    this._applyAssemblyProgress();
  }

  _clearScene() {
    while (this.rootGroup.children.length > 0) {
      const child = this.rootGroup.children[0];
      this.rootGroup.remove(child);
    }
    this.layerGroups = [];
    this.interactivePieces = [];
    this.orderedPieceEntries = [];
    this.highlightMesh.visible = false;
  }

  _createLayerGroup(key, title, orderIndex, product, baseExplodeStep = 0.25) {
    const group = new THREE.Group();
    group.name = key;
    group.userData = {
      layerKey: key,
      title,
      orderIndex,
      productId: product ? product.id : null,
      productName: product ? `${product.brand} · ${product.model}` : title,
      baseY: 0,
      explodeStep: baseExplodeStep,
    };
    if (!this.layerStates[key]) {
      this.layerStates[key] = { visible: true, transparent: false };
    }
    this.rootGroup.add(group);
    this.layerGroups.push(group);
    return group;
  }

  _registerPieceMesh(mesh, meta) {
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData = {
      isBIMPiece: true,
      ...meta,
      targetScale: mesh.scale.clone(),
    };
    this.interactivePieces.push(mesh);
    this.orderedPieceEntries.push({ type: 'mesh', mesh, meta });
  }

  // ===========================================================================
  // CONSTRUCCIÓN 3D DEMO A: TEJADO INCLINADO PIEZA A PIEZA
  // ===========================================================================
  _buildSlopedRoof3D(rep) {
    // Acotamos el fragmento físico renderizado en 3D a un módulo demostrativo de alta densidad
    // (máx 3.2 m × 2.8 m) para que cada teja, rastrel, clip y canalón se distinga con nitidez absoluta,
    // manteniendo las dimensiones exactas en milímetros de cada producto comercial.
    const visWidthM = Math.min(rep.geometry.widthM, 3.0);
    const visHorizLenM = Math.min(rep.geometry.lengthHorizM, 3.2);
    const slopePct = rep.geometry.slopePct;
    const slopeAngle = Math.atan(slopePct / 100);
    const visRafterLenM = visHorizLenM * Math.sqrt(1 + Math.pow(slopePct / 100, 2));

    const { supportPanel, battenSys, covering, fastener, gutter } = rep.products;
    const stepM = rep.replanteoParams.battenStepMm / 1000;
    const supportStepM = rep.replanteoParams.supportBattenStepMm / 1000;
    const usefulWidM = rep.replanteoParams.usefulWidthMm / 1000;

    // Grupo contenedor inclinado según la pendiente real del faldón
    const pitchPivot = new THREE.Group();
    pitchPivot.rotation.x = slopeAngle;
    pitchPivot.position.set(0, 0.45, 0);
    this.rootGroup.add(pitchPivot);

    const addPitchLayer = (key, title, orderIndex, prod, explodeStep) => {
      const g = new THREE.Group();
      g.name = key;
      g.userData = {
        layerKey: key,
        title,
        orderIndex,
        productId: prod ? prod.id : null,
        productName: prod ? `${prod.brand} · ${prod.model}` : title,
        baseY: 0,
        explodeStep,
      };
      if (!this.layerStates[key]) {
        this.layerStates[key] = { visible: true, transparent: false };
      }
      pitchPivot.add(g);
      this.layerGroups.push(g);
      return g;
    };

    // -------------------------------------------------------------------------
    // CAPA 1: PARES ESTRUCTURALES DE MADERA LAMINADA (80×160 mm cada 600 mm)
    // -------------------------------------------------------------------------
    const gRafters = addPitchLayer(
      'L1_PARES',
      '1. Estructura de Pares (Madera GL24h 80×160 mm)',
      1,
      supportPanel,
      0.22
    );
    const rafterMat = this._makeMaterial({
      color: 0xb78652,
      textureKey: 'wood_pine',
      roughness: 0.72,
      repeat: [1, 4],
    });
    const numVisRafters = Math.floor(visWidthM / 0.60) + 1;
    const startX = -visWidthM / 2;

    for (let i = 0; i < numVisRafters; i++) {
      const rx = Math.min(visWidthM / 2, startX + i * 0.60);
      const rGeo = new THREE.BoxGeometry(0.08, 0.16, visRafterLenM);
      const rMesh = new THREE.Mesh(rGeo, rafterMat);
      rMesh.position.set(rx, -0.08, 0);
      gRafters.add(rMesh);
      this._registerPieceMesh(rMesh, {
        pieceCode: `PAR-E${String(i + 1).padStart(2, '0')}`,
        layerKey: 'L1_PARES',
        layerName: 'Estructura de Pares GL24h',
        productId: supportPanel.id,
        roleLabel: 'Par estructural de cubierta inclinada',
        row: 1,
        col: i + 1,
        dimensionsMm: `80 × 160 × ${Math.round(visRafterLenM * 1000)} mm (Intereje 600 mm)`,
        weightKg: Number((visRafterLenM * 6.2).toFixed(1)),
      });
    }

    // -------------------------------------------------------------------------
    // CAPA 2: PANELES SÁNDWICH THERMOCHIP TAH (2400×550×e mm)
    // -------------------------------------------------------------------------
    const panelThickM = (supportPanel.geometry.thicknessMm || 109) / 1000;
    const gPanels = addPitchLayer(
      'L2_SOPORTE',
      `2. Panel Sándwich ${supportPanel.brand} (${supportPanel.geometry.thicknessMm} mm)`,
      2,
      supportPanel,
      0.26
    );
    const woodFaceMat = this._makeMaterial({
      color: 0xd7b377,
      textureKey: 'wood_pine',
      roughness: 0.68,
      repeat: [2, 1],
    });
    const xpsCoreMat = this._makeMaterial({
      color: 0x38bdf8,
      textureKey: 'xps_foam',
      roughness: 0.55,
    });

    const pLenM = Math.min(visWidthM / 2 - 0.004, 1.48);
    const pWidM = 0.545;
    const pRows = Math.ceil(visRafterLenM / pWidM);
    let pIdx = 1;

    for (let r = 0; r < pRows; r++) {
      const zCenter = -visRafterLenM / 2 + (r + 0.5) * (visRafterLenM / pRows);
      const actualPWid = visRafterLenM / pRows - 0.004;
      for (let c = 0; c < 2; c++) {
        const xCenter = c === 0 ? -visWidthM / 4 : visWidthM / 4;
        const pGroup = new THREE.Mesh(
          new THREE.BoxGeometry(pLenM, panelThickM, actualPWid),
          xpsCoreMat
        );
        // Tablero superior hidrófugo 19 mm y friso inferior 10 mm
        const topBoard = new THREE.Mesh(
          new THREE.BoxGeometry(pLenM, 0.016, actualPWid),
          woodFaceMat
        );
        topBoard.position.y = panelThickM / 2 - 0.008;
        pGroup.add(topBoard);

        const botBoard = new THREE.Mesh(
          new THREE.BoxGeometry(pLenM, 0.012, actualPWid),
          woodFaceMat
        );
        botBoard.position.y = -panelThickM / 2 + 0.006;
        pGroup.add(botBoard);

        pGroup.position.set(xCenter, panelThickM / 2, zCenter);
        gPanels.add(pGroup);

        this._registerPieceMesh(pGroup, {
          pieceCode: `TAH-F${String(r + 1).padStart(2, '0')}-C${c + 1}`,
          layerKey: 'L2_SOPORTE',
          layerName: supportPanel.model,
          productId: supportPanel.id,
          roleLabel: 'Panel sándwich machihembrado de soporte y aislamiento',
          row: r + 1,
          col: c + 1,
          dimensionsMm: `${supportPanel.geometry.lengthNominalMm} × ${supportPanel.geometry.widthNominalMm} × ${supportPanel.geometry.thicknessMm} mm`,
          weightKg: supportPanel.geometry.unitWeightKg,
        });
        pIdx++;
      }
    }

    // -------------------------------------------------------------------------
    // CAPA 3: LÁMINA IMPERMEABLE TRANSPIRABLE ROTHOBLAAS TRASPIR EVO
    // -------------------------------------------------------------------------
    const gMembrane = addPitchLayer(
      'L3_LAMINA',
      '3. Lámina Transpirable Rothoblaas TRASPIR EVO (Sd=0,04 m)',
      3,
      battenSys,
      0.34
    );
    const membMat = this._makeMaterial({
      color: 0x2a3441,
      textureKey: 'geotextile',
      roughness: 0.78,
      repeat: [4, 4],
    });
    const stripeMat = new THREE.MeshBasicMaterial({ color: 0xf97316 }); // Línea de solape sellado 100 mm

    const numBands = 3;
    const bandDepth = visRafterLenM / numBands;
    for (let b = 0; b < numBands; b++) {
      // De alero (+Z) a cumbrera (-Z)
      const zPos = visRafterLenM / 2 - (b + 0.5) * bandDepth;
      const bandMesh = new THREE.Mesh(
        new THREE.BoxGeometry(visWidthM + 0.02, 0.004, bandDepth + 0.08),
        membMat
      );
      bandMesh.position.set(0, panelThickM + 0.003 + b * 0.001, zPos);

      // Cinta de solape adhesivo Rothoblaas
      const tapeMesh = new THREE.Mesh(
        new THREE.BoxGeometry(visWidthM + 0.022, 0.0015, 0.025),
        stripeMat
      );
      tapeMesh.position.set(0, 0.0025, -bandDepth / 2 + 0.04);
      bandMesh.add(tapeMesh);

      gMembrane.add(bandMesh);
      this._registerPieceMesh(bandMesh, {
        pieceCode: `TRASPIR-BANDA-0${b + 1}`,
        layerKey: 'L3_LAMINA',
        layerName: 'Lámina Transpirable Rothoblaas TRASPIR EVO 210',
        productId: battenSys.id,
        roleLabel: 'Banda impermeable transpirable con solape adhesivo de 100 mm',
        row: b + 1,
        col: 1,
        dimensionsMm: `Ancho rollo 1500 mm · Solape 100 mm · e=0,85 mm`,
        weightKg: Number((visWidthM * bandDepth * 0.21).toFixed(2)),
      });
    }

    // -------------------------------------------------------------------------
    // CAPA 4: CONTRARASTRELES Y RASTRELES HORIZONTALES AL PASO EXACTO
    // -------------------------------------------------------------------------
    const gBattens = addPitchLayer(
      'L4_RASTRELES',
      `4. Doble Rastrel Ventilado (Paso exacto = ${rep.replanteoParams.supportBattenStepMm} mm)`,
      4,
      battenSys,
      0.42
    );
    const battenMat = this._makeMaterial({
      color: 0xc29862,
      textureKey: 'wood_pine',
      roughness: 0.65,
      repeat: [3, 1],
    });

    const baseBattenY = panelThickM + 0.006;
    const cbHeightM = 0.03; // Contrarastrel 50×30 mm
    const hbHeightM = (battenSys.geometry.thicknessMm || 30) / 1000;
    const hbWidthM = (battenSys.geometry.widthNominalMm || 50) / 1000;

    // 4A. Contrarastreles longitudinales (línea de máxima pendiente)
    for (let i = 0; i < numVisRafters; i++) {
      const rx = Math.min(visWidthM / 2, startX + i * 0.60);
      const cbMesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.05, cbHeightM, visRafterLenM),
        battenMat
      );
      cbMesh.position.set(rx, baseBattenY + cbHeightM / 2, 0);
      gBattens.add(cbMesh);
      this._registerPieceMesh(cbMesh, {
        pieceCode: `CONTRARASTREL-C${String(i + 1).padStart(2, '0')}`,
        layerKey: 'L4_RASTRELES',
        layerName: battenSys.model,
        productId: battenSys.id,
        roleLabel: 'Contrarastrel vertical de ventilación bajo teja (cámara libre 30 mm)',
        row: 1,
        col: i + 1,
        dimensionsMm: `50 × 30 × ${Math.round(visRafterLenM * 1000)} mm`,
        weightKg: Number((visRafterLenM * 0.72).toFixed(2)),
      });
    }

    // 4B. Rastreles horizontales separados exactamente a supportStepM (Paso de rastrel oficial)
    const visBattenRows = Math.floor(visRafterLenM / supportStepM);
    const horizontalBattenY = baseBattenY + cbHeightM + hbHeightM / 2;

    for (let r = 0; r <= visBattenRows; r++) {
      // Colocados desde el alero (+visRafterLenM/2) subiendo hacia cumbrera (-visRafterLenM/2)
      const zBatten = visRafterLenM / 2 - 0.06 - r * supportStepM;
      if (zBatten < -visRafterLenM / 2 + 0.03) break;

      const hbMesh = new THREE.Mesh(
        new THREE.BoxGeometry(visWidthM, hbHeightM, hbWidthM),
        battenMat
      );
      hbMesh.position.set(0, horizontalBattenY, zBatten);
      gBattens.add(hbMesh);
      this._registerPieceMesh(hbMesh, {
        pieceCode: `RASTREL-H${String(r + 1).padStart(2, '0')}`,
        layerKey: 'L4_RASTRELES',
        layerName: `${battenSys.model} (Hilada #${r + 1})`,
        productId: battenSys.id,
        roleLabel: `Rastrel horizontal de apoyo · Paso real = ${rep.replanteoParams.supportBattenStepMm} mm`,
        row: r + 1,
        col: 1,
        dimensionsMm: `${Math.round(visWidthM * 1000)} × ${battenSys.geometry.widthNominalMm} × ${battenSys.geometry.thicknessMm} mm (Paso ${rep.replanteoParams.supportBattenStepMm} mm)`,
        weightKg: Number((visWidthM * (battenSys.geometry.linearWeightKgM || 0.72)).toFixed(2)),
      });
    }

    // -------------------------------------------------------------------------
    // CAPA 5: CANALÓN SEMICIRCULAR VMZINC D333 Y GAFAS DE SOPORTE EN ALERO
    // -------------------------------------------------------------------------
    const gGutter = addPitchLayer(
      'L5_CANALON',
      `5. Evacuación de Alero ${gutter.brand} (Ø${gutter.geometry.widthNominalMm} mm)`,
      5,
      gutter,
      0.50
    );
    const zincMat = this._makeMaterial({
      color: 0x8e9ba8,
      textureKey: 'zinc_vmz',
      roughness: 0.35,
      metalness: 0.72,
    });
    const gutterRadiusM = (gutter.geometry.widthNominalMm || 153) / 2000;
    const gutterZ = visRafterLenM / 2 + gutterRadiusM + 0.02;
    const gutterY = baseBattenY - 0.02;

    const troughGeo = new THREE.CylinderGeometry(
      gutterRadiusM,
      gutterRadiusM,
      visWidthM + 0.12,
      24,
      1,
      true,
      0,
      Math.PI
    );
    troughGeo.rotateZ(-Math.PI / 2);
    const troughMesh = new THREE.Mesh(troughGeo, zincMat);
    troughMesh.position.set(0, gutterY, gutterZ);

    // Bordón enrollado frontal Ø14 mm
    const beadGeo = new THREE.CylinderGeometry(0.008, 0.008, visWidthM + 0.12, 14);
    beadGeo.rotateZ(Math.PI / 2);
    const beadMesh = new THREE.Mesh(beadGeo, zincMat);
    beadMesh.position.set(0, 0, gutterRadiusM);
    troughMesh.add(beadMesh);

    gGutter.add(troughMesh);
    this._registerPieceMesh(troughMesh, {
      pieceCode: `CANALON-VMZ-D${gutter.geometry.developmentMm || 333}`,
      layerKey: 'L5_CANALON',
      layerName: gutter.model,
      productId: gutter.id,
      roleLabel: 'Canalón semicircular de zinc-titanio con bordón exterior',
      row: 1,
      col: 1,
      dimensionsMm: `L=${Math.round(visWidthM * 1000)} mm · Ø${gutter.geometry.widthNominalMm} mm (Desarrollo ${gutter.geometry.developmentMm || 333} mm)`,
      weightKg: gutter.geometry.unitWeightKg,
    });

    // -------------------------------------------------------------------------
    // CAPA 6: COBERTURA EXTERIOR PIEZA A PIEZA (GEOMETRÍA 3D REAL POR PRODUCTO)
    // -------------------------------------------------------------------------
    const gCovering = addPitchLayer(
      'L6_COBERTURA',
      `6. Cobertura Pieza a Pieza: ${covering.brand} ${covering.model}`,
      6,
      covering,
      0.64
    );

    const tileBaseY = horizontalBattenY + hbHeightM / 2 + 0.004;
    const covMat = this._makeMaterial({
      color: covering.colorHex || '#b65338',
      textureKey: covering.textureKey || 'terracotta',
      roughness:
        covering.subType === 'zinc_junta_alzada' || covering.subType === 'panel_sandwich_metalico'
          ? 0.35
          : covering.subType === 'pizarra_natural'
          ? 0.48
          : 0.58,
      metalness:
        covering.subType === 'zinc_junta_alzada' || covering.subType === 'panel_sandwich_metalico'
          ? 0.68
          : 0.06,
    });

    const gFasteners = addPitchLayer(
      'L7_FIJACIONES',
      `7. Fijaciones Mecánicas (${fastener.brand}) y Cumbrera Ventilada`,
      7,
      fastener,
      0.78
    );
    const inoxMat = this._makeMaterial({
      color: 0xdbe4ee,
      textureKey: 'brushed_metal',
      roughness: 0.25,
      metalness: 0.88,
    });

    const lenNomM = (covering.geometry.lengthNominalMm || 450) / 1000;
    const widNomM = (covering.geometry.widthNominalMm || 260) / 1000;
    const visCols = Math.max(2, Math.floor(visWidthM / usefulWidM));
    const visRows = Math.max(1, Math.floor((visRafterLenM - 0.12) / stepM));

    if (covering.subType === 'teja_curva') {
      // =======================================================================
      // TEJA CURVA ÁRABE (BORJA C-50.21): DIFERENCIACIÓN REAL CANAL Y COBIJA
      // =======================================================================
      const rFront = (covering.geometry.widthFrontMm || 210) / 2000;
      const rRear = (covering.geometry.widthRearMm || 170) / 2000;

      // Geometría de canal (cóncava hacia arriba) y cobija (convexa hacia arriba)
      const canalGeo = new THREE.CylinderGeometry(rRear, rFront, lenNomM, 18, 1, true, 0, Math.PI);
      canalGeo.rotateY(-Math.PI / 2);
      canalGeo.rotateX(Math.PI / 2);

      const cobijaGeo = new THREE.CylinderGeometry(rFront, rRear, lenNomM, 18, 1, true, 0, Math.PI);
      cobijaGeo.rotateY(Math.PI / 2);
      cobijaGeo.rotateX(Math.PI / 2);

      const cobijaMat = covMat.clone();
      cobijaMat.color.offsetHSL(0.01, 0.04, 0.04);

      // 1º Se colocan todas las Tejas CANAL de alero a cumbrera
      for (let r = 0; r < visRows; r++) {
        const zCenter = visRafterLenM / 2 - lenNomM / 2 - r * stepM;
        const yRowLift = r * 0.008; // Escalonado de solape
        for (let c = 0; c < visCols; c++) {
          const xCenter = -((visCols - 1) * usefulWidM) / 2 + c * usefulWidM;
          const canalMesh = new THREE.Mesh(canalGeo, covMat);
          canalMesh.position.set(xCenter, tileBaseY + rFront * 0.95 + yRowLift, zCenter);
          canalMesh.rotation.x = -0.025;
          gCovering.add(canalMesh);

          const wFrontMm = covering.geometry.widthFrontMm || covering.geometry.widthNominalMm || 210;
          const wRearMm = covering.geometry.widthRearMm || covering.geometry.widthNarrowMm || 170;
          this._registerPieceMesh(canalMesh, {
            pieceCode: `CANAL-F${String(r + 1).padStart(2, '0')}-C${String(c + 1).padStart(2, '0')}`,
            layerKey: 'L6_COBERTURA',
            layerName: `${covering.model} (Posición CANAL)`,
            productId: covering.id,
            roleLabel: `Teja Curva CANAL (Escorrentía) · Hilada ${r + 1}, Columna ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${covering.geometry.lengthNominalMm} × ${wFrontMm}/${wRearMm} × ${covering.geometry.thicknessMm} mm (Solape ${rep.replanteoParams.realOverlapLongMm} mm)`,
            weightKg: covering.geometry.unitWeightKg,
          });
        }
      }

      // 2º Se colocan todas las Tejas COBIJA cubriendo las juntas entre canales
      for (let r = 0; r < visRows; r++) {
        const zCenter = visRafterLenM / 2 - lenNomM / 2 - r * stepM;
        const yRowLift = r * 0.008;
        for (let c = 0; c < visCols - 1; c++) {
          const xCenter = -((visCols - 1) * usefulWidM) / 2 + (c + 0.5) * usefulWidM;
          const cobijaMesh = new THREE.Mesh(cobijaGeo, cobijaMat);
          cobijaMesh.position.set(xCenter, tileBaseY + rFront * 0.95 + yRowLift, zCenter);
          cobijaMesh.rotation.x = -0.025;
          gCovering.add(cobijaMesh);

          const wFrontMm = covering.geometry.widthFrontMm || covering.geometry.widthNominalMm || 210;
          const wRearMm = covering.geometry.widthRearMm || covering.geometry.widthNarrowMm || 170;
          this._registerPieceMesh(cobijaMesh, {
            pieceCode: `COBIJA-F${String(r + 1).padStart(2, '0')}-C${String(c + 1).padStart(2, '0')}`,
            layerKey: 'L6_COBERTURA',
            layerName: `${covering.model} (Posición COBIJA)`,
            productId: covering.id,
            roleLabel: `Teja Curva COBIJA (Cubierta de junta) · Hilada ${r + 1}, Entre-canal ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${covering.geometry.lengthNominalMm} × ${wFrontMm}/${wRearMm} × ${covering.geometry.thicknessMm} mm (Solape ${rep.replanteoParams.realOverlapLongMm} mm)`,
            weightKg: covering.geometry.unitWeightKg,
          });

          // Gancho inoxidable SFS de sujeción de cobija en perímetro e interior
          if (r === 0 || r === visRows - 1 || (r + c) % 2 === 0) {
            const clipMesh = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.032, 0.045), inoxMat);
            clipMesh.position.set(
              xCenter,
              tileBaseY + rFront * 0.95 + yRowLift,
              zCenter + lenNomM / 2 - 0.015
            );
            gFasteners.add(clipMesh);
            this._registerPieceMesh(clipMesh, {
              pieceCode: `CLIP-SFS-F${r + 1}C${c + 1}`,
              layerKey: 'L7_FIJACIONES',
              layerName: fastener.model,
              productId: fastener.id,
              roleLabel: 'Gancho inoxidable AISI 304 de retención de cola de cobija',
              row: r + 1,
              col: c + 1,
              dimensionsMm: `${fastener.geometry.lengthNominalMm} × ${fastener.geometry.widthNominalMm} mm`,
              weightKg: fastener.geometry.unitWeightKg,
            });
          }
        }
      }
    } else if (covering.subType === 'teja_mixta') {
      // =======================================================================
      // TEJA MIXTA DE DOBLE ENCAJE (TEJAS BORJA TB-12 / LA ESCANDELLA SELECTUM)
      // =======================================================================
      for (let r = 0; r < visRows; r++) {
        const zCenter = visRafterLenM / 2 - lenNomM / 2 - r * stepM;
        const yRowLift = r * 0.007;
        for (let c = 0; c < visCols; c++) {
          const xCenter = -((visCols - 1) * usefulWidM) / 2 + c * usefulWidM;

          // Pieza compuesta por canal plano + onda curva lateral + nervio de encaje
          const tileContainer = new THREE.Mesh(
            new THREE.BoxGeometry(usefulWidM * 0.56, 0.014, lenNomM),
            covMat
          );
          tileContainer.position.set(xCenter, tileBaseY + 0.012 + yRowLift, zCenter);
          tileContainer.rotation.x = -0.022;

          const archGeo = new THREE.CylinderGeometry(
            usefulWidM * 0.27,
            usefulWidM * 0.29,
            lenNomM,
            14,
            1,
            true,
            0,
            Math.PI
          );
          archGeo.rotateY(Math.PI / 2);
          archGeo.rotateX(Math.PI / 2);
          const archMesh = new THREE.Mesh(archGeo, covMat);
          archMesh.position.set(usefulWidM * 0.23, 0.008, 0);
          tileContainer.add(archMesh);

          gCovering.add(tileContainer);

          this._registerPieceMesh(tileContainer, {
            pieceCode: `TEJA-MIXTA-F${String(r + 1).padStart(2, '0')}-C${String(c + 1).padStart(2, '0')}`,
            layerKey: 'L6_COBERTURA',
            layerName: covering.model,
            productId: covering.id,
            roleLabel: `Teja Mixta de Doble Encaje · Hilada ${r + 1}, Columna ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm} mm (Paso útil ${rep.replanteoParams.battenStepMm}×${rep.replanteoParams.usefulWidthMm} mm)`,
            weightKg: covering.geometry.unitWeightKg,
          });

          if (r === 0 || c === 0 || c === visCols - 1 || (r + c) % 3 === 0) {
            const clipMesh = new THREE.Mesh(new THREE.BoxGeometry(0.016, 0.024, 0.035), inoxMat);
            clipMesh.position.set(xCenter - usefulWidM * 0.45, tileBaseY + 0.012 + yRowLift, zCenter);
            gFasteners.add(clipMesh);
            this._registerPieceMesh(clipMesh, {
              pieceCode: `CLIP-SFS-F${r + 1}C${c + 1}`,
              layerKey: 'L7_FIJACIONES',
              layerName: fastener.model,
              productId: fastener.id,
              roleLabel: 'Clip lateral inoxidable SFS de fijación al rastrel',
              row: r + 1,
              col: c + 1,
              dimensionsMm: `${fastener.geometry.lengthNominalMm} × ${fastener.geometry.widthNominalMm} mm`,
              weightKg: fastener.geometry.unitWeightKg,
            });
          }
        }
      }
    } else if (covering.subType === 'teja_plana') {
      // =======================================================================
      // TEJA PLANA DE ENCAJE (TEJAS BORJA FLAT-10 TECH 475×285 mm)
      // =======================================================================
      for (let r = 0; r < visRows; r++) {
        const zCenter = visRafterLenM / 2 - lenNomM / 2 - r * stepM;
        const yRowLift = r * 0.006;
        // En teja plana se puede montar a junta corrida o a matajunta; mostramos un ligero bisel técnico
        for (let c = 0; c < visCols; c++) {
          const xCenter = -((visCols - 1) * usefulWidM) / 2 + c * usefulWidM;
          const flatMesh = new THREE.Mesh(
            new THREE.BoxGeometry(usefulWidM - 0.003, 0.018, lenNomM),
            covMat
          );
          // Escalonado frontal biselado
          const lipMesh = new THREE.Mesh(
            new THREE.BoxGeometry(usefulWidM - 0.006, 0.007, lenNomM * 0.78),
            covMat
          );
          lipMesh.position.set(0, 0.011, 0.02);
          flatMesh.add(lipMesh);

          flatMesh.position.set(xCenter, tileBaseY + 0.011 + yRowLift, zCenter);
          flatMesh.rotation.x = -0.018;
          gCovering.add(flatMesh);

          this._registerPieceMesh(flatMesh, {
            pieceCode: `FLAT10-F${String(r + 1).padStart(2, '0')}-C${String(c + 1).padStart(2, '0')}`,
            layerKey: 'L6_COBERTURA',
            layerName: covering.model,
            productId: covering.id,
            roleLabel: `Teja Cerámica Plana FLAT-10 · Hilada ${r + 1}, Columna ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm} mm (Paso ${rep.replanteoParams.battenStepMm} mm · Solape ${rep.replanteoParams.realOverlapLongMm} mm)`,
            weightKg: covering.geometry.unitWeightKg,
          });
        }
      }
    } else if (covering.subType === 'pizarra_natural') {
      // =======================================================================
      // PIZARRA NATURAL A MATAJUNTA Y TRIPLE SOLAPE (CUPA 4 32×22 / 40×25 cm)
      // =======================================================================
      const maxSlateRows = Math.min(visRows, 18);
      for (let r = 0; r < maxSlateRows; r++) {
        const zCenter = visRafterLenM / 2 - lenNomM / 2 - r * stepM;
        const yRowLift = r * 0.0025;
        const staggerX = (r % 2) * (usefulWidM / 2); // Colocación a matajunta

        for (let c = 0; c < visCols; c++) {
          const xCenter = -((visCols - 1) * usefulWidM) / 2 + c * usefulWidM + staggerX - usefulWidM * 0.25;
          if (Math.abs(xCenter) > visWidthM / 2 + 0.05) continue;

          const slateMesh = new THREE.Mesh(
            new THREE.BoxGeometry(usefulWidM - 0.003, 0.006, lenNomM),
            covMat
          );
          slateMesh.position.set(xCenter, tileBaseY + 0.005 + yRowLift, zCenter);
          slateMesh.rotation.x = -0.016;
          gCovering.add(slateMesh);

          this._registerPieceMesh(slateMesh, {
            pieceCode: `LAJA-CUPA4-F${String(r + 1).padStart(2, '0')}-C${String(c + 1).padStart(2, '0')}`,
            layerKey: 'L6_COBERTURA',
            layerName: covering.model,
            productId: covering.id,
            roleLabel: `Laja de Pizarra Natural a Matajunta · Hilada ${r + 1}, Posición ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm} × ${covering.geometry.thicknessMm} mm (Paso ${rep.replanteoParams.battenStepMm} mm · Solape ${rep.replanteoParams.realOverlapLongMm} mm)`,
            weightKg: covering.geometry.unitWeightKg,
          });

          // Gancho inoxidable visto en el borde inferior de cada laja de pizarra
          const hookMesh = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.014, 0.022), inoxMat);
          hookMesh.position.set(
            xCenter,
            tileBaseY + 0.007 + yRowLift,
            zCenter + lenNomM / 2 - 0.006
          );
          gFasteners.add(hookMesh);
          this._registerPieceMesh(hookMesh, {
            pieceCode: `GANCHO-INOX-F${r + 1}C${c + 1}`,
            layerKey: 'L7_FIJACIONES',
            layerName: fastener.model,
            productId: fastener.id,
            roleLabel: 'Gancho de acero inoxidable AISI 316 nervado para pizarra',
            row: r + 1,
            col: c + 1,
            dimensionsMm: `L=${fastener.geometry.lengthNominalMm} mm · Ø2,7 mm`,
            weightKg: fastener.geometry.unitWeightKg,
          });
        }
      }
    } else if (covering.subType === 'zinc_junta_alzada') {
      // =======================================================================
      // BANDEJAS DE ZINC ENGATILLADAS EN DOBLE JUNTA ALZADA (VMZINC 430 / 530 mm)
      // =======================================================================
      const seamHeightM = (covering.geometry.seamHeightMm || 25) / 1000;
      const trayCols = Math.max(2, Math.floor(visWidthM / usefulWidM));
      for (let c = 0; c < trayCols; c++) {
        const xCenter = -((trayCols - 1) * usefulWidM) / 2 + c * usefulWidM;
        const trayMesh = new THREE.Mesh(
          new THREE.BoxGeometry(usefulWidM - 0.006, 0.003, visRafterLenM),
          covMat
        );
        // Pliegues verticales de doble junta alzada H=25 mm
        const leftSeam = new THREE.Mesh(
          new THREE.BoxGeometry(0.008, seamHeightM, visRafterLenM),
          covMat
        );
        leftSeam.position.set(-usefulWidM / 2 + 0.004, seamHeightM / 2, 0);
        trayMesh.add(leftSeam);

        const rightSeam = new THREE.Mesh(
          new THREE.BoxGeometry(0.012, seamHeightM + 0.003, visRafterLenM),
          covMat
        );
        rightSeam.position.set(usefulWidM / 2 - 0.004, seamHeightM / 2, 0);
        trayMesh.add(rightSeam);

        trayMesh.position.set(xCenter, tileBaseY + 0.002, 0);
        gCovering.add(trayMesh);

        this._registerPieceMesh(trayMesh, {
          pieceCode: `BANDEJA-VMZ-C${String(c + 1).padStart(2, '0')}`,
          layerKey: 'L6_COBERTURA',
          layerName: covering.model,
          productId: covering.id,
          roleLabel: `Bandeja Continua VMZINC Doble Junta Alzada H=${covering.geometry.seamHeightMm} mm · Bandeja #${c + 1}`,
          row: 1,
          col: c + 1,
          dimensionsMm: `Ancho entre-ejes ${covering.geometry.usefulWidthMm} mm × L=${Math.round(visRafterLenM * 1000)} mm · e=${covering.geometry.thicknessMm} mm`,
          weightKg: Number((visRafterLenM * (covering.geometry.usefulWidthMm / 1000) * covering.geometry.surfaceWeightKgM2).toFixed(2)),
        });

        // Patas fijas y correderas cada 330 mm a lo largo de la junta
        for (let r = 0; r <= visBattenRows; r += 2) {
          const zClip = visRafterLenM / 2 - 0.10 - r * supportStepM;
          if (zClip < -visRafterLenM / 2) break;
          const clipMesh = new THREE.Mesh(new THREE.BoxGeometry(0.026, seamHeightM, 0.065), inoxMat);
          clipMesh.position.set(xCenter + usefulWidM / 2, tileBaseY + seamHeightM / 2, zClip);
          gFasteners.add(clipMesh);
          this._registerPieceMesh(clipMesh, {
            pieceCode: `PATA-VMZ-C${c + 1}R${r + 1}`,
            layerKey: 'L7_FIJACIONES',
            layerName: fastener.model,
            productId: fastener.id,
            roleLabel: r === 2 ? 'Pata Fija Inox AISI 304 (Zona punto fijo)' : 'Pata Corredera Inox AISI 304 (Dilatación ±25 mm)',
            row: r + 1,
            col: c + 1,
            dimensionsMm: `75 × 28 × H=${covering.geometry.seamHeightMm} mm`,
            weightKg: fastener.geometry.unitWeightKg,
          });
        }
      }
    } else if (covering.subType === 'panel_sandwich_metalico') {
      // =======================================================================
      // PANEL SÁNDWICH METÁLICO DE 3 GRECAS (KINGSPAN KS1000 RW QUADCORE)
      // =======================================================================
      const coreThickM = (covering.geometry.thicknessMm || 80) / 1000;
      const ribHeightM = (covering.geometry.ribHeightMm || 35) / 1000;
      const swCols = Math.max(2, Math.floor(visWidthM / 1.0));
      const pirMat = this._makeMaterial({ color: 0xfef08a, textureKey: 'xps_foam', roughness: 0.6 });

      for (let c = 0; c < swCols; c++) {
        const xCenter = -((swCols - 1) * 1.0) / 2 + c * 1.0;
        const panelMesh = new THREE.Mesh(
          new THREE.BoxGeometry(0.996, coreThickM, visRafterLenM),
          pirMat
        );
        const topSteel = new THREE.Mesh(
          new THREE.BoxGeometry(1.0, 0.004, visRafterLenM),
          covMat
        );
        topSteel.position.y = coreThickM / 2 + 0.002;
        panelMesh.add(topSteel);

        // 3 Grecas trapezoidales de +35 mm
        [-0.48, 0.0, 0.48].forEach((rx) => {
          const ribMesh = new THREE.Mesh(
            new THREE.BoxGeometry(0.042, ribHeightM, visRafterLenM),
            covMat
          );
          ribMesh.position.set(rx, coreThickM / 2 + ribHeightM / 2, 0);
          panelMesh.add(ribMesh);
        });

        panelMesh.position.set(xCenter, tileBaseY + coreThickM / 2, 0);
        gCovering.add(panelMesh);

        this._registerPieceMesh(panelMesh, {
          pieceCode: `KS1000RW-C${String(c + 1).padStart(2, '0')}`,
          layerKey: 'L6_COBERTURA',
          layerName: covering.model,
          productId: covering.id,
          roleLabel: `Panel Sándwich 3 Grecas Kingspan KS1000 RW · Módulo #${c + 1}`,
          row: 1,
          col: c + 1,
          dimensionsMm: `Ancho útil 1000 mm · Espesor valle ${covering.geometry.thicknessMm} mm (Cresta ${covering.geometry.thicknessMm + 35} mm)`,
          weightKg: covering.geometry.unitWeightKg,
        });
      }
    } else {
      // =======================================================================
      // PLACA ONDULADA FIBROCEMENTO SIN AMIANTO (EURONIT GRANONDA NT)
      // =======================================================================
      for (let r = 0; r < visRows; r++) {
        const zCenter = visRafterLenM / 2 - lenNomM / 2 - r * stepM;
        for (let c = 0; c < visCols; c++) {
          const xCenter = -((visCols - 1) * usefulWidM) / 2 + c * usefulWidM;
          const sheetContainer = new THREE.Mesh(
            new THREE.BoxGeometry(usefulWidM, 0.012, lenNomM),
            covMat
          );
          const numWaves = 6;
          const wavePitch = usefulWidM / numWaves;
          for (let w = 0; w < numWaves; w++) {
            const waveGeo = new THREE.CylinderGeometry(0.025, 0.025, lenNomM, 10, 1, true, 0, Math.PI);
            waveGeo.rotateY(Math.PI / 2);
            waveGeo.rotateX(Math.PI / 2);
            const waveMesh = new THREE.Mesh(waveGeo, covMat);
            waveMesh.position.set(-usefulWidM / 2 + (w + 0.5) * wavePitch, 0.008, 0);
            sheetContainer.add(waveMesh);
          }
          sheetContainer.position.set(xCenter, tileBaseY + 0.018 + r * 0.01, zCenter);
          gCovering.add(sheetContainer);

          this._registerPieceMesh(sheetContainer, {
            pieceCode: `GRANONDA-F${r + 1}-C${c + 1}`,
            layerKey: 'L6_COBERTURA',
            layerName: covering.model,
            productId: covering.id,
            roleLabel: `Placa Ondulada Fibrocemento NT (Onda 177/51) · Hilada ${r + 1}, Columna ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm} × 6,5 mm`,
            weightKg: covering.geometry.unitWeightKg,
          });
        }
      }
    }

    // Caballetes de cumbrera ventilada en el extremo superior del faldón (-Z)
    const ridgeCount = Math.ceil(visWidthM / 0.38);
    const ridgeGeo = new THREE.CylinderGeometry(0.11, 0.11, 0.42, 16, 1, true, 0, Math.PI);
    ridgeGeo.rotateZ(Math.PI / 2);
    for (let k = 0; k < ridgeCount; k++) {
      const rx = -visWidthM / 2 + (k + 0.5) * (visWidthM / ridgeCount);
      const ridgeMesh = new THREE.Mesh(ridgeGeo, covMat);
      ridgeMesh.position.set(rx, tileBaseY + 0.11, -visRafterLenM / 2 + 0.06);
      gFasteners.add(ridgeMesh);
      this._registerPieceMesh(ridgeMesh, {
        pieceCode: `CUMBRERA-C${String(k + 1).padStart(2, '0')}`,
        layerKey: 'L7_FIJACIONES',
        layerName: `Caballete de Cumbrera Ventilada (${covering.brand})`,
        productId: covering.id,
        roleLabel: 'Pieza especial de remate de cumbrera ventilada en seco',
        row: 1,
        col: k + 1,
        dimensionsMm: `420 × 220 mm (Paso útil 380 mm)`,
        weightKg: 3.4,
      });
    }
  }

  // ===========================================================================
  // CONSTRUCCIÓN 3D DEMO B: AZOTEA INVERTIDA / CONVENCIONAL / AJARDINADA
  // ===========================================================================
  _buildFlatRoof3D(rep) {
    const visLenM = Math.min(rep.geometry.lengthM, 3.6);
    const visWidM = Math.min(rep.geometry.widthM, 3.0);
    const roofSubType = rep.roofSubType;
    const {
      waterproofing,
      separatorBot,
      insulation,
      separatorTop,
      drainageLayer,
      plots,
      pavement,
      greenRoof,
      drainUnit,
    } = rep.products;

    // -------------------------------------------------------------------------
    // CAPA 1: FORJADO ESTRUCTURAL + FORMACIÓN DE PENDIENTES + PETOS PERIMETRALES
    // -------------------------------------------------------------------------
    const gSlab = this._createLayerGroup(
      'L1_SOPORTE_AZOTEA',
      `1. Forjado + Formación de Pendientes (${rep.geometry.slopePct}%) + Peto Perimetral`,
      1,
      null,
      0.0
    );
    const concMat = this._makeMaterial({
      color: 0x8d959e,
      textureKey: 'concrete',
      roughness: 0.82,
      repeat: [3, 3],
    });
    const slopeMat = this._makeMaterial({
      color: 0xa29c94,
      textureKey: 'cellular_concrete',
      roughness: 0.86,
      repeat: [3, 3],
    });

    const slabMesh = new THREE.Mesh(new THREE.BoxGeometry(visLenM, 0.22, visWidM), concMat);
    slabMesh.position.set(0, -0.11, 0);
    gSlab.add(slabMesh);

    const slopeMesh = new THREE.Mesh(new THREE.BoxGeometry(visLenM, 0.06, visWidM), slopeMat);
    slopeMesh.position.set(0, 0.03, 0);
    gSlab.add(slopeMesh);

    // Peto perimetral en L (trasero y lateral izquierdo) para ver claramente la sección en primer plano
    const parapetH = 0.55;
    const parapetBack = new THREE.Mesh(
      new THREE.BoxGeometry(visLenM + 0.16, parapetH, 0.16),
      concMat
    );
    parapetBack.position.set(0, parapetH / 2, -visWidM / 2 - 0.08);
    gSlab.add(parapetBack);

    const parapetLeft = new THREE.Mesh(
      new THREE.BoxGeometry(0.16, parapetH, visWidM + 0.16),
      concMat
    );
    parapetLeft.position.set(-visLenM / 2 - 0.08, parapetH / 2, 0);
    gSlab.add(parapetLeft);

    this._registerPieceMesh(slabMesh, {
      pieceCode: 'FORJADO-HA25-01',
      layerKey: 'L1_SOPORTE_AZOTEA',
      layerName: `Forjado HA-25 + Hormigón Celular de Pendientes (${rep.geometry.slopePct}%)`,
      productId: waterproofing.id,
      roleLabel: 'Soporte estructural resistente y formación de pendientes hacia sumidero',
      row: 1,
      col: 1,
      dimensionsMm: `${Math.round(rep.geometry.lengthM * 1000)} × ${Math.round(rep.geometry.widthM * 1000)} × 280 mm`,
      weightKg: Number((rep.geometry.flatAreaM2 * 380).toFixed(0)),
    });

    let currentY = 0.06;

    // -------------------------------------------------------------------------
    // CAPA 2: CAZOLETA SIFÓNICA JIMTEN S-77 Ø110 mm (A ≥ 50 cm de petos)
    // -------------------------------------------------------------------------
    const gDrain = this._createLayerGroup(
      'L2_CAZOLETA',
      `2. Punto Singular de Evacuación: ${drainUnit.brand} ${drainUnit.model}`,
      2,
      drainUnit,
      0.16
    );
    const epdmFlangeMat = this._makeMaterial({
      color: 0x1e2229,
      textureKey: 'bitumen',
      roughness: 0.7,
    });
    const grateMat = this._makeMaterial({
      color: 0xb0bac5,
      textureKey: 'brushed_metal',
      roughness: 0.3,
      metalness: 0.82,
    });

    const drainX = -visLenM / 2 + 0.62; // A > 50 cm reglamentarios del peto
    const drainZ = -visWidM / 2 + 0.62;

    const drainAssembly = new THREE.Mesh(
      new THREE.BoxGeometry(0.42, 0.012, 0.42),
      epdmFlangeMat
    );
    drainAssembly.position.set(drainX, currentY + 0.008, drainZ);

    const outletRadius = (drainUnit.geometry.outletDiameterMm || 110) / 2000;
    const pipeMesh = new THREE.Mesh(
      new THREE.CylinderGeometry(outletRadius, outletRadius, 0.38, 20),
      epdmFlangeMat
    );
    pipeMesh.position.set(0, -0.18, 0);
    drainAssembly.add(pipeMesh);

    const grateMesh = new THREE.Mesh(
      new THREE.BoxGeometry(0.24, 0.018, 0.24),
      grateMat
    );
    grateMesh.position.set(0, 0.016, 0);
    drainAssembly.add(grateMesh);

    gDrain.add(drainAssembly);
    this._registerPieceMesh(drainAssembly, {
      pieceCode: `CAZOLETA-JIMTEN-Ø${drainUnit.geometry.outletDiameterMm}`,
      layerKey: 'L2_CAZOLETA',
      layerName: drainUnit.model,
      productId: drainUnit.id,
      roleLabel: `Cazoleta sifónica registrable con ala de ${drainUnit.geometry.flangeWidthMm} mm (Capacidad ${drainUnit.geometry.hydraulicCapacityLs} L/s)`,
      row: 1,
      col: 1,
      dimensionsMm: `Rejilla 240×240 mm · Salida Ø${drainUnit.geometry.outletDiameterMm} mm · Distancia a peto 620 mm (≥500 mm CTE)`,
      weightKg: drainUnit.geometry.unitWeightKg,
    });

    // Helper para construir las bandas de impermeabilización con solapes y remonte en peto
    const buildWaterproofingLayer = (orderIndex, baseY, explodeStep) => {
      const gWp = this._createLayerGroup(
        'L3_IMPERMEABILIZACION',
        `${orderIndex}. Impermeabilización ${waterproofing.brand} (${waterproofing.model})`,
        orderIndex,
        waterproofing,
        explodeStep
      );
      const wpMat = this._makeMaterial({
        color: waterproofing.colorHex || '#23262b',
        textureKey: waterproofing.textureKey || 'bitumen',
        roughness: 0.62,
        repeat: [3, 1],
      });
      const seamMat = new THREE.MeshStandardMaterial({
        color: waterproofing.isPvcPlasticized ? 0x94a3b8 : 0x111317,
        roughness: 0.4,
      });

      const stripWidM = Math.min(1.0, (waterproofing.geometry.usefulWidthMm || 920) / 1000);
      const numStrips = Math.ceil(visWidM / stripWidM);
      const actualStripW = visWidM / numStrips;
      const overlapM = (waterproofing.geometry.overlapLongMinMm || 80) / 1000;

      for (let s = 0; s < numStrips; s++) {
        const zStrip = -visWidM / 2 + (s + 0.5) * actualStripW;
        const stripMesh = new THREE.Mesh(
          new THREE.BoxGeometry(visLenM, 0.008, actualStripW + overlapM * 0.5),
          wpMat
        );
        // Cordón de solape termosoldado de 80 mm
        const seamCord = new THREE.Mesh(
          new THREE.BoxGeometry(visLenM + 0.004, 0.003, overlapM),
          seamMat
        );
        seamCord.position.set(0, 0.005, actualStripW / 2);
        stripMesh.add(seamCord);

        stripMesh.position.set(0, baseY + 0.004 + s * 0.0008, zStrip);
        gWp.add(stripMesh);

        this._registerPieceMesh(stripMesh, {
          pieceCode: `MEMBRANA-BANDA-0${s + 1}`,
          layerKey: 'L3_IMPERMEABILIZACION',
          layerName: waterproofing.model,
          productId: waterproofing.id,
          roleLabel: `Banda impermeable #${s + 1} con solape longitudinal soldado de ${waterproofing.geometry.overlapLongMinMm} mm`,
          row: s + 1,
          col: 1,
          dimensionsMm: `Ancho nominal ${waterproofing.geometry.widthNominalMm} mm (Útil ${waterproofing.geometry.usefulWidthMm} mm) · e=${waterproofing.geometry.thicknessMm} mm`,
          weightKg: Number((visLenM * actualStripW * waterproofing.geometry.surfaceWeightKgM2).toFixed(1)),
        });
      }

      // Remonte vertical en peto (parapetTurnupMm)
      const turnupH = (rep.geometry.parapetTurnupMm || 200) / 1000;
      const turnupBack = new THREE.Mesh(
        new THREE.BoxGeometry(visLenM, turnupH, 0.012),
        wpMat
      );
      turnupBack.position.set(0, baseY + turnupH / 2, -visWidM / 2 + 0.006);
      gWp.add(turnupBack);

      const turnupLeft = new THREE.Mesh(
        new THREE.BoxGeometry(0.012, turnupH, visWidM),
        wpMat
      );
      turnupLeft.position.set(-visLenM / 2 + 0.006, baseY + turnupH / 2, 0);
      gWp.add(turnupLeft);

      this._registerPieceMesh(turnupBack, {
        pieceCode: `REMONTE-PETO-${rep.geometry.parapetTurnupMm}MM`,
        layerKey: 'L3_IMPERMEABILIZACION',
        layerName: `Entrega Vertical en Peto (${waterproofing.brand})`,
        productId: waterproofing.id,
        roleLabel: `Remonte perimetral impermeabilizante h=${rep.geometry.parapetTurnupMm} mm (CTE DB-HS 1 ≥ 200 mm)`,
        row: 1,
        col: 1,
        dimensionsMm: `Altura entrega vertical: ${rep.geometry.parapetTurnupMm} mm + Roza y perfil metálico`,
        weightKg: Number((rep.geometry.turnupAreaM2 * waterproofing.geometry.surfaceWeightKgM2).toFixed(1)),
      });

      return baseY + 0.012;
    };

    // Helper para construir las planchas individuales de aislamiento térmico a matajunta
    const buildInsulationLayer = (orderIndex, baseY, explodeStep) => {
      const insThickM = (insulation.geometry.thicknessMm || 60) / 1000;
      const gIns = this._createLayerGroup(
        'L5_AISLAMIENTO',
        `${orderIndex}. Aislamiento Térmico Pieza a Pieza: ${insulation.brand} (${insulation.geometry.thicknessMm} mm)`,
        orderIndex,
        insulation,
        explodeStep
      );
      const insMat = this._makeMaterial({
        color: insulation.colorHex || '#f1df80',
        textureKey: insulation.textureKey || 'xps_foam',
        roughness: 0.55,
      });

      const bLenM = (insulation.geometry.usefulLengthNominalMm || 1235) / 1000;
      const bWidM = (insulation.geometry.usefulWidthMm || 585) / 1000;
      const cols = Math.ceil(visLenM / bLenM);
      const rows = Math.ceil(visWidM / bWidM);
      const cellLen = visLenM / cols;
      const cellWid = visWidM / rows;

      for (let r = 0; r < rows; r++) {
        const zBoard = -visWidM / 2 + (r + 0.5) * cellWid;
        for (let c = 0; c < cols; c++) {
          const xBoard = -visLenM / 2 + (c + 0.5) * cellLen;
          // Plancha individual con junta a media madera
          const boardMesh = new THREE.Mesh(
            new THREE.BoxGeometry(cellLen - 0.005, insThickM, cellWid - 0.005),
            insMat
          );
          boardMesh.position.set(xBoard, baseY + insThickM / 2, zBoard);
          gIns.add(boardMesh);

          this._registerPieceMesh(boardMesh, {
            pieceCode: `PLANCHA-${insulation.manufacturerId}-F${String(r + 1).padStart(2, '0')}-C${String(c + 1).padStart(2, '0')}`,
            layerKey: 'L5_AISLAMIENTO',
            layerName: insulation.model,
            productId: insulation.id,
            roleLabel: `Plancha aislante individual a media madera · Fila ${r + 1}, Columna ${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `${insulation.geometry.lengthNominalMm} × ${insulation.geometry.widthNominalMm} × ${insulation.geometry.thicknessMm} mm (Rd = ${rep.summary.thermalResistanceRd} m²K/W)`,
            weightKg: insulation.geometry.unitWeightKg,
          });
        }
      }
      return baseY + insThickM;
    };

    // Helper para geotextil separador
    const buildGeotextileLayer = (key, title, orderIndex, prod, baseY, explodeStep) => {
      const gGeo = this._createLayerGroup(key, title, orderIndex, prod, explodeStep);
      const geoMat = this._makeMaterial({
        color: prod.colorHex || '#e2eff8',
        textureKey: 'geotextile',
        roughness: 0.85,
        repeat: [4, 4],
      });
      const numGStrips = 2;
      const gStripW = visWidM / numGStrips;
      for (let i = 0; i < numGStrips; i++) {
        const zG = -visWidM / 2 + (i + 0.5) * gStripW;
        const gMesh = new THREE.Mesh(
          new THREE.BoxGeometry(visLenM - 0.01, 0.005, gStripW + 0.08),
          geoMat
        );
        gMesh.position.set(0, baseY + 0.003 + i * 0.001, zG);
        gGeo.add(gMesh);
        this._registerPieceMesh(gMesh, {
          pieceCode: `DANOFELT-PY-0${i + 1}`,
          layerKey: key,
          layerName: prod.model,
          productId: prod.id,
          roleLabel: 'Geotextil no tejido separador y antipunzonamiento (Solape 150 mm)',
          row: i + 1,
          col: 1,
          dimensionsMm: `Gramaje ${prod.geometry.surfaceWeightKgM2 * 1000} g/m² · e=${prod.geometry.thicknessMm} mm · Solape 150 mm`,
          weightKg: Number((visLenM * gStripW * prod.geometry.surfaceWeightKgM2).toFixed(2)),
        });
      }
      return baseY + 0.007;
    };

    if (roofSubType === 'convencional_fija') {
      // Azotea Convencional: Aislamiento debajo -> Impermeabilización -> Geotextil -> Pavimento recibido
      currentY = buildInsulationLayer(3, currentY, 0.25);
      currentY = buildWaterproofingLayer(4, currentY, 0.40);
      currentY = buildGeotextileLayer(
        'L4_GEOTEXTIL',
        `5. Capa Separadora ${separatorTop.brand} (${separatorTop.model})`,
        5,
        separatorTop,
        currentY,
        0.52
      );
    } else {
      // Azotea Invertida o Ajardinada: Impermeabilización -> Geotextil -> Aislamiento XPS
      currentY = buildWaterproofingLayer(3, currentY, 0.24);
      currentY = buildGeotextileLayer(
        'L4_GEOTEXTIL',
        `4. Geotextil Separador ${separatorBot.brand} (${separatorBot.model})`,
        4,
        separatorBot,
        currentY,
        0.36
      );
      currentY = buildInsulationLayer(5, currentY, 0.48);
    }

    if (roofSubType === 'ajardinada') {
      // -----------------------------------------------------------------------
      // CAPA 6 Y 7 (AJARDINADA): SISTEMA OPTIGRÜN FKD 25 + SUSTRATO + SEDUM
      // -----------------------------------------------------------------------
      const gGreen = this._createLayerGroup(
        'L6_AJARDINADA',
        `6. Sistema Ecológico ${greenRoof.brand} (${greenRoof.model})`,
        6,
        greenRoof,
        0.66
      );
      const fkdMat = this._makeMaterial({ color: 0x1e293b, textureKey: 'bitumen', roughness: 0.65 });
      const subMat = this._makeMaterial({ color: 0x5c4433, textureKey: 'mortar', roughness: 0.92 });
      const sedumMat = this._makeMaterial({ color: 0x458b4e, textureKey: 'geotextile', roughness: 0.85 });
      const gravelMat = this._makeMaterial({ color: 0xd1d5db, textureKey: 'gravel', roughness: 0.8 });

      // Placa drenante FKD 25
      const fkdMesh = new THREE.Mesh(new THREE.BoxGeometry(visLenM - 0.02, 0.025, visWidM - 0.02), fkdMat);
      fkdMesh.position.set(0, currentY + 0.0125, 0);
      gGreen.add(fkdMesh);

      // Franja perimetral de grava estéril (35 cm junto a petos)
      const gravelStrip = new THREE.Mesh(
        new THREE.BoxGeometry(visLenM - 0.02, 0.08, 0.35),
        gravelMat
      );
      gravelStrip.position.set(0, currentY + 0.065, -visWidM / 2 + 0.185);
      gGreen.add(gravelStrip);

      // Sustrato mineral + Tapiz vegetal Sedum dividido en módulos inspeccionables
      const subThickM = ((greenRoof.geometry.thicknessMm || 108) - 25) / 1000;
      const gCols = 3;
      const gRows = 2;
      const modL = (visLenM - 0.36) / gCols;
      const modW = (visWidM - 0.36) / gRows;

      for (let r = 0; r < gRows; r++) {
        for (let c = 0; c < gCols; c++) {
          const mx = -visLenM / 2 + 0.35 + (c + 0.5) * modL;
          const mz = -visWidM / 2 + 0.35 + (r + 0.5) * modW;
          const packMesh = new THREE.Mesh(
            new THREE.BoxGeometry(modL - 0.008, subThickM, modW - 0.008),
            subMat
          );
          const sedumTop = new THREE.Mesh(
            new THREE.BoxGeometry(modL - 0.008, 0.022, modW - 0.008),
            sedumMat
          );
          sedumTop.position.y = subThickM / 2 + 0.011;
          packMesh.add(sedumTop);

          packMesh.position.set(mx, currentY + 0.025 + subThickM / 2, mz);
          gGreen.add(packMesh);

          this._registerPieceMesh(packMesh, {
            pieceCode: `OPTIGRUN-MOD-F${r + 1}C${c + 1}`,
            layerKey: 'L6_AJARDINADA',
            layerName: greenRoof.model,
            productId: greenRoof.id,
            roleLabel: `Módulo FKD 25 + Sustrato Mineral + Tapiz Sedum · Sector ${r + 1}-${c + 1}`,
            row: r + 1,
            col: c + 1,
            dimensionsMm: `Espesor total ${greenRoof.geometry.thicknessMm} mm · Retención 40 L/m² · Peso sat. ${greenRoof.geometry.surfaceWeightKgM2} kg/m²`,
            weightKg: Number((modL * modW * greenRoof.geometry.surfaceWeightKgM2).toFixed(1)),
          });
        }
      }
      return;
    }

    // -------------------------------------------------------------------------
    // CAPA 6: PLOTS REGULABLES AUTONIVELANTES PEYGRAN XSP5 PRO (PIEZA A PIEZA)
    // -------------------------------------------------------------------------
    const tileLenM = (rep.replanteoParams.tileLenMm || 600) / 1000;
    const tileWidM = (rep.replanteoParams.tileWidMm || 600) / 1000;
    const jointM = (rep.replanteoParams.jointMm || 4) / 1000;

    const visTilesX = Math.max(2, Math.floor(visLenM / tileLenM));
    const visTilesZ = Math.max(2, Math.floor(visWidM / tileWidM));
    const gridTotalX = visTilesX * tileLenM;
    const gridTotalZ = visTilesZ * tileWidM;
    const startGridX = -gridTotalX / 2;
    const startGridZ = -gridTotalZ / 2;

    let paverBaseY = currentY + 0.015;

    if (roofSubType === 'invertida_plots') {
      const plotHeightM = (plots.geometry.thicknessMm || 95) / 1000;
      const baseRadiusM = (plots.geometry.baseDiameterMm || 220) / 2000;
      const headRadiusM = (plots.geometry.headDiameterMm || 155) / 2000;

      const gPlots = this._createLayerGroup(
        'L6_PLOTS',
        `6. Plots Regulables Pieza a Pieza: ${plots.brand} (H=${plots.geometry.thicknessMm} mm)`,
        6,
        plots,
        0.62
      );
      const plotMat = this._makeMaterial({
        color: 0x22272e,
        textureKey: 'brushed_metal',
        roughness: 0.48,
        metalness: 0.2,
      });
      const rubberRingMat = new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.5 });

      for (let rz = 0; rz <= visTilesZ; rz++) {
        const pz = startGridZ + rz * tileWidM;
        for (let cx = 0; cx <= visTilesX; cx++) {
          const px = startGridX + cx * tileLenM;

          // Geometría 3D real del plot Peygran: Base Ø220 mm + Rosca + Cabezal Ø155 mm + Cruceta 4 mm
          const plotRoot = new THREE.Mesh(
            new THREE.CylinderGeometry(baseRadiusM, baseRadiusM, 0.008, 18),
            plotMat
          );
          plotRoot.position.set(px, currentY + 0.004, pz);

          const colHeight = Math.max(0.025, plotHeightM - 0.014);
          const colMesh = new THREE.Mesh(
            new THREE.CylinderGeometry(0.048, 0.055, colHeight, 16),
            plotMat
          );
          colMesh.position.y = colHeight / 2 + 0.004;
          plotRoot.add(colMesh);

          const headMesh = new THREE.Mesh(
            new THREE.CylinderGeometry(headRadiusM, headRadiusM, 0.01, 18),
            rubberRingMat
          );
          headMesh.position.y = plotHeightM - 0.005;
          plotRoot.add(headMesh);

          // Crucetas separadoras de 4 mm en la cabeza del plot
          const tab1 = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.014, jointM), plotMat);
          tab1.position.y = plotHeightM + 0.005;
          plotRoot.add(tab1);

          const tab2 = new THREE.Mesh(new THREE.BoxGeometry(jointM, 0.014, 0.09), plotMat);
          tab2.position.y = plotHeightM + 0.005;
          plotRoot.add(tab2);

          gPlots.add(plotRoot);

          const isPerimeter = rz === 0 || rz === visTilesZ || cx === 0 || cx === visTilesX;
          this._registerPieceMesh(plotRoot, {
            pieceCode: `PLOT-X${String(cx + 1).padStart(2, '0')}-Y${String(rz + 1).padStart(2, '0')}`,
            layerKey: 'L6_PLOTS',
            layerName: plots.model,
            productId: plots.id,
            roleLabel: isPerimeter
              ? `Plot Regulable Perimetral (Borde) · Nudo (${cx + 1}, ${rz + 1})`
              : `Plot Regulable Central (4 vértices) · Nudo (${cx + 1}, ${rz + 1})`,
            row: rz + 1,
            col: cx + 1,
            dimensionsMm: `Base Ø${plots.geometry.baseDiameterMm} mm · Altura H=${plots.geometry.thicknessMm} mm (Rango ${plots.geometry.minHeightMm}–${plots.geometry.maxHeightMm} mm) · Cruceta ${rep.replanteoParams.jointMm} mm`,
            weightKg: plots.geometry.unitWeightKg,
          });
        }
      }
      paverBaseY = currentY + plotHeightM;
    }

    // -------------------------------------------------------------------------
    // CAPA 7: BALDOSAS PORCELÁNICAS GRES ARAGÓN ORDESA 20MM (PIEZA A PIEZA)
    // -------------------------------------------------------------------------
    const paverThickM = (pavement.geometry.thicknessMm || 20) / 1000;
    const gPavers = this._createLayerGroup(
      'L7_PAVIMENTO',
      `7. Pavimento Porcelánico Pieza a Pieza: ${pavement.brand} (${rep.replanteoParams.tileLenMm}×${rep.replanteoParams.tileWidMm}×${pavement.geometry.thicknessMm} mm)`,
      7,
      pavement,
      0.80
    );
    const tileMat = this._makeMaterial({
      color: pavement.colorHex || '#c87358',
      textureKey: pavement.textureKey || 'terracotta',
      roughness: 0.46,
    });
    const drainTileMat = tileMat.clone();
    drainTileMat.color.offsetHSL(0, 0, -0.06);

    for (let rz = 0; rz < visTilesZ; rz++) {
      const tz = startGridZ + (rz + 0.5) * tileWidM;
      for (let cx = 0; cx < visTilesX; cx++) {
        const tx = startGridX + (cx + 0.5) * tileLenM;
        const isDrainRegister = rz === 0 && cx === 0;

        const tileMesh = new THREE.Mesh(
          new THREE.BoxGeometry(
            tileLenM - jointM * 1.4,
            paverThickM,
            tileWidM - jointM * 1.4
          ),
          isDrainRegister ? drainTileMat : tileMat
        );

        // Si es la baldosa registrable sobre la cazoleta sifónica Jimten, añadimos rejilla ranurada
        if (isDrainRegister) {
          const slotGrate = new THREE.Mesh(
            new THREE.BoxGeometry(0.18, paverThickM + 0.003, 0.18),
            grateMat
          );
          tileMesh.add(slotGrate);
        }

        tileMesh.position.set(tx, paverBaseY + paverThickM / 2, tz);
        gPavers.add(tileMesh);

        this._registerPieceMesh(tileMesh, {
          pieceCode: `BALDOSA-F${String(rz + 1).padStart(2, '0')}-C${String(cx + 1).padStart(2, '0')}`,
          layerKey: 'L7_PAVIMENTO',
          layerName: isDrainRegister
            ? `${pavement.model} (Baldosa Registrable sobre Cazoleta S-77)`
            : pavement.model,
          productId: pavement.id,
          roleLabel: isDrainRegister
            ? `Baldosa Porcelánica Registrable sobre Sumidero · Fila ${rz + 1}, Col ${cx + 1}`
            : `Baldosa Porcelánica 20mm sobre 4 Plots (Junta abierta ${rep.replanteoParams.jointMm} mm) · Fila ${rz + 1}, Col ${cx + 1}`,
          row: rz + 1,
          col: cx + 1,
          dimensionsMm: `${rep.replanteoParams.tileLenMm} × ${rep.replanteoParams.tileWidMm} × ${pavement.geometry.thicknessMm} mm (Junta perimetral ${rep.replanteoParams.jointMm} mm)`,
          weightKg: pavement.geometry.unitWeightKg,
        });
      }
    }
  }

  // ===========================================================================
  // CONTROL INTERACTIVO DE CAPAS, EXPLOSIONADO, MONTAJE Y SELECCIÓN RAYCAST
  // ===========================================================================
  getLayerDescriptors() {
    return this.layerGroups.map((g) => {
      const key = g.userData.layerKey;
      const st = this.layerStates[key] || { visible: true, transparent: false };
      return {
        key,
        title: g.userData.title,
        orderIndex: g.userData.orderIndex,
        productId: g.userData.productId,
        productName: g.userData.productName,
        visible: st.visible,
        transparent: st.transparent,
      };
    });
  }

  setLayerVisibility(layerKey, visible) {
    if (!this.layerStates[layerKey]) {
      this.layerStates[layerKey] = { visible: true, transparent: false };
    }
    this.layerStates[layerKey].visible = Boolean(visible);
    this._applyLayerStates();
  }

  setLayerTransparency(layerKey, transparent) {
    if (!this.layerStates[layerKey]) {
      this.layerStates[layerKey] = { visible: true, transparent: false };
    }
    this.layerStates[layerKey].transparent = Boolean(transparent);
    this._applyLayerStates();
  }

  isolateLayer(layerKey) {
    const allHiddenExceptThis = this.layerGroups.every((g) => {
      const k = g.userData.layerKey;
      return k === layerKey ? this.layerStates[k]?.visible : !this.layerStates[k]?.visible;
    });

    this.layerGroups.forEach((g) => {
      const k = g.userData.layerKey;
      this.layerStates[k].visible = allHiddenExceptThis ? true : k === layerKey;
    });
    this._applyLayerStates();
  }

  _applyLayerStates() {
    this.layerGroups.forEach((g) => {
      const st = this.layerStates[g.userData.layerKey] || { visible: true, transparent: false };
      g.visible = st.visible;
      g.traverse((obj) => {
        if (obj.isMesh && obj.material) {
          const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
          mats.forEach((m) => {
            m.transparent = st.transparent;
            m.opacity = st.transparent ? 0.28 : 1.0;
            m.needsUpdate = true;
          });
        }
      });
    });
  }

  setExplodeFactor(factor) {
    this.explodeFactor = Math.max(0, Math.min(1, Number(factor) || 0));
    this._applyExplodeFactor();
  }

  _applyExplodeFactor() {
    this.layerGroups.forEach((g, idx) => {
      const step = g.userData.explodeStep ?? idx * 0.2;
      g.position.y = (g.userData.baseY || 0) + this.explodeFactor * step * 1.35;
    });
    if (this.selectedPieceMeta && this.selectedPieceMeta._meshRef) {
      this._updateHighlightBox(this.selectedPieceMeta._meshRef);
    }
  }

  setAssemblyProgress(progress0to1) {
    this.assemblyProgress = Math.max(0.02, Math.min(1.0, Number(progress0to1) || 1.0));
    this._applyAssemblyProgress();
  }

  togglePlayAssembly(onProgressChange) {
    this.onProgressChange = onProgressChange;
    if (this.isPlayingAssembly) {
      this.isPlayingAssembly = false;
    } else {
      if (this.assemblyProgress >= 0.99) this.assemblyProgress = 0.04;
      this.isPlayingAssembly = true;
    }
    return this.isPlayingAssembly;
  }

  _applyAssemblyProgress() {
    const total = this.orderedPieceEntries.length;
    if (total === 0) return;
    const cutoff = Math.ceil(this.assemblyProgress * total);

    for (let i = 0; i < total; i++) {
      const entry = this.orderedPieceEntries[i];
      const mesh = entry.mesh;
      const layerVis = this.layerStates[entry.meta.layerKey]?.visible !== false;
      const shouldShow = i < cutoff && layerVis;
      mesh.visible = shouldShow;
    }
  }

  setCameraPreset(preset) {
    if (!this.camera || !this.controls) return;
    this.controls.target.set(0, 0.35, 0);
    if (preset === 'top') {
      this.camera.position.set(0.01, 7.2, 0.01);
    } else if (preset === 'front') {
      this.camera.position.set(0, 1.4, 6.4);
    } else if (preset === 'side') {
      this.camera.position.set(6.4, 1.4, 0);
    } else if (preset === 'detail') {
      this.camera.position.set(2.3, 1.8, 2.5);
    } else {
      this.camera.position.set(5.4, 4.2, 5.8);
    }
    this.controls.update();
  }

  _pickPieceAtEvent(e) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.pointer, this.camera);
    const visiblePieces = this.interactivePieces.filter((m) => m.visible && m.parent?.visible !== false);
    const hits = this.raycaster.intersectObjects(visiblePieces, true);

    if (hits.length > 0) {
      let target = hits[0].object;
      while (target && !target.userData?.isBIMPiece && target.parent) {
        target = target.parent;
      }
      if (target && target.userData?.isBIMPiece) {
        this._updateHighlightBox(target);
        this.selectedPieceMeta = { ...target.userData, _meshRef: target };
        this.onPieceSelected(this.selectedPieceMeta);
        return;
      }
    }
    this.highlightMesh.visible = false;
    this.selectedPieceMeta = null;
    this.onPieceSelected(null);
  }

  _updateHighlightBox(mesh) {
    const box = new THREE.Box3().setFromObject(mesh);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    this.highlightMesh.scale.set(size.x + 0.015, size.y + 0.015, size.z + 0.015);
    this.highlightMesh.position.copy(center);
    this.highlightMesh.visible = true;
  }
}

/**
 * =============================================================================
 * RENDERIZADOR DEL PLANO CAD 2D DE REPLANTEO PARAMÉTRICO (SECCIÓN 12)
 * =============================================================================
 * Dibuja a escala el faldón o azotea con todas las líneas de rastrel, retícula
 * de piezas individuales, zonas de corte perimetral, cotas de paso/solape y
 * resalta en cian la pieza seleccionada en el visor 3D.
 */
export class BIMReplanteo2DRenderer {
  static draw(canvas, replanteo, selectedPieceMeta = null) {
    if (!canvas || !replanteo) return;
    const ctx = canvas.getContext('2d');
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssW = canvas.clientWidth || 460;
    const cssH = canvas.clientHeight || 300;
    if (canvas.width !== cssW * dpr || canvas.height !== cssH * dpr) {
      canvas.width = cssW * dpr;
      canvas.height = cssH * dpr;
    }
    ctx.save();
    ctx.scale(dpr, dpr);

    // Fondo estilo plano CAD técnico oscuro
    ctx.fillStyle = '#090f18';
    ctx.fillRect(0, 0, cssW, cssH);

    // Cuadrícula de fondo
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.06)';
    ctx.lineWidth = 1;
    for (let x = 0; x < cssW; x += 24) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, cssH);
      ctx.stroke();
    }
    for (let y = 0; y < cssH; y += 24) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(cssW, y);
      ctx.stroke();
    }

    const padL = 56;
    const padR = 38;
    const padT = 42;
    const padB = 46;
    const availW = Math.max(120, cssW - padL - padR);
    const availH = Math.max(100, cssH - padT - padB);

    if (replanteo.systemType === 'tejado') {
      const realW = replanteo.geometry.widthM;
      const realL = replanteo.geometry.rafterLengthM;
      const scale = Math.min(availW / realW, availH / realL);
      const drawW = realW * scale;
      const drawH = realL * scale;
      const ox = padL + (availW - drawW) / 2;
      const oy = padT + (availH - drawH) / 2;

      const { numRows, numCols, battenStepMm, usefulWidthMm, realOverlapLongMm } =
        replanteo.replanteoParams;
      const { covering } = replanteo.products;

      // Contorno de faldón
      ctx.fillStyle = 'rgba(30, 41, 59, 0.7)';
      ctx.fillRect(ox, oy, drawW, drawH);

      // Retícula de piezas de cobertura (tejas / pizarras / bandejas)
      const cellW = ((usefulWidthMm / 1000) * scale);
      const cellH = ((battenStepMm / 1000) * scale);

      ctx.save();
      ctx.beginPath();
      ctx.rect(ox, oy, drawW, drawH);
      ctx.clip();

      for (let r = 0; r < numRows; r++) {
        // De alero (abajo) a cumbrera (arriba)
        const py = oy + drawH - (r + 1) * cellH;
        const stagger = covering.subType === 'pizarra_natural' ? (r % 2) * (cellW * 0.5) : 0;

        for (let c = 0; c < numCols; c++) {
          const px = ox + c * cellW + stagger;
          const isCutEdge = px + cellW > ox + drawW + 1 || py < oy - 1;
          const isSelected =
            selectedPieceMeta &&
            selectedPieceMeta.row === r + 1 &&
            selectedPieceMeta.col === c + 1;

          ctx.fillStyle = isSelected
            ? 'rgba(0, 229, 255, 0.45)'
            : isCutEdge
            ? 'rgba(245, 158, 11, 0.24)'
            : 'rgba(182, 83, 56, 0.25)';
          ctx.fillRect(px + 0.5, Math.max(oy, py) + 0.5, cellW - 1, cellH - 1);

          ctx.strokeStyle = isSelected
            ? '#00e5ff'
            : 'rgba(226, 232, 240, 0.25)';
          ctx.lineWidth = isSelected ? 2 : 0.8;
          ctx.strokeRect(px + 0.5, Math.max(oy, py) + 0.5, cellW - 1, cellH - 1);
        }

        // Línea horizontal de rastrel (en ámbar discontinuo)
        const battenY = oy + drawH - r * cellH;
        ctx.strokeStyle = 'rgba(251, 191, 36, 0.75)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(ox, battenY);
        ctx.lineTo(ox + drawW, battenY);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      ctx.restore();

      // Borde exterior de faldón
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 1.8;
      ctx.strokeRect(ox, oy, drawW, drawH);

      // Etiquetas técnicas de Cumbrera, Alero y Cotas
      ctx.fillStyle = '#94a3b8';
      ctx.font = '600 10px Inter, system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(
        `CUMBRERA VENTILADA (${replanteo.replanteoParams.ridgePiecesCount} caballetes · L = ${realW.toFixed(2)} m)`,
        ox + drawW / 2,
        oy - 10
      );
      ctx.fillStyle = '#38bdf8';
      ctx.fillText(
        `ALERO + CANALÓN VMZINC (${replanteo.replanteoParams.eavePiecesCount} uds/hilada · Paso útil = ${usefulWidthMm} mm)`,
        ox + drawW / 2,
        oy + drawH + 16
      );

      // Cota vertical izquierda (Longitud real de faldón y paso de rastrel)
      ctx.save();
      ctx.translate(ox - 20, oy + drawH / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = '#fbbf24';
      ctx.fillText(
        `L faldón = ${realL.toFixed(2)} m (${numRows} hiladas)`,
        0,
        -4
      );
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(
        `Paso ${battenStepMm} mm · Solape ${realOverlapLongMm} mm`,
        0,
        9
      );
      ctx.restore();
    } else {
      // PLANO CAD 2D DE REPLANTEO DE AZOTEA (DEMO B: BALDOSAS + PLOTS + CAZOLETA)
      const realL = replanteo.geometry.lengthM;
      const realW = replanteo.geometry.widthM;
      const scale = Math.min(availW / realL, availH / realW);
      const drawW = realL * scale;
      const drawH = realW * scale;
      const ox = padL + (availW - drawW) / 2;
      const oy = padT + (availH - drawH) / 2;

      const { numTilesX, numTilesY, tileLenMm, tileWidMm, jointMm } = replanteo.replanteoParams;
      const cellW = ((tileLenMm + jointMm) / 1000) * scale;
      const cellH = ((tileWidMm + jointMm) / 1000) * scale;

      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.fillRect(ox, oy, drawW, drawH);

      ctx.save();
      ctx.beginPath();
      ctx.rect(ox, oy, drawW, drawH);
      ctx.clip();

      for (let r = 0; r < numTilesY; r++) {
        const py = oy + r * cellH;
        for (let c = 0; c < numTilesX; c++) {
          const px = ox + c * cellW;
          const isCut = px + cellW > ox + drawW + 1 || py + cellH > oy + drawH + 1;
          const isSelected =
            selectedPieceMeta &&
            selectedPieceMeta.row === r + 1 &&
            selectedPieceMeta.col === c + 1;

          ctx.fillStyle = isSelected
            ? 'rgba(0, 229, 255, 0.45)'
            : isCut
            ? 'rgba(245, 158, 11, 0.28)'
            : 'rgba(200, 115, 88, 0.25)';
          ctx.fillRect(px + 1, py + 1, cellW - 2, cellH - 2);

          ctx.strokeStyle = isSelected ? '#00e5ff' : 'rgba(148, 163, 184, 0.32)';
          ctx.lineWidth = isSelected ? 2 : 0.8;
          ctx.strokeRect(px + 1, py + 1, cellW - 2, cellH - 2);
        }
      }

      // Dibujar los Plots Peygran en cada vértice de 4 baldosas
      if (replanteo.roofSubType === 'invertida_plots') {
        for (let r = 0; r <= numTilesY; r++) {
          const py = Math.min(oy + drawH, oy + r * cellH);
          for (let c = 0; c <= numTilesX; c++) {
            const px = Math.min(ox + drawW, ox + c * cellW);
            ctx.beginPath();
            ctx.arc(px, py, 3.2, 0, Math.PI * 2);
            ctx.fillStyle = '#10b981';
            ctx.fill();
          }
        }
      }

      // Dibujar Cazoleta Sifónica Jimten S-77 a ≥ 50 cm de petos
      const drainPx = ox + Math.min(0.62 * scale, drawW * 0.22);
      const drainPy = oy + Math.min(0.62 * scale, drawH * 0.25);
      ctx.beginPath();
      ctx.arc(drainPx, drainPy, 7, 0, Math.PI * 2);
      ctx.fillStyle = '#00e5ff';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.restore();

      // Contorno de peto perimetral
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2.2;
      ctx.strokeRect(ox, oy, drawW, drawH);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '600 10px Inter, system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(
        `PETO PERIMETRAL (Remonte impermeable h=${replanteo.geometry.parapetTurnupMm} mm · L = ${realL.toFixed(2)} m)`,
        ox + drawW / 2,
        oy - 10
      );
      ctx.fillStyle = '#10b981';
      ctx.fillText(
        `RETÍCULA ${numTilesX}×${numTilesY} BALDOSAS (${tileLenMm}×${tileWidMm} mm · Junta ${jointMm} mm) + ${replanteo.replanteoParams.assemblyPlotsCount} PLOTS PEYGRAN`,
        ox + drawW / 2,
        oy + drawH + 16
      );
    }

    // Leyenda superior derecha
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '700 10px Inter, system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('PLANO CAD 2D DE REPLANTEO AUTOMÁTICO (ESCALA REAL)', 12, 16);

    ctx.restore();
  }
}
