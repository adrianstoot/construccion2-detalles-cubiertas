r"""
Builds Exact Millimetric 3D Models (.blend + .glb) and Renders Photorealistic Cycles HIP Shots
for all 3 UPV Construccion II Technical Details from d:\C2\src\specs.py.

Run via Blender 5.2 CLI:
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python "d:\C2\src\build_blender_scenes.py" -- all
"""

import math
import os
import sys
import bmesh
import bpy

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

    # Export clean GLB containing ONLY model objects (excluding StudioRig lights/floor/cameras)
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
# DETALLE 1: Cartillas IVE — Azotea Transitable Convencional (Peto + 7 Capas)
# ==============================================================================
def build_detalle1():
    reset_scene()
    mats = geo.get_material_palette()
    meta = DETAILS["detalle1"]
    p = meta["params"]
    st = p["steps_x"]
    col = geo.ensure_collection("Detalle1_IVE")

    dx_end = p["deck_end_x"]          # 985
    j_x0, j_x1 = dx_end, dx_end + p["junta_eps_w"]        # 985..1000
    ei_x0, ei_x1 = j_x1, j_x1 + p["enfoscado_int_w"]      # 1000..1015
    pb_x0, pb_x1 = ei_x1, ei_x1 + p["peto_brick_w"]       # 1015..1155
    ee_x0, ee_x1 = pb_x1, pb_x1 + p["enfoscado_ext_w"]    # 1155..1175
    y_max = 960.0

    def z_fp_core(x): return p["fp_min_h"] + p["slope"] * x
    def z_fp_top(x): return z_fp_core(x) + p["fp_reg_h"]
    def z_bv_top(x): return z_fp_top(x) + p["bv_h"]
    def z_at_top(x): return z_bv_top(x) + p["at_h"]
    def z_i_top(x): return z_at_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_m_top(x): return z_cs_top(x) + p["mortero_agarre_h"]
    def z_p_top(x): return z_m_top(x) + p["tile_h"]

    model_objs = []

    # 1. SR: Soporte Resistente (Forjado Unidireccional con senos y bovedillas ceramicas reales)
    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]
    sr_slab_parts = [
        geo.make_box_mm("SR_Comp", 0, ee_x1, 0, y_max, comp_bot, 0.0, mats["concrete"], col, bevel_mm=0.8),
        geo.make_box_mm("SR_Zuncho", 840, ee_x1, 0, y_max, forj_bot, comp_bot, mats["concrete"], col, bevel_mm=0.8),
        geo.make_prism_xz(
            "SR_Macizado",
            [(786.0, comp_bot), (840.0, comp_bot), (840.0, forj_bot),
             (820.0, forj_bot), (820.0, forj_bot + 40.0), (794.0, forj_bot + 43.0), (788.0, forj_bot + 50.0)],
            0.0, y_max, mats["concrete"], col, bevel_mm=0.0
        ),
    ]

    # Viguetas pretensadas en X=180 y X=760 (corren a lo largo de Y)
    vig_parts = []
    for vx in (180.0, 760.0):
        vp = [
            (vx - 60, forj_bot), (vx + 60, forj_bot), (vx + 60, forj_bot + 40),
            (vx + 34, forj_bot + 43), (vx + 28, forj_bot + 50), (vx + 26, comp_bot),
            (vx - 26, comp_bot), (vx - 28, forj_bot + 50), (vx - 34, forj_bot + 43),
            (vx - 60, forj_bot + 40),
        ]
        vig_parts.append(geo.make_prism_xz(f"Vig_{int(vx)}", vp, 0, y_max, mats["concrete"], col, bevel_mm=0.4))
        for rx in (vx - 28, vx + 28):
            bar = geo.make_box_mm(f"Rebar_{int(vx)}_{int(rx)}", rx - 3.5, rx + 3.5, -8.0, y_max, forj_bot + 16.5, forj_bot + 23.5, mats["rebar"], col, bevel_mm=0.3)
            vig_parts.append(bar)
    model_objs.append(join_objects(vig_parts, "SR_Viguetas", col))

    # Bovedillas ceramicas reales con tacones y 10 celdas huecas + senos de hormigon HA-25
    bov_parts = []
    yb = 0.0
    added_senos = False
    while yb < y_max - 5.0:
        yb1 = min(yb + 197.0, y_max)
        bov_c, s_cl, s_cr = geo.make_bovedilla_ceramica(f"BovC_{int(yb)}", 180.0, 760.0, yb, yb1, forj_bot, comp_bot, mats["brick"], col)
        bov_l, _, s_lr = geo.make_bovedilla_ceramica(f"BovL_{int(yb)}", -400.0, 180.0, yb, yb1, forj_bot, comp_bot, mats["brick"], col, clip_x0=0.0)
        bov_parts.extend([bov_l, bov_c])
        if not added_senos:
            sr_slab_parts.append(geo.make_prism_xz("SR_SenoL", s_lr, 0.0, y_max, mats["concrete"], col, bevel_mm=0.0))
            sr_slab_parts.append(geo.make_prism_xz("SR_SenoCL", s_cl, 0.0, y_max, mats["concrete"], col, bevel_mm=0.0))
            sr_slab_parts.append(geo.make_prism_xz("SR_SenoCR", s_cr, 0.0, y_max, mats["concrete"], col, bevel_mm=0.0))
            added_senos = True
        yb += 200.0
    model_objs.append(join_objects(sr_slab_parts, "SR_Slab", col))
    model_objs.append(join_objects(bov_parts, "SR_Bovedillas", col))

    # 2. PETO DE FABRICA (Ladrillo hueco doble 140 mm con huecos en el corte Y=0 + enfoscados + junta EPS)
    peto_top = p["peto_top_z"]
    brick_parts = []
    z_cur = 0.0
    brick_h = 90.0
    mortar_h = 10.0
    row_i = 0
    while z_cur + brick_h <= peto_top:
        y_cur = 0.0
        # Alternar aparejo a soga en cada hilada
        if row_i % 2 == 1:
            brick_parts.append(geo.make_hollow_brick(f"PB_{row_i}_0", pb_x0, pb_x1, 0.0, 120.0, z_cur, z_cur + brick_h, 2, 3, mats["brick"], col))
            y_cur = 128.0
        while y_cur < y_max - 10.0:
            y_end = min(y_cur + 240.0, y_max)
            brick_parts.append(geo.make_hollow_brick(f"PB_{row_i}_{int(y_cur)}", pb_x0, pb_x1, y_cur, y_end, z_cur, z_cur + brick_h, 2, 3, mats["brick"], col))
            y_cur = y_end + 8.0
        if z_cur + brick_h + mortar_h <= peto_top:
            brick_parts.append(geo.make_box_mm(f"PM_{row_i}", pb_x0, pb_x1, 0, y_max, z_cur + brick_h, z_cur + brick_h + mortar_h, mats["mortar"], col, bevel_mm=0.2))
        z_cur += brick_h + mortar_h
        row_i += 1
    model_objs.append(join_objects(brick_parts, "Peto_Bricks", col))

    ren_parts = [
        geo.make_box_mm("Enf_Int", ei_x0, ei_x1, 0, y_max, 0.0, peto_top, mats["mortar"], col, bevel_mm=0.5),
        geo.make_box_mm("Enf_Ext", ee_x0, ee_x1, 0, y_max, 0.0, peto_top, mats["render"], col, bevel_mm=0.6),
        geo.make_prism_xz("Albardilla", [(ei_x0 - 8, peto_top), (ee_x1 + 8, peto_top), (ee_x1 + 8, peto_top + 38), (ei_x0 - 8, peto_top + 48)], 0, y_max, mats["render"], col, bevel_mm=1.0),
    ]
    model_objs.append(join_objects(ren_parts, "Peto_Render", col))

    z_eps_top = z_at_top(dx_end)
    model_objs.append(geo.make_box_mm("Peto_JuntaEPS", j_x0, j_x1, 0, y_max, 0.0, z_eps_top, mats["eps"], col, bevel_mm=0.3))

    # 3. Capas escalonadas (IVE axonometric cutaway exacto)
    x_fp = st["FP"]
    model_objs.append(geo.make_prism_xz("FP_Concrete", [(x_fp, 0), (dx_end, 0), (dx_end, z_fp_core(dx_end)), (x_fp, z_fp_core(x_fp))], 0, y_max, mats["light_conc"], col, bevel_mm=0.6))
    model_objs.append(geo.make_prism_xz("FP_Regularization", [(x_fp, z_fp_core(x_fp)), (dx_end, z_fp_core(dx_end)), (dx_end, z_fp_top(dx_end)), (x_fp, z_fp_top(x_fp))], 0, y_max, mats["mortar"], col, bevel_mm=0.4))

    x_bv = st["BV"]
    model_objs.append(geo.make_prism_xz("BV_VaporBarrier", [(x_bv, z_fp_top(x_bv)), (dx_end, z_fp_top(dx_end)), (dx_end, z_bv_top(dx_end)), (x_bv, z_bv_top(x_bv))], 0, y_max, mats["vapor"], col, bevel_mm=0.2))

    x_at = st["AT"]
    model_objs.append(geo.make_prism_xz("AT_XPS", [(x_at, z_bv_top(x_at)), (dx_end, z_bv_top(dx_end)), (dx_end, z_at_top(dx_end)), (x_at, z_at_top(x_at))], 0, y_max, mats["xps"], col, bevel_mm=0.8))

    x_i = st["I"]
    z_turn = z_p_top(dx_end) + p["i_turnup_h"]
    i_poly = [(x_i, z_at_top(x_i)), (dx_end, z_at_top(dx_end)), (ei_x0, z_at_top(dx_end)), (ei_x0, z_turn),
              (ei_x0 - p["i_h"], z_turn), (ei_x0 - p["i_h"], z_i_top(dx_end)), (x_i, z_i_top(x_i))]
    model_objs.append(geo.make_prism_xz("I_Membrane", i_poly, 0, y_max, mats["bitumen"], col, bevel_mm=0.2))

    x_cs = st["CS"]
    cs_end = ei_x0 - p["i_h"] - p["junta_perimetral"]
    model_objs.append(geo.make_prism_xz("CS_Geotextile", [(x_cs, z_i_top(x_cs)), (cs_end, z_i_top(cs_end)), (cs_end, z_cs_top(cs_end)), (x_cs, z_cs_top(x_cs))], 0, y_max, mats["geotextile"], col, bevel_mm=0.2))

    x_pm = st["P_MORTERO"]
    model_objs.append(geo.make_prism_xz("P_Mortar", [(x_pm, z_cs_top(x_pm)), (cs_end, z_cs_top(cs_end)), (cs_end, z_m_top(cs_end)), (x_pm, z_m_top(x_pm))], 0, y_max, mats["mortar_dark"], col, bevel_mm=0.5))

    # P_Tiles individuales (280x140x20 mm a matajunta)
    x_p = st["P"]
    tl, tw, tj = p["tile_l"], p["tile_w"], p["tile_joint"]
    tile_parts = []
    # Llenar en filas paralelas al peto (tiras en Y)
    row_x = x_p
    row_idx = 0
    while row_x < cs_end - 12.0:
        rx1 = min(row_x + tw, cs_end)
        cy = 0.0
        if row_idx % 2 == 1:
            cy_end = min(tl * 0.5, y_max)
            m = mats["rasilla"] if (row_idx % 3 != 0) else mats["rasilla_alt"]
            tile_parts.append(geo.make_prism_xz(f"PT_{row_idx}_0", [(row_x, z_m_top(row_x)), (rx1, z_m_top(rx1)), (rx1, z_p_top(rx1)), (row_x, z_p_top(row_x))], 0.0, cy_end, m, col, bevel_mm=1.2))
            cy = cy_end + tj
        while cy < y_max - 10.0:
            cy_end = min(cy + tl, y_max)
            m = mats["rasilla"] if ((row_idx + int(cy)) % 3 != 0) else mats["rasilla_alt"]
            tile_parts.append(geo.make_prism_xz(f"PT_{row_idx}_{int(cy)}", [(row_x, z_m_top(row_x)), (rx1, z_m_top(rx1)), (rx1, z_p_top(rx1)), (row_x, z_p_top(row_x))], cy, cy_end, m, col, bevel_mm=1.2))
            cy = cy_end + tj
        row_x = rx1 + tj
        row_idx += 1
    model_objs.append(join_objects(tile_parts, "P_Tiles", col))

    # Rodapie ceramico vertical + mortero + junta elastica
    rod_x1 = ei_x0 - p["i_h"] - 8.0
    rod_x0 = rod_x1 - p["rodapie_t"]
    rod_z0 = z_p_top(dx_end) + 4.0
    rod_z1 = rod_z0 + p["rodapie_h"]
    rod_parts = [geo.make_box_mm("Rod_Adh", rod_x1, ei_x0 - p["i_h"], 0, y_max, rod_z0, rod_z1, mats["mortar_dark"], col, bevel_mm=0.3)]
    cy = 0.0
    while cy < y_max - 10.0:
        cy_end = min(cy + 140.0, y_max)
        rod_parts.append(geo.make_box_mm(f"Rod_{int(cy)}", rod_x0, rod_x1, cy, cy_end, rod_z0, rod_z1, mats["rasilla"], col, bevel_mm=1.0))
        cy = cy_end + tj
    model_objs.append(join_objects(rod_parts, "P_Rodapie", col))
    model_objs.append(geo.make_box_mm("P_Joint", cs_end, ei_x0 - p["i_h"], 0, y_max, z_i_top(dx_end), z_p_top(dx_end), mats["elastomer"], col, bevel_mm=0.2))

    # Studio + Export + Cycles Renders
    geo.setup_studio_environment(bpy.context.scene, floor_z_mm=forj_bot, center_xy_mm=(580, 480), scale_diag_m=2.1)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle1_ive_peto.blend", r"d:\C2\models\detalle1_ive_peto.glb")

    geo.render_camera_shot(bpy.context.scene, "Cam_Hero", (-1380, -1420, 1150), (580, 460, 240),
                           r"d:\C2\renders\detalle1_hero.png", lens_mm=48.0)
    geo.render_camera_shot(bpy.context.scene, "Cam_Closeup", (320, -680, 440), (880, 260, 140),
                           r"d:\C2\renders\detalle1_closeup.png", lens_mm=70.0, dof_fstop=5.6)
    geo.render_camera_shot(bpy.context.scene, "Cam_Section", (588, -2600, 310), (588, 0, 310),
                           r"d:\C2\renders\detalle1_section.png", ortho_scale_m=2.05)


