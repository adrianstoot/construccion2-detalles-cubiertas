r"""
Exact Millimetric BMesh Geometry Builders & Photorealistic PBR Studio Materials for Blender 5.2 (Cycles HIP + GLB)
All input dimensions in millimeters (mm); converted to Blender meters via MM = 0.001.
Includes tapered teja curva, teja mixta, natural pizarra + hooks, zinc standing-seam,
semicircular gutters, adjustable PLOTS pedestals, and seamless curved studio cyclorama + sun grazing light.
"""

import math
import os
import bmesh
import bpy
from mathutils import Matrix, Vector, geometry as mgeom

MM = 0.001
TEX_DIR = r"d:\C2\textures"


def ensure_collection(name, parent=None):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def link_obj(obj, collection):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)


def apply_metric_box_uv(obj, tile_size_m=0.35):
    """Assigns clean metric world-scale box UVs directly on mesh loops (no mode switching)."""
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv_layer = mesh.uv_layers.active.data
    verts = mesh.vertices
    inv = 1.0 / max(1e-4, tile_size_m)
    for poly in mesh.polygons:
        n = poly.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for li in poly.loop_indices:
            co = verts[mesh.loops[li].vertex_index].co
            if az >= ax and az >= ay:
                u, v = co.x * inv, co.y * inv
            elif ay >= ax and ay >= az:
                u, v = co.x * inv, co.z * inv
            else:
                u, v = co.y * inv, co.z * inv
            uv_layer[li].uv = (u, v)


def finalize_mesh(bm, name, mat, collection, tile_size_m=0.35, bevel_mm=0.0, smooth=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True

    obj = bpy.data.objects.new(name, mesh)
    link_obj(obj, collection)
    if mat is not None:
        mesh.materials.append(mat)
    apply_metric_box_uv(obj, tile_size_m=tile_size_m)

    if bevel_mm > 0.0:
        bev = obj.modifiers.new(name="Bevel", type="BEVEL")
        bev.width = bevel_mm * MM
        bev.segments = 2
        bev.limit_method = "ANGLE"
        bev.angle_limit = math.radians(30.0)
        bev.harden_normals = False
    return obj


# ==============================================================================
# Core Millimetric BMesh Solids
# ==============================================================================
def make_prism_xz(name, poly_xz, y0_mm, y1_mm, mat, col, tile_size_m=0.35, bevel_mm=0.5):
    """Extrudes a 2D closed (x, z) polygon along Y from y0_mm to y1_mm (triangulated if n>4)."""
    if len(poly_xz) > 4:
        return make_extruded_poly_with_holes(name, poly_xz, [], y0_mm, y1_mm, mat, col, tile_size_m=tile_size_m, bevel_mm=bevel_mm)
    bm = bmesh.new()
    y0, y1 = y0_mm * MM, y1_mm * MM
    front = [bm.verts.new((x * MM, y0, z * MM)) for (x, z) in poly_xz]
    back = [bm.verts.new((x * MM, y1, z * MM)) for (x, z) in poly_xz]
    n = len(poly_xz)
    bm.faces.new(list(reversed(front)))
    bm.faces.new(back)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([front[i], front[j], back[j], back[i]])
    return finalize_mesh(bm, name, mat, col, tile_size_m=tile_size_m, bevel_mm=bevel_mm)


def make_box_mm(name, x0, x1, y0, y1, z0, z1, mat, col, tile_size_m=0.35, bevel_mm=0.6):
    return make_prism_xz(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, mat, col, tile_size_m, bevel_mm)


def _add_box_bm(bm, x0, x1, y0, y1, z0, z1):
    xa, xb = x0 * MM, x1 * MM
    ya, yb = y0 * MM, y1 * MM
    za, zb = z0 * MM, z1 * MM
    v0 = bm.verts.new((xa, ya, za))
    v1 = bm.verts.new((xb, ya, za))
    v2 = bm.verts.new((xb, yb, za))
    v3 = bm.verts.new((xa, yb, za))
    v4 = bm.verts.new((xa, ya, zb))
    v5 = bm.verts.new((xb, ya, zb))
    v6 = bm.verts.new((xb, yb, zb))
    v7 = bm.verts.new((xa, yb, zb))
    bm.faces.new([v3, v2, v1, v0])
    bm.faces.new([v4, v5, v6, v7])
    bm.faces.new([v0, v1, v5, v4])
    bm.faces.new([v2, v3, v7, v6])
    bm.faces.new([v1, v2, v6, v5])
    bm.faces.new([v3, v0, v4, v7])


def make_hollow_brick(name, x0, x1, y0, y1, z0, z1, cols, rows, mat, col, tunnel_axis="Y", bevel_mm=0.6):
    """True 3D hollow ceramic brick with realistic thin physical internal shells & tunnels."""
    bm = bmesh.new()
    if tunnel_axis == "Y":
        w, h = x1 - x0, z1 - z0
        wx = min(8.5, max(5.5, w * 0.065))
        wz = min(8.0, max(5.0, h * 0.075))
        cw = (w - (cols + 1) * wx) / cols
        ch = (h - (rows + 1) * wz) / rows
        for ir in range(rows + 1):
            za = z0 + ir * (ch + wz)
            _add_box_bm(bm, x0, x1, y0, y1, za, za + wz)
        for ic in range(cols + 1):
            xa = x0 + ic * (cw + wx)
            for ir in range(rows):
                za = z0 + wz + ir * (ch + wz)
                _add_box_bm(bm, xa, xa + wx, y0, y1, za, za + ch)
    else:
        w, h = y1 - y0, z1 - z0
        wy = min(8.5, max(5.5, w * 0.065))
        wz = min(8.0, max(5.0, h * 0.075))
        cw = (w - (cols + 1) * wy) / cols
        ch = (h - (rows + 1) * wz) / rows
        for ir in range(rows + 1):
            za = z0 + ir * (ch + wz)
            _add_box_bm(bm, x0, x1, y0, y1, za, za + wz)
        for ic in range(cols + 1):
            ya = y0 + ic * (cw + wy)
            for ir in range(rows):
                za = z0 + wz + ir * (ch + wz)
                _add_box_bm(bm, x0, x1, ya, ya + wy, za, za + ch)
    return finalize_mesh(bm, name, mat, col, tile_size_m=0.22, bevel_mm=bevel_mm)


def make_extruded_poly_with_holes(name, outer_xz, holes_xz, y0_mm, y1_mm, mat, col,
                                  tile_size_m=0.22, bevel_mm=0.35):
    """Extrude a 2D X-Z polygon with interior hole tunnels along Y in millimeters."""
    bm = bmesh.new()
    rings = [outer_xz] + list(holes_xz)
    poly_2d = [[Vector((p[0] * MM, p[1] * MM, 0.0)) for p in ring] for ring in rings]
    tris = mgeom.tessellate_polygon(poly_2d)

    v_front_all = []
    v_back_all = []
    ring_pairs = []
    for ring in rings:
        vf = [bm.verts.new((p[0] * MM, y0_mm * MM, p[1] * MM)) for p in ring]
        vb = [bm.verts.new((p[0] * MM, y1_mm * MM, p[1] * MM)) for p in ring]
        v_front_all.extend(vf)
        v_back_all.extend(vb)
        ring_pairs.append((vf, vb))

    for i0, i1, i2 in tris:
        try:
            bm.faces.new([v_front_all[i0], v_front_all[i1], v_front_all[i2]])
            bm.faces.new([v_back_all[i0], v_back_all[i2], v_back_all[i1]])
        except ValueError:
            pass

    for vf, vb in ring_pairs:
        n = len(vf)
        for i in range(n):
            j = (i + 1) % n
            try:
                bm.faces.new([vf[j], vf[i], vb[i], vb[j]])
            except ValueError:
                pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finalize_mesh(bm, name, mat, col, tile_size_m=tile_size_m, bevel_mm=bevel_mm)


def make_bovedilla_ceramica(name, vx_left, vx_right, y0_mm, y1_mm, forj_bot, comp_bot,
                            mat, col, clip_x0=None, clip_x1=None):
    """Build true architectural ceramic bovedilla (tacones + 10 hollow vaults) and return (obj, seno_l, seno_r)."""
    from specs import compute_bovedilla_profile
    outer_pts, holes, seno_l, seno_r = compute_bovedilla_profile(
        vx_left, vx_right, forj_bot, comp_bot, clip_x0=clip_x0, clip_x1=clip_x1
    )
    obj = make_extruded_poly_with_holes(
        name, outer_pts, holes, y0_mm, y1_mm, mat, col, tile_size_m=0.22, bevel_mm=0.35
    )
    return obj, seno_l, seno_r


def make_revolved_profile(name, rz_pts, theta0, theta1, segs, mat, col, tile_size_m=0.25, smooth=True, close_caps=True):
    bm = bmesh.new()
    m = len(rz_pts)
    rings = []
    full_circle = abs((theta1 - theta0) - 2.0 * math.pi) < 1e-4
    steps = segs if full_circle else segs + 1

    for iseg in range(steps):
        th = theta0 + (theta1 - theta0) * (iseg / segs)
        c, s = math.cos(th), math.sin(th)
        rings.append([bm.verts.new((r * MM * c, r * MM * s, z * MM)) for (r, z) in rz_pts])

    num_r = len(rings)
    for ir in range(segs):
        r0 = rings[ir]
        r1 = rings[(ir + 1) % num_r] if full_circle else rings[ir + 1]
        for ip in range(m):
            jp = (ip + 1) % m
            bm.faces.new([r0[ip], r0[jp], r1[jp], r1[ip]])

    if close_caps and not full_circle:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])

    return finalize_mesh(bm, name, mat, col, tile_size_m=tile_size_m, bevel_mm=0.0, smooth=smooth)


