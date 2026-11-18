r"""
Generates Exact Millimetric 2D CAD Sheets (.dxf, .pdf, .svg, .png) for Details 4 through 9:
  - DET-04: Azotea Invertida con Pavimento Flotante sobre Soportes (PLOTS)
  - DET-05: Tejado de Teja Curva sobre Tabiquillos Palomeros y Canalon Visto
  - DET-06: Cumbrera Ventilada en Seco de Teja Curva sobre Doble Rastrelado
  - DET-07: Faldon de Teja Mixta sobre Doble Rastrel y Encuentro con Paramento
  - DET-08: Tejado de Pizarra Natural QTP-14 con Ganchos y Doble Rastrel
  - DET-09: Cubierta Metalica de Zinc Prepatinado en Junta Alzada Engatillada
"""

import math
import os
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from specs import DETAILS
from cad_2d_core import SheetCanvas2D
from generate_2d_cad import draw_hollow_brick_section, draw_bovedilla_and_senos_2d


def draw_curved_tile_arch(cv, x_start, x_end, z_start, z_end, r_outer, thickness, fill="#F3D6C8", stroke="#8F2F1B"):
    """Draws an authentic longitudinal barrel tile shell strip from (x_start,z_start) to (x_end,z_end)."""
    dx, dz = x_end - x_start, z_end - z_start
    L = math.hypot(dx, dz)
    if L < 1e-3:
        return
    ux, uz = dx / L, dz / L
    nx, nz = -uz, ux
    # Tapered visual shell body (perpendicular offset)
    p0 = (x_start + nx * r_outer, z_start + nz * r_outer)
    p1 = (x_end + nx * r_outer, z_end + nz * r_outer)
    p2 = (x_end + nx * (r_outer - thickness), z_end + nz * (r_outer - thickness))
    p3 = (x_start + nx * (r_outer - thickness), z_start + nz * (r_outer - thickness))
    cv.add_poly("TEJA", [p0, p1, p2, p3], True, fill_hex=fill, stroke_hex=stroke, lw=0.34)
    cv.add_hatch("HATCH_BRICK", "diag45", [p0, p1, p2, p3], spacing=10.0)


# ==============================================================================
# DET-04: Azotea Invertida Transitable con Pavimento Flotante sobre PLOTS
# ==============================================================================
def build_detalle4_plots_2d():
    meta = DETAILS["detalle4_plots"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(124.0, 96.0))

    dx_end = p["deck_end_x"]       # 1020
    j_x0, j_x1 = dx_end, dx_end + p["junta_eps_w"]        # 1020..1035
    ei_x0, ei_x1 = j_x1, j_x1 + p["enfoscado_int_w"]      # 1035..1050
    pb_x0, pb_x1 = ei_x1, ei_x1 + p["peto_brick_w"]       # 1050..1190
    ee_x0, ee_x1 = pb_x1, pb_x1 + p["enfoscado_ext_w"]    # 1190..1210

    def z_fp_core(x): return p["fp_min_h"] + p["slope"] * x
    def z_fp_top(x): return z_fp_core(x) + p["fp_reg_h"]
    def z_i_top(x): return z_fp_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_at_top(x): return z_cs_top(x) + p["at_h"]
    z_losa_bot = z_at_top(dx_end) + p["plot_h"]   # horizontal floating floor level!
    z_losa_top = z_losa_bot + p["tile_h"]

    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]

    # 1. Forjado unidireccional + zuncho
    cv.add_rect("FORJADO", 0.0, comp_bot, ee_x1, 0.0, fill_hex="#E2E6E9", stroke_hex="#252B33", lw=0.40)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(0, comp_bot), (ee_x1, comp_bot), (ee_x1, 0), (0, 0)], spacing=18.0)
    cv.add_rect("FORJADO", 860.0, forj_bot, ee_x1, comp_bot, fill_hex="#D7DCE0", stroke_hex="#252B33", lw=0.38)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(860, forj_bot), (ee_x1, forj_bot), (ee_x1, comp_bot), (860, comp_bot)], spacing=22.0)

    for vx in (200.0, 780.0):
        v_pts = [(vx - 60, forj_bot), (vx + 60, forj_bot), (vx + 60, forj_bot + 40),
                 (vx + 34, forj_bot + 43), (vx + 28, forj_bot + 50), (vx + 26, comp_bot),
                 (vx - 26, comp_bot), (vx - 28, forj_bot + 50), (vx - 34, forj_bot + 43),
                 (vx - 60, forj_bot + 40)]
        cv.add_poly("FORJADO", v_pts, True, fill_hex="#C7CDD2", stroke_hex="#14191F", lw=0.36)
        cv.add_circle("FORJADO", vx - 28, forj_bot + 20, 4.0, fill_hex="#14191F")
        cv.add_circle("FORJADO", vx + 28, forj_bot + 20, 4.0, fill_hex="#14191F")

    draw_bovedilla_and_senos_2d(cv, -380.0, 200.0, forj_bot, comp_bot, clip_x0=0.0)
    draw_bovedilla_and_senos_2d(cv, 200.0, 780.0, forj_bot, comp_bot)
    mac_pts = [(806.0, comp_bot), (860.0, comp_bot), (860.0, forj_bot),
               (840.0, forj_bot), (840.0, forj_bot + 40.0), (814.0, forj_bot + 43.0), (808.0, forj_bot + 50.0)]
    cv.add_poly("FORJADO", mac_pts, True, fill_hex="#D7DCE0", stroke_hex="#252B33", lw=0.26)
    cv.add_hatch("HATCH_LIGHT", "concrete", mac_pts, spacing=20.0)

    # 2. Formacion de pendientes + regularizacion 20 mm
    fp_pts = [(0, 0), (dx_end, 0), (dx_end, z_fp_core(dx_end)), (0, z_fp_core(0))]
    cv.add_poly("HORMIGON_CEL", fp_pts, True, fill_hex="#E5E1D9", stroke_hex="#4A4E54", lw=0.30)
    cv.add_hatch("HATCH_LIGHT", "concrete", fp_pts, spacing=16.0)
    reg_pts = [(0, z_fp_core(0)), (dx_end, z_fp_core(dx_end)), (dx_end, z_fp_top(dx_end)), (0, z_fp_top(0))]
    cv.add_poly("MORTERO", reg_pts, True, fill_hex="#D6CFC4", stroke_hex="#5E5850", lw=0.26)
    cv.add_hatch("HATCH_LIGHT", "dots", reg_pts, spacing=9.0)

    # 3. Junta EPS + Peto LHD + Barrera antihumedad + Albardilla piedra artificial con goteron
    cv.add_rect("AISLAMIENTO", j_x0, 0.0, j_x1, z_at_top(dx_end), fill_hex="#FFFDF5", stroke_hex="#A8810A", lw=0.20)
    cv.add_hatch("HATCH_INSUL", "cross", [(j_x0, 0), (j_x1, 0), (j_x1, z_at_top(dx_end)), (j_x0, z_at_top(dx_end))], spacing=6.0)

    z_peto = p["peto_top_z"]
    course_h = 72.0
    zc = 0.0
    while zc + 50.0 < z_peto:
        bh = min(62.0, z_peto - zc - 8.0)
        # Interrumpir ligeramente por barrera antihumedad bajo ultima hilada
        draw_hollow_brick_section(cv, pb_x0, zc, pb_x1, zc + bh, cols=2, rows=2)
        if zc + bh + 10.0 < z_peto:
            cv.add_rect("MORTERO", pb_x0, zc + bh, pb_x1, zc + bh + 10.0, fill_hex="#DED8CE", stroke_hex="#5E5850", lw=0.14)
        zc += course_h

    # Enfoscados & barrera antihumedad en coronacion
    cv.add_rect("MORTERO", ei_x0, 0.0, ei_x1, z_peto, fill_hex="#EAE5DC", stroke_hex="#5E5850", lw=0.22)
    cv.add_rect("MORTERO", ee_x0, forj_bot, ee_x1, z_peto, fill_hex="#EAE5DC", stroke_hex="#5E5850", lw=0.22)
    cv.add_rect("MEMBRANA", ei_x0, z_peto - 5.0, ee_x1, z_peto, fill_hex="#181B20", stroke_hex="#101214", lw=0.30)

    # Albardilla piedra artificial con doble goteron (X: ei_x0 - 25 .. ee_x1 + 25)
    ov = p["albardilla_overhang"]
    alb_top = z_peto + p["albardilla_h"]
    alb_pts = [
        (ei_x0 - ov, z_peto - 8), (ei_x0 - ov + 8, z_peto - 8), (ei_x0 - ov + 8, z_peto),
        (ee_x1 + ov - 8, z_peto), (ee_x1 + ov - 8, z_peto - 8), (ee_x1 + ov, z_peto - 8),
        (ee_x1 + ov, alb_top - 6), (0.5 * (ei_x0 + ee_x1), alb_top), (ei_x0 - ov, alb_top - 6)
    ]
    cv.add_poly("FORJADO", alb_pts, True, fill_hex="#EFECE6", stroke_hex="#252B33", lw=0.38)
    cv.add_hatch("HATCH_LIGHT", "concrete", alb_pts, spacing=14.0)

    # 4. Membrana bicapa SBS (con refuerzo perimetral y entrega 210 mm en peto)
    z_turn = z_fp_top(dx_end) + p["i_turnup_h"]
    mem_pts = [
        (0, z_fp_top(0)), (dx_end, z_fp_top(dx_end)), (ei_x0, z_fp_top(dx_end)),
        (ei_x0, z_turn), (ei_x0 - p["i_h"], z_turn), (ei_x0 - p["i_h"], z_i_top(dx_end)),
        (0, z_i_top(0)),
    ]
    cv.add_poly("MEMBRANA", mem_pts, True, fill_hex="#1E2126", stroke_hex="#101214", lw=0.45)
    # Perfil metalico remate superior membrana en peto
    cv.add_poly("METAL_CAZ", [(ei_x0 - 10, z_turn + 6), (ei_x0, z_turn + 6), (ei_x0, z_turn - 18), (ei_x0 - 6, z_turn - 18), (ei_x0 - 10, z_turn)],
                True, fill_hex="#9AA7B2", stroke_hex="#233F54", lw=0.28)

    # 5. Geotextil CS antipunzonante + XPS 80 mm (INVERTIDA: encima de membrana!)
    cs_pts = [(0, z_i_top(0)), (j_x0, z_i_top(j_x0)), (j_x0, z_cs_top(j_x0)), (0, z_cs_top(0))]
    cv.add_poly("CAPA_SEP", cs_pts, True, fill_hex="#D2ECF7", stroke_hex="#24749C", lw=0.25)

    xps_pts = [(0, z_cs_top(0)), (j_x0 - 4, z_cs_top(j_x0 - 4)), (j_x0 - 4, z_at_top(j_x0 - 4)), (0, z_at_top(0))]
    cv.add_poly("AISLAMIENTO", xps_pts, True, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.30)
    slope_deg = math.degrees(math.atan(p["slope"]))
    cv.add_hatch("HATCH_INSUL", "batt_insul", xps_pts, spacing=18.0, angle_deg=slope_deg)

    # 6. PLOTS regulables roscados (en x = 180, 584, 988)
    for px in (180.0, 584.0, 988.0):
        zb = z_at_top(px)
        zt = z_losa_bot
        # Disco base + fuste roscado + cabezal cruceta 4 mm
        cv.add_rect("METAL_CAZ", px - 70, zb, px + 70, zb + 10, fill_hex="#464D57", stroke_hex="#14191F", lw=0.26)
        cv.add_rect("METAL_CAZ", px - 24, zb + 10, px + 24, zt - 10, fill_hex="#333942", stroke_hex="#14191F", lw=0.26)
        # Rosca horizontal visual
        zr = zb + 20
        while zr < zt - 14:
            cv.add_line("METAL_CAZ", px - 24, zr, px + 24, zr, color_hex="#7A8491", lw=0.14)
            zr += 9.0
        cv.add_rect("METAL_CAZ", px - 58, zt - 10, px + 58, zt, fill_hex="#464D57", stroke_hex="#14191F", lw=0.26)
        # Cruceta separadora entre losas (4 mm)
        cv.add_rect("METAL_CAZ", px - 2, zt, px + 2, zt + 20, fill_hex="#233F54", stroke_hex="#14191F", lw=0.22)

    # 7. Pavimento Flotante: Losas Armadas 400x400x40 mm nivel horizontal con junta abierta 4 mm
    for lx0, lx1 in ((0.0, 178.0), (182.0, 582.0), (586.0, 986.0), (990.0, 1014.0)):
        cv.add_rect("FORJADO", lx0, z_losa_bot, lx1, z_losa_top, fill_hex="#D2CCC2", stroke_hex="#14191F", lw=0.38)
        cv.add_hatch("HATCH_LIGHT", "concrete", [(lx0, z_losa_bot), (lx1, z_losa_bot), (lx1, z_losa_top), (lx0, z_losa_top)], spacing=16.0)
        # Varilla armadura vista en seccion losa
        cv.add_line("FORJADO", lx0 + 8, z_losa_bot + 16, lx1 - 8, z_losa_bot + 16, color_hex="#353B42", lw=0.24, dash=(2.5, 1.5))

    # Drenaje agua por juntas abiertas hacia pendiente inferior
    for px in (180.0, 584.0):
        cv.add_flow_arrow([(px, z_losa_top + 24), (px, z_losa_bot - 12)], color_hex="#0B72B9", lw=0.26, head_mm=8.0)
    cv.add_flow_arrow([(880, z_i_top(880) + 12), (460, z_i_top(460) + 12), (40, z_i_top(40) + 12)],
                      color_hex="#0B72B9", lw=0.32, head_mm=12.0, dash=(3.0, 1.5))

    # Lineas de rotura en corte izquierdo
    cv.add_breakline(0.0, forj_bot, 0.0, z_losa_top)

    # Cotas y Pendiente
    cv.add_slope_marker(240.0, z_i_top(240.0), -p["slope"], length=160.0, dir_x=-1.0, label="Pend. esc. 2,5%", lift_mm=14.0)
    cv.add_dim_h(0.0, dx_end, -315.0, forj_bot, forj_bot, label="1020 (faldón)")
    cv.add_dim_h(dx_end, ee_x1, -315.0, forj_bot, forj_bot, label="190 (peto+junta)")
    cv.add_dim_v(forj_bot, 0.0, 1270.0, ee_x1, ee_x1, label="260")
    cv.add_dim_v(0.0, z_i_top(dx_end), 1270.0, dx_end, dx_end, label="101 (FP+I)")
    cv.add_dim_v(z_i_top(dx_end), z_losa_top, 1270.0, ee_x1, ee_x1, label="208 (AT+Plot+Losa)")
    cv.add_dim_v(0.0, alb_top, 1345.0, ee_x1, ee_x1, label="865")

    # Llamadas columna izquierda limpia
    cv.add_leader((380, z_losa_top - 15), (140, 560), (-45, 560),
                  "PF · PAVIMENTO FLOTANTE (40 mm)", "Baldosas armadas 400×400 · junta abierta 4 mm", align="right", badge=1)
    cv.add_leader((180, z_at_top(180) + 45), (90, 480), (-45, 480),
                  "PLOT · SOPORTE REGULABLE (H ≈ 85 mm)", "Polipropileno roscado + cruceta separadora 4 mm", align="right", badge=2)
    cv.add_leader((460, z_cs_top(460) + 40), (140, 400), (-45, 400),
                  "AT · AISLAMIENTO INVERTIDO XPS (80 mm)", "Poliestireno extruido 300 kPa sobre lámina", align="right", badge=3)
    cv.add_leader((640, z_cs_top(640) - 1.5), (160, 320), (-45, 320),
                  "CS · GEOTEXTIL ANTIPUNZONANTE (300 g/m²)", "Capa separadora bajo XPS y plots", align="right", badge=4)
    cv.add_leader((760, z_fp_top(760) + 3), (180, 240), (-45, 240),
                  "I · MEMBRANA BICAPA SBS (6 mm)", "LBM-40 + refuerzo + entrega 210 mm con perfil", align="right", badge=5)
    cv.add_leader((520, 38), (120, 150), (-45, 150),
                  "FP · FORMACIÓN PENDIENTE (2,5%)", "Hormigón ligero + regularización mortero 20 mm", align="right", badge=6)
    cv.add_leader((500, -135), (140, -135), (-45, -135),
                  "SR · FORJADO UNIDIRECCIONAL (260 mm)", "Semiviguetas pretensadas + bovedillas + HA-25", align="right", badge=7)
    cv.add_leader((pb_x0 + 70, alb_top - 22), (820, 880), (740, 880),
                  "ALBARDILLA + BARRERA ANTIHUMEDAD", "Piedra artificial con doble goterón + LHD 140 mm", align="right", badge=8)

    cv.export_dxf(r"d:\C2\planos_2d\detalle4_invertida_plots.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle4_invertida_plots.pdf", r"d:\C2\planos_2d\detalle4_invertida_plots.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle4_invertida_plots.svg")
    print("Generated DET-04 (Azotea Invertida PLOTS) 2D CAD.")