# ==============================================================================
# DETALLE 2A: NTE QAT-16 — Encuentro con Cazoleta
# ==============================================================================
def build_detalle2_qat16():
    reset_scene()
    mats = geo.get_material_palette()
    meta = DETAILS["detalle2_qat16"]
    p = meta["params"]
    col = geo.ensure_collection("Detalle2_QAT16")

    pit_in = p["pit_inner_half"]          # 110
    ptl_out = pit_in + p["ptl7_wall_t"]   # 160
    ptl_h = p["ptl7_h"]                   # 120
    slope = p["slope"]                    # 0.05
    x_min, x_max = -280.0, 840.0
    y_max = 360.0
    forj_bot = -p["forjado_h"]            # -250
    hole_r = 63.0
    br = p["bajante_od"] * 0.5            # 55
    bw = p["bajante_wall"]
    copa_r = br + 4.5
    caz_h = p["cazoleta_outer_half"]      # 102
    fl_w = p["cazoleta_flange_w"]         # 36

    def z_fal(x): return ptl_h + slope * max(0.0, x - ptl_out)
    def z_reg(x): return z_fal(x) + p["reg_mortar_h"]
    def z_mem(x): return z_reg(x) + p["mem_sup_h"]
    def z_ag(x): return z_mem(x) + p["agarre_h"]
    def z_ras(x): return z_ag(x) + p["rasilla_h"]

    model_objs = []

    # 1. Forjado estructural perforado en (0,0) (cutaway Y >= 0)
    # Use clean outer rectangle [-280..840] by building left (-280..280) annular + right extension (280..840)
    f_ann = geo.make_annular_box_cutaway("Forj_Ring", hole_r, 280.0, y_max, forj_bot, 0.0, mats["concrete"], col)
    f_ext = geo.make_box_mm("Forj_Ext", 280.0, x_max, 0.0, y_max, forj_bot, 0.0, mats["concrete"], col)
    model_objs.append(join_objects([f_ann, f_ext], "Q16_Forjado", col))

    # 2. Bajante PVC Ø110 con copa superior (revolucion theta 0..pi)
    baj_rz = [
        (br - bw, -270.0), (br, -270.0), (br, -55.0), (copa_r, -42.0), (copa_r, 0.0),
        (copa_r - bw, 0.0), (copa_r - bw, -42.0), (br - bw, -55.0)
    ]
    model_objs.append(geo.make_revolved_profile("Q16_Bajante", baj_rz, 0.0, math.pi, 36, mats["pvc"], col))

    # 3. Caja PTL-7 de ladrillo hueco sencillo (50 mm espesor, Z: 0..120, Y: 0..160 + pared trasera)
    model_objs.append(geo.make_square_hollow_curb_cutaway("Q16_PTL7_Bricks", pit_in, ptl_out, 0.0, ptl_out, 0.0, ptl_h, 1, 3, mats["brick"], col))

    # Mortero asiento fondo de caja PTL-7 (anillo alrededor de bajante Z: 0..24)
    m_pit = geo.make_annular_box_cutaway("Q16_PTL7_Mortar", br, pit_in, pit_in, 0.0, 24.0, mats["mortar"], col)
    model_objs.append(m_pit)

    # 4. Faldon de hormigon aligerado (X: 160..840 + faldones laterales atras Y: 160..360)
    fal_objs = [
        geo.make_prism_xz("Fal_R", [(ptl_out, 0), (x_max, 0), (x_max, z_fal(x_max)), (ptl_out, ptl_h)], 0.0, y_max, mats["light_conc"], col),
        geo.make_box_mm("Fal_Back", -ptl_out, ptl_out, ptl_out, y_max, 0.0, ptl_h, mats["light_conc"], col),
    ]
    model_objs.append(join_objects(fal_objs, "Q16_HormigonAlig", col))

    # 5. Mortero regularizacion 1:6
    reg_objs = [
        geo.make_prism_xz("Reg_R", [(pit_in + 12, ptl_h), (ptl_out, ptl_h), (x_max, z_fal(x_max)),
                                    (x_max, z_reg(x_max)), (ptl_out, z_reg(ptl_out)), (pit_in + 12, z_reg(ptl_out))],
                          0.0, y_max, mats["mortar"], col, bevel_mm=0.3),
        geo.make_box_mm("Reg_Back", -pit_in - 12, ptl_out, pit_in + 12, y_max, ptl_h, z_reg(ptl_out), mats["mortar"], col, bevel_mm=0.3),
    ]
    model_objs.append(join_objects(reg_objs, "Q16_RegMortar", col))

    # 6. QAT-10 Membrana inferior penetrando en bajante (cuadrada en caja PTL-7 -> cilindrica en bajante)
    mem_inf_parts = [
        geo.make_square_pit_ring("Q16MI_Wall", pit_in - 4.0, 0.0, pit_in - 4.0, pit_in, 0.0, pit_in,
                                 lambda x, y: 24.0, lambda x, y: ptl_h + 19.0, mats["bitumen"], col, bevel_mm=0.2),
        geo.make_square_pit_ring("Q16MI_Rim", pit_in, 0.0, pit_in, pit_in + 35.0, 0.0, pit_in + 35.0,
                                 lambda x, y: ptl_h + 15.0, lambda x, y: ptl_h + 19.0, mats["bitumen"], col, bevel_mm=0.2),
        geo.make_annular_box_cutaway("Q16MI_Floor", br - 6.0, pit_in, pit_in, 24.0, 28.0, mats["bitumen"], col, bevel_mm=0.2),
        geo.make_revolved_profile("Q16MI_Throat", [(br - 10.0, -42.0), (br - 6.0, -42.0), (br - 6.0, 28.0), (br - 10.0, 28.0)],
                                  0.0, math.pi, 32, mats["bitumen"], col, smooth=False),
    ]
    model_objs.append(join_objects(mem_inf_parts, "Q16_MembraneInf", col))

    # 7. Cazoleta metalica (cubeta cuadrada ajustada a caja PTL-7 + cuello cilindrico) + Rejilla + Babero izquierdo
    caz_top = z_reg(ptl_out) + 5.0  # 140
    caz_parts = [
        geo.make_square_pit_ring("Q16C_Ala", caz_h, 0.0, caz_h, caz_h + fl_w, 0.0, caz_h + fl_w,
                                 lambda x, y: caz_top, lambda x, y: caz_top + 3.0, mats["stainless"], col, bevel_mm=0.3),
        geo.make_square_pit_ring("Q16C_Wall", caz_h - 3.5, 0.0, caz_h - 3.5, caz_h, 0.0, caz_h,
                                 lambda x, y: 28.0, lambda x, y: caz_top + 3.0, mats["stainless"], col, bevel_mm=0.3),
        geo.make_annular_box_cutaway("Q16C_Floor", 45.0, caz_h, caz_h, 28.0, 31.5, mats["stainless"], col, bevel_mm=0.3),
        geo.make_revolved_profile("Q16C_Spigot", [(42.0, -45.0), (45.0, -45.0), (45.0, 31.5), (42.0, 31.5)],
                                  0.0, math.pi, 32, mats["stainless"], col),
    ]
    model_objs.append(join_objects(caz_parts, "Q16_Cazoleta", col))

    # Rejilla ranurada
    rej_parts = [
        geo.make_box_mm("Rej_Frame_R", caz_h - 8, caz_h, 0.0, caz_h, caz_top - 4.0, caz_top + 6.0, mats["cast_iron"], col, bevel_mm=0.4),
        geo.make_box_mm("Rej_Frame_L", -caz_h, -caz_h + 8, 0.0, caz_h, caz_top - 4.0, caz_top + 6.0, mats["cast_iron"], col, bevel_mm=0.4),
        geo.make_box_mm("Rej_Frame_B", -caz_h, caz_h, caz_h - 8, caz_h, caz_top - 4.0, caz_top + 6.0, mats["cast_iron"], col, bevel_mm=0.4),
    ]
    for gx in range(-86, 87, 22):
        rej_parts.append(geo.make_box_mm(f"Rej_Bar_{gx}", gx - 5.0, gx + 5.0, 0.0, caz_h - 8, caz_top - 3.0, caz_top + 6.0, mats["stainless"], col, bevel_mm=0.4))
    model_objs.append(join_objects(rej_parts, "Q16_Rejilla", col))

    # Babero / remate vierteaguas izquierdo con labio plegado de goteron
    model_objs.append(geo.make_prism_xz("Q16_Flashing", [(-240.0, caz_top + 28.0), (-240.0, caz_top + 20.0), (-237.0, caz_top + 20.0), (-237.0, caz_top + 24.5),
                                                         (-caz_h - 4, caz_top + 6.0), (-caz_h - 4, caz_top + 3.0), (-240.0, caz_top + 21.5)],
                                        0.0, y_max, mats["zinc"], col, bevel_mm=0.3))

    # 8. QAT-10 Membrana superior (solape 100 mm sobre ala de cazoleta)
    sol_x0 = caz_h + 2.0
    m_sup = geo.make_prism_xz("Q16_MembraneSup", [(sol_x0, caz_top + 4.0), (ptl_out, z_reg(ptl_out)), (x_max, z_reg(x_max)),
                                                  (x_max, z_mem(x_max)), (ptl_out, z_mem(ptl_out)), (sol_x0, caz_top + 8.0)],
                              0.0, y_max, mats["bitumen"], col, bevel_mm=0.2)
    model_objs.append(m_sup)

    # 9. Mortero agarre + Rasilla ceramica
    x_ts = caz_h + 36.0
    model_objs.append(geo.make_prism_xz("Q16_Agarre", [(x_ts + 12, z_mem(ptl_out)), (x_max, z_mem(x_max)), (x_max, z_ag(x_max)), (x_ts + 12, z_ag(ptl_out))],
                                        0.0, y_max, mats["mortar_dark"], col, bevel_mm=0.4))

    tile_parts = []
    tx = x_ts
    idx = 0
    while tx < x_max - 15.0:
        tx_end = min(tx + p["rasilla_l"], x_max)
        zb0 = z_ag(max(tx, ptl_out))
        zb1 = z_ag(tx_end)
        cy = 0.0
        while cy < y_max - 10.0:
            cy_end = min(cy + 140.0, y_max)
            m = mats["rasilla"] if ((idx + int(cy)) % 3 != 0) else mats["rasilla_alt"]
            tile_parts.append(geo.make_prism_xz(f"Q16_T_{idx}_{int(cy)}", [(tx, zb0), (tx_end, zb1), (tx_end, zb1 + p["rasilla_h"]), (tx, zb0 + p["rasilla_h"])],
                                                cy, cy_end, m, col, bevel_mm=1.2))
            cy = cy_end + p["rasilla_joint"]
        tx = tx_end + p["rasilla_joint"]
        idx += 1
    model_objs.append(join_objects(tile_parts, "Q16_Rasilla", col))

    geo.setup_studio_environment(bpy.context.scene, floor_z_mm=forj_bot, center_xy_mm=(250, 180), scale_diag_m=1.4)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle2_nte_qat16_cazoleta.blend", r"d:\C2\models\detalle2_nte_qat16_cazoleta.glb")

    geo.render_camera_shot(bpy.context.scene, "Cam_Hero", (-640, -1120, 560), (240, 150, 10),
                           r"d:\C2\renders\detalle2_qat16_hero.png", lens_mm=58.0)
    geo.render_camera_shot(bpy.context.scene, "Cam_Section", (280, -1900, 0), (280, 0, 0),
                           r"d:\C2\renders\detalle2_qat16_section.png", ortho_scale_m=1.40)


