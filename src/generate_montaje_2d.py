"""
Generates the Finished 2D Assembly Sequence CAD Package for Detalle 1 (Cartillas IVE)
with 12 Strictly Chronological Site Execution Phases (Fases 01-12):
  1. Complete A3 CAD Sheet (Escala 1:5) with numbered assembly phases 01-12 & execution schedule:
     d:\C2\planos_2d\detalle1_ive_montaje.{dxf, pdf, svg, png}
  2. Live interactive phase-tagged SVG for the Web Assembly Sequencer:
     d:\C2\planos_2d\detalle1_ive_montaje_live.svg
  3. Clean cropped progressive 2D CAD snapshots (cad2d_phase_00..12.png) for the 30s HD Cycles video.
"""

import os
import sys
import xml.sax.saxutils as sax
import pymupdf

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from specs import DETAILS, compute_bovedilla_profile
from cad_2d_core import SheetCanvas2D, hex_to_rgb01
from generate_2d_cad import draw_hollow_brick_section, draw_slope_triangle


PHASES_DETALLE1 = [
    {
        "phase": 1,
        "code": "SR · VIGUETAS",
        "title": "Viguetas pretensadas y armadura sobre sopandas",
        "thickness": "120×210 mm @ 580 mm",
        "desc": "Alineación y acodalamiento sobre sopandas de viguetas pretensadas de hormigón con su armadura inferior Ø8.",
        "t_start": 0.0,
        "t_end": 2.0,
        "color": "#7A828C",
    },
    {
        "phase": 2,
        "code": "SR · BOVEDILLAS",
        "title": "Entrevigado de bovedillas cerámicas reales",
        "thickness": "210×512 mm (10 celdas)",
        "desc": "Colocación de bovedillas cerámicas aligerantes apoyando sus tacones laterales sobre las alas de las viguetas.",
        "t_start": 2.0,
        "t_end": 4.4,
        "color": "#C96A50",
    },
    {
        "phase": 3,
        "code": "SR · HA-25",
        "title": "Ferralla, mallazo, zuncho y vertido in-situ HA-25",
        "thickness": "50 mm comp. + senos + zuncho",
        "desc": "Armado de zuncho perimetral y mallazo de reparto #150×150 Ø6; vertido de hormigón HA-25 macizando senos y losa.",
        "t_start": 4.4,
        "t_end": 7.2,
        "color": "#8E969E",
    },
    {
        "phase": 4,
        "code": "PETO · LHD",
        "title": "Fábrica de peto LHD 140 mm hilada a hilada",
        "thickness": "140 mm (8 hiladas + mortero)",
        "desc": "Levantamiento hilada por hilada a matajunta de fábrica LHD 140 mm recibida con tendeles M-5 (sin revestir aún).",
        "t_start": 7.2,
        "t_end": 10.8,
        "color": "#B8664B",
    },
    {
        "phase": 5,
        "code": "PETO · ENFOSC.",
        "title": "Enfoscado maestreado int./ext. y albardilla",
        "thickness": "15 mm int. / 20 mm ext.",
        "desc": "Tendida ascendente de enfoscado de mortero hidrófugo sobre la fábrica terminada y colocación de albardilla con goterón.",
        "t_start": 10.8,
        "t_end": 13.4,
        "color": "#C7BDB0",
    },
    {
        "phase": 6,
        "code": "FP · PENDIENTE",
        "title": "Banda EPS, hormigón aligerado 2,5% y regularización",
        "thickness": "15 mm EPS + 55–80 mm + 15 mm reg.",
        "desc": "Banda desolidarizadora EPS contra enfoscado, vertido de arlita al 2,5% y capa superior de regularización mortero 1:6.",
        "t_start": 13.4,
        "t_end": 16.0,
        "color": "#9E7E63",
    },
    {
        "phase": 7,
        "code": "BV · VAPOR",
        "title": "Extensión barrera de vapor bituminosa",
        "thickness": "3 mm",
        "desc": "Desenrollado continuo de lámina oxiasfáltica sobre la regularización impidiendo condensaciones intersticiales.",
        "t_start": 16.0,
        "t_end": 17.6,
        "color": "#2E3034",
    },
    {
        "phase": 8,
        "code": "AT · XPS",
        "title": "Planchas aislantes de poliestireno extruido (XPS)",
        "thickness": "50 mm (300 kPa)",
        "desc": "Colocación a tope y matajunta de planchas rígidas de XPS ajustadas contra la banda perimetral de EPS.",
        "t_start": 17.6,
        "t_end": 19.6,
        "color": "#E0C441",
    },
    {
        "phase": 9,
        "code": "I · IMPERM.",
        "title": "Membrana impermeabilizante SBS y entrega 200 mm",
        "thickness": "4 mm (LBM-40-FP)",
        "desc": "Adhesión de lámina bituminosa SBS sobre el aislante térmico y remonte vertical de 200 mm adherido al enfoscado.",
        "t_start": 19.6,
        "t_end": 22.0,
        "color": "#1E2024",
    },
    {
        "phase": 10,
        "code": "CS · GEOTEX.",
        "title": "Capa separadora de fieltro geotextil",
        "thickness": "2 mm (150 g/m²)",
        "desc": "Extensión de lámina geotextil de polipropileno desolidarizando el mortero de agarre respecto a la impermeabilización.",
        "t_start": 22.0,
        "t_end": 23.4,
        "color": "#3988B5",
    },
    {
        "phase": 11,
        "code": "P · SOLADO",
        "title": "Mortero de agarre y pavimento cerámico fijo",
        "thickness": "20 mm agarre + 20 mm baldosa",
        "desc": "Capa de mortero de cemento 1:6 y colocación a matajunta de baldosa cerámica 280×140×20 mm con junta de 6 mm.",
        "t_start": 23.4,
        "t_end": 25.6,
        "color": "#C45B42",
    },
    {
        "phase": 12,
        "code": "P · RODAPIÉ",
        "title": "Junta elástica perimetral y rodapié cerámico",
        "thickness": "10 mm junta + 200×15 mm rodapié",
        "desc": "Sellado de junta elástica perimetral, recibido de rodapié cerámico y perfil metálico protector de entrega.",
        "t_start": 25.6,
        "t_end": 27.5,
        "color": "#9C3B26",
    },
]


