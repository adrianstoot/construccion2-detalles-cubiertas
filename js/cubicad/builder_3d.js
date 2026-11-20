/**
 * =============================================================================
 * CubiCAD · Constructor CAD/BIM de Cubiertas
 * Motor 3D Fotorrealista PBR e Interactivo CAD en Vivo (Three.js)
 * =============================================================================
 * Incluye:
 * - 3 Edificios Base arquitectónicos realistas y modificables:
 *   1. Vivienda unifamiliar aislada de 2 plantas (Tejados: 2 aguas, 4 aguas, L, asimétrica)
 *   2. Edificio urbano contemporáneo de 4 plantas (Azoteas: plots, convencional, ajardinada)
 *   3. Nave industrial / Pabellón deportivo de gran luz (Metálicas: 2 aguas, 1 agua, diente sierra)
 * - Construcción real capa a capa y pieza a pieza con texturas PBR (albedo/normal/rough)
 * - Interactividad CAD en vivo:
 *   · Gizmos arrastrables (mover cumbrera/pendiente, desplazar faldón, mover sumidero)
 *   · Trazado de líneas CAD (Cumbrera, Limatesa, Limahoya, Contorno) con cota en vivo
 *   · Selección simple, multiselección (Shift) y selección por zona/marquesina (M)
 *   · Despiece / levantar capas instantáneo y animación de secuencia de montaje + captura HD/WebM
 */

import * as THREE from '../vendor/three.module.min.js';
import { OrbitControls } from '../vendor/OrbitControls.js';
import { RoomEnvironment } from '../vendor/RoomEnvironment.js';

export class CubiCADBuilder3D {
  constructor(canvas, callbacks = {}) {
    this.canvas = canvas;
    this.callbacks = callbacks;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    this.rootGroup = new THREE.Group();
    this.buildingGroup = new THREE.Group();
    this.roofLayersGroup = new THREE.Group();
    this.cadOverlayGroup = new THREE.Group();
    this.gizmosGroup = new THREE.Group();
    this.selectionBoxesGroup = new THREE.Group();

    this.textures = {};
    this.layerGroups = [];
    this.interactiveEntries = []; // { mesh, meta }
    this.orderedSequenceEntries = []; // Orden cronológico para secuencia de montaje
    this.gizmoMeshes = [];

    this.theme = 'light'; // 'light' (Apple Blanco/Negro) | 'dark'
    this.explodeFactor = 0.0;
    this.assemblyProgress = 1.0;
    this.isPlayingSequence = false;

    this.activeTool = 'select';
    this.activeLineType = 'cumbrera';
    this.roofSurfaceY = 6.2; // Plano de referencia superior del edificio activo
    this.currentState = null;
    this.currentReplanteo = null;

    // Estado de interacción CAD en canvas
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this._pointerDown = null;
    this._draggingGizmo = null;
    this._drawStartPoint = null;
    this._previewLine = null;
    this._marqueeActive = false;
    this._marqueeStart = null;
    this._marqueeEl = null;

    this._lastTypology = null;
    this._initEngine();
  }

  _initEngine() {
    if (!this.canvas) return;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf2f4f7);
    this.scene.fog = new THREE.Fog(0xf2f4f7, 42, 95);

    const w = this.canvas.clientWidth || 1000;
    const h = this.canvas.clientHeight || 680;

    this.camera = new THREE.PerspectiveCamera(36, w / h, 0.1, 180);
    this.camera.position.set(14.5, 11.5, 15.5);

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
    this.renderer.toneMappingExposure = 1.08;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

    // Iluminación arquitectónica de estudio calibrada
    this.hemiLight = new THREE.HemisphereLight(0xffffff, 0xcbd5e1, 0.92);
    this.scene.add(this.hemiLight);

    this.sunLight = new THREE.DirectionalLight(0xfff9f0, 2.15);
    this.sunLight.position.set(18, 28, 16);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.set(2048, 2048);
    this.sunLight.shadow.camera.near = 2;
    this.sunLight.shadow.camera.far = 75;
    const d = 22;
    this.sunLight.shadow.camera.left = -d;
    this.sunLight.shadow.camera.right = d;
    this.sunLight.shadow.camera.top = d;
    this.sunLight.shadow.camera.bottom = -d;
    this.sunLight.shadow.bias = -0.00035;
    this.scene.add(this.sunLight);

    this.rimLight = new THREE.DirectionalLight(0xdbeafe, 0.65);
    this.rimLight.position.set(-16, 12, -14);
    this.scene.add(this.rimLight);

    // Plano base y cuadrícula CAD minimalista
    const groundGeo = new THREE.PlaneGeometry(140, 140);
    groundGeo.rotateX(-Math.PI / 2);
    this.groundMat = new THREE.MeshStandardMaterial({
      color: 0xe9ecf1,
      roughness: 0.92,
      metalness: 0.0,
    });
    this.groundMesh = new THREE.Mesh(groundGeo, this.groundMat);
    this.groundMesh.position.y = -0.02;
    this.groundMesh.receiveShadow = true;
    this.scene.add(this.groundMesh);

    this.gridLight = new THREE.GridHelper(60, 60, 0xcbd5e1, 0xdce2ea);
    this.gridLight.position.y = 0.002;
    this.scene.add(this.gridLight);

    this.gridDark = new THREE.GridHelper(60, 60, 0x263244, 0x18202c);
    this.gridDark.position.y = 0.002;
    this.gridDark.visible = false;
    this.scene.add(this.gridDark);

    this.rootGroup.add(this.buildingGroup);
    this.rootGroup.add(this.roofLayersGroup);
    this.rootGroup.add(this.cadOverlayGroup);
    this.rootGroup.add(this.gizmosGroup);
    this.scene.add(this.rootGroup);
    this.scene.add(this.selectionBoxesGroup);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.075;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.03;
    this.controls.minDistance = 2.0;
    this.controls.maxDistance = 58.0;
    this.controls.target.set(0, 5.5, 0);