def make_annular_box_cutaway(name, r_in_mm, x_out_mm, y_out_mm, z_bot_mm, z_top_mm, mat, col,
                            y_start_mm=0.0, segs=36, tile_size_m=0.35, bevel_mm=0.5):
    bm = bmesh.new()
    outer_pts, inner_pts = [], []
    for i in range(segs + 1):
        th = math.pi * (i / segs)
        c, s = math.cos(th), math.sin(th)
        inner_pts.append((r_in_mm * c, max(y_start_mm, r_in_mm * s)))
        tx = (x_out_mm / abs(c)) if abs(c) > 1e-6 else 1e9
        ty = (y_out_mm / abs(s)) if abs(s) > 1e-6 else 1e9
        t = min(tx, ty)
        outer_pts.append((max(-x_out_mm, min(x_out_mm, t * c)), max(y_start_mm, min(y_out_mm, t * s))))

    v_bot_in = [bm.verts.new((x * MM, y * MM, z_bot_mm * MM)) for (x, y) in inner_pts]
    v_bot_out = [bm.verts.new((x * MM, y * MM, z_bot_mm * MM)) for (x, y) in outer_pts]
    v_top_in = [bm.verts.new((x * MM, y * MM, z_top_mm * MM)) for (x, y) in inner_pts]
    v_top_out = [bm.verts.new((x * MM, y * MM, z_top_mm * MM)) for (x, y) in outer_pts]

    for i in range(segs):
        bm.faces.new([v_top_in[i], v_top_out[i], v_top_out[i + 1], v_top_in[i + 1]])
        bm.faces.new([v_bot_in[i + 1], v_bot_out[i + 1], v_bot_out[i], v_bot_in[i]])
        bm.faces.new([v_bot_in[i], v_top_in[i], v_top_in[i + 1], v_bot_in[i + 1]])
        bm.faces.new([v_bot_out[i + 1], v_top_out[i + 1], v_top_out[i], v_bot_out[i]])

    bm.faces.new([v_bot_in[0], v_bot_out[0], v_top_out[0], v_top_in[0]])
    bm.faces.new([v_bot_out[-1], v_bot_in[-1], v_top_in[-1], v_top_out[-1]])
    return finalize_mesh(bm, name, mat, col, tile_size_m=tile_size_m, bevel_mm=bevel_mm)