def _emit_phase_geometry(cv, ph_idx, is_ghost=False):
    """Emits ONLY the geometry belonging strictly to phase ph_idx (1..12) onto cv."""
    p = DETAILS["detalle1"]["params"]
    dx_end = p["deck_end_x"]
    j_x0, j_x1 = dx_end, dx_end + p["junta_eps_w"]
    ei_x0, ei_x1 = j_x1, j_x1 + p["enfoscado_int_w"]
    pb_x0, pb_x1 = ei_x1, ei_x1 + p["peto_brick_w"]
    ee_x0, ee_x1 = pb_x1, pb_x1 + p["enfoscado_ext_w"]

    def z_fp_core(x): return p["fp_min_h"] + p["slope"] * x
    def z_fp_top(x): return z_fp_core(x) + p["fp_reg_h"]
    def z_bv_top(x): return z_fp_top(x) + p["bv_h"]
    def z_at_top(x): return z_bv_top(x) + p["at_h"]
    def z_i_top(x): return z_at_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_m_top(x): return z_cs_top(x) + p["mortero_agarre_h"]
    def z_p_top(x): return z_m_top(x) + p["tile_h"]

    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]
    peto_top = p["peto_top_z"]
    z_eps_top = z_at_top(dx_end)
    z_turn_top = z_p_top(dx_end) + p["i_turnup_h"]
    cs_x_end = ei_x0 - p["i_h"] - p["junta_perimetral"]

    if is_ghost:
        cv.add_rect("HATCH_LIGHT", 0.0, forj_bot, ee_x1, 0.0, stroke_hex="#DDD9D0", lw=0.14, dash=[2.0, 2.0])
        cv.add_rect("HATCH_LIGHT", ei_x0, 0.0, ee_x1, peto_top, stroke_hex="#DDD9D0", lw=0.14, dash=[2.0, 2.0])
        return

    if ph_idx == 1:
        for vx in (180.0, 760.0):
            v_pts = [
                (vx - 60, forj_bot), (vx + 60, forj_bot), (vx + 60, forj_bot + 40),
                (vx + 34, forj_bot + 43), (vx + 28, forj_bot + 50), (vx + 26, comp_bot),
                (vx - 26, comp_bot), (vx - 28, forj_bot + 50), (vx - 34, forj_bot + 43),
                (vx - 60, forj_bot + 40),
            ]
            cv.add_poly("FORJADO", v_pts, True, fill_hex="#C7CDD2", stroke_hex="#1B2026", lw=0.36)
            cv.add_circle("FORJADO", vx - 28, forj_bot + 20, 4.0, fill_hex="#1B2026")
            cv.add_circle("FORJADO", vx + 28, forj_bot + 20, 4.0, fill_hex="#1B2026")

    elif ph_idx == 2:
        for vx_l, vx_r, cx0 in ((-400.0, 180.0, 0.0), (180.0, 760.0, None)):
            outer_pts, holes, _, _ = compute_bovedilla_profile(vx_l, vx_r, forj_bot, comp_bot, clip_x0=cx0)
            cv.add_poly("LADRILLO", outer_pts, True, fill_hex="#F7E4DC", stroke_hex="#7D3723", lw=0.30)
            for h_pts in holes:
                cv.add_poly("LADRILLO", h_pts, True, fill_hex="#FFFFFF", stroke_hex="#7D3723", lw=0.18)

    elif ph_idx == 3:
        # Senos laterales de hormigon HA-25 + macizado junto a zuncho
        for vx_l, vx_r, cx0 in ((-400.0, 180.0, 0.0), (180.0, 760.0, None)):
            _, _, seno_l, seno_r = compute_bovedilla_profile(vx_l, vx_r, forj_bot, comp_bot, clip_x0=cx0)
            for seno in (seno_l, seno_r):
                if not seno:
                    continue
                xs = [pt[0] for pt in seno]
                if cx0 is not None and max(xs) <= cx0 + 1.0:
                    continue
                cv.add_poly("FORJADO", seno, True, fill_hex="#D7DCE0", stroke_hex="#2B3138", lw=0.26)
                cv.add_hatch("HATCH_LIGHT", "concrete", seno, spacing=20.0)
        mac_pts = [(786.0, comp_bot), (840.0, comp_bot), (840.0, forj_bot),
                   (820.0, forj_bot), (820.0, forj_bot + 40.0), (794.0, forj_bot + 43.0), (788.0, forj_bot + 50.0)]
        cv.add_poly("FORJADO", mac_pts, True, fill_hex="#D7DCE0", stroke_hex="#2B3138", lw=0.26)
        cv.add_hatch("HATCH_LIGHT", "concrete", mac_pts, spacing=20.0)

        # Zuncho de borde + capa de compresion HA-25
        cv.add_rect("FORJADO", 840.0, forj_bot, ee_x1, comp_bot, fill_hex="#D7DCE0", stroke_hex="#2B3138", lw=0.38)
        cv.add_hatch("HATCH_LIGHT", "concrete", [(840, forj_bot), (ee_x1, forj_bot), (ee_x1, comp_bot), (840, comp_bot)], spacing=22.0)
        cv.add_rect("FORJADO", 0.0, comp_bot, ee_x1, 0.0, fill_hex="#E2E6E9", stroke_hex="#2B3138", lw=0.40)
        cv.add_hatch("HATCH_LIGHT", "concrete", [(0, comp_bot), (ee_x1, comp_bot), (ee_x1, 0), (0, 0)], spacing=18.0)

        # Estribos zuncho + ferralla mallazo de reparto en seccion
        cv.add_rect("FORJADO", 864.0, forj_bot + 24.0, ee_x1 - 24.0, -24.0, fill_hex=None, stroke_hex="#1B2026", lw=0.30)
        for rx in (868.0, ee_x1 - 28.0):
            for rz in (forj_bot + 28.0, -28.0):
                cv.add_circle("FORJADO", rx, rz, 4.5, fill_hex="#1B2026")
        cv.add_line("FORJADO", 8.0, -25.0, ee_x1 - 24.0, -25.0, color_hex="#1B2026", lw=0.32)
        for mx in range(70, int(ee_x1) - 30, 150):
            cv.add_circle("FORJADO", float(mx), -25.0, 2.8, fill_hex="#1B2026")

    elif ph_idx == 4:
        # Solo fabrica de ladrillo LHD hilada a hilada + tendeles M-5 (sin enfoscados!)
        z_cur = 0.0
        while z_cur + 90.0 <= peto_top:
            draw_hollow_brick_section(cv, pb_x0, z_cur, pb_x1, z_cur + 90.0, cols=2, rows=3)
            if z_cur + 100.0 <= peto_top:
                cv.add_rect("MORTERO", pb_x0, z_cur + 90.0, pb_x1, z_cur + 100.0, fill_hex="#CFC9C0", stroke_hex="#5C5852", lw=0.14)
            z_cur += 100.0

    elif ph_idx == 5:
        # Enfoscados maestreados int/ext y albardilla con pendiente y goteron
        cv.add_rect("MORTERO", ei_x0, 0.0, ei_x1, peto_top, fill_hex="#DFD8CE")
        cv.add_rect("MORTERO", ee_x0, 0.0, ee_x1, peto_top, fill_hex="#EFE7DA")
        cv.add_poly("MORTERO", [(ei_x0 - 8, peto_top), (ee_x1 + 8, peto_top), (ee_x1 + 8, peto_top + 38), (ei_x0 - 8, peto_top + 48)],
                    True, fill_hex="#D8CFC2", stroke_hex="#1B2026", lw=0.35)

    elif ph_idx == 6:
        # Junta perimetral EPS + hormigon aligerado arlita 2.5% + mortero regularizacion
        cv.add_rect("AISLAMIENTO", j_x0, 0.0, j_x1, z_eps_top, fill_hex="#FBF8EE", stroke_hex="#4A4E54", lw=0.24)
        cv.add_hatch("HATCH_LIGHT", "cross", [(j_x0, 0), (j_x1, 0), (j_x1, z_eps_top), (j_x0, z_eps_top)], spacing=7.0)
        fp_poly = [(0, 0), (dx_end, 0), (dx_end, z_fp_core(dx_end)), (0, z_fp_core(0))]
        cv.add_poly("HORMIGON_CEL", fp_poly, True, fill_hex="#EBE4D8")
        cv.add_hatch("HATCH_LIGHT", "cellular", fp_poly, spacing=13.0)
        reg_poly = [(0, z_fp_core(0)), (dx_end, z_fp_core(dx_end)), (dx_end, z_fp_top(dx_end)), (0, z_fp_top(0))]
        cv.add_poly("MORTERO", reg_poly, True, fill_hex="#D5CCC0")
        cv.add_hatch("HATCH_LIGHT", "dots", reg_poly, spacing=8.0)

    elif ph_idx == 7:
        bv_poly = [(0, z_fp_top(0)), (dx_end, z_fp_top(dx_end)), (dx_end, z_bv_top(dx_end)), (0, z_bv_top(0))]
        cv.add_poly("MEMBRANA", bv_poly, True, fill_hex="#2D3035", stroke_hex="#101214", lw=0.35)

    elif ph_idx == 8:
        at_poly = [(0, z_bv_top(0)), (dx_end, z_bv_top(dx_end)), (dx_end, z_at_top(dx_end)), (0, z_at_top(0))]
        cv.add_poly("AISLAMIENTO", at_poly, True, fill_hex="#FAF0B2")
        cv.add_hatch("HATCH_INSUL", "diag45", at_poly, spacing=11.0)

    elif ph_idx == 9:
        i_poly = [
            (0, z_at_top(0)), (dx_end, z_at_top(dx_end)),
            (ei_x0, z_at_top(dx_end)), (ei_x0, z_turn_top),
            (ei_x0 - p["i_h"], z_turn_top), (ei_x0 - p["i_h"], z_i_top(dx_end)),
            (0, z_i_top(0)),
        ]
        cv.add_poly("MEMBRANA", i_poly, True, fill_hex="#1E2024", stroke_hex="#101214", lw=0.45)

    elif ph_idx == 10:
        cs_poly = [(0, z_i_top(0)), (cs_x_end, z_i_top(cs_x_end)), (cs_x_end, z_cs_top(cs_x_end)), (0, z_cs_top(0))]
        cv.add_poly("CAPA_SEP", cs_poly, True, fill_hex="#CFEBF7", stroke_hex="#2D7FA8", lw=0.30)

    elif ph_idx == 11:
        m_poly = [(0, z_cs_top(0)), (cs_x_end, z_cs_top(cs_x_end)), (cs_x_end, z_m_top(cs_x_end)), (0, z_m_top(0))]
        cv.add_poly("MORTERO", m_poly, True, fill_hex="#CFC7BC")
        cv.add_hatch("HATCH_LIGHT", "dots", m_poly, spacing=9.0)
        tx = 12.0
        while tx < cs_x_end - 15.0:
            tx_end = min(tx + p["tile_l"], cs_x_end)
            t_poly = [(tx, z_m_top(tx)), (tx_end, z_m_top(tx_end)), (tx_end, z_p_top(tx_end)), (tx, z_p_top(tx))]
            cv.add_poly("PAVIMENTO", t_poly, True, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
            cv.add_hatch("HATCH_BRICK", "diag45", t_poly, spacing=7.0)
            tx = tx_end + p["tile_joint"]

    elif ph_idx == 12:
        cv.add_rect("MEMBRANA", cs_x_end, z_i_top(dx_end), ei_x0 - p["i_h"], z_p_top(dx_end),
                    fill_hex="#4A4F57", stroke_hex="#182028", lw=0.22)
        rod_x1 = ei_x0 - p["i_h"] - 8.0
        rod_x0 = rod_x1 - p["rodapie_t"]
        rod_z0 = z_p_top(dx_end) + 4.0
        rod_z1 = rod_z0 + p["rodapie_h"]
        cv.add_rect("MORTERO", rod_x1, rod_z0, ei_x0 - p["i_h"], rod_z1, fill_hex="#CFC7BC")
        cv.add_rect("PAVIMENTO", rod_x0, rod_z0, rod_x1, rod_z1, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
        cv.add_hatch("HATCH_BRICK", "diag45", [(rod_x0, rod_z0), (rod_x1, rod_z0), (rod_x1, rod_z1), (rod_x0, rod_z1)], spacing=7.0)
        cv.add_poly("METAL_CAZ", [(ei_x0 - 20, rod_z1 + 12), (ei_x0 + 4, rod_z1 + 6), (ei_x0 + 4, rod_z1 + 2), (ei_x0 - 18, rod_z1 + 8)],
                    True, fill_hex="#9AA2AA", stroke_hex="#29465B", lw=0.28)


def _add_annotations(cv):
    p = DETAILS["detalle1"]["params"]
    dx_end = p["deck_end_x"]
    ei_x0 = dx_end + p["junta_eps_w"] + p["enfoscado_int_w"]
    ee_x1 = ei_x0 + p["peto_brick_w"] + p["enfoscado_ext_w"]
    forj_bot = -p["forjado_h"]
    peto_top = p["peto_top_z"]
    def z_fp_top(x): return p["fp_min_h"] + p["slope"] * x + p["fp_reg_h"]
    def z_bv_top(x): return z_fp_top(x) + p["bv_h"]
    def z_at_top(x): return z_bv_top(x) + p["at_h"]
    def z_i_top(x): return z_at_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_m_top(x): return z_cs_top(x) + p["mortero_agarre_h"]
    def z_p_top(x): return z_m_top(x) + p["tile_h"]
    z_turn_top = z_p_top(dx_end) + p["i_turnup_h"]

    cv.add_dim_h(0.0, dx_end, -300.0, forj_bot, forj_bot, label="985 mm")
    cv.add_dim_h(dx_end, ee_x1, -300.0, forj_bot, forj_bot, label="190 mm")
    cv.add_dim_v(forj_bot, 0.0, -48.0, 0.0, 0.0, label="260")
    cv.add_dim_v(0.0, z_fp_top(0), -48.0, 0.0, 0.0, label="70")
    cv.add_dim_v(z_fp_top(0), z_at_top(0), -48.0, 0.0, 0.0, label="53")
    cv.add_dim_v(z_at_top(0), z_p_top(0), -48.0, 0.0, 0.0, label="46")
    cv.add_dim_v(z_p_top(dx_end), z_turn_top, 1218.0, ee_x1, ei_x0, label="200 (entrega I)")
    cv.add_dim_v(0.0, peto_top, 1265.0, ee_x1, ee_x1, label="820")
    draw_slope_triangle(cv, 150.0, z_p_top(150.0), p["slope"], length=220.0, label="2,5%", dir_x=-1.0)

    badge_targets = [
        (1, (180.0, -140.0), (110.0, 625.0)),
        (2, (470.0, -145.0), (200.0, 585.0)),
        (3, (780.0, -25.0), (295.0, 545.0)),
        (4, (1085.0, 620.0), (885.0, 680.0)),
        (5, (1165.0, 745.0), (955.0, 740.0)),
        (6, (640.0, 40.0), (640.0, 290.0)),
        (7, (535.0, 0.5 * (z_fp_top(535) + z_bv_top(535))), (535.0, 345.0)),
        (8, (430.0, 0.5 * (z_bv_top(430) + z_at_top(430))), (430.0, 405.0)),
        (9, (325.0, 0.5 * (z_at_top(325) + z_i_top(325))), (325.0, 465.0)),
        (10, (220.0, 0.5 * (z_i_top(220) + z_cs_top(220))), (745.0, 345.0)),
        (11, (115.0, 0.5 * (z_m_top(115) + z_p_top(115))), (835.0, 415.0)),
        (12, (985.0, z_p_top(dx_end) + 110.0), (885.0, 505.0)),
    ]
    for num, tgt, pos in badge_targets:
        cv.add_line("CALLOUTS", tgt[0], tgt[1], pos[0], pos[1], color_hex="#9C3B26", lw=0.22)
        cv.add_circle("CALLOUTS", tgt[0], tgt[1], 3.0, fill_hex="#9C3B26", stroke_hex="#9C3B26", lw=0.15)
        cv.add_circle("CALLOUTS", pos[0], pos[1], 19.0, fill_hex="#FAF4F1", stroke_hex="#9C3B26", lw=0.35)
        cv.add_text("CALLOUTS", pos[0], pos[1] - 4.0, f"{num:02d}", height_sheet_mm=2.3, color_hex="#9C3B26", align="center")


def _build_phase_canvas(max_phase=12, origin_sheet=(163.0, 108.0), include_schedule=False):
    meta = dict(DETAILS["detalle1"])
    meta["code"] = "IVE · MONTAJE 01–12"
    meta["title"] = "Secuencia de Montaje · Azotea Transitable Convencional (Peto)"
    meta["slide"] = "Diapositiva 1 · Pág. 20 (Orden Constructivo Estricto 12 Fases)"
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=origin_sheet)

    if max_phase < len(PHASES_DETALLE1):
        _emit_phase_geometry(cv, 0, is_ghost=True)
    for ph in range(1, max_phase + 1):
        _emit_phase_geometry(cv, ph, is_ghost=False)
    if include_schedule:
        _add_annotations(cv)
    return cv


def export_finished_montaje_sheet():
    n_ph = len(PHASES_DETALLE1)
    cv = _build_phase_canvas(max_phase=n_ph, origin_sheet=(163.0, 114.0), include_schedule=True)
    dxf_path = r"d:\C2\planos_2d\detalle1_ive_montaje.dxf"
    pdf_path = r"d:\C2\planos_2d\detalle1_ive_montaje.pdf"
    svg_path = r"d:\C2\planos_2d\detalle1_ive_montaje.svg"
    png_path = r"d:\C2\planos_2d\detalle1_ive_montaje.png"

    cv.export_dxf(dxf_path)
    cv.export_pdf_and_png(pdf_path, png_path, dpi=240)
    cv.export_svg(svg_path)

    mm2pt = 72.0 / 25.4
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    shape = page.new_shape()

    def spt(x, y):
        return pymupdf.Point(x * mm2pt, (297.0 - y) * mm2pt)

    bx0, by0, bx1, by1 = 16.0, 35.0, 148.0, 263.0
    p0, p1 = spt(bx0, by0), spt(bx1, by1)
    shape.draw_rect(pymupdf.Rect(min(p0.x, p1.x), min(p0.y, p1.y), max(p0.x, p1.x), max(p0.y, p1.y)))
    shape.finish(fill=(0.985, 0.980, 0.968), color=(0.11, 0.13, 0.15), width=0.35 * mm2pt * 0.72)

    svg_extra = [
        '  <g id="montaje_schedule">',
        '    <rect x="16" y="34" width="132" height="228" fill="#FBF9F5" stroke="#1B2026" stroke-width="0.35"/>',
        '    <text x="20" y="42" font-size="2.35" font-weight="700" fill="#9C3B26">SECUENCIA CONSTRUCTIVA DE MONTAJE (FASES 01–12)</text>',
        '    <text x="20" y="46.2" font-size="1.75" fill="#505A66">Orden cronológico estricto de ejecución en obra · Detalle IVE 1</text>',
    ]

    cur_y = 243.5
    row_h = 17.2
    for ph in PHASES_DETALLE1:
        y_top = cur_y
        shape.draw_line(spt(19.0, y_top + 2.0), spt(145.0, y_top + 2.0))
        shape.finish(color=(0.86, 0.84, 0.80), width=0.32)
        c_pt = spt(23.5, y_top - 2.6)
        shape.draw_circle(c_pt, 2.8 * mm2pt)
        shape.finish(color=(0.61, 0.23, 0.15), fill=(0.98, 0.94, 0.92), width=0.50)
        cur_y -= row_h

    shape.commit()

    page.insert_text(spt(20.0, 255.2), "SECUENCIA CONSTRUCTIVA DE MONTAJE (FASES 01–12)",
                     fontname="hebo", fontsize=2.30 * mm2pt, color=(0.61, 0.23, 0.15))
    page.insert_text(spt(20.0, 250.8), "Orden cronológico estricto de ejecución en obra · Detalle IVE Tipología 1",
                     fontname="helv", fontsize=1.70 * mm2pt, color=(0.35, 0.39, 0.44))

    cur_y = 243.5
    for ph in PHASES_DETALLE1:
        y_top = cur_y
        svg_y_top = 297.0 - y_top
        svg_extra.append(f'    <line x1="19" y1="{svg_y_top - 2.0:.1f}" x2="145" y2="{svg_y_top - 2.0:.1f}" stroke="#DBD6CC" stroke-width="0.20"/>')

        page.insert_text(spt(21.85, y_top - 3.3), f"{ph['phase']:02d}", fontname="hebo", fontsize=1.85 * mm2pt, color=(0.61, 0.23, 0.15))
        page.insert_text(spt(28.5, y_top - 1.9), f"{ph['code']} · {ph['title']}", fontname="hebo", fontsize=1.78 * mm2pt, color=(0.09, 0.11, 0.13))
        page.insert_text(spt(28.5, y_top - 5.5), f"Cota/Dim.: {ph['thickness']}", fontname="helv", fontsize=1.52 * mm2pt, color=(0.11, 0.42, 0.27))

        desc = ph["desc"]
        split_at = desc.rfind(" ", 0, 74) if len(desc) > 74 else len(desc)
        d1, d2 = desc[:split_at], desc[split_at + 1 :]
        page.insert_text(spt(28.5, y_top - 8.9), d1, fontname="helv", fontsize=1.45 * mm2pt, color=(0.30, 0.34, 0.38))
        if d2:
            page.insert_text(spt(28.5, y_top - 11.9), d2, fontname="helv", fontsize=1.45 * mm2pt, color=(0.30, 0.34, 0.38))

        svg_extra.append(f'    <circle cx="23.5" cy="{svg_y_top + 2.6:.1f}" r="2.8" fill="#FAF0EC" stroke="#9C3B26" stroke-width="0.28"/>')
        svg_extra.append(f'    <text x="23.5" y="{svg_y_top + 3.3:.1f}" font-size="1.85" font-weight="700" fill="#9C3B26" text-anchor="middle">{ph["phase"]:02d}</text>')
        svg_extra.append(f'    <text x="28.5" y="{svg_y_top + 1.9:.1f}" font-size="1.8" font-weight="700" fill="#182028">{sax.escape(ph["code"] + " · " + ph["title"])}</text>')
        svg_extra.append(f'    <text x="28.5" y="{svg_y_top + 5.4:.1f}" font-size="1.55" font-weight="600" fill="#185A37">Cota/Dim.: {sax.escape(ph["thickness"])}</text>')
        svg_extra.append(f'    <text x="28.5" y="{svg_y_top + 8.9:.1f}" font-size="1.48" fill="#4B5563">{sax.escape(d1)}</text>')
        if d2:
            svg_extra.append(f'    <text x="28.5" y="{svg_y_top + 11.9:.1f}" font-size="1.48" fill="#4B5563">{sax.escape(d2)}</text>')
        cur_y -= row_h

    tmp_pdf = pdf_path + ".tmp"
    doc.save(tmp_pdf)
    pix = doc[0].get_pixmap(dpi=240, alpha=False)
    pix.save(png_path)
    doc.close()
    os.replace(tmp_pdf, pdf_path)

    svg_extra.append('  </g>')
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_txt = f.read()
    svg_txt = svg_txt.replace("</svg>", "\n".join(svg_extra) + "\n</svg>")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_txt)
    print(f"Generated finished 2D assembly sheet: {png_path}")


