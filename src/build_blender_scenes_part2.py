r"""
Builds Exact Millimetric 3D Models (.blend + .glb) and Renders Photorealistic Cycles HIP Shots
for Details 4 through 9 (Azotea Plots, Teja Curva Alero, Cumbrera Ventilada, Teja Mixta, Pizarra Natural, Zinc Junta Alzada).
"""

import math
import os
import sys
import bmesh
import bpy
from mathutils import Vector

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from specs import DETAILS
import blender_geo as geo

MM = geo.MM


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def join_objects(objs, target_name, col):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) == 1:
        objs[0].name = target_name
        if objs[0].data:
            objs[0].data.name = target_name
        geo.link_obj(objs[0], col)
        return objs[0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = target_name
    if joined.data:
        joined.data.name = target_name
    geo.link_obj(joined, col)
    return joined


def export_model_glb_and_blend(model_objs, blend_path, glb_path):
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.object.select_all(action="DESELECT")
    for o in model_objs:
        if o is not None:
            o.hide_viewport = False
            o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        use_selection=True,
        export_materials="EXPORT",
        export_normals=True,
        export_apply=True,
        export_yup=True,
    )
    print(f"Exported BLEND + GLB: {glb_path}")


# ==============================================================================
# DET-04: Azotea Invertida Transitable · Pavimento Flotante sobre PLOTS
# ==============================================================================
def build_detalle4_plots():
    reset_scene()
    mats = geo.get_material_palette()
    p = DETAILS["detalle4_plots"]["params"]
    col = geo.ensure_collection("Detalle4_Plots")

    dx_end = p["deck_end_x"]          # 1020
    j_x0, j_x1 = dx_end, dx_end + p["junta_eps_w"]        # 1020..1035
    ei_x0, ei_x1 = j_x1, j_x1 + p["enfoscado_int_w"]      # 1035..1050
    pb_x0, pb_x1 = ei_x1, ei_x1 + p["peto_brick_w"]       # 1050..1190
    ee_x0, ee_x1 = pb_x1, pb_x1 + p["enfoscado_ext_w"]    # 1190..1210
    y0, y1 = -440.0, 440.0

    def z_fp_core(x): return p["fp_min_h"] + p["slope"] * x
    def z_fp_top(x): return z_fp_core(x) + p["fp_reg_h"]
    def z_i_top(x): return z_fp_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_at_top(x): return z_cs_top(x) + p["at_h"]
    z_losa_bot = z_at_top(dx_end) + p["plot_h"]
    z_losa_top = z_losa_bot + p["tile_h"]

    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]
    model_objs = []

    # SR Forjado + viguetas + zuncho + senos + bovedillas reales
    sr_parts = [
        geo.make_box_mm("SR_Comp", 0.0, ee_x1, y0, y1, comp_bot, 0.0, mats["concrete"], col, tile_size_m=0.45),
        geo.make_prism_xz(
            "SR_Macizado",
            [(806.0, comp_bot), (860.0, comp_bot), (860.0, forj_bot),
             (840.0, forj_bot), (840.0, forj_bot + 40.0), (814.0, forj_bot + 43.0), (808.0, forj_bot + 50.0)],
            y0, y1, mats["concrete"], col, bevel_mm=0.0
        ),
    ]
    for vx in (200.0, 780.0):
        vp = [(vx - 60, forj_bot), (vx + 60, forj_bot), (vx + 60, forj_bot + 40),
              (vx + 34, forj_bot + 43), (vx + 28, forj_bot + 50), (vx + 26, comp_bot),
              (vx - 26, comp_bot), (vx - 28, forj_bot + 50), (vx - 34, forj_bot + 43),
              (vx - 60, forj_bot + 40)]
        sr_parts.append(geo.make_prism_xz(f"Vig_{int(vx)}", vp, y0, y1, mats["concrete"], col, bevel_mm=0.4))
        for rx in (vx - 28, vx + 28):
            sr_parts.append(geo.make_box_mm(f"Reb_{int(vx)}_{int(rx)}", rx - 4, rx + 4, y0, y1, forj_bot + 16, forj_bot + 24, mats["rebar"], col, bevel_mm=0.2))

    bovs = []
    added_senos = False
    for yb in range(-440, 440, 220):
        yb1 = min(yb + 217.0, 440.0)
        bov_c, s_cl, s_cr = geo.make_bovedilla_ceramica(f"BovC_{yb}", 200.0, 780.0, yb, yb1, forj_bot, comp_bot, mats["brick"], col)
        bov_l, _, s_lr = geo.make_bovedilla_ceramica(f"BovL_{yb}", -380.0, 200.0, yb, yb1, forj_bot, comp_bot, mats["brick"], col, clip_x0=0.0)
        bovs.extend([bov_l, bov_c])
        if not added_senos:
            sr_parts.append(geo.make_prism_xz("D4_SenoL", s_lr, y0, y1, mats["concrete"], col, bevel_mm=0.0))
            sr_parts.append(geo.make_prism_xz("D4_SenoCL", s_cl, y0, y1, mats["concrete"], col, bevel_mm=0.0))
            sr_parts.append(geo.make_prism_xz("D4_SenoCR", s_cr, y0, y1, mats["concrete"], col, bevel_mm=0.0))
            added_senos = True
    model_objs.append(join_objects(sr_parts, "D4_SR_Forjado", col))
    model_objs.append(geo.make_box_mm("D4_SR_Zuncho", 860.0, ee_x1, y0, y1, forj_bot, comp_bot, mats["concrete"], col, tile_size_m=0.45))
    model_objs.append(join_objects(bovs, "D4_SR_Bovedillas", col))

    # Peto + Enfoscado + Barrera antihumedad + Albardilla piedra artificial con goteron
    bricks, mortars = [], []
    course_h = 72.0
    brick_l = 290.0
    zc, row_i = 0.0, 0
    peto_top = p["peto_top_z"]
    while zc + 50.0 < peto_top:
        bh = min(62.0, peto_top - zc - 8.0)
        y_off = 0.0 if (row_i % 2 == 0) else -145.0
        yc = y0 + y_off
        while yc < y1 - 2.0:
            ya, yb_b = max(y0, yc), min(y1, yc + brick_l - 10.0)
            if yb_b > ya + 15.0:
                bricks.append(geo.make_hollow_brick(f"PBrick_{row_i}_{int(ya)}", pb_x0, pb_x1, ya, yb_b, zc, zc + bh, 2, 2, mats["brick"], col))
            if yb_b < y1 - 2.0:
                mortars.append(geo.make_box_mm(f"PMortV_{row_i}_{int(yb_b)}", pb_x0 + 2, pb_x1 - 2, yb_b, min(y1, yb_b + 10.0), zc, zc + bh, mats["mortar"], col, bevel_mm=0.2))
            yc += brick_l
        if zc + bh + 10.0 < peto_top:
            mortars.append(geo.make_box_mm(f"PMortH_{row_i}", pb_x0 + 2, pb_x1 - 2, y0, y1, zc + bh, zc + bh + 10.0, mats["mortar"], col, bevel_mm=0.2))
        zc += course_h
        row_i += 1
    model_objs.append(join_objects(bricks, "D4_Peto_Bricks", col))

    enf = [
        geo.make_box_mm("EnfInt", ei_x0, ei_x1, y0, y1, 0.0, peto_top, mats["render"], col),
        geo.make_box_mm("EnfExt", ee_x0, ee_x1, y0, y1, forj_bot, peto_top, mats["render"], col),
        geo.make_box_mm("JuntaEPS", j_x0, j_x1, y0, y1, 0.0, z_at_top(dx_end), mats["eps"], col),
    ] + mortars
    model_objs.append(join_objects(enf, "D4_Peto_Enfoscado", col))
    model_objs.append(geo.make_box_mm("D4_Barrera", ei_x0, ee_x1, y0, y1, peto_top - 5.0, peto_top, mats["bitumen"], col))

    ov = p["albardilla_overhang"]
    alb_top = peto_top + p["albardilla_h"]
    alb_pts = [
        (ei_x0 - ov, peto_top - 8), (ei_x0 - ov + 8, peto_top - 8), (ei_x0 - ov + 8, peto_top),
        (ee_x1 + ov - 8, peto_top), (ee_x1 + ov - 8, peto_top - 8), (ee_x1 + ov, peto_top - 8),
        (ee_x1 + ov, alb_top - 6), (0.5 * (ei_x0 + ee_x1), alb_top), (ei_x0 - ov, alb_top - 6)
    ]
    model_objs.append(geo.make_prism_xz("D4_Albardilla", alb_pts, y0, y1, mats["stone"], col, tile_size_m=0.35, bevel_mm=1.2))

    # Stepped cutaway along X (90, 200, 300, 390, 490)
    x_fp, x_i, x_cs, x_at, x_pf = 90.0, 200.0, 300.0, 390.0, 490.0
    model_objs.append(geo.make_prism_xz("D4_FP_Core", [(x_fp, 0), (dx_end, 0), (dx_end, z_fp_core(dx_end)), (x_fp, z_fp_core(x_fp))],
                                        y0, y1, mats["light_conc"], col, tile_size_m=0.38))
    model_objs.append(geo.make_prism_xz("D4_FP_Reg", [(x_fp, z_fp_core(x_fp)), (dx_end, z_fp_core(dx_end)), (dx_end, z_fp_top(dx_end)), (x_fp, z_fp_top(x_fp))],
                                        y0, y1, mats["mortar"], col, tile_size_m=0.35))

    z_turn = z_fp_top(dx_end) + p["i_turnup_h"]
    i_poly = [(x_i, z_fp_top(x_i)), (dx_end, z_fp_top(dx_end)), (ei_x0, z_fp_top(dx_end)), (ei_x0, z_turn),
              (ei_x0 - p["i_h"], z_turn), (ei_x0 - p["i_h"], z_i_top(dx_end)), (x_i, z_i_top(x_i))]
    mem_parts = [
        geo.make_prism_xz("MemMain", i_poly, y0, y1, mats["bitumen"], col, bevel_mm=0.3),
        geo.make_prism_xz("MemPerfil", [(ei_x0 - 10, z_turn + 6), (ei_x0, z_turn + 6), (ei_x0, z_turn - 16), (ei_x0 - 6, z_turn - 16), (ei_x0 - 10, z_turn)],
                          y0, y1, mats["zinc"], col, bevel_mm=0.3),
    ]
    model_objs.append(join_objects(mem_parts, "D4_I_Membrane", col))

    model_objs.append(geo.make_prism_xz("D4_CS_Geotextile", [(x_cs, z_i_top(x_cs)), (j_x0, z_i_top(j_x0)), (j_x0, z_cs_top(j_x0)), (x_cs, z_cs_top(x_cs))],
                                        y0, y1, mats["geotextile"], col, bevel_mm=0.2))
    model_objs.append(geo.make_prism_xz("D4_AT_XPS", [(x_at, z_cs_top(x_at)), (j_x0, z_cs_top(j_x0)), (j_x0, z_at_top(j_x0)), (x_at, z_at_top(x_at))],
                                        y0, y1, mats["xps"], col, tile_size_m=0.40, bevel_mm=0.8))

    # Plots regulables (grid supporting 400x400 pavers) + Losas Armadas horizontales
    plots = []
    losas = []
    px_coords = [580.0, 960.0]
    py_coords = [-360.0, 40.0, 420.0]
    for px in px_coords:
        zb = z_at_top(px)
        for py in py_coords:
            plots.append(geo.make_adjustable_plot(f"Plot_{int(px)}_{int(py)}", px, py, zb, z_losa_bot, mats["pp_plot"], col))
    model_objs.append(join_objects(plots, "D4_Plots", col))

    # Paving slab grid (floating horizontally with 4 mm open drainage joints)
    x_spans = [(x_pf, 578.0), (582.0, 958.0), (962.0, j_x0 - 4.0)]
    y_spans = [(-440.0, -362.0), (-358.0, 38.0), (42.0, 418.0), (422.0, 440.0)]
    for ix, (xa, xb) in enumerate(x_spans):
        for iy, (ya, yb) in enumerate(y_spans):
            if xb > xa + 20 and yb > ya + 15:
                losas.append(geo.make_box_mm(f"Losa_{ix}_{iy}", xa, xb, ya, yb, z_losa_bot, z_losa_top, mats["paver"], col, tile_size_m=0.45, bevel_mm=1.2))
    model_objs.append(join_objects(losas, "D4_Losas", col))

    scene = bpy.context.scene
    geo.setup_studio_environment(scene, floor_z_mm=forj_bot, center_xy_mm=(600.0, 0.0), scale_diag_m=2.0)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle4_invertida_plots.blend", r"d:\C2\models\detalle4_invertida_plots.glb")

    geo.render_camera_shot(scene, "D4_Hero", (-1180.0, -1820.0, 1260.0), (580.0, 20.0, 240.0),
                           r"d:\C2\renders\detalle4_hero.png", lens_mm=60.0, res_x=2040, res_y=1360)
    geo.render_camera_shot(scene, "D4_Closeup", (320.0, -760.0, 520.0), (740.0, -20.0, 210.0),
                           r"d:\C2\renders\detalle4_closeup.png", lens_mm=72.0, res_x=1920, res_y=1280)
    geo.render_camera_shot(scene, "D4_Section", (590.0, -2600.0, 305.0), (590.0, 0.0, 305.0),
                           r"d:\C2\renders\detalle4_section.png", ortho_scale_m=1.78)
    print("Built & rendered DET-04 (Invertida PLOTS).")