def make_square_pit_ring(name, in_hx, in_y0, in_y1, out_hx, out_y0, out_y1, z_bot_fn, z_top_fn,
                         mat, col, tile_size_m=0.35, bevel_mm=0.5):
    bm = bmesh.new()
    rects = [
        (-out_hx, -in_hx, out_y0, in_y1),
        (in_hx, out_hx, out_y0, in_y1),
        (-out_hx, out_hx, in_y1, out_y1),
    ]
    for (xa, xb, ya, yb) in rects:
        if xb <= xa + 0.1 or yb <= ya + 0.1:
            continue
        nx = max(1, int(round((xb - xa) / 140.0)))
        ny = max(1, int(round((yb - ya) / 140.0)))
        xs = [xa + (xb - xa) * i / nx for i in range(nx + 1)]
        ys = [ya + (yb - ya) * j / ny for j in range(ny + 1)]
        grid_b = [[bm.verts.new((x * MM, y * MM, z_bot_fn(x, y) * MM)) for y in ys] for x in xs]
        grid_t = [[bm.verts.new((x * MM, y * MM, z_top_fn(x, y) * MM)) for y in ys] for x in xs]
        for i in range(nx):
            for j in range(ny):
                bm.faces.new([grid_t[i][j], grid_t[i + 1][j], grid_t[i + 1][j + 1], grid_t[i][j + 1]])
                bm.faces.new([grid_b[i][j + 1], grid_b[i + 1][j + 1], grid_b[i + 1][j], grid_b[i][j]])
        for j in range(ny):
            bm.faces.new([grid_b[0][j + 1], grid_b[0][j], grid_t[0][j], grid_t[0][j + 1]])
            bm.faces.new([grid_b[nx][j], grid_b[nx][j + 1], grid_t[nx][j + 1], grid_t[nx][j]])
        for i in range(nx):
            bm.faces.new([grid_b[i][0], grid_b[i + 1][0], grid_t[i + 1][0], grid_t[i][0]])
            bm.faces.new([grid_b[i + 1][ny], grid_b[i][ny], grid_t[i][ny], grid_t[i + 1][ny]])
    return finalize_mesh(bm, name, mat, col, tile_size_m=tile_size_m, bevel_mm=bevel_mm)


def make_square_hollow_curb_cutaway(name, in_hx, out_hx, y_cut, out_hy, z_bot, z_top, cols, rows, mat, col):
    bm = bmesh.new()
    w, h = out_hx - in_hx, z_top - z_bot
    wx, wz = min(8.5, max(5.5, w * 0.065)), min(8.0, max(5.0, h * 0.075))
    cw, ch = (w - (cols + 1) * wx) / cols, (h - (rows + 1) * wz) / rows
    for sx in (-1, 1):
        xa0 = min(sx * in_hx, sx * out_hx)
        for ir in range(rows + 1):
            za = z_bot + ir * (ch + wz)
            _add_box_bm(bm, xa0, xa0 + w, y_cut, out_hy, za, za + wz)
        for ic in range(cols + 1):
            xb0 = xa0 + ic * (cw + wx)
            for ir in range(rows):
                za = z_bot + wz + ir * (ch + wz)
                _add_box_bm(bm, xb0, xb0 + wx, y_cut, out_hy, za, za + ch)
    _add_box_bm(bm, -in_hx, in_hx, in_hx, out_hy, z_bot, z_top)
    return finalize_mesh(bm, name, mat, col, tile_size_m=0.22, bevel_mm=0.5)


# ==============================================================================
# Specialized Pitched-Roof & PLOTS Millimetric BMesh Builders
# ==============================================================================
def make_oriented_box_mm(name, origin_xz, slope_rad, len_u, thick_n, y0_mm, y1_mm, mat, col,
                         u0=0.0, n0=0.0, tile_size_m=0.35, bevel_mm=0.5):
    """Box aligned along slope_rad: origin + u*(cos a, sin a) + n*(-sin a, cos a)."""
    ox, oz = origin_xz
    c, s = math.cos(slope_rad), math.sin(slope_rad)
    ux, uz = c, s
    nx, nz = -s, c
    p0 = (ox + u0 * ux + n0 * nx, oz + u0 * uz + n0 * nz)
    p1 = (p0[0] + len_u * ux, p0[1] + len_u * uz)
    p2 = (p1[0] + thick_n * nx, p1[1] + thick_n * nz)
    p3 = (p0[0] + thick_n * nx, p0[1] + thick_n * nz)
    return make_prism_xz(name, [p0, p1, p2, p3], y0_mm, y1_mm, mat, col, tile_size_m=tile_size_m, bevel_mm=bevel_mm)


