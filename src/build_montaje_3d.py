r"""
Builds the Piece-by-Piece / Layer-by-Layer Animated Assembly Scene for Detalle 1 (Cartillas IVE)
in Blender 5.2:
  - Exports granular GLB: d:\C2\models\detalle1_montaje_piezas.glb (every piece tagged PH01..PH10)
  - Saves animated BLEND: d:\C2\models\detalle1_montaje.blend
  - Renders 900 photorealistic EEVEE Raytracing frames (30 fps x 30.0 s) to d:\C2\scratch_montaje\frames3d\

Usage:
  blender.exe -b --python "d:\C2\src\build_montaje_3d.py" -- test     # exports GLB + renders 3 check frames
  blender.exe -b --python "d:\C2\src\build_montaje_3d.py" -- render   # exports GLB + renders all 900 frames
"""

import math
import os
import sys
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


def keyframe_piece(obj, f_start, f_end, dz_mm=220.0, dx_mm=0.0, dy_mm=0.0):
    """Animates a piece appearing at f_start and easing smoothly into exact final position at f_end."""
    # Ensure exact resting transform at (0,0,0) delta
    obj.location = (0.0, 0.0, 0.0)
    if f_start > 1:
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=0)
        obj.keyframe_insert(data_path="hide_render", frame=f_start - 1)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=f_start)

    obj.location = (dx_mm * MM, dy_mm * MM, dz_mm * MM)
    obj.keyframe_insert(data_path="location", frame=f_start)

    obj.location = (0.0, 0.0, 0.0)
    obj.keyframe_insert(data_path="location", frame=f_end)

    # Ease-out bezier curves for smooth mechanical placement
    if obj.animation_data and obj.animation_data.action:
        try:
            for fc in obj.animation_data.action.fcurves:
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"
                elif fc.data_path == "location":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "BEZIER"
                        kp.handle_left_type = "AUTO_CLAMPED"
                        kp.handle_right_type = "AUTO_CLAMPED"
        except Exception:
            pass