# ==============================================================================
# DET-05: Tejado de Teja Curva sobre Tabiquillos Palomeros + Canalon Visto
# ==============================================================================
def build_detalle5_alero_teja():
    reset_scene()
    mats = geo.get_material_palette()
    p = DETAILS["detalle5_alero_teja"]["params"]
    col = geo.ensure_collection("Detalle5_AleroTeja")

    slope = p["slope"]
    ang = math.atan(slope)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 150..290
    cx1, ix1 = p["cham_x1"], p["int_x1"]    # 340, 400
    x_end = 1220.0
    corn_x0 = wx0 - p["cornice_overhang"]   # 60
    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]
    y0, y1 = -500.0, 500.0

    def z_tab_bot(x): return p["tablero_z_eaves"] + slope * (x - wx0)
    def z_tab_top(x): return z_tab_bot(x) + p["tablero_h"]
    def z_reg_top(x): return z_tab_top(x) + p["reg_h"]

    model_objs = []

    # 1. Fachada exterior bajo forjado (Z:-340..-260) + sardinel volado bajo cornisa (-148..-50) -> cero solape con zuncho!
    fach = []
    z_fbot = -380.0
    zc, row = z_fbot, 0
    while zc + 50.0 < forj_bot:
        bh = min(62.0, forj_bot - 6.0 - zc)
        yo = 0.0 if row % 2 == 0 else -145.0
        yc = y0 + yo
        while yc < y1 - 2.0:
            ya, yb_b = max(y0, yc), min(y1, yc + 280.0)
            if yb_b > ya + 15.0:
                fach.append(geo.make_hollow_brick(f"FacBr_{row}_{int(ya)}", wx0, wx1, ya, yb_b, zc, zc + bh, 2, 2, mats["brick"], col))
            yc += 290.0
        zc += 72.0
        row += 1
    fach.append(geo.make_box_mm("FacEnf", wx0 - 12, wx0, y0, y1, z_fbot, forj_bot, mats["render"], col))
    fach.append(geo.make_hollow_brick("FacSard", corn_x0 + 25, wx0, y0, y1, -148.0, -52.0, 1, 2, mats["brick"], col))
    fach.append(geo.make_box_mm("FacAisl", wx1, cx1, y0, y1, z_fbot, forj_bot, mats["fiberglass"], col))
    fach.append(geo.make_hollow_brick("FacInt", cx1, ix1, y0, y1, z_fbot, forj_bot, 1, 3, mats["brick"], col))
    fach.append(geo.make_box_mm("FacEnl", ix1, ix1 + 14, y0, y1, z_fbot, forj_bot, mats["revest"], col))
    model_objs.append(join_objects(fach, "D5_Fachada", col))

    # 2. Forjado unidireccional + zuncho (X:150..440, debajo de compresion) + cornisa volada (-88..0) + senos + bovedillas
    forj = [
        geo.make_box_mm("ForjComp", corn_x0, x_end, y0, y1, comp_bot, 0.0, mats["concrete"], col, tile_size_m=0.45),
        geo.make_prism_xz("ForjZun", [(corn_x0, -88), (150, -88), (150, forj_bot), (440, forj_bot), (440, comp_bot), (corn_x0, comp_bot)],
                          y0, y1, mats["concrete"], col),
        geo.make_prism_xz("ForjVig", [(780, forj_bot), (900, forj_bot), (900, forj_bot + 40),
                                      (874, forj_bot + 43), (868, forj_bot + 50), (866, comp_bot),
                                      (814, comp_bot), (812, forj_bot + 50), (806, forj_bot + 43), (780, forj_bot + 40)],
                          y0, y1, mats["concrete"], col, bevel_mm=0.4),
    ]

    bovs = []
    added_senos = False
    for yb in range(-500, 500, 200):
        yb1 = min(yb + 197.0, 500.0)
        bov_l, _, s_lr = geo.make_bovedilla_ceramica(f"D5_BovL_{yb}", 300.0, 840.0, yb, yb1, forj_bot, comp_bot, mats["brick"], col, clip_x0=440.0)
        bov_r, s_rl, _ = geo.make_bovedilla_ceramica(f"D5_BovR_{yb}", 840.0, 1420.0, yb, yb1, forj_bot, comp_bot, mats["brick"], col, clip_x1=x_end)
        bovs.extend([bov_l, bov_r])
        if not added_senos:
            if s_lr:
                forj.append(geo.make_prism_xz("D5_SenoL", s_lr, y0, y1, mats["concrete"], col, bevel_mm=0.0))
            if s_rl:
                forj.append(geo.make_prism_xz("D5_SenoR", s_rl, y0, y1, mats["concrete"], col, bevel_mm=0.0))
            added_senos = True
    model_objs.append(join_objects(forj, "D5_Forjado", col))
    model_objs.append(join_objects(bovs, "D5_Bovedillas", col))

    # 3. Lana mineral sobre forjado (stepped Y reveal: -500..+480)
    ais = []
    for ax0, ax1 in ((wx1 + 65, 468.0), (542.0, 958.0), (1032.0, x_end)):
        ais.append(geo.make_box_mm(f"D5_Lana_{int(ax0)}", ax0, ax1, -480.0, 480.0, 0.0, p["at_h"], mats["fiberglass"], col, tile_size_m=0.35, bevel_mm=0.8))
    model_objs.append(join_objects(ais, "D5_Aislamiento", col))

    # 4. Tabiquillos palomeros calados + murete arranque alero
    pal = []
    # Murete apoyo cornice (corriendo a lo largo de Y en bordes/continuo en respaldo cornisa)
    pal.append(geo.make_prism_xz("PalCorn", [(corn_x0, 0), (wx0 + 60, 0), (wx0 + 60, z_tab_bot(wx0 + 60)), (corn_x0, z_tab_bot(corn_x0))],
                                 -440.0, 480.0, mats["brick"], col))
    for tx0, tx1 in ((470.0, 540.0), (960.0, 1030.0)):
        ztop_l = z_tab_bot(tx0) - 18.0
        ztop_r = z_tab_bot(tx1) - 18.0
        zt, row = 0.0, 0
        while zt + 55.0 < ztop_l:
            # Alternar ladrillos espaciados a lo largo de Y (calado 25% ventilacion cruzada!)
            y_cur = -480.0 + (0.0 if row % 2 == 0 else 160.0)
            while y_cur < 480.0:
                ya, yb = max(-480.0, y_cur), min(480.0, y_cur + 240.0)
                if yb > ya + 30.0:
                    pal.append(geo.make_hollow_brick(f"Pal_{int(tx0)}_{row}_{int(ya)}", tx0, tx1, ya, yb, zt, min(zt + 58.0, ztop_l),
                                                     1, 2, mats["brick_alt"], col))
                y_cur += 320.0  # deja huecos libres de 80 mm cada ladrillo!!
            zt += 66.0
            row += 1
        pal.append(geo.make_prism_xz(f"Maestra_{int(tx0)}", [(tx0, ztop_l), (tx1, ztop_r), (tx1, z_tab_bot(tx1)), (tx0, z_tab_bot(tx0))],
                                     -480.0, 480.0, mats["mortar"], col))
    model_objs.append(join_objects(pal, "D5_Tabiquillos", col))

    # 5. Tablero ceramico machihembrado (-380..+480) + regularizacion M-5 (-310..+480)
    xb0 = corn_x0 - 15.0  # 45
    bards = []
    # Piezas bardo a lo largo de la pendiente
    step_b = 380.0
    x_cur = xb0
    idx_b = 0
    while x_cur < x_end - 20.0:
        xn = min(x_cur + step_b - 4.0, x_end)
        # Seccion con 4 huecos longitudinales extruida en Y (-380..+480)
        bards.append(geo.make_oriented_box_mm(f"Bardo_{idx_b}", (x_cur, z_tab_bot(x_cur)), ang,
                                              (xn - x_cur) / cos_a, p["tablero_h"], -380.0, 480.0, mats["brick"], col, bevel_mm=0.6))
        x_cur += step_b
        idx_b += 1
    model_objs.append(join_objects(bards, "D5_Tablero", col))

    model_objs.append(geo.make_prism_xz("D5_Regularizacion", [(xb0, z_tab_top(xb0)), (x_end, z_tab_top(x_end)),
                                                              (x_end, z_reg_top(x_end)), (xb0, z_reg_top(xb0))],
                                        -310.0, 480.0, mats["mortar"], col, tile_size_m=0.38))

    # 6. Canalon visto Zinc + Ganchos metalicos (abrazadera exterior sin penetrar seno del canalon)
    gcx, gcz, gr = p["gutter_cx"], p["gutter_cz"], p["gutter_r"]
    model_objs.append(geo.make_semicircular_gutter("D5_Canalon", gcx, gcz, gr, 4.0, y0, y1, mats["zinc"], col))
    hooks = []
    for yh in (-360.0, -80.0, 200.0, 440.0):
        pts_h = []
        # Outer semicircular arc cradling underside of gutter (r = gr + 1 to gr + 7)
        for k in range(13):
            a = math.radians(180.0 + k * 180.0 / 12.0)
            pts_h.append((gcx + (gr + 1.0) * math.cos(a), gcz + (gr + 1.0) * math.sin(a)))
        pts_h.append((xb0 + 40.0, gcz + 2.0))
        pts_h.append((xb0 + 40.0, gcz - 6.0))
        for k in range(12, -1, -1):
            a = math.radians(180.0 + k * 180.0 / 12.0)
            pts_h.append((gcx + (gr + 7.5) * math.cos(a), gcz + (gr + 7.5) * math.sin(a)))
        hooks.append(geo.make_prism_xz(f"Gancho_{int(yh)}", pts_h, yh - 10.0, yh + 10.0, mats["stainless"], col, bevel_mm=0.3))
    model_objs.append(join_objects(hooks, "D5_Ganchos", col))

    # 7. Mortero de agarre M-2.5 (recalce en 1a hilada + cordones discontinuos)
    yc_cols = [-240.0, 0.0, 240.0]
    morts = []
    morts.append(geo.make_prism_xz("Mortero_Alero_Recalce",
                                   [(xb0 + 2, z_reg_top(xb0 + 2)), (xb0 + 360, z_reg_top(xb0 + 360)),
                                    (xb0 + 360, z_reg_top(xb0 + 360) + 22), (xb0 + 2, z_reg_top(xb0 + 2) + 38)],
                                   -220.0, 480.0, mats["mortar_dark"], col, bevel_mm=0.8))
    for cy in yc_cols:
        morts.append(geo.make_prism_xz(f"Mortero_Cordon_{int(cy)}",
                                       [(xb0 + 340, z_reg_top(xb0 + 340)), (x_end, z_reg_top(x_end)),
                                        (x_end, z_reg_top(x_end) + 22), (xb0 + 340, z_reg_top(xb0 + 340) + 22)],
                                       max(-310.0, cy - 38.0), cy + 38.0, mats["mortar_dark"], col, bevel_mm=0.8))
    model_objs.append(join_objects(morts, "D5_Mortero_Agarre", col))

    # 8. TRUE 3D Tapered Teja Curva (Canales en -240, 0, +240, +480? -> Canales en -240, 0, 240; Cobijas cabalgando entre ellos en -120, +120!)
    eave_tip_x = xb0 - p["vuelo_alero"]
    step = p["tile_len"] - p["tile_solape"]
    u_vec = (cos_a, 0.0, sin_a)
    n_vec = (-sin_a, 0.0, cos_a)
    canals, cobijas = [], []
    t_vars = mats["teja_vars"]

    for col_i, cy in enumerate(yc_cols):
        for r_i in range(4):
            s_d = r_i * step
            x_s = eave_tip_x + s_d * cos_a
            if x_s > x_end - 80.0:
                continue
            L_tile = min(p["tile_len"], (x_end - x_s) / cos_a)
            base_z = z_reg_top(xb0) + (x_s - xb0) * slope + 22.0 + p["tile_r_narrow"] * 0.78 + r_i * 7.5
            mat_t = t_vars[(col_i * 3 + r_i) % len(t_vars)]
            canals.append(geo.make_teja_curva(
                f"Canal_r{r_i}_c{col_i}", (x_s, cy, base_z), u_vec, n_vec,
                L_tile, p["tile_r_wide"], p["tile_r_narrow"], p["tile_t"], is_cobija=False, mat=mat_t, col=col
            ))
    model_objs.append(join_objects(canals, "D5_Teja_Canal", col))

    # Cobijas perfectamente centradas cabalgando sobre DOS canales adyacentes (-120 entre -240 y 0; +120 entre 0 y +240)
    cob_ys = [-120.0, 120.0]
    for col_i, cy in enumerate(cob_ys):
        for r_i in range(4):
            s_d = r_i * step + (14.0 if r_i == 0 else 0.0)
            x_s = eave_tip_x + s_d * cos_a
            if x_s > x_end - 80.0:
                continue
            L_tile = min(p["tile_len"] - (14.0 if r_i == 0 else 0.0), (x_end - x_s) / cos_a)
            base_z = z_reg_top(xb0) + (x_s - xb0) * slope + 22.0 + 22.0 + r_i * 8.0
            mat_t = t_vars[(col_i * 2 + r_i + 1) % len(t_vars)]
            cobijas.append(geo.make_teja_curva(
                f"Cobija_r{r_i}_c{col_i}", (x_s, cy, base_z), u_vec, n_vec,
                L_tile, p["tile_r_wide"], p["tile_r_narrow"], p["tile_t"], is_cobija=True, mat=mat_t, col=col
            ))
    model_objs.append(join_objects(cobijas, "D5_Teja_Cobija", col))

    scene = bpy.context.scene
    geo.setup_studio_environment(scene, floor_z_mm=-380.0, center_xy_mm=(600.0, 0.0), scale_diag_m=2.3)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle5_alero_teja_curva.blend", r"d:\C2\models\detalle5_alero_teja_curva.glb")

    geo.render_camera_shot(scene, "D5_Hero", (-1450.0, -2150.0, 1080.0), (540.0, -10.0, 125.0),
                           r"d:\C2\renders\detalle5_hero.png", lens_mm=58.0, res_x=2040, res_y=1360)
    geo.render_camera_shot(scene, "D5_Closeup", (-480.0, -820.0, 420.0), (140.0, -20.0, 145.0),
                           r"d:\C2\renders\detalle5_closeup.png", lens_mm=70.0, res_x=1920, res_y=1280)
    geo.render_camera_shot(scene, "D5_Section", (560.0, -2700.0, 130.0), (560.0, 0.0, 130.0),
                           r"d:\C2\renders\detalle5_section.png", ortho_scale_m=1.65)
    print("Built & rendered DET-05 (Alero Teja Curva).")