def make_teja_curva(name, start_xyz_mm, axis_u_vec, axis_n_vec, length_mm, r_wide, r_narrow,
                    thick_mm, is_cobija, mat, col, arc_deg=156.0, segs_arc=18, segs_len=4):
    """
    True watertight 3D conical barrel roof tile (Teja Curva Ceramica).
    axis_u_vec points UPSLOPE along tile axis; axis_n_vec points UPWARD normal to roof plane.
      - CANAL (is_cobija=False): concave UPWARD, wide mouth UPslope (t=1), narrow mouth DOWNslope (t=0).
      - COBIJA (is_cobija=True): convex UPWARD, wide mouth DOWNslope (t=0), narrow mouth UPslope (t=1).
    """
    bm = bmesh.new()
    u = Vector(axis_u_vec).normalized()
    n = Vector(axis_n_vec).normalized()
    v_lat = n.cross(u).normalized()  # lateral horizontal axis Y

    sx, sy, sz = start_xyz_mm
    base = Vector((sx * MM, sy * MM, sz * MM))

    half_a = math.radians(arc_deg * 0.5)
    rings_out = []
    rings_in = []

    for il in range(segs_len + 1):
        t = il / segs_len
        dist_m = t * length_mm * MM
        if is_cobija:
            r_mid = (r_wide * (1.0 - t) + r_narrow * t) * MM
            # Slight downward drop at wide lip so underside clears cleanly when telescoping
            drop_z = 0.0
        else:
            r_mid = (r_narrow * (1.0 - t) + r_wide * t) * MM
            drop_z = 0.0
        ro = r_mid + 0.5 * thick_mm * MM
        ri = max(0.015, r_mid - 0.5 * thick_mm * MM)

        ring_o, ring_i = [], []
        for ia in range(segs_arc + 1):
            # Parameterize arc around lateral vector:
            # Canal: bottom is -n; Cobija: crest is +n
            ang = -half_a + (2.0 * half_a) * (ia / segs_arc)
            rad_dir = (math.sin(ang) * v_lat + math.cos(ang) * n) if is_cobija else (math.sin(ang) * v_lat - math.cos(ang) * n)
            # Lift canal center by r_wide*0.92 or keep origin consistent around tile trough axis
            center = base + u * dist_m + n * (drop_z * MM)
            ring_o.append(bm.verts.new(center + rad_dir * ro))
            ring_i.append(bm.verts.new(center + rad_dir * ri))
        rings_out.append(ring_o)
        rings_in.append(ring_i)

    # Side longitudinal outer, inner & bottom/crest thickness strips
    for il in range(segs_len):
        ro0, ro1 = rings_out[il], rings_out[il + 1]
        ri0, ri1 = rings_in[il], rings_in[il + 1]
        for ia in range(segs_arc):
            bm.faces.new([ro0[ia], ro0[ia + 1], ro1[ia + 1], ro1[ia]])
            bm.faces.new([ri0[ia + 1], ri0[ia], ri1[ia], ri1[ia + 1]])
        # Two lateral long edges (ia=0 and ia=segs_arc)
        bm.faces.new([ri0[0], ro0[0], ro1[0], ri1[0]])
        bm.faces.new([ro0[-1], ri0[-1], ri1[-1], ro1[-1]])

    # End crescents (t=0 and t=1)
    for ia in range(segs_arc):
        bm.faces.new([rings_in[0][ia], rings_in[0][ia + 1], rings_out[0][ia + 1], rings_out[0][ia]])
        bm.faces.new([rings_out[-1][ia], rings_out[-1][ia + 1], rings_in[-1][ia + 1], rings_in[-1][ia]])

    return finalize_mesh(bm, name, mat, col, tile_size_m=0.28, bevel_mm=0.0, smooth=True)


def make_teja_mixta(name, origin_xyz_mm, slope_rad, tile_l, tile_w, wave_h, thick, mat, col):
    """
    Authentic Spanish Mixed Tile (Teja Mixta):
    Left half (Y: 0..0.52*w) flat interlocking pan + Right half (Y: 0.52*w..w) rounded barrel wave + rear tacones.
    """
    bm = bmesh.new()
    c, s = math.cos(slope_rad), math.sin(slope_rad)
    u = Vector((c, 0.0, s))
    n = Vector((-s, 0.0, c))
    v = Vector((0.0, 1.0, 0.0))
    ox, oy, oz = origin_xyz_mm
    base = Vector((ox * MM, oy * MM, oz * MM))

    # Cross-section profile points (y_local_mm, z_local_mm) on upper surface -> offset by thick down
    ys = [0.0, 18.0, 26.0, 118.0, 132.0, 146.0, 166.0, 190.0, 214.0, 236.0, tile_w - 8.0, tile_w]
    zs = [12.0, 12.0, 4.0, 4.0, 20.0, 34.0, wave_h, wave_h, 34.0, 18.0, 4.0, 4.0]
    m = len(ys)

    def make_section(x_dist_mm):
        up_v, dn_v = [], []
        off = u * (x_dist_mm * MM)
        for yl, zl in zip(ys, zs):
            p_up = base + off + v * (yl * MM) + n * (zl * MM)
            p_dn = base + off + v * (yl * MM) + n * ((zl - thick) * MM)
            up_v.append(bm.verts.new(p_up))
            dn_v.append(bm.verts.new(p_dn))
        return up_v, dn_v

    u0, d0 = make_section(0.0)
    u1, d1 = make_section(tile_l)
    for i in range(m - 1):
        bm.faces.new([u0[i], u0[i + 1], u1[i + 1], u1[i]])
        bm.faces.new([d0[i + 1], d0[i], d1[i], d1[i + 1]])
        bm.faces.new([d0[i], d0[i + 1], u0[i + 1], u0[i]])
        bm.faces.new([u1[i], u1[i + 1], d1[i + 1], d1[i]])
    bm.faces.new([d0[0], u0[0], u1[0], d1[0]])
    bm.faces.new([u0[-1], d0[-1], d1[-1], u1[-1]])

    # Two locking lugs (tacones) at top underside (x_dist = tile_l - 42..tile_l - 12)
    for ly0, ly1 in ((40.0, 95.0), (165.0, 215.0)):
        b0 = base + u * ((tile_l - 42.0) * MM) + v * (ly0 * MM)
        # small box below pan
        for dx0, dx1, nz0, nz1 in ((0.0, 30.0, -14.0, 4.0),):
            p = [
                b0 + n * (nz0 * MM),
                b0 + u * (dx1 * MM) + n * (nz0 * MM),
                b0 + u * (dx1 * MM) + v * ((ly1 - ly0) * MM) + n * (nz0 * MM),
                b0 + v * ((ly1 - ly0) * MM) + n * (nz0 * MM),
                b0 + n * (nz1 * MM),
                b0 + u * (dx1 * MM) + n * (nz1 * MM),
                b0 + u * (dx1 * MM) + v * ((ly1 - ly0) * MM) + n * (nz1 * MM),
                b0 + v * ((ly1 - ly0) * MM) + n * (nz1 * MM),
            ]
            vs = [bm.verts.new(pt) for pt in p]
            bm.faces.new([vs[3], vs[2], vs[1], vs[0]])
            bm.faces.new([vs[4], vs[5], vs[6], vs[7]])
            bm.faces.new([vs[0], vs[1], vs[5], vs[4]])
            bm.faces.new([vs[2], vs[3], vs[7], vs[6]])
            bm.faces.new([vs[1], vs[2], vs[6], vs[5]])
            bm.faces.new([vs[3], vs[0], vs[4], vs[7]])

    return finalize_mesh(bm, name, mat, col, tile_size_m=0.30, bevel_mm=0.4, smooth=False)


