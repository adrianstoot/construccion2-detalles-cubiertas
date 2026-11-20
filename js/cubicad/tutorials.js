/**
 * =============================================================================
 * CubiCAD · Constructor CAD/BIM de Cubiertas
 * Motor de Tutorial Interactivo Guiado de Primer Uso (3 Tipologías desde Cero)
 * =============================================================================
 * Guía paso a paso al estudiante para:
 * 1. Montar desde cero un Tejado Inclinado (Vivienda 2 plantas)
 * 2. Montar desde cero una Azotea Invertida sobre Plots (Edificio 4 plantas)
 * 3. Montar desde cero una Cubierta Metálica de Gran Luz (Pabellón / Nave)
 * Incluyendo al final de cada recorrido cómo abrir el Detalle 2D Vivo y
 * cómo generar la Secuencia Animada de Montaje / Render HD.
 */

export const CUBICAD_TUTORIALS = {
  tut_tejado: {
    id: 'tut_tejado',
    typology: 'tejado',
    badge: 'TUTORIAL 01 · TEJADO INCLINADO',
    title: 'Construir un Tejado de Teja Curva desde cero',
    subtitle: 'Vivienda aislada 2 plantas · Thermochip + Rothoblaas + Tejas Borja + VMZINC + Detalle 2D + Secuencia',
    steps: [
      {
        title: '1. Edificio Base: Vivienda de 2 Plantas sin cubierta',
        instruction:
          'Partimos de la vivienda aislada de 2 plantas limpia sobre su forjado superior. Vamos a elegir la variante geométrica (Dos Aguas, Cuatro Aguas o Planta en L) y montar el tejado capa a capa.',
        highlightSelector: '#tool-layer-building',
        actionLabel: 'Preparar vivienda vacía (Dos Aguas)',
        execute: (app) => {
          app.stateManager.switchTypology('tejado', true);
          app.setMainTab('builder');
          app.builder3D.setCameraPreset('iso');
        },
      },
      {
        title: '2. Colocar Soporte Estructural y Aislamiento (Thermochip TAH)',
        instruction:
          'Pulsa en el botón "Soporte" de la paleta izquierda para colocar los pares estructurales y los paneles sándwich Thermochip TAH con núcleo XPS.',
        highlightSelector: '#tool-layer-support',
        actionLabel: 'Montar Soporte Thermochip TAH',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.support = true;
            st.layersEnabled.insulation = true;
            st.products.supportPanelId = 'THERMOCHIP-TAH-80';
          }, 'Tutorial: Montar Soporte');
        },
      },
      {
        title: '3. Extender Lámina Transpirable y Doble Rastrel (Rothoblaas)',
        instruction:
          'Añadimos la lámina impermeable transpirable TRASPIR EVO (Sd = 0,04 m) y el doble rastrelado ventilado 30×50 mm al paso oficial exacto de la teja.',
        highlightSelector: '#tool-layer-battens',
        actionLabel: 'Montar Lámina + Doble Rastrel',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.membrane = true;
            st.layersEnabled.battens = true;
            st.products.battenSystemId = 'ROTHOBLAAS-RASTREL-3050';
          }, 'Tutorial: Montar Rastreles');
        },
      },
      {
        title: '4. Colocar Cobertura Pieza a Pieza (Tejas Borja C-50.21) y Canalón',
        instruction:
          'Desde el botón "Cobertura / Teja" elegimos Teja Curva Árabe (canales y cobijas reales con solape 120 mm) y cerramos con cumbrera ventilada y canalón semicircular VMZINC D333.',
        highlightSelector: '#tool-layer-covering',
        actionLabel: 'Colocar Teja Curva + Canalón VMZINC',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.covering = true;
            st.layersEnabled.drainage = true;
            st.products.coveringId = 'BORJA-C5021';
            st.products.gutterId = 'VMZINC-CANALON-333';
          }, 'Tutorial: Colocar Tejas Borja');
        },
      },
      {
        title: '5. Ver el Detalle Constructivo 2D Acotado en Vivo',
        instruction:
          'Pulsa "Detalle 2D Vivo" (tecla 2) para ver al instante la sección constructiva 2D acotada en milímetros con los espesores reales y las referencias de cada fabricante.',
        highlightSelector: '#tool-cad-detail2d',
        actionLabel: 'Abrir Detalle 2D Instantáneo',
        execute: (app) => {
          app.toggleLiveDetail2DPanel(true);
        },
      },
      {
        title: '6. Generar Secuencia Animada de Montaje y Render HD',
        instruction:
          'Por último, abre la pestaña "Render y Secuencia" para reproducir la secuencia de montaje capa a capa de tu tejado, capturar un render PNG en alta resolución o grabar un vídeo WebM.',
        highlightSelector: '[data-maintab="render"]',
        actionLabel: 'Ir a Render y Reproducir Secuencia',
        execute: (app) => {
          app.toggleLiveDetail2DPanel(false);
          app.setMainTab('render');
          app.startLiveSequencePlayback();
        },
      },
    ],
  },

  tut_azotea: {
    id: 'tut_azotea',
    typology: 'azotea',
    badge: 'TUTORIAL 02 · AZOTEA PLANA',
    title: 'Construir una Azotea Invertida sobre Plots desde cero',
    subtitle: 'Edificio urbano 4 plantas · DANOSA + URSA XPS + Peygran XSP5 + Gres Aragón + Hydro 3D',
    steps: [
      {
        title: '1. Edificio Urbano de 4 Plantas: Soporte Superior y Peto',
        instruction:
          'Cambiamos al edificio urbano de 4 plantas y trabajamos en su planta cubierta sobre el forjado superior y el peto perimetral de hormigón.',
        highlightSelector: '[data-typology="azotea"]',
        actionLabel: 'Preparar Edificio 4 Plantas vacío',
        execute: (app) => {
          app.stateManager.switchTypology('azotea', true);
          app.setMainTab('builder');
          app.builder3D.setCameraPreset('roof_close');
        },
      },
      {
        title: '2. Formación de Pendientes y Cazoleta Sifónica (Jimten S-77)',
        instruction:
          'Colocamos el hormigón celular de pendientes (2%) y la cazoleta sifónica registrable Jimten S-77 Ø110 mm a más de 50 cm del peto (CTE DB-HS 1).',
        highlightSelector: '#tool-layer-drainage',
        actionLabel: 'Montar Pendientes + Cazoleta Jimten',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.support = true;
            st.layersEnabled.drainage = true;
            st.products.drainUnitId = 'JIMTEN-S77-110';
          }, 'Tutorial: Pendientes y Cazoleta');
        },
      },
      {
        title: '3. Impermeabilización con Remonte 22 cm y Geotextil (DANOSA)',
        instruction:
          'Aplicamos la membrana bituminosa SBS DANOSA ESTERDAN 40 P ELAST remontando 220 mm en petos (≥200 mm CTE) y extendemos el geotextil separador DANOFELT PY 200.',
        highlightSelector: '#tool-layer-waterproofing',
        actionLabel: 'Montar DANOSA ESTERDAN + Geotextil',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.waterproofing = true;
            st.layersEnabled.membrane = true;
            st.products.waterproofingId = 'DANOSA-ESTERDAN40P';
            st.products.separatorBotId = 'DANOSA-DANOFELT-PY200';
          }, 'Tutorial: Impermeabilización DANOSA');
        },
      },
      {
        title: '4. Aislamiento Invertido (URSA XPS) + Plots (Peygran) + Baldosas (Gres Aragón)',
        instruction:
          'Colocamos las planchas a media madera URSA XPS N-III-L (300 kPa), la retícula de soportes autonivelantes Peygran XSP5 Pro y el pavimento porcelánico Gres Aragón 20mm con junta abierta de 4 mm.',
        highlightSelector: '#tool-layer-covering',
        actionLabel: 'Montar XPS + Plots + Pavimento 20mm',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.insulation = true;
            st.layersEnabled.battens = true;
            st.layersEnabled.covering = true;
            st.products.insulationId = 'URSA-XPS-NIIIL-60';
            st.products.plotsId = 'PEYGRAN-XSP5-PRO';
            st.products.pavementId = 'GRESARAGON-ORDESA-6060';
          }, 'Tutorial: Paquete Invertido Plots');
        },
      },
      {
        title: '5. Levantar Capas Instantáneamente y Comprobar Detalle 2D Vivo',
        instruction:
          'Elevamos el despiece vertical de capas y abrimos el Detalle 2D Vivo para verificar el remonte perimetral de 220 mm y el espesor total del paquete constructivo.',
        highlightSelector: '#tool-cad-explode',
        actionLabel: 'Levantar Capas + Abrir Detalle 2D',
        execute: (app) => {
          app.setExplodeUI(55);
          app.toggleLiveDetail2DPanel(true);
        },
      },
      {
        title: '6. Probar Escorrentía Real en Simulador de Agua o Generar Secuencia',
        instruction:
          'Ahora puedes abrir la pestaña "Simulador Agua" (sincronizado automáticamente con tus productos Gres Aragón + Peygran + Jimten) o generar tu secuencia de montaje en "Render y Secuencia".',
        highlightSelector: '[data-maintab="hydro"]',
        actionLabel: 'Abrir Simulador de Agua (Sincronizado)',
        execute: (app) => {
          app.setExplodeUI(0);
          app.toggleLiveDetail2DPanel(false);
          app.setMainTab('hydro');
        },
      },
    ],
  },

  tut_metalica: {
    id: 'tut_metalica',
    typology: 'metalica',
    badge: 'TUTORIAL 03 · CUBIERTA METÁLICA',
    title: 'Construir una Cubierta Metálica de Pabellón Deportivo desde cero',
    subtitle: 'Nave / Club Deportivo de gran luz · Pórticos + VMZINC Junta Alzada / Kingspan + Secuencia',
    steps: [
      {
        title: '1. Edificio Base: Pabellón Deportivo / Nave de Gran Luz',
        instruction:
          'Activamos el modo Cubierta Metálica sobre una nave/pabellón con pórticos estructurales de acero IPE vistos y lucernarios corridos, listo para recibir la cubierta.',
        highlightSelector: '[data-typology="metalica"]',
        actionLabel: 'Preparar Pabellón Deportivo vacío',
        execute: (app) => {
          app.stateManager.switchTypology('metalica', true);
          app.setMainTab('builder');
          app.builder3D.setCameraPreset('iso');
        },
      },
      {
        title: '2. Colocar Correas Metálicas Z, Soporte Ventilado y Lámina',
        instruction:
          'Montamos las correas metálicas Z sobre los pórticos, el entarimado continuo ventilado y la membrana/esterilla separadora.',
        highlightSelector: '#tool-layer-support',
        actionLabel: 'Montar Correas Z + Soporte + Lámina',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.support = true;
            st.layersEnabled.membrane = true;
            st.layersEnabled.insulation = true;
            st.layersEnabled.battens = true;
          }, 'Tutorial: Correas y Soporte Metálico');
        },
      },
      {
        title: '3. Instalar Bandejas VMZINC Junta Alzada (o Panel Kingspan) y Canalón',
        instruction:
          'Colocamos las bandejas continuas QUARTZ-ZINC engatilladas en doble junta alzada H=25 mm con patas fijas/correderas inoxidables y canalón industrial de gran caudal.',
        highlightSelector: '#tool-layer-covering',
        actionLabel: 'Instalar VMZINC Junta Alzada + Canalón',
        execute: (app) => {
          app.stateManager.commit((st) => {
            st.layersEnabled.covering = true;
            st.layersEnabled.drainage = true;
            st.products.coveringId = 'VMZINC-JUNTA-ALZADA-500';
            st.products.fastenerId = 'VMZINC-PATAS-INOX';
            st.products.gutterId = 'VMZINC-CANALON-333';
          }, 'Tutorial: Bandejas VMZINC');
        },
      },
      {
        title: '4. Detalle 2D Vivo y Generación de Secuencia de Montaje',
        instruction:
          'Comprobamos la sección constructiva 2D instantánea y pasamos a "Render y Secuencia" para animar el montaje desde pórticos hasta el acabado metálico.',
        highlightSelector: '[data-maintab="render"]',
        actionLabel: 'Ver Detalle 2D y Generar Secuencia',
        execute: (app) => {
          app.toggleLiveDetail2DPanel(true);
          setTimeout(() => {
            app.toggleLiveDetail2DPanel(false);
            app.setMainTab('render');
            app.startLiveSequencePlayback();
          }, 900);
        },
      },
    ],
  },
};