# ==============================================================================
# DET-06: Cumbrera Ventilada en Seco de Teja Curva sobre Doble Rastrelado
# ==============================================================================
def build_detalle6_cumbrera_teja():
    reset_scene()
    mats = geo.get_material_palette()
    p = DETAILS["detalle6_cumbrera_teja"]["params"]
    col = geo.ensure_collection("Detalle6_CumbreraTeja")

    slope = p["slope"]
    hx = p["half_span_x"]       # 760
    ang = math.atan(slope)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    y0, y1 = -460.0, 460.0

    # Thickness perpendicular-to-slope cumulative offsets
    t_tab = p["tablero_h"]
    t_reg = p["reg_h"]
    t_at = p["at_h"]
    t_lam = p["lamina_h"]
    t_cr = p["contrarastrel_h"]
    t_ra = p["rastrel_h"]

    model_objs = []
    # Central structural beam + dual sloped ceramic deck + regularizacion
    model_objs.append(geo.make_box_mm("D6_Soporte", -70.0, 70.0, y0, y1, -280.0, 0.0, mats["concrete"], col, tile_size_m=0.40))

    tabs, at_parts, lam_parts, crs, ras, canals, cobijas = [], [], [], [], [], [], []
    t_vars = mats["teja_vars"]

    for sx in (-1.0, 1.0):
        # Vector pointing DOWNSLOPE for sx slab geometry, or origin at apex (0,0) going outward along slope -ang
        # Let's define unit vector u_down from apex outward: (sx*cos_a, 0, -sin_a) and normal_up: (sx*sin_a, 0, cos_a)
        u_out = Vector((sx * cos_a, 0.0, -sin_a))
        n_up = Vector((sx * sin_a, 0.0, cos_a))
        u_up = -u_out  # points UPSLOPE toward apex!
        L_slope = hx / cos_a

        # Build prism helper in this side frame: n in [n0..n1], d_out in [d0..d1]
        def side_poly(d0, d1, n0, n1):
            p0 = u_out * d0 + n_up * n0
            p1 = u_out * d1 + n_up * n0
            p2 = u_out * d1 + n_up * n1
            p3 = u_out * d0 + n_up * n1
            return [(v.x, v.z) for v in (p0, p1, p2, p3)]

        # Tablero ceramico + reg M-5 con inglete vertical limpio en X=0 (sin cruce!)
        t_v = t_tab / cos_a
        tabs.append(geo.make_prism_xz(f"Tab_{int(sx)}", [(0.0, -t_v), (sx * hx, -hx * slope - t_v), (sx * hx, -hx * slope), (0.0, 0.0)],
                                      y0, y1, mats["brick"], col))
        r_v = t_reg / cos_a
        tabs.append(geo.make_prism_xz(f"Reg_{int(sx)}", [(0.0, 0.0), (sx * hx, -hx * slope), (sx * hx, -hx * slope + r_v), (0.0, r_v)],
                                      y0 + 50.0, y1, mats["mortar"], col))

        # XPS continuo ingletado limpio en X=0 (-360..+460)
        n_at0 = t_reg
        n_at1 = n_at0 + t_at
        a0_v, a1_v = r_v, r_v + t_at / cos_a
        at_parts.append(geo.make_prism_xz(f"XPS_{int(sx)}", [(0.0, a0_v), (sx * hx, a0_v - hx * slope), (sx * hx, a1_v - hx * slope), (0.0, a1_v)],
                                          -360.0, y1, mats["xps"], col, bevel_mm=0.8))

        # Lamina impermeable transpirable (-290..+460)
        n_l1 = n_at1 + t_lam
        lam_parts.append(geo.make_prism_xz(f"Lam_{int(sx)}", side_poly(15.0, L_slope, n_at1, n_l1), -290.0, y1, mats["lamina_trans"], col, bevel_mm=0.2))

        # Contrarastrel running along slope (at Y = -180, +60, +300) starting at Y=-220
        n_cr1 = n_l1 + t_cr
        for yc in (-160.0, 80.0, 320.0):
            crs.append(geo.make_prism_xz(f"CR_{int(sx)}_{int(yc)}", side_poly(35.0, L_slope - 20, n_l1, n_cr1),
                                         max(-220.0, yc - 20.0), yc + 20.0, mats["wood"], col, bevel_mm=0.6))

        # Horizontal rastreles (along Y from -180..+460) at distances along slope
        n_ra1 = n_cr1 + t_ra
        for d_r in (85.0, 325.0, 565.0):
            ras.append(geo.make_prism_xz(f"Ra_{int(sx)}_{int(d_r)}", side_poly(d_r - 20.0, d_r + 20.0, n_cr1, n_ra1),
                                         -180.0, y1, mats["wood_dark"], col, bevel_mm=0.6))

        # Barrel tiles (Canales + Cobijas) on BOTH slopes leaving 56 mm gap at apex!
        step = p["tile_len"] - p["tile_solape"]  # 310
        for col_i, cy in enumerate((-40.0, 200.0)):
            for r_i in range(2):
                d_near_ridge = 30.0 + r_i * step
                d_far = d_near_ridge + p["tile_len"]
                if d_near_ridge > L_slope - 60:
                    continue
                L_t = min(p["tile_len"], L_slope - d_near_ridge)
                # Start coordinates at lower tail of tile, vector u_up pointing toward ridge!
                p_low = (u_out * (d_near_ridge + L_t) + n_up * (n_ra1 + p["tile_r_narrow"] * 0.65 + r_i * 6.0))
                mat_t = t_vars[(col_i * 2 + r_i + (1 if sx > 0 else 0)) % len(t_vars)]
                canals.append(geo.make_teja_curva(
                    f"D6Can_{int(sx)}_{col_i}_{r_i}", (p_low.x, cy, p_low.z),
                    tuple(u_up), tuple(n_up), L_t, p["tile_r_wide"], p["tile_r_narrow"],
                    p["tile_t"], is_cobija=False, mat=mat_t, col=col
                ))

        for col_i, cy in enumerate((-160.0, 80.0, 320.0)):
            for r_i in range(2):
                d_near_ridge = 28.0 + r_i * step
                L_t = min(p["tile_len"], L_slope - d_near_ridge)
                p_low = (u_out * (d_near_ridge + L_t) + n_up * (n_ra1 + 22.0 + r_i * 7.0))
                mat_t = t_vars[(col_i * 3 + r_i) % len(t_vars)]
                cobijas.append(geo.make_teja_curva(
                    f"D6Cob_{int(sx)}_{col_i}_{r_i}", (p_low.x, cy, p_low.z),
                    tuple(u_up), tuple(n_up), L_t, p["tile_r_wide"], p["tile_r_narrow"],
                    p["tile_t"], is_cobija=True, mat=mat_t, col=col
                ))

    model_objs.append(join_objects(tabs, "D6_Tablero", col))
    model_objs.append(join_objects(at_parts, "D6_AT_XPS", col))
    model_objs.append(join_objects(lam_parts, "D6_Lamina_Transpirable", col))
    model_objs.append(join_objects(crs, "D6_Contrarastreles", col))
    model_objs.append(join_objects(ras, "D6_Rastreles", col))
    model_objs.append(join_objects(canals, "D6_Teja_Canal", col))
    model_objs.append(join_objects(cobijas, "D6_Teja_Cobija", col))

    # Ridge hardware: Soporte metalico estribado bajo rastrel cumbrera + Rastrel + Remate ventilado + Caballetes con clip superior
    z_apex = (t_reg + t_at) / cos_a + 18.0
    sups = []
    for ys in (-120.0, 140.0, 380.0):
        sups.append(geo.make_prism_xz(f"SupCab_{int(ys)}", [(-28, a1_v), (28, a1_v), (28, z_apex + 16), (-28, z_apex + 16)],
                                      ys - 18.0, ys + 18.0, mats["stainless"], col, bevel_mm=0.4))
    model_objs.append(join_objects(sups, "D6_Soporte_Caballete", col))
    model_objs.append(geo.make_box_mm("D6_Rastrel_Cumbrera", -22.5, 22.5, -160.0, y1, z_apex, z_apex + 50.0, mats["wood"], col))

    # Remate ventilado plisado envolviendo limpiamente rastrel cumbrera y tejas
    rem_poly = [(-170, z_apex - 14), (-38, z_apex + 51), (38, z_apex + 51), (170, z_apex - 14),
                (170, z_apex - 8), (40, z_apex + 58), (-40, z_apex + 58), (-170, z_apex - 8)]
    model_objs.append(geo.make_prism_xz("D6_Remate_Ventilado", rem_poly, -140.0, y1, mats["butyl"], col, bevel_mm=0.3))

    # Caballetes (tejas de cumbrera con clip inox en tornillo cenital)
    cabs, clips = [], []
    y_cab = -100.0
    i_c = 0
    while y_cab < 410.0:
        L_c = min(440.0, y1 - y_cab)
        cabs.append(geo.make_teja_curva(
            f"Cab_{i_c}", (0.0, y_cab, z_apex + 48.0 + i_c * 7.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            L_c, 108.0, 86.0, 14.0, is_cobija=True, mat=t_vars[i_c % 2], col=col, arc_deg=148.0
        ))
        # Arandela + cabeza tornillo estanca sobre solape + grapa de servicio inferior
        clips.append(geo.make_box_mm(f"ClipTorn_{i_c}", -9.0, 9.0, y_cab + 22.0, y_cab + 40.0, z_apex + 138.0 + i_c * 7.0, z_apex + 148.0 + i_c * 7.0, mats["stainless"], col))
        clips.append(geo.make_box_mm(f"ClipGrapa_{i_c}", -6.0, 6.0, y_cab - 4.0, y_cab + 18.0, z_apex + 58.0, z_apex + 82.0, mats["stainless"], col))
        y_cab += 360.0
        i_c += 1
    model_objs.append(join_objects(cabs, "D6_Caballetes", col))
    model_objs.append(join_objects(clips, "D6_Clips", col))

    scene = bpy.context.scene
    geo.setup_studio_environment(scene, floor_z_mm=-285.0, center_xy_mm=(0.0, 0.0), scale_diag_m=2.2)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle6_cumbrera_teja_ventilada.blend", r"d:\C2\models\detalle6_cumbrera_teja_ventilada.glb")

    geo.render_camera_shot(scene, "D6_Hero", (-1520.0, -1880.0, 1060.0), (0.0, 0.0, 75.0),
                           r"d:\C2\renders\detalle6_hero.png", lens_mm=58.0, res_x=2040, res_y=1360)
    geo.render_camera_shot(scene, "D6_Closeup", (-620.0, -780.0, 520.0), (20.0, 20.0, 180.0),
                           r"d:\C2\renders\detalle6_closeup.png", lens_mm=72.0, res_x=1920, res_y=1280)
    geo.render_camera_shot(scene, "D6_Section", (0.0, -2700.0, 55.0), (0.0, 0.0, 55.0),
                           r"d:\C2\renders\detalle6_section.png", ortho_scale_m=1.72)
    print("Built & rendered DET-06 (Cumbrera Ventilada Teja).")


# ==============================================================================
# DET-07: Faldon de Teja Mixta sobre Doble Rastrel + Encuentro con Paramento
# ==============================================================================
def build_detalle7_teja_mixta():
    reset_scene()
    mats = geo.get_material_palette()
    p = DETAILS["detalle7_teja_mixta"]["params"]
    col = geo.ensure_collection("Detalle7_TejaMixta")

    slope = p["slope"]
    ang = math.atan(slope)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    deck_end = p["deck_end_x"]  # 1000
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 1000..1160
    y0, y1 = -480.0, 480.0

    def zb(x): return slope * x
    t_f = p["forjado_h"]
    t_reg = p["reg_h"]
    t_at = p["at_h"]
    t_lam = p["lamina_h"]
    t_cr = p["contrarastrel_h"]
    t_ra = p["rastrel_h"]

    model_objs = []
    # 1. Forjado + Regularizacion
    model_objs.append(geo.make_oriented_box_mm("D7_Forjado", (0, 0), ang, deck_end / cos_a, -t_f, y0, y1, mats["concrete"], col, bevel_mm=0.6))
    model_objs.append(geo.make_oriented_box_mm("D7_Regularizacion", (0, 0), ang, deck_end / cos_a, t_reg, y0, y1, mats["mortar"], col, n0=0.0))

    # 2. Contrarastrel + XPS 70 + Lamina + Rastrel horizontal (+20 mm primer rastrel!) + Peine de alero
    L_sl = deck_end / cos_a
    n_at0 = t_reg / cos_a * cos_a  # in perpendicular normal coords: just exact thicknesses t_reg!
    # Wait: using oriented_box_mm, thicknesses n are perpendicular directly!
    n0 = t_reg
    model_objs.append(geo.make_oriented_box_mm("D7_AT_XPS", (0, 0), ang, L_sl - 20, t_at, -420.0, y1, mats["xps"], col, n0=n0, bevel_mm=0.8))

    n1 = n0 + t_at
    model_objs.append(geo.make_oriented_box_mm("D7_Lamina", (0, 0), ang, L_sl - 10, t_lam, -340.0, y1, mats["lamina_trans"], col, n0=n1))

    crs = []
    for yc in (-220.0, 40.0, 300.0):
        crs.append(geo.make_oriented_box_mm(f"D7CR_{int(yc)}", (0, 0), ang, L_sl - 20, t_cr, max(-280.0, yc - 20), yc + 20, mats["wood"], col, n0=n1 + t_lam))
    model_objs.append(join_objects(crs, "D7_Contrarastreles", col))

    n2 = n1 + t_lam + t_cr
    ras = []
    for k, d_a in enumerate((130.0, 485.0, 840.0)):
        rh = 52.0 if k == 0 else t_ra
        ras.append(geo.make_oriented_box_mm(f"D7Ra_{k}", (0, 0), ang, 40.0, rh, -200.0, y1, mats["wood_dark"], col, u0=d_a - 20, n0=n2))
    model_objs.append(join_objects(ras, "D7_Rastreles", col))
    model_objs.append(geo.make_oriented_box_mm("D7_Peine_Alero", (0, 0), ang, 22.0, 32.0, -160.0, y1, mats["butyl"], col, u0=35.0, n0=n2))

    # 3. Teja Mixta sculpted tiles (3 rows x 3 cols: Y = -140..+480)
    mixtas = []
    m_vars = mats["mixta_vars"]
    for col_i, yt in enumerate((-120.0, 125.0, 370.0)):
        for row_i in range(3):
            u_s = 15.0 + row_i * 335.0
            if u_s > L_sl - 80.0:
                continue
            L_tm = min(p["tile_l"], L_sl - u_s - 6.0)
            xs = u_s * cos_a - (n2 + 38.0 + row_i * 4.0) * sin_a
            zs = u_s * sin_a + (n2 + 38.0 + row_i * 4.0) * cos_a
            mixtas.append(geo.make_teja_mixta(f"TejaMix_{row_i}_{col_i}", (xs, yt, zs), ang,
                                              L_tm, p["tile_w"], p["wave_h"], p["tile_h"], m_vars[(col_i + row_i) % len(m_vars)], col))
    model_objs.append(join_objects(mixtas, "D7_Teja_Mixta", col))

    # 4. Paramento vertical (LHD 140 + Enfoscado 20 + Roza + Albardilla)
    z_mbot = zb(deck_end) - t_f / cos_a
    z_mtop = p["wall_top_z"]
    bricks = []
    zc, row_i = z_mbot, 0
    while zc + 50.0 < z_mtop:
        bh = min(62.0, z_mtop - zc - 8.0)
        yo = 0.0 if row_i % 2 == 0 else -145.0
        yc = y0 + yo
        while yc < y1 - 2.0:
            ya, yb_b = max(y0, yc), min(y1, yc + 280.0)
            if yb_b > ya + 15.0:
                bricks.append(geo.make_hollow_brick(f"MBr_{row_i}_{int(ya)}", wx0 + 20, wx1, ya, yb_b, zc, zc + bh, 2, 2, mats["brick"], col))
            yc += 290.0
        zc += 72.0
        row_i += 1
    model_objs.append(join_objects(bricks, "D7_Muro_Bricks", col))

    enf = [
        geo.make_box_mm("MuroEnf", wx0, wx0 + 20, y0, y1, z_mbot, z_mtop, mats["render"], col),
        geo.make_box_mm("MuroAlb", wx0 - 12, wx1 + 14, y0, y1, z_mtop, z_mtop + 38, mats["stone"], col, bevel_mm=1.0),
    ]
    model_objs.append(join_objects(enf, "D7_Muro_Enfoscado", col))

    # 5. Banda impermeable autoadhesiva >= 100 mm + Babero Zinc >= 250 mm en roza
    z_tile_wall = zb(deck_end) + (n2 + 64.0) / cos_a
    z_bab_top = z_tile_wall + p["babero_up_h"]
    band_poly = [(deck_end - 135, z_tile_wall - 44), (wx0, z_tile_wall + 6), (wx0, z_tile_wall + 135),
                 (wx0 - 4, z_tile_wall + 135), (wx0 - 4, z_tile_wall + 10), (deck_end - 135, z_tile_wall - 38)]
    model_objs.append(geo.make_prism_xz("D7_Banda_Impermeable", band_poly, -210.0, y1, mats["butyl"], col, bevel_mm=0.3))

    bab_poly = [(deck_end - 155, z_tile_wall - 46), (wx0 - 10, z_tile_wall + 8), (wx0 - 10, z_bab_top),
                (wx0 + 24, z_bab_top + 12), (wx0 + 24, z_bab_top + 2), (wx0 - 2, z_bab_top - 6),
                (wx0 - 2, z_tile_wall + 4), (deck_end - 155, z_tile_wall - 52)]
    model_objs.append(geo.make_prism_xz("D7_Babero_Zinc", bab_poly, -160.0, y1, mats["zinc"], col, bevel_mm=0.3))

    scene = bpy.context.scene
    geo.setup_studio_environment(scene, floor_z_mm=-240.0, center_xy_mm=(580.0, 0.0), scale_diag_m=2.1)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle7_teja_mixta_paramento.blend", r"d:\C2\models\detalle7_teja_mixta_paramento.glb")

    geo.render_camera_shot(scene, "D7_Hero", (-1280.0, -1960.0, 1280.0), (580.0, 0.0, 275.0),
                           r"d:\C2\renders\detalle7_hero.png", lens_mm=58.0, res_x=2040, res_y=1360)
    geo.render_camera_shot(scene, "D7_Closeup", (320.0, -780.0, 680.0), (840.0, 40.0, 420.0),
                           r"d:\C2\renders\detalle7_closeup.png", lens_mm=72.0, res_x=1920, res_y=1280)
    geo.render_camera_shot(scene, "D7_Section", (560.0, -2700.0, 290.0), (560.0, 0.0, 290.0),
                           r"d:\C2\renders\detalle7_section.png", ortho_scale_m=1.68)
    print("Built & rendered DET-07 (Teja Mixta + Paramento).")


# ==============================================================================
# DET-08: Tejado de Pizarra Natural QTP-14 (Emboble, Ganchos Inox y Doble Rastrel)
# ==============================================================================
def build_detalle8_pizarra():
    reset_scene()
    mats = geo.get_material_palette()
    p = DETAILS["detalle8_pizarra"]["params"]
    col = geo.ensure_collection("Detalle8_Pizarra")

    slope = p["slope"]          # 0.56
    ang = math.atan(slope)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 110..290
    x_alero = wx0 - 60.0        # 50
    x_end = 980.0
    y0, y1 = -440.0, 440.0
    L_sl = (x_end - x_alero) / cos_a
    orig = (x_alero, 0.0)

    model_objs = []
    # 1. Muro apoyo + Forjado inclinado + regularizacion
    muro_p = [
        geo.make_hollow_brick("PizMuro", wx0 + 8, wx1 - 8, y0, y1, -260.0, -10.0, 2, 3, mats["brick"], col),
        geo.make_box_mm("PizEnf", wx0 - 8, wx0 + 8, y0, y1, -260.0, -12.0, mats["render"], col),
    ]
    model_objs.append(join_objects(muro_p, "D8_Muro", col))

    forj_p = [
        geo.make_oriented_box_mm("PizForj", orig, ang, L_sl, -p["forjado_h"], y0, y1, mats["concrete"], col),
        geo.make_oriented_box_mm("PizReg", orig, ang, L_sl, p["reg_h"], y0, y1, mats["mortar"], col, n0=0.0),
    ]
    model_objs.append(join_objects(forj_p, "D8_Forjado", col))

    # 2. Aislamiento 50 + Contrarastreles (rotura puente termico) + Rastreles horizontales paso 100 mm
    n0 = p["reg_h"]
    model_objs.append(geo.make_oriented_box_mm("D8_AT_XPS", orig, ang, L_sl - 30, p["at_h"], -400.0, y1, mats["xps"], col, u0=35.0, n0=n0, bevel_mm=0.8))

    crs = []
    for yc in (-220.0, 20.0, 260.0):
        crs.append(geo.make_oriented_box_mm(f"PizCR_{int(yc)}", orig, ang, L_sl, p["contrarastrel_h"] + p["camara_h"],
                                            max(-320.0, yc - 25.0), yc + 25.0, mats["wood"], col, u0=25.0, n0=n0, bevel_mm=0.6))
    model_objs.append(join_objects(crs, "D8_Contrarastreles", col))

    n_ra = n0 + p["contrarastrel_h"] + p["camara_h"]
    vista = p["slate_vista"]  # 100
    ras = []
    for k in range(10):
        u_r = 40.0 + k * vista
        if u_r > L_sl - 30.0:
            break
        ras.append(geo.make_oriented_box_mm(f"PizRa_{k}", orig, ang, p["rastrel_w"], p["rastrel_h"],
                                            -240.0, y1, mats["wood_dark"], col, u0=u_r - 20.0, n0=n_ra, bevel_mm=0.5))
    model_objs.append(join_objects(ras, "D8_Rastreles", col))

    # 3. Chapa goteron zinc en alero
    gz0 = -45.0
    got_poly = [(x_alero - 22, n_ra - 38), (x_alero + 10, n_ra + 2), (x_alero + 150, n_ra + 150 * slope + 2),
                (x_alero + 150, n_ra + 150 * slope - 2), (x_alero + 8, n_ra - 3), (x_alero - 18, n_ra - 38)]
    model_objs.append(geo.make_prism_xz("D8_Gotero_Zinc", got_poly, -280.0, y1, mats["zinc"], col, bevel_mm=0.3))

    # 4. Emboble doble en alero + Pizarra natural biselada + Ganchos vistos AISI 316!
    n_sl0 = n_ra + p["rastrel_h"]
    embobles, slates, hooks = [], [], []
    s_vars = mats["slate_vars"]
    d_tip0 = -p["vuelo_alero"]  # -50 vuelo alero QTP-14

    # Emboble starter course along Y: -160..+440 (200 mm long x 200 mm wide each, 4 mm lateral joint)
    yc = -160.0
    col_i = 0
    while yc < y1 - 20.0:
        yw = min(p["slate_w"] - 4.0, y1 - yc)
        embobles.append(geo.make_oriented_box_mm(f"Emb_{col_i}", orig, ang, 200.0, p["slate_t"], yc, yc + yw,
                                                 s_vars[col_i % len(s_vars)], col, u0=d_tip0, n0=n_sl0 + 2.0, bevel_mm=1.0))
        yc += p["slate_w"]
        col_i += 1
    model_objs.append(join_objects(embobles, "D8_Pizarra_Emboble", col))

    # Regular staggered slate courses (step vista = 100 mm, half-width offset every odd row!)
    for row_i in range(9):
        u_s = d_tip0 + row_i * vista
        if u_s > L_sl - 40.0:
            break
        L_p = min(p["slate_l"], L_sl - u_s)
        n_cur = n_sl0 + 10.0 + row_i * 3.8  # clean progressive non-intersecting shingle tilt!
        y_off = 0.0 if row_i % 2 == 0 else -100.0
        yc = -160.0 + y_off
        col_j = 0
        while yc < y1 - 20.0:
            ya, yb = max(-160.0, yc), min(y1, yc + p["slate_w"] - 4.0)
            if yb > ya + 30.0:
                slates.append(geo.make_oriented_box_mm(f"Piz_r{row_i}_c{col_j}", orig, ang, L_p, p["slate_t"], ya, yb,
                                                       s_vars[(row_i + col_j) % len(s_vars)], col, u0=u_s, n0=n_cur, bevel_mm=1.1))
                # Stainless steel gancho clipping bottom edge of slate centered at ya/yb seam? No, center of lower slate joint!
                hy = 0.5 * (ya + yb)
                if ya <= -140.0 or yb >= y1 - 10.0 or abs(yb - ya) > 150.0:
                    # Clip bottom tail edge (u_s) down under lower course!
                    hooks.append(geo.make_oriented_box_mm(f"Gan_r{row_i}_c{col_j}", orig, ang, 18.0, 2.8, hy - 2.0, hy + 2.0,
                                                         mats["stainless"], col, u0=u_s - 4.0, n0=n_cur + p["slate_t"], bevel_mm=0.3))
                    hooks.append(geo.make_oriented_box_mm(f"GanV_r{row_i}_c{col_j}", orig, ang, 3.0, p["slate_t"] + 6.0, hy - 2.0, hy + 2.0,
                                                         mats["stainless"], col, u0=u_s - 4.0, n0=n_cur - 3.0, bevel_mm=0.2))
            yc += p["slate_w"]
            col_j += 1
    model_objs.append(join_objects(slates, "D8_Pizarras", col))
    model_objs.append(join_objects(hooks, "D8_Ganchos", col))

    scene = bpy.context.scene
    geo.setup_studio_environment(scene, floor_z_mm=-260.0, center_xy_mm=(500.0, 0.0), scale_diag_m=2.0)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle8_pizarra_alero_qtp14.blend", r"d:\C2\models\detalle8_pizarra_alero_qtp14.glb")

    geo.render_camera_shot(scene, "D8_Hero", (-1280.0, -1920.0, 1120.0), (460.0, 10.0, 210.0),
                           r"d:\C2\renders\detalle8_hero.png", lens_mm=58.0, res_x=2040, res_y=1360)
    geo.render_camera_shot(scene, "D8_Closeup", (-360.0, -760.0, 560.0), (260.0, 20.0, 240.0),
                           r"d:\C2\renders\detalle8_closeup.png", lens_mm=72.0, res_x=1920, res_y=1280)
    geo.render_camera_shot(scene, "D8_Section", (490.0, -2700.0, 200.0), (490.0, 0.0, 200.0),
                           r"d:\C2\renders\detalle8_section.png", ortho_scale_m=1.55)
    print("Built & rendered DET-08 (Pizarra Natural QTP-14).")


# ==============================================================================
# DET-09: Cubierta Metalica Zinc Prepatinado en Junta Alzada + Patas Inox + Peto
# ==============================================================================
def build_detalle9_zinc():
    reset_scene()
    mats = geo.get_material_palette()
    p = DETAILS["detalle9_zinc"]["params"]
    col = geo.ensure_collection("Detalle9_ZincVMZ")

    slope = p["slope"]
    ang = math.atan(slope)
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    deck_end = p["deck_end_x"]  # 1000
    wx0, wx1 = p["wall_x0"], p["wall_x1"]   # 1000..1160
    y0, y1 = -620.0, 620.0
    L_sl = deck_end / cos_a

    model_objs = []
    # 1. Forjado + Peto
    model_objs.append(geo.make_oriented_box_mm("D9_Forjado", (0, 0), ang, L_sl, -p["forjado_h"], y0, y1, mats["concrete"], col, bevel_mm=0.6))

    z_mbot = -p["forjado_h"] / cos_a
    z_mtop = 690.0
    peto = []
    zc, row = z_mbot, 0
    while zc + 50.0 < z_mtop:
        bh = min(62.0, z_mtop - zc - 8.0)
        yo = 0.0 if row % 2 == 0 else -145.0
        yc = y0 + yo
        while yc < y1 - 2.0:
            ya, yb = max(y0, yc), min(y1, yc + 280.0)
            if yb > ya + 15.0:
                peto.append(geo.make_hollow_brick(f"D9Br_{row}_{int(ya)}", wx0 + 20, wx1, ya, yb, zc, zc + bh, 2, 2, mats["brick"], col))
            yc += 290.0
        zc += 72.0
        row += 1
    peto.append(geo.make_box_mm("D9Enf", wx0, wx0 + 20, y0, y1, z_mbot, z_mtop, mats["render"], col))
    model_objs.append(join_objects(peto, "D9_Peto", col))

    # 2. Barrera vapor (-620..+620) + XPS 80 (-540..+620)
    model_objs.append(geo.make_oriented_box_mm("D9_BV", (0, 0), ang, L_sl, p["bv_h"], y0, y1, mats["bitumen"], col, n0=0.0))
    n1 = p["bv_h"]
    model_objs.append(geo.make_oriented_box_mm("D9_AT", (0, 0), ang, L_sl - 15, p["at_h"], -520.0, y1, mats["xps"], col, n0=n1, bevel_mm=0.8))

    # 3. Camara ventilada (rastreles madera along slope) + Entarimado continuo de tablas de pino (con junta 8 mm!)
    n2 = n1 + p["at_h"]
    ras = []
    for yr in (-380.0, -80.0, 220.0, 520.0):
        ras.append(geo.make_oriented_box_mm(f"D9CR_{int(yr)}", (0, 0), ang, L_sl - 15, p["camara_h"],
                                            max(-440.0, yr - 22.0), yr + 22.0, mats["wood"], col, n0=n2, bevel_mm=0.6))
    model_objs.append(join_objects(ras, "D9_Rastreles_Camara", col))

    n3 = n2 + p["camara_h"]
    planks = []
    xc, idx_p = 0.0, 0
    while xc < L_sl - 25.0:
        xn = min(xc + 122.0, L_sl - 8.0)
        planks.append(geo.make_oriented_box_mm(f"Ent_{idx_p}", (0, 0), ang, xn - xc, p["entarimado_h"], -340.0, y1,
                                               mats["wood"] if idx_p % 2 == 0 else mats["wood_dark"], col, u0=xc, n0=n3, bevel_mm=0.6))
        xc += 130.0
        idx_p += 1
    model_objs.append(join_objects(planks, "D9_Entarimado", col))

    # 4. Esterilla drenante estructurada (-240..+620) + Patas fijas/correderas Inox!
    n4 = n3 + p["entarimado_h"]
    model_objs.append(geo.make_oriented_box_mm("D9_Esterilla_Drenante", (0, 0), ang, L_sl - 12, p["capa_dren_h"], -240.0, y1, mats["lamina_trans"], col, n0=n4))

    n5 = n4 + p["capa_dren_h"]
    patas = []
    # Visible stainless L-clips along Y = -290 (center seam!) and Y = +290 (upper seam!)
    for ys_c in (-200.0, 380.0):
        for xp in (180.0, 480.0, 780.0):
            patas.append(geo.make_oriented_box_mm(f"PataH_{int(ys_c)}_{int(xp)}", (0, 0), ang, 60.0, 2.5, ys_c - 32.0, ys_c + 2.0, mats["stainless"], col, u0=xp, n0=n5))
            patas.append(geo.make_oriented_box_mm(f"PataV_{int(ys_c)}_{int(xp)}", (0, 0), ang, 60.0, 26.0, ys_c - 2.0, ys_c + 2.0, mats["stainless"], col, u0=xp, n0=n5))
    model_objs.append(join_objects(patas, "D9_Patas_Inox", col))

    # 5. Bandejas VMZ Zinc Prepatinado 580 mm module (-180..+400 & +400..+620? Let's place 2 trays centered at Y=90 and Y=500 -> clean visibility at Y=-200..+620!)
    # Better: first tray Y: -180..+400 (580 mm wide!), second tray Y: +400..+620! Both with true 25 mm standing seams!
    z_tray0 = n5 / cos_a
    tray1 = geo.make_standing_seam_tray("Tray_Main", 0.0, deck_end - 6.0, ang, z_tray0, 90.0, 580.0, p["seam_h"], 3.0, mats["zinc_vmz"], col, turnup_x1_h=160.0)
    tray2 = geo.make_standing_seam_tray("Tray_Ext", 0.0, deck_end - 6.0, ang, z_tray0, 490.0, 220.0, p["seam_h"], 3.0, mats["zinc_vmz"], col, turnup_x1_h=160.0)
    model_objs.append(join_objects([tray1, tray2], "D9_Bandejas_Zinc", col))

    # Extruded folded seam caps highlighting the double-lock standing seam profile
    seam_caps = []
    for ys in (-200.0, 380.0):
        seam_caps.append(geo.make_oriented_box_mm(f"SeamCap_{int(ys)}", (0, 0), ang, L_sl - 10, 8.0, ys - 4.0, ys + 4.0, mats["zinc_vmz"], col, n0=n5 + p["seam_h"] - 4.0, bevel_mm=0.5))
    model_objs.append(join_objects(seam_caps, "D9_Juntas_Alzadas", col))

    # 6. Remate de peto: babero zinc engatillado + albardilla metalica doble goteron
    z_tw = deck_end * slope + z_tray0
    z_bab_top = z_tw + 225.0
    rem = [
        geo.make_prism_xz("BabZinc", [(deck_end - 14, z_tw + 65), (deck_end - 14, z_bab_top), (wx0 + 22, z_bab_top + 10),
                                      (wx0 + 22, z_bab_top), (wx0 - 6, z_bab_top - 8), (wx0 - 6, z_tw + 65)],
                          -180.0, y1, mats["zinc_vmz"], col, bevel_mm=0.3),
        geo.make_prism_xz("AlbZinc", [(wx0 - 24, z_mtop - 14), (wx0 - 20, z_mtop - 14), (wx0 - 20, z_mtop + 28),
                                      (wx1 + 20, z_mtop + 38), (wx1 + 20, z_mtop - 14), (wx1 + 24, z_mtop - 14),
                                      (wx1 + 24, z_mtop + 43), (wx0 - 24, z_mtop + 33)],
                          y0, y1, mats["zinc_vmz"], col, bevel_mm=0.4),
    ]
    model_objs.append(join_objects(rem, "D9_Remate_Peto", col))

    scene = bpy.context.scene
    geo.setup_studio_environment(scene, floor_z_mm=-230.0, center_xy_mm=(580.0, 0.0), scale_diag_m=2.2)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle9_zinc_junta_alzada.blend", r"d:\C2\models\detalle9_zinc_junta_alzada.glb")

    geo.render_camera_shot(scene, "D9_Hero", (-1320.0, -1980.0, 1180.0), (580.0, 0.0, 230.0),
                           r"d:\C2\renders\detalle9_hero.png", lens_mm=58.0, res_x=2040, res_y=1360)
    geo.render_camera_shot(scene, "D9_Closeup", (320.0, -820.0, 620.0), (740.0, 40.0, 280.0),
                           r"d:\C2\renders\detalle9_closeup.png", lens_mm=72.0, res_x=1920, res_y=1280)
    geo.render_camera_shot(scene, "D9_Section", (580.0, -2700.0, 240.0), (580.0, 0.0, 240.0),
                           r"d:\C2\renders\detalle9_section.png", ortho_scale_m=1.65)
    print("Built & rendered DET-09 (Cubierta Zinc Junta Alzada).")


def build_part2_3d():
    build_detalle4_plots()
    build_detalle5_alero_teja()
    build_detalle6_cumbrera_teja()
    build_detalle7_teja_mixta()
    build_detalle8_pizarra()
    build_detalle9_zinc()


if __name__ == "__main__":
    arg = sys.argv[-1] if "--" in sys.argv else "all"
    mapping = {
        "detalle4": build_detalle4_plots,
        "detalle5": build_detalle5_alero_teja,
        "detalle6": build_detalle6_cumbrera_teja,
        "detalle7": build_detalle7_teja_mixta,
        "detalle8": build_detalle8_pizarra,
        "detalle9": build_detalle9_zinc,
    }
    if arg in mapping:
        mapping[arg]()
    else:
        build_part2_3d()