def make_standing_seam_tray(name, x0, x1, slope_rad, z_base_x0, y_center, pan_w, seam_h, thick,
                            mat, col, turnup_x1_h=0.0):
    """
    VMZ Titanium Zinc standing seam tray: flat pan + double-lock upright standing seam ribs (H=25 mm)
    along +/-pan_w/2 edges, plus optional vertical upturn against parapet.
    """
    bm = bmesh.new()
    c, s = math.cos(slope_rad), math.sin(slope_rad)
    dx = x1 - x0
    L = dx / c
    u = Vector((c, 0.0, s))
    n = Vector((-s, 0.0, c))
    v = Vector((0.0, 1.0, 0.0))
    base = Vector((x0 * MM, y_center * MM, z_base_x0 * MM))

    hp = 0.5 * pan_w
    # Cross section polyline extruded along slope:
    # Left rib -> left fold -> flat pan -> right fold -> right cap
    pts_yn = [
        (-hp, seam_h), (-hp + 5.0, seam_h), (-hp + 5.0, 0.0),
        (hp - 5.0, 0.0), (hp - 5.0, seam_h), (hp, seam_h),
        (hp, thick), (-hp, thick),
    ]
    # Better: build outer pan + left upright fold + right upright fold cleanly as 3 connected manifold blocks
    # 1. Flat pan from (-hp+4 .. +hp-4), height 0..thick
    p_pan_0 = base + v * ((-hp + 4.0) * MM)
    _add_oriented_subbox(bm, base, u, v, n, 0.0, L, -hp, hp, 0.0, thick)
    # 2. Left standing seam folded rib (double thickness 4.5 mm, H=seam_h)
    _add_oriented_subbox(bm, base, u, v, n, 0.0, L, -hp, -hp + 5.5, 0.0, seam_h)
    _add_oriented_subbox(bm, base, u, v, n, 0.0, L, -hp - 1.5, -hp + 7.5, seam_h - 6.0, seam_h + 2.0)
    # 3. Right standing seam folded rib
    _add_oriented_subbox(bm, base, u, v, n, 0.0, L, hp - 5.5, hp, 0.0, seam_h)
    _add_oriented_subbox(bm, base, u, v, n, 0.0, L, hp - 7.5, hp + 1.5, seam_h - 6.0, seam_h + 2.0)

    if turnup_x1_h > 0.0:
        z_x1 = z_base_x0 + dx * math.tan(slope_rad)
        _add_box_bm(bm, x1 - 4.0, x1, y_center - hp, y_center + hp, z_x1, z_x1 + turnup_x1_h)

    return finalize_mesh(bm, name, mat, col, tile_size_m=0.45, bevel_mm=0.35, smooth=False)


def _add_oriented_subbox(bm, base, u, v, n, u0, u1, v0, v1, n0, n1):
    corners = [
        base + u * (u0 * MM) + v * (v0 * MM) + n * (n0 * MM),
        base + u * (u1 * MM) + v * (v0 * MM) + n * (n0 * MM),
        base + u * (u1 * MM) + v * (v1 * MM) + n * (n0 * MM),
        base + u * (u0 * MM) + v * (v1 * MM) + n * (n0 * MM),
        base + u * (u0 * MM) + v * (v0 * MM) + n * (n1 * MM),
        base + u * (u1 * MM) + v * (v0 * MM) + n * (n1 * MM),
        base + u * (u1 * MM) + v * (v1 * MM) + n * (n1 * MM),
        base + u * (u0 * MM) + v * (v1 * MM) + n * (n1 * MM),
    ]
    vs = [bm.verts.new(p) for p in corners]
    bm.faces.new([vs[3], vs[2], vs[1], vs[0]])
    bm.faces.new([vs[4], vs[5], vs[6], vs[7]])
    bm.faces.new([vs[0], vs[1], vs[5], vs[4]])
    bm.faces.new([vs[2], vs[3], vs[7], vs[6]])
    bm.faces.new([vs[1], vs[2], vs[6], vs[5]])
    bm.faces.new([vs[3], vs[0], vs[4], vs[7]])


def make_semicircular_gutter(name, cx_mm, cz_mm, radius_mm, thick_mm, y0_mm, y1_mm, mat, col, segs=24):
    """Rolled-lip semicircular Zinc gutter extruded along Y."""
    pts = []
    for i in range(segs + 1):
        a = math.radians(180.0 + 180.0 * (i / segs))
        pts.append((cx_mm + radius_mm * math.cos(a), cz_mm + radius_mm * math.sin(a)))
    for i in range(segs, -1, -1):
        a = math.radians(180.0 + 180.0 * (i / segs))
        pts.append((cx_mm + (radius_mm - thick_mm) * math.cos(a), cz_mm + (radius_mm - thick_mm) * math.sin(a)))
    return make_prism_xz(name, pts, y0_mm, y1_mm, mat, col, tile_size_m=0.25, bevel_mm=0.3)