# ==============================================================================
# DET-05: Tejado de Teja Curva sobre Tabiquillos Palomeros + Alero Canalon Visto
# ==============================================================================
def build_detalle5_alero_teja_2d():
    meta = DETAILS["detalle5_alero_teja"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=6.0, origin_sheet=(132.0, 118.0))

    slope = p["slope"]             # 0.30
    deg = math.degrees(math.atan(slope))
    cos_a, sin_a = math.cos(math.atan(slope)), math.sin(math.atan(slope))
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 150..290
    cx1, ix1 = p["cham_x1"], p["int_x1"]    # 340, 400
    x_end = 1220.0
    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]
    corn_x0 = wx0 - p["cornice_overhang"]   # 60

    def z_tab_bot(x): return p["tablero_z_eaves"] + slope * (x - wx0)
    def z_tab_top(x): return z_tab_bot(x) + p["tablero_h"]
    def z_reg_top(x): return z_tab_top(x) + p["reg_h"]

    # 1. Fachada capuchina inferior (hasta Z=-320) con goteron y sardinel de alero
    z_fbot = -340.0
    zc = z_fbot
    while zc < -110.0:
        draw_hollow_brick_section(cv, wx0, zc, wx1, min(zc + 62, -95.0), cols=2, rows=2)
        zc += 72.0
    # Ladrillo a sardinel remate cornice exterior (x: 100..150) + goteron
    cv.add_rect("LADRILLO", corn_x0 + 25, -88.0, wx0, 0.0, fill_hex="#F7E4DC", stroke_hex="#7D3522", lw=0.28)
    cv.add_hatch("HATCH_BRICK", "diag45", [(corn_x0 + 25, -88.0), (wx0, -88.0), (wx0, 0.0), (corn_x0 + 25, 0.0)], spacing=9.0)
    # Aislamiento camara + tabique interior + enfoscados
    cv.add_rect("MORTERO", wx0 - 12, z_fbot, wx0, -88.0, fill_hex="#EAE5DC", stroke_hex="#5E5850", lw=0.20)
    cv.add_rect("AISLAMIENTO", wx1, z_fbot, cx1, forj_bot, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.22)
    cv.add_hatch("HATCH_INSUL", "batt_insul", [(wx1, z_fbot), (cx1, z_fbot), (cx1, forj_bot), (wx1, forj_bot)], spacing=16.0, angle_deg=90.0)
    draw_hollow_brick_section(cv, cx1, z_fbot, ix1, forj_bot, cols=1, rows=3)
    cv.add_rect("MORTERO", ix1, z_fbot, ix1 + 14, forj_bot, fill_hex="#F3F0EA", stroke_hex="#5E5850", lw=0.18)

    # 2. Forjado unidireccional + zuncho de borde + cornisa galce
    cv.add_rect("FORJADO", corn_x0, comp_bot, x_end, 0.0, fill_hex="#E2E6E9", stroke_hex="#252B33", lw=0.40)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(corn_x0, comp_bot), (x_end, comp_bot), (x_end, 0.0), (corn_x0, 0.0)], spacing=18.0)
    # Zuncho + galce cornisa
    cv.add_poly("FORJADO", [(corn_x0, -88.0), (wx0, -88.0), (wx0, forj_bot), (440, forj_bot), (440, comp_bot), (corn_x0, comp_bot)],
                True, fill_hex="#D7DCE0", stroke_hex="#252B33", lw=0.38)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(wx0, forj_bot), (440, forj_bot), (440, comp_bot), (wx0, comp_bot)], spacing=22.0)
    # Estribo zuncho
    cv.add_rect("FORJADO", wx0 + 25, forj_bot + 25, 415, -25, fill_hex=None, stroke_hex="#14191F", lw=0.24)
    # Vigueta + bovedillas ceramicas reales con tacones y senos
    vx = 840.0
    cv.add_poly("FORJADO", [(vx - 60, forj_bot), (vx + 60, forj_bot), (vx + 60, forj_bot + 40),
                            (vx + 34, forj_bot + 43), (vx + 28, forj_bot + 50), (vx + 26, comp_bot),
                            (vx - 26, comp_bot), (vx - 28, forj_bot + 50), (vx - 34, forj_bot + 43),
                            (vx - 60, forj_bot + 40)], True, fill_hex="#C7CDD2", stroke_hex="#14191F", lw=0.34)
    draw_bovedilla_and_senos_2d(cv, 300.0, vx, forj_bot, comp_bot, clip_x0=440.0)
    draw_bovedilla_and_senos_2d(cv, vx, vx + 580.0, forj_bot, comp_bot, clip_x1=x_end)

    # 3. Aislamiento termico sobre forjado (80 mm lana mineral entre tabiquillos)
    for ax0, ax1 in ((wx1, 470.0), (540.0, 960.0), (1030.0, x_end)):
        at_pts = [(ax0, 0), (ax1, 0), (ax1, p["at_h"]), (ax0, p["at_h"])]
        cv.add_poly("AISLAMIENTO", at_pts, True, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.26)
        cv.add_hatch("HATCH_INSUL", "batt_insul", at_pts, spacing=16.0, angle_deg=0.0)

    # 4. Tabiquillos palomeros calados (x=470..540 y x=960..1030)
    for tx0, tx1 in ((470.0, 540.0), (960.0, 1030.0)):
        ztop_l = z_tab_bot(tx0) - 18.0
        ztop_r = z_tab_bot(tx1) - 18.0
        zt = 0.0
        idx = 0
        while zt + 55.0 < ztop_l:
            if idx % 2 == 0:  # hilada ladrillo
                draw_hollow_brick_section(cv, tx0, zt, tx1, zt + 58.0, cols=1, rows=2)
            else:             # hilada calada (espacio libre ventilacion a izq/der de la muestra)
                draw_hollow_brick_section(cv, tx0 + 18, zt, tx1 - 18, zt + 58.0, cols=1, rows=1)
            zt += 66.0
            idx += 1
        # Maestra mortero superior inclinada bajo tablero
        m_pts = [(tx0, ztop_l), (tx1, ztop_r), (tx1, z_tab_bot(tx1)), (tx0, z_tab_bot(tx0))]
        cv.add_poly("MORTERO", m_pts, True, fill_hex="#D6CFC4", stroke_hex="#5E5850", lw=0.22)

    # Murete apoyo de borde sobre zuncho (x=wx0..wx0+90)
    cv.add_poly("LADRILLO", [(corn_x0, 0.0), (wx0 + 70, 0.0), (wx0 + 70, z_tab_bot(wx0 + 70)), (corn_x0, z_tab_bot(corn_x0))],
                True, fill_hex="#F7E4DC", stroke_hex="#7D3522", lw=0.28)
    cv.add_hatch("HATCH_BRICK", "horiz_masonry", [(corn_x0, 0.0), (wx0 + 70, 0.0), (wx0 + 70, z_tab_bot(wx0 + 70)), (corn_x0, z_tab_bot(corn_x0))], spacing=16.0)

    # 5. Tablero ceramico machihembrado (bardo 40 mm) + Regularizacion M-5 (25 mm)
    xb0 = corn_x0 - 15.0  # 45 mm
    tab_pts = [(xb0, z_tab_bot(xb0)), (x_end, z_tab_bot(x_end)), (x_end, z_tab_top(x_end)), (xb0, z_tab_top(xb0))]
    cv.add_poly("LADRILLO", tab_pts, True, fill_hex="#F5DFD4", stroke_hex="#7D3522", lw=0.34)
    cv.add_hatch("HATCH_BRICK", "diag135", tab_pts, spacing=12.0)

    reg_pts = [(xb0, z_tab_top(xb0)), (x_end, z_tab_top(x_end)), (x_end, z_reg_top(x_end)), (xb0, z_reg_top(xb0))]
    cv.add_poly("MORTERO", reg_pts, True, fill_hex="#D7D0C4", stroke_hex="#5E5850", lw=0.26)
    cv.add_hatch("HATCH_LIGHT", "dots", reg_pts, spacing=9.0)

    # 6. Canalon visto semicircular de Zinc + gancho atornillado a cornisa
    gcx, gcz, gr = p["gutter_cx"], p["gutter_cz"], p["gutter_r"]
    g_pts = []
    for k in range(25):
        a = math.radians(180.0 + k * 180.0 / 24.0)
        g_pts.append((gcx + gr * math.cos(a), gcz + gr * math.sin(a)))
    for k in range(24, -1, -1):
        a = math.radians(180.0 + k * 180.0 / 24.0)
        g_pts.append((gcx + (gr - 6.0) * math.cos(a), gcz + (gr - 6.0) * math.sin(a)))
    cv.add_poly("ZINC", g_pts, True, fill_hex="#C5D4E0", stroke_hex="#30495E", lw=0.34)
    # Bordon enrollado exterior canalon + pletina gancho al alero
    cv.add_circle("ZINC", gcx - gr, gcz, 7.0, fill_hex="#C5D4E0", stroke_hex="#30495E", lw=0.26)
    cv.add_poly("METAL_CAZ", [(gcx - gr - 4, gcz), (gcx + gr + 2, gcz + 18), (xb0 + 45, z_tab_bot(xb0 + 45) - 6),
                              (xb0 + 45, z_tab_bot(xb0 + 45) - 14), (gcx + gr - 2, gcz + 6), (gcx - gr + 4, gcz - 4)],
                True, fill_hex="#8A96A2", stroke_hex="#14191F", lw=0.24)

    # 7. Teja Curva Canal + Cobija con solape 140 mm, recalce 1a hilada & vuelo 55 mm sobre canalon!
    eave_tip_x = xb0 - p["vuelo_alero"]  # 45 - 55 = -10 mm (sobre canalon!)
    step = p["tile_len"] - p["tile_solape"]  # 310 mm
    tlen = p["tile_len"]
    # Hiladas de abajo a arriba: hilada 0 (alero recalzada), 1, 2, 3
    for i in range(4):
        s_along = i * step
        xs0 = eave_tip_x + s_along * cos_a
        zs0 = z_reg_top(xb0) + (xs0 - xb0) * slope
        # Recalce con mortero M-2,5 en borde alero + pendiente paralela al faldón
        mor_h = p["mortar_bed_h"] + (18.0 if i == 0 else 6.0)
        xs1 = xs0 + tlen * cos_a
        zs1 = z_reg_top(xb0) + (xs1 - xb0) * slope
        if xs0 < x_end - 40:
            xe = min(xs1, x_end)
            ze = zs0 + slope * (xe - xs0)
            # Mortero de agarre bajo teja canal (con macizado frente alero en hilada 0)
            m0 = (max(xb0, xs0), z_reg_top(max(xb0, xs0)))
            m1 = (xe, z_reg_top(xe))
            m2 = (xe, ze + 22.0)
            m3 = (max(xb0, xs0), z_reg_top(max(xb0, xs0)) + (34.0 if i == 0 else 20.0))
            cv.add_poly("MORTERO", [m0, m1, m2, m3], True, fill_hex="#C9C0B3", stroke_hex="#5E5850", lw=0.20)
            # Teja CANAL
            draw_curved_tile_arch(cv, xs0, xe, zs0 + 24.0 + i * 5.0, ze + 30.0 + i * 5.0,
                                  r_outer=18.0, thickness=12.0, fill="#F3CEBE", stroke="#8F2F1B")
            # Teja COBIJA solapando por encima (hilada 0 ligeramente mas corta/cortada en borde!)
            cob_x0 = xs0 + (15.0 if i == 0 else 0.0)
            cob_z0 = zs0 + 24.0 + i * 5.0 + (10.0 if i == 0 else 0.0)
            draw_curved_tile_arch(cv, cob_x0, xe, cob_z0 + 48.0, ze + 30.0 + i * 5.0 + 48.0,
                                  r_outer=26.0, thickness=13.0, fill="#DE8368", stroke="#7A2210")

    # Flujos agua + aire microventilacion
    cv.add_flow_arrow([(700, z_reg_top(700) + 125), (300, z_reg_top(300) + 125), (gcx + 8, gcz + 55), (gcx, gcz + 12)],
                      color_hex="#0B72B9", lw=0.34, head_mm=12.0)
    cv.add_flow_arrow([(260, 96), (620, 120), (1080, 180)], color_hex="#1985A1", lw=0.26, head_mm=10.0, dash=(4.0, 2.5))

    # Breaklines
    cv.add_breakline(x_end, forj_bot, x_end, z_reg_top(x_end) + 95.0)
    cv.add_breakline(wx0, z_fbot, ix1 + 14, z_fbot)

    # Cotas y pendiente
    cv.add_slope_marker(460.0, z_reg_top(460.0) + 128.0, slope, length=200.0, dir_x=1.0, label="Pend. 30% (16,7°)", lift_mm=24.0)
    cv.add_dim_h(eave_tip_x, xb0, 220.0, gcz + 65, z_reg_top(xb0), label="55 (vuelo)")
    cv.add_dim_h(470.0, 1030.0, -320.0, 0.0, 0.0, label="Paso tabiquillos ~500 mm")
    cv.add_dim_v(forj_bot, 0.0, 1285.0, x_end, x_end, label="260")
    cv.add_dim_v(0.0, z_tab_bot(x_end), 1285.0, x_end, x_end, label="Cámara palomeros")

    # Llamadas organizadas arriba-izquierda, arriba-derecha y bajo-izquierda (cero cruces)
    cv.add_leader((320, z_reg_top(320) + 92), (180, 575), (-20, 575),
                  "TEJA COBIJA CERÁMICA (L=450 mm)", "Solape 140 mm · 1ª cobija cortada en alero", align="right", badge=1)
    cv.add_leader((480, z_reg_top(480) + 48), (220, 485), (-20, 485),
                  "TEJA CANAL CERÁMICA + RECALCE", "Vuelo 55 mm · paso entre cobijas ≥35 mm", align="right", badge=2)
    cv.add_leader((190, z_reg_top(190) + 12), (80, 395), (-20, 395),
                  "MORTERO DE AGARRE M-2,5 (1:8)", "Cordones ventilados + macizado de alero (QTT-14)", align="right", badge=3)
    cv.add_leader((gcx - 20, gcz - 52), (-30, 270), (-80, 270),
                  "CANALÓN VISTO DE ZINC Ø130", "Ganchos pletina galvanizada cada 500 mm", align="right", badge=4)
    cv.add_leader((680, z_tab_bot(680) + 28), (910, 740), (1080, 740),
                  "TABLERO BARDO + CAPA M-5", "Bardo machihembrado 40 mm + reg. 25 mm", align="left", badge=5)
    cv.add_leader((505, 110), (930, 655), (1080, 655),
                  "TABIQUILLO PALOMERO CALADO", "LHD calado 25% ventilación + maestra", align="left", badge=6)
    cv.add_leader((760, 40), (620, -395), (260, -395),
                  "LANA MINERAL (80 mm) + FORJADO", "Aislamiento continuo s/ forjado + cornisa goterón", align="right", badge=7)

    cv.export_dxf(r"d:\C2\planos_2d\detalle5_alero_teja_curva.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle5_alero_teja_curva.pdf", r"d:\C2\planos_2d\detalle5_alero_teja_curva.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle5_alero_teja_curva.svg")
    print("Generated DET-05 (Alero Teja Curva + Palomeros) 2D CAD.")


