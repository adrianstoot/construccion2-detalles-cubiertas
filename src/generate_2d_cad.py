"""
Generates exact millimetric 2D CAD sheets (.dxf, .pdf, .svg, .png) for all details
directly from d:\C2\src\specs.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specs import DETAILS, compute_bovedilla_profile
from cad_2d_core import SheetCanvas2D


def draw_hollow_brick_section(cv, x0, z0, x1, z1, cols=2, rows=4, border_col="#7D3723", fill_col="#F9EAE3", hole_col="#FFFFFF"):
    """Draws a true hollow brick cross-section with exact thin physical inner cell voids."""
    cv.add_rect("LADRILLO", x0, z0, x1, z1, fill_hex=fill_col, stroke_hex=border_col, lw=0.30)
    w = x1 - x0
    h = z1 - z0
    wall_x = min(8.5, max(5.5, w * 0.065))
    wall_z = min(8.0, max(5.0, h * 0.075))
    cell_w = (w - (cols + 1) * wall_x) / cols
    cell_h = (h - (rows + 1) * wall_z) / rows
    if cell_w > 3.0 and cell_h > 3.0:
        for ic in range(cols):
            for ir in range(rows):
                cx0 = x0 + wall_x + ic * (cell_w + wall_x)
                cz0 = z0 + wall_z + ir * (cell_h + wall_z)
                cv.add_rect("LADRILLO", cx0, cz0, cx0 + cell_w, cz0 + cell_h, fill_hex=hole_col, stroke_hex=border_col, lw=0.18)


def draw_bovedilla_and_senos_2d(cv, vx_left, vx_right, forj_bot, comp_bot, clip_x0=None, clip_x1=None):
    """Draw authentic ceramic bovedilla (tacones + 10 cells) and poured concrete senos around joists."""
    outer_pts, holes, seno_l, seno_r = compute_bovedilla_profile(
        vx_left, vx_right, forj_bot, comp_bot, clip_x0=clip_x0, clip_x1=clip_x1
    )
    for seno in (seno_l, seno_r):
        if not seno:
            continue
        xs = [pt[0] for pt in seno]
        if clip_x0 is not None and max(xs) <= clip_x0 + 1.0:
            continue
        if clip_x1 is not None and min(xs) >= clip_x1 - 1.0:
            continue
        cv.add_poly("FORJADO", seno, True, fill_hex="#D7DCE0", stroke_hex="#2B3138", lw=0.26)
        cv.add_hatch("HATCH_LIGHT", "concrete", seno, spacing=20.0)
    if outer_pts:
        cv.add_poly("LADRILLO", outer_pts, True, fill_hex="#F7E4DC", stroke_hex="#7D3723", lw=0.30)
    for h_pts in holes:
        cv.add_poly("LADRILLO", h_pts, True, fill_hex="#FFFFFF", stroke_hex="#7D3723", lw=0.18)


def draw_slope_triangle(cv, x_left, z_left, slope, length=120.0, label="2,5%", dir_x=-1.0):
    """Draws an architectural slope indicator arrow + % label above the roof surface."""
    x_right = x_left + length
    z_right = z_left + slope * length
    if dir_x < 0:
        cv.add_flow_arrow([(x_right, z_right + 16.0), (x_left, z_left + 16.0)], color_hex="#185A37", lw=0.24, head_mm=10.0)
    else:
        cv.add_flow_arrow([(x_left, z_left + 16.0), (x_right, z_right + 16.0)], color_hex="#185A37", lw=0.24, head_mm=10.0)
    cv.add_text("COTAS", 0.5 * (x_left + x_right), 0.5 * (z_left + z_right) + 24.0, f"Pend. {label}", height_sheet_mm=2.1, align="center")


# ==============================================================================
# DETALLE 1: Cartillas IVE - Azotea Transitable Convencional (Peto + 7 Capas)
# ==============================================================================
def build_detalle1_2d():
    meta = DETAILS["detalle1"]
    p = meta["params"]
    # Origin mapping so [-100..1350, -320..880] sits nicely on A3 @ 1:5
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(118.0, 98.0))

    dx_end = p["deck_end_x"]          # 985
    j_x0, j_x1 = dx_end, dx_end + p["junta_eps_w"]        # 985..1000
    ei_x0, ei_x1 = j_x1, j_x1 + p["enfoscado_int_w"]      # 1000..1015
    pb_x0, pb_x1 = ei_x1, ei_x1 + p["peto_brick_w"]       # 1015..1155
    ee_x0, ee_x1 = pb_x1, pb_x1 + p["enfoscado_ext_w"]    # 1155..1175

    # Helper: Z bottom of each layer as function of x (2.5% rising toward parapet)
    def z_fp_bot(x): return 0.0
    def z_fp_core_top(x): return p["fp_min_h"] + p["slope"] * x
    def z_fp_top(x): return z_fp_core_top(x) + p["fp_reg_h"]
    def z_bv_top(x): return z_fp_top(x) + p["bv_h"]
    def z_at_top(x): return z_bv_top(x) + p["at_h"]
    def z_i_top(x): return z_at_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_m_top(x): return z_cs_top(x) + p["mortero_agarre_h"]
    def z_p_top(x): return z_m_top(x) + p["tile_h"]

    # 1. SR: Soporte Resistente (Forjado Unidireccional: Viguetas + Bovedillas + Compresion)
    forj_bot = -p["forjado_h"]        # -260
    comp_bot = -p["compresion_h"]     # -50
    cv.add_rect("FORJADO", 0.0, comp_bot, ee_x1, 0.0, fill_hex="#E2E6E9", stroke_hex="#2B3138", lw=0.40)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(0, comp_bot), (ee_x1, comp_bot), (ee_x1, 0), (0, 0)], spacing=18.0)

    # Zuncho de borde bajo peto (X: 840..1175, Z: -260..0)
    cv.add_rect("FORJADO", 840.0, forj_bot, ee_x1, comp_bot, fill_hex="#D7DCE0", stroke_hex="#2B3138", lw=0.38)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(840, forj_bot), (ee_x1, forj_bot), (ee_x1, comp_bot), (840, comp_bot)], spacing=22.0)

    # Viguetas pretensadas en X=180 y X=760
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

    # Bovedillas ceramicas reales con tacones y senos de hormigon in-situ (vanos -400..180 clipped at 0, y 180..760)
    draw_bovedilla_and_senos_2d(cv, -400.0, 180.0, forj_bot, comp_bot, clip_x0=0.0)
    draw_bovedilla_and_senos_2d(cv, 180.0, 760.0, forj_bot, comp_bot)
    # Macizado de hormigon entre vigueta X=760 y zuncho X=840
    mac_pts = [(786.0, comp_bot), (840.0, comp_bot), (840.0, forj_bot),
               (820.0, forj_bot), (820.0, forj_bot + 40.0), (794.0, forj_bot + 43.0), (788.0, forj_bot + 50.0)]
    cv.add_poly("FORJADO", mac_pts, True, fill_hex="#D7DCE0", stroke_hex="#2B3138", lw=0.26)
    cv.add_hatch("HATCH_LIGHT", "concrete", mac_pts, spacing=20.0)

    # 2. Peto de Fabrica (Z: 0..820) con hiladas LHD 140 mm
    peto_top = p["peto_top_z"]
    # Enfoscado interior & exterior
    cv.add_rect("MORTERO", ei_x0, 0.0, ei_x1, peto_top, fill_hex="#DFD8CE")
    cv.add_rect("MORTERO", ee_x0, 0.0, ee_x1, peto_top, fill_hex="#EFE7DA")
    # Albardilla / coronacion del peto
    cv.add_poly("MORTERO", [(ei_x0 - 8, peto_top), (ee_x1 + 8, peto_top), (ee_x1 + 8, peto_top + 38), (ei_x0 - 8, peto_top + 48)],
                True, fill_hex="#D8CFC2", stroke_hex="#1B2026", lw=0.35)
    # Hiladas de ladrillo hueco doble (90 mm alto + 10 mm junta)
    z_cur = 0.0
    brick_h = 90.0
    joint_b = 10.0
    while z_cur + brick_h <= peto_top:
        draw_hollow_brick_section(cv, pb_x0, z_cur, pb_x1, z_cur + brick_h, cols=2, rows=3)
        if z_cur + brick_h + joint_b <= peto_top:
            cv.add_rect("MORTERO", pb_x0, z_cur + brick_h, pb_x1, z_cur + brick_h + joint_b, fill_hex="#CFC9C0", stroke_hex="#5C5852", lw=0.14)
        z_cur += brick_h + joint_b

    # 3. Junta Perimetral EPS (X: 985..1000, desde Z=0 hasta Z_at_top)
    z_eps_top = z_at_top(dx_end)
    cv.add_rect("AISLAMIENTO", j_x0, 0.0, j_x1, z_eps_top, fill_hex="#FBF8EE", stroke_hex="#4A4E54", lw=0.24)
    cv.add_hatch("HATCH_LIGHT", "cross", [(j_x0, 0), (j_x1, 0), (j_x1, z_eps_top), (j_x0, z_eps_top)], spacing=7.0)

    # 4. FP: Formacion de Pendiente (hormigon aligerado + regularizacion)
    fp_poly = [(0, 0), (dx_end, 0), (dx_end, z_fp_core_top(dx_end)), (0, z_fp_core_top(0))]
    cv.add_poly("HORMIGON_CEL", fp_poly, True, fill_hex="#EBE4D8")
    cv.add_hatch("HATCH_LIGHT", "cellular", fp_poly, spacing=13.0)
    reg_poly = [(0, z_fp_core_top(0)), (dx_end, z_fp_core_top(dx_end)), (dx_end, z_fp_top(dx_end)), (0, z_fp_top(0))]
    cv.add_poly("MORTERO", reg_poly, True, fill_hex="#D5CCC0")
    cv.add_hatch("HATCH_LIGHT", "dots", reg_poly, spacing=8.0)

    # 5. BV: Barrera de Vapor (3 mm)
    bv_poly = [(0, z_fp_top(0)), (dx_end, z_fp_top(dx_end)), (dx_end, z_bv_top(dx_end)), (0, z_bv_top(0))]
    cv.add_poly("MEMBRANA", bv_poly, True, fill_hex="#2D3035", stroke_hex="#101214", lw=0.35)

    # 6. AT: Aislamiento Termico XPS (50 mm)
    at_poly = [(0, z_bv_top(0)), (dx_end, z_bv_top(dx_end)), (dx_end, z_at_top(dx_end)), (0, z_at_top(0))]
    cv.add_poly("AISLAMIENTO", at_poly, True, fill_hex="#FAF0B2")
    cv.add_hatch("HATCH_INSUL", "diag45", at_poly, spacing=11.0)

    # 7. I: Impermeabilizacion (4 mm + entrega vertical 200 mm en peto)
    z_turn_top = z_p_top(dx_end) + p["i_turnup_h"]
    i_poly = [
        (0, z_at_top(0)), (dx_end, z_at_top(dx_end)),
        (ei_x0, z_at_top(dx_end)), (ei_x0, z_turn_top),
        (ei_x0 - p["i_h"], z_turn_top), (ei_x0 - p["i_h"], z_i_top(dx_end)),
        (0, z_i_top(0)),
    ]
    cv.add_poly("MEMBRANA", i_poly, True, fill_hex="#1E2024", stroke_hex="#101214", lw=0.45)

    # 8. CS: Capa Separadora Geotextil (2 mm, azul claro)
    cs_x_end = ei_x0 - p["i_h"] - p["junta_perimetral"]
    cs_poly = [(0, z_i_top(0)), (cs_x_end, z_i_top(cs_x_end)), (cs_x_end, z_cs_top(cs_x_end)), (0, z_cs_top(0))]
    cv.add_poly("CAPA_SEP", cs_poly, True, fill_hex="#CFEBF7", stroke_hex="#2D7FA8", lw=0.30)

    # 9. P: Mortero de agarre + Baldosas ceramicas + Junta perimetral + Rodapie
    m_poly = [(0, z_cs_top(0)), (cs_x_end, z_cs_top(cs_x_end)), (cs_x_end, z_m_top(cs_x_end)), (0, z_m_top(0))]
    cv.add_poly("MORTERO", m_poly, True, fill_hex="#CFC7BC")
    cv.add_hatch("HATCH_LIGHT", "dots", m_poly, spacing=9.0)

    # Baldosas P individuales (280 mm + 6 mm junta)
    tx = 12.0
    tl = p["tile_l"]
    tj = p["tile_joint"]
    while tx < cs_x_end - 15.0:
        tx_end = min(tx + tl, cs_x_end)
        t_poly = [(tx, z_m_top(tx)), (tx_end, z_m_top(tx_end)), (tx_end, z_p_top(tx_end)), (tx, z_p_top(tx))]
        cv.add_poly("PAVIMENTO", t_poly, True, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
        cv.add_hatch("HATCH_BRICK", "diag45", t_poly, spacing=7.0)
        tx = tx_end + tj

    # Junta elastica perimetral (10 mm)
    jp_x0 = cs_x_end
    jp_x1 = ei_x0 - p["i_h"]
    cv.add_rect("MEMBRANA", jp_x0, z_i_top(dx_end), jp_x1, z_p_top(dx_end), fill_hex="#4A4F57", stroke_hex="#182028", lw=0.22)

    # Rodapie ceramico vertical sobre la entrega de I
    rod_x1 = ei_x0 - p["i_h"] - 8.0   # 8 mm mortero adhesivo
    rod_x0 = rod_x1 - p["rodapie_t"]
    rod_z0 = z_p_top(dx_end) + 4.0
    rod_z1 = rod_z0 + p["rodapie_h"]
    cv.add_rect("MORTERO", rod_x1, rod_z0, ei_x0 - p["i_h"], rod_z1, fill_hex="#CFC7BC")
    cv.add_rect("PAVIMENTO", rod_x0, rod_z0, rod_x1, rod_z1, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
    cv.add_hatch("HATCH_BRICK", "diag45", [(rod_x0, rod_z0), (rod_x1, rod_z0), (rod_x1, rod_z1), (rod_x0, rod_z1)], spacing=7.0)

    # Remate superior entrega I con sellado elastomerico
    cv.add_poly("METAL_CAZ", [(ei_x0 - 20, rod_z1 + 12), (ei_x0 + 4, rod_z1 + 6), (ei_x0 + 4, rod_z1 + 2), (ei_x0 - 18, rod_z1 + 8)],
                True, fill_hex="#9AA2AA", stroke_hex="#29465B", lw=0.28)

    # Cotas de precision en mm
    cv.add_breakline(0.0, forj_bot, 0.0, z_p_top(0))
    cv.add_dim_h(0.0, dx_end, -325.0, forj_bot, forj_bot, label="985 mm (faldón secc.)")
    cv.add_dim_h(dx_end, ee_x1, -325.0, forj_bot, forj_bot, label="190 mm (peto+junta)")
    cv.add_dim_v(forj_bot, 0.0, -55.0, 0.0, 0.0, label="260")
    cv.add_dim_v(0.0, z_fp_top(0), -55.0, 0.0, 0.0, label="70")
    cv.add_dim_v(z_fp_top(0), z_at_top(0), -55.0, 0.0, 0.0, label="53")
    cv.add_dim_v(z_at_top(0), z_p_top(0), -55.0, 0.0, 0.0, label="46")
    cv.add_dim_v(z_p_top(dx_end), z_turn_top, 1235.0, ee_x1, ei_x0, label="200 (entrega I)")
    cv.add_dim_v(0.0, peto_top, 1300.0, ee_x1, ee_x1, label="820")
    draw_slope_triangle(cv, 150.0, z_p_top(150.0), p["slope"], length=220.0, label="2,5%", dir_x=-1.0)

    # Leyenda tecnica Cartillas IVE (sin cruces ni solapes)
    cv.add_leader((190.0, 0.5 * (z_m_top(190) + z_p_top(190))), (130.0, 560.0), (-20.0, 560.0),
                  "P · PAVIMENTO FIJO (20 + 20 mm)", "Baldosa cerámica 280×140×20 mm + agarre", align="right")
    cv.add_leader((280.0, 0.5 * (z_i_top(280) + z_cs_top(280))), (215.0, 490.0), (-20.0, 490.0),
                  "CS · CAPA SEPARADORA (2 mm)", "Geotextil polipropileno 150 g/m²", align="right")
    cv.add_leader((370.0, 0.5 * (z_at_top(370) + z_i_top(370))), (305.0, 420.0), (-20.0, 420.0),
                  "I · IMPERMEABILIZACIÓN (4 mm)", "Lámina LBM-40-FP + entrega 200 mm", align="right")
    cv.add_leader((460.0, 0.5 * (z_bv_top(460) + z_at_top(460))), (395.0, 350.0), (-20.0, 350.0),
                  "AT · AISLAMIENTO TÉRMICO (50 mm)", "Poliestireno extruido XPS 300 kPa", align="right")
    cv.add_leader((555.0, 0.5 * (z_fp_top(555) + z_bv_top(555))), (485.0, 280.0), (-20.0, 280.0),
                  "BV · BARRERA DE VAPOR (3 mm)", "Lámina oxiasfalto s/ pendiente", align="right")
    cv.add_leader((650.0, 40.0), (575.0, 210.0), (-20.0, 210.0),
                  "FP · FORMACIÓN PENDIENTE (2,5%)", "Hormigón arlita + mortero reg. 15 mm", align="right")
    cv.add_leader((760.0, -140.0), (160.0, -340.0), (-20.0, -340.0),
                  "SR · SOPORTE RESISTENTE (260 mm)", "Forjado unidireccional (vigueta + bovedilla)", align="right")
    cv.add_leader((1085.0, 745.0), (960.0, 810.0), (920.0, 810.0),
                  "PETO LHD 140 mm + ENFOSCADO", "Junta EPS 15 mm + rodapié 200 mm", align="right")

    cv.export_dxf(r"d:\C2\planos_2d\detalle1_ive_peto.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle1_ive_peto.pdf", r"d:\C2\planos_2d\detalle1_ive_peto.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle1_ive_peto.svg")
    print("Generated Detalle 1 2D CAD.")


# ==============================================================================
# DETALLE 2A: NTE QAT-16 - Encuentro con Cazoleta
# ==============================================================================
def build_detalle2_qat16_2d():
    meta = DETAILS["detalle2_qat16"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(170.0, 145.0))

    pit_in = p["pit_inner_half"]          # 110
    ptl_out = pit_in + p["ptl7_wall_t"]   # 160
    ptl_h = p["ptl7_h"]                   # 120
    slope = p["slope"]                    # 0.05
    x_max = 840.0
    x_min = -280.0

    def z_faldon_top(x): return ptl_h + slope * max(0.0, x - ptl_out)
    def z_reg_top(x): return z_faldon_top(x) + p["reg_mortar_h"]
    def z_mem_top(x): return z_reg_top(x) + p["mem_sup_h"]
    def z_ag_top(x): return z_mem_top(x) + p["agarre_h"]
    def z_ras_top(x): return z_ag_top(x) + p["rasilla_h"]

    # 1. Forjado estructural (Z: -250..0) con paso central para bajante (Ø126)
    hole_r = 63.0
    forj_bot = -p["forjado_h"]
    cv.add_rect("FORJADO", x_min, forj_bot, -hole_r, 0.0, fill_hex="#E2E6E9")
    cv.add_hatch("HATCH_LIGHT", "concrete", [(x_min, forj_bot), (-hole_r, forj_bot), (-hole_r, 0), (x_min, 0)], spacing=22.0)
    cv.add_rect("FORJADO", hole_r, forj_bot, x_max, 0.0, fill_hex="#E2E6E9")
    cv.add_hatch("HATCH_LIGHT", "concrete", [(hole_r, forj_bot), (x_max, forj_bot), (x_max, 0), (hole_r, 0)], spacing=22.0)

    # 2. Bajante PVC Ø110 con copa superior (Z: -260..0)
    br = p["bajante_od"] * 0.5
    bw = p["bajante_wall"]
    copa_r = br + 4.5
    for sx in (-1, 1):
        pipe_pts = [
            (sx * (br - bw), -270.0), (sx * br, -270.0), (sx * br, -55.0),
            (sx * copa_r, -42.0), (sx * copa_r, 0.0), (sx * (copa_r - bw), 0.0),
            (sx * (copa_r - bw), -42.0), (sx * (br - bw), -55.0)
        ]
        cv.add_poly("FONTANERIA", pipe_pts, True, fill_hex="#B7C2CC", stroke_hex="#29465B", lw=0.34)

    # 3. Caja PTL-7 de ladrillo hueco sencillo (ambos lados de cazoleta X: +-110..+-160, Z: 0..120)
    for sx in (-1, 1):
        bx0, bx1 = sorted((sx * pit_in, sx * ptl_out))
        draw_hollow_brick_section(cv, bx0, 0.0, bx1, ptl_h, cols=1, rows=3)
    # Mortero asiento en fondo de caja (Z: 0..24 fuera de bajante)
    cv.add_poly("MORTERO", [(-pit_in, 0), (-br, 0), (-br, 24), (-pit_in, 24)], True, fill_hex="#D5CCC0")
    cv.add_poly("MORTERO", [(br, 0), (pit_in, 0), (pit_in, 24), (br, 24)], True, fill_hex="#D5CCC0")
    cv.add_hatch("HATCH_LIGHT", "dots", [(-pit_in, 0), (-br, 0), (-br, 24), (-pit_in, 24)], spacing=6.0)
    cv.add_hatch("HATCH_LIGHT", "dots", [(br, 0), (pit_in, 0), (pit_in, 24), (br, 24)], spacing=6.0)

    # 4. Faldon de hormigon aligerado (derecha X: 160..840)
    fal_poly = [(ptl_out, 0), (x_max, 0), (x_max, z_faldon_top(x_max)), (ptl_out, z_faldon_top(ptl_out))]
    cv.add_poly("HORMIGON_CEL", fal_poly, True, fill_hex="#EBE4D8")
    cv.add_hatch("HATCH_LIGHT", "cellular", fal_poly, spacing=15.0)

    # 5. Mortero de regularizacion 1:6 sobre faldon y puente sobre PTL-7
    reg_poly = [(pit_in + 12, ptl_h), (ptl_out, ptl_h), (x_max, z_faldon_top(x_max)),
                (x_max, z_reg_top(x_max)), (ptl_out, z_reg_top(ptl_out)), (pit_in + 12, z_reg_top(ptl_out))]
    cv.add_poly("MORTERO", reg_poly, True, fill_hex="#D5CCC0")
    cv.add_hatch("HATCH_LIGHT", "dots", reg_poly, spacing=8.0)

    # 6. QAT-10 Membrana inferior penetrando hasta la bajante
    for sx in (-1, 1):
        m_inf = [
            (sx * (pit_in + 35), ptl_h + 15.0),
            (sx * pit_in, ptl_h + 15.0),
            (sx * pit_in, 24.0),
            (sx * (br - 6.0), 24.0),
            (sx * (br - 6.0), -42.0),
            (sx * (br - 10.0), -42.0),
            (sx * (br - 10.0), 28.0),
            (sx * (pit_in - 4.0), 28.0),
            (sx * (pit_in - 4.0), ptl_h + 19.0),
            (sx * (pit_in + 35), ptl_h + 19.0),
        ]
        cv.add_poly("MEMBRANA", m_inf, True, fill_hex="#181A1E", stroke_hex="#101214", lw=0.40)

    # 7. Cazoleta metalica + rejilla + babero izquierdo
    caz_h = p["cazoleta_outer_half"]      # 102
    fl_w = p["cazoleta_flange_w"]         # 36
    caz_top = z_reg_top(ptl_out) + 5.0    # 140
    caz_bot = 28.0
    caz_pts = [
        (-caz_h - fl_w, caz_top), (-caz_h, caz_top), (-caz_h, caz_bot),
        (-48.0, caz_bot), (-48.0, -35.0), (-44.0, -35.0), (-44.0, caz_bot + 3.0),
        (-caz_h + 3.5, caz_bot + 3.0), (-caz_h + 3.5, caz_top + 3.0), (-caz_h - fl_w, caz_top + 3.0)
    ]
    cv.add_poly("METAL_CAZ", caz_pts, True, fill_hex="#9AA5AE", stroke_hex="#29465B", lw=0.32)
    caz_pts_r = [(-x, z) for (x, z) in caz_pts]
    cv.add_poly("METAL_CAZ", caz_pts_r, True, fill_hex="#9AA5AE", stroke_hex="#29465B", lw=0.32)

    # Rejilla ranurada en boca de cazoleta
    cv.add_rect("METAL_CAZ", -caz_h, caz_top - 4.0, caz_h, caz_top + 6.0, fill_hex="#73808A", stroke_hex="#1B2026", lw=0.32)
    for gx in range(-84, 85, 24):
        cv.add_rect("METAL_CAZ", gx - 6.0, caz_top - 4.0, gx + 6.0, caz_top + 6.0, fill_hex="#FFFFFF", stroke_hex="#1B2026", lw=0.20)

    # Babero / remate lateral izquierdo QAT-16
    cv.add_poly("METAL_CAZ", [(-280, caz_top + 24), (-caz_h - 6, caz_top + 6), (-caz_h - 6, caz_top + 3), (-280, caz_top + 21)],
                True, fill_hex="#A4AFB8", stroke_hex="#29465B", lw=0.30)

    # 8. QAT-10 Membrana superior con SOLAPE DE 100 mm (10 cm) sobre ala de cazoleta
    sol_x0 = caz_h + 2.0                  # inicia sobre ala cazoleta (+104) -> solape 100 mm hasta +204
    m_sup = [
        (sol_x0, caz_top + 4.0), (ptl_out, z_reg_top(ptl_out)), (x_max, z_reg_top(x_max)),
        (x_max, z_mem_top(x_max)), (ptl_out, z_mem_top(ptl_out)), (sol_x0, caz_top + 8.0)
    ]
    cv.add_poly("MEMBRANA", m_sup, True, fill_hex="#181A1E", stroke_hex="#101214", lw=0.45)

    # 9. Mortero de agarre + Rasilla ceramica con vuelo goteron sobre borde de caja
    x_tile_start = caz_h + 36.0           # 138
    ag_poly = [
        (x_tile_start + 12, z_mem_top(ptl_out)), (x_max, z_mem_top(x_max)),
        (x_max, z_ag_top(x_max)), (x_tile_start + 12, z_ag_top(ptl_out))
    ]
    cv.add_poly("MORTERO", ag_poly, True, fill_hex="#CFC7BC")
    cv.add_hatch("HATCH_LIGHT", "dots", ag_poly, spacing=8.0)

    tx = x_tile_start
    while tx < x_max - 15.0:
        tx_end = min(tx + p["rasilla_l"], x_max)
        t_poly = [(tx, z_ag_top(max(tx, ptl_out))), (tx_end, z_ag_top(tx_end)),
                  (tx_end, z_ras_top(tx_end)), (tx, z_ras_top(max(tx, ptl_out)))]
        cv.add_poly("PAVIMENTO", t_poly, True, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
        cv.add_hatch("HATCH_BRICK", "diag45", t_poly, spacing=7.0)
        tx = tx_end + p["rasilla_joint"]

    # Flujo de agua azul
    cv.add_flow_arrow([(-45, caz_top + 55), (-45, caz_top + 8), (-20, 45), (-12, -160)], lw=0.30, head_mm=12.0)
    cv.add_flow_arrow([(135, z_ras_top(ptl_out) + 18), (65, caz_top + 22), (45, caz_top + 2)], lw=0.30, head_mm=12.0)

    # Cotas y textos NTE QAT-16
    cv.add_dim_h(caz_h + 2.0, caz_h + 102.0, 225.0, caz_top + 8.0, z_mem_top(204), label="SOLAPE 100 mm (10 cm)")
    cv.add_dim_h(-pit_in, pit_in, -310.0, 0.0, 0.0, label="220 (caja PTL-7)")
    cv.add_dim_h(-br, br, -355.0, -270.0, -270.0, label="Ø110")
    cv.add_dim_v(forj_bot, 0.0, -315.0, x_min, x_min, label="250")
    cv.add_dim_v(0.0, ptl_h, -315.0, -ptl_out, -ptl_out, label="120")
    draw_slope_triangle(cv, 460.0, z_ras_top(460.0), slope, length=200.0, label="5,0%", dir_x=-1.0)

    # Llamadas NTE
    cv.add_leader((-caz_h - 15, caz_top + 2.0), (-230, 265), (-370, 265),
                  "QAT-10 · MEMBRANA IMPERMEABILIZANTE", "Penetra en bajante + solape 100 mm sobre cazoleta", align="right")
    cv.add_leader((-135, 65), (-240, 65), (-370, 65),
                  "PTL-7 · CAJA LADRILLO HUECO SENCILLO", "Tabique LHS 40 mm recibido con mortero 1:6", align="right")
    cv.add_leader((480, 60), (540, -310), (590, -310),
                  "FALDÓN HORMIGÓN ALIGERADO (5%)", "Sobre forjado estructural de 250 mm", align="left")
    cv.add_leader((460, z_ag_top(460) + 10), (490, 315), (560, 315),
                  "RASILLA CERÁMICA + MORTERO 1:8", "Regularización mortero 1:6 bajo membrana", align="left")

    cv.add_text("NOTES", 440.0, 465.0, "NOTA NTE QAT-10: No realizar impermeabilización con lluvia o T < +5 °C.", height_sheet_mm=2.15, align="left")

    cv.export_dxf(r"d:\C2\planos_2d\detalle2_nte_qat16_cazoleta.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle2_nte_qat16_cazoleta.pdf", r"d:\C2\planos_2d\detalle2_nte_qat16_cazoleta.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle2_nte_qat16_cazoleta.svg")
    print("Generated Detalle 2A (QAT-16) 2D CAD.")


# ==============================================================================
# DETALLE 2B: NTE QAT-17 - Canalon en Faldon de Hormigon Aligerado-S
# ==============================================================================
def build_detalle2_qat17_2d():
    meta = DETAILS["detalle2_qat17"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(135.0, 96.0))

    wall_x0 = -p["wall_t"]               # -240
    wall_top = p["wall_top_z"]            # 640
    forj_bot = -p["forjado_h"]            # -250
    roza_s = p["roza_size"]               # 50
    roza_z0 = p["roza_bot_z"]             # 485
    roza_z1 = roza_z0 + roza_s            # 535
    ptl7_x0 = p["ptl7_x0"]                # 200
    ptl7_x1 = ptl7_x0 + p["ptl7_t"]       # 250
    ptl7_h = p["ptl7_h"]                  # 135
    x_max = 940.0
    slope = p["slope"]                    # 0.05

    def z_fal_top(x): return ptl7_h + slope * max(0.0, x - ptl7_x1)
    def z_reg_top(x): return z_fal_top(x) + p["reg_mortar_h"]
    def z_mem_top(x): return z_reg_top(x) + p["mem_h"]
    def z_ag_top(x): return z_mem_top(x) + p["agarre_h"]
    def z_ras_top(x): return z_ag_top(x) + p["rasilla_h"]

    # 1. Forjado estructural (X: -240..940, Z: -250..0)
    cv.add_rect("FORJADO", wall_x0, forj_bot, x_max, 0.0, fill_hex="#E2E6E9")
    cv.add_hatch("HATCH_LIGHT", "concrete", [(wall_x0, forj_bot), (x_max, forj_bot), (x_max, 0), (wall_x0, 0)], spacing=22.0)

    # 2. Muro de fabrica de ladrillo con ROZA PTL-2 (50x50 mm en X: -50..0, Z: 485..535)
    wall_poly = [
        (wall_x0, 0.0), (0.0, 0.0), (0.0, roza_z0), (-roza_s, roza_z0),
        (-roza_s, roza_z1), (0.0, roza_z1), (0.0, wall_top), (wall_x0, wall_top)
    ]
    cv.add_poly("LADRILLO", wall_poly, True, fill_hex="#F7E4DC", stroke_hex="#7D3723", lw=0.34)
    cv.add_hatch("HATCH_BRICK", "horiz_masonry", wall_poly, spacing=12.0)

    # 3. RPE-3 Mortero 1:8 bajo el canalon (X: 0..200, Z: 0..20)
    rpe_h = p["rpe3_h"]
    cv.add_rect("MORTERO", 0.0, 0.0, ptl7_x0, rpe_h, fill_hex="#D5CCC0")
    cv.add_hatch("HATCH_LIGHT", "dots", [(0, 0), (ptl7_x0, 0), (ptl7_x0, rpe_h), (0, rpe_h)], spacing=7.0)

    # 4. PTL-7 Maestra de ladrillo hueco sencillo (X: 200..250, Z: 0..135)
    draw_hollow_brick_section(cv, ptl7_x0, 0.0, ptl7_x1, ptl7_h, cols=1, rows=3)

    # 5. Faldon de hormigon aligerado (X: 250..940)
    fal_poly = [(ptl7_x1, 0), (x_max, 0), (x_max, z_fal_top(x_max)), (ptl7_x1, ptl7_h)]
    cv.add_poly("HORMIGON_CEL", fal_poly, True, fill_hex="#EBE4D8")
    cv.add_hatch("HATCH_LIGHT", "cellular", fal_poly, spacing=15.0)

    # 6. Mortero regularizacion 1:6 sobre faldon y PTL-7
    reg_poly = [(ptl7_x0, ptl7_h), (ptl7_x1, ptl7_h), (x_max, z_fal_top(x_max)),
                (x_max, z_reg_top(x_max)), (ptl7_x1, z_reg_top(ptl7_x1)), (ptl7_x0, z_reg_top(ptl7_x1))]
    cv.add_poly("MORTERO", reg_poly, True, fill_hex="#D5CCC0")
    cv.add_hatch("HATCH_LIGHT", "dots", reg_poly, spacing=8.0)

    # 7. QAT-2 Canalon de cinc plegado (roza PTL-2 -> pared vertical 350 mm -> fondo achaflanado -> maestra PTL-7 -> ala 120 mm)
    ch = p["gutter_chamfer"]  # 25
    fl_end = ptl7_x0 + p["zinc_flange_w"]  # 320
    z_ala = z_reg_top(ptl7_x1) + 1.5
    zinc_pts = [
        (-38.0, roza_z0 + 30.0), (2.0, roza_z0), (2.0, rpe_h + ch),
        (2.0 + ch, rpe_h), (ptl7_x0 - ch - 2.0, rpe_h), (ptl7_x0 - 2.0, rpe_h + ch),
        (ptl7_x0 - 2.0, z_ala), (fl_end, z_ala)
    ]
    cv.add_poly("METAL_CAZ", zinc_pts, False, stroke_hex="#1B394F", lw=0.55)
    # Mortero sellado dentro de roza PTL-2
    cv.add_poly("MORTERO", [(-roza_s, roza_z0), (0, roza_z0), (-38, roza_z0 + 30), (-roza_s, roza_z0 + 30)], True, fill_hex="#CFC7BC")

    # 8. Membrana impermeabilizante con SOLAPE MINIMO 10 cm (100 mm) sobre el canalon
    sol_x0 = fl_end - p["solape_mm"]      # 220 (sobre 220..320 = 100 mm)
    mem_poly = [
        (sol_x0, z_ala + 1.0), (ptl7_x1, z_ala + 1.0), (x_max, z_reg_top(x_max)),
        (x_max, z_mem_top(x_max)), (ptl7_x1, z_mem_top(ptl7_x1)), (sol_x0, z_ala + 5.0)
    ]
    cv.add_poly("MEMBRANA", mem_poly, True, fill_hex="#181A1E", stroke_hex="#101214", lw=0.45)

    # 9. Mortero agarre + Rasilla con vuelo 20 mm sobre canalon
    tile_start = ptl7_x0 - p["rasilla_overhang"]  # 180
    ag_poly = [
        (ptl7_x0 + 8.0, z_mem_top(ptl7_x1)), (x_max, z_mem_top(x_max)),
        (x_max, z_ag_top(x_max)), (ptl7_x0 + 8.0, z_ag_top(ptl7_x1))
    ]
    cv.add_poly("MORTERO", ag_poly, True, fill_hex="#CFC7BC")
    cv.add_hatch("HATCH_LIGHT", "dots", ag_poly, spacing=8.0)

    tx = tile_start
    while tx < x_max - 15.0:
        tx_end = min(tx + p["rasilla_l"], x_max)
        z_b0 = z_ag_top(max(tx, ptl7_x1))
        z_b1 = z_ag_top(tx_end)
        t_poly = [(tx, z_b0), (tx_end, z_b1), (tx_end, z_b1 + p["rasilla_h"]), (tx, z_b0 + p["rasilla_h"])]
        cv.add_poly("PAVIMENTO", t_poly, True, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
        cv.add_hatch("HATCH_BRICK", "diag45", t_poly, spacing=7.0)
        tx = tx_end + p["rasilla_joint"]

    # Cotas exactas NTE QAT-17
    cv.add_dim_v(ptl7_h, roza_z0, 72.0, 2.0, 2.0, label="350 (35 cm)")
    cv.add_dim_h(0.0, ptl7_x0, -310.0, 0.0, 0.0, label="200 (luz canalón)")
    cv.add_dim_h(sol_x0, fl_end, 265.0, z_ala, z_ala, label="SOLAPE ≥ 100 mm")
    cv.add_dim_v(forj_bot, 0.0, -310.0, wall_x0, wall_x0, label="250")
    cv.add_dim_v(roza_z0, roza_z1, -310.0, wall_x0, wall_x0, label="50 (5 cm)")
    draw_slope_triangle(cv, 500.0, z_ras_top(500.0), slope, length=210.0, label="5,0%", dir_x=-1.0)

    # Llamadas NTE QAT-17
    cv.add_leader((-25, 0.5 * (roza_z0 + roza_z1)), (-280, 560), (-360, 560),
                  "PTL-2 · ROZA 5×5 cm (50×50 mm)", "Para recibido y sellado del canalón de cinc", align="right")
    cv.add_leader((2.0, 220.0), (-280, 260), (-360, 260),
                  "QAT-2 · CANALÓN DE CINC", "Solape mínimo membrana 10 cm sobre ala", align="right")
    cv.add_leader((100.0, 10.0), (-280, 95), (-360, 95),
                  "RPE-3 · MORTERO ASIENTO (1:8)", "Mortero cemento y arena de río 20 mm", align="right")
    cv.add_leader((225.0, 55.0), (265, -285), (320, -285),
                  "PTL-7 · MAESTRA LADRILLO HUECO", "LHS 40 mm recibido con mortero 1:6", align="left")
    cv.add_leader((720.0, 80.0), (760, 290), (800, 290),
                  "FALDÓN HORMIGÓN ALIGERADO (5%)", "Regularización 1:6 + rasilla vuelo 20 mm", align="left")

    cv.export_dxf(r"d:\C2\planos_2d\detalle2_nte_qat17_canalon.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle2_nte_qat17_canalon.pdf", r"d:\C2\planos_2d\detalle2_nte_qat17_canalon.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle2_nte_qat17_canalon.svg")
    print("Generated Detalle 2B (QAT-17) 2D CAD.")


# ==============================================================================
# DETALLE 3: Analisis Detalle - Azotea Transitable con Hormigon Celular - Cazoleta Sifonica
# ==============================================================================
def build_detalle3_2d():
    meta = DETAILS["detalle3"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(224.0, 185.0))

    hx = p["span_half_x"]                 # 750
    forj_bot = -p["forjado_h"]            # -250
    rev_h = p["revest_h"]                 # 15
    hole_r = p["slab_hole_r"]             # 84
    br = p["bajante_od"] * 0.5            # 55
    bw = p["bajante_wall"]                # 3.2
    copa_r = p["copa_od"] * 0.5           # 59
    fib_r = br + p["fibra_t"]             # 80
    fal_in = p["falseado_inner_half"]     # 100
    fal_out = fal_in + p["falseado_brick_t"]  # 140
    fal_bot = p["falseado_bot_z"]         # -600
    bv_h = p["bv_h"]                      # 3
    pit_in = p["pit_inner_half"]          # 125
    pit_out = pit_in + p["pit_brick_t"]   # 195
    pit_top = bv_h + p["pit_brick_h"]     # 118
    slope = p["slope"]                    # 0.03

    def z_hc_top(ax): return pit_top + slope * max(0.0, abs(ax) - pit_out)
    def z_m16_top(ax): return z_hc_top(ax) + p["mortero16_h"]    # 136 en pit
    def z_mem_top(ax): return z_m16_top(ax) + p["membrana_h"]     # 140 en pit
    def z_m18_top(ax): return z_mem_top(ax) + p["mortero18_h"] + 7.0  # 162 en borde rejilla
    def z_ras_top(ax): return z_m18_top(ax) + p["rasilla_h"]      # 182 en borde rejilla

    # 1. Forjado estructural (izquierda y derecha del paso Ø168 mm)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hole_r, sx * hx))
        cv.add_rect("FORJADO", x0, forj_bot, x1, 0.0, fill_hex="#E2E6E9")
        cv.add_hatch("HATCH_LIGHT", "concrete", [(x0, forj_bot), (x1, forj_bot), (x1, 0), (x0, 0)], spacing=24.0)

    # 2. Revestimiento inferior (15 mm bajo forjado y cara exterior del falseado Ladrillo del 4)
    for sx in (-1, 1):
        rev_pts = [
            (sx * hx, forj_bot), (sx * fal_out, forj_bot), (sx * fal_out, fal_bot),
            (sx * (fal_out + rev_h), fal_bot), (sx * (fal_out + rev_h), forj_bot - rev_h), (sx * hx, forj_bot - rev_h)
        ]
        cv.add_poly("REVESTIMIENTO", rev_pts, True, fill_hex="#F7DFDD", stroke_hex="#9E2A22", lw=0.28)
        cv.add_hatch("HATCH_REV", "diag45", rev_pts, spacing=9.0)

    # 3. Falseado Ladrillo del 4 (tabique hueco 40 mm en X: +-100..+-140, Z: -600..-250)
    for sx in (-1, 1):
        bx0, bx1 = sorted((sx * fal_in, sx * fal_out))
        z_c = fal_bot + 10.0
        while z_c + 105.0 <= forj_bot + 5.0:
            draw_hollow_brick_section(cv, bx0, z_c, bx1, min(z_c + 105.0, forj_bot), cols=1, rows=2)
            z_c += 115.0

    # 4. Bajante PVC Ø110 mm con copa superior (Z: -600..0)
    for sx in (-1, 1):
        pipe_pts = [
            (sx * (br - bw), fal_bot), (sx * br, fal_bot), (sx * br, -55.0),
            (sx * copa_r, -42.0), (sx * copa_r, 0.0), (sx * (copa_r - bw), 0.0),
            (sx * (copa_r - bw), -42.0), (sx * (br - bw), -55.0)
        ]
        cv.add_poly("FONTANERIA", pipe_pts, True, fill_hex="#B7C2CC", stroke_hex="#29465B", lw=0.34)

    # 5. Manta Fibra de Vidrio (25 mm alrededor de bajante en forjado y patinillo)
    for sx in (-1, 1):
        f_pts = [(sx * (br + 1.0), fal_bot), (sx * fib_r, fal_bot), (sx * fib_r, -2.0), (sx * (copa_r + 1.0), -2.0),
                 (sx * (copa_r + 1.0), -44.0), (sx * (br + 1.0), -57.0)]
        f_pts_ord = [(min(p[0] for p in f_pts), fal_bot), (max(p[0] for p in f_pts), fal_bot),
                     (max(p[0] for p in f_pts), -2.0), (min(p[0] for p in f_pts), -2.0)]
        # Dibujar silueta exacta siguiendo la copa
        cv.add_poly("AISLAMIENTO", f_pts, True, fill_hex="#FFF5D6", stroke_hex="#C98512", lw=0.22)
        cv.add_hatch("HATCH_INSUL", "zigzag_v", [(min(sx * (copa_r + 1), sx * fib_r), fal_bot),
                                                 (max(sx * (copa_r + 1), sx * fib_r), fal_bot),
                                                 (max(sx * (copa_r + 1), sx * fib_r), -4.0),
                                                 (min(sx * (copa_r + 1), sx * fib_r), -4.0)], spacing=9.0)

    # 6. Barrera Cortavapor (3 mm sobre forjado Z: 0..3)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * hole_r, sx * hx))
        cv.add_rect("MEMBRANA", x0, 0.0, x1, bv_h, fill_hex="#2B2E33", stroke_hex="#101214", lw=0.36)

    # 7. Caja de ladrillo hueco alrededor de cazoleta (LHD 70x115 mm, 2x4 celdas huecas, Z: 3..118)
    for sx in (-1, 1):
        bx0, bx1 = sorted((sx * pit_in, sx * pit_out))
        draw_hollow_brick_section(cv, bx0, bv_h, bx1, pit_top, cols=2, rows=4)
    # Mortero asiento fondo cazoleta (Z: 3..35)
    for sx in (-1, 1):
        mx0, mx1 = sorted((sx * (copa_r + 2.0), sx * pit_in))
        cv.add_rect("MORTERO", mx0, bv_h, mx1, p["caz_bot_z"], fill_hex="#D5CCC0")
        cv.add_hatch("HATCH_LIGHT", "dots", [(mx0, bv_h), (mx1, bv_h), (mx1, p["caz_bot_z"]), (mx0, p["caz_bot_z"])], spacing=6.0)

    # 8. Hormigon Celular con pendiente 3% (|X|: 195..750)
    for sx in (-1, 1):
        p0, p1 = sx * pit_out, sx * hx
        hc_poly = [(p0, bv_h), (p1, bv_h), (p1, z_hc_top(hx)), (p0, pit_top)]
        if sx < 0:
            hc_poly = [(p1, bv_h), (p0, bv_h), (p0, pit_top), (p1, z_hc_top(hx))]
        cv.add_poly("HORMIGON_CEL", hc_poly, True, fill_hex="#EBE4D8")
        cv.add_hatch("HATCH_LIGHT", "cellular", hc_poly, spacing=15.0)

    # 9. Mortero 1:6 (Regularizacion sobre Hormigon Celular y puente sobre caja LHD)
    for sx in (-1, 1):
        x_in = sx * pit_in
        x_mid = sx * pit_out
        x_out = sx * hx
        m16_poly = [
            (x_in, pit_top), (x_mid, pit_top), (x_out, z_hc_top(hx)),
            (x_out, z_m16_top(hx)), (x_mid, z_m16_top(pit_out)), (x_in, z_m16_top(pit_out))
        ]
        if sx < 0:
            m16_poly = list(reversed(m16_poly))
        cv.add_poly("MORTERO", m16_poly, True, fill_hex="#D5CCC0")
        cv.add_hatch("HATCH_LIGHT", "dots", m16_poly, spacing=8.0)

    # 10. Refuerzo Membrana (llega hasta la embocadura de la bajante) + Membrana Principal (solape 100 mm)
    ref_ext = pit_out + p["refuerzo_ext_w"]  # 435
    caz_h = p["caz_outer_half"]              # 120
    caz_bot = p["caz_bot_z"]                 # 35
    caz_fl = p["caz_flange_z"]               # 139
    tail_bot = p["tail_bot_z"]               # -45
    weir_r = p["weir_id"] * 0.5              # 52

    for sx in (-1, 1):
        # Refuerzo membrana inferior
        ref_pts = [
            (sx * ref_ext, z_m16_top(ref_ext)),
            (sx * pit_out, z_m16_top(pit_out)),
            (sx * pit_in, z_m16_top(pit_out)),
            (sx * pit_in, caz_bot),
            (sx * (weir_r + 3.0), caz_bot),
            (sx * (weir_r + 3.0), tail_bot),
            (sx * (weir_r - 1.0), tail_bot),
            (sx * (weir_r - 1.0), caz_bot + 4.0),
            (sx * (pit_in - 4.0), caz_bot + 4.0),
            (sx * (pit_in - 4.0), z_m16_top(pit_out) + 4.0),
            (sx * pit_out, z_m16_top(pit_out) + 4.0),
            (sx * ref_ext, z_m16_top(ref_ext) + 4.0),
        ]
        cv.add_poly("MEMBRANA", ref_pts, True, fill_hex="#181A1E", stroke_hex="#101214", lw=0.40)

        # Membrana impermeabilizante principal (solapando 100 mm sobre ala cazoleta / refuerzo)
        sol_start = caz_h + 6.0              # +126 -> solape hasta +226 (100 mm)
        mem_pts = [
            (sx * sol_start, caz_fl + 5.0),
            (sx * pit_out, z_m16_top(pit_out) + 5.0),
            (sx * hx, z_m16_top(hx)),
            (sx * hx, z_mem_top(hx)),
            (sx * pit_out, z_m16_top(pit_out) + 9.0),
            (sx * sol_start, caz_fl + 9.0),
        ]
        cv.add_poly("MEMBRANA", mem_pts, True, fill_hex="#23262B", stroke_hex="#101214", lw=0.45)

    # 11. Cazoleta Sifonica + Agua (sello hidraulico) + Campana Sifonica + Rejilla
    weir_top = p["weir_top_z"]               # 98
    bell_r = p["bell_od"] * 0.5              # 82
    bell_bot = p["bell_skirt_z"]             # 65 (sumergida 33 mm)
    bell_dome = p["bell_dome_z"]             # 126
    rej_out = p["rejilla_outer_half"]        # 124
    rej_in = p["rejilla_inner_half"]         # 109
    rej_top = p["rejilla_top_z"]             # 182
    rej_t = p["rejilla_t"]                   # 10

    # Agua dentro del sifon (Z: 38..98 entre pared cazoleta y rebosadero)
    for sx in (-1, 1):
        wx0, wx1 = sorted((sx * (weir_r + 3.0), sx * (caz_h - 3.0)))
        cv.add_rect("AGUA_FLUJO", wx0, caz_bot + 3.0, wx1, weir_top, fill_hex="#E2F3FC", stroke_hex="#0B72B9", lw=0.22)
        cv.add_line("AGUA_FLUJO", wx0, weir_top, wx1, weir_top, color_hex="#0B72B9", lw=0.32, dash=[2.5, 1.5])

    # Cubeta exterior + ala + tubo rebosadero central
    for sx in (-1, 1):
        body_pts = [
            (sx * (caz_h + p["caz_flange_w"]), caz_fl),
            (sx * caz_h, caz_fl),
            (sx * caz_h, caz_bot),
            (sx * weir_r, caz_bot),
            (sx * weir_r, tail_bot),
            (sx * (weir_r + 3.0), tail_bot),
            (sx * (weir_r + 3.0), weir_top),
            (sx * weir_r, weir_top),
            (sx * weir_r, caz_bot + 3.0),
            (sx * (caz_h - 3.0), caz_bot + 3.0),
            (sx * (caz_h - 3.0), caz_fl + 3.0),
            (sx * (caz_h + p["caz_flange_w"]), caz_fl + 3.0),
        ]
        cv.add_poly("METAL_CAZ", body_pts, True, fill_hex="#9AA5AE", stroke_hex="#29465B", lw=0.34)

    # Campana sifonica acampanada + vastago central roscado
    bell_pts = [
        (-bell_r, bell_bot), (-bell_r + 4.0, bell_bot), (-bell_r + 4.0, bell_dome - 14.0),
        (-36.0, bell_dome), (36.0, bell_dome), (bell_r - 4.0, bell_dome - 14.0),
        (bell_r - 4.0, bell_bot), (bell_r, bell_bot), (bell_r, bell_dome - 10.0),
        (38.0, bell_dome + 4.0), (11.0, bell_dome + 4.0), (11.0, rej_top - rej_t),
        (-11.0, rej_top - rej_t), (-11.0, bell_dome + 4.0), (-38.0, bell_dome + 4.0),
        (-bell_r, bell_dome - 10.0)
    ]
    cv.add_poly("METAL_CAZ", bell_pts, True, fill_hex="#7F8C96", stroke_hex="#1B2026", lw=0.36)

    # Marco perimetral y Rejilla ranurada + tornillo central
    for sx in (-1, 1):
        fx0, fx1 = sorted((sx * rej_in, sx * rej_out))
        cv.add_rect("METAL_CAZ", fx0, rej_top - 22.0, fx1, rej_top, fill_hex="#68747E", stroke_hex="#1B2026", lw=0.34)
    cv.add_rect("METAL_CAZ", -rej_in, rej_top - rej_t, rej_in, rej_top, fill_hex="#8E9AA4", stroke_hex="#1B2026", lw=0.34)
    for gx in range(-92, 93, 22):
        if abs(gx) < 12:
            continue
        cv.add_rect("METAL_CAZ", gx - 5.5, rej_top - rej_t, gx + 5.5, rej_top, fill_hex="#FFFFFF", stroke_hex="#1B2026", lw=0.22)
    # Tornillo central
    cv.add_rect("METAL_CAZ", -5.0, rej_top - 24.0, 5.0, rej_top + 2.0, fill_hex="#3E4852", stroke_hex="#1B2026", lw=0.30)

    # 12. Mortero de agarre 1:8 + Rasilla de Aspe a ambos lados
    for sx in (-1, 1):
        x_edge = sx * rej_out
        x_end = sx * hx
        ag_pts = [
            (x_edge, z_mem_top(pit_out) + 5.0),
            (x_end, z_mem_top(hx)),
            (x_end, z_m18_top(hx)),
            (x_edge, z_m18_top(rej_out)),
        ]
        if sx < 0:
            ag_pts = list(reversed(ag_pts))
        cv.add_poly("MORTERO", ag_pts, True, fill_hex="#CFC7BC")
        cv.add_hatch("HATCH_LIGHT", "dots", ag_pts, spacing=8.0)

        # Rasillas individuales saliendo desde ±rej_out
        cur = rej_out + 4.0
        while cur < hx - 10.0:
            nxt = min(cur + p["rasilla_l"], hx)
            x0, x1 = sorted((sx * cur, sx * nxt))
            t_pts = [
                (x0, z_m18_top(abs(x0))), (x1, z_m18_top(abs(x1))),
                (x1, z_ras_top(abs(x1))), (x0, z_ras_top(abs(x0)))
            ]
            cv.add_poly("PAVIMENTO", t_pts, True, fill_hex="#DE8E7A", stroke_hex="#8F331E", lw=0.34)
            cv.add_hatch("HATCH_BRICK", "diag45", t_pts, spacing=7.0)
            cur = nxt + p["rasilla_joint"]

    # Flechas azules de funcionamiento del sifon hidraulico
    for sx in (-1, 1):
        cv.add_flow_arrow([(sx * 95, rej_top + 38), (sx * 95, 88), (sx * 95, 50), (sx * 64, 50), (sx * 64, 108), (sx * 32, 110), (sx * 24, 30)],
                          color_hex="#0B72B9", lw=0.32, head_mm=11.0)
    cv.add_flow_arrow([(0, -10), (0, -210)], color_hex="#0B72B9", lw=0.38, head_mm=14.0)

    # Cotas exactas en mm (verticales en lado derecho para cero cruces con llamadas izquierdas)
    cv.add_dim_h(-pit_in, pit_in, -660.0, 0.0, 0.0, label="250 (caja LHD)")
    cv.add_dim_h(-br, br, -715.0, fal_bot, fal_bot, label="Ø110 (bajante)")
    cv.add_dim_h(-fal_out - rev_h, fal_out + rev_h, -770.0, fal_bot, fal_bot, label="310 (falseado+rev.)")
    cv.add_dim_h(caz_h + 6.0, caz_h + 106.0, 240.0, caz_fl + 9.0, z_mem_top(226), label="SOLAPE 100 mm")
    cv.add_dim_v(forj_bot, 0.0, 800.0, hx, hx, label="250")
    cv.add_dim_v(bv_h, pit_top, 800.0, hx, hx, label="115")
    cv.add_dim_v(pit_top, z_ras_top(hx), 800.0, hx, hx, label="80")
    cv.add_dim_v(bell_bot, weir_top, 865.0, bell_r, weir_r, label="33 (cierre)")
    draw_slope_triangle(cv, -660.0, z_ras_top(660.0), -slope, length=240.0, label="3,0%", dir_x=1.0)

    # 13 llamadas exactas de Diapositiva 3
    cv.add_leader((-520, z_ras_top(520) - 8), (-600, 395), (-760, 395),
                  "RASILLA DE ASPE (280×140×20 mm)", "Junta de 6 mm enrasada con cerco", align="right")
    cv.add_leader((-450, z_m18_top(450) - 6), (-530, 330), (-760, 330),
                  "MORTERO DE AGARRE 1:8 (15 mm)", "Lecho de asiento de rasilla cerámica", align="right")
    cv.add_leader((-380, z_m16_top(380) - 8), (-460, 265), (-760, 265),
                  "MORTERO 1:6 (18 mm)", "Capa regularización sobre hormigón celular", align="right")
    cv.add_leader((-290, z_mem_top(290) - 2), (-360, 200), (-760, 200),
                  "MEMBRANA IMPERMEABILIZANTE (4 mm)", "Solape mínimo 100 mm sobre ala cazoleta", align="right")
    cv.add_leader((-220, z_m16_top(220) + 2), (-250, 135), (-760, 135),
                  "REFUERZO MEMBRANA (4 mm)", "Penetra hasta embocadura de bajante (QAT-10)", align="right")

    cv.add_leader((-560, 62), (-680, -350), (-760, -350),
                  "HORMIGÓN CELULAR (3%)", "115 mm mín. + caja LHD 70×115 mm", align="right")
    cv.add_leader((-410, 1.5), (-520, -415), (-760, -415),
                  "BARRERA CORTAVAPOR (3 mm)", "Sobre cara superior del forjado", align="right")
    cv.add_leader((-480, -125), (-540, -480), (-760, -480),
                  "FORJADO ESTRUCTURAL (250 mm)", "Perforación circular Ø168 mm", align="right")
    cv.add_leader((-360, -258), (-400, -545), (-760, -545),
                  "REVESTIMIENTO (15 mm)", "Enlucido bajo forjado y falseado", align="right")
    cv.add_leader((-120, -420), (-210, -610), (-360, -610),
                  "FALSEADO LADRILLO DEL 4 (40 mm)", "Patinillo cerámico registrable", align="right")

    cv.add_leader((40, rej_top - 4), (110, 370), (280, 370),
                  "REJILLA RANURADA (218×218 mm)", "Tornillo central inox a campana sifónica", align="left")
    cv.add_leader((30, 108), (190, 305), (280, 305),
                  "CAZOLETA SIFÓNICA (240×240 mm)", "Campana Ø164 + sello hidráulico 33 mm", align="left")
    cv.add_leader((48, -320), (260, -320), (350, -320),
                  "BAJANTE PVC-U Ø110 mm", "Con copa superior de acople estanco", align="left")
    cv.add_leader((70, -440), (260, -440), (350, -440),
                  "MANTA FIBRA DE VIDRIO (25 mm)", "Aislamiento acústico y anticondensación", align="left")

    cv.export_dxf(r"d:\C2\planos_2d\detalle3_cazoleta_sifonica.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle3_cazoleta_sifonica.pdf", r"d:\C2\planos_2d\detalle3_cazoleta_sifonica.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle3_cazoleta_sifonica.svg")
    print("Generated Detalle 3 (Cazoleta Sifonica) 2D CAD.")


if __name__ == "__main__":
    build_detalle1_2d()
    build_detalle2_qat16_2d()
    build_detalle2_qat17_2d()
    build_detalle3_2d()
    from generate_2d_cad_part2 import build_part2_2d
    build_part2_2d()