def make_adjustable_plot(name, cx_mm, cy_mm, z_bot_mm, z_top_mm, mat, col):
    """Detailed adjustable polypropylene PLOTS pedestal (flanged base, threaded shaft, load head, 4 mm crucetas)."""
    bm = bmesh.new()
    segs = 20
    # Lathe parts: base flange (r=90, h=8), shaft (r=28..28, h=8..H-10), adjustment collar (r=38), head (r=70, h=8)
    h_tot = max(45.0, z_top_mm - z_bot_mm)
    rz_parts = [
        (0.0, z_bot_mm), (90.0, z_bot_mm), (90.0, z_bot_mm + 6.0), (52.0, z_bot_mm + 12.0),
        (28.0, z_bot_mm + 14.0), (28.0, z_bot_mm + 0.42 * h_tot),
        (39.0, z_bot_mm + 0.44 * h_tot), (39.0, z_bot_mm + 0.56 * h_tot),
        (26.0, z_bot_mm + 0.58 * h_tot), (26.0, z_top_mm - 9.0),
        (68.0, z_top_mm - 7.0), (68.0, z_top_mm), (0.0, z_top_mm),
    ]
    rings = []
    for iseg in range(segs):
        th = 2.0 * math.pi * (iseg / segs)
        c, s = math.cos(th), math.sin(th)
        rings.append([bm.verts.new(((cx_mm + r * c) * MM, (cy_mm + r * s) * MM, z * MM)) for (r, z) in rz_parts])
    for ir in range(segs):
        r0 = rings[ir]
        r1 = rings[(ir + 1) % segs]
        for ip in range(len(rz_parts) - 1):
            bm.faces.new([r0[ip], r0[ip + 1], r1[ip + 1], r1[ip]])
    # Crucetas separadoras superiores (4 mm espesor x 14 mm alto x 50 mm largo)
    _add_box_bm(bm, cx_mm - 2.0, cx_mm + 2.0, cy_mm - 38.0, cy_mm + 38.0, z_top_mm, z_top_mm + 14.0)
    _add_box_bm(bm, cx_mm - 38.0, cx_mm + 38.0, cy_mm - 2.0, cy_mm + 2.0, z_top_mm, z_top_mm + 14.0)
    return finalize_mesh(bm, name, mat, col, tile_size_m=0.25, bevel_mm=0.0, smooth=True)


# ==============================================================================
# PBR Material Factory (1024x1024 HD maps + Multi-Tone Variant Shaders)
# ==============================================================================
def get_pbr_material(mat_name, tex_prefix, tint=(1.0, 1.0, 1.0), metallic=0.0, rough_mult=1.0,
                     normal_str=1.15, clearcoat=0.0, ior=1.50, spec_level=0.50):
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["IOR"].default_value = ior
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec_level
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    alb_path = os.path.join(TEX_DIR, f"{tex_prefix}_albedo.png")
    rgh_path = os.path.join(TEX_DIR, f"{tex_prefix}_rough.png")
    nrm_path = os.path.join(TEX_DIR, f"{tex_prefix}_normal.png")

    if os.path.exists(alb_path):
        img_a = bpy.data.images.load(alb_path, check_existing=True)
        tex_a = nt.nodes.new("ShaderNodeTexImage")
        tex_a.image = img_a
        nt.links.new(tex_coord.outputs["UV"], tex_a.inputs["Vector"])
        if tint != (1.0, 1.0, 1.0):
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs["B"].default_value = (*tint, 1.0)
            nt.links.new(tex_a.outputs["Color"], mix.inputs["A"])
            nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        else:
            nt.links.new(tex_a.outputs["Color"], bsdf.inputs["Base Color"])

    if os.path.exists(rgh_path):
        img_r = bpy.data.images.load(rgh_path, check_existing=True)
        img_r.colorspace_settings.name = "Non-Color"
        tex_r = nt.nodes.new("ShaderNodeTexImage")
        tex_r.image = img_r
        nt.links.new(tex_coord.outputs["UV"], tex_r.inputs["Vector"])
        if abs(rough_mult - 1.0) > 1e-3:
            math_n = nt.nodes.new("ShaderNodeMath")
            math_n.operation = "MULTIPLY"
            math_n.use_clamp = True
            math_n.inputs[1].default_value = rough_mult
            nt.links.new(tex_r.outputs["Color"], math_n.inputs[0])
            nt.links.new(math_n.outputs["Value"], bsdf.inputs["Roughness"])
        else:
            nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])

    if os.path.exists(nrm_path):
        img_n = bpy.data.images.load(nrm_path, check_existing=True)
        img_n.colorspace_settings.name = "Non-Color"
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = img_n
        nt.links.new(tex_coord.outputs["UV"], tex_n.inputs["Vector"])
        nrm = nt.nodes.new("ShaderNodeNormalMap")
        nrm.inputs["Strength"].default_value = normal_str
        nt.links.new(tex_n.outputs["Color"], nrm.inputs["Color"])
        nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def get_solid_material(mat_name, rgba, rough=0.45, metallic=0.0, transmission=0.0, ior=1.45):
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["IOR"].default_value = ior
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    return mat