def _render_clean_2d_section_to_png(cv, out_png, dpi=180):
    """Renders pure model-space 2D drawing WITHOUT A3 border/title block (for crisp HUD overlay)."""
    mm2pt = 72.0 / 25.4
    w_mm, h_mm = 278.0, 248.0
    cv.ox = 18.0
    cv.oy = 68.0
    cv.sheet_w = w_mm
    cv.sheet_h = h_mm

    doc = pymupdf.open()
    page = doc.new_page(width=w_mm * mm2pt, height=h_mm * mm2pt)
    shape = page.new_shape()
    page.draw_rect(page.rect, fill=(1, 1, 1), color=None)

    for layer, pts, closed, fill_hex, stroke_hex, lw, dash in cv.polys:
        p_pts = [cv._pdf_pt(*cv.m2s(x, z)) for (x, z) in pts]
        if closed:
            p_pts.append(p_pts[0])
        shape.draw_polyline(p_pts)
        shape.finish(
            color=hex_to_rgb01(stroke_hex) if stroke_hex else None,
            fill=hex_to_rgb01(fill_hex) if fill_hex else None,
            width=lw * mm2pt * 0.72,
            closePath=closed,
            dashes=f"[{dash[0]*mm2pt:.1f} {dash[1]*mm2pt:.1f}] 0" if dash else None,
        )

    for layer, kind, poly, spacing, color_hex, ang in cv.hatches:
        segs, circs = cv._generate_hatch_segments(kind, poly, spacing, ang)
        col = hex_to_rgb01(color_hex)
        for ax, az, bx, bz in segs:
            shape.draw_line(cv._pdf_pt(*cv.m2s(ax, az)), cv._pdf_pt(*cv.m2s(bx, bz)))
            shape.finish(color=col, width=0.14 * mm2pt * 0.72)
        for px, pz, r in circs:
            cp = cv._pdf_pt(*cv.m2s(px, pz))
            rp = (r / cv.scale) * mm2pt
            shape.draw_circle(cp, rp)
            shape.finish(color=col, fill=col if kind == "dots" else None, width=0.14 * mm2pt * 0.72)

    for layer, x0, z0, x1, z1, color_hex, lw, dash in cv.lines:
        shape.draw_line(cv._pdf_pt(*cv.m2s(x0, z0)), cv._pdf_pt(*cv.m2s(x1, z1)))
        shape.finish(color=hex_to_rgb01(color_hex), width=lw * mm2pt * 0.72)

    for layer, cx, cz, r, fill_hex, stroke_hex, lw in cv.circles:
        cp = cv._pdf_pt(*cv.m2s(cx, cz))
        rp = (r / cv.scale) * mm2pt
        shape.draw_circle(cp, rp)
        shape.finish(color=hex_to_rgb01(stroke_hex) if stroke_hex else None,
                     fill=hex_to_rgb01(fill_hex) if fill_hex else None,
                     width=lw * mm2pt * 0.72)

    for layer, pts, color_hex, lw, head_mm, dash in cv.arrows:
        col = hex_to_rgb01(color_hex)
        p_pts = [cv._pdf_pt(*cv.m2s(x, z)) for (x, z) in pts]
        shape.draw_polyline(p_pts)
        shape.finish(color=col, width=lw * mm2pt * 0.72)

    shape.commit()

    for layer, x, z, text, h_sheet, color_hex, align, angle in cv.texts:
        sx, sy = cv.m2s(x, z)
        fs = h_sheet * mm2pt
        col = hex_to_rgb01(color_hex)
        tw = pymupdf.get_text_length(text, fontname="helv", fontsize=fs)
        if abs(angle - 90.0) < 1.0:
            pt = cv._pdf_pt(sx, sy - (tw / mm2pt) * 0.5 if align == "center" else sy)
            page.insert_text(pt, text, fontname="helv", fontsize=fs, color=col, rotate=90)
        else:
            dx_mm = (-tw / mm2pt * 0.5) if align == "center" else ((-tw / mm2pt) if align == "right" else 0.0)
            page.insert_text(cv._pdf_pt(sx + dx_mm, sy), text, fontname="helv", fontsize=fs, color=col)

    pix = page.get_pixmap(dpi=dpi, alpha=False)
    pix.save(out_png)
    doc.close()