    this._loadPBRTextures();
    this._createMarqueeOverlay();
    this._bindCanvasInteraction();
    this._startLoop();
  }

  _loadPBRTextures() {
    const loader = new THREE.TextureLoader();
    const mapSets = {
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
      teja_hormigon: 'concrete_paver',
      concrete_paver: 'concrete_paver',
      wood_pine: 'wood_pine',
      slate_cupa: 'slate_pizarra',
      slate_pizarra: 'slate_pizarra',
      zinc_vmz: 'zinc_vmz',
      brushed_metal: 'brushed_metal',
      fiberglass: 'fiberglass',
      render: 'render',
      brick_clay: 'brick_clay',
      artificial_stone: 'artificial_stone',
    };

    const cache = {};
    const loadTex = (name, isColor) => {
      if (cache[name]) return cache[name];
      const t = loader.load(`./textures/${name}.png`);
      t.wrapS = THREE.RepeatWrapping;
      t.wrapT = THREE.RepeatWrapping;
      if (isColor) t.colorSpace = THREE.SRGBColorSpace;
      cache[name] = t;
      return t;
    };

    Object.entries(mapSets).forEach(([key, prefix]) => {
      this.textures[key] = {
        albedo: loadTex(`${prefix}_albedo`, true),
        normal: loadTex(`${prefix}_normal`, false),
        rough: loadTex(`${prefix}_rough`, false),
      };
    });
  }

  _makePBRMat(opts = {}) {
    const params = {
      color: opts.color ?? 0xffffff,
      roughness: opts.roughness ?? 0.65,
      metalness: opts.metalness ?? 0.05,
      side: opts.side ?? THREE.DoubleSide,
    };
    const pbr = opts.textureKey ? this.textures[opts.textureKey] : null;
    if (pbr && pbr.albedo) {
      params.map = pbr.albedo;
      params.normalMap = pbr.normal;
      params.normalScale = new THREE.Vector2(opts.normalScale ?? 0.55, opts.normalScale ?? 0.55);
      params.roughnessMap = pbr.rough;
    }
    return new THREE.MeshStandardMaterial(params);
  }

  setTheme(mode) {
    this.theme = mode === 'dark' ? 'dark' : 'light';
    if (this.theme === 'dark') {
      this.scene.background.setHex(0x0c0f15);
      this.scene.fog.color.setHex(0x0c0f15);
      this.groundMat.color.setHex(0x121721);
      this.gridLight.visible = false;
      this.gridDark.visible = true;
      this.hemiLight.intensity = 0.72;
    } else {
      this.scene.background.setHex(0xf2f4f7);
      this.scene.fog.color.setHex(0xf2f4f7);
      this.groundMat.color.setHex(0xe9ecf1);
      this.gridLight.visible = true;
      this.gridDark.visible = false;
      this.hemiLight.intensity = 0.94;
    }
  }

  setTool(tool, lineType = null) {
    this.activeTool = tool;
    if (lineType) this.activeLineType = lineType;
    this._drawStartPoint = null;
    this._clearPreviewLine();

    // Mostrar gizmos de edición en vivo cuando la herramienta Mover/Editar está activa
    this.gizmosGroup.visible = tool === 'move';
    this.renderer.domElement.style.cursor =
      tool === 'draw_line'
        ? 'crosshair'
        : tool === 'marquee'
        ? 'crosshair'
        : tool === 'move'
        ? 'grab'
        : 'default';
  }

  _createMarqueeOverlay() {
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const el = document.createElement('div');
    el.className = 'cubicad-marquee-box';
    el.style.display = 'none';
    parent.appendChild(el);
    this._marqueeEl = el;
  }

  _bindCanvasInteraction() {
    const dom = this.renderer.domElement;

    dom.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      this._pointerDown = { x: e.clientX, y: e.clientY, shiftKey: e.shiftKey };

      // 1. Herramienta Selección por Zona / Marquesina (M)
      if (this.activeTool === 'marquee') {
        this._marqueeActive = true;
        this.controls.enabled = false;
        const rect = dom.getBoundingClientRect();
        this._marqueeStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        if (this._marqueeEl) {
          this._marqueeEl.style.display = 'block';
          this._marqueeEl.style.left = `${this._marqueeStart.x}px`;
          this._marqueeEl.style.top = `${this._marqueeStart.y}px`;
          this._marqueeEl.style.width = '0px';
          this._marqueeEl.style.height = '0px';
        }
        return;
      }

      // 2. Herramienta Mover / Editar en vivo (G): comprobar si se agarra un Gizmo 3D
      if (this.activeTool === 'move' && this.gizmoMeshes.length > 0) {
        this._updatePointerCoords(e);
        this.raycaster.setFromCamera(this.pointer, this.camera);
        const hits = this.raycaster.intersectObjects(this.gizmoMeshes, false);
        if (hits.length > 0) {
          this._draggingGizmo = hits[0].object;
          this.controls.enabled = false;
          dom.style.cursor = 'grabbing';
          return;
        }
      }
    });

    dom.addEventListener('pointermove', (e) => {
      // Actualizar marquesina de selección por zona
      if (this._marqueeActive && this._marqueeStart && this._marqueeEl) {
        const rect = dom.getBoundingClientRect();
        const cx = e.clientX - rect.left;
        const cy = e.clientY - rect.top;
        const x = Math.min(this._marqueeStart.x, cx);
        const y = Math.min(this._marqueeStart.y, cy);
        const w = Math.abs(cx - this._marqueeStart.x);
        const h = Math.abs(cy - this._marqueeStart.y);
        this._marqueeEl.style.left = `${x}px`;
        this._marqueeEl.style.top = `${y}px`;
        this._marqueeEl.style.width = `${w}px`;
        this._marqueeEl.style.height = `${h}px`;
        return;
      }

      // Arrastrar Gizmo 3D en vivo (cumbrera/pendiente, alero o sumidero)
      if (this._draggingGizmo && this.currentState) {
        const hitPt = this._intersectRoofWorkPlane(e, this._draggingGizmo.userData.dragPlane || 'horizontal');
        if (hitPt && this.callbacks.onGizmoDrag) {
          this.callbacks.onGizmoDrag(this._draggingGizmo.userData.gizmoId, hitPt);
        }
        return;
      }

      // Previsualización de trazado de línea CAD (cumbrera/limatesa/limahoya)
      if (this.activeTool === 'draw_line' && this._drawStartPoint) {
        const pt = this._intersectRoofWorkPlane(e, 'horizontal');
        if (pt) this._updatePreviewLine(this._drawStartPoint, pt);
      }
    });

    window.addEventListener('pointerup', (e) => {
      // Finalizar marquesina de selección por zona
      if (this._marqueeActive) {
        this._marqueeActive = false;
        this.controls.enabled = true;
        if (this._marqueeEl) {
          const rect = dom.getBoundingClientRect();
          const endX = e.clientX - rect.left;
          const endY = e.clientY - rect.top;
          const xMin = Math.min(this._marqueeStart.x, endX);
          const xMax = Math.max(this._marqueeStart.x, endX);
          const yMin = Math.min(this._marqueeStart.y, endY);
          const yMax = Math.max(this._marqueeStart.y, endY);
          this._marqueeEl.style.display = 'none';
          if (xMax - xMin > 8 && yMax - yMin > 8) {
            this._selectInsideScreenRect(xMin, yMin, xMax, yMax, e.shiftKey);
          }
        }
        return;
      }

      // Finalizar arrastre de Gizmo
      if (this._draggingGizmo) {
        this._draggingGizmo = null;
        this.controls.enabled = true;
        dom.style.cursor = 'grab';
        if (this.callbacks.onGizmoDragEnd) this.callbacks.onGizmoDragEnd();
        return;
      }

      if (!this._pointerDown || e.target !== dom) return;
      const dx = Math.abs(e.clientX - this._pointerDown.x);
      const dy = Math.abs(e.clientY - this._pointerDown.y);
      const wasShift = this._pointerDown.shiftKey;
      this._pointerDown = null;
      if (dx > 5 || dy > 5) return; // Fue órbita de cámara

      // Trazado CAD de 2 clics (Cumbrera / Limatesa / Limahoya / Contorno)
      if (this.activeTool === 'draw_line') {
        const pt = this._intersectRoofWorkPlane(e, 'horizontal');
        if (!pt) return;
        if (!this._drawStartPoint) {
          this._drawStartPoint = pt.clone();
          if (this.callbacks.onStatusHint) {
            this.callbacks.onStatusHint(
              `Punto inicial (${pt.x.toFixed(2)}, ${pt.z.toFixed(2)} m) fijado · Haz clic en el segundo punto para cerrar ${this.activeLineType.toUpperCase()}.`
            );
          }
        } else {
          const p1 = { x: Number(this._drawStartPoint.x.toFixed(2)), y: Number(this._drawStartPoint.y.toFixed(2)), z: Number(this._drawStartPoint.z.toFixed(2)) };
          const p2 = { x: Number(pt.x.toFixed(2)), y: Number(pt.y.toFixed(2)), z: Number(pt.z.toFixed(2)) };
          this._drawStartPoint = null;
          this._clearPreviewLine();
          if (this.callbacks.onCadLineDrawn) {
            this.callbacks.onCadLineDrawn({ type: this.activeLineType, p1, p2 });
          }
        }
        return;
      }

      // Selección de elemento / pieza 3D (con soporte Shift+clic)
      this._pickSingleElement(e, wasShift);
    });

    window.addEventListener('resize', () => this.resize());
  }

  _updatePointerCoords(e) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  }

  _intersectRoofWorkPlane(e, planeKind = 'horizontal') {
    this._updatePointerCoords(e);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const target = new THREE.Vector3();
    if (planeKind === 'vertical_ridge') {
      const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
      return this.raycaster.ray.intersectPlane(plane, target) ? target : null;
    }
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -(this.roofSurfaceY + 0.35));
    return this.raycaster.ray.intersectPlane(plane, target) ? target : null;
  }

  _updatePreviewLine(p1, p2) {
    this._clearPreviewLine();
    const colorMap = {
      cumbrera: 0xef4444,
      limatesa: 0x0071e3,
      limahoya: 0x06b6d4,
      contorno: 0x111827,
    };
    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(p1.x, p1.y + 0.08, p1.z),
      new THREE.Vector3(p2.x, p2.y + 0.08, p2.z),
    ]);
    const mat = new THREE.LineBasicMaterial({
      color: colorMap[this.activeLineType] || 0x0071e3,
      linewidth: 2,
    });
    this._previewLine = new THREE.Line(geom, mat);
    this.scene.add(this._previewLine);
  }

  _clearPreviewLine() {
    if (this._previewLine) {
      this.scene.remove(this._previewLine);
      this._previewLine.geometry.dispose();
      this._previewLine = null;
    }
  }

  _pickSingleElement(e, shiftKey) {
    this._updatePointerCoords(e);
    this.raycaster.setFromCamera(this.pointer, this.camera);

    const visibleMeshes = this.interactiveEntries
      .filter((en) => en.mesh.visible && en.mesh.parent?.visible !== false)
      .map((en) => en.mesh);
    const hits = this.raycaster.intersectObjects(visibleMeshes, true);

    if (hits.length > 0) {
      let obj = hits[0].object;
      while (obj && !obj.userData?.isCubiPiece && obj.parent) {
        obj = obj.parent;
      }
      if (obj && obj.userData?.isCubiPiece) {
        if (this.callbacks.onSelectItems) {
          this.callbacks.onSelectItems([obj.userData], shiftKey);
        }
        return;
      }
    }
    if (!shiftKey && this.callbacks.onSelectItems) {
      this.callbacks.onSelectItems([], false);
    }
  }

  _selectInsideScreenRect(xMin, yMin, xMax, yMax, shiftKey) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    const selected = [];
    const worldPos = new THREE.Vector3();

    this.interactiveEntries.forEach(({ mesh, meta }) => {
      if (!mesh.visible || mesh.parent?.visible === false) return;
      mesh.getWorldPosition(worldPos);
      worldPos.project(this.camera);
      const sx = ((worldPos.x + 1) / 2) * rect.width;
      const sy = ((-worldPos.y + 1) / 2) * rect.height;
      if (sx >= xMin && sx <= xMax && sy >= yMin && sy <= yMax) {
        selected.push(meta);
      }
    });

    if (this.callbacks.onSelectItems) {
      this.callbacks.onSelectItems(selected.slice(0, 60), shiftKey);
    }
  }

  highlightSelectedCodes(selectedSet) {
    while (this.selectionBoxesGroup.children.length > 0) {
      this.selectionBoxesGroup.remove(this.selectionBoxesGroup.children[0]);
    }
    if (!selectedSet || selectedSet.size === 0) return;

    const hlMat = new THREE.LineBasicMaterial({ color: 0x0071e3 });
    this.interactiveEntries.forEach(({ mesh, meta }) => {
      const code = meta.pieceCode || meta.id;
      if (!selectedSet.has(code) || !mesh.visible) return;
      const box = new THREE.Box3().setFromObject(mesh);
      if (box.isEmpty()) return;
      const helper = new THREE.Box3Helper(box, 0x0071e3);
      helper.material = hlMat;
      this.selectionBoxesGroup.add(helper);
    });
  }

  resize() {
    if (!this.canvas || !this.renderer || !this.camera) return;
    const parent = this.canvas.parentElement;
    const w = (parent && parent.clientWidth) || this.canvas.clientWidth || 1000;
    const h = (parent && parent.clientHeight) || this.canvas.clientHeight || 680;
    if (w < 60 || h < 60) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  }

  _startLoop() {
    const loop = () => {
      requestAnimationFrame(loop);
      if (this.isPlayingSequence) {
        this.assemblyProgress += 0.0045;
        if (this.assemblyProgress >= 1.0) {
          this.assemblyProgress = 1.0;
          this.isPlayingSequence = false;
          if (this.callbacks.onSequenceTick) this.callbacks.onSequenceTick(1.0, false);
        } else if (this.callbacks.onSequenceTick) {
          this.callbacks.onSequenceTick(this.assemblyProgress, true);
        }
        this._applyAssemblyProgress();
      }
      if (this.controls) this.controls.update();
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    };
    loop();
  }

  // ===========================================================================
  // RECONSTRUCCIÓN COMPLETA DE EDIFICIO BASE + CUBIERTA CAPA A CAPA
  // ===========================================================================
  rebuild(state, replanteo, selectedSet = new Set()) {
    this.currentState = state;
    this.currentReplanteo = replanteo;

    const clearGroup = (g) => {
      while (g.children.length > 0) g.remove(g.children[0]);
    };
    clearGroup(this.buildingGroup);
    clearGroup(this.roofLayersGroup);
    clearGroup(this.cadOverlayGroup);
    clearGroup(this.gizmosGroup);

    this.layerGroups = [];
    this.interactiveEntries = [];
    this.orderedSequenceEntries = [];
    this.gizmoMeshes = [];

    if (state.typology === 'tejado') {
      this._buildHouse2FloorsAndSlopedRoof(state, replanteo);
    } else if (state.typology === 'azotea') {
      this._buildApartment4FloorsAndFlatRoof(state, replanteo);
    } else {
      this._buildSportsHallAndMetalRoof(state, replanteo);
    }

    this._renderUserCadLines(state.cadLines || []);
    this._applyExplodeFactor();
    this._applyAssemblyProgress();
    this.highlightSelectedCodes(selectedSet);
    this.gizmosGroup.visible = this.activeTool === 'move';

    // Reenfocar cámara limpiamente solo al cambiar de tipología
    if (this._lastTypology !== state.typology) {
      this._lastTypology = state.typology;
      this.setCameraPreset('iso');
    }
  }

  _registerInteractive(mesh, meta, includeInSequence = true) {
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData = { isCubiPiece: true, ...meta };
    this.interactiveEntries.push({ mesh, meta: mesh.userData });
    if (includeInSequence) {
      this.orderedSequenceEntries.push({ mesh, meta: mesh.userData });
    }
  }

  _createLayer(key, title, orderIndex, explodeStep, productId) {
    const g = new THREE.Group();
    g.name = key;
    g.userData = { layerKey: key, title, orderIndex, explodeStep, productId };
    this.roofLayersGroup.add(g);
    this.layerGroups.push(g);
    return g;
  }

  _addGizmoHandle(id, pos, colorHex, dragPlane = 'horizontal', label = '') {
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.28, 20, 20),
      new THREE.MeshStandardMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: 0.35,
        roughness: 0.25,
        metalness: 0.3,
      })
    );
    sphere.position.copy(pos);
    sphere.userData = { gizmoId: id, dragPlane, label };
    // Anillo exterior Apple
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(0.42, 0.035, 10, 28),
      new THREE.MeshBasicMaterial({ color: 0xffffff })
    );
    ring.rotation.x = Math.PI / 2;
    sphere.add(ring);

    this.gizmosGroup.add(sphere);
    this.gizmoMeshes.push(sphere);
  }

  // ===========================================================================
  // TIPOLOGÍA 1: VIVIENDA AISLADA 2 PLANTAS + TEJADO INCLINADO (4 VARIANTES)
  // ===========================================================================
  _buildHouse2FloorsAndSlopedRoof(state, rep) {
    const L = state.geometry.lengthM || 10.4; // Eje X
    const W = state.geometry.widthM || 8.2;   // Eje Z
    const H = 6.0; // 2 plantas reales (3,0 m por planta)
    this.roofSurfaceY = H;

    // 1. EDIFICIO BASE: Vivienda unifamiliar moderna de 2 plantas
    const stuccoMat = this._makePBRMat({ color: 0xf7f7f5, textureKey: 'render', roughness: 0.82, normalScale: 0.25 });
    const plinthMat = this._makePBRMat({ color: 0xd8dce2, textureKey: 'artificial_stone', roughness: 0.78 });
    const frameMat = new THREE.MeshStandardMaterial({ color: 0x181b20, roughness: 0.38, metalness: 0.65 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x26384d, roughness: 0.08, metalness: 0.85, transparent: true, opacity: 0.82 });
    const slabMat = this._makePBRMat({ color: 0x9ca3af, textureKey: 'concrete', roughness: 0.8 });

    // Parcela y plataforma de acceso
    const lawn = new THREE.Mesh(
      new THREE.BoxGeometry(L + 8, 0.08, W + 8),
      new THREE.MeshStandardMaterial({ color: 0xd9e2d5, roughness: 0.95 })
    );
    lawn.position.set(0, 0.04, 0);
    lawn.receiveShadow = true;
    this.buildingGroup.add(lawn);

    const walkway = new THREE.Mesh(new THREE.BoxGeometry(L + 2.2, 0.14, W + 2.2), plinthMat);
    walkway.position.set(0, 0.07, 0);
    walkway.receiveShadow = true;
    this.buildingGroup.add(walkway);

    // Volumen principal 2 plantas
    const body = new THREE.Mesh(new THREE.BoxGeometry(L, H - 0.22, W), stuccoMat);
    body.position.set(0, (H - 0.22) / 2 + 0.14, 0);
    body.castShadow = true;
    body.receiveShadow = true;
    this.buildingGroup.add(body);

    // Forjado superior resistente (soporte sobre el que se construye el tejado)
    const topSlab = new THREE.Mesh(new THREE.BoxGeometry(L + 0.2, 0.24, W + 0.2), slabMat);
    topSlab.position.set(0, H - 0.12, 0);
    topSlab.castShadow = true;
    topSlab.receiveShadow = true;
    this.buildingGroup.add(topSlab);

    // Si la variante es Planta en L, añadir el ala arquitectónica perpendicular (+Z)
    const isLShape = state.variant === 'planta_L';
    const wingW = W * 0.52;
    const wingLen = L * 0.48;
    if (isLShape) {
      const wingBody = new THREE.Mesh(new THREE.BoxGeometry(wingW, H - 0.22, wingLen), stuccoMat);
      wingBody.position.set(-L / 2 + wingW / 2, (H - 0.22) / 2 + 0.14, W / 2 + wingLen / 2);
      wingBody.castShadow = true;
      wingBody.receiveShadow = true;
      this.buildingGroup.add(wingBody);

      const wingSlab = new THREE.Mesh(new THREE.BoxGeometry(wingW + 0.2, 0.24, wingLen + 0.2), slabMat);
      wingSlab.position.set(-L / 2 + wingW / 2, H - 0.12, W / 2 + wingLen / 2);
      this.buildingGroup.add(wingSlab);
    }

    // Ventanas acristaladas de Planta Baja y Planta Primera en fachadas frontal (+Z) y trasera (-Z)
    const addWindow = (x, y, z, w, h, rotY = 0) => {
      const grp = new THREE.Group();
      const frame = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.12), frameMat);
      const pane = new THREE.Mesh(new THREE.BoxGeometry(w - 0.14, h - 0.14, 0.14), glassMat);
      grp.add(frame, pane);
      grp.position.set(x, y, z);
      grp.rotation.y = rotY;
      this.buildingGroup.add(grp);
    };

    const numWinX = Math.max(2, Math.floor(L / 3.1));
    for (let i = 0; i < numWinX; i++) {
      const wx = -L / 2 + (L / (numWinX + 1)) * (i + 1);
      // Planta baja y planta alta fachada delantera
      if (!(isLShape && wx < -L / 2 + wingW + 0.4)) {
        addWindow(wx, 1.55, W / 2 + 0.02, 1.65, 1.85, 0);
        addWindow(wx, 4.45, W / 2 + 0.02, 1.75, 1.45, 0);
      }
      // Fachada trasera
      addWindow(wx, 1.55, -W / 2 - 0.02, 1.65, 1.65, 0);
      addWindow(wx, 4.45, -W / 2 - 0.02, 1.65, 1.45, 0);
    }
    // Ventanas laterales
    addWindow(L / 2 + 0.02, 4.45, -W * 0.2, 1.5, 1.4, Math.PI / 2);
    addWindow(L / 2 + 0.02, 4.45, W * 0.2, 1.5, 1.4, Math.PI / 2);
    addWindow(-L / 2 - 0.02, 4.45, 0, 1.6, 1.4, Math.PI / 2);

    // Línea de forjado entre planta baja y primera
    const midBand = new THREE.Mesh(new THREE.BoxGeometry(L + 0.08, 0.16, W + 0.08), plinthMat);
    midBand.position.set(0, 3.05, 0);
    this.buildingGroup.add(midBand);

    // =========================================================================
    // 2. CONSTRUCCIÓN DE LA CUBIERTA INCLINADA CAPA A CAPA Y PIEZA A PIEZA
    // =========================================================================
    const slopePct = state.geometry.slopePct || 32;
    const overhang = state.geometry.eaveOverhangM ?? 0.45;
    const ridgeOffset = state.variant === 'asimetrica' ? (state.geometry.ridgeOffsetRatio || 0) * W : 0;

    const totalLenX = L + overhang * 2;
    const halfWFront = W / 2 + overhang - ridgeOffset;
    const halfWBack = W / 2 + overhang + ridgeOffset;
    const ridgeHeight = Math.max(0.45, Math.min(halfWFront, halfWBack) * (slopePct / 100));

    // Hastiales triangulares para Dos Aguas o Asimétrica (cuando hay soporte activo)
    if (state.layersEnabled.support && (state.variant === 'dos_aguas' || state.variant === 'asimetrica' || isLShape)) {
      const gableShape = new THREE.Shape();
      gableShape.moveTo(-W / 2, 0);
      gableShape.lineTo(W / 2, 0);
      gableShape.lineTo(ridgeOffset, ridgeHeight);
      gableShape.closePath();
      const gableGeo = new THREE.ExtrudeGeometry(gableShape, { depth: 0.24, bevelEnabled: false });
      gableGeo.rotateY(Math.PI / 2);

      const gRight = new THREE.Mesh(gableGeo, stuccoMat);
      gRight.position.set(L / 2 - 0.24, H, 0);
      this.buildingGroup.add(gRight);

      const gLeft = new THREE.Mesh(gableGeo, stuccoMat);
      gLeft.position.set(-L / 2, H, 0);
      this.buildingGroup.add(gLeft);
    }

    // Construimos cada faldón (Delantero +Z y Trasero -Z; y si es Cuatro Aguas o Planta L, los paños adicionales)
    const { supportPanel, battenSys, covering, fastener, gutter } = rep.products;

    const gSupport = this._createLayer('L1_SOPORTE', `1. Soporte ${supportPanel.brand}`, 1, 0.35, supportPanel.id);
    const gMembrane = this._createLayer('L2_LAMINA', `2. Lámina Transpirable ${battenSys.brand}`, 2, 0.72, battenSys.id);
    const gBattens = this._createLayer('L5_RASTRELES_PLOTS', `3. Doble Rastrel (${rep.replanteoParams.supportBattenStepMm} mm)`, 3, 1.08, battenSys.id);
    const gCovering = this._createLayer('L6_COBERTURA', `4. Cobertura ${covering.brand} (${covering.model})`, 4, 1.48, covering.id);
    const gDrainage = this._createLayer('L7_EVACUACION', `5. Canalón ${gutter.brand} y Cumbrera/Limatesas`, 5, 1.88, gutter.id);

    const buildSlopePlane = (planeCfg) => {
      const {
        idPrefix,
        widthAlongEave,
        horizRun,
        rise,
        originPos,
        yawRad,
        isHipTrapezoid = false,
        hipSideInsetTop = 0,
      } = planeCfg;

      const angle = Math.atan2(rise, horizRun);
      const rafterLen = Math.hypot(horizRun, rise);

      const makeSlopeContainer = (parentLayer) => {
        const pivot = new THREE.Group();
        pivot.position.copy(originPos);
        pivot.rotation.y = yawRad;
        const tilt = new THREE.Group();
        tilt.rotation.x = angle;
        pivot.add(tilt);
        parentLayer.add(pivot);
        return tilt;
      };

      const woodMat = this._makePBRMat({ color: 0xc89b63, textureKey: 'wood_pine', roughness: 0.7 });
      const xpsMat = this._makePBRMat({ color: 0x38bdf8, textureKey: 'xps_foam', roughness: 0.55 });
      const membMat = this._makePBRMat({ color: 0x1e293b, textureKey: 'geotextile', roughness: 0.8 });
      const covMat = this._makePBRMat({
        color: covering.colorHex || '#c86446',
        textureKey: covering.textureKey || 'terracotta',
        roughness: covering.subType === 'pizarra_natural' ? 0.45 : covering.subType === 'zinc_junta_alzada' ? 0.34 : 0.56,
        metalness: covering.subType === 'zinc_junta_alzada' || covering.subType === 'panel_sandwich_metalico' ? 0.68 : 0.05,
      });
      const zincMat = this._makePBRMat({ color: 0x94a3b8, textureKey: 'zinc_vmz', roughness: 0.34, metalness: 0.76 });

      const panelThick = (supportPanel.geometry.thicknessMm || 109) / 1000;
      const battenStepM = Math.max(0.115, (rep.replanteoParams.supportBattenStepMm || 380) / 1000);

      // CAPA 1: Soporte estructural (pares + paneles sándwich Thermochip TAH)
      if (state.layersEnabled.support) {
        const tiltSup = makeSlopeContainer(gSupport);
        const numRafters = Math.max(3, Math.floor(widthAlongEave / 0.85) + 1);
        for (let i = 0; i < numRafters; i++) {
          const rx = -widthAlongEave / 2 + (widthAlongEave / (numRafters - 1)) * i;
          // En 4 aguas (limatesas), acortar los pares de esquina según el trapecio real
          let localLen = rafterLen;
          if (isHipTrapezoid && hipSideInsetTop > 0.05) {
            const topHalf = Math.max(0.1, widthAlongEave / 2 - hipSideInsetTop);
            if (Math.abs(rx) > topHalf) {
              const frac = Math.max(0.12, 1 - (Math.abs(rx) - topHalf) / hipSideInsetTop);
              localLen = rafterLen * frac;
            }
          }
          const rMesh = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.14, localLen), woodMat);
          rMesh.position.set(rx, -0.07, rafterLen - localLen / 2);
          tiltSup.add(rMesh);
        }

        // Panel sándwich continuo/modular (recortado en trapecio si es 4 aguas)
        const panelMesh = this._makeTrapezoidSlab(
          widthAlongEave,
          isHipTrapezoid ? Math.max(0.2, widthAlongEave - hipSideInsetTop * 2) : widthAlongEave,
          rafterLen,
          panelThick,
          state.layersEnabled.insulation ? xpsMat : woodMat
        );
        panelMesh.position.set(0, panelThick / 2, rafterLen / 2);
        // Cara superior tablero madera
        const topSkin = this._makeTrapezoidSlab(
          widthAlongEave,
          isHipTrapezoid ? Math.max(0.2, widthAlongEave - hipSideInsetTop * 2) : widthAlongEave,
          rafterLen,
          0.016,
          woodMat
        );
        topSkin.position.set(0, panelThick + 0.008, rafterLen / 2);
        tiltSup.add(panelMesh, topSkin);

        this._registerInteractive(panelMesh, {
          pieceCode: `SOPORTE-${idPrefix}`,
          layerKey: 'L1_SOPORTE',
          layerName: supportPanel.model,
          productId: supportPanel.id,
          roleLabel: `Soporte estructural + núcleo aislante ${supportPanel.brand} (${supportPanel.geometry.thicknessMm} mm)`,
          dimensionsMm: `${Math.round(widthAlongEave * 1000)} × ${Math.round(rafterLen * 1000)} × ${supportPanel.geometry.thicknessMm} mm`,
          weightKg: Number((widthAlongEave * rafterLen * (supportPanel.geometry.surfaceWeightKgM2 || 24)).toFixed(1)),
        });
      }

      // CAPA 2: Lámina Impermeable Transpirable Rothoblaas TRASPIR EVO
      if (state.layersEnabled.membrane) {
        const tiltMem = makeSlopeContainer(gMembrane);
        const memMesh = this._makeTrapezoidSlab(
          widthAlongEave + 0.02,
          isHipTrapezoid ? Math.max(0.22, widthAlongEave - hipSideInsetTop * 2) : widthAlongEave + 0.02,
          rafterLen,
          0.006,
          membMat
        );
        memMesh.position.set(0, panelThick + 0.022, rafterLen / 2);
        tiltMem.add(memMesh);
        this._registerInteractive(memMesh, {
          pieceCode: `LAMINA-${idPrefix}`,
          layerKey: 'L2_LAMINA',
          layerName: 'Lámina Transpirable Rothoblaas TRASPIR EVO 210',
          productId: battenSys.id,
          roleLabel: 'Barrera impermeable transpirable Sd = 0,04 m con solape sellado 100 mm',
          dimensionsMm: `Ancho rollo 1500 mm · e = 0,85 mm`,
          weightKg: Number((widthAlongEave * rafterLen * 0.21).toFixed(1)),
        });
      }

      // CAPA 3: Contrarastreles y Rastreles Horizontales al paso real de ficha técnica
      const baseBattenY = panelThick + 0.03;
      if (state.layersEnabled.battens) {
        const tiltBat = makeSlopeContainer(gBattens);
        const nRowsBat = Math.min(26, Math.max(3, Math.floor(rafterLen / battenStepM)));
        for (let r = 0; r <= nRowsBat; r++) {
          const zFromRidge = rafterLen - 0.06 - r * (rafterLen / (nRowsBat + 0.5));
          if (zFromRidge < 0.06) continue;
          const fracFromEave = 1 - zFromRidge / rafterLen;
          const rowSpan = isHipTrapezoid
            ? Math.max(0.3, widthAlongEave - 2 * hipSideInsetTop * fracFromEave)
            : widthAlongEave;

          const bMesh = new THREE.Mesh(new THREE.BoxGeometry(rowSpan, 0.032, 0.048), woodMat);
          bMesh.position.set(0, baseBattenY + 0.038, zFromRidge);
          tiltBat.add(bMesh);
          if (r % 2 === 0) {
            this._registerInteractive(bMesh, {
              pieceCode: `RASTREL-${idPrefix}-H${r + 1}`,
              layerKey: 'L5_RASTRELES_PLOTS',
              layerName: battenSys.model,
              productId: battenSys.id,
              roleLabel: `Rastrel horizontal 30×50 mm · Paso real ${rep.replanteoParams.supportBattenStepMm} mm`,
              dimensionsMm: `${Math.round(rowSpan * 1000)} × 50 × 30 mm`,
              weightKg: Number((rowSpan * 0.72).toFixed(1)),
            });
          }
        }
      }

      // CAPA 4: Cobertura Exterior Pieza a Pieza (InstancedMesh ultra fluido con geometría 3D real)
      const covY = baseBattenY + 0.062;
      if (state.layersEnabled.covering) {
        const tiltCov = makeSlopeContainer(gCovering);
        this._populateSlopeCoveringPieces(tiltCov, {
          idPrefix,
          widthAlongEave,
          rafterLen,
          covY,
          covering,
          covMat,
          rep,
          isHipTrapezoid,
          hipSideInsetTop,
        });
      }

      // CAPA 5: Canalón de alero VMZINC D333
      if (state.layersEnabled.drainage) {
        const tiltDr = makeSlopeContainer(gDrainage);
        const rGut = (gutter.geometry.widthNominalMm || 153) / 2000;
        const gutGeo = new THREE.CylinderGeometry(rGut, rGut, widthAlongEave + 0.14, 18, 1, true, 0, Math.PI);
        gutGeo.rotateZ(-Math.PI / 2);
        const gutMesh = new THREE.Mesh(gutGeo, zincMat);
        gutMesh.position.set(0, baseBattenY + 0.01, rafterLen + rGut + 0.02);
        tiltDr.add(gutMesh);

        this._registerInteractive(gutMesh, {
          pieceCode: `CANALON-${idPrefix}`,
          layerKey: 'L7_EVACUACION',
          layerName: gutter.model,
          productId: gutter.id,
          roleLabel: `Canalón semicircular de zinc-titanio D${gutter.geometry.developmentMm || 333} (Ø${gutter.geometry.widthNominalMm} mm)`,
          dimensionsMm: `L = ${Math.round(widthAlongEave * 1000)} mm · Ø${gutter.geometry.widthNominalMm} mm`,
          weightKg: Number(((widthAlongEave / 4) * gutter.geometry.unitWeightKg).toFixed(1)),
        });
      }
    };

    const isFourWaters = state.variant === 'cuatro_aguas';
    const hipInset = isFourWaters ? Math.min(totalLenX * 0.42, halfWFront) : 0;

    // Faldón Frontal (+Z)
    buildSlopePlane({
      idPrefix: 'SUR',
      widthAlongEave: totalLenX,
      horizRun: halfWFront,
      rise: ridgeHeight,
      originPos: new THREE.Vector3(0, H + ridgeHeight, ridgeOffset),
      yawRad: 0,
      isHipTrapezoid: isFourWaters,
      hipSideInsetTop: hipInset,
    });

    // Faldón Trasero (-Z)
    buildSlopePlane({
      idPrefix: 'NORTE',
      widthAlongEave: totalLenX,
      horizRun: halfWBack,
      rise: ridgeHeight,
      originPos: new THREE.Vector3(0, H + ridgeHeight, ridgeOffset),
      yawRad: Math.PI,
      isHipTrapezoid: isFourWaters,
      hipSideInsetTop: hipInset,
    });

    // Si es Cuatro Aguas: añadir los 2 faldones triangulares laterales (Este y Oeste) + 4 limatesas
    if (isFourWaters) {
      buildSlopePlane({
        idPrefix: 'ESTE',
        widthAlongEave: W + overhang * 2,
        horizRun: hipInset,
        rise: ridgeHeight,
        originPos: new THREE.Vector3(totalLenX / 2 - hipInset, H + ridgeHeight, 0),
        yawRad: Math.PI / 2,
        isHipTrapezoid: true,
        hipSideInsetTop: (W + overhang * 2) * 0.49,
      });
      buildSlopePlane({
        idPrefix: 'OESTE',
        widthAlongEave: W + overhang * 2,
        horizRun: hipInset,
        rise: ridgeHeight,
        originPos: new THREE.Vector3(-totalLenX / 2 + hipInset, H + ridgeHeight, 0),
        yawRad: -Math.PI / 2,
        isHipTrapezoid: true,
        hipSideInsetTop: (W + overhang * 2) * 0.49,
      });
    }

    // Si es Planta en L: añadir los 2 faldones perpendiculares del ala lateral + limahoya metálica
    if (isLShape) {
      const wingRidgeX = -L / 2 + wingW / 2;
      const wingHalfSpan = wingW / 2 + overhang;
      const wingRise = Math.min(ridgeHeight, wingHalfSpan * (slopePct / 100));
      const wingLengthTotal = wingLen + W * 0.35 + overhang;

      buildSlopePlane({
        idPrefix: 'ALA-ESTE',
        widthAlongEave: wingLengthTotal,
        horizRun: wingHalfSpan,
        rise: wingRise,
        originPos: new THREE.Vector3(wingRidgeX, H + wingRise, W / 2 + wingLen / 2 - W * 0.14),
        yawRad: Math.PI / 2,
      });
      buildSlopePlane({
        idPrefix: 'ALA-OESTE',
        widthAlongEave: wingLengthTotal,
        horizRun: wingHalfSpan,
        rise: wingRise,
        originPos: new THREE.Vector3(wingRidgeX, H + wingRise, W / 2 + wingLen / 2 - W * 0.14),
        yawRad: -Math.PI / 2,
      });
    }

    // Cumbrera ventilada de remate en L7_EVACUACION
    if (state.layersEnabled.drainage && state.layersEnabled.covering) {
      const ridgeLen = isFourWaters ? Math.max(0.5, totalLenX - hipInset * 2) : totalLenX;
      const ridgeMat = this._makePBRMat({
        color: covering.colorHex || '#c86446',
        textureKey: covering.textureKey || 'terracotta',
        roughness: 0.55,
      });
      const rGeo = new THREE.CylinderGeometry(0.13, 0.13, ridgeLen, 16, 1, true, 0, Math.PI);
      rGeo.rotateZ(Math.PI / 2);
      const rMesh = new THREE.Mesh(rGeo, ridgeMat);
      rMesh.position.set(0, H + ridgeHeight + 0.22, ridgeOffset);
      gDrainage.add(rMesh);
      this._registerInteractive(rMesh, {
        pieceCode: 'CUMBRERA-VENTILADA',
        layerKey: 'L7_EVACUACION',
        layerName: `Caballetes de Cumbrera Ventilada (${covering.brand})`,
        productId: covering.id,
        roleLabel: 'Remate ventilado en seco de cumbrera con banda autoadhesiva',
        dimensionsMm: `Longitud cumbrera ${Math.round(ridgeLen * 1000)} mm`,
        weightKg: Number((Math.ceil(ridgeLen / 0.38) * 3.4).toFixed(1)),
      });
    }

    // Gizmos manipuladores interactivos 3D (arrastrar cumbrera para pendiente/asimetría y alero para ancho)
    this._addGizmoHandle(
      'ridge_height',
      new THREE.Vector3(0, H + ridgeHeight + 0.55, ridgeOffset),
      0x0071e3,
      'vertical_ridge',
      'Arrastrar Cumbrera (Pendiente / Posición)'
    );
    this._addGizmoHandle(
      'eave_width',
      new THREE.Vector3(totalLenX / 2 + 0.15, H + 0.15, W / 2),
      0x16a34a,
      'horizontal',
      'Arrastrar Esquina (Dimensiones)'
    );
  }

  /**
   * Genera cada pieza individual de cobertura sobre un faldón usando InstancedMesh
   * para obtener 60 FPS fluidos con geometría 3D real (Teja curva canal/cobija, mixta, plana, hormigón, pizarra, zinc, panel sándwich, fibrocemento).
   */
  _populateSlopeCoveringPieces(parentTilt, cfg) {
    const {
      idPrefix,
      widthAlongEave,
      rafterLen,
      covY,
      covering,
      covMat,
      rep,
      isHipTrapezoid,
      hipSideInsetTop,
    } = cfg;

    const stepM = Math.max(0.12, (rep.replanteoParams.battenStepMm || 380) / 1000);
    const usefulWidM = Math.max(0.18, (rep.replanteoParams.usefulWidthMm || 240) / 1000);
    const lenNomM = (covering.geometry.lengthNominalMm || 450) / 1000;

    if (covering.subType === 'zinc_junta_alzada') {
      const seamH = (covering.geometry.seamHeightMm || 25) / 1000;
      const cols = Math.max(3, Math.floor(widthAlongEave / usefulWidM));
      const dummy = new THREE.Object3D();
      const trayGeo = new THREE.BoxGeometry(usefulWidM - 0.008, 0.006, rafterLen);
      const seamGeo = new THREE.BoxGeometry(0.014, seamH, rafterLen);

      const trayInst = new THREE.InstancedMesh(trayGeo, covMat, cols);
      const seamInst = new THREE.InstancedMesh(seamGeo, covMat, cols + 1);
      for (let c = 0; c < cols; c++) {
        const x = -((cols - 1) * usefulWidM) / 2 + c * usefulWidM;
        dummy.position.set(x, covY, rafterLen / 2);
        dummy.rotation.set(0, 0, 0);
        dummy.updateMatrix();
        trayInst.setMatrixAt(c, dummy.matrix);
      }
      for (let c = 0; c <= cols; c++) {
        const x = -(cols * usefulWidM) / 2 + c * usefulWidM;
        dummy.position.set(x, covY + seamH / 2, rafterLen / 2);
        dummy.updateMatrix();
        seamInst.setMatrixAt(c, dummy.matrix);
      }
      parentTilt.add(trayInst, seamInst);
      this._registerInteractive(trayInst, {
        pieceCode: `ZINC-BANDEJAS-${idPrefix}`,
        layerKey: 'L6_COBERTURA',
        layerName: covering.model,
        productId: covering.id,
        roleLabel: `${cols} bandejas VMZINC Doble Junta Alzada H=${covering.geometry.seamHeightMm} mm`,
        dimensionsMm: `Ancho útil ${covering.geometry.usefulWidthMm} mm × L=${Math.round(rafterLen * 1000)} mm`,
        weightKg: Number((widthAlongEave * rafterLen * (covering.geometry.surfaceWeightKgM2 || 6.3)).toFixed(1)),
      });
      return;
    }

    if (covering.subType === 'panel_sandwich_metalico') {
      const coreThick = (covering.geometry.thicknessMm || 80) / 1000;
      const cols = Math.max(3, Math.floor(widthAlongEave / 1.0));
      const dummy = new THREE.Object3D();
      const bodyGeo = new THREE.BoxGeometry(0.992, coreThick, rafterLen);
      const ribGeo = new THREE.BoxGeometry(0.052, 0.036, rafterLen);

      const bodyInst = new THREE.InstancedMesh(bodyGeo, covMat, cols);
      const ribInst = new THREE.InstancedMesh(ribGeo, covMat, cols * 3);
      let rIdx = 0;
      for (let c = 0; c < cols; c++) {
        const x = -((cols - 1) * 1.0) / 2 + c * 1.0;
        dummy.position.set(x, covY + coreThick / 2, rafterLen / 2);
        dummy.rotation.set(0, 0, 0);
        dummy.updateMatrix();
        bodyInst.setMatrixAt(c, dummy.matrix);

        [-0.46, 0, 0.46].forEach((rx) => {
          dummy.position.set(x + rx, covY + coreThick + 0.018, rafterLen / 2);
          dummy.updateMatrix();
          ribInst.setMatrixAt(rIdx++, dummy.matrix);
        });
      }
      parentTilt.add(bodyInst, ribInst);
      this._registerInteractive(bodyInst, {
        pieceCode: `KINGSPAN-${idPrefix}`,
        layerKey: 'L6_COBERTURA',
        layerName: covering.model,
        productId: covering.id,
        roleLabel: `${cols} Paneles Sándwich 3 Grecas (Núcleo PIR ${covering.geometry.thicknessMm} mm)`,
        dimensionsMm: `Ancho útil 1000 mm · Espesor valle ${covering.geometry.thicknessMm} mm`,
        weightKg: Number((widthAlongEave * rafterLen * (covering.geometry.surfaceWeightKgM2 || 12.3)).toFixed(1)),
      });
      return;
    }

    // Teja Curva (Canal + Cobija), Teja Mixta, Teja Plana, Teja Hormigón, Pizarra Natural o Fibrocemento
    const maxRows = covering.subType === 'pizarra_natural' ? Math.min(34, Math.ceil(rafterLen / stepM)) : Math.min(24, Math.ceil(rafterLen / stepM));
    const maxCols = Math.min(48, Math.ceil(widthAlongEave / usefulWidM));
    const placements = [];

    for (let r = 0; r < maxRows; r++) {
      const zCenter = rafterLen - lenNomM * 0.45 - r * (rafterLen / maxRows);
      if (zCenter < 0.05) continue;
      const fracFromEave = 1 - zCenter / rafterLen;
      const allowedHalfW = isHipTrapezoid
        ? Math.max(0.15, widthAlongEave / 2 - hipSideInsetTop * fracFromEave)
        : widthAlongEave / 2;
      const stagger = covering.subType === 'pizarra_natural' ? (r % 2) * (usefulWidM * 0.5) : 0;

      for (let c = 0; c < maxCols; c++) {
        const xCenter = -((maxCols - 1) * usefulWidM) / 2 + c * usefulWidM + stagger;
        if (Math.abs(xCenter) > allowedHalfW) continue;
        placements.push({ x: xCenter, y: covY + r * 0.004, z: zCenter, r, c });
      }
    }

    if (placements.length === 0) return;
    const dummy = new THREE.Object3D();

    if (covering.subType === 'teja_curva') {
      const rFront = (covering.geometry.widthNominalMm || 210) / 2000;
      const rRear = (covering.geometry.widthNarrowMm || 170) / 2000;

      const canalGeo = new THREE.CylinderGeometry(rRear, rFront, lenNomM, 10, 1, true, 0, Math.PI);
      canalGeo.rotateY(-Math.PI / 2);
      canalGeo.rotateX(Math.PI / 2);

      const cobijaGeo = new THREE.CylinderGeometry(rFront, rRear, lenNomM, 10, 1, true, 0, Math.PI);
      cobijaGeo.rotateY(Math.PI / 2);
      cobijaGeo.rotateX(Math.PI / 2);

      const cobijaMat = covMat.clone();
      cobijaMat.color.offsetHSL(0.01, 0.04, 0.04);

      const canalInst = new THREE.InstancedMesh(canalGeo, covMat, placements.length);
      const cobijaInst = new THREE.InstancedMesh(cobijaGeo, cobijaMat, placements.length);

      placements.forEach((p, idx) => {
        dummy.position.set(p.x, p.y + rFront * 0.85, p.z);
        dummy.rotation.set(-0.025, 0, 0);
        dummy.updateMatrix();
        canalInst.setMatrixAt(idx, dummy.matrix);

        dummy.position.set(p.x + usefulWidM * 0.5, p.y + rFront * 0.95, p.z);
        dummy.updateMatrix();
        cobijaInst.setMatrixAt(idx, dummy.matrix);
      });

      parentTilt.add(canalInst, cobijaInst);
      this._registerInteractive(cobijaInst, {
        pieceCode: `TEJAS-CURVAS-${idPrefix}`,
        layerKey: 'L6_COBERTURA',
        layerName: covering.model,
        productId: covering.id,
        roleLabel: `${placements.length} canales + ${placements.length} cobijas (${covering.brand}) · Paso ${rep.replanteoParams.battenStepMm} mm`,
        dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm}/${covering.geometry.widthNarrowMm || 170} × ${covering.geometry.thicknessMm} mm`,
        weightKg: Number((placements.length * 2 * covering.geometry.unitWeightKg).toFixed(1)),
      });
    } else if (covering.subType === 'pizarra_natural' || covering.subType === 'teja_plana') {
      const thickM = covering.subType === 'pizarra_natural' ? 0.007 : 0.018;
      const tileGeo = new THREE.BoxGeometry(usefulWidM - 0.004, thickM, lenNomM);
      const inst = new THREE.InstancedMesh(tileGeo, covMat, placements.length);
      placements.forEach((p, idx) => {
        dummy.position.set(p.x, p.y + thickM / 2, p.z);
        dummy.rotation.set(-0.018, 0, 0);
        dummy.updateMatrix();
        inst.setMatrixAt(idx, dummy.matrix);
      });
      parentTilt.add(inst);
      this._registerInteractive(inst, {
        pieceCode: `${covering.subType === 'pizarra_natural' ? 'PIZARRA' : 'TEJA-PLANA'}-${idPrefix}`,
        layerKey: 'L6_COBERTURA',
        layerName: covering.model,
        productId: covering.id,
        roleLabel: `${placements.length} piezas individuales (${covering.brand}) · Paso ${rep.replanteoParams.battenStepMm} mm`,
        dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm} × ${covering.geometry.thicknessMm} mm`,
        weightKg: Number((placements.length * covering.geometry.unitWeightKg).toFixed(1)),
      });
    } else {
      // Teja Mixta / Teja de Hormigón / Placa Ondulada
      const flatGeo = new THREE.BoxGeometry(usefulWidM - 0.004, 0.015, lenNomM);
      const archGeo = new THREE.CylinderGeometry(usefulWidM * 0.26, usefulWidM * 0.28, lenNomM, 8, 1, true, 0, Math.PI);
      archGeo.rotateY(Math.PI / 2);
      archGeo.rotateX(Math.PI / 2);

      const flatInst = new THREE.InstancedMesh(flatGeo, covMat, placements.length);
      const archInst = new THREE.InstancedMesh(archGeo, covMat, placements.length);
      placements.forEach((p, idx) => {
        dummy.position.set(p.x, p.y + 0.012, p.z);
        dummy.rotation.set(-0.02, 0, 0);
        dummy.updateMatrix();
        flatInst.setMatrixAt(idx, dummy.matrix);

        dummy.position.set(p.x + usefulWidM * 0.2, p.y + 0.018, p.z);
        dummy.updateMatrix();
        archInst.setMatrixAt(idx, dummy.matrix);
      });
      parentTilt.add(flatInst, archInst);
      this._registerInteractive(archInst, {
        pieceCode: `COBERTURA-${idPrefix}`,
        layerKey: 'L6_COBERTURA',
        layerName: covering.model,
        productId: covering.id,
        roleLabel: `${placements.length} piezas (${covering.brand}) · Paso ${rep.replanteoParams.battenStepMm} mm`,
        dimensionsMm: `${covering.geometry.lengthNominalMm} × ${covering.geometry.widthNominalMm} × ${covering.geometry.thicknessMm} mm`,
        weightKg: Number((placements.length * covering.geometry.unitWeightKg).toFixed(1)),
      });
    }
  }

  _makeTrapezoidSlab(wBottom, wTop, depth, thick, mat) {
    const shape = new THREE.Shape();
    shape.moveTo(-wBottom / 2, depth / 2);
    shape.lineTo(wBottom / 2, depth / 2);
    shape.lineTo(wTop / 2, -depth / 2);
    shape.lineTo(-wTop / 2, -depth / 2);
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, { depth: thick, bevelEnabled: false });
    geo.rotateX(Math.PI / 2);
    geo.translate(0, thick / 2, 0);
    return new THREE.Mesh(geo, mat);
  }

  // ===========================================================================
  // TIPOLOGÍA 2: EDIFICIO URBANO DE 4 PLANTAS + AZOTEA CAPA A CAPA
  // ===========================================================================
  _buildApartment4FloorsAndFlatRoof(state, rep) {
    const L = state.geometry.lengthM || 12.0;
    const W = state.geometry.widthM || 9.6;
    const floors = 4;
    const floorH = 3.05;
    const totalH = floors * floorH; // 12,2 m
    this.roofSurfaceY = totalH;

    const facadeMat = this._makePBRMat({ color: 0xf1f3f5, textureKey: 'render', roughness: 0.78, normalScale: 0.2 });
    const concreteMat = this._makePBRMat({ color: 0x9ca3af, textureKey: 'concrete', roughness: 0.8 });
    const darkMetalMat = new THREE.MeshStandardMaterial({ color: 0x1c2026, roughness: 0.4, metalness: 0.6 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x2a3e54, roughness: 0.1, metalness: 0.85, transparent: true, opacity: 0.82 });

    // Acera urbana minimalista
    const plaza = new THREE.Mesh(
      new THREE.BoxGeometry(L + 7, 0.12, W + 7),
      this._makePBRMat({ color: 0xdbe0e7, textureKey: 'artificial_stone', roughness: 0.85 })
    );
    plaza.position.set(0, 0.06, 0);
    plaza.receiveShadow = true;
    this.buildingGroup.add(plaza);

    // Cuerpo del edificio de 4 plantas
    const tower = new THREE.Mesh(new THREE.BoxGeometry(L, totalH, W), facadeMat);
    tower.position.set(0, totalH / 2, 0);
    tower.castShadow = true;
    tower.receiveShadow = true;
    this.buildingGroup.add(tower);

    // Bandas de forjado y ventanas por cada una de las 4 plantas
    for (let fl = 0; fl < floors; fl++) {
      const ySlab = (fl + 1) * floorH;
      const slabBand = new THREE.Mesh(new THREE.BoxGeometry(L + 0.18, 0.22, W + 0.18), concreteMat);
      slabBand.position.set(0, ySlab - 0.11, 0);
      this.buildingGroup.add(slabBand);

      const yWin = fl * floorH + 1.55;
      const nW = Math.max(3, Math.floor(L / 2.8));
      for (let i = 0; i < nW; i++) {
        const wx = -L / 2 + (L / (nW + 1)) * (i + 1);
        [W / 2 + 0.02, -W / 2 - 0.02].forEach((wz) => {
          const wf = new THREE.Mesh(new THREE.BoxGeometry(1.75, 1.65, 0.1), darkMetalMat);
          const wg = new THREE.Mesh(new THREE.BoxGeometry(1.62, 1.52, 0.12), glassMat);
          wf.position.set(wx, yWin, wz);
          wg.position.set(wx, yWin, wz);
          this.buildingGroup.add(wf, wg);
        });
      }
      // Fachadas laterales
      [-L / 2 - 0.02, L / 2 + 0.02].forEach((wx) => {
        [-W * 0.24, W * 0.24].forEach((wz) => {
          const wf = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.65, 1.75), darkMetalMat);
          const wg = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.52, 1.62), glassMat);
          wf.position.set(wx, yWin, wz);
          wg.position.set(wx, yWin, wz);
          this.buildingGroup.add(wf, wg);
        });
      });
    }

    // Petos perimetrales (en los 3 lados + peto rebajado en fachada frontal para ver sección de capas)
    const parapetH = state.geometry.parapetHeightM || 1.05;
    const pThick = 0.24;
    const pBack = new THREE.Mesh(new THREE.BoxGeometry(L, parapetH, pThick), concreteMat);
    pBack.position.set(0, totalH + parapetH / 2, -W / 2 + pThick / 2);
    const pLeft = new THREE.Mesh(new THREE.BoxGeometry(pThick, parapetH, W), concreteMat);
    pLeft.position.set(-L / 2 + pThick / 2, totalH + parapetH / 2, 0);
    const pRight = new THREE.Mesh(new THREE.BoxGeometry(pThick, parapetH, W), concreteMat);
    pRight.position.set(L / 2 - pThick / 2, totalH + parapetH / 2, 0);
    // Peto frontal seccionado (más bajo para inspeccionar el paquete de capas al detalle)
    const pFront = new THREE.Mesh(new THREE.BoxGeometry(L, 0.28, pThick), concreteMat);
    pFront.position.set(0, totalH + 0.14, W / 2 - pThick / 2);
    this.buildingGroup.add(pBack, pLeft, pRight, pFront);

    // Casetón de acceso a la azotea en la esquina trasera derecha
    const caseton = new THREE.Mesh(new THREE.BoxGeometry(2.6, 2.55, 2.4), facadeMat);
    caseton.position.set(L / 2 - 1.75, totalH + 1.275, -W / 2 + 1.65);
    caseton.castShadow = true;
    const door = new THREE.Mesh(new THREE.BoxGeometry(0.95, 2.05, 0.08), darkMetalMat);
    door.position.set(L / 2 - 1.75, totalH + 1.025, -W / 2 + 2.86);
    this.buildingGroup.add(caseton, door);

    // =========================================================================
    // CAPAS DE LA AZOTEA SOBRE EL SOPORTE RESISTENTE SUPERIOR
    // =========================================================================
    const innerL = L - pThick * 2 - 0.06;
    const innerW = W - pThick * 2 - 0.06;
    const {
      waterproofing,
      separatorBot,
      insulation,
      plots,
      pavement,
      greenRoof,
      drainUnit,
    } = rep.products;

    let curY = totalH;

    // 1. Formación de pendientes (Hormigón celular)
    const gSlope = this._createLayer('L1_SOPORTE', '1. Formación de Pendientes (Hormigón Celular)', 1, 0.15, null);
    if (state.layersEnabled.support) {
      const slopeMesh = new THREE.Mesh(
        new THREE.BoxGeometry(innerL, 0.08, innerW),
        this._makePBRMat({ color: 0xa8a29e, textureKey: 'cellular_concrete', roughness: 0.88 })
      );
      slopeMesh.position.set(0, curY + 0.04, 0);
      gSlope.add(slopeMesh);
      this._registerInteractive(slopeMesh, {
        pieceCode: 'PENDIENTES-HC',
        layerKey: 'L1_SOPORTE',
        layerName: `Hormigón Celular de Pendientes (${state.geometry.slopePct}%)`,
        productId: waterproofing.id,
        roleLabel: `Formación de pendientes hacia cazoleta (${state.geometry.slopePct}%)`,
        dimensionsMm: `${Math.round(innerL * 1000)} × ${Math.round(innerW * 1000)} × 80 mm`,
        weightKg: Number((innerL * innerW * 48).toFixed(0)),
      });
      curY += 0.08;
    }

    // 2. Cazoleta Sifónica Jimten S-77 (arrastrable con Gizmo)
    const gDrain = this._createLayer('L7_EVACUACION', `Cazoleta Sifónica ${drainUnit.brand}`, 2, 0.25, drainUnit.id);
    const drainX = Math.max(-innerL / 2 + 0.45, Math.min(innerL / 2 - 0.45, state.geometry.drainPosX ?? -innerL * 0.28));
    const drainZ = Math.max(-innerW / 2 + 0.45, Math.min(innerW / 2 - 0.45, state.geometry.drainPosZ ?? -innerW * 0.24));
    if (state.layersEnabled.drainage) {
      const flange = new THREE.Mesh(
        new THREE.BoxGeometry(0.46, 0.02, 0.46),
        this._makePBRMat({ color: 0x1f242b, textureKey: 'bitumen', roughness: 0.7 })
      );
      const grate = new THREE.Mesh(
        new THREE.BoxGeometry(0.26, 0.03, 0.26),
        this._makePBRMat({ color: 0xb8c4d0, textureKey: 'brushed_metal', roughness: 0.3, metalness: 0.85 })
      );
      grate.position.y = 0.02;
      flange.add(grate);
      flange.position.set(drainX, curY + 0.015, drainZ);
      gDrain.add(flange);
      this._registerInteractive(flange, {
        pieceCode: `CAZOLETA-JIMTEN-Ø${drainUnit.geometry.outletDiameterMm}`,
        layerKey: 'L7_EVACUACION',
        layerName: drainUnit.model,
        productId: drainUnit.id,
        roleLabel: `Cazoleta sifónica Ø${drainUnit.geometry.outletDiameterMm} mm (${drainUnit.geometry.hydraulicCapacityLs} L/s)`,
        dimensionsMm: `Rejilla 240×240 mm · Ala ${drainUnit.geometry.flangeWidthMm} mm`,
        weightKg: drainUnit.geometry.unitWeightKg,
      });
    }

    const addWaterproof = (orderIdx, expStep) => {
      const gWp = this._createLayer('L3_IMPERMEABILIZACION', `Impermeabilización ${waterproofing.brand}`, orderIdx, expStep, waterproofing.id);
      if (!state.layersEnabled.waterproofing) return;
      const wpMat = this._makePBRMat({
        color: waterproofing.colorHex || '#23262b',
        textureKey: waterproofing.textureKey || 'bitumen',
        roughness: 0.58,
      });
      const wpMesh = new THREE.Mesh(new THREE.BoxGeometry(innerL, 0.016, innerW), wpMat);
      wpMesh.position.set(0, curY + 0.008, 0);
      gWp.add(wpMesh);

      // Remonte en petos (parapetTurnupMm)
      const turnH = (state.geometry.parapetTurnupMm || 220) / 1000;
      const tBack = new THREE.Mesh(new THREE.BoxGeometry(innerL, turnH, 0.018), wpMat);
      tBack.position.set(0, curY + turnH / 2, -innerW / 2 + 0.009);
      const tLeft = new THREE.Mesh(new THREE.BoxGeometry(0.018, turnH, innerW), wpMat);
      tLeft.position.set(-innerL / 2 + 0.009, curY + turnH / 2, 0);
      const tRight = new THREE.Mesh(new THREE.BoxGeometry(0.018, turnH, innerW), wpMat);
      tRight.position.set(innerL / 2 - 0.009, curY + turnH / 2, 0);
      gWp.add(tBack, tLeft, tRight);

      this._registerInteractive(wpMesh, {
        pieceCode: `MEMBRANA-${waterproofing.manufacturerId}`,
        layerKey: 'L3_IMPERMEABILIZACION',
        layerName: waterproofing.model,
        productId: waterproofing.id,
        roleLabel: `Membrana impermeable + remonte perimetral h=${state.geometry.parapetTurnupMm} mm`,
        dimensionsMm: `e=${waterproofing.geometry.thicknessMm} mm · Solape ${waterproofing.geometry.overlapLongMinMm} mm`,
        weightKg: Number((innerL * innerW * waterproofing.geometry.surfaceWeightKgM2).toFixed(1)),
      });
      curY += 0.02;
    };

    const addGeotextile = (orderIdx, expStep) => {
      const gGeo = this._createLayer('L2_LAMINA', `Geotextil ${separatorBot.brand}`, orderIdx, expStep, separatorBot.id);
      if (!state.layersEnabled.membrane) return;
      const geoMesh = new THREE.Mesh(
        new THREE.BoxGeometry(innerL - 0.02, 0.008, innerW - 0.02),
        this._makePBRMat({ color: 0xe8f1f8, textureKey: 'geotextile', roughness: 0.85 })
      );
      geoMesh.position.set(0, curY + 0.005, 0);
      gGeo.add(geoMesh);
      this._registerInteractive(geoMesh, {
        pieceCode: 'GEOTEXTIL-DANOFELT',
        layerKey: 'L2_LAMINA',
        layerName: separatorBot.model,
        productId: separatorBot.id,
        roleLabel: 'Capa separadora antipunzonante y filtrante (Solape 150 mm)',
        dimensionsMm: `200 g/m² · e=${separatorBot.geometry.thicknessMm} mm`,
        weightKg: Number((innerL * innerW * 0.2).toFixed(1)),
      });
      curY += 0.012;
    };

    const addInsulation = (orderIdx, expStep) => {
      const gIns = this._createLayer('L4_AISLAMIENTO', `Aislamiento ${insulation.brand} (${insulation.geometry.thicknessMm} mm)`, orderIdx, expStep, insulation.id);
      if (!state.layersEnabled.insulation) return;
      const thickM = (insulation.geometry.thicknessMm || 60) / 1000;
      const bL = (insulation.geometry.usefulLengthNominalMm || 1235) / 1000;
      const bW = (insulation.geometry.usefulWidthMm || 585) / 1000;
      const cols = Math.min(12, Math.max(3, Math.floor(innerL / bL)));
      const rows = Math.min(16, Math.max(3, Math.floor(innerW / bW)));
      const cellL = innerL / cols;
      const cellW = innerW / rows;

      const boardGeo = new THREE.BoxGeometry(cellL - 0.014, thickM, cellW - 0.014);
      const boardMat = this._makePBRMat({ color: insulation.colorHex || '#f1df80', textureKey: insulation.textureKey || 'xps_foam', roughness: 0.56 });
      const inst = new THREE.InstancedMesh(boardGeo, boardMat, cols * rows);
      const dummy = new THREE.Object3D();
      let idx = 0;
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          dummy.position.set(-innerL / 2 + (c + 0.5) * cellL, curY + thickM / 2, -innerW / 2 + (r + 0.5) * cellW);
          dummy.updateMatrix();
          inst.setMatrixAt(idx++, dummy.matrix);
        }
      }
      gIns.add(inst);
      this._registerInteractive(inst, {
        pieceCode: `AISLAMIENTO-${insulation.manufacturerId}`,
        layerKey: 'L4_AISLAMIENTO',
        layerName: insulation.model,
        productId: insulation.id,
        roleLabel: `${cols * rows} planchas individuales a matajunta (${insulation.geometry.thicknessMm} mm)`,
        dimensionsMm: `${insulation.geometry.lengthNominalMm} × ${insulation.geometry.widthNominalMm} × ${insulation.geometry.thicknessMm} mm`,
        weightKg: Number((cols * rows * insulation.geometry.unitWeightKg).toFixed(1)),
      });
      curY += thickM + 0.004;
    };

    if (state.variant === 'convencional_fija') {
      addInsulation(3, 0.45);
      addWaterproof(4, 0.78);
      addGeotextile(5, 1.05);
    } else {
      addWaterproof(3, 0.42);
      addGeotextile(4, 0.72);
      addInsulation(5, 1.02);
    }

    // 6. Plots Regulables Peygran XSP5 Pro o Drenaje Ajardinada
    const tileL = (pavement.geometry.lengthNominalMm || 600) / 1000;
    const tileW = (pavement.geometry.widthNominalMm || 600) / 1000;
    const nx = Math.min(20, Math.max(4, Math.floor(innerL / tileL)));
    const nz = Math.min(16, Math.max(4, Math.floor(innerW / tileW)));
    const stepX = innerL / nx;
    const stepZ = innerW / nz;

    const gPlots = this._createLayer(
      'L5_RASTRELES_PLOTS',
      state.variant === 'ajardinada' ? `Drenaje ${greenRoof.brand}` : `Plots ${plots.brand} (H=${plots.geometry.thicknessMm} mm)`,
      6,
      1.38,
      state.variant === 'ajardinada' ? greenRoof.id : plots.id
    );

    if (state.layersEnabled.battens) {
      if (state.variant === 'invertida_plots') {
        const plotH = (plots.geometry.thicknessMm || 95) / 1000;
        const pCount = (nx + 1) * (nz + 1);
        const plotGeo = new THREE.CylinderGeometry(0.08, 0.11, plotH, 12);
        const plotMat = this._makePBRMat({ color: 0x1e242b, textureKey: 'brushed_metal', roughness: 0.45, metalness: 0.25 });
        const headGeo = new THREE.CylinderGeometry(0.085, 0.085, 0.015, 12);
        const headMat = new THREE.MeshStandardMaterial({ color: 0x16a34a, roughness: 0.5 });

        const pInst = new THREE.InstancedMesh(plotGeo, plotMat, pCount);
        const hInst = new THREE.InstancedMesh(headGeo, headMat, pCount);
        const dummy = new THREE.Object3D();
        let idx = 0;
        for (let r = 0; r <= nz; r++) {
          for (let c = 0; c <= nx; c++) {
            const px = -innerL / 2 + c * stepX;
            const pz = -innerW / 2 + r * stepZ;
            dummy.position.set(px, curY + plotH / 2, pz);
            dummy.updateMatrix();
            pInst.setMatrixAt(idx, dummy.matrix);
            dummy.position.set(px, curY + plotH, pz);
            dummy.updateMatrix();
            hInst.setMatrixAt(idx, dummy.matrix);
            idx++;
          }
        }
        gPlots.add(pInst, hInst);
        this._registerInteractive(pInst, {
          pieceCode: `PLOTS-PEYGRAN-${pCount}UDS`,
          layerKey: 'L5_RASTRELES_PLOTS',
          layerName: plots.model,
          productId: plots.id,
          roleLabel: `${pCount} soportes regulables autonivelantes Ø${plots.geometry.baseDiameterMm} mm`,
          dimensionsMm: `H=${plots.geometry.thicknessMm} mm (Rango ${plots.geometry.minHeightMm}–${plots.geometry.maxHeightMm} mm)`,
          weightKg: Number((pCount * plots.geometry.unitWeightKg).toFixed(1)),
        });
        curY += plotH + 0.01;
      } else if (state.variant === 'ajardinada') {
        const fkdMesh = new THREE.Mesh(
          new THREE.BoxGeometry(innerL - 0.04, 0.028, innerW - 0.04),
          this._makePBRMat({ color: 0x1e293b, textureKey: 'bitumen', roughness: 0.65 })
        );
        fkdMesh.position.set(0, curY + 0.014, 0);
        gPlots.add(fkdMesh);
        curY += 0.03;
      }
    }

    // 7. Acabado Superior: Baldosas individuales Gres Aragón Ordesa 20mm o Cubierta Ajardinada Sedum
    const gFinish = this._createLayer(
      'L6_COBERTURA',
      state.variant === 'ajardinada' ? `Sustrato y Sedum ${greenRoof.brand}` : `Pavimento ${pavement.brand}`,
      7,
      1.78,
      state.variant === 'ajardinada' ? greenRoof.id : pavement.id
    );

    if (state.layersEnabled.covering) {
      if (state.variant === 'ajardinada') {
        const subMesh = new THREE.Mesh(
          new THREE.BoxGeometry(innerL - 0.7, 0.09, innerW - 0.7),
          this._makePBRMat({ color: 0x5c4636, textureKey: 'mortar', roughness: 0.94 })
        );
        subMesh.position.set(0, curY + 0.045, 0);
        const sedumMesh = new THREE.Mesh(
          new THREE.BoxGeometry(innerL - 0.72, 0.03, innerW - 0.72),
          this._makePBRMat({ color: 0x3f844c, textureKey: 'geotextile', roughness: 0.88 })
        );
        sedumMesh.position.set(0, curY + 0.105, 0);
        const gravelBorder = new THREE.Mesh(
          new THREE.BoxGeometry(innerL - 0.04, 0.075, innerW - 0.04),
          this._makePBRMat({ color: 0xd1d5db, textureKey: 'concrete_paver', roughness: 0.85 })
        );
        gravelBorder.position.set(0, curY + 0.038, 0);
        gFinish.add(gravelBorder, subMesh, sedumMesh);
        this._registerInteractive(sedumMesh, {
          pieceCode: 'AJARDINADA-OPTIGRUN',
          layerKey: 'L6_COBERTURA',
          layerName: greenRoof.model,
          productId: greenRoof.id,
          roleLabel: 'Sustrato volcánico extensivo + Tapiz vegetal Sedum + franja perimetral grava',
          dimensionsMm: `Espesor total ${greenRoof.geometry.thicknessMm} mm · Retención 40 L/m²`,
          weightKg: Number((innerL * innerW * greenRoof.geometry.surfaceWeightKgM2).toFixed(1)),
        });
      } else {
        const pThick = (pavement.geometry.thicknessMm || 20) / 1000;
        const tileGeo = new THREE.BoxGeometry(stepX - 0.012, pThick, stepZ - 0.012);
        const tileMat = this._makePBRMat({
          color: pavement.colorHex || '#c87358',
          textureKey: pavement.textureKey || 'terracotta',
          roughness: 0.44,
        });
        const inst = new THREE.InstancedMesh(tileGeo, tileMat, nx * nz);
        const dummy = new THREE.Object3D();
        let idx = 0;
        for (let r = 0; r < nz; r++) {
          for (let c = 0; c < nx; c++) {
            dummy.position.set(-innerL / 2 + (c + 0.5) * stepX, curY + pThick / 2, -innerW / 2 + (r + 0.5) * stepZ);
            dummy.updateMatrix();
            inst.setMatrixAt(idx++, dummy.matrix);
          }
        }
        gFinish.add(inst);
        this._registerInteractive(inst, {
          pieceCode: `PAVIMENTO-${pavement.manufacturerId}-${nx}x${nz}`,
          layerKey: 'L6_COBERTURA',
          layerName: pavement.model,
          productId: pavement.id,
          roleLabel: `${nx * nz} baldosas porcelánicas 20 mm (Junta abierta 4 mm)`,
          dimensionsMm: `${pavement.geometry.lengthNominalMm} × ${pavement.geometry.widthNominalMm} × ${pavement.geometry.thicknessMm} mm`,
          weightKg: Number((nx * nz * pavement.geometry.unitWeightKg).toFixed(1)),
        });
      }
    }

    // Gizmo arrastrable para mover la cazoleta sifónica en vivo sobre la azotea
    this._addGizmoHandle(
      'drain_pos',
      new THREE.Vector3(drainX, curY + 0.42, drainZ),
      0x0071e3,
      'horizontal',
      'Arrastrar Cazoleta Sifónica (Posición en Azotea)'
    );
  }

  // ===========================================================================
  // TIPOLOGÍA 3: NAVE INDUSTRIAL / CLUB DEPORTIVO DE GRAN LUZ + CUBIERTA METÁLICA
  // ===========================================================================
  _buildSportsHallAndMetalRoof(state, rep) {
    const L = state.geometry.lengthM || 18.0; // Eje X
    const W = state.geometry.widthM || 12.6;  // Eje Z
    const H = 6.4; // Altura a alero del pabellón/nave
    this.roofSurfaceY = H;

    const steelMat = this._makePBRMat({ color: 0x262d38, textureKey: 'brushed_metal', roughness: 0.36, metalness: 0.78 });
    const concreteBaseMat = this._makePBRMat({ color: 0xd1d6dd, textureKey: 'concrete', roughness: 0.82 });
    const claddingMat = this._makePBRMat({ color: 0xe6eaf0, textureKey: 'zinc_vmz', roughness: 0.42, metalness: 0.45 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x60a5fa, roughness: 0.12, metalness: 0.75, transparent: true, opacity: 0.55 });

    // Solera exterior industrial
    const apron = new THREE.Mesh(
      new THREE.BoxGeometry(L + 8, 0.12, W + 8),
      this._makePBRMat({ color: 0xdde2e8, textureKey: 'concrete_paver', roughness: 0.88 })
    );
    apron.position.set(0, 0.06, 0);
    apron.receiveShadow = true;
    this.buildingGroup.add(apron);

    // Zócalo prefabricado de hormigón (h=2.4 m) + Cerramiento panel arquitectónico + Lucernario corrido
    const wallLower = new THREE.Mesh(new THREE.BoxGeometry(L, 2.5, W), concreteBaseMat);
    wallLower.position.set(0, 1.25, 0);
    wallLower.castShadow = true;
    wallLower.receiveShadow = true;
    this.buildingGroup.add(wallLower);

    const wallMid = new THREE.Mesh(new THREE.BoxGeometry(L - 0.08, 2.4, W - 0.08), claddingMat);
    wallMid.position.set(0, 3.7, 0);
    this.buildingGroup.add(wallMid);

    const clerestoryGlass = new THREE.Mesh(new THREE.BoxGeometry(L - 0.14, 1.35, W - 0.14), glassMat);
    clerestoryGlass.position.set(0, 5.55, 0);
    this.buildingGroup.add(clerestoryGlass);

    // Pórticos estructurales de acero IPE vistos cada 4,5 m
    const numPortals = Math.max(4, Math.floor(L / 4.2) + 1);
    for (let i = 0; i < numPortals; i++) {
      const px = -L / 2 + (L / (numPortals - 1)) * i;
      [-W / 2 - 0.06, W / 2 + 0.06].forEach((pz) => {
        const col = new THREE.Mesh(new THREE.BoxGeometry(0.28, H, 0.28), steelMat);
        col.position.set(px, H / 2, pz);
        col.castShadow = true;
        this.buildingGroup.add(col);
      });
      // Viga horizontal / cordón inferior de cercha
      const tie = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.24, W + 0.2), steelMat);
      tie.position.set(px, H - 0.12, 0);
      this.buildingGroup.add(tie);
    }

    // Cubierta Metálica Capa a Capa según variante (nave_dos_aguas, club_un_agua, diente_sierra)
    const { supportPanel, battenSys, covering, gutter } = rep.products;
    const slopePct = Math.max(5, state.geometry.slopePct || 12);
    const overhang = state.geometry.eaveOverhangM ?? 0.55;
    const totalX = L + overhang * 2;
    const totalZ = W + overhang * 2;

    const gSupport = this._createLayer('L1_SOPORTE', '1. Correas Metálicas Z y Soporte Ventilado', 1, 0.35, supportPanel.id);
    const gMembrane = this._createLayer('L2_LAMINA', '2. Lámina / Esterilla Separadora Ventilada', 2, 0.72, battenSys.id);
    const gBattens = this._createLayer('L5_RASTRELES_PLOTS', '3. Correas / Rastreles de Fijación', 3, 1.08, battenSys.id);
    const gCovering = this._createLayer('L6_COBERTURA', `4. Cobertura Metálica ${covering.brand}`, 4, 1.48, covering.id);
    const gDrainage = this._createLayer('L7_EVACUACION', `5. Canalón Industrial ${gutter.brand} y Remates`, 5, 1.88, gutter.id);

    const covMat = this._makePBRMat({
      color: covering.colorHex || '#7d8892',
      textureKey: covering.textureKey || 'zinc_vmz',
      roughness: 0.34,
      metalness: 0.72,
    });
    const zincMat = this._makePBRMat({ color: 0x94a3b8, textureKey: 'zinc_vmz', roughness: 0.34, metalness: 0.78 });

    const buildMetalSlope = (idPrefix, horizRun, rise, originPos, yawRad) => {
      const angle = Math.atan2(rise, horizRun);
      const rafterLen = Math.hypot(horizRun, rise);

      const makeTilt = (parent) => {
        const pv = new THREE.Group();
        pv.position.copy(originPos);
        pv.rotation.y = yawRad;
        const t = new THREE.Group();
        t.rotation.x = angle;
        pv.add(t);
        parent.add(pv);
        return t;
      };

      if (state.layersEnabled.support) {
        const tSup = makeTilt(gSupport);
        const nPurlins = Math.max(4, Math.floor(rafterLen / 1.4) + 1);
        for (let k = 0; k < nPurlins; k++) {
          const zP = (rafterLen / (nPurlins - 1)) * k;
          const purlin = new THREE.Mesh(new THREE.BoxGeometry(totalX, 0.14, 0.08), steelMat);
          purlin.position.set(0, 0.07, zP);
          tSup.add(purlin);
        }
        const deck = new THREE.Mesh(
          new THREE.BoxGeometry(totalX, 0.04, rafterLen),
          this._makePBRMat({ color: 0xd7b377, textureKey: 'wood_pine', roughness: 0.72 })
        );
        deck.position.set(0, 0.16, rafterLen / 2);
        tSup.add(deck);
        this._registerInteractive(deck, {
          pieceCode: `SOPORTE-METAL-${idPrefix}`,
          layerKey: 'L1_SOPORTE',
          layerName: 'Correas Metálicas Z + Entarimado / Soporte',
          productId: supportPanel.id,
          roleLabel: 'Subestructura de correas metálicas Z y soporte continuo ventilado',
          dimensionsMm: `${Math.round(totalX * 1000)} × ${Math.round(rafterLen * 1000)} mm`,
          weightKg: Number((totalX * rafterLen * 16).toFixed(1)),
        });
      }

      if (state.layersEnabled.membrane) {
        const tMem = makeTilt(gMembrane);
        const mem = new THREE.Mesh(
          new THREE.BoxGeometry(totalX, 0.01, rafterLen),
          this._makePBRMat({ color: 0x1e293b, textureKey: 'geotextile', roughness: 0.8 })
        );
        mem.position.set(0, 0.19, rafterLen / 2);
        tMem.add(mem);
      }

      if (state.layersEnabled.covering) {
        const tCov = makeTilt(gCovering);
        this._populateSlopeCoveringPieces(tCov, {
          idPrefix,
          widthAlongEave: totalX,
          rafterLen,
          covY: 0.22,
          covering,
          covMat,
          rep,
          isHipTrapezoid: false,
          hipSideInsetTop: 0,
        });
      }

      if (state.layersEnabled.drainage) {
        const tDr = makeTilt(gDrainage);
        const rGut = 0.095;
        const gutGeo = new THREE.CylinderGeometry(rGut, rGut, totalX + 0.16, 16, 1, true, 0, Math.PI);
        gutGeo.rotateZ(-Math.PI / 2);
        const gut = new THREE.Mesh(gutGeo, zincMat);
        gut.position.set(0, 0.18, rafterLen + rGut + 0.02);
        tDr.add(gut);
        this._registerInteractive(gut, {
          pieceCode: `CANALON-IND-${idPrefix}`,
          layerKey: 'L7_EVACUACION',
          layerName: gutter.model,
          productId: gutter.id,
          roleLabel: 'Canalón pluvial perimetral de gran caudal en zinc-titanio',
          dimensionsMm: `L=${Math.round(totalX * 1000)} mm · Ø${gutter.geometry.widthNominalMm} mm`,
          weightKg: Number(((totalX / 4) * gutter.geometry.unitWeightKg).toFixed(1)),
        });
      }
    };

    let topGizmoY = H + 1.2;
    if (state.variant === 'club_un_agua') {
      const rise = totalZ * (slopePct / 100);
      topGizmoY = H + rise;
      buildMetalSlope('PABELLON-UN-AGUA', totalZ, rise, new THREE.Vector3(0, H + rise, -totalZ / 2), 0);
    } else if (state.variant === 'diente_sierra') {
      const bays = 3;
      const bayZ = totalZ / bays;
      const bayRise = bayZ * Math.max(0.22, slopePct / 100);
      topGizmoY = H + bayRise;
      for (let b = 0; b < bays; b++) {
        const zStart = -totalZ / 2 + b * bayZ;
        buildMetalSlope(`SHED-0${b + 1}`, bayZ, bayRise, new THREE.Vector3(0, H + bayRise, zStart), 0);
        // Paño vertical acristalado de diente de sierra orientado a norte
        const shedGlass = new THREE.Mesh(new THREE.BoxGeometry(totalX - 0.1, bayRise, 0.06), glassMat);
        shedGlass.position.set(0, H + bayRise / 2, zStart);
        this.buildingGroup.add(shedGlass);
      }
    } else {
      const halfZ = totalZ / 2;
      const rise = halfZ * (slopePct / 100);
      topGizmoY = H + rise;
      buildMetalSlope('NAVE-SUR', halfZ, rise, new THREE.Vector3(0, H + rise, 0), 0);
      buildMetalSlope('NAVE-NORTE', halfZ, rise, new THREE.Vector3(0, H + rise, 0), Math.PI);
    }

    this._addGizmoHandle(
      'ridge_height',
      new THREE.Vector3(0, topGizmoY + 0.55, 0),
      0x0071e3,
      'vertical_ridge',
      'Arrastrar Cumbrera Metálica (Pendiente)'
    );
  }

  // ===========================================================================
  // LÍNEAS CAD DIBUJADAS POR EL USUARIO (CUMBRERA, LIMATESA, LIMAHOYA, CONTORNO)
  // ===========================================================================
  _renderUserCadLines(cadLines) {
    const styleMap = {
      cumbrera: { color: 0xef4444, label: 'Cumbrera CAD' },
      limatesa: { color: 0x0071e3, label: 'Limatesa CAD' },
      limahoya: { color: 0x06b6d4, label: 'Limahoya CAD' },
      contorno: { color: 0x111827, label: 'Línea de Contorno CAD' },
    };

    cadLines.forEach((ln) => {
      const st = styleMap[ln.type] || styleMap.contorno;
      const p1 = new THREE.Vector3(ln.p1.x, ln.p1.y + 0.12, ln.p1.z);
      const p2 = new THREE.Vector3(ln.p2.x, ln.p2.y + 0.12, ln.p2.z);
      const dist = p1.distanceTo(p2);
      if (dist < 0.05) return;

      const tubeGeo = new THREE.CylinderGeometry(0.045, 0.045, dist, 10);
      const tubeMat = new THREE.MeshStandardMaterial({
        color: st.color,
        emissive: st.color,
        emissiveIntensity: 0.3,
        roughness: 0.3,
      });
      const mesh = new THREE.Mesh(tubeGeo, tubeMat);
      const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
      mesh.position.copy(mid);
      mesh.quaternion.setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        new THREE.Vector3().subVectors(p2, p1).normalize()
      );
      this.cadOverlayGroup.add(mesh);

      this._registerInteractive(
        mesh,
        {
          id: ln.id,
          pieceCode: ln.id,
          isCadLine: true,
          layerKey: 'CAD_LINES',
          layerName: `${st.label} (${ln.id})`,
          roleLabel: `Trazado CAD interactivo · Longitud real = ${dist.toFixed(2)} m`,
          dimensionsMm: `L = ${Math.round(dist * 1000)} mm · De (${ln.p1.x}, ${ln.p1.z}) a (${ln.p2.x}, ${ln.p2.z})`,
          weightKg: 0,
        },
        false
      );
    });
  }

  // ===========================================================================
  // CONTROLES DE CÁMARA, DESPIECE, SECUENCIA Y CAPTURA HD / VÍDEO WEBM
  // ===========================================================================
  setExplodeFactor(factor) {
    this.explodeFactor = Math.max(0, Math.min(1, Number(factor) || 0));
    this._applyExplodeFactor();
  }

  _applyExplodeFactor() {
    this.layerGroups.forEach((g) => {
      const step = g.userData.explodeStep || 0.4;
      g.position.y = this.explodeFactor * step * 1.45;
    });
  }

  setAssemblyProgress(progress0to1) {
    this.assemblyProgress = Math.max(0, Math.min(1, Number(progress0to1)));
    this._applyAssemblyProgress();
  }

  toggleSequencePlay() {
    if (this.isPlayingSequence) {
      this.isPlayingSequence = false;
    } else {
      if (this.assemblyProgress >= 0.99) this.assemblyProgress = 0.02;
      this.isPlayingSequence = true;
    }
    return this.isPlayingSequence;
  }

  _applyAssemblyProgress() {
    const total = this.orderedSequenceEntries.length;
    if (total === 0) return;
    const cutoff = Math.ceil(this.assemblyProgress * total);
    for (let i = 0; i < total; i++) {
      this.orderedSequenceEntries[i].mesh.visible = i < cutoff;
    }
  }

  setCameraPreset(preset) {
    if (!this.camera || !this.controls) return;
    const yFocus =
      this.currentState?.typology === 'azotea'
        ? this.roofSurfaceY + 0.5
        : this.currentState?.typology === 'metalica'
        ? this.roofSurfaceY + 0.2
        : this.roofSurfaceY + 0.6;
    const dist =
      this.currentState?.typology === 'metalica'
        ? 23.0
        : this.currentState?.typology === 'azotea'
        ? 17.5
        : 15.0;

    this.controls.target.set(0, yFocus, 0);
    if (preset === 'top') {
      this.camera.position.set(0.01, yFocus + dist * 1.15, 0.01);
    } else if (preset === 'front') {
      this.camera.position.set(0, yFocus + 2.2, dist * 1.05);
    } else if (preset === 'side') {
      this.camera.position.set(dist * 1.05, yFocus + 2.2, 0);
    } else if (preset === 'roof_close') {
      this.camera.position.set(dist * 0.48, yFocus + dist * 0.34, dist * 0.52);
    } else {
      // Vista isométrica arquitectónica perfecta
      this.camera.position.set(dist * 0.78, yFocus + dist * 0.52, dist * 0.85);
    }
    this.controls.update();
  }

  captureHighResPNG() {
    this.renderer.render(this.scene, this.camera);
    return this.canvas.toDataURL('image/png');
  }

  /**
   * Graba en vivo un vídeo WebM real de la secuencia de montaje capa a capa desde el visor 3D.
   */
  recordSequenceVideo(durationMs = 6500, onProgress = () => {}) {
    return new Promise((resolve, reject) => {
      if (typeof MediaRecorder === 'undefined' || !this.canvas.captureStream) {
        reject(new Error('Tu navegador no soporta grabación directa de vídeo WebM.'));
        return;
      }
      const stream = this.canvas.captureStream(30);
      const chunks = [];
      const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) chunks.push(ev.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' });
        resolve(URL.createObjectURL(blob));
      };

      this.isPlayingSequence = false;
      this.setAssemblyProgress(0.02);
      recorder.start();

      const t0 = performance.now();
      const stepFrame = () => {
        const elapsed = performance.now() - t0;
        const p = Math.min(1.0, elapsed / durationMs);
        this.setAssemblyProgress(p);
        onProgress(p);
        if (p < 1.0) {
          requestAnimationFrame(stepFrame);
        } else {
          setTimeout(() => recorder.stop(), 350);
        }
      };
      requestAnimationFrame(stepFrame);
    });
  }
}