def get_material_palette():
    pal = {
        "rasilla": get_pbr_material("Mat_Rasilla_Aspe", "terracotta", tint=(1.0, 0.98, 0.95), rough_mult=0.90, normal_str=1.10),
        "rasilla_alt": get_pbr_material("Mat_Rasilla_Var", "terracotta", tint=(0.90, 0.86, 0.83), rough_mult=0.95, normal_str=1.10),
        "brick": get_pbr_material("Mat_Ladrillo_Hueco", "brick_clay", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.15),
        "brick_alt": get_pbr_material("Mat_Ladrillo_Pal", "brick_clay", tint=(0.93, 0.89, 0.86), rough_mult=1.0, normal_str=1.15),
        "cellular": get_pbr_material("Mat_Hormigon_Celular", "cellular_concrete", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.35),
        "light_conc": get_pbr_material("Mat_Hormigon_Aligerado", "lightweight_concrete", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.25),
        "concrete": get_pbr_material("Mat_Forjado_HA25", "structural_concrete", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.10),
        "mortar": get_pbr_material("Mat_Mortero_1_6", "mortar", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.20),
        "mortar_dark": get_pbr_material("Mat_Mortero_1_8", "mortar", tint=(0.86, 0.84, 0.80), rough_mult=1.02, normal_str=1.25),
        "bitumen": get_pbr_material("Mat_Membrana_Bitumen", "bitumen", tint=(1.0, 1.0, 1.0), rough_mult=0.82, normal_str=1.15, clearcoat=0.18),
        "granule": get_pbr_material("Mat_Membrana_Granulo", "membrane_granule", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.35),
        "vapor": get_pbr_material("Mat_Barrera_Vapor", "bitumen", tint=(1.15, 1.15, 1.22), rough_mult=0.92, normal_str=0.80),
        "geotextile": get_pbr_material("Mat_Capa_Separadora_CS", "geotextile", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=0.95),
        "lamina_trans": get_pbr_material("Mat_Lamina_Transpirable", "geotextile", tint=(0.45, 0.68, 0.88), rough_mult=0.88, normal_str=0.85),
        "xps": get_pbr_material("Mat_Aislamiento_XPS", "xps_foam", tint=(1.0, 1.0, 1.0), rough_mult=0.94, normal_str=0.85),
        "fiberglass": get_pbr_material("Mat_Fibra_Vidrio", "fiberglass", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.35),
        "stainless": get_pbr_material("Mat_Acero_Inox", "brushed_metal", tint=(1.0, 1.0, 1.0), metallic=0.95, rough_mult=0.72, normal_str=0.55),
        "cast_iron": get_pbr_material("Mat_Fundicion_Rejilla", "brushed_metal", tint=(0.42, 0.45, 0.49), metallic=0.90, rough_mult=1.12, normal_str=0.80),
        "zinc": get_pbr_material("Mat_Cinc_Canalon", "zinc", tint=(0.76, 0.82, 0.88), metallic=0.88, rough_mult=0.78, normal_str=0.55),
        "zinc_vmz": get_pbr_material("Mat_Zinc_VMZ_Quartz", "zinc_vmz", tint=(0.95, 0.98, 1.02), metallic=0.90, rough_mult=0.76, normal_str=0.65),
        "render": get_pbr_material("Mat_Enfoscado_Peto", "render", tint=(1.0, 1.0, 1.0), rough_mult=1.0, normal_str=1.05),
        "revest": get_pbr_material("Mat_Revestimiento_Yeso", "render", tint=(0.98, 0.95, 0.91), rough_mult=0.94, normal_str=0.70),
        "stone": get_pbr_material("Mat_Piedra_Artificial", "artificial_stone", tint=(1.0, 1.0, 1.0), rough_mult=0.95, normal_str=1.15),
        "paver": get_pbr_material("Mat_Losa_Armada", "concrete_paver", tint=(1.0, 1.0, 1.0), rough_mult=0.92, normal_str=1.20),
        "wood": get_pbr_material("Mat_Madera_Pino", "wood_pine", tint=(1.0, 1.0, 1.0), rough_mult=0.92, normal_str=1.10),
        "wood_dark": get_pbr_material("Mat_Madera_Tratada", "wood_pine", tint=(0.82, 0.78, 0.70), rough_mult=0.96, normal_str=1.10),
        "butyl": get_solid_material("Mat_Banda_Butilo", (0.20, 0.21, 0.23, 1.0), rough=0.45, metallic=0.35),
        "pp_plot": get_solid_material("Mat_Polipropileno_Plot", (0.14, 0.16, 0.19, 1.0), rough=0.48, metallic=0.0),
        "pvc": get_solid_material("Mat_PVC_Bajante", (0.44, 0.48, 0.52, 1.0), rough=0.32, metallic=0.0),
        "eps": get_solid_material("Mat_Junta_EPS", (0.94, 0.94, 0.92, 1.0), rough=0.78, metallic=0.0),
        "elastomer": get_solid_material("Mat_Junta_Elastica", (0.14, 0.15, 0.17, 1.0), rough=0.52, metallic=0.0),
        "rebar": get_solid_material("Mat_Acero_Armadura", (0.28, 0.29, 0.31, 1.0), rough=0.40, metallic=0.90),
        "water": get_solid_material("Mat_Agua_Sifon", (0.68, 0.91, 0.99, 1.0), rough=0.03, metallic=0.0, transmission=0.94, ior=1.333),
    }
    # Natural multi-tone kiln/quarry variants (100% glTF compliant!)
    teja_tints = [
        (1.00, 0.98, 0.95),
        (0.92, 0.84, 0.78),
        (1.05, 1.04, 0.92),  # warmer ochre-terracotta
        (0.84, 0.74, 0.70),  # toasted deep clay
        (0.96, 0.92, 0.85),
    ]
    pal["teja_vars"] = [
        get_pbr_material(f"Mat_Teja_Curva_V{i}", "teja_curva", tint=t, rough_mult=0.92 + 0.04 * (i % 3), normal_str=1.25)
        for i, t in enumerate(teja_tints)
    ]
    mixta_tints = [(1.0, 0.98, 0.96), (0.93, 0.89, 0.86), (1.03, 0.95, 0.90)]
    pal["mixta_vars"] = [
        get_pbr_material(f"Mat_Teja_Mixta_V{i}", "teja_mixta", tint=t, rough_mult=0.90, normal_str=1.10, clearcoat=0.06)
        for i, t in enumerate(mixta_tints)
    ]
    slate_tints = [(1.0, 1.0, 1.0), (0.88, 0.90, 0.94), (1.06, 1.05, 1.03), (0.94, 0.96, 0.99)]
    pal["slate_vars"] = [
        get_pbr_material(f"Mat_Pizarra_Nat_V{i}", "slate_pizarra", tint=t, rough_mult=0.78 + 0.05 * (i % 2), normal_str=0.42, spec_level=0.55)
        for i, t in enumerate(slate_tints)
    ]
    return pal