# ==============================================================================
# DET-06: Cumbrera Ventilada en Seco de Teja Curva sobre Doble Rastrelado
# ==============================================================================
def build_detalle6_cumbrera_teja_2d():
    meta = DETAILS["detalle6_cumbrera_teja"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(210.0, 148.0))

    slope = p["slope"]          # 0.32
    hx = p["half_span_x"]       # 760
    ang = math.atan(slope)
    deg = math.degrees(ang)
    cos_a, sin_a = math.cos(ang), math.sin(ang)

    # Altura vertical por capa medida perpendicular al faldon -> dz = t / cos_a
    t_tab = p["tablero_h"] / cos_a
    t_reg = p["reg_h"] / cos_a
    t_at = p["at_h"] / cos_a
    t_cr = p["contrarastrel_h"] / cos_a
    t_ra = p["rastrel_h"] / cos_a

    # Eje vertical central + apoyo cumbrera (viga / murete LHD)
    cv.add_line("ROTURA", 0.0, -320.0, 0.0, 310.0, color_hex="#8E969E", lw=0.16, dash=(5.0, 2.0, 1.0, 2.0))
    cv.add_rect("FORJADO", -70.0, -290.0, 70.0, 0.0, fill_hex="#D7DCE0", stroke_hex="#252B33", lw=0.38)
    cv.add_hatch("HATCH_LIGHT", "concrete", [(-70, -290), (70, -290), (70, 0), (-70, 0)], spacing=18.0)

    # Ambos faldones simetricos desde x=0 hasta x=+-hx
    for sx in (-1.0, 1.0):
        # Tablero + reg
        tab_pts = [(0, -t_tab), (sx * hx, -hx * slope - t_tab), (sx * hx, -hx * slope), (0, 0)]
        cv.add_poly("LADRILLO", tab_pts, True, fill_hex="#F5DFD4", stroke_hex="#7D3522", lw=0.34)
        cv.add_hatch("HATCH_BRICK", "diag45" if sx > 0 else "diag135", tab_pts, spacing=12.0)

        reg_pts = [(0, 0), (sx * hx, -hx * slope), (sx * hx, -hx * slope + t_reg), (0, t_reg)]
        cv.add_poly("MORTERO", reg_pts, True, fill_hex="#D7D0C4", stroke_hex="#5E5850", lw=0.22)

        # XPS 60 mm continuo
        z0 = t_reg
        z1 = z0 + t_at
        at_pts = [(0, z0), (sx * hx, z0 - hx * slope), (sx * hx, z1 - hx * slope), (0, z1)]
        cv.add_poly("AISLAMIENTO", at_pts, True, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.28)
        cv.add_hatch("HATCH_INSUL", "batt_insul", at_pts, spacing=16.0, angle_deg=-sx * deg)

        # Lamina impermeable transpirable
        cv.add_line("CAPA_SEP", 0, z1 + 2, sx * hx, z1 - hx * slope + 2, color_hex="#24749C", lw=0.45)

        # Contrarastrel paralelo a pendiente (camara microventilacion)
        z2 = z1 + t_cr
        cr_pts = [(sx * 32, z1 - 32 * slope), (sx * (hx - 40), z1 - (hx - 40) * slope),
                  (sx * (hx - 40), z2 - (hx - 40) * slope), (sx * 32, z2 - 32 * slope)]
        cv.add_poly("MADERA", cr_pts, True, fill_hex="#EDD6B6", stroke_hex="#754E1E", lw=0.26)
        cv.add_hatch("HATCH_WOOD", "wood_grain", cr_pts, spacing=7.0, angle_deg=-sx * deg)

        # Rastreles horizontales en seccion transversal (cuadradillos 40x30 sobre contrarastrel)
        for d_along in (75.0, 290.0, 505.0, 715.0):
            xc = sx * d_along * cos_a
            zc_base = z2 - abs(xc) * slope
            hw, hh = 20.0, 15.0
            rx_pts = [
                (xc - sx * hw * cos_a, zc_base + hw * sin_a),
                (xc + sx * hw * cos_a, zc_base - hw * sin_a),
                (xc + sx * hw * cos_a - sx * 30 * sin_a, zc_base - hw * sin_a + 30 * cos_a),
                (xc - sx * hw * cos_a - sx * 30 * sin_a, zc_base + hw * sin_a + 30 * cos_a),
            ]
            cv.add_poly("MADERA", rx_pts, True, fill_hex="#DFBA84", stroke_hex="#754E1E", lw=0.28)
            cv.add_hatch("HATCH_WOOD", "wood_cut", rx_pts, spacing=5.0)

        # Teja canal + Teja cobija dejando paso ventilacion 5 cm en cumbrera
        gap_x = p["ridge_gap_half"]  # 28 mm a cada lado -> 56 mm total
        for hl in (0, 1):
            d0 = gap_x / cos_a + hl * (p["tile_len"] - p["tile_solape"])
            d1 = d0 + p["tile_len"]
            xa = sx * d0 * cos_a
            xb = sx * min(d1 * cos_a, hx)
            if abs(xb) <= abs(xa) + 20:
                continue
            za = z2 + 30.0 / cos_a - abs(xa) * slope + (0 if hl == 0 else -5.0)
            zb = z2 + 30.0 / cos_a - abs(xb) * slope + (0 if hl == 0 else -5.0)
            # Teja canal + cobija
            off_n = 16.0 if sx > 0 else -16.0
            # Direct offset outward (up-normal)
            ux, uz = sx * cos_a, -sin_a
            nx, nz = sx * sin_a, cos_a
            # Canal shell
            c_pts = [(xa, za), (xb, zb), (xb + nx * 13, zb + nz * 13), (xa + nx * 13, za + nz * 13)]
            cv.add_poly("TEJA", c_pts, True, fill_hex="#F3CEBE", stroke_hex="#8F2F1B", lw=0.32)
            # Cobija shell (elevada por arco)
            cb_pts = [(xa + nx * 36, za + nz * 36), (xb + nx * 36, zb + nz * 36),
                      (xb + nx * 50, zb + nz * 50), (xa + nx * 50, za + nz * 50)]
            cv.add_poly("TEJA", cb_pts, True, fill_hex="#DE8368", stroke_hex="#7A2210", lw=0.34)
            cv.add_hatch("HATCH_BRICK", "diag45", cb_pts, spacing=9.0)

        # Flechas microventilacion ascendente
        cv.add_flow_arrow([(sx * 520, z1 + 16 - 520 * slope), (sx * 160, z1 + 16 - 160 * slope), (sx * 38, z2 + 65), (sx * 72, z2 + 95)],
                          color_hex="#1985A1", lw=0.28, head_mm=10.0, dash=(3.5, 2.0))

    # Soporte metalico del caballete + rastrel cumbrera + remate ventilado + teja caballete
    z_apex = t_reg + t_at + t_cr + 42.0
    # Soporte metalico regulable U
    cv.add_poly("METAL_CAZ", [(-30, t_reg + t_at), (30, t_reg + t_at), (30, z_apex + 55), (-30, z_apex + 55)],
                True, fill_hex="#9AA7B2", stroke_hex="#14191F", lw=0.28)
    # Rastrel cumbrera 45x55
    cv.add_rect("MADERA", -22.5, z_apex, 22.5, z_apex + 55.0, fill_hex="#DFBA84", stroke_hex="#754E1E", lw=0.32)
    cv.add_hatch("HATCH_WOOD", "wood_cut", [(-22.5, z_apex), (22.5, z_apex), (22.5, z_apex + 55), (-22.5, z_apex + 55)], spacing=5.0)

    # Banda remate de cumbrera ventilado (plisado sobre onda cobijas)
    cv.add_poly("ZINC", [(-165, z_apex - 15), (-40, z_apex + 48), (40, z_apex + 48), (165, z_apex - 15),
                         (165, z_apex - 8), (42, z_apex + 56), (-42, z_apex + 56), (-165, z_apex - 8)],
                True, fill_hex="#6D7A86", stroke_hex="#233F54", lw=0.30)

    # Teja de cumbrera (caballete) semicircular en seccion + clip tornillo inox
    arc_out, arc_in = [], []
    cz_c = z_apex + 55.0
    for k in range(25):
        a = math.radians(15.0 + k * 150.0 / 24.0)
        arc_out.append((102.0 * math.cos(a), cz_c - 16.0 + 96.0 * math.sin(a)))
        arc_in.append((86.0 * math.cos(a), cz_c - 16.0 + 80.0 * math.sin(a)))
    cv.add_poly("TEJA", arc_out + list(reversed(arc_in)), True, fill_hex="#CE674A", stroke_hex="#7A2210", lw=0.40)
    # Clip tornillo superior
    cv.add_line("METAL_CAZ", 0.0, cz_c + 86.0, 0.0, cz_c + 20.0, color_hex="#14191F", lw=0.34)
    cv.add_rect("METAL_CAZ", -8.0, cz_c + 78.0, 8.0, cz_c + 84.0, fill_hex="#DCE4EB", stroke_hex="#14191F", lw=0.22)

    # Roturas izq/der + vigacentral abajo
    cv.add_breakline(-hx, -hx * slope - t_tab, -hx, z2 - hx * slope + 95.0)
    cv.add_breakline(hx, -hx * slope - t_tab, hx, z2 - hx * slope + 95.0)
    cv.add_breakline(-70.0, -290.0, 70.0, -290.0)

    # Cotas
    cv.add_dim_h(-28.0, 28.0, 295.0, z_apex - 10, z_apex - 10, label="56 (paso ventil.)")
    cv.add_slope_marker(-560.0, z2 - 560 * slope + 65.0, slope, length=180.0, dir_x=1.0, label="Pend. 32% (17,7°)", lift_mm=20.0)
    cv.add_slope_marker(560.0, z2 - 560 * slope + 65.0, slope, length=180.0, dir_x=-1.0, label="Pend. 32%", lift_mm=20.0)

    # Llamadas en dos columnas claras
    cv.add_leader((-20, cz_c + 72), (-180, 340), (-340, 340),
                  "TEJA CUMBRERA CON CLIP INOX", "Solape ≥50 mm · fijación en seco sin mortero", align="right", badge=1)
    cv.add_leader((-110, z_apex + 14), (-220, 255), (-340, 255),
                  "REMATE CUMBRERA VENTILADO", "Banda plisada aluminio/butilo microperforada", align="right", badge=2)
    cv.add_leader((-420, z2 + 72 - 420 * slope), (-520, 155), (-580, 155),
                  "TEJA CURVA (CANAL + COBIJA)", "Paso ventilación 5 cm en vértice cumbrera", align="right", badge=3)
    cv.add_leader((-300, z1 + 14 - 300 * slope), (-420, -370), (-290, -370),
                  "DOBLE RASTRELADO MICROVENT.", "Contrarastrel 30 mm + Rastrel 30 mm + lámina", align="right", badge=4)

    cv.add_leader((20, z_apex + 30), (180, 340), (340, 340),
                  "SOPORTE METÁLICO CABALLETE", "Soporte regulable + rastrel cumbrera 45×55", align="left", badge=5)
    cv.add_leader((340, z1 - 30 - 340 * slope), (420, -295), (300, -295),
                  "AISLAMIENTO TÉRMICO XPS (60 mm)", "Continuo en cumbrera s/ lámina transpirable", align="left", badge=6)
    cv.add_leader((480, -18 - 480 * slope), (540, -380), (300, -380),
                  "TABLERO CERÁMICO + M-5 + VIGA", "Bardo 40 mm + reg. 20 mm s/ viga cumbrera", align="left", badge=7)

    cv.export_dxf(r"d:\C2\planos_2d\detalle6_cumbrera_teja_ventilada.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle6_cumbrera_teja_ventilada.pdf", r"d:\C2\planos_2d\detalle6_cumbrera_teja_ventilada.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle6_cumbrera_teja_ventilada.svg")
    print("Generated DET-06 (Cumbrera Ventilada Teja Curva) 2D CAD.")