# ==============================================================================
# DETALLE 2B: NTE QAT-17 — Canalon en Faldon de Hormigon Aligerado-S
# ==============================================================================
def build_detalle2_qat17():
    reset_scene()
    mats = geo.get_material_palette()
    meta = DETAILS["detalle2_qat17"]
    p = meta["params"]
    col = geo.ensure_collection("Detalle2_QAT17")

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
    y_max = 380.0
    slope = p["slope"]

    def z_fal(x): return ptl7_h + slope * max(0.0, x - ptl7_x1)
    def z_reg(x): return z_fal(x) + p["reg_mortar_h"]
    def z_mem(x): return z_reg(x) + p["mem_h"]
    def z_ag(x): return z_mem(x) + p["agarre_h"]

    model_objs = []

    # 1. Forjado estructural
    model_objs.append(geo.make_box_mm("Q17_Forjado", wall_x0, x_max, 0.0, y_max, forj_bot, 0.0, mats["concrete"], col, bevel_mm=0.8))

    # 2. Muro fabrica ladrillo con hiladas reales y juntas de mortero + ROZA PTL-2 (50x50 mm)
    wall_parts = []
    z_b = 0.0
    bh, mh = 52.0, 10.0
    row_k = 0
    while z_b < wall_top:
        z_hi = min(z_b + bh, wall_top)
        # Check if this course intersects roza PTL-2 (Z in [roza_z0, roza_z1], X in [-roza_s, 0])
        if z_hi > roza_z0 and z_b < roza_z1:
            # Split cleanly around roza
            if z_b < roza_z0:
                wall_parts.append(geo.make_box_mm(f"WB_{row_k}_bot", wall_x0, 0.0, 0.0, y_max, z_b, roza_z0, mats["brick"], col, bevel_mm=0.6))
            za = max(z_b, roza_z0)
            zb = min(z_hi, roza_z1)
            wall_parts.append(geo.make_box_mm(f"WB_{row_k}_back", wall_x0, -roza_s, 0.0, y_max, za, zb, mats["brick"], col, bevel_mm=0.6))
            if z_hi > roza_z1:
                wall_parts.append(geo.make_box_mm(f"WB_{row_k}_top", wall_x0, 0.0, 0.0, y_max, roza_z1, z_hi, mats["brick"], col, bevel_mm=0.6))
        else:
            # Two brick wythes in 1-pie 240mm wall
            if row_k % 2 == 0:
                wall_parts.append(geo.make_box_mm(f"WB_{row_k}_A", wall_x0, -125.0, 0.0, y_max, z_b, z_hi, mats["brick"], col, bevel_mm=0.8))
                wall_parts.append(geo.make_box_mm(f"WB_{row_k}_B", -115.0, 0.0, 0.0, y_max, z_b, z_hi, mats["brick"], col, bevel_mm=0.8))
                wall_parts.append(geo.make_box_mm(f"WMV_{row_k}", -125.0, -115.0, 0.0, y_max, z_b, z_hi, mats["mortar"], col, bevel_mm=0.2))
            else:
                wall_parts.append(geo.make_box_mm(f"WB_{row_k}_F", wall_x0, 0.0, 0.0, y_max, z_b, z_hi, mats["brick"], col, bevel_mm=0.8))
        if z_hi + mh <= wall_top:
            x_j_end = -roza_s if (z_hi + mh > roza_z0 and z_hi < roza_z1) else 0.0
            wall_parts.append(geo.make_box_mm(f"WM_{row_k}", wall_x0, x_j_end, 0.0, y_max, z_hi, z_hi + mh, mats["mortar"], col, bevel_mm=0.2))
        z_b += bh + mh
        row_k += 1
    model_objs.append(join_objects(wall_parts, "Q17_WallBricks", col))

    # 3. RPE-3 Mortero 1:8 bajo canalon
    rpe_h = p["rpe3_h"]
    model_objs.append(geo.make_box_mm("Q17_RPE3", 0.0, ptl7_x0, 0.0, y_max, 0.0, rpe_h, mats["mortar_dark"], col, bevel_mm=0.4))

    # 4. PTL-7 Maestra ladrillo hueco sencillo (X: 200..250, Z: 0..135)
    model_objs.append(geo.make_hollow_brick("Q17_PTL7_Bricks", ptl7_x0, ptl7_x1, 0.0, y_max, 0.0, ptl7_h, 1, 3, mats["brick"], col))

    # 5. Faldon hormigon aligerado
    model_objs.append(geo.make_prism_xz("Q17_HormigonAlig", [(ptl7_x1, 0), (x_max, 0), (x_max, z_fal(x_max)), (ptl7_x1, ptl7_h)],
                                        0.0, y_max, mats["light_conc"], col, bevel_mm=0.6))

    # 6. Mortero regularizacion 1:6
    reg_poly = [(ptl7_x0, ptl7_h), (ptl7_x1, ptl7_h), (x_max, z_fal(x_max)), (x_max, z_reg(x_max)), (ptl7_x1, z_reg(ptl7_x1)), (ptl7_x0, z_reg(ptl7_x1))]
    reg_objs = [
        geo.make_prism_xz("Reg_Main", reg_poly, 0.0, y_max, mats["mortar"], col, bevel_mm=0.4),
        geo.make_prism_xz("Roza_Mortar", [(-roza_s, roza_z0), (0, roza_z0), (-38, roza_z0 + 30), (-roza_s, roza_z0 + 30)], 0.0, y_max, mats["mortar"], col, bevel_mm=0.3),
    ]
    model_objs.append(join_objects(reg_objs, "Q17_RegMortar", col))

    # 7. QAT-2 Canalon de cinc plegado (espesor 2.0 mm solido para vista nitida)
    ch = p["gutter_chamfer"]
    fl_end = ptl7_x0 + p["zinc_flange_w"]
    z_ala = z_reg(ptl7_x1) + 1.5
    t = 2.0
    zinc_poly = [
        (-38.0, roza_z0 + 30.0), (2.0, roza_z0), (2.0, rpe_h + ch), (2.0 + ch, rpe_h),
        (ptl7_x0 - ch - 2.0, rpe_h), (ptl7_x0 - 2.0, rpe_h + ch), (ptl7_x0 - 2.0, z_ala), (fl_end, z_ala),
        (fl_end, z_ala + t), (ptl7_x0 - 2.0 - t, z_ala + t), (ptl7_x0 - 2.0 - t, rpe_h + ch + 0.8),
        (ptl7_x0 - ch - 2.8, rpe_h + t), (2.8 + ch, rpe_h + t), (2.0 + t, rpe_h + ch + 0.8),
        (2.0 + t, roza_z0 + t), (-36.5, roza_z0 + 31.5)
    ]
    model_objs.append(geo.make_prism_xz("Q17_ZincGutter", zinc_poly, 0.0, y_max, mats["zinc"], col, bevel_mm=0.3))

    # 8. Membrana impermeabilizante (solape >= 100 mm sobre canalon)
    sol_x0 = fl_end - p["solape_mm"]
    mem_poly = [(sol_x0, z_ala + t), (ptl7_x1, z_ala + t), (x_max, z_reg(x_max)),
                (x_max, z_mem(x_max)), (ptl7_x1, z_mem(ptl7_x1)), (sol_x0, z_ala + t + 4.0)]
    model_objs.append(geo.make_prism_xz("Q17_Membrane", mem_poly, 0.0, y_max, mats["bitumen"], col, bevel_mm=0.2))

    # 9. Mortero agarre + Rasilla con vuelo 20 mm sobre canalon
    model_objs.append(geo.make_prism_xz("Q17_Agarre", [(ptl7_x0 + 8.0, z_mem(ptl7_x1)), (x_max, z_mem(x_max)),
                                                       (x_max, z_ag(x_max)), (ptl7_x0 + 8.0, z_ag(ptl7_x1))],
                                        0.0, y_max, mats["mortar_dark"], col, bevel_mm=0.4))

    tile_parts = []
    tx = ptl7_x0 - p["rasilla_overhang"]
    idx = 0
    while tx < x_max - 15.0:
        tx_end = min(tx + p["rasilla_l"], x_max)
        zb0 = z_ag(max(tx, ptl7_x1))
        zb1 = z_ag(tx_end)
        cy = 0.0
        while cy < y_max - 10.0:
            cy_end = min(cy + 140.0, y_max)
            m = mats["rasilla"] if ((idx + int(cy)) % 3 != 0) else mats["rasilla_alt"]
            tile_parts.append(geo.make_prism_xz(f"Q17_T_{idx}_{int(cy)}", [(tx, zb0), (tx_end, zb1), (tx_end, zb1 + p["rasilla_h"]), (tx, zb0 + p["rasilla_h"])],
                                                cy, cy_end, m, col, bevel_mm=1.2))
            cy = cy_end + p["rasilla_joint"]
        tx = tx_end + p["rasilla_joint"]
        idx += 1
    model_objs.append(join_objects(tile_parts, "Q17_Rasilla", col))

    geo.setup_studio_environment(bpy.context.scene, floor_z_mm=forj_bot, center_xy_mm=(320, 190), scale_diag_m=1.8)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle2_nte_qat17_canalon.blend", r"d:\C2\models\detalle2_nte_qat17_canalon.glb")

    geo.render_camera_shot(bpy.context.scene, "Cam_Hero", (-780, -1520, 820), (330, 160, 210),
                           r"d:\C2\renders\detalle2_qat17_hero.png", lens_mm=48.0)
    geo.render_camera_shot(bpy.context.scene, "Cam_Section", (350, -2300, 195), (350, 0, 195),
                           r"d:\C2\renders\detalle2_qat17_section.png", ortho_scale_m=1.75)


