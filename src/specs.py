"""
Single Source of Truth — Millimetric Engineering Specifications (units: mm)
Construccion II (UPV - ETSIE) · Tejados y Azoteas:
  1. Detalle 1: Cartillas IVE — Azotea Transitable, No Ventilada, Convencional, Pavimento Fijo (Peto)
  2A. Detalle 2A: NTE QAT-16 — Encuentro con Cazoleta
  2B. Detalle 2B: NTE QAT-17 — Canalon en Faldon de Hormigon Aligerado-S
  3. Detalle 3: Analisis Detalle — Azotea Transitable con Hormigon Celular · Cazoleta Sifonica
"""

import json
import os


DETAILS = {
    "detalle1": {
        "id": "detalle1",
        "category": "azoteas",
        "category_label": "Azoteas Planas",
        "code": "DET-01 · IVE TIPOLOGÍA 1",
        "slide": "Diapositiva 1 · Pág. 20 (Análisis Cartillas IVE)",
        "title": "Azotea Transitable · No Ventilada · Convencional · Pavimento Fijo",
        "subtitle": "Encuentro con peto de fábrica y secuencia escalonada de capas (P, CS, I, AT, BV, FP, SR)",
        "scale_2d": "1:5",
        "normativa": "Cartillas IVE · CTE DB-HS1 / DB-HE1",
        "bounds_mm": {"x_min": 0.0, "x_max": 1175.0, "y_min": 0.0, "y_max": 960.0, "z_min": -260.0, "z_max": 820.0},
        "params": {
            "deck_end_x": 985.0,
            "junta_eps_w": 15.0,          # X: 985..1000
            "enfoscado_int_w": 15.0,      # X: 1000..1015
            "peto_brick_w": 140.0,        # X: 1015..1155 (LHD 140 mm con huecos visibles)
            "enfoscado_ext_w": 20.0,      # X: 1155..1175
            "peto_top_z": 820.0,
            "forjado_h": 260.0,           # 210 bovedilla/vigueta + 50 capa compresion
            "compresion_h": 50.0,
            "vigueta_spacing": 600.0,
            "slope": 0.025,               # 2.5% hacia X=0
            "fp_min_h": 55.0,             # en X=0 (hormigon aligerado arlita)
            "fp_reg_h": 15.0,             # mortero de regularizacion sobre FP
            "bv_h": 3.0,                  # Barrera de vapor
            "at_h": 50.0,                 # Aislamiento termico XPS
            "i_h": 4.0,                   # Impermeabilizacion + entrega vertical 200 mm
            "i_turnup_h": 200.0,
            "cs_h": 2.0,                  # Capa separadora geotextil
            "mortero_agarre_h": 20.0,     # Mortero de agarre para pavimento P
            "tile_h": 20.0,               # Pavimento P (baldosa / rasilla 280x140x20)
            "tile_l": 280.0,
            "tile_w": 140.0,
            "tile_joint": 6.0,
            "rodapie_h": 200.0,
            "rodapie_t": 15.0,
            "junta_perimetral": 10.0,
            # Offsets del despiece escalonado 3D (X de inicio para vista Cartillas IVE)
            "steps_x": {
                "SR": 0.0,
                "FP": 85.0,
                "BV": 175.0,
                "AT": 265.0,
                "I": 355.0,
                "CS": 445.0,
                "P_MORTERO": 525.0,
                "P": 575.0,
            },
        },
        "layers": [
            {
                "code": "P",
                "name": "Pavimento Fijo (Baldosa / Rasilla + Rodapié)",
                "thickness_mm": "20 mm + 20 mm agarre",
                "spec": "Baldosa cerámica extrusionada 280×140×20 mm colocada a matajunta con junta abierta de 6 mm sobre capa de mortero de agarre 1:6 de 20 mm. Rodapié cerámico vertical de 200×15 mm con junta perimetral elástica de 10 mm.",
                "color": "#C45B42",
                "mesh_keys": ["P_Tiles", "P_Mortar", "P_Rodapie", "P_Joint"],
                "explode_z": 240.0,
            },
            {
                "code": "CS",
                "name": "Capa Separadora Geotextil",
                "thickness_mm": "2 mm",
                "spec": "Lámina separadora de fieltro geotextil no tejido de polipropileno (150 g/m²) que independiza el pavimento y su mortero de agarre respecto a la impermeabilización.",
                "color": "#D7EBF5",
                "mesh_keys": ["CS_Geotextile"],
                "explode_z": 195.0,
            },
            {
                "code": "I",
                "name": "Membrana Impermeabilizante",
                "thickness_mm": "4 mm",
                "spec": "Lámina bituminosa modificada con elastómeros SBS (LBM-40-FP) totalmente adherida, con entrega vertical de 200 mm sobre el enfoscado del peto rematada bajo el rodapié.",
                "color": "#383B40",
                "mesh_keys": ["I_Membrane"],
                "explode_z": 150.0,
            },
            {
                "code": "AT",
                "name": "Aislamiento Térmico (XPS)",
                "thickness_mm": "50 mm",
                "spec": "Plancha rígida de poliestireno extruido (XPS) de alta resistencia a compresión (300 kPa), junta a media madera y conductividad λ = 0,034 W/m·K.",
                "color": "#F3E48C",
                "mesh_keys": ["AT_XPS"],
                "explode_z": 105.0,
            },
            {
                "code": "BV",
                "name": "Barrera de Vapor",
                "thickness_mm": "3 mm",
                "spec": "Lámina bituminosa oxiasfáltica o film barrera de vapor dispuesto sobre la formación de pendiente y bajo el aislamiento térmico para evitar condensaciones intersticiales.",
                "color": "#2E3034",
                "mesh_keys": ["BV_VaporBarrier"],
                "explode_z": 65.0,
            },
            {
                "code": "FP",
                "name": "Formación de Pendiente (2,5%)",
                "thickness_mm": "55–80 mm + 15 mm reg.",
                "spec": "Hormigón aligerado con arcilla expandida (arlita) vertido in situ con pendiente del 2,5%, coronado por capa de regularización de mortero de cemento 1:6 de 15 mm.",
                "color": "#9E7E63",
                "mesh_keys": ["FP_Concrete", "FP_Regularization"],
                "explode_z": 30.0,
            },
            {
                "code": "SR",
                "name": "Soporte Resistente (Forjado Unidireccional)",
                "thickness_mm": "260 mm (21+5)",
                "spec": "Forjado unidireccional de viguetas pretensadas cada 600 mm, bovedillas cerámicas aligerantes y capa de compresión de hormigón armado HA-25 de 50 mm con mallazo.",
                "color": "#CFD3D6",
                "mesh_keys": ["SR_Slab", "SR_Viguetas", "SR_Bovedillas"],
                "explode_z": 0.0,
            },
            {
                "code": "PETO",
                "name": "Peto de Fábrica + Junta Perimetral EPS",
                "thickness_mm": "175 mm + 15 mm EPS",
                "spec": "Fábrica de ladrillo hueco doble (140 mm) enfoscada interior (15 mm) y exteriormente (20 mm), con banda desolidarizadora de EPS de 15 mm entre las capas de cubierta y el peto.",
                "color": "#DFC5A4",
                "mesh_keys": ["Peto_Bricks", "Peto_Render", "Peto_JuntaEPS"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle2_qat16": {
        "id": "detalle2_qat16",
        "category": "azoteas",
        "category_label": "Azoteas Planas",
        "code": "DET-02A · NTE QAT-16",
        "slide": "Diapositiva 2 · Pág. 19 (Análisis NTE · QAT-16)",
        "title": "QAT-16 · Encuentro con Cazoleta",
        "subtitle": "Caja de ladrillo hueco sencillo (PTL-7), membrana penetrando a bajante y solape de 10 cm (QAT-10)",
        "scale_2d": "1:5",
        "normativa": "NTE-QAT (QAT-16 · QAT-10 · PTL-7)",
        "bounds_mm": {"x_min": -320.0, "x_max": 860.0, "y_min": -360.0, "y_max": 360.0, "z_min": -250.0, "z_max": 260.0},
        "params": {
            "forjado_h": 250.0,
            "pit_inner_half": 110.0,      # 220x220 mm luz interior caja
            "ptl7_wall_t": 50.0,          # Ladrillo hueco sencillo 40 mm + 10 mm mortero 1:6 -> X: +-110..+-160
            "ptl7_h": 120.0,              # Z: 0..120
            "slope": 0.05,                # 5% pendiente en faldon derecho (X > 160)
            "faldon_min_h": 120.0,        # en X=160
            "reg_mortar_h": 15.0,
            "mem_inf_h": 4.0,             # QAT-10 inferior penetrando en bajante
            "mem_sup_h": 4.0,             # QAT-10 superior con solape >= 100 mm
            "solape_mm": 100.0,           # 10 cm reglamentarios
            "agarre_h": 15.0,
            "rasilla_h": 20.0,
            "rasilla_l": 280.0,
            "rasilla_joint": 6.0,
            "bajante_od": 110.0,
            "bajante_wall": 3.2,
            "cazoleta_outer_half": 102.0, # 204x204 mm cuerpo cazoleta
            "cazoleta_flange_w": 36.0,    # ala perimetral apoyada en caja PTL-7
            "cazoleta_depth": 105.0,
            "grate_h": 10.0,
        },
        "layers": [
            {
                "code": "PAV",
                "name": "Pavimento de Rasilla Cerámica + Mortero",
                "thickness_mm": "20 mm + 15 mm agarre",
                "spec": "Rasilla cerámica extrusionada sobre mortero de agarre de cemento y arena de río, rematada con vuelo goterón de 15 mm junto al perímetro de la rejilla.",
                "color": "#C25940",
                "mesh_keys": ["Q16_Rasilla", "Q16_Agarre"],
                "explode_z": 180.0,
            },
            {
                "code": "QAT-10",
                "name": "Membrana Impermeabilizante + Solape 10 cm",
                "thickness_mm": "4 mm + solape 100 mm",
                "spec": "QAT-10: La parte inferior de la membrana llegará hasta la bajante penetrando en ella. Una vez recibida la cazoleta se ejecutará el resto de la membrana con un solape de 10 cm sobre ella.",
                "color": "#26282B",
                "mesh_keys": ["Q16_MembraneSup", "Q16_MembraneInf"],
                "explode_z": 135.0,
            },
            {
                "code": "CAZ",
                "name": "Cazoleta Metálica con Rejilla y Vierteaguas",
                "thickness_mm": "204×204 mm / ala 36 mm",
                "spec": "Cazoleta prefabricada metálica/cinc con ala perimetral recibida entre ambas hojas de membrana, rejilla superior ranurada de desagüe y babero vierteaguas lateral.",
                "color": "#8E969E",
                "mesh_keys": ["Q16_Cazoleta", "Q16_Rejilla", "Q16_Flashing"],
                "explode_z": 95.0,
            },
            {
                "code": "REG",
                "name": "Mortero de Regularización (1:6)",
                "thickness_mm": "15 mm",
                "spec": "Capa de mortero de cemento y arena 1:6 sobre faldón aligerado para asiento uniforme de la impermeabilización.",
                "color": "#B3AAA0",
                "mesh_keys": ["Q16_RegMortar"],
                "explode_z": 60.0,
            },
            {
                "code": "PTL-7",
                "name": "Caja PTL-7 de Ladrillo Hueco Sencillo",
                "thickness_mm": "50 mm (LHS 40 mm + 1:6)",
                "spec": "PTL-7: Caja para recibir la cazoleta formada por tabique de ladrillo hueco sencillo recibido con mortero de cemento y arena de río, de dosificación 1:6.",
                "color": "#CC6D4A",
                "mesh_keys": ["Q16_PTL7_Bricks", "Q16_PTL7_Mortar"],
                "explode_z": 30.0,
            },
            {
                "code": "FAL",
                "name": "Faldón de Hormigón Aligerado (5%)",
                "thickness_mm": "120–155 mm",
                "spec": "Formación de pendiente con hormigón aligerado al 5% apoyada directamente sobre el forjado estructural.",
                "color": "#A7A299",
                "mesh_keys": ["Q16_HormigonAlig"],
                "explode_z": 25.0,
            },
            {
                "code": "FORJ",
                "name": "Forjado + Bajante PVC Ø110",
                "thickness_mm": "250 mm / Ø110 mm",
                "spec": "Forjado estructural horizontal perforado para paso de la bajante de PVC Ø110 mm con copa superior para acople estanco de la cazoleta.",
                "color": "#CACFD2",
                "mesh_keys": ["Q16_Forjado", "Q16_Bajante"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle2_qat17": {
        "id": "detalle2_qat17",
        "category": "azoteas",
        "category_label": "Azoteas Planas",
        "code": "DET-02B · NTE QAT-17",
        "slide": "Diapositiva 2 · Pág. 19 (Análisis NTE · QAT-17)",
        "title": "QAT-17 · Canalón en Faldón de Hormigón Aligerado-S",
        "subtitle": "Roza PTL-2 (5×5 cm), canalón de cinc QAT-2 (35 cm), maestra PTL-7 y mortero RPE-3",
        "scale_2d": "1:5",
        "normativa": "NTE-QAT (QAT-17 · QAT-2 · PTL-2 · PTL-7 · RPE-3)",
        "bounds_mm": {"x_min": -240.0, "x_max": 950.0, "y_min": -380.0, "y_max": 380.0, "z_min": -250.0, "z_max": 640.0},
        "params": {
            "wall_t": 240.0,               # X: -240..0 muro fabrica ladrillo
            "wall_top_z": 640.0,
            "forjado_h": 250.0,            # Z: -250..0
            "roza_size": 50.0,             # PTL-2: roza 5x5 cm (50x50 mm)
            "roza_bot_z": 485.0,           # 350 mm (35 cm) encima del nivel de entrega Z=135
            "gutter_drop_h": 350.0,        # Cota exacta "35" cm entre roza/solape y nivel de faldón
            "rpe3_h": 20.0,                # RPE-3 mortero 1:8 bajo fondo canalon (Z: 0..20)
            "gutter_w": 200.0,             # X: 0..200 luz canalon
            "gutter_chamfer": 25.0,
            "zinc_t": 1.8,                 # Canalon de cinc QAT-2
            "zinc_flange_w": 120.0,        # ala sobre PTL-7 para solape >= 100 mm
            "ptl7_x0": 200.0,
            "ptl7_t": 50.0,                # X: 200..250 maestra LHS 40 mm + mortero 1:6
            "ptl7_h": 135.0,               # Z: 0..135
            "slope": 0.05,                 # 5%
            "faldon_min_h": 135.0,         # en X=250
            "reg_mortar_h": 15.0,
            "mem_h": 4.0,
            "solape_mm": 100.0,            # >= 10 cm sobre el canalon
            "agarre_h": 15.0,
            "rasilla_h": 20.0,
            "rasilla_l": 280.0,
            "rasilla_joint": 6.0,
            "rasilla_overhang": 20.0,      # vuelo sobre el canalon
        },
        "layers": [
            {
                "code": "PAV",
                "name": "Rasilla Cerámica + Mortero de Agarre",
                "thickness_mm": "20 mm + 15 mm agarre",
                "spec": "Pavimento de rasilla con vuelo goterón de 20 mm sobre la vertical interior del canalón.",
                "color": "#C25940",
                "mesh_keys": ["Q17_Rasilla", "Q17_Agarre"],
                "explode_z": 180.0,
            },
            {
                "code": "MEM",
                "name": "Membrana Impermeabilizante (Solape ≥10 cm)",
                "thickness_mm": "4 mm / solape 100 mm",
                "spec": "Membrana impermeabilizante bituminosa extendida sobre mortero de regularización con solape mínimo reglamentario de 10 cm (100 mm) sobre el ala del canalón de cinc.",
                "color": "#26282B",
                "mesh_keys": ["Q17_Membrane"],
                "explode_z": 130.0,
            },
            {
                "code": "QAT-2",
                "name": "Canalón de Cinc Plegado (Cota 35 cm)",
                "thickness_mm": "1,8 mm / H = 350 mm",
                "spec": "QAT-2: Canalón de cinc con fondo achaflanado de 200 mm, pared vertical rematada a 35 cm en roza PTL-2 de 5×5 cm y ala horizontal de 120 mm sobre maestra PTL-7.",
                "color": "#8D9BA3",
                "mesh_keys": ["Q17_ZincGutter"],
                "explode_z": 90.0,
            },
            {
                "code": "RPE-3",
                "name": "Mortero de Asiento RPE-3 (1:8)",
                "thickness_mm": "20 mm",
                "spec": "RPE-3: Mortero de cemento y arena de río, de dosificación 1:8, sirviendo de lecho continuo bajo la solera del canalón de cinc.",
                "color": "#9B9489",
                "mesh_keys": ["Q17_RPE3"],
                "explode_z": 40.0,
            },
            {
                "code": "PTL-7",
                "name": "Maestra PTL-7 de Ladrillo Hueco Sencillo",
                "thickness_mm": "50 mm (LHS 40 mm + 1:6)",
                "spec": "PTL-7: Maestra formada por tabique de ladrillo hueco sencillo recibido con mortero de cemento y arena de río, de dosificación 1:6.",
                "color": "#CC6D4A",
                "mesh_keys": ["Q17_PTL7_Bricks", "Q17_RegMortar"],
                "explode_z": 30.0,
            },
            {
                "code": "FAL",
                "name": "Faldón de Hormigón Aligerado (5%)",
                "thickness_mm": "135–170 mm",
                "spec": "Formación de pendiente de hormigón aligerado con caída del 5% hacia la maestra del canalón.",
                "color": "#A7A299",
                "mesh_keys": ["Q17_HormigonAlig"],
                "explode_z": 20.0,
            },
            {
                "code": "MURO",
                "name": "Muro con Roza PTL-2 (5×5 cm) + Forjado",
                "thickness_mm": "Muro 240 mm / Forj. 250 mm",
                "spec": "Fábrica de ladrillo de 1 pie (240 mm) con roza PTL-2 de 5×5 cm para recibido del canalón, sobre forjado de hormigón de 250 mm.",
                "color": "#B8664B",
                "mesh_keys": ["Q17_WallBricks", "Q17_Forjado"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle3": {
        "id": "detalle3",
        "category": "azoteas",
        "category_label": "Azoteas Planas",
        "code": "DET-03 · CAZOLETA SIFÓNICA",
        "slide": "Diapositiva 3 · Pág. 21 (Análisis Detalle)",
        "title": "Azotea Transitable con Hormigón Celular · Cazoleta Sifónica",
        "subtitle": "Despiece completo de cazoleta sifónica con sello hidráulico, cámara de bajante aislada y rasilla de Aspe",
        "scale_2d": "1:5",
        "normativa": "CTE DB-HS1 / DB-HS5 / DB-HR · NTE-QAT",
        "bounds_mm": {"x_min": -750.0, "x_max": 750.0, "y_min": -420.0, "y_max": 420.0, "z_min": -600.0, "z_max": 230.0},
        "params": {
            "span_half_x": 750.0,
            "span_half_y": 420.0,
            "forjado_h": 250.0,            # Z: -250..0
            "slab_hole_r": 84.0,           # Diametro 168 mm para bajante 110 + fibra 25 mm + holgura
            "revest_h": 15.0,              # Z: -265..-250 y cara exterior falseado
            "falseado_inner_half": 100.0,  # 200x200 interior patinillo
            "falseado_brick_t": 40.0,      # Ladrillo hueco sencillo del 4 (X: 100..140)
            "falseado_bot_z": -600.0,
            "bajante_od": 110.0,           # PVC Ø110 mm (radio 55)
            "bajante_wall": 3.2,
            "copa_od": 118.0,              # copa superior Z: -55..0
            "fibra_t": 25.0,               # Manta fibra de vidrio alrededor de bajante (r: 56..81)
            "bv_h": 3.0,                   # Barrera cortavapor Z: 0..3
            "pit_inner_half": 125.0,       # 250x250 hueco interior caja ladrillo
            "pit_brick_t": 70.0,           # LHD 240x115x70 mm -> X: 125..195
            "pit_brick_h": 115.0,          # Z: 3..118 (2x4 celdas huecas visibles)
            "pit_mortar_bed_h": 32.0,      # mortero asiento cazoleta Z: 3..35
            "slope": 0.03,                 # 3% pendiente hormigón celular
            "hc_min_h": 115.0,             # en X=+-195 -> Z_top=118
            "mortero16_h": 18.0,            # Mortero 1:6 regularizacion
            "refuerzo_h": 4.0,             # Refuerzo membrana (penetra hasta bajante)
            "refuerzo_ext_w": 240.0,       # extension desde borde caja sobre faldon
            "membrana_h": 4.0,             # Membrana impermeabilizante principal
            "solape_mm": 100.0,            # Solape 10 cm sobre ala/refuerzo
            "mortero18_h": 15.0,            # Mortero agarre 1:8
            "rasilla_h": 20.0,             # Rasilla de Aspe 280x140x20
            "rasilla_l": 280.0,
            "rasilla_w": 140.0,
            "rasilla_joint": 6.0,
            # Cazoleta sifonica milimetrica
            "caz_outer_half": 120.0,       # 240x240 cuerpo exterior
            "caz_wall": 3.0,
            "caz_bot_z": 35.0,
            "caz_flange_z": 139.0,
            "caz_flange_w": 36.0,          # ala perimetral 36 mm
            "weir_id": 104.0,              # tubo rebosadero central
            "weir_top_z": 98.0,            # nivel de rebose = nivel sello hidraulico
            "tail_bot_z": -45.0,           # penetra 45 mm dentro de la copa de bajante
            "bell_od": 164.0,              # campana sifonica Ø164 mm
            "bell_skirt_z": 65.0,          # sumergida 33 mm bajo agua (98 - 65 = 33 mm cierre)
            "bell_dome_z": 126.0,
            "rejilla_outer_half": 124.0,   # 248x248 marco exterior rasante con pavimento
            "rejilla_inner_half": 109.0,   # 218x218 rejilla ranurada
            "rejilla_top_z": 182.0,        # rasante con superficie superior de Rasilla de Aspe
            "rejilla_t": 10.0,
        },
        "layers": [
            {
                "code": "RASILLA",
                "name": "Rasilla de Aspe + Rejilla Sifónica",
                "thickness_mm": "20 mm (280×140×20)",
                "spec": "Pavimento fijo de rasilla cerámica extrusionada de Aspe (280×140×20 mm) con junta de 6 mm, enrasada perimetralmente con el cerco y rejilla ranurada atornillada de la cazoleta sifónica.",
                "color": "#C65A42",
                "mesh_keys": ["D3_Rasilla", "D3_RejillaFrame", "D3_RejillaGrate"],
                "explode_z": 240.0,
            },
            {
                "code": "M-1:8",
                "name": "Mortero de Agarre 1:8",
                "thickness_mm": "15 mm",
                "spec": "Mortero bastardo/cemento de agarre de dosificación 1:8 extendido en capa continua de 15 mm para recibido de la rasilla y el cerco de la rejilla.",
                "color": "#BFB7AC",
                "mesh_keys": ["D3_Mortero18"],
                "explode_z": 195.0,
            },
            {
                "code": "IMP",
                "name": "Membrana Impermeabilizante + Refuerzo",
                "thickness_mm": "4 mm + 4 mm refuerzo (solape 10 cm)",
                "spec": "Doble sistema impermeabilizante: refuerzo inferior de lámina adherida penetrando hasta la embocadura de la bajante y membrana principal solapada ≥100 mm sobre el ala de la cazoleta.",
                "color": "#232528",
                "mesh_keys": ["D3_Membrana", "D3_RefuerzoMembrana"],
                "explode_z": 150.0,
            },
            {
                "code": "CAZ-SIF",
                "name": "Cazoleta Sifónica (Campana + Sello Hidráulico)",
                "thickness_mm": "240×240 mm · Sello 33 mm",
                "spec": "Cazoleta sifónica registrable con cubeta receptora, rebosadero central Ø104 mm, campana sifónica Ø164 mm sumergida 33 mm bajo lámina de agua (sello hidráulico 60 mm) y tornillo central de fijación a rejilla.",
                "color": "#949CA4",
                "mesh_keys": ["D3_CazoletaBody", "D3_CampanaSifonica", "D3_WaterSeal"],
                "explode_z": 105.0,
            },
            {
                "code": "M-1:6",
                "name": "Mortero de Regularización 1:6",
                "thickness_mm": "18 mm",
                "spec": "Capa de regularización superficial de mortero de cemento y arena 1:6 sobre el hormigón celular y sobre la caja de ladrillo hueco, creando un soporte liso para la membrana.",
                "color": "#A69E92",
                "mesh_keys": ["D3_Mortero16", "D3_PitMortarBed"],
                "explode_z": 70.0,
            },
            {
                "code": "HC",
                "name": "Hormigón Celular (3%) + Caja Ladrillo Hueco",
                "thickness_mm": "115–132 mm (LHD 70 mm)",
                "spec": "Hormigón celular aligerado con formación de pendiente al 3% hacia el sumidero, contenido perimetralmente por caja de ladrillo hueco doble (70×115 mm) alrededor de la cazoleta.",
                "color": "#D7D2C7",
                "mesh_keys": ["D3_HormigonCelular", "D3_PitBricks"],
                "explode_z": 35.0,
            },
            {
                "code": "BV",
                "name": "Barrera Cortavapor",
                "thickness_mm": "3 mm",
                "spec": "Barrera cortavapor continua dispuesta entre el forjado y el hormigón celular, interrumpida limpiamente en el paso estanco de la bajante.",
                "color": "#2E3136",
                "mesh_keys": ["D3_BarreraCortavapor"],
                "explode_z": 15.0,
            },
            {
                "code": "FORJ",
                "name": "Forjado + Bajante Ø110 + Fibra Vidrio + Falseado",
                "thickness_mm": "250 mm / Ø110 + 25 mm + LHS 4 cm",
                "spec": "Forjado estructural (250 mm) con revestimiento inferior (15 mm), paso de bajante PVC Ø110 mm envuelta en manta acústica/térmica de fibra de vidrio (25 mm) y falseado con tabique de ladrillo hueco sencillo del 4 (40 mm) revestido.",
                "color": "#C6CBD0",
                "mesh_keys": ["D3_Forjado", "D3_Revestimiento", "D3_FalseadoBricks", "D3_FibraVidrio", "D3_Bajante"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle4_plots": {
        "id": "detalle4_plots",
        "category": "azoteas",
        "category_label": "Azoteas Planas",
        "code": "DET-04 · AZOTEA INVERTIDA PLOTS",
        "slide": "AZ-08 · Págs. 26, 52 y 55 (Azotea Invertida con Pavimento sobre Soportes)",
        "title": "Azotea Invertida Transitable · Pavimento Flotante sobre Soportes (PLOTS)",
        "subtitle": "Losas armadas 400×400 con junta abierta, plots regulables, XPS sobre membrana bicapa y peto con albardilla",
        "scale_2d": "1:5",
        "normativa": "AZ-08 (IVE Typ. 4-5) · CTE DB-HS1 / DB-HE1",
        "bounds_mm": {"x_min": 0.0, "x_max": 1220.0, "y_min": -440.0, "y_max": 440.0, "z_min": -260.0, "z_max": 860.0},
        "params": {
            "deck_end_x": 1020.0,
            "junta_eps_w": 15.0,
            "enfoscado_int_w": 15.0,
            "peto_brick_w": 140.0,
            "enfoscado_ext_w": 20.0,
            "albardilla_h": 45.0,
            "albardilla_overhang": 25.0,
            "peto_top_z": 820.0,
            "forjado_h": 260.0,
            "compresion_h": 50.0,
            "slope": 0.025,
            "fp_min_h": 50.0,
            "fp_reg_h": 20.0,
            "i_h": 6.0,
            "i_turnup_h": 210.0,
            "cs_h": 3.0,
            "at_h": 80.0,
            "plot_h": 85.0,
            "plot_step": 404.0,
            "tile_l": 400.0,
            "tile_w": 400.0,
            "tile_h": 40.0,
            "tile_joint": 4.0,
        },
        "layers": [
            {
                "code": "PF",
                "name": "Pavimento Flotante (Losas Armadas 400×400)",
                "thickness_mm": "40 mm (junta abierta 4 mm)",
                "spec": "Baldosas armadas de hormigón prefabricado 400×400×40 mm colocadas en seco con junta abierta de 4 mm para drenaje directo hacia el plano inferior impermeabilizado.",
                "color": "#B3ADA3",
                "mesh_keys": ["D4_Losas"],
                "explode_z": 260.0,
            },
            {
                "code": "PLOT",
                "name": "Soportes Regulables (PLOTS) + Separadores",
                "thickness_mm": "75–105 mm (H nom. 85 mm)",
                "spec": "Pedestales regulables roscados de polipropileno reciclado con base Ø180 mm, disco repartidor de carga y cabezal Ø140 mm con crucetas separadoras de 4 mm absorbiendo la pendiente.",
                "color": "#2F353D",
                "mesh_keys": ["D4_Plots"],
                "explode_z": 200.0,
            },
            {
                "code": "AT",
                "name": "Aislamiento Térmico Invertido (XPS)",
                "thickness_mm": "80 mm (300 kPa)",
                "spec": "Planchas rígidas de poliestireno extruido XPS dispuestas sobre la impermeabilización, con junta perimetral y conductividad térmica λ = 0,034 W/m·K.",
                "color": "#F3E48C",
                "mesh_keys": ["D4_AT_XPS"],
                "explode_z": 150.0,
            },
            {
                "code": "CS",
                "name": "Capa Separadora Geotextil Antipunzonante",
                "thickness_mm": "3 mm (300 g/m²)",
                "spec": "Fieltro geotextil de polipropileno no tejido (300 g/m²) bajo XPS para evitar compatibilidad química y punzonamiento de la lámina.",
                "color": "#D7EBF5",
                "mesh_keys": ["D4_CS_Geotextile"],
                "explode_z": 110.0,
            },
            {
                "code": "I",
                "name": "Membrana Impermeabilizante Bicapa SBS",
                "thickness_mm": "6 mm (4 + 4 LBM) + entrega",
                "spec": "Sistema bicapa bituminoso SBS con refuerzo perimetral y entrega vertical de 210 mm rematada con perfil metálico sobre el peto.",
                "color": "#26292E",
                "mesh_keys": ["D4_I_Membrane"],
                "explode_z": 75.0,
            },
            {
                "code": "FP",
                "name": "Formación de Pendientes (2,5% Hormigón Ligero)",
                "thickness_mm": "50–76 mm + 20 mm reg.",
                "spec": "Hormigón ligero con pendiente mínima del 2,5% regularizado mediante capa de mortero de cemento 1:6 fratasada de 20 mm.",
                "color": "#C4BDB2",
                "mesh_keys": ["D4_FP_Core", "D4_FP_Reg"],
                "explode_z": 35.0,
            },
            {
                "code": "SR",
                "name": "Soporte Resistente (Forjado Unidireccional)",
                "thickness_mm": "260 mm (210 + 50)",
                "spec": "Forjado unidireccional de semiviguetas pretensadas, bovedilla cerámica y capa de compresión de 50 mm HA-25 con zuncho perimetral.",
                "color": "#C6CBD0",
                "mesh_keys": ["D4_SR_Forjado", "D4_SR_Bovedillas", "D4_SR_Zuncho"],
                "explode_z": 0.0,
            },
            {
                "code": "PETO",
                "name": "Peto de Fábrica + Barrera Antihumedad + Albardilla",
                "thickness_mm": "140 mm LHD + Albardilla",
                "spec": "Peto de fábrica de ladrillo perforado/hueco 140 mm enfoscado interior/exterior, barrera antihumedad bajo coronación y albardilla de piedra artificial con doble goterón.",
                "color": "#D4886A",
                "mesh_keys": ["D4_Peto_Bricks", "D4_Peto_Enfoscado", "D4_Albardilla", "D4_Barrera"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle5_alero_teja": {
        "id": "detalle5_alero_teja",
        "category": "teja",
        "category_label": "Tejados de Teja",
        "code": "DET-05 · ALERO TEJA CURVA + PALOMEROS",
        "slide": "CLASE p.43 · L2 pp.24, 35-38 (QTT-14 Alero de Teja Curva)",
        "title": "Tejado de Teja Curva sobre Tabiquillos Palomeros · Alero y Canalón Visto",
        "subtitle": "Tabiquillos aligerados calados, tablero cerámico machihembrado, mortero M-2,5 y teja curva canal/cobija con vuelo 5 cm",
        "scale_2d": "1:6",
        "normativa": "CTE DB-HS1 2.4.4.2.2 · NTE-QTT-14 · UNE 136020",
        "bounds_mm": {"x_min": -80.0, "x_max": 1240.0, "y_min": -520.0, "y_max": 520.0, "z_min": -340.0, "z_max": 620.0},
        "params": {
            "slope": 0.30,                # 30% (16.7 deg) - Zona 2
            "wall_x0": 150.0,
            "wall_x1": 290.0,             # 140 mm hoja exterior LHD
            "cham_x1": 340.0,             # 50 mm aislamiento en fachada
            "int_x1": 400.0,              # 60 mm trasdosado interior + enlucido
            "forjado_h": 260.0,
            "compresion_h": 50.0,
            "cornice_overhang": 90.0,     # galce / cornisa de alero (x: 60..150)
            "at_h": 80.0,                 # manta lana mineral sobre forjado
            "tablero_z_eaves": 115.0,     # cota inferior del bardo en X=150 (despeje ventilado s/ aislamiento)
            "tablero_h": 40.0,            # bardo ceramico machihembrado 40 mm
            "reg_h": 25.0,                # mortero M-5 regularizacion
            "mortar_bed_h": 22.0,         # mortero agarre M-2,5 (1:8)
            "tile_len": 450.0,
            "tile_r_wide": 98.0,
            "tile_r_narrow": 76.0,
            "tile_t": 12.0,
            "tile_solape": 140.0,         # paso efectivo 310 mm
            "tile_pitch_y": 240.0,        # separacion transversal ejes canal (30-50 mm entre cobijas)
            "vuelo_alero": 55.0,          # CTE >= 50 mm sobre alero/canalon
            "gutter_cx": 20.0,
            "gutter_cz": 45.0,
            "gutter_r": 65.0,
        },
        "layers": [
            {
                "code": "TEJA",
                "name": "Cobertura de Teja Curva (Canal y Cobija)",
                "thickness_mm": "450×200×160 mm (e=12 mm)",
                "spec": "Teja cerámica curva cónica dispuesta en canales y cobijas con solape mínimo 140 mm (pend. 30%), separación libre ≥35 mm entre cobijas y vuelo de 55 mm sobre canalón con 1ª cobija cortada.",
                "color": "#C95A36",
                "mesh_keys": ["D5_Teja_Canal", "D5_Teja_Cobija"],
                "explode_z": 240.0,
            },
            {
                "code": "MOR",
                "name": "Mortero de Agarre M-2,5 (Recalce y Macizado)",
                "thickness_mm": "22 mm + recalce 1ª hilada",
                "spec": "Mortero mixto M-2,5 (1:8) en cordones longitudinales discontinuos para ventilación, recalzando la primera hilada de canales y macizando el frente del alero (QTT-14).",
                "color": "#AEA69A",
                "mesh_keys": ["D5_Mortero_Agarre"],
                "explode_z": 185.0,
            },
            {
                "code": "CAN",
                "name": "Canalón Visto Semicircular de Zinc + Ganchos",
                "thickness_mm": "Ø130 mm · Zinc 0,8 mm",
                "spec": "Canalón visto semicircular de zinc prepatinado/galvanizado (pendiente ≥1%) colgado mediante ganchos de pletina galvanizada atornillados al alero cada 500 mm.",
                "color": "#7E93A6",
                "mesh_keys": ["D5_Canalon", "D5_Ganchos"],
                "explode_z": 140.0,
            },
            {
                "code": "TAB",
                "name": "Tablero Cerámico Machihembrado + Capa Compresión",
                "thickness_mm": "40 mm + 25 mm M-5",
                "spec": "Tablero de bardos/rasillones cerámicos machihembrados de 40 mm recibidos con mortero, coronado con capa de regularización/compresión M-5 de 25 mm.",
                "color": "#D97F5D",
                "mesh_keys": ["D5_Tablero", "D5_Regularizacion"],
                "explode_z": 100.0,
            },
            {
                "code": "PAL",
                "name": "Tabiquillos Palomeros Aligerados (Ventilación 25%)",
                "thickness_mm": "LHD 70 mm · paso 500 mm",
                "spec": "Tabiquillos conejeros calados con un 25% de huecos para ventilación cruzada de cámara bajo faldón, replanteados con lienza al 30% y rematados con maestra superior de mortero.",
                "color": "#CC6E4B",
                "mesh_keys": ["D5_Tabiquillos"],
                "explode_z": 55.0,
            },
            {
                "code": "AT",
                "name": "Aislamiento Térmico sobre Forjado (Lana Mineral)",
                "thickness_mm": "80 mm",
                "spec": "Manta de lana mineral/fibra de vidrio de 80 mm extendida de forma continua sobre la cara superior del forjado horizontal entre tabiquillos palomeros.",
                "color": "#E6BD42",
                "mesh_keys": ["D5_Aislamiento"],
                "explode_z": 25.0,
            },
            {
                "code": "SR",
                "name": "Forjado Unidireccional + Cornisa Alero + Fachada",
                "thickness_mm": "260 mm + Fachada capuchina",
                "spec": "Forjado de semiviguetas y bovedillas con zuncho de borde y galce/cornisa armada con goterón sobre fachada de fábrica con aislamiento intermedio.",
                "color": "#C6CBD0",
                "mesh_keys": ["D5_Forjado", "D5_Bovedillas", "D5_Fachada"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle6_cumbrera_teja": {
        "id": "detalle6_cumbrera_teja",
        "category": "teja",
        "category_label": "Tejados de Teja",
        "code": "DET-06 · CUMBRERA VENTILADA EN SECO",
        "slide": "L2 pp.33 y 118 (Detalle Cumbrera Ventilada de Teja Curva)",
        "title": "Cumbrera Ventilada en Seco de Teja Curva sobre Doble Rastrelado",
        "subtitle": "Teja caballete con clip, banda ventilada plisada, soporte metálico regulable y microventilación en doble rastrel",
        "scale_2d": "1:5",
        "normativa": "CTE DB-HS1 2.4.4.2.5 · UNE 136020 · QTT-10",
        "bounds_mm": {"x_min": -760.0, "x_max": 760.0, "y_min": -480.0, "y_max": 480.0, "z_min": -280.0, "z_max": 360.0},
        "params": {
            "half_span_x": 760.0,
            "slope": 0.32,                # 32% (17.74 deg) ambas vertientes
            "tablero_h": 40.0,
            "reg_h": 20.0,
            "at_h": 60.0,                 # XPS sobre tablero bajo lamina
            "lamina_h": 2.0,              # lamina impermeable transpirable
            "contrarastrel_h": 30.0,      # paralelo a maxima pendiente (camara microventilacion)
            "contrarastrel_w": 40.0,
            "rastrel_h": 30.0,            # horizontal transversal
            "rastrel_w": 40.0,
            "tile_len": 450.0,
            "tile_r_wide": 98.0,
            "tile_r_narrow": 76.0,
            "tile_t": 12.0,
            "tile_solape": 140.0,
            "tile_pitch_y": 240.0,
            "ridge_gap_half": 28.0,       # paso ventilacion ~5 cm en cumbrera (L2 p.33)
            "caballete_batten_w": 45.0,
            "caballete_batten_h": 55.0,
        },
        "layers": [
            {
                "code": "CAB",
                "name": "Teja de Cumbrera (Caballete) con Clip Inoxidable",
                "thickness_mm": "440×220×14 mm + clip",
                "spec": "Piezas especiales de cumbrera curva con solape ≥50 mm fijadas en seco mediante ganchos/clips de acero inoxidable sobre rastrel de cumbrera.",
                "color": "#B8492A",
                "mesh_keys": ["D6_Caballetes", "D6_Clips"],
                "explode_z": 260.0,
            },
            {
                "code": "RMV",
                "name": "Banda / Remate de Cumbrera Ventilado + Soporte",
                "thickness_mm": "Ancho 320 mm · Aluminio/Butilo",
                "spec": "Lámina microperforada de aluminio plisado con bandas autoadhesivas de butilo adaptadas al perfil de las cobijas, permitiendo salida de aire caliente sin entrada de agua, apoyada en rastrel elevado por soporte metálico del caballete.",
                "color": "#5C6873",
                "mesh_keys": ["D6_Remate_Ventilado", "D6_Soporte_Caballete", "D6_Rastrel_Cumbrera"],
                "explode_z": 210.0,
            },
            {
                "code": "TEJA",
                "name": "Teja Curva Cerámica (Canal y Cobija)",
                "thickness_mm": "450×200×160 mm · 5 cm paso libre",
                "spec": "Hiladas superiores de teja canal y cobija dejando apertura libre de 50 mm en cumbrera para tiraje ascendente continuo de la cámara de aire.",
                "color": "#C95A36",
                "mesh_keys": ["D6_Teja_Canal", "D6_Teja_Cobija"],
                "explode_z": 160.0,
            },
            {
                "code": "RAST",
                "name": "Doble Rastrelado de Madera Tratada (Microventilación)",
                "thickness_mm": "Contrarastrel 40×30 + Rastrel 40×30",
                "spec": "Sistema de doble enrastrelado en madera de pino tratada autoclave creando una cámara de microventilación libre de ≥30 mm bajo teja.",
                "color": "#C49556",
                "mesh_keys": ["D6_Rastreles", "D6_Contrarastreles"],
                "explode_z": 100.0,
            },
            {
                "code": "IMP",
                "name": "Lámina Impermeable Transpirable bajo Teja",
                "thickness_mm": "2 mm (Sd ≤ 0,05 m)",
                "spec": "Membrana transpirable de alta difusión al vapor de agua e impermeable al viento y lluvia accidental sobre el aislamiento.",
                "color": "#45769E",
                "mesh_keys": ["D6_Lamina_Transpirable"],
                "explode_z": 60.0,
            },
            {
                "code": "AT",
                "name": "Aislamiento Térmico XPS sobre Faldón",
                "thickness_mm": "60 mm",
                "spec": "Planchas rígidas machihembradas de XPS de 60 mm continuas en ambos faldones hasta la línea de cumbrera para rotura de puente térmico.",
                "color": "#F3E48C",
                "mesh_keys": ["D6_AT_XPS"],
                "explode_z": 30.0,
            },
            {
                "code": "SOP",
                "name": "Soporte Inclinado (Tablero Cerámico + Viga Cumbrera)",
                "thickness_mm": "40 mm bardo + 20 mm M-5",
                "spec": "Tablero de bardo cerámico regularizado con mortero M-5 apoyado sobre viga o tabiquillo de cumbrera estructural.",
                "color": "#C6CBD0",
                "mesh_keys": ["D6_Soporte", "D6_Tablero"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle7_teja_mixta": {
        "id": "detalle7_teja_mixta",
        "category": "teja",
        "category_label": "Tejados de Teja",
        "code": "DET-07 · TEJA MIXTA + ENCUENTRO PARAMENTO",
        "slide": "L2 pp.75, 81, 87, 88 y 118 (Teja Mixta sobre Doble Rastrel)",
        "title": "Faldón de Teja Mixta sobre Doble Rastrel · Encuentro con Paramento Vertical",
        "subtitle": "Perfil mixto de doble encaje sobre rastreles con contrarastrel, peine de alero, banda autoadhesiva ≥10 cm y babero zinc ≥25 cm",
        "scale_2d": "1:5",
        "normativa": "CTE DB-HS1 2.4.4.2.1 · NTE-QTT-13 · UNE 136020",
        "bounds_mm": {"x_min": -60.0, "x_max": 1240.0, "y_min": -480.0, "y_max": 480.0, "z_min": -260.0, "z_max": 860.0},
        "params": {
            "slope": 0.36,                # 36% (19.8 deg)
            "deck_end_x": 1000.0,
            "wall_x0": 1000.0,
            "wall_x1": 1160.0,            # 140 mm LHD + 20 mm enfoscado
            "wall_top_z": 840.0,
            "forjado_h": 220.0,
            "reg_h": 20.0,
            "at_h": 70.0,
            "lamina_h": 2.0,
            "contrarastrel_h": 35.0,
            "rastrel_h": 35.0,
            "rastrel_w": 40.0,
            "tile_l": 440.0,
            "tile_w": 260.0,
            "tile_step": 355.0,
            "tile_h": 14.0,
            "wave_h": 42.0,
            "babero_up_h": 260.0,         # >= 250 mm entrega vertical s/ teja (L2 p.87)
            "babero_lap": 120.0,          # >= 100 mm banda impermeable autoadhesiva
        },
        "layers": [
            {
                "code": "BAB",
                "name": "Babero de Zinc/Plomo + Banda Impermeable Autoadhesiva",
                "thickness_mm": "Zinc 0,8 mm · ≥25 cm + ≥10 cm",
                "spec": "Encuentro estanco con paramento vertical formado por banda impermeable autoadhesiva plisada ≥100 mm sobre teja mixta y babero metálico de zinc engatillado ≥250 mm recibido en roza y sellado.",
                "color": "#6E8396",
                "mesh_keys": ["D7_Babero_Zinc", "D7_Banda_Impermeable"],
                "explode_z": 240.0,
            },
            {
                "code": "TEJA-M",
                "name": "Teja Cerámica Mixta con Doble Encaje",
                "thickness_mm": "440×260 mm (solape 85 mm)",
                "spec": "Teja cerámica de encaje mixto (canal plano + cobija curva) con tacones de apoyo sobre rastrel y fijación mediante tornillo/gancho inoxidable. Primer rastrel recrecido +20 mm.",
                "color": "#B34B30",
                "mesh_keys": ["D7_Teja_Mixta", "D7_Peine_Alero"],
                "explode_z": 185.0,
            },
            {
                "code": "RAST",
                "name": "Rastrel Horizontal + Contrarastrel + Aislamiento XPS",
                "thickness_mm": "35+35 mm rastrel · 70 mm XPS",
                "spec": "Doble enrastrelado de pino tratado autoclave sobre lámina impermeable transpirable con aislamiento XPS de 70 mm entre contrarastreles y cámara ventilada de 35 mm.",
                "color": "#C49556",
                "mesh_keys": ["D7_Rastreles", "D7_Contrarastreles", "D7_AT_XPS", "D7_Lamina"],
                "explode_z": 115.0,
            },
            {
                "code": "MURO",
                "name": "Paramento Vertical Enfoscado + Remate Albardilla",
                "thickness_mm": "LHD 140 mm + 20 mm enfoscado",
                "spec": "Muro de cerramiento/casetón de ladrillo hueco doble enfoscado con mortero 1:6, roza perimetral para entrega de babero metálico y coronación.",
                "color": "#D4886A",
                "mesh_keys": ["D7_Muro_Bricks", "D7_Muro_Enfoscado"],
                "explode_z": 0.0,
            },
            {
                "code": "FORJ",
                "name": "Forjado Inclinado de Hormigón + Regularización",
                "thickness_mm": "220 mm + 20 mm M-5",
                "spec": "Faldón estructural inclinado (36%) de hormigón armado regularizado con mortero fratasado M-5 y barrera cortavapor.",
                "color": "#C6CBD0",
                "mesh_keys": ["D7_Forjado", "D7_Regularizacion"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle8_pizarra": {
        "id": "detalle8_pizarra",
        "category": "pizarra",
        "category_label": "Pizarra Natural",
        "code": "DET-08 · PIZARRA NATURAL QTP-14",
        "slide": "L4 pp.17, 45 y 51 (QTP-14 Alero + Doble Rastrel y Ganchos)",
        "title": "Tejado de Pizarra Natural · Alero con Emboble, Ganchos Inox y Doble Rastrel",
        "subtitle": "Solape R=100 mm, vista V=100 mm, vuelo 50 mm en alero, ganchos vistos AISI 316 y rotura de puente térmico",
        "scale_2d": "1:5",
        "normativa": "NTE-QTP-14 · UNE-EN 12326 · CTE DB-HS1",
        "bounds_mm": {"x_min": -80.0, "x_max": 1060.0, "y_min": -440.0, "y_max": 440.0, "z_min": -260.0, "z_max": 660.0},
        "params": {
            "slope": 0.56,                # 56% (~29.2 deg) tipica cubierta de pizarra
            "wall_x0": 110.0,
            "wall_x1": 290.0,
            "forjado_h": 210.0,
            "reg_h": 20.0,
            "at_h": 50.0,                 # aislamiento entre contrarastreles 50x50
            "contrarastrel_h": 50.0,
            "camara_h": 30.0,             # camara ventilacion min 30 mm (L4 p.51)
            "rastrel_h": 25.0,            # rastrel horizontal 40x25 mm
            "rastrel_w": 40.0,
            "slate_l": 300.0,             # 300 x 200 x 6 mm rectangular (QTP-14)
            "slate_w": 200.0,
            "slate_t": 6.5,
            "slate_vista": 100.0,         # V = 100 mm, R = 100 mm -> 3 capas en solape
            "vuelo_alero": 50.0,
        },
        "layers": [
            {
                "code": "PIZ",
                "name": "Lajas de Pizarra Natural Biselada (300×200×6,5 mm)",
                "thickness_mm": "6,5 mm · V=100 · R=100 mm",
                "spec": "Pizarra natural exfoliada con bordes biselados dispuesta por hiladas con recubrimiento R=100 mm, parte vista V=100 mm y doble hilada en alero (emboble) volando 50 mm.",
                "color": "#3B424D",
                "mesh_keys": ["D8_Pizarras", "D8_Pizarra_Emboble"],
                "explode_z": 220.0,
            },
            {
                "code": "GAN",
                "name": "Ganchos Vistos Acero Inoxidable + Chapa Goterón Zinc",
                "thickness_mm": "Ø 2,7 mm AISI 316 · Chapa 0,8 mm",
                "spec": "Sujeción por gancho inoxidable clavado al rastrel horizontal y chapa goterón metálica de zinc de arranque en el borde del alero para escupir agua y proteger la madera.",
                "color": "#9AA4AE",
                "mesh_keys": ["D8_Ganchos", "D8_Gotero_Zinc"],
                "explode_z": 165.0,
            },
            {
                "code": "RAST",
                "name": "Rastrel Horizontal + Contrarastrel Ventilado + Aislamiento",
                "thickness_mm": "40×25 + cámara 30 + XPS 50 mm",
                "spec": "Doble enrastrelado de madera tratada con aislamiento térmico de 50 mm encajado entre contrarastreles (rotura de puente térmico) y cámara de ventilación ≥30 mm.",
                "color": "#C49556",
                "mesh_keys": ["D8_Rastreles", "D8_Contrarastreles", "D8_AT_XPS"],
                "explode_z": 95.0,
            },
            {
                "code": "FORJ",
                "name": "Forjado Unidireccional Inclinado + Muro de Apoyo",
                "thickness_mm": "210 mm + 20 mm reg.",
                "spec": "Forjado inclinado (56%) de viguetas y bovedillas regularizado con mortero armado y apoyado sobre muro de cerramiento enfoscado.",
                "color": "#C6CBD0",
                "mesh_keys": ["D8_Forjado", "D8_Muro"],
                "explode_z": 0.0,
            },
        ],
    },
    "detalle9_zinc": {
        "id": "detalle9_zinc",
        "category": "metal",
        "category_label": "Metálicas",
        "code": "DET-09 · ZINC JUNTA ALZADA VMZ",
        "slide": "L6 pp.8, 11 y 12 (Cubierta Engatillada de Zinc en Junta Alzada)",
        "title": "Cubierta Metálica de Zinc Prepatinado en Junta Alzada Engatillada",
        "subtitle": "Bandejas modulares 580 mm con doble engatillado 25 mm, patas fijas/correderas inox, entarimado ventilado y remate peto",
        "scale_2d": "1:5",
        "normativa": "UNE-EN 988 · CTE DB-HS1 2.4 · Sistemas VMZINC",
        "bounds_mm": {"x_min": 0.0, "x_max": 1220.0, "y_min": -660.0, "y_max": 660.0, "z_min": -240.0, "z_max": 780.0},
        "params": {
            "slope": 0.16,                # 16% (9.1 deg)
            "deck_end_x": 1000.0,
            "wall_x0": 1000.0,
            "wall_x1": 1160.0,
            "forjado_h": 200.0,
            "bv_h": 3.0,
            "at_h": 80.0,
            "camara_h": 40.0,             # rastrel ventilacion 40x50 mm
            "entarimado_h": 24.0,         # tabla pino macho/separacion 8 mm
            "capa_dren_h": 8.0,           # esterilla drenante estructurada (antiruido / antihumedad zinc)
            "zinc_t": 1.2,                # representacion visual 0.8-1.2 mm (exact seam 25 mm high)
            "seam_h": 28.0,
            "pan_module_y": 580.0,        # L6 p.11 exact 580 mm bandeja module
        },
        "layers": [
            {
                "code": "ZN",
                "name": "Bandejas de Zinc Prepatinado en Junta Alzada (580 mm)",
                "thickness_mm": "0,8 mm · Alzado H=25 mm · Remates",
                "spec": "Bandejas de zinc-titanio prepatinado (módulo 580 mm) con pliegue lateral doble engatillado de 25 mm de altura, encuentro relevado contra peto cubierto con babero de zinc y coronación de albardilla metálica.",
                "color": "#73808C",
                "mesh_keys": ["D9_Bandejas_Zinc", "D9_Juntas_Alzadas", "D9_Remate_Peto"],
                "explode_z": 240.0,
            },
            {
                "code": "PATA",
                "name": "Patas Fijas y Correderas Acero Inox + Capa Drenante",
                "thickness_mm": "AISI 304 · Esterilla 8 mm",
                "spec": "Clips de acero inoxidable (patas fijas y correderas deslizantes para absorber dilataciones térmicas del zinc) y lámina separadora estructurada drenante de 8 mm.",
                "color": "#B8C2CC",
                "mesh_keys": ["D9_Patas_Inox", "D9_Esterilla_Drenante"],
                "explode_z": 175.0,
            },
            {
                "code": "MAD",
                "name": "Entarimado Ventilado de Madera + Rastreles Cámara",
                "thickness_mm": "24 mm entarimado + 40 mm cámara",
                "spec": "Entarimado continuo de tablas de pino tratadas de 24 mm con separación entre juntas, apoyado sobre rastreles longitudinales de 40 mm formando cámara inferior ventilada.",
                "color": "#C49556",
                "mesh_keys": ["D9_Entarimado", "D9_Rastreles_Camara"],
                "explode_z": 115.0,
            },
            {
                "code": "AT",
                "name": "Aislamiento Térmico + Barrera de Vapor",
                "thickness_mm": "80 mm XPS/PIR + BV 3 mm",
                "spec": "Aislamiento térmico rígido de 80 mm entre listones sobre barrera reguladora de vapor continua.",
                "color": "#F3E48C",
                "mesh_keys": ["D9_AT", "D9_BV"],
                "explode_z": 55.0,
            },
            {
                "code": "FORJ",
                "name": "Soporte Inclinado + Muro Peto Enfoscado",
                "thickness_mm": "200 mm forjado + 140 mm peto",
                "spec": "Soporte resistente inclinado (16%) y peto perimetral de fábrica enfoscada rematado con vierteaguas metálico.",
                "color": "#C6CBD0",
                "mesh_keys": ["D9_Forjado", "D9_Peto"],
                "explode_z": 0.0,
            },
        ],
    },
}


def _clip_poly_halfplane(poly, fn_val, fn_lerp):
    if not poly:
        return []
    out = []
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        va, vb = fn_val(a), fn_val(b)
        if va >= -1e-6:
            if vb >= -1e-6:
                out.append(b)
            else:
                out.append(fn_lerp(a, b, va / (va - vb + 1e-12)))
        elif vb >= -1e-6:
            out.append(fn_lerp(a, b, va / (va - vb + 1e-12)))
            out.append(b)
    return out


def clip_poly_rect(poly, x0, z0, x1, z1):
    """Exact Sutherland-Hodgman clip of a 2D (x, z) polygon against axis-aligned box [x0, x1] x [z0, z1]."""
    def lerp(a, b, t):
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    res = list(poly)
    res = _clip_poly_halfplane(res, lambda p: p[0] - x0, lerp)
    res = _clip_poly_halfplane(res, lambda p: x1 - p[0], lerp)
    res = _clip_poly_halfplane(res, lambda p: p[1] - z0, lerp)
    res = _clip_poly_halfplane(res, lambda p: z1 - p[1], lerp)
    # Deduplicate near-identical consecutive vertices
    clean = []
    for pt in res:
        if not clean or (abs(pt[0] - clean[-1][0]) > 0.2 or abs(pt[1] - clean[-1][1]) > 0.2):
            clean.append(pt)
    if len(clean) >= 2 and abs(clean[0][0] - clean[-1][0]) <= 0.2 and abs(clean[0][1] - clean[-1][1]) <= 0.2:
        clean.pop()
    return clean if len(clean) >= 3 else []


def _poly_signed_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, z0 = poly[i]
        x1, z1 = poly[(i + 1) % len(poly)]
        s += x0 * z1 - x1 * z0
    return 0.5 * s


def compute_bovedilla_profile(vx_left, vx_right, forj_bot, comp_bot, clip_x0=None, clip_x1=None):
    """
    Computes exact architectural Spanish ceramic bovedilla (UNE-EN 15037-3 / Hispalyt):
      - Stepped lower bearing ears resting directly atop joist flanges (z = forj_bot + 42.5 mm)
      - Recessed soffit spanning joist bay (z = forj_bot + 2 mm)
      - Vaulted top + sloped haunches leaving true concrete 'senos' beside joist webs
      - Authentic thin-shell (7.5-8.0 mm) hollow cellular voids (2 tiers x 5 bays)
    Returns (outer_poly_ccw, hole_polys_cw, seno_left_poly, seno_right_poly).
    """
    xl = vx_left + 34.0       # bears against joist upper web above 43 mm flange shelf
    xr = vx_right - 34.0
    x_dl = vx_left + 62.0     # drops down cleanly outside 60 mm joist flange edge
    x_dr = vx_right - 62.0
    z_ear = forj_bot + 43.2   # rests cleanly on top of 40-43 mm joist flange
    z_sof = forj_bot + 2.0    # flush ceiling soffit
    z_sh_bot = z_ear + 28.0   # outer vertical shoulder tip height
    span = xr - xl
    x_tl = xl + min(92.0, span * 0.19)
    x_tr = xr - min(92.0, span * 0.19)
    x_mid = 0.5 * (xl + xr)

    outer_full = [
        (xl, z_ear),
        (x_dl, z_ear),
        (x_dl + 2.0, z_sof),
        (x_dr - 2.0, z_sof),
        (x_dr, z_ear),
        (xr, z_ear),
        (xr, z_sh_bot),
        (xr - (xr - x_tr) * 0.38, z_sh_bot + (comp_bot - z_sh_bot) * 0.48),
        (x_tr, comp_bot - 1.5),
        (x_mid, comp_bot),
        (x_tl, comp_bot - 1.5),
        (xl + (x_tl - xl) * 0.38, z_sh_bot + (comp_bot - z_sh_bot) * 0.48),
        (xl, z_sh_bot),
    ]

    # Inner shell cavity polygon (inset cleanly ~8 mm inward for uniform thin ceramic wall)
    wt = 8.0
    inner_cavity = [
        (xl + wt, z_ear + wt),
        (x_dl + wt, z_ear + wt),
        (x_dl + wt + 2.0, z_sof + wt),
        (x_dr - wt - 2.0, z_sof + wt),
        (x_dr - wt, z_ear + wt),
        (xr - wt, z_ear + wt),
        (xr - wt, z_sh_bot - 2.0),
        (xr - (xr - x_tr) * 0.38 - wt * 0.7, z_sh_bot + (comp_bot - z_sh_bot) * 0.48 - wt),
        (x_tr - wt * 0.4, comp_bot - wt - 1.0),
        (x_mid, comp_bot - wt),
        (x_tl + wt * 0.4, comp_bot - wt - 1.0),
        (xl + (x_tl - xl) * 0.38 + wt * 0.7, z_sh_bot + (comp_bot - z_sh_bot) * 0.48 - wt),
        (xl + wt, z_sh_bot - 2.0),
    ]

    cx0 = xl - 1.0 if clip_x0 is None else clip_x0
    cx1 = xr + 1.0 if clip_x1 is None else clip_x1

    outer_clipped = clip_poly_rect(outer_full, cx0, forj_bot - 2.0, cx1, comp_bot + 2.0)
    if _poly_signed_area(outer_clipped) < 0:
        outer_clipped.reverse()

    # Slice inner_cavity into 2 horizontal tiers x 5 bays separated by thin 7 mm ceramic webs!
    rib = 7.0
    n_cols = 5
    dx_bay = (span - 2 * wt - (n_cols - 1) * rib) / n_cols
    x_bands = []
    xc = xl + wt
    for _ in range(n_cols):
        x_bands.append((xc, xc + dx_bay))
        xc += dx_bay + rib

    z_mid = 0.5 * (z_sof + comp_bot)
    z_bands = [
        (z_sof + wt - 0.5, z_mid - 0.5 * rib),
        (z_mid + 0.5 * rib, comp_bot - wt + 0.5),
    ]

    holes = []
    for (za, zb) in z_bands:
        for (xa, xb) in x_bands:
            ca, cb = max(xa, cx0 + (0.0 if clip_x0 is None else 0.0)), min(xb, cx1)
            # Keep outer cut plane open or closed at clip? Wait: if cut at x=0, leave open face or keep thin 7 mm?
            # Leave open cut cell inside 6 mm rim if full, or slice strictly inside outer_clipped inset by 6 mm!
            if cb - ca > 14.0 and zb - za > 14.0:
                sub = clip_poly_rect(inner_cavity, ca, za, cb, zb)
                if sub and abs(_poly_signed_area(sub)) > 220.0:
                    if _poly_signed_area(sub) > 0:
                        sub.reverse()  # holes CW opposite CCW outer
                    holes.append(sub)

    # Complementary concrete 'senos' filling between joist web and sloped bovedilla shoulders (strictly simple CCW polygons)
    seno_r = [
        (x_tr, comp_bot),
        (x_tr, comp_bot - 1.5),
        (xr - (xr - x_tr) * 0.38, z_sh_bot + (comp_bot - z_sh_bot) * 0.48),
        (xr, z_sh_bot),
        (xr, z_ear),
        (vx_right - 28.0, forj_bot + 50.0),
        (vx_right - 26.0, comp_bot),
    ]
    seno_l = [
        (vx_left + 26.0, comp_bot),
        (vx_left + 28.0, forj_bot + 50.0),
        (xl, z_ear),
        (xl, z_sh_bot),
        (xl + (x_tl - xl) * 0.38, z_sh_bot + (comp_bot - z_sh_bot) * 0.48),
        (x_tl, comp_bot - 1.5),
        (x_tl, comp_bot),
    ]
    if clip_x0 is not None or clip_x1 is not None:
        seno_l = clip_poly_rect(seno_l, cx0, forj_bot - 2.0, cx1, comp_bot + 2.0)
        seno_r = clip_poly_rect(seno_r, cx0, forj_bot - 2.0, cx1, comp_bot + 2.0)
    return outer_clipped, holes, seno_l, seno_r


def write_manifest(out_path=r"d:\C2\data\details_manifest.json"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(DETAILS, f, ensure_ascii=False, indent=2)
    print(f"Manifest written: {out_path}")


if __name__ == "__main__":
    write_manifest()