# ==============================================================================
# DET-07: Faldon de Teja Mixta sobre Doble Rastrel + Encuentro Paramento
# ==============================================================================
def build_detalle7_teja_mixta_2d():
    meta = DETAILS["detalle7_teja_mixta"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(118.0, 96.0))

    slope = p["slope"]          # 0.36
    ang = math.atan(slope)
    deg = math.degrees(ang)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 1000..1160
    deck_end = p["deck_end_x"]

    # Base del forjado inclinado en x: z_base(x) = slope * x
    def zb(x): return slope * x
    t_f = p["forjado_h"] / cos_a
    t_reg = p["reg_h"] / cos_a
    t_at = p["at_h"] / cos_a
    t_cr = p["contrarastrel_h"] / cos_a
    t_ra = p["rastrel_h"] / cos_a

    # 1. Forjado estructural inclinado
    f_pts = [(0, -t_f), (deck_end, zb(deck_end) - t_f), (deck_end, zb(deck_end)), (0, 0)]
    cv.add_poly("FORJADO", f_pts, True, fill_hex="#E2E6E9", stroke_hex="#252B33", lw=0.40)
    cv.add_hatch("HATCH_LIGHT", "concrete", f_pts, spacing=18.0)

    # Regularizacion + barrera vapor
    r_pts = [(0, 0), (deck_end, zb(deck_end)), (deck_end, zb(deck_end) + t_reg), (0, t_reg)]
    cv.add_poly("MORTERO", r_pts, True, fill_hex="#D7D0C4", stroke_hex="#5E5850", lw=0.22)
    z1 = t_reg
    cv.add_line("MEMBRANA", 0, z1 + 1.5, deck_end, zb(deck_end) + z1 + 1.5, color_hex="#101214", lw=0.38)

    # XPS 70 mm entre contrarastreles (en corte longitudinal paralelo a contrarastrel)
    z2 = z1 + t_at
    at_pts = [(0, z1 + 3), (deck_end, zb(deck_end) + z1 + 3), (deck_end, zb(deck_end) + z2), (0, z2)]
    cv.add_poly("AISLAMIENTO", at_pts, True, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.28)
    cv.add_hatch("HATCH_INSUL", "batt_insul", at_pts, spacing=16.0, angle_deg=deg)
    # Contrarastrel + Lamina transpirable encima
    z3 = z2 + t_cr
    cr_pts = [(0, z2), (deck_end, zb(deck_end) + z2), (deck_end, zb(deck_end) + z3), (0, z3)]
    cv.add_poly("MADERA", cr_pts, True, fill_hex="#EDD6B6", stroke_hex="#754E1E", lw=0.26)
    cv.add_hatch("HATCH_WOOD", "wood_grain", cr_pts, spacing=8.0, angle_deg=deg)
    cv.add_line("CAPA_SEP", 0, z2 + 1.5, deck_end, zb(deck_end) + z2 + 1.5, color_hex="#24749C", lw=0.42)

    # Rastreles horizontales paso 355 mm (+ primer rastrel recrecido en x~140 mm)
    for k, d_a in enumerate((130.0, 485.0, 840.0)):
        xc = d_a * cos_a
        zc_b = zb(xc) + z3
        rh = 52.0 if k == 0 else 35.0
        hw = 20.0
        pts_r = [
            (xc - hw * cos_a, zc_b - hw * sin_a),
            (xc + hw * cos_a, zc_b + hw * sin_a),
            (xc + hw * cos_a - rh * sin_a, zc_b + hw * sin_a + rh * cos_a),
            (xc - hw * cos_a - rh * sin_a, zc_b - hw * sin_a + rh * cos_a),
        ]
        cv.add_poly("MADERA", pts_r, True, fill_hex="#DFBA84", stroke_hex="#754E1E", lw=0.28)
        cv.add_hatch("HATCH_WOOD", "wood_cut", pts_r, spacing=5.0)

    # 2. Tejas ceramicas mixtas encajadas sobre rastrel con tacon de enganche
    ux, uz = cos_a, sin_a
    nx, nz = -sin_a, cos_a
    for k in range(3):
        d0 = 20.0 + k * 335.0
        d1 = min(d0 + 430.0, (deck_end - 8.0) / cos_a)
        xb0 = d0 * cos_a
        zb0 = zb(xb0) + z3 + 38.0 / cos_a + k * 4.0
        xb1 = d1 * cos_a
        zb1 = zb0 + (d1 - d0) * sin_a
        # Teja con tacon inferior sobre rastrel + cuerpo escalonado
        tp = [
            (xb0, zb0), (xb1 - 70 * ux, zb1 - 70 * uz),
            (xb1 - 70 * ux - 12 * nx, zb1 - 70 * uz - 12 * nz),
            (xb1 - 45 * ux - 12 * nx, zb1 - 45 * uz - 12 * nz),
            (xb1 - 45 * ux, zb1 - 45 * uz), (xb1, zb1),
            (xb1 + 18 * nx, zb1 + 18 * nz), (xb0 + 18 * nx, zb0 + 18 * nz),
        ]
        cv.add_poly("TEJA", tp, True, fill_hex="#E2967D", stroke_hex="#7A2210", lw=0.34)
        cv.add_hatch("HATCH_BRICK", "diag45", tp, spacing=10.0)

    # 3. Paramento vertical (LHD 140 + Enfoscado 20 + Roza para babero + Albardilla)
    z_mbot = zb(deck_end) - t_f
    z_mtop = p["wall_top_z"]
    cv.add_rect("LADRILLO", wx0 + 20, z_mbot, wx1, z_mtop, fill_hex="#F7E4DC", stroke_hex="#7D3522", lw=0.30)
    zc = z_mbot
    while zc + 52 < z_mtop:
        draw_hollow_brick_section(cv, wx0 + 20, zc, wx1, min(zc + 60, z_mtop), cols=2, rows=2)
        zc += 70.0
    cv.add_rect("MORTERO", wx0, z_mbot, wx0 + 20, z_mtop, fill_hex="#EAE5DC", stroke_hex="#5E5850", lw=0.22)
    cv.add_rect("FORJADO", wx0 - 10, z_mtop, wx1 + 15, z_mtop + 38, fill_hex="#EFECE6", stroke_hex="#252B33", lw=0.34)

    # 4. Banda impermeable autoadhesiva >= 100 mm + Babero Zinc engatillado >= 250 mm en roza (L2 p.87)
    z_tile_wall = zb(deck_end) + z3 + 64.0
    z_bab_top = z_tile_wall + p["babero_up_h"]
    # Banda impermeable autoadhesiva (oscuro)
    cv.add_poly("MEMBRANA", [(deck_end - 130, z_tile_wall - 40), (wx0, z_tile_wall + 5),
                             (wx0, z_tile_wall + 135), (wx0 - 4, z_tile_wall + 135),
                             (wx0 - 4, z_tile_wall + 10), (deck_end - 130, z_tile_wall - 34)],
                True, fill_hex="#1E2126", stroke_hex="#101214", lw=0.34)
    # Babero metalico zinc engatillado introducido en roza 30x30 + sellado masilla
    cv.add_poly("ZINC", [(deck_end - 150, z_tile_wall - 44), (wx0 - 10, z_tile_wall + 8),
                         (wx0 - 10, z_bab_top), (wx0 + 24, z_bab_top + 12),
                         (wx0 + 24, z_bab_top + 2), (wx0 - 2, z_bab_top - 6),
                         (wx0 - 2, z_tile_wall + 4), (deck_end - 150, z_tile_wall - 50)],
                True, fill_hex="#BACBD9", stroke_hex="#30495E", lw=0.34)

    # Ventilacion y roturas
    cv.add_flow_arrow([(140, z2 + 78), (740, zb(740) + z2 + 24)], color_hex="#1985A1", lw=0.26, head_mm=9.0, dash=(3.5, 2.0))
    cv.add_breakline(0.0, -t_f, 0.0, z3 + 60.0)
    cv.add_breakline(wx0, z_mbot, wx1, z_mbot)

    # Cotas
    cv.add_slope_marker(320.0, zb(320.0) + z3 + 110.0, slope, length=180.0, dir_x=1.0, label="Pend. 36% (19,8°)", lift_mm=22.0)
    cv.add_dim_v(z_tile_wall, z_bab_top, 1245.0, wx1, wx1, label="≥250 (babero)")
    cv.add_dim_h(deck_end - 150.0, deck_end, z_tile_wall + 315.0, z_tile_wall - 44, z_tile_wall, label="≥150 solape")

    # Llamadas
    cv.add_leader((wx0 - 6, z_bab_top - 70), (760, 825), (600, 825),
                  "BABERO ZINC + ROZA SELLADA (≥25 cm)", "Chapa 0,8 mm engatillada con entregas s/ roza", align="right", badge=1)
    cv.add_leader((wx0 - 2, z_tile_wall + 70), (720, 735), (600, 735),
                  "BANDA IMPERMEABLE AUTOADHESIVA", "Entrega ≥10 cm s/ teja y paramento (L2 p.87)", align="right", badge=2)
    cv.add_leader((520, zb(520) + z3 + 48), (360, 625), (-40, 625),
                  "TEJA CERÁMICA MIXTA (440×260 mm)", "Doble encaje con tacón y fijación inox s/ rastrel", align="right", badge=3)
    cv.add_leader((130 * cos_a, zb(130 * cos_a) + z3 + 24), (80, 465), (-40, 465),
                  "DOBLE RASTREL (+20 mm 1er RASTREL)", "Contrarastrel 35 mm + Rastrel horizontal 35 mm", align="right", badge=4)
    cv.add_leader((340, zb(340) + z1 + 35), (140, 380), (-40, 380),
                  "XPS (70 mm) + LÁMINA TRANSPIRABLE", "Aislamiento continuo y cámara ventilada", align="right", badge=5)
    cv.add_leader((460, zb(460) - 90), (240, -180), (-40, -180),
                  "FORJADO INCLINADO (220 mm + M-5)", "Soporte estructural 36% + paramento LHD enfoscado", align="right", badge=6)

    cv.export_dxf(r"d:\C2\planos_2d\detalle7_teja_mixta_paramento.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle7_teja_mixta_paramento.pdf", r"d:\C2\planos_2d\detalle7_teja_mixta_paramento.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle7_teja_mixta_paramento.svg")
    print("Generated DET-07 (Teja Mixta + Paramento) 2D CAD.")