def export_progressive_2d_frames_and_live_svg():
    out_dir = r"d:\C2\scratch_montaje\cad2d_phases"
    os.makedirs(out_dir, exist_ok=True)
    n_ph = len(PHASES_DETALLE1)
    for ph in range(0, n_ph + 1):
        cv = _build_phase_canvas(max_phase=ph, origin_sheet=(18.0, 68.0), include_schedule=(ph == n_ph))
        _render_clean_2d_section_to_png(cv, os.path.join(out_dir, f"cad2d_phase_{ph:02d}.png"), dpi=165)

    w_mm, h_mm = 278.0, 248.0
    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_mm:.1f} {h_mm:.1f}" style="background:#ffffff; font-family:\'Inter\',Arial,sans-serif;">',
        f'  <rect x="0" y="0" width="{w_mm:.1f}" height="{h_mm:.1f}" fill="#ffffff"/>',
    ]
    for ph in range(0, n_ph + 1):
        cv = SheetCanvas2D(DETAILS["detalle1"], scale_denom=5.0, origin_sheet=(18.0, 68.0))
        cv.sheet_w, cv.sheet_h = w_mm, h_mm
        if ph == 0:
            _emit_phase_geometry(cv, 0, is_ghost=True)
        else:
            _emit_phase_geometry(cv, ph, is_ghost=False)
            if ph == n_ph:
                _add_annotations(cv)

        tmp_svg = os.path.join(out_dir, f"_tmp_{ph}.svg")
        cv.export_svg(tmp_svg)
        raw = open(tmp_svg, encoding="utf-8").read()
        os.remove(tmp_svg)
        start = raw.find('<g id="model_geometry">')
        end = raw.rfind("</g>")
        inner = raw[start + len('<g id="model_geometry">') : end]
        gid = "phase_ghost" if ph == 0 else f"phase_{ph}"
        svg_parts.append(f'  <g id="{gid}" data-phase="{ph}">{inner}</g>')

    svg_parts.append("</svg>")
    live_svg_path = r"d:\C2\planos_2d\detalle1_ive_montaje_live.svg"
    with open(live_svg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
    print(f"Exported progressive 2D frames (00..{n_ph:02d}) & live SVG: {live_svg_path}")


if __name__ == "__main__":
    export_finished_montaje_sheet()
    export_progressive_2d_frames_and_live_svg()