# ==============================================================================
# Seamless Curved Cyclorama & Architectural Sun+Softbox Cycles HIP Studio Rig
# ==============================================================================
def setup_studio_environment(scene, floor_z_mm=-620.0, center_xy_mm=(0.0, 0.0), scale_diag_m=2.0):
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "HIP"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type == "HIP")
    scene.cycles.device = "GPU"
    scene.cycles.samples = 192
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 8

    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = 0.08

    # Soft studio sky gradient world
    world = scene.world or bpy.data.worlds.new("StudioWorld")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.82, 0.85, 0.90, 1.0)
    bg.inputs["Strength"].default_value = 0.45
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    col = ensure_collection("StudioRig")
    cx, cy = center_xy_mm[0] * MM, center_xy_mm[1] * MM
    fz = floor_z_mm * MM - 0.004

    # Seamless curved infinity cyclorama (floor -> smooth fillet curve -> rear backdrop) -> ZERO corner seam!
    bm = bmesh.new()
    s = scale_diag_m * 4.5
    R = s * 0.90
    y_curve_start = cy + s * 0.55
    profile_yz = [(cy - s * 2.5, fz), (y_curve_start, fz)]
    n_arc = 16
    for k in range(1, n_arc + 1):
        a = -0.5 * math.pi + 0.5 * math.pi * (k / n_arc)
        profile_yz.append((y_curve_start + R * math.cos(a), fz + R + R * math.sin(a)))
    profile_yz.append((y_curve_start + R, fz + R + s * 2.5))

    x_left, x_right = cx - s * 2.5, cx + s * 2.5
    row_l = [bm.verts.new((x_left, y, z)) for (y, z) in profile_yz]
    row_r = [bm.verts.new((x_right, y, z)) for (y, z) in profile_yz]
    for i in range(len(profile_yz) - 1):
        bm.faces.new([row_l[i], row_r[i], row_r[i + 1], row_l[i + 1]])

    floor_mat = get_solid_material("Studio_Cyclorama", (0.91, 0.90, 0.88, 1.0), rough=0.92)
    cyc_obj = finalize_mesh(bm, "Studio_Backdrop_Floor", floor_mat, col, smooth=True)
    cyc_obj.visible_shadow = True

    def add_area(name, loc, target, energy, size, color):
        ldata = bpy.data.lights.new(name=name, type="AREA")
        ldata.energy = energy
        ldata.size = size
        ldata.color = color
        lobj = bpy.data.objects.new(name, ldata)
        link_obj(lobj, col)
        lobj.location = loc
        direction = Vector(target) - Vector(loc)
        lobj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    tgt = (cx, cy, fz + scale_diag_m * 0.25)
    # Warm grazing sun key (sculpts every tile arch, mortar joint, bevel & metal crease)
    sun_data = bpy.data.lights.new(name="Sun_Key", type="SUN")
    sun_data.energy = 2.6
    sun_data.angle = math.radians(3.2)
    sun_data.color = (1.0, 0.95, 0.88)
    sun_obj = bpy.data.objects.new("Sun_Key", sun_data)
    link_obj(sun_obj, col)
    sun_loc = Vector((cx - 2.6 * scale_diag_m, cy - 2.4 * scale_diag_m, fz + 2.7 * scale_diag_m))
    sun_obj.location = sun_loc
    sun_obj.rotation_euler = (Vector(tgt) - sun_loc).to_track_quat("-Z", "Y").to_euler()

    # Large diffused front-left studio softbox
    add_area("Key_Light", (cx - 2.2 * scale_diag_m, cy - 2.6 * scale_diag_m, fz + 2.8 * scale_diag_m),
             tgt, energy=260.0 * (scale_diag_m ** 1.4), size=2.6 * scale_diag_m, color=(1.0, 0.97, 0.93))
    # Cool skylight fill (front-right)
    add_area("Fill_Light", (cx + 2.6 * scale_diag_m, cy - 1.8 * scale_diag_m, fz + 1.8 * scale_diag_m),
             tgt, energy=145.0 * (scale_diag_m ** 1.4), size=3.0 * scale_diag_m, color=(0.85, 0.92, 1.0))
    # Back rim accent for bevel & metal edges
    add_area("Rim_Light", (cx + 0.5 * scale_diag_m, cy + 2.2 * scale_diag_m, fz + 2.1 * scale_diag_m),
             tgt, energy=180.0 * (scale_diag_m ** 1.4), size=2.0 * scale_diag_m, color=(1.0, 0.99, 0.97))


def render_camera_shot(scene, cam_name, loc_mm, target_mm, out_path, lens_mm=58.0,
                       ortho_scale_m=None, res_x=1920, res_y=1280, dof_fstop=8.0):
    col = ensure_collection("StudioRig")
    cdata = bpy.data.cameras.new(cam_name)
    if ortho_scale_m is not None:
        cdata.type = "ORTHO"
        cdata.ortho_scale = ortho_scale_m
    else:
        cdata.type = "PERSP"
        cdata.lens = lens_mm
    cdata.clip_start = 0.01
    cdata.clip_end = 100.0

    loc = Vector((loc_mm[0] * MM, loc_mm[1] * MM, loc_mm[2] * MM))
    tgt = Vector((target_mm[0] * MM, target_mm[1] * MM, target_mm[2] * MM))
    if dof_fstop is not None and ortho_scale_m is None:
        cdata.dof.use_dof = True
        cdata.dof.focus_distance = (tgt - loc).length
        cdata.dof.aperture_fstop = dof_fstop

    cobj = bpy.data.objects.new(cam_name, cdata)
    link_obj(cobj, col)
    cobj.location = loc
    cobj.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()

    scene.camera = cobj
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Cycles shot: {out_path}")