# ==============================================================================
# DET-08: Tejado de Pizarra Natural QTP-14 (Alero, Emboble, Ganchos y Doble Rastrel)
# ==============================================================================
def build_detalle8_pizarra_2d():
    meta = DETAILS["detalle8_pizarra"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(132.0, 108.0))

    slope = p["slope"]          # 0.56
    ang = math.atan(slope)
    deg = math.degrees(ang)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 110..290
    x_end = 980.0

    def zb(x): return slope * (x - wx0)
    t_f = p["forjado_h"] / cos_a
    t_reg = p["reg_h"] / cos_a
    t_cr = p["contrarastrel_h"] / cos_a
    t_cam = p["camara_h"] / cos_a

    # 1. Muro de fachada bajo alero
    z_mbot = -260.0
    cv.add_rect("LADRILLO", wx0, z_mbot, wx1, 0.0, fill_hex="#F7E4DC", stroke_hex="#7D3522", lw=0.30)
    zc = z_mbot
    while zc + 52.0 < -10.0:
        draw_hollow_brick_section(cv, wx0 + 10, zc, wx1 - 10, min(zc + 60, -12.0), cols=2, rows=2)
        zc += 68.0
    cv.add_rect("MORTERO", wx0 - 14, z_mbot, wx0, -25.0, fill_hex="#EAE5DC", stroke_hex="#5E5850", lw=0.22)

    # 2. Forjado unidireccional inclinado (con alero volado hasta x=50)
    x_alero = wx0 - 60.0  # 50
    f_pts = [(x_alero, zb(x_alero) - t_f * 0.6), (wx0, -t_f), (x_end, zb(x_end) - t_f),
             (x_end, zb(x_end)), (x_alero, zb(x_alero))]
    cv.add_poly("FORJADO", f_pts, True, fill_hex="#E2E6E9", stroke_hex="#252B33", lw=0.40)
    cv.add_hatch("HATCH_LIGHT", "concrete", f_pts, spacing=18.0)

    r_pts = [(x_alero, zb(x_alero)), (x_end, zb(x_end)), (x_end, zb(x_end) + t_reg), (x_alero, zb(x_alero) + t_reg)]
    cv.add_poly("MORTERO", r_pts, True, fill_hex="#D7D0C4", stroke_hex="#5E5850", lw=0.22)

    # 3. Contrarastrel 50x50 + XPS 50 mm entre contrarastreles (rotura puente termico) + camara 30 mm
    z1 = t_reg
    z2 = z1 + t_cr
    at_pts = [(x_alero + 45, zb(x_alero + 45) + z1), (x_end, zb(x_end) + z1),
              (x_end, zb(x_end) + z2), (x_alero + 45, zb(x_alero + 45) + z2)]
    cv.add_poly("AISLAMIENTO", at_pts, True, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.26)
    cv.add_hatch("HATCH_INSUL", "batt_insul", at_pts, spacing=14.0, angle_deg=deg)

    # Contrarastrel sobreXPS (liston vertical de camara ventilada 30 mm!)
    z3 = z2 + t_cam
    cam_pts = [(x_alero + 30, zb(x_alero + 30) + z2), (x_end, zb(x_end) + z2),
               (x_end, zb(x_end) + z3), (x_alero + 30, zb(x_alero + 30) + z3)]
    cv.add_poly("MADERA", cam_pts, True, fill_hex="#F4E3C9", stroke_hex="#754E1E", lw=0.24)
    cv.add_hatch("HATCH_WOOD", "wood_grain", cam_pts, spacing=7.0, angle_deg=deg)

    # Chapa goteron zinc en borde del alero bajo primera hilada pizarra
    gx0, gz0 = x_alero - 22.0, zb(x_alero) + z3 - 22.0
    cv.add_poly("ZINC", [(gx0, gz0 - 20), (x_alero + 10, zb(x_alero + 10) + z3 + 2),
                         (x_alero + 160, zb(x_alero + 160) + z3 + 2), (x_alero + 160, zb(x_alero + 160) + z3 - 2),
                         (x_alero + 8, zb(x_alero + 8) + z3 - 3), (gx0 + 4, gz0 - 20)],
                True, fill_hex="#BACBD9", stroke_hex="#30495E", lw=0.30)

    # 4. Rastreles horizontales (40x25 mm) paso exacto V = 100 mm vista!
    ux, uz = cos_a, sin_a
    nx, nz = -sin_a, cos_a
    d_start = 45.0
    vista = p["slate_vista"]  # 100 mm exact
    for k in range(10):
        da = d_start + k * vista
        rx = x_alero + da * ux
        if rx > x_end - 30:
            break
        rz = zb(rx) + z3
        rh = 25.0
        hw = 18.0
        rpts = [
            (rx - hw * ux, rz - hw * uz), (rx + hw * ux, rz + hw * uz),
            (rx + hw * ux + rh * nx, rz + hw * uz + rh * nz),
            (rx - hw * ux + rh * nx, rz - hw * uz + rh * nz),
        ]
        cv.add_poly("MADERA", rpts, True, fill_hex="#D9AE73", stroke_hex="#754E1E", lw=0.26)
        cv.add_hatch("HATCH_WOOD", "wood_cut", rpts, spacing=4.0)

    # 5. Lajas de Pizarra Natural 300x200x6.5 mm: Emboble doble en alero (vuelo 50 mm) + hiladas V=100, R=100 mm + ganchos inox
    slate_t = p["slate_t"]
    d_tip0 = -p["vuelo_alero"]  # -50 mm vuelo sobre borde alero (QTP-14)
    for k in range(9):
        # Hilada 0 = emboble (mas corta 200 mm debajo), luego hiladas 300 mm desplazadas V=100 mm
        L_sl = 200.0 if k == 0 else p["slate_l"]
        da = d_tip0 + (0.0 if k == 0 else (k - 1) * vista)
        # Elevacion incremental minima para apilamiento limpio de 3 solapes sin colisionar
        n_lift = 25.0 + 3.0 + (k % 3) * (slate_t + 2.5) + (0.0 if k == 0 else (7.0 if k == 1 else k * 0.4))
        if k == 0:
            n_lift = 25.0 + 2.0
        else:
            n_lift = 25.0 + 10.0 + (k - 1) * 3.8
        p0x = x_alero + da * ux + n_lift * nx
        p0z = zb(x_alero) + z3 + da * uz + n_lift * nz
        p1x = p0x + min(L_sl, (x_end - p0x) / ux) * ux
        p1z = p0z + min(L_sl, (x_end - p0x) / ux) * uz
        if p1x <= p0x + 15.0:
            continue
        sl_poly = [(p0x, p0z), (p1x, p1z), (p1x + slate_t * nx, p1z + slate_t * nz), (p0x + slate_t * nx, p0z + slate_t * nz)]
        cv.add_poly("PIZARRA", sl_poly, True, fill_hex="#474F5B", stroke_hex="#181C22", lw=0.32)
        # Gancho visto en borde inferior de cada laja regular (k >= 1)
        if k >= 1:
            g_pts = [(p0x - 4 * ux, p0z - 4 * uz), (p0x + 12 * ux, p0z + 12 * uz), (p0x - 2 * nx, p0z - 2 * nz)]
            cv.add_poly("METAL_CAZ", g_pts, False, fill_hex=None, stroke_hex="#9AA7B2", lw=0.30)

    # Flujo aire y agua
    cv.add_flow_arrow([(120, zb(120) + z2 + 12), (820, zb(820) + z2 + 12)], color_hex="#1985A1", lw=0.26, head_mm=9.0, dash=(3.5, 2.0))
    cv.add_flow_arrow([(520, zb(520) + z3 + 105), (x_alero - 25, zb(x_alero - 25) + z3 + 95)], color_hex="#0B72B9", lw=0.32, head_mm=11.0)

    cv.add_breakline(x_end, zb(x_end) - t_f, x_end, zb(x_end) + z3 + 95.0)
    cv.add_breakline(wx0, z_mbot, wx1, z_mbot)

    # Cotas exactas QTP-14
    cv.add_slope_marker(460.0, zb(460.0) + z3 + 95.0, slope, length=160.0, dir_x=-1.0, label="Pend. 56% (29,2°)", lift_mm=22.0)
    cv.add_dim_h(x_alero + d_tip0 * ux, x_alero, 220.0, zb(x_alero) + 35, zb(x_alero) + 35, label="50 (vuelo)")
    cv.add_dim_h(320.0, 420.0, -295.0, 0.0, 0.0, label="Paso rastrel 100")

    # Llamadas
    cv.add_leader((340, zb(340) + z3 + 52), (160, 560), (-45, 560),
                  "PIZARRA NATURAL (300×200×6,5 mm)", "Solape R=100 mm · Vista V=100 mm · Emboble", align="right", badge=1)
    cv.add_leader((210, zb(210) + z3 + 38), (90, 465), (-45, 465),
                  "GANCHO VISTO ACERO INOX Ø2,7 mm", "Clavado al rastrel · sin perforar zona vista", align="right", badge=2)
    cv.add_leader((x_alero - 5, zb(x_alero) + z3 - 10), (0, 355), (-45, 355),
                  "CHAPA GOTERÓN DE ZINC + EMBOBLE", "Doble pieza de arranque + vuelo 50 mm (QTP-14)", align="right", badge=3)
    cv.add_leader((520, zb(520) + z3 + 12), (740, 200), (1040, 200),
                  "RASTREL HORIZONTAL 40×25 mm", "Sobre cámara ventilación ≥30 mm (L4 p.51)", align="left", badge=4)
    cv.add_leader((610, zb(610) + z1 + 25), (820, 105), (1040, 105),
                  "AISLAMIENTO 50 mm + CONTRARASTREL", "Rotura puente térmico entre contrarastreles", align="left", badge=5)
    cv.add_leader((480, zb(480) - 90), (800, -145), (1040, -145),
                  "FORJADO INCLINADO (56%) + MURO", "Forjado vigueta/bovedilla + reg. 20 mm", align="left", badge=6)

    cv.export_dxf(r"d:\C2\planos_2d\detalle8_pizarra_alero_qtp14.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle8_pizarra_alero_qtp14.pdf", r"d:\C2\planos_2d\detalle8_pizarra_alero_qtp14.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle8_pizarra_alero_qtp14.svg")
    print("Generated DET-08 (Tejado Pizarra Natural QTP-14) 2D CAD.")