def build_animated_detalle1():
    reset_scene()
    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = 899
    scene.render.fps = 30

    mats = geo.get_material_palette()
    p = DETAILS["detalle1"]["params"]
    st = p["steps_x"]
    col = geo.ensure_collection("Detalle1_Montaje")

    dx_end = p["deck_end_x"]          # 985
    j_x0, j_x1 = dx_end, dx_end + p["junta_eps_w"]        # 985..1000
    ei_x0, ei_x1 = j_x1, j_x1 + p["enfoscado_int_w"]      # 1000..1015
    pb_x0, pb_x1 = ei_x1, ei_x1 + p["peto_brick_w"]       # 1015..1155
    ee_x0, ee_x1 = pb_x1, pb_x1 + p["enfoscado_ext_w"]    # 1155..1175
    y_max = 960.0
    forj_bot = -p["forjado_h"]
    comp_bot = -p["compresion_h"]
    peto_top = p["peto_top_z"]

    def z_fp_core(x): return p["fp_min_h"] + p["slope"] * x
    def z_fp_top(x): return z_fp_core(x) + p["fp_reg_h"]
    def z_bv_top(x): return z_fp_top(x) + p["bv_h"]
    def z_at_top(x): return z_bv_top(x) + p["at_h"]
    def z_i_top(x): return z_at_top(x) + p["i_h"]
    def z_cs_top(x): return z_i_top(x) + p["cs_h"]
    def z_m_top(x): return z_cs_top(x) + p["mortero_agarre_h"]
    def z_p_top(x): return z_m_top(x) + p["tile_h"]

    model_objs = []

    def reg(obj, fs, fe, dz=200.0, dx=0.0, dy=0.0):
        model_objs.append(obj)
        keyframe_piece(obj, fs, fe, dz_mm=dz, dx_mm=dx, dy_mm=dy)
        return obj

    # ------------------------------------------------------------------
    # FASE 01 (frames 2..84): SR Viguetas Pretensadas + Bovedillas
    # ------------------------------------------------------------------
    for idx, vx in enumerate((180.0, 760.0)):
        vp = [
            (vx - 60, forj_bot), (vx + 60, forj_bot), (vx + 60, forj_bot + 42),
            (vx + 28, forj_bot + 52), (vx + 26, comp_bot), (vx - 26, comp_bot),
            (vx - 28, forj_bot + 52), (vx - 60, forj_bot + 42)
        ]
        vig = geo.make_prism_xz(f"PH01_{idx:02d}_Vigueta", vp, 0, y_max, mats["concrete"], col, bevel_mm=0.6)
        reg(vig, 2 + idx * 8, 22 + idx * 8, dz=240.0)
        for r_i, rx in enumerate((vx - 28, vx + 28)):
            bar = geo.make_box_mm(f"PH01_{idx:02d}_Armadura_{r_i}", rx - 3.5, rx + 3.5, -8.0, y_max,
                                  forj_bot + 16.5, forj_bot + 23.5, mats["rebar"], col, bevel_mm=0.3)
            reg(bar, 2 + idx * 8, 22 + idx * 8, dz=240.0)

    yb = 0.0
    bov_i = 0
    while yb < y_max - 5.0:
        yb1 = min(yb + 245.0, y_max)
        fs = 26 + bov_i * 6
        b_c = geo.make_hollow_brick(f"PH01_{bov_i:02d}_BovedillaC", 240.0, 700.0, yb, yb1, forj_bot + 10, comp_bot, 3, 1, mats["brick"], col)
        b_l = geo.make_hollow_brick(f"PH01_{bov_i:02d}_BovedillaL", 0.0, 120.0, yb, yb1, forj_bot + 10, comp_bot, 1, 1, mats["brick"], col)
        reg(b_c, fs, fs + 18, dz=200.0)
        reg(b_l, fs + 2, fs + 20, dz=200.0)
        yb += 250.0
        bov_i += 1

    # ------------------------------------------------------------------
    # FASE 02 (frames 84..156): SR Capa de Compresion + Zuncho
    # ------------------------------------------------------------------
    zun = geo.make_box_mm("PH02_00_Zuncho", 840.0, ee_x1, 0, y_max, forj_bot, comp_bot, mats["concrete"], col, bevel_mm=0.8)
    reg(zun, 86, 120, dz=180.0)
    comp = geo.make_box_mm("PH02_01_Compresion", 0.0, ee_x1, 0, y_max, comp_bot, 0.0, mats["concrete"], col, bevel_mm=0.8)
    reg(comp, 114, 152, dz=180.0)

    # ------------------------------------------------------------------
    # FASE 03 (frames 156..264): Peto LHD por hiladas + Enfoscado + Albardilla + EPS
    # ------------------------------------------------------------------
    z_cur = 0.0
    row_i = 0
    while z_cur + 90.0 <= peto_top:
        fs = 156 + row_i * 8
        row_objs = []
        y_cur = 0.0
        if row_i % 2 == 1:
            row_objs.append(geo.make_hollow_brick(f"PH03_R{row_i}_B0", pb_x0, pb_x1, 0.0, 120.0, z_cur, z_cur + 90.0, 2, 3, mats["brick"], col))
            y_cur = 128.0
        b_k = 1
        while y_cur < y_max - 10.0:
            y_end = min(y_cur + 240.0, y_max)
            row_objs.append(geo.make_hollow_brick(f"PH03_R{row_i}_B{b_k}", pb_x0, pb_x1, y_cur, y_end, z_cur, z_cur + 90.0, 2, 3, mats["brick"], col))
            y_cur = y_end + 8.0
            b_k += 1
        if z_cur + 100.0 <= peto_top:
            row_objs.append(geo.make_box_mm(f"PH03_R{row_i}_M", pb_x0, pb_x1, 0, y_max, z_cur + 90.0, z_cur + 100.0, mats["mortar"], col, bevel_mm=0.2))
        for k, o in enumerate(row_objs):
            reg(o, fs + k, fs + k + 14, dz=110.0)
        z_cur += 100.0
        row_i += 1

    enf_int = geo.make_box_mm("PH03_90_EnfoscadoInt", ei_x0, ei_x1, 0, y_max, 0.0, peto_top, mats["mortar"], col, bevel_mm=0.5)
    enf_ext = geo.make_box_mm("PH03_91_EnfoscadoExt", ee_x0, ee_x1, 0, y_max, 0.0, peto_top, mats["render"], col, bevel_mm=0.6)
    albard = geo.make_prism_xz("PH03_92_Albardilla", [(ei_x0 - 8, peto_top), (ee_x1 + 8, peto_top), (ee_x1 + 8, peto_top + 38), (ei_x0 - 8, peto_top + 48)], 0, y_max, mats["render"], col, bevel_mm=1.0)
    eps = geo.make_box_mm("PH03_93_JuntaEPS", j_x0, j_x1, 0, y_max, 0.0, z_at_top(dx_end), mats["eps"], col, bevel_mm=0.3)
    reg(enf_int, 224, 242, dx=-80.0, dz=40.0)
    reg(enf_ext, 226, 244, dx=80.0, dz=40.0)
    reg(albard, 236, 256, dz=120.0)
    reg(eps, 244, 262, dz=140.0)

    # ------------------------------------------------------------------
    # FASE 04 (frames 264..342): FP Formacion de Pendiente + Regularizacion
    # ------------------------------------------------------------------
    x_fp = st["FP"]
    fp_c = geo.make_prism_xz("PH04_00_FPHormigon", [(x_fp, 0), (dx_end, 0), (dx_end, z_fp_core(dx_end)), (x_fp, z_fp_core(x_fp))], 0, y_max, mats["light_conc"], col, bevel_mm=0.6)
    fp_r = geo.make_prism_xz("PH04_01_FPRegulariz", [(x_fp, z_fp_core(x_fp)), (dx_end, z_fp_core(dx_end)), (dx_end, z_fp_top(dx_end)), (x_fp, z_fp_top(x_fp))], 0, y_max, mats["mortar"], col, bevel_mm=0.4)
    reg(fp_c, 266, 306, dz=180.0)
    reg(fp_r, 304, 338, dz=160.0)

    # ------------------------------------------------------------------
    # FASE 05 (frames 342..408): BV Barrera de Vapor
    # ------------------------------------------------------------------
    x_bv = st["BV"]
    bv = geo.make_prism_xz("PH05_00_BarreraVapor", [(x_bv, z_fp_top(x_bv)), (dx_end, z_fp_top(dx_end)), (dx_end, z_bv_top(dx_end)), (x_bv, z_bv_top(x_bv))], 0, y_max, mats["vapor"], col, bevel_mm=0.2)
    reg(bv, 344, 402, dz=180.0)

    # ------------------------------------------------------------------
    # FASE 06 (frames 408..480): AT Aislamiento Termico XPS por planchas
    # ------------------------------------------------------------------
    x_at = st["AT"]
    x_mid_at = 0.5 * (x_at + dx_end)
    y_mid = y_max * 0.5
    xps_rects = [
        (x_at, x_mid_at - 1.5, 0.0, y_mid - 1.5),
        (x_mid_at + 1.5, dx_end, 0.0, y_mid - 1.5),
        (x_at, x_mid_at - 1.5, y_mid + 1.5, y_max),
        (x_mid_at + 1.5, dx_end, y_mid + 1.5, y_max),
    ]
    for xi, (xa, xb, ya, yb_p) in enumerate(xps_rects):
        board = geo.make_prism_xz(f"PH06_{xi:02d}_XPS", [(xa, z_bv_top(xa)), (xb, z_bv_top(xb)), (xb, z_at_top(xb)), (xa, z_at_top(xa))], ya, yb_p, mats["xps"], col, bevel_mm=0.8)
        reg(board, 410 + xi * 12, 434 + xi * 12, dz=200.0)

    # ------------------------------------------------------------------
    # FASE 07 (frames 480..564): I Membrana Impermeabilizante + Entrega 200 mm
    # ------------------------------------------------------------------
    x_i = st["I"]
    z_turn = z_p_top(dx_end) + p["i_turnup_h"]
    i_poly = [(x_i, z_at_top(x_i)), (dx_end, z_at_top(dx_end)), (ei_x0, z_at_top(dx_end)), (ei_x0, z_turn),
              (ei_x0 - p["i_h"], z_turn), (ei_x0 - p["i_h"], z_i_top(dx_end)), (x_i, z_i_top(x_i))]
    mem = geo.make_prism_xz("PH07_00_Membrana", i_poly, 0, y_max, mats["bitumen"], col, bevel_mm=0.2)
    reg(mem, 484, 554, dz=200.0)

    # ------------------------------------------------------------------
    # FASE 08 (frames 564..630): CS Capa Separadora Geotextil
    # ------------------------------------------------------------------
    x_cs = st["CS"]
    cs_end = ei_x0 - p["i_h"] - p["junta_perimetral"]
    cs = geo.make_prism_xz("PH08_00_CapaSeparadora", [(x_cs, z_i_top(x_cs)), (cs_end, z_i_top(cs_end)), (cs_end, z_cs_top(cs_end)), (x_cs, z_cs_top(x_cs))], 0, y_max, mats["geotextile"], col, bevel_mm=0.2)
    reg(cs, 566, 622, dz=180.0)

    # ------------------------------------------------------------------
    # FASE 09 (frames 630..732): P Mortero Agarre + Baldosas Ceramicas pieza a pieza
    # ------------------------------------------------------------------
    x_pm = st["P_MORTERO"]
    pmor = geo.make_prism_xz("PH09_00_MorteroAgarre", [(x_pm, z_cs_top(x_pm)), (cs_end, z_cs_top(cs_end)), (cs_end, z_m_top(cs_end)), (x_pm, z_m_top(x_pm))], 0, y_max, mats["mortar_dark"], col, bevel_mm=0.5)
    reg(pmor, 632, 664, dz=160.0)

    x_p = st["P"]
    tl, tw, tj = p["tile_l"], p["tile_w"], p["tile_joint"]
    tile_idx = 1
    row_x = x_p
    row_k = 0
    tile_queue = []
    while row_x < cs_end - 12.0:
        rx1 = min(row_x + tw, cs_end)
        cy = 0.0
        if row_k % 2 == 1:
            cy_end = min(tl * 0.5, y_max)
            m = mats["rasilla"] if (row_k % 3 != 0) else mats["rasilla_alt"]
            t_o = geo.make_prism_xz(f"PH09_{tile_idx:02d}_Baldosa", [(row_x, z_m_top(row_x)), (rx1, z_m_top(rx1)), (rx1, z_p_top(rx1)), (row_x, z_p_top(row_x))], 0.0, cy_end, m, col, bevel_mm=1.2)
            tile_queue.append(t_o)
            tile_idx += 1
            cy = cy_end + tj
        while cy < y_max - 10.0:
            cy_end = min(cy + tl, y_max)
            m = mats["rasilla"] if ((row_k + int(cy)) % 3 != 0) else mats["rasilla_alt"]
            t_o = geo.make_prism_xz(f"PH09_{tile_idx:02d}_Baldosa", [(row_x, z_m_top(row_x)), (rx1, z_m_top(rx1)), (rx1, z_p_top(rx1)), (row_x, z_p_top(row_x))], cy, cy_end, m, col, bevel_mm=1.2)
            tile_queue.append(t_o)
            tile_idx += 1
            cy = cy_end + tj
        row_x = rx1 + tj
        row_k += 1

    # Stagger all ceramic tiles across frames 664..728
    n_t = max(1, len(tile_queue))
    for i_t, t_o in enumerate(tile_queue):
        fs = 664 + int(round((i_t / n_t) * 44.0))
        reg(t_o, fs, fs + 18, dz=160.0)

    # ------------------------------------------------------------------
    # FASE 10 (frames 732..810): P Junta Perimetral + Rodapie Ceramico
    # ------------------------------------------------------------------
    j_elast = geo.make_box_mm("PH10_00_JuntaElastica", cs_end, ei_x0 - p["i_h"], 0, y_max, z_i_top(dx_end), z_p_top(dx_end), mats["elastomer"], col, bevel_mm=0.2)
    reg(j_elast, 734, 756, dz=120.0)

    rod_x1 = ei_x0 - p["i_h"] - 8.0
    rod_x0 = rod_x1 - p["rodapie_t"]
    rod_z0 = z_p_top(dx_end) + 4.0
    rod_z1 = rod_z0 + p["rodapie_h"]
    rod_adh = geo.make_box_mm("PH10_01_MorteroRodapie", rod_x1, ei_x0 - p["i_h"], 0, y_max, rod_z0, rod_z1, mats["mortar_dark"], col, bevel_mm=0.3)
    reg(rod_adh, 752, 774, dx=-70.0, dz=50.0)

    cy = 0.0
    r_idx = 2
    while cy < y_max - 10.0:
        cy_end = min(cy + 140.0, y_max)
        r_piece = geo.make_box_mm(f"PH10_{r_idx:02d}_Rodapie", rod_x0, rod_x1, cy, cy_end, rod_z0, rod_z1, mats["rasilla"], col, bevel_mm=1.0)
        fs = 766 + (r_idx - 2) * 4
        reg(r_piece, fs, min(806, fs + 16), dx=-90.0, dz=70.0)
        cy = cy_end + tj
        r_idx += 1

    # ------------------------------------------------------------------
    # Studio Backdrop, EEVEE Next Raytracing & Animated Camera
    # ------------------------------------------------------------------
    geo.setup_studio_environment(scene, floor_z_mm=forj_bot, center_xy_mm=(580, 480), scale_diag_m=5.5)

    # Export clean static GLB with all pieces PH01..PH10 for WebGL interactive sequencer
    bpy.ops.object.select_all(action="DESELECT")
    for o in model_objs:
        o.hide_render = False
        o.hide_viewport = False
        o.location = (0.0, 0.0, 0.0)
        o.select_set(True)
    glb_out = r"d:\C2\models\detalle1_montaje_piezas.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_out,
        export_format="GLB",
        use_selection=True,
        export_materials="EXPORT",
        export_normals=True,
        export_apply=True,
        export_yup=True,
    )
    print(f"Exported granular assembly GLB: {glb_out} ({len(model_objs)} pieces)")

    # Re-apply animation frames cleanly after export? Keyframes remain intact; set frame=0
    scene.frame_set(0)

    # Switch to EEVEE Next Raytracing (0.33s/frame -> 900 frames ~5 min)
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng
            break
        except Exception:
            pass
    try:
        scene.eevee.use_raytracing = True
        scene.eevee.taa_render_samples = 24
        scene.eevee.use_shadows = True
    except Exception:
        pass

    # Animated Camera (keeps entire parapet + albardilla + falling pieces comfortably inside frame!)
    rig = geo.ensure_collection("StudioRig")
    cdata = bpy.data.cameras.new("Cam_Montaje")
    cdata.lens = 44.0
    cdata.clip_start = 0.01
    cdata.clip_end = 100.0
    cobj = bpy.data.objects.new("Cam_Montaje", cdata)
    geo.link_obj(cobj, rig)
    scene.camera = cobj

    tgt_empty = bpy.data.objects.new("Cam_Target", None)
    geo.link_obj(tgt_empty, rig)
    tgt_empty.location = (0.58, 0.45, 0.25)

    trk = cobj.constraints.new(type="TRACK_TO")
    trk.target = tgt_empty
    trk.track_axis = "TRACK_NEGATIVE_Z"
    trk.up_axis = "UP_Y"

    cam_keys = [
        (0, (-1.62, -1.68, 1.08), (0.57, 0.44, 0.16)),
        (300, (-1.66, -1.72, 1.24), (0.58, 0.45, 0.24)),
        (600, (-1.64, -1.74, 1.34), (0.58, 0.45, 0.26)),
        (810, (-1.56, -1.78, 1.32), (0.58, 0.45, 0.25)),
        (899, (-1.38, -1.86, 1.28), (0.58, 0.45, 0.25)),
    ]
    for kf, loc, tgt in cam_keys:
        cobj.location = loc
        cobj.keyframe_insert(data_path="location", frame=kf)
        tgt_empty.location = tgt
        tgt_empty.keyframe_insert(data_path="location", frame=kf)

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 864
    scene.render.image_settings.file_format = "PNG"

    blend_out = r"d:\C2\models\detalle1_montaje.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"Saved animated BLEND: {blend_out}")
    return scene


if __name__ == "__main__":
    mode = sys.argv[-1] if "--" in sys.argv else "test"
    scene = build_animated_detalle1()
    frames_dir = r"d:\C2\scratch_montaje\frames3d"
    os.makedirs(frames_dir, exist_ok=True)

    if mode == "test":
        for f in (50, 440, 895):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(frames_dir, f"test_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            print(f"Test frame {f} rendered.")
    elif mode == "render":
        scene.render.filepath = os.path.join(frames_dir, "frame_")
        bpy.ops.render.render(animation=True)
        print("All 900 frames rendered cleanly!")