# ==============================================================================
# DETALLE 3: Analisis Detalle — Azotea con Hormigon Celular · Cazoleta Sifonica
# ==============================================================================
def build_detalle3():
    reset_scene()
    mats = geo.get_material_palette()
    meta = DETAILS["detalle3"]
    p = meta["params"]
    col = geo.ensure_collection("Detalle3_CazoletaSifonica")

    hx = p["span_half_x"]                 # 750
    y_max = p["span_half_y"]              # 420
    forj_bot = -p["forjado_h"]            # -250
    rev_h = p["revest_h"]                 # 15
    hole_r = p["slab_hole_r"]             # 84
    br = p["bajante_od"] * 0.5            # 55
    bw = p["bajante_wall"]
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

    def z_hc(ax): return pit_top + slope * max(0.0, abs(ax) - pit_out)
    def z_m16(ax): return z_hc(ax) + p["mortero16_h"]
    def z_mem(ax): return z_m16(ax) + p["membrana_h"]
    def z_m18(ax): return z_mem(ax) + p["mortero18_h"] + 7.0
    def z_ras(ax): return z_m18(ax) + p["rasilla_h"]

    model_objs = []

    # 1. Forjado estructural con perforacion Ø168 mm en (0,0) (cutaway Y >= 0)
    f_ann = geo.make_annular_box_cutaway("D3F_Ring", hole_r, 420.0, y_max, forj_bot, 0.0, mats["concrete"], col)
    f_l = geo.make_box_mm("D3F_L", -hx, -420.0, 0.0, y_max, forj_bot, 0.0, mats["concrete"], col)
    f_r = geo.make_box_mm("D3F_R", 420.0, hx, 0.0, y_max, forj_bot, 0.0, mats["concrete"], col)
    model_objs.append(join_objects([f_ann, f_l, f_r], "D3_Forjado", col))

    # 2. Revestimiento inferior (15 mm bajo forjado + cara exterior falseado)
    rev_parts = [
        geo.make_box_mm("Rev_L", -hx, -fal_out, 0.0, y_max, forj_bot - rev_h, forj_bot, mats["revest"], col, bevel_mm=0.4),
        geo.make_box_mm("Rev_R", fal_out, hx, 0.0, y_max, forj_bot - rev_h, forj_bot, mats["revest"], col, bevel_mm=0.4),
        geo.make_box_mm("Rev_B", -fal_out, fal_out, fal_out, y_max, forj_bot - rev_h, forj_bot, mats["revest"], col, bevel_mm=0.4),
        geo.make_box_mm("Rev_SL", -fal_out - rev_h, -fal_out, 0.0, fal_out + rev_h, fal_bot, forj_bot, mats["revest"], col, bevel_mm=0.4),
        geo.make_box_mm("Rev_SR", fal_out, fal_out + rev_h, 0.0, fal_out + rev_h, fal_bot, forj_bot, mats["revest"], col, bevel_mm=0.4),
        geo.make_box_mm("Rev_SB", -fal_out, fal_out, fal_out, fal_out + rev_h, fal_bot, forj_bot, mats["revest"], col, bevel_mm=0.4),
    ]
    model_objs.append(join_objects(rev_parts, "D3_Revestimiento", col))

    # 3. Falseado Ladrillo del 4 (40 mm alrededor del patinillo, con celdas huecas visibles en Y=0)
    fal_parts = []
    z_c = fal_bot + 5.0
    while z_c + 108.0 <= forj_bot + 5.0:
        z_hi = min(z_c + 108.0, forj_bot)
        fal_parts.append(geo.make_hollow_brick(f"FalL_{int(z_c)}", -fal_out, -fal_in, 0.0, fal_out, z_c, z_hi, 1, 2, mats["brick"], col))
        fal_parts.append(geo.make_hollow_brick(f"FalR_{int(z_c)}", fal_in, fal_out, 0.0, fal_out, z_c, z_hi, 1, 2, mats["brick"], col))
        fal_parts.append(geo.make_box_mm(f"FalB_{int(z_c)}", -fal_in, fal_in, fal_in, fal_out, z_c, z_hi, mats["brick"], col))
        z_c += 116.0
    model_objs.append(join_objects(fal_parts, "D3_FalseadoBricks", col))

    # 4. Bajante PVC-U Ø110 mm con copa superior
    baj_rz = [
        (br - bw, fal_bot), (br, fal_bot), (br, -55.0), (copa_r, -42.0), (copa_r, 0.0),
        (copa_r - bw, 0.0), (copa_r - bw, -42.0), (br - bw, -55.0)
    ]
    model_objs.append(geo.make_revolved_profile("D3_Bajante", baj_rz, 0.0, math.pi, 36, mats["pvc"], col))

    # 5. Manta Fibra de Vidrio (25 mm envolviendo bajante y copa)
    fib_rz = [
        (br + 0.8, fal_bot), (fib_r, fal_bot), (fib_r, -1.0), (copa_r + 0.8, -1.0),
        (copa_r + 0.8, -43.0), (br + 0.8, -56.0)
    ]
    model_objs.append(geo.make_revolved_profile("D3_FibraVidrio", fib_rz, 0.0, math.pi, 36, mats["fiberglass"], col))

    # 6. Barrera Cortavapor (3 mm sobre forjado)
    bv_ann = geo.make_annular_box_cutaway("D3BV_Ring", hole_r, 420.0, y_max, 0.0, bv_h, mats["vapor"], col, bevel_mm=0.2)
    bv_l = geo.make_box_mm("D3BV_L", -hx, -420.0, 0.0, y_max, 0.0, bv_h, mats["vapor"], col, bevel_mm=0.2)
    bv_r = geo.make_box_mm("D3BV_R", 420.0, hx, 0.0, y_max, 0.0, bv_h, mats["vapor"], col, bevel_mm=0.2)
    model_objs.append(join_objects([bv_ann, bv_l, bv_r], "D3_BarreraCortavapor", col))

    # 7. Caja de Ladrillo Hueco alrededor de cazoleta (LHD 70x115 mm, 2x4 celdas huecas visibles)
    model_objs.append(geo.make_square_hollow_curb_cutaway("D3_PitBricks", pit_in, pit_out, 0.0, pit_out, bv_h, pit_top, 2, 4, mats["brick"], col))

    # Mortero asiento en el fondo de la caja
    model_objs.append(geo.make_annular_box_cutaway("D3_PitMortarBed", copa_r + 2.0, pit_in, pit_in, bv_h, p["caz_bot_z"], mats["mortar"], col, bevel_mm=0.4))

    # 8. Hormigon Celular al 3% rodeando la caja de ladrillo
    model_objs.append(geo.make_square_pit_ring(
        "D3_HormigonCelular", pit_out, 0.0, pit_out, hx, 0.0, y_max,
        lambda x, y: bv_h, lambda x, y: z_hc(x), mats["cellular"], col, bevel_mm=0.6
    ))

    # 9. Mortero 1:6 regularizacion
    model_objs.append(geo.make_square_pit_ring(
        "D3_Mortero16", pit_in, 0.0, pit_in, hx, 0.0, y_max,
        lambda x, y: z_hc(x), lambda x, y: z_m16(x), mats["mortar"], col, bevel_mm=0.4
    ))

    # 10. Refuerzo Membrana (penetra hasta la bajante) + Membrana Principal (solape 100 mm)
    caz_h = p["caz_outer_half"]              # 120
    caz_bot = p["caz_bot_z"]                 # 35
    caz_fl = p["caz_flange_z"]               # 139
    tail_bot = p["tail_bot_z"]               # -45
    weir_r = p["weir_id"] * 0.5              # 52
    ref_ext = pit_out + p["refuerzo_ext_w"]  # 435

    ref_parts = [
        geo.make_square_pit_ring("Ref_Slope", pit_in - 4.0, 0.0, pit_in - 4.0, ref_ext, 0.0, min(y_max, ref_ext),
                                 lambda x, y: z_m16(x), lambda x, y: z_m16(x) + 4.0, mats["bitumen"], col, bevel_mm=0.2),
        geo.make_square_pit_ring("Ref_PitWall", pit_in - 4.0, 0.0, pit_in - 4.0, pit_in, 0.0, pit_in,
                                 lambda x, y: caz_bot, lambda x, y: z_m16(pit_out) + 4.0, mats["bitumen"], col, bevel_mm=0.2),
        geo.make_annular_box_cutaway("Ref_PitFloor", weir_r + 0.5, pit_in, pit_in, caz_bot, caz_bot + 4.0, mats["bitumen"], col, bevel_mm=0.2),
        geo.make_revolved_profile("Ref_Throat", [(weir_r + 0.5, tail_bot), (weir_r + 3.5, tail_bot), (weir_r + 3.5, caz_bot + 4.0), (weir_r + 0.5, caz_bot + 4.0)],
                                  0.0, math.pi, 32, mats["bitumen"], col, smooth=False),
    ]
    model_objs.append(join_objects(ref_parts, "D3_RefuerzoMembrana", col))

    sol_start = caz_h + 6.0
    model_objs.append(geo.make_square_pit_ring(
        "D3_Membrana", sol_start, 0.0, sol_start, hx, 0.0, y_max,
        lambda x, y: z_m16(x) + 7.2 if abs(x) < caz_h + p["caz_flange_w"] and y < caz_h + p["caz_flange_w"] else z_m16(x) + 4.5,
        lambda x, y: z_m16(x) + 11.2 if abs(x) < caz_h + p["caz_flange_w"] and y < caz_h + p["caz_flange_w"] else z_m16(x) + 8.5,
        mats["bitumen"], col, bevel_mm=0.2
    ))

    # 11. Cazoleta Sifonica + Agua (sello hidraulico) + Campana Sifonica + Rejilla
    weir_top = p["weir_top_z"]               # 98
    bell_r = p["bell_od"] * 0.5              # 82
    bell_bot = p["bell_skirt_z"]             # 65
    bell_dome = p["bell_dome_z"]             # 126
    rej_out = p["rejilla_outer_half"]        # 124
    rej_in = p["rejilla_inner_half"]         # 109
    rej_top = p["rejilla_top_z"]             # 182
    rej_t = p["rejilla_t"]                   # 10

    # Cuerpo exterior cazoleta + ala + tubo rebosadero central (entra dentro del cuello Ref_Throat limpiamente!)
    caz_parts = [
        geo.make_square_pit_ring("Caz_Ala", caz_h, 0.0, caz_h, caz_h + p["caz_flange_w"], 0.0, caz_h + p["caz_flange_w"],
                                 lambda x, y: caz_fl + 1.0, lambda x, y: caz_fl + 4.0, mats["stainless"], col, bevel_mm=0.4),
        geo.make_square_pit_ring("Caz_Wall", caz_h - 3.0, 0.0, caz_h - 3.0, caz_h, 0.0, caz_h,
                                 lambda x, y: caz_bot + 4.0, lambda x, y: caz_fl + 4.0, mats["stainless"], col, bevel_mm=0.3),
        geo.make_annular_box_cutaway("Caz_Floor", weir_r - 3.0, caz_h, caz_h, caz_bot + 4.0, caz_bot + 7.0, mats["stainless"], col, bevel_mm=0.3),
        geo.make_revolved_profile("Caz_Weir", [(weir_r - 3.0, tail_bot - 3.0), (weir_r, tail_bot - 3.0), (weir_r, weir_top), (weir_r - 3.0, weir_top)],
                                  0.0, math.pi, 36, mats["stainless"], col),
    ]
    model_objs.append(join_objects(caz_parts, "D3_CazoletaBody", col))

    # Agua del sello hidraulico (transparente azul claro IOR 1.333 entre rebosadero y cubeta)
    model_objs.append(geo.make_annular_box_cutaway(
        "D3_WaterSeal", weir_r + 0.2, caz_h - 3.2, caz_h - 3.2, caz_bot + 7.2, weir_top, mats["water"], col, bevel_mm=0.0
    ))

    # Campana sifonica acampanada + vastago central
    bell_rz = [
        (bell_r - 4.0, bell_bot), (bell_r, bell_bot), (bell_r, bell_dome - 10.0), (38.0, bell_dome + 4.0),
        (11.0, bell_dome + 4.0), (11.0, rej_top - rej_t), (0.0, rej_top - rej_t),
        (0.0, bell_dome), (36.0, bell_dome), (bell_r - 4.0, bell_dome - 14.0)
    ]
    model_objs.append(geo.make_revolved_profile("D3_CampanaSifonica", bell_rz, 0.0, math.pi, 36, mats["stainless"], col))

    # Marco perimetral + Rejilla ranurada + Tornillo central inox
    model_objs.append(geo.make_square_pit_ring(
        "D3_RejillaFrame", rej_in, 0.0, rej_in, rej_out, 0.0, rej_out,
        lambda x, y: rej_top - 22.0, lambda x, y: rej_top, mats["cast_iron"], col, bevel_mm=0.6
    ))
    grate_parts = [
        geo.make_box_mm("Rej_CrossC", -12.0, 12.0, 0.0, rej_in, rej_top - rej_t, rej_top, mats["stainless"], col, bevel_mm=0.4),
        geo.make_box_mm("Rej_Bolt", -5.0, 5.0, 0.0, 5.0, rej_top - 24.0, rej_top + 2.0, mats["cast_iron"], col, bevel_mm=0.5),
    ]
    for gx in range(-96, 97, 22):
        if abs(gx) < 16:
            continue
        grate_parts.append(geo.make_box_mm(f"Rej_Bar_{gx}", gx - 5.0, gx + 5.0, 0.0, rej_in, rej_top - rej_t, rej_top, mats["stainless"], col, bevel_mm=0.4))
    model_objs.append(join_objects(grate_parts, "D3_RejillaGrate", col))

    # 12. Mortero de agarre 1:8
    model_objs.append(geo.make_square_pit_ring(
        "D3_Mortero18", rej_out, 0.0, rej_out, hx, 0.0, y_max,
        lambda x, y: z_mem(x) + 4.5, lambda x, y: z_m18(x), mats["mortar_dark"], col, bevel_mm=0.4
    ))

    # 13. Rasilla de Aspe (280x140x20 mm con junta 6 mm rodeando rejilla y con pendiente 3%)
    tile_parts = []
    tl, tw, tj = p["rasilla_l"], p["rasilla_w"], p["rasilla_joint"]
    # Tiras de rasilla por bandas en Y: fuera de la rejilla y al lado izquierdo/derecho
    for sx in (-1, 1):
        cx_s = rej_out + 4.0
        col_i = 0
        while cx_s < hx - 12.0:
            cx_e = min(cx_s + tl, hx)
            x0, x1 = sorted((sx * cx_s, sx * cx_e))
            cy = 0.0
            while cy < y_max - 10.0:
                cy_e = min(cy + tw, y_max)
                m = mats["rasilla"] if ((col_i + int(cy)) % 3 != 0) else mats["rasilla_alt"]
                t_poly = [(x0, z_m18(abs(x0))), (x1, z_m18(abs(x1))), (x1, z_ras(abs(x1))), (x0, z_ras(abs(x0)))]
                tile_parts.append(geo.make_prism_xz(f"D3T_{sx}_{col_i}_{int(cy)}", t_poly, cy, cy_e, m, col, bevel_mm=1.2))
                cy = cy_e + tj
            cx_s = cx_e + tj
            col_i += 1
    # Baldosas detras de la rejilla (|X| <= rej_out, Y: rej_out+4..y_max)
    cy = rej_out + 4.0
    r_i = 0
    while cy < y_max - 10.0:
        cy_e = min(cy + tw, y_max)
        # dividir X en dos piezas simetricas [-rej_out..-3] y [3..rej_out]
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 3.0, sx * rej_out))
            m = mats["rasilla"] if ((r_i + (1 if sx > 0 else 0)) % 2 == 0) else mats["rasilla_alt"]
            t_poly = [(x0, z_m18(abs(x0))), (x1, z_m18(abs(x1))), (x1, z_ras(abs(x1))), (x0, z_ras(abs(x0)))]
            tile_parts.append(geo.make_prism_xz(f"D3TB_{sx}_{r_i}", t_poly, cy, cy_e, m, col, bevel_mm=1.2))
        cy = cy_e + tj
        r_i += 1
    model_objs.append(join_objects(tile_parts, "D3_Rasilla", col))

    geo.setup_studio_environment(bpy.context.scene, floor_z_mm=fal_bot, center_xy_mm=(0, 200), scale_diag_m=1.85)
    export_model_glb_and_blend(model_objs, r"d:\C2\models\detalle3_cazoleta_sifonica.blend", r"d:\C2\models\detalle3_cazoleta_sifonica.glb")

    geo.render_camera_shot(bpy.context.scene, "Cam_Hero", (-1060, -1840, 560), (0, 140, -135),
                           r"d:\C2\renders\detalle3_hero.png", lens_mm=52.0)
    geo.render_camera_shot(bpy.context.scene, "Cam_Closeup", (-280, -680, 275), (0, 50, 75),
                           r"d:\C2\renders\detalle3_closeup.png", lens_mm=70.0, dof_fstop=5.0)
    geo.render_camera_shot(bpy.context.scene, "Cam_Section", (0, -2500, -180), (0, 0, -180),
                           r"d:\C2\renders\detalle3_section.png", ortho_scale_m=1.75)


if __name__ == "__main__":
    arg = sys.argv[-1] if "--" in sys.argv else "all"
    if arg in ("all", "1"):
        build_detalle1()
    if arg in ("all", "2a", "2"):
        build_detalle2_qat16()
    if arg in ("all", "2b", "2"):
        build_detalle2_qat17()
    if arg in ("all", "3"):
        build_detalle3()
    if arg in ("all", "part2"):
        from build_blender_scenes_part2 import build_part2_3d
        build_part2_3d()