# ==============================================================================
# DET-09: Cubierta Metalica Zinc Prepatinado en Junta Alzada + Seccion Junta VMZ
# ==============================================================================
def build_detalle9_zinc_2d():
    meta = DETAILS["detalle9_zinc"]
    p = meta["params"]
    cv = SheetCanvas2D(meta, scale_denom=5.0, origin_sheet=(124.0, 96.0))

    slope = p["slope"]          # 0.16
    ang = math.atan(slope)
    deg = math.degrees(ang)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    deck_end = p["deck_end_x"]  # 1000
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 1000..1160

    def zb(x): return slope * x
    t_f = p["forjado_h"] / cos_a
    t_at = p["at_h"] / cos_a
    t_cam = p["camara_h"] / cos_a
    t_mad = p["entarimado_h"] / cos_a
    t_dr = p["capa_dren_h"] / cos_a

    # 1. Forjado inclinado
    f_pts = [(0, -t_f), (deck_end, zb(deck_end) - t_f), (deck_end, zb(deck_end)), (0, 0)]
    cv.add_poly("FORJADO", f_pts, True, fill_hex="#E2E6E9", stroke_hex="#252B33", lw=0.40)
    cv.add_hatch("HATCH_LIGHT", "concrete", f_pts, spacing=18.0)

    # Barrera de vapor + XPS/PIR 80 mm entre listones
    cv.add_line("MEMBRANA", 0, 2, deck_end, zb(deck_end) + 2, color_hex="#101214", lw=0.40)
    z1 = 3.0
    z2 = z1 + t_at
    at_pts = [(0, z1), (deck_end, zb(deck_end) + z1), (deck_end, zb(deck_end) + z2), (0, z2)]
    cv.add_poly("AISLAMIENTO", at_pts, True, fill_hex="#FDF0B8", stroke_hex="#A8810A", lw=0.28)
    cv.add_hatch("HATCH_INSUL", "batt_insul", at_pts, spacing=16.0, angle_deg=deg)

    # Camara ventilada 40 mm sobre rastreles
    z3 = z2 + t_cam
    cam_pts = [(0, z2), (deck_end, zb(deck_end) + z2), (deck_end, zb(deck_end) + z3), (0, z3)]
    cv.add_poly("MADERA", cam_pts, True, fill_hex="#FAF5EE", stroke_hex="#754E1E", lw=0.22)
    cv.add_flow_arrow([(60, z2 + 20), (880, zb(880) + z2 + 20)], color_hex="#1985A1", lw=0.28, head_mm=10.0, dash=(4.0, 2.5))

    # Entarimado continuo de madera 24 mm (tablas con separacion junta 8 mm!)
    z4 = z3 + t_mad
    step_tab = 130.0
    x_cur = 0.0
    while x_cur < deck_end - 25.0:
        x_nxt = min(x_cur + step_tab - 8.0, deck_end - 8.0)
        tpts = [(x_cur, zb(x_cur) + z3), (x_nxt, zb(x_nxt) + z3),
                (x_nxt, zb(x_nxt) + z4), (x_cur, zb(x_cur) + z4)]
        cv.add_poly("MADERA", tpts, True, fill_hex="#DFBA84", stroke_hex="#754E1E", lw=0.26)
        cv.add_hatch("HATCH_WOOD", "wood_cut", tpts, spacing=5.0)
        x_cur += step_tab

    # Capa separadora drenante estructurada (8 mm antiruido/drenante)
    z5 = z4 + t_dr
    dr_pts = [(0, z4), (deck_end, zb(deck_end) + z4), (deck_end, zb(deck_end) + z5), (0, z5)]
    cv.add_poly("CAPA_SEP", dr_pts, True, fill_hex="#D2ECF7", stroke_hex="#24749C", lw=0.25)

    # Bandeja de Zinc prepatinado VMZ (con pliegue alzado H=28 mm visto de fondo + entrega en peto)
    z_seam_top = z5 + p["seam_h"]
    # Alzado de junta alzada visto tras el plano de corte
    cv.add_poly("ZINC", [(0, zb(0) + z5), (deck_end - 8, zb(deck_end - 8) + z5),
                         (deck_end - 8, zb(deck_end - 8) + z_seam_top), (0, zb(0) + z_seam_top)],
                True, fill_hex="#CFD9E2", stroke_hex="#30495E", lw=0.26)
    # Entrega vertical de bandeja zinc contra muro + junta de chapa en corte fuerte
    zn_pts = [(0, z5), (deck_end - 6, zb(deck_end - 6) + z5), (deck_end - 6, zb(deck_end - 6) + z5 + 160),
              (deck_end - 11, zb(deck_end - 11) + z5 + 160), (deck_end - 11, zb(deck_end - 11) + z5 + 4), (0, z5 + 4)]
    cv.add_poly("ZINC", zn_pts, True, fill_hex="#6D7A86", stroke_hex="#14191F", lw=0.45)

    # Muro peto + babero engatillado + albardilla metalica zinc
    z_mbot = -t_f
    z_mtop = 690.0
    cv.add_rect("LADRILLO", wx0 + 20, z_mbot, wx1, z_mtop, fill_hex="#F7E4DC", stroke_hex="#7D3522", lw=0.30)
    zc = z_mbot
    while zc + 52.0 < z_mtop:
        draw_hollow_brick_section(cv, wx0 + 20, zc, wx1, min(zc + 60, z_mtop), cols=2, rows=2)
        zc += 70.0
    cv.add_rect("MORTERO", wx0, z_mbot, wx0 + 20, z_mtop, fill_hex="#EAE5DC", stroke_hex="#5E5850", lw=0.22)
    # Babero engatillado solapando entrega zinc
    z_bab_top = zb(deck_end) + z5 + 225.0
    cv.add_poly("ZINC", [(deck_end - 14, zb(deck_end) + z5 + 65), (deck_end - 14, z_bab_top),
                         (wx0 + 22, z_bab_top + 10), (wx0 + 22, z_bab_top), (wx0 - 6, z_bab_top - 8),
                         (wx0 - 6, zb(deck_end) + z5 + 65)],
                True, fill_hex="#A8B8C7", stroke_hex="#233F54", lw=0.30)
    # Coronacion albardilla zinc engatillada con goterones
    cv.add_poly("ZINC", [(wx0 - 24, z_mtop - 12), (wx0 - 20, z_mtop - 12), (wx0 - 20, z_mtop + 28),
                         (wx1 + 20, z_mtop + 38), (wx1 + 20, z_mtop - 12), (wx1 + 24, z_mtop - 12),
                         (wx1 + 24, z_mtop + 43), (wx0 - 24, z_mtop + 33)],
                True, fill_hex="#A8B8C7", stroke_hex="#14191F", lw=0.36)

    # RECUADRO DETALLE AMPLIADO (Escala esquematica): SECCION TRANSVERSAL JUNTA ALZADA + PATA FIJA/CORREDERA (L6 p.11)
    ix0, iz0 = -55.0, 470.0
    cv.add_rect("FRAME", ix0 - 15, iz0 - 30, ix0 + 340, iz0 + 180, fill_hex="#FAF9F6", stroke_hex="#505A66", lw=0.24)
    cv.add_text("CALLOUTS", ix0 - 2, iz0 + 158, "SECCIÓN JUNTA ALZADA (MÓD. 580 mm)", height_sheet_mm=1.95, color_hex="#9C3B26", align="left")
    # Entarimado base + patas + bandejas izquierda/derecha engatilladas
    cv.add_rect("MADERA", ix0 + 12, iz0, ix0 + 312, iz0 + 26, fill_hex="#DFBA84", stroke_hex="#754E1E", lw=0.24)
    # Pata fija / corredera inoxidable enganchada en junta central
    jx = ix0 + 162
    cv.add_poly("METAL_CAZ", [(jx - 40, iz0 + 26), (jx - 4, iz0 + 26), (jx - 4, iz0 + 96), (jx + 14, iz0 + 96),
                              (jx + 14, iz0 + 84), (jx + 4, iz0 + 84), (jx + 4, iz0 + 32), (jx - 40, iz0 + 32)],
                True, fill_hex="#CFD9E2", stroke_hex="#14191F", lw=0.26)
    # Dos bandejas engatilladas H=25 mm en doble pliegue
    cv.add_poly("ZINC", [(ix0 + 18, iz0 + 32), (jx - 8, iz0 + 32), (jx - 8, iz0 + 105), (jx + 18, iz0 + 105),
                         (jx + 18, iz0 + 78), (jx + 10, iz0 + 78), (jx + 10, iz0 + 98), (jx - 2, iz0 + 98),
                         (jx - 2, iz0 + 38), (ix0 + 18, iz0 + 38)],
                True, fill_hex="#6D7A86", stroke_hex="#14191F", lw=0.30)
    cv.add_poly("ZINC", [(jx + 8, iz0 + 32), (ix0 + 306, iz0 + 32), (ix0 + 306, iz0 + 38), (jx + 14, iz0 + 38),
                         (jx + 14, iz0 + 112), (jx - 12, iz0 + 112), (jx - 12, iz0 + 82), (jx - 6, iz0 + 82),
                         (jx - 6, iz0 + 104), (jx + 8, iz0 + 104)],
                True, fill_hex="#8C9AA6", stroke_hex="#14191F", lw=0.30)
    cv.add_text("NOTES", ix0 + 14, iz0 + 124, "Doble engatillado H=25 + pata fija/corredera inox", height_sheet_mm=1.75, color_hex="#30495E", align="left")

    cv.add_breakline(0.0, -t_f, 0.0, z_seam_top + 35.0)
    cv.add_breakline(wx0, z_mbot, wx1, z_mbot)

    cv.add_slope_marker(460.0, zb(460.0) + z_seam_top + 18.0, slope, length=180.0, dir_x=-1.0, label="Pend. 16% (9,1°)", lift_mm=20.0)
    cv.add_dim_h(0.0, deck_end, -275.0, -t_f, -t_f, label="1000 (faldón)")
    cv.add_dim_v(-t_f, zb(deck_end) + z5, 1245.0, wx1, wx1, label="520 (sección)")
    cv.add_dim_v(zb(deck_end) + z5, z_mtop + 43, 1245.0, wx1, wx1, label="415 (peto)")

    # Llamadas (bien separadas del recuadro izquierdo y peto derecho)
    cv.add_leader((wx0 - 8, z_bab_top - 45), (840, 745), (760, 745),
                  "BABERO ZINC + ALBARDILLA", "Remate peto engatillado con doble goterón", align="right", badge=1)
    cv.add_leader((620, zb(620) + z5 + 14), (800, 645), (760, 645),
                  "BANDEJA ZINC VMZ (MÓD. 580)", "Junta alzada doble engatillada H=25 mm", align="right", badge=2)
    cv.add_leader((520, zb(520) + z4 + 4), (800, 545), (760, 545),
                  "CAPA DRENANTE (8 mm)", "Desolidarización y microventilación zinc", align="right", badge=3)
    cv.add_leader((460, zb(460) + z3 + 12), (240, 290), (-45, 290),
                  "ENTARIMADO MADERA PINO (24 mm)", "Tablas machihembradas/juntas 8 mm s/ cámara 40", align="right", badge=4)
    cv.add_leader((320, zb(320) + z1 + 40), (140, 175), (-45, 175),
                  "AISLAMIENTO (80 mm) + BV (3 mm)", "Aislamiento continuo s/ soporte inclinado 16%", align="right", badge=5)
    cv.add_leader((360, -85), (160, -155), (-45, -155),
                  "SOPORTE ESTRUCTURAL (200 mm)", "Faldón hormigón + peto LHD 140 enfoscado", align="right", badge=6)

    cv.export_dxf(r"d:\C2\planos_2d\detalle9_zinc_junta_alzada.dxf")
    cv.export_pdf_and_png(r"d:\C2\planos_2d\detalle9_zinc_junta_alzada.pdf", r"d:\C2\planos_2d\detalle9_zinc_junta_alzada.png")
    cv.export_svg(r"d:\C2\planos_2d\detalle9_zinc_junta_alzada.svg")
    print("Generated DET-09 (Cubierta Zinc Junta Alzada) 2D CAD.")


def build_part2_2d():
    build_detalle4_plots_2d()
    build_detalle5_alero_teja_2d()
    build_detalle6_cumbrera_teja_2d()
    build_detalle7_teja_mixta_2d()
    build_detalle8_pizarra_2d()
    build_detalle9_zinc_2d()


if __name__ == "__main__":
    build_part2_2d()
