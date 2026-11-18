r"""
Unified Exact Millimetric 2D CAD Engine (Model-Space mm -> DXF + Vector PDF + Vector SVG)
Upgraded Architectural Editorial Pen Hierarchy, Hatch Primitives, Break Lines & A3 Cajetin.
"""

import math
import os
import xml.sax.saxutils as sax
import ezdxf
import pymupdf


# Layer visual & CAD metadata (ACI color index, hex RGB for PDF/SVG, lineweight in mm)
LAYER_STYLES = {
    "FRAME": {"aci": 7, "hex": "#14191F", "lw": 0.35},
    "TITLE_BLOCK": {"aci": 7, "hex": "#14191F", "lw": 0.22},
    "CORTE": {"aci": 7, "hex": "#12161B", "lw": 0.52},
    "FORJADO": {"aci": 8, "hex": "#252B33", "lw": 0.44},
    "LADRILLO": {"aci": 30, "hex": "#7D3522", "lw": 0.32},
    "TEJA": {"aci": 12, "hex": "#8F2F1B", "lw": 0.36},
    "PIZARRA": {"aci": 250, "hex": "#242A34", "lw": 0.34},
    "MADERA": {"aci": 40, "hex": "#754E1E", "lw": 0.30},
    "ZINC": {"aci": 141, "hex": "#30495E", "lw": 0.36},
    "HORMIGON_CEL": {"aci": 9, "hex": "#4A4E54", "lw": 0.28},
    "MORTERO": {"aci": 252, "hex": "#5E5850", "lw": 0.22},
    "AISLAMIENTO": {"aci": 2, "hex": "#A8810A", "lw": 0.26},
    "MEMBRANA": {"aci": 7, "hex": "#101214", "lw": 0.52},
    "CAPA_SEP": {"aci": 4, "hex": "#24749C", "lw": 0.26},
    "PAVIMENTO": {"aci": 10, "hex": "#963420", "lw": 0.36},
    "METAL_CAZ": {"aci": 5, "hex": "#233F54", "lw": 0.34},
    "FONTANERIA": {"aci": 140, "hex": "#35526B", "lw": 0.34},
    "AGUA_FLUJO": {"aci": 150, "hex": "#0B72B9", "lw": 0.30},
    "VENT_FLUJO": {"aci": 130, "hex": "#1985A1", "lw": 0.28},
    "ROTURA": {"aci": 8, "hex": "#4E5761", "lw": 0.20},
    "REVESTIMIENTO": {"aci": 1, "hex": "#942820", "lw": 0.24},
    "HATCH_LIGHT": {"aci": 253, "hex": "#757C85", "lw": 0.10},
    "HATCH_BRICK": {"aci": 32, "hex": "#AC5E48", "lw": 0.10},
    "HATCH_INSUL": {"aci": 42, "hex": "#BA8418", "lw": 0.14},
    "HATCH_WOOD": {"aci": 42, "hex": "#9C6E34", "lw": 0.12},
    "HATCH_SLATE": {"aci": 252, "hex": "#46505E", "lw": 0.09},
    "HATCH_REV": {"aci": 12, "hex": "#B5453C", "lw": 0.11},
    "COTAS": {"aci": 3, "hex": "#165C3A", "lw": 0.14},
    "CALLOUTS": {"aci": 7, "hex": "#161D24", "lw": 0.17},
    "NOTES": {"aci": 8, "hex": "#4C5663", "lw": 0.16},
}


VALID_DXF_LW = (0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80, 90, 100, 106, 120, 140, 158, 200, 211)


def snap_dxf_lw(lw_mm):
    target = int(round(lw_mm * 100))
    return min(VALID_DXF_LW, key=lambda v: abs(v - target))


def hex_to_rgb01(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


class SheetCanvas2D:
    """
    Collects exact model-space millimeter geometry (x, z) and sheet-space annotations,
    then writes AutoCAD DXF (1:1 in mm), Vector PDF (A3 420x297 mm @ scale), and Vector SVG.
    """

    def __init__(self, detail_meta, scale_denom=5.0, origin_sheet=(165.0, 128.0)):
        self.meta = detail_meta
        self.scale = scale_denom  # 5.0 -> Escala 1:5
        self.ox, self.oy = origin_sheet
        self.sheet_w = 420.0
        self.sheet_h = 297.0

        self.polys = []       # (layer, pts, closed, fill_hex, stroke_hex, lw_mm, dash)
        self.lines = []       # (layer, x1, y1, x2, y2, color_hex, lw_mm, dash)
        self.circles = []     # (layer, cx, cy, r, fill_hex, stroke_hex, lw_mm)
        self.texts = []       # (layer, x, y, text, size_mm, color_hex, align, angle)
        self.arrows = []      # (layer, pts, color_hex, lw_mm, head_mm, dash)
        self.hatches = []     # (layer, kind, polygon, spacing_mm, color_hex, angle_deg)

    def m2s(self, x_mm, z_mm):
        return (self.ox + x_mm / self.scale, self.oy + z_mm / self.scale)

    # --- Model-space geometry emitters (exact mm) ---
    def add_poly(self, layer, pts, closed=True, fill_hex=None, stroke_hex=None, lw=None, dash=None):
        st = LAYER_STYLES.get(layer, LAYER_STYLES["FRAME"])
        self.polys.append((
            layer, list(pts), closed, fill_hex,
            stroke_hex if stroke_hex is not None else st["hex"],
            lw if lw is not None else st["lw"], dash
        ))

    def add_rect(self, layer, x0, z0, x1, z1, fill_hex=None, stroke_hex=None, lw=None, dash=None):
        pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        self.add_poly(layer, pts, True, fill_hex, stroke_hex, lw, dash)

    def add_line(self, layer, x0, z0, x1, z1, color_hex=None, lw=None, dash=None):
        st = LAYER_STYLES.get(layer, LAYER_STYLES["FRAME"])
        self.lines.append((
            layer, x0, z0, x1, z1, color_hex or st["hex"],
            lw if lw is not None else st["lw"], dash
        ))

    def add_circle(self, layer, cx, cz, r, fill_hex=None, stroke_hex=None, lw=None):
        st = LAYER_STYLES.get(layer, LAYER_STYLES["FRAME"])
        self.circles.append((
            layer, cx, cz, r, fill_hex, stroke_hex if stroke_hex is not None else st["hex"],
            lw if lw is not None else st["lw"]
        ))

    def add_hatch(self, layer, kind, poly_pts, spacing=12.0, color_hex=None, angle_deg=0.0):
        """
        kind: 'diag45', 'diag135', 'cross', 'horiz_masonry', 'concrete',
              'cellular', 'dots', 'zigzag_v', 'batt_insul', 'wood_cut',
              'wood_grain', 'slate_layers'
        """
        st = LAYER_STYLES.get(layer, LAYER_STYLES["HATCH_LIGHT"])
        self.hatches.append((layer, kind, list(poly_pts), spacing, color_hex or st["hex"], angle_deg))

    def add_text(self, layer, x, z, text, height_sheet_mm=2.4, color_hex=None, align="left", angle=0.0):
        st = LAYER_STYLES.get(layer, LAYER_STYLES["CALLOUTS"])
        self.texts.append((layer, x, z, text, height_sheet_mm, color_hex or st["hex"], align, angle))

    def add_breakline(self, x0, z0, x1, z1, amp=10.0, over_ext=16.0):
        """Draws a crisp architectural zig-zag break line along segment (x0,z0)->(x1,z1)."""
        dx, dz = x1 - x0, z1 - z0
        L = math.hypot(dx, dz)
        if L < 1e-3:
            return
        ux, uz = dx / L, dz / L
        nx, nz = -uz, ux
        mid_x, mid_z = 0.5 * (x0 + x1), 0.5 * (z0 + z1)
        z_span = min(32.0, L * 0.35)
        p_start = (x0 - ux * over_ext, z0 - uz * over_ext)
        p_b1 = (mid_x - ux * (z_span * 0.5), mid_z - uz * (z_span * 0.5))
        p_pk1 = (mid_x - ux * (z_span * 0.16) + nx * amp, mid_z - uz * (z_span * 0.16) + nz * amp)
        p_pk2 = (mid_x + ux * (z_span * 0.16) - nx * amp, mid_z + uz * (z_span * 0.16) - nz * amp)
        p_b2 = (mid_x + ux * (z_span * 0.5), mid_z + uz * (z_span * 0.5))
        p_end = (x1 + ux * over_ext, z1 + uz * over_ext)
        self.add_poly("ROTURA", [p_start, p_b1, p_pk1, p_pk2, p_b2, p_end], closed=False, fill_hex=None, stroke_hex="#46505A", lw=0.22)

    def add_slope_marker(self, x_base, z_base, slope, length=120.0, dir_x=1.0, label=None, lift_mm=22.0):
        """Draws an architectural slope triangle & grade/degree annotation along an inclined or flat deck."""
        x0 = x_base
        z0 = z_base + lift_mm
        x1 = x_base + dir_x * length
        z1 = z_base + slope * (dir_x * length) + lift_mm
        deg = math.degrees(math.atan(abs(slope)))
        pct = abs(slope) * 100.0
        txt = label or f"Pend. {pct:.0f}% ({deg:.1f}°)"
        # Arrow along slope
        self.add_flow_arrow([(x0, z0), (x1, z1)], color_hex="#165C3A", lw=0.24, head_mm=10.0)
        # Fine right triangle reference below arrow
        tx_mid = 0.5 * (x0 + x1)
        tz_mid = 0.5 * (z0 + z1)
        self.add_text("COTAS", tx_mid, max(z0, z1) + 7.5, txt, height_sheet_mm=2.1, color_hex="#165C3A", align="center")

    def add_leader(self, target_xz, elbow_xz, text_end_xz, label, sublabel=None, align="left", badge=None):
        x0, z0 = target_xz
        x1, z1 = elbow_xz
        x2, z2 = text_end_xz
        sc = self.scale
        # Target double ring dot
        self.add_circle("CALLOUTS", x0, z0, 0.90 * sc, fill_hex="#FFFFFF", stroke_hex="#161D24", lw=0.18)
        self.add_circle("CALLOUTS", x0, z0, 0.44 * sc, fill_hex="#9C3B26", stroke_hex="#9C3B26", lw=0.10)
        self.add_line("CALLOUTS", x0, z0, x1, z1, color_hex="#2D3742", lw=0.18)
        self.add_line("CALLOUTS", x1, z1, x2, z2, color_hex="#2D3742", lw=0.18)
        if badge is not None:
            r_b = 1.45 * sc
            bx = x2 + (1.55 * sc if align == "left" else -1.55 * sc)
            self.add_circle("CALLOUTS", bx, z2, r_b, fill_hex="#FAF7F2", stroke_hex="#9C3B26", lw=0.22)
            self.add_text("CALLOUTS", bx, z2 - 0.65 * sc, str(badge), height_sheet_mm=1.85, color_hex="#9C3B26", align="center")
            tx = bx + (2.35 * sc if align == "left" else -2.35 * sc)
        else:
            tx = x2 + (1.20 * sc if align == "left" else -1.20 * sc)
        self.add_text("CALLOUTS", tx, z2 + (0.45 * sc if sublabel else -0.50 * sc), label, height_sheet_mm=2.35, color_hex="#14191F", align=align)
        if sublabel:
            self.add_text("NOTES", tx, z2 - 1.95 * sc, sublabel, height_sheet_mm=1.85, color_hex="#505A66", align=align)

    def add_dim_h(self, x0, x1, z_dim, z_ref0, z_ref1, label=None, offset_dir=1.0):
        """Exact horizontal dimension in mm with architectural ticks."""
        ext_over = 10.0 * offset_dir
        self.add_line("COTAS", x0, z_ref0, x0, z_dim + ext_over, lw=0.13)
        self.add_line("COTAS", x1, z_ref1, x1, z_dim + ext_over, lw=0.13)
        self.add_line("COTAS", x0 - 12.0, z_dim, x1 + 12.0, z_dim, lw=0.18)
        for tx in (x0, x1):
            self.add_line("COTAS", tx - 5.0, z_dim - 5.0, tx + 5.0, z_dim + 5.0, lw=0.38)
        val = abs(x1 - x0)
        txt = label or (f"{val:.0f}" if abs(val - round(val)) < 0.05 else f"{val:.1f}")
        self.add_text("COTAS", (x0 + x1) * 0.5, z_dim + 5.0, txt, height_sheet_mm=2.15, align="center")

    def add_dim_v(self, z0, z1, x_dim, x_ref0, x_ref1, label=None, offset_dir=1.0):
        """Exact vertical dimension in mm with architectural ticks."""
        ext_over = 10.0 * offset_dir
        self.add_line("COTAS", x_ref0, z0, x_dim + ext_over, z0, lw=0.13)
        self.add_line("COTAS", x_ref1, z1, x_dim + ext_over, z1, lw=0.13)
        self.add_line("COTAS", x_dim, min(z0, z1) - 12.0, x_dim, max(z0, z1) + 12.0, lw=0.18)
        for tz in (z0, z1):
            self.add_line("COTAS", x_dim - 5.0, tz - 5.0, x_dim + 5.0, tz + 5.0, lw=0.38)
        val = abs(z1 - z0)
        txt = label or (f"{val:.0f}" if abs(val - round(val)) < 0.05 else f"{val:.1f}")
        self.add_text("COTAS", x_dim - 5.0, (z0 + z1) * 0.5, txt, height_sheet_mm=2.15, align="center", angle=90.0)

    def add_flow_arrow(self, pts, color_hex="#0B72B9", lw=0.32, head_mm=13.0, dash=None):
        self.arrows.append(("AGUA_FLUJO", list(pts), color_hex, lw, head_mm, dash))

    def _generate_hatch_segments(self, kind, poly, spacing, angle_deg=0.0):
        """Deterministic geometric hatch generator returning lines & circles in model mm."""
        xs = [p[0] for p in poly]
        zs = [p[1] for p in poly]
        minx, maxx = min(xs), max(xs)
        minz, maxz = min(zs), max(zs)
        segs = []
        circs = []

        def point_in_poly(px, pz):
            inside = False
            n = len(poly)
            j = n - 1
            for i in range(n):
                xi, zi = poly[i]
                xj, zj = poly[j]
                if ((zi > pz) != (zj > pz)) and (px < (xj - xi) * (pz - zi) / (zj - zi + 1e-9) + xi):
                    inside = not inside
                j = i
            return inside

        def clip_segment_to_poly(ax, az, bx, bz):
            ts = [0.0, 1.0]
            dx, dz = bx - ax, bz - az
            n = len(poly)
            for i in range(n):
                cx, cz = poly[i]
                ex, ez = poly[(i + 1) % n]
                rx, rz = ex - cx, ez - cz
                denom = dx * rz - dz * rx
                if abs(denom) > 1e-9:
                    t = ((cx - ax) * rz - (cz - az) * rx) / denom
                    u = ((cx - ax) * dz - (cz - az) * dx) / denom
                    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                        ts.append(t)
            ts = sorted(set(round(t, 6) for t in ts))
            out = []
            for k in range(len(ts) - 1):
                t0, t1 = ts[k], ts[k + 1]
                if t1 - t0 < 1e-5:
                    continue
                tm = 0.5 * (t0 + t1)
                if point_in_poly(ax + tm * dx, az + tm * dz):
                    out.append((ax + t0 * dx, az + t0 * dz, ax + t1 * dx, az + t1 * dz))
            return out

        if kind in ("diag45", "diag135", "cross", "slate_layers"):
            if kind == "slate_layers":
                angles = [angle_deg if abs(angle_deg) > 0.1 else 25.0]
            else:
                angles = [45.0] if kind == "diag45" else ([135.0] if kind == "diag135" else [45.0, 135.0])
            diag = math.hypot(maxx - minx, maxz - minz) + spacing * 2
            cx, cz = 0.5 * (minx + maxx), 0.5 * (minz + maxz)
            for ang in angles:
                rad = math.radians(ang)
                ux, uz = math.cos(rad), math.sin(rad)
                nx, nz = -uz, ux
                steps = int(diag / spacing) + 2
                for s in range(-steps, steps + 1):
                    px, pz = cx + s * spacing * nx, cz + s * spacing * nz
                    ax, az = px - diag * ux, pz - diag * uz
                    bx, bz = px + diag * ux, pz + diag * uz
                    segs.extend(clip_segment_to_poly(ax, az, bx, bz))
        elif kind == "horiz_masonry":
            z = minz + spacing * 0.5
            row = 0
            while z < maxz:
                segs.extend(clip_segment_to_poly(minx - 5, z, maxx + 5, z))
                if row % 2 == 1:
                    segs.extend(clip_segment_to_poly(minx - 5, z + spacing * 0.25, maxx + 5, z + spacing * 0.25))
                z += spacing
                row += 1
        elif kind == "wood_cut":
            if len(poly) >= 4:
                segs.extend(clip_segment_to_poly(poly[0][0], poly[0][1], poly[2][0], poly[2][1]))
                segs.extend(clip_segment_to_poly(poly[1][0], poly[1][1], poly[3][0], poly[3][1]))
        elif kind == "wood_grain":
            rad = math.radians(angle_deg)
            ux, uz = math.cos(rad), math.sin(rad)
            nx, nz = -uz, ux
            diag = math.hypot(maxx - minx, maxz - minz) + spacing * 2
            cx, cz = 0.5 * (minx + maxx), 0.5 * (minz + maxz)
            steps = int(diag / max(4.0, spacing)) + 2
            for s in range(-steps, steps + 1):
                px, pz = cx + s * spacing * nx, cz + s * spacing * nz
                # Subtle wavy grain polyline segments
                n_seg = 12
                for i in range(n_seg):
                    t0 = -0.5 * diag + (i / n_seg) * diag
                    t1 = -0.5 * diag + ((i + 1) / n_seg) * diag
                    w0 = math.sin(i * 0.9 + s) * 1.4
                    w1 = math.sin((i + 1) * 0.9 + s) * 1.4
                    ax, az = px + t0 * ux + w0 * nx, pz + t0 * uz + w0 * nz
                    bx, bz = px + t1 * ux + w1 * nx, pz + t1 * uz + w1 * nz
                    segs.extend(clip_segment_to_poly(ax, az, bx, bz))
        elif kind == "batt_insul":
            # Architectural sinusoidal insulation loop along angle_deg
            rad = math.radians(angle_deg)
            ux, uz = math.cos(rad), math.sin(rad)
            nx, nz = -uz, ux
            cx, cz = 0.5 * (minx + maxx), 0.5 * (minz + maxz)
            # Project vertices onto u and n axes
            us = [(px - cx) * ux + (pz - cz) * uz for px, pz in poly]
            ns = [(px - cx) * nx + (pz - cz) * nz for px, pz in poly]
            u_min, u_max = min(us), max(us)
            n_min, n_max = min(ns), max(ns)
            amp = max(4.0, 0.36 * (n_max - n_min))
            n_mid = 0.5 * (n_min + n_max)
            half_per = max(6.0, spacing)
            u = u_min + 2.0
            prev_p = None
            steps = max(2, int((u_max - u_min) / (half_per * 0.25)))
            for k in range(steps + 1):
                uk = u_min + (k / steps) * (u_max - u_min)
                ph = (uk - u_min) * math.pi / half_per
                nk = n_mid + amp * math.sin(ph)
                pk = (cx + uk * ux + nk * nx, cz + uk * uz + nk * nz)
                if prev_p is not None:
                    segs.extend(clip_segment_to_poly(prev_p[0], prev_p[1], pk[0], pk[1]))
                prev_p = pk
        elif kind in ("cellular", "concrete", "dots"):
            seed = int(abs(minx * 13 + minz * 29 + maxx * 7)) & 0xFFFF
            step_x = spacing
            step_z = spacing
            ix = 0
            x = minx + step_x * 0.4
            while x < maxx:
                iz = 0
                z = minz + step_z * 0.4
                while z < maxz:
                    h = ((ix * 73856093) ^ (iz * 19349663) ^ seed) & 0xFFFF
                    jx = ((h % 100) / 100.0 - 0.5) * step_x * 0.65
                    jz = (((h >> 6) % 100) / 100.0 - 0.5) * step_z * 0.65
                    px, pz = x + jx, z + jz
                    if point_in_poly(px, pz):
                        if kind == "cellular":
                            r = 1.6 + (h % 5) * 0.45 if (h % 3 != 0) else 0.75
                            if (
                                point_in_poly(px - r, pz) and point_in_poly(px + r, pz)
                                and point_in_poly(px, pz - r) and point_in_poly(px, pz + r)
                            ):
                                circs.append((px, pz, r))
                        elif kind == "concrete":
                            if h % 4 == 0:
                                r = 2.4 + (h % 3) * 0.9
                                if (
                                    point_in_poly(px - r, pz) and point_in_poly(px + r, pz)
                                    and point_in_poly(px, pz - r) and point_in_poly(px, pz + r)
                                ):
                                    p1 = (px - r, pz - r * 0.6)
                                    p2 = (px + r * 0.9, pz - r * 0.2)
                                    p3 = (px - r * 0.1, pz + r * 0.9)
                                    segs.append((p1[0], p1[1], p2[0], p2[1]))
                                    segs.append((p2[0], p2[1], p3[0], p3[1]))
                                    segs.append((p3[0], p3[1], p1[0], p1[1]))
                            else:
                                circs.append((px, pz, 0.7))
                        else:
                            circs.append((px, pz, 0.65))
                    z += step_z
                    iz += 1
                x += step_x
                ix += 1
        elif kind == "zigzag_v":
            cx = 0.5 * (minx + maxx)
            half_w = max(2.0, 0.40 * (maxx - minx))
            z = minz + 3.0
            step = max(6.0, spacing)
            prev_x, prev_z = cx - half_w, z
            side = 1
            while z + step <= maxz - 2.0:
                nx = cx + side * half_w
                nz = z + step
                segs.append((prev_x, prev_z, nx, nz))
                prev_x, prev_z = nx, nz
                side *= -1
                z += step
        return segs, circs

    # ------------------------------------------------------------------
    # Exporters: DXF (1:1 in mm) + Vector PDF (A3) + Vector SVG
    # ------------------------------------------------------------------
    def export_dxf(self, path):
        doc = ezdxf.new("R2010")
        doc.units = ezdxf.units.MM
        doc.header["$INSUNITS"] = 4
        doc.header["$MEASUREMENT"] = 1
        msp = doc.modelspace()

        for lname, st in LAYER_STYLES.items():
            if lname not in doc.layers:
                doc.layers.add(lname, color=st["aci"], lineweight=snap_dxf_lw(st["lw"]))

        for layer, pts, closed, fill_hex, _, lw, _ in self.polys:
            msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": layer, "lineweight": snap_dxf_lw(lw)})
            if fill_hex and closed and layer in ("MEMBRANA",):
                h = msp.add_hatch(color=LAYER_STYLES[layer]["aci"], dxfattribs={"layer": "HATCH_LIGHT"})
                h.paths.add_polyline_path(pts, is_closed=True)

        for layer, x0, z0, x1, z1, _, lw, _ in self.lines:
            msp.add_line((x0, z0), (x1, z1), dxfattribs={"layer": layer, "lineweight": snap_dxf_lw(lw)})

        for layer, cx, cz, r, _, _, lw in self.circles:
            msp.add_circle((cx, cz), r, dxfattribs={"layer": layer, "lineweight": snap_dxf_lw(lw)})

        for layer, kind, poly, spacing, _, ang in self.hatches:
            segs, circs = self._generate_hatch_segments(kind, poly, spacing, ang)
            for ax, az, bx, bz in segs:
                msp.add_line((ax, az), (bx, bz), dxfattribs={"layer": layer})
            for px, pz, r in circs:
                msp.add_circle((px, pz), r, dxfattribs={"layer": layer})

        for layer, pts, _, lw, head_mm, _ in self.arrows:
            if len(pts) >= 2:
                msp.add_lwpolyline(pts, close=False, dxfattribs={"layer": layer, "lineweight": snap_dxf_lw(lw)})
                p1, p2 = pts[-2], pts[-1]
                ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
                for da in (152, -152):
                    a = ang + math.radians(da)
                    msp.add_line(p2, (p2[0] + head_mm * math.cos(a), p2[1] + head_mm * math.sin(a)), dxfattribs={"layer": layer})

        for layer, x, z, text, h_sheet, _, align, angle in self.texts:
            h_model = h_sheet * self.scale
            att = msp.add_mtext(
                text,
                dxfattribs={
                    "layer": layer,
                    "char_height": h_model,
                    "rotation": angle,
                    "attachment_point": 5 if align == "center" else (6 if align == "right" else 4),
                },
            )
            att.set_location((x, z))

        bx = self.meta["bounds_mm"]
        msp.add_mtext(
            f"{self.meta['code']} — {self.meta['title']}\\PEscala de plano 1:{int(self.scale)} · Unidades: mm · {self.meta['normativa']}",
            dxfattribs={"layer": "NOTES", "char_height": 14.0},
        ).set_location((bx["x_min"], bx["z_max"] + 120.0))

        os.makedirs(os.path.dirname(path), exist_ok=True)
        doc.saveas(path)

    def _pdf_pt(self, sx_mm, sy_mm):
        mm2pt = 72.0 / 25.4
        return pymupdf.Point(sx_mm * mm2pt, (self.sheet_h - sy_mm) * mm2pt)

    def export_pdf_and_png(self, pdf_path, png_path, dpi=250):
        mm2pt = 72.0 / 25.4
        doc = pymupdf.open()
        page = doc.new_page(width=self.sheet_w * mm2pt, height=self.sheet_h * mm2pt)
        shape = page.new_shape()

        # Subtle warm studio drafting paper margin outside frame, crisp white field inside
        page.draw_rect(page.rect, fill=hex_to_rgb01("#F6F4EE"), color=None)
        p0_f = self._pdf_pt(10.0, 287.0)
        p1_f = self._pdf_pt(410.0, 10.0)
        page.draw_rect(pymupdf.Rect(p0_f.x, p0_f.y, p1_f.x, p1_f.y), fill=(1, 1, 1), color=None)

        # 1. Polygons (background fills first)
        for layer, pts, closed, fill_hex, stroke_hex, lw, dash in self.polys:
            p_pts = [self._pdf_pt(*self.m2s(x, z)) for (x, z) in pts]
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

        # 2. Hatches (subtle fine CAD pen)
        for layer, kind, poly, spacing, color_hex, ang in self.hatches:
            segs, circs = self._generate_hatch_segments(kind, poly, spacing, ang)
            col = hex_to_rgb01(color_hex)
            lw = LAYER_STYLES.get(layer, LAYER_STYLES["HATCH_LIGHT"])["lw"] * mm2pt * 0.70
            for ax, az, bx, bz in segs:
                shape.draw_line(self._pdf_pt(*self.m2s(ax, az)), self._pdf_pt(*self.m2s(bx, bz)))
                shape.finish(color=col, width=lw)
            for px, pz, r in circs:
                cp = self._pdf_pt(*self.m2s(px, pz))
                rp = (r / self.scale) * mm2pt
                shape.draw_circle(cp, rp)
                if kind == "dots":
                    shape.finish(color=col, fill=col, width=0.2)
                else:
                    shape.finish(color=col, width=lw)

        # 3. Lines
        for layer, x0, z0, x1, z1, color_hex, lw, dash in self.lines:
            shape.draw_line(self._pdf_pt(*self.m2s(x0, z0)), self._pdf_pt(*self.m2s(x1, z1)))
            shape.finish(
                color=hex_to_rgb01(color_hex),
                width=lw * mm2pt * 0.72,
                dashes=f"[{dash[0]*mm2pt:.1f} {dash[1]*mm2pt:.1f}] 0" if dash else None,
            )

        # 4. Circles
        for layer, cx, cz, r, fill_hex, stroke_hex, lw in self.circles:
            cp = self._pdf_pt(*self.m2s(cx, cz))
            rp = (r / self.scale) * mm2pt
            shape.draw_circle(cp, rp)
            shape.finish(
                color=hex_to_rgb01(stroke_hex) if stroke_hex else None,
                fill=hex_to_rgb01(fill_hex) if fill_hex else None,
                width=lw * mm2pt * 0.72,
            )

        # 5. Flow arrows
        for layer, pts, color_hex, lw, head_mm, dash in self.arrows:
            col = hex_to_rgb01(color_hex)
            p_pts = [self._pdf_pt(*self.m2s(x, z)) for (x, z) in pts]
            shape.draw_polyline(p_pts)
            shape.finish(
                color=col,
                width=lw * mm2pt * 0.72,
                dashes=f"[{dash[0]*mm2pt:.1f} {dash[1]*mm2pt:.1f}] 0" if dash else None,
            )
            p1, p2 = pts[-2], pts[-1]
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            tip = self._pdf_pt(*self.m2s(*p2))
            w1 = self._pdf_pt(*self.m2s(p2[0] + head_mm * math.cos(ang + math.radians(150)), p2[1] + head_mm * math.sin(ang + math.radians(150))))
            w2 = self._pdf_pt(*self.m2s(p2[0] + head_mm * math.cos(ang - math.radians(150)), p2[1] + head_mm * math.sin(ang - math.radians(150))))
            shape.draw_polyline([w1, tip, w2])
            shape.finish(color=col, fill=col, closePath=True, width=0.4)

        # 6. A3 Sheet Frame + Architectural Title Block & Legend
        self._draw_pdf_title_block(shape, page, mm2pt)
        shape.commit()

        # 7. Model-space text labels with true Segoe UI TrueType metrics (exact Unicode glyphs & right-align)
        f_reg_path = r"C:\Windows\Fonts\segoeui.ttf"
        f_bld_path = r"C:\Windows\Fonts\segoeuib.ttf"
        has_ttf = os.path.exists(f_reg_path) and os.path.exists(f_bld_path)
        if has_ttf:
            page.insert_font(fontname="S_REG", fontfile=f_reg_path)
            page.insert_font(fontname="S_BLD", fontfile=f_bld_path)
            f_reg_m = pymupdf.Font(fontfile=f_reg_path)
            f_bld_m = pymupdf.Font(fontfile=f_bld_path)
        for layer, x, z, text, h_sheet, color_hex, align, angle in self.texts:
            sx, sy = self.m2s(x, z)
            fs = h_sheet * mm2pt
            col = hex_to_rgb01(color_hex)
            if has_ttf:
                is_bld = (layer == "CALLOUTS")
                fname = "S_BLD" if is_bld else "S_REG"
                tw = (f_bld_m if is_bld else f_reg_m).text_length(text, fontsize=fs)
            else:
                fname = "hebo" if layer == "CALLOUTS" else "helv"
                tw = pymupdf.get_text_length(text, fontname=fname, fontsize=fs)
            if abs(angle - 90.0) < 1.0:
                pt = self._pdf_pt(sx, sy - (tw / mm2pt) * 0.5 if align == "center" else sy)
                page.insert_text(pt, text, fontname=fname, fontsize=fs, color=col, rotate=90)
            else:
                dx_mm = (-tw / mm2pt * 0.5) if align == "center" else ((-tw / mm2pt) if align == "right" else 0.0)
                pt = self._pdf_pt(sx + dx_mm, sy)
                page.insert_text(pt, text, fontname=fname, fontsize=fs, color=col)

        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        tmp_pdf = pdf_path + ".tmp.pdf"
        doc.save(tmp_pdf)
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        pix.save(png_path)
        doc.close()
        os.replace(tmp_pdf, pdf_path)

    def _draw_pdf_title_block(self, shape, page, mm2pt):
        def rect(x0, y0, x1, y1, lw=0.35, color="#14191F", fill=None):
            p0 = self._pdf_pt(x0, y0)
            p1 = self._pdf_pt(x1, y1)
            r = pymupdf.Rect(min(p0.x, p1.x), min(p0.y, p1.y), max(p0.x, p1.x), max(p0.y, p1.y))
            shape.draw_rect(r)
            shape.finish(color=hex_to_rgb01(color) if color else None, fill=fill, width=lw * mm2pt * 0.72)

        def line(x0, y0, x1, y1, lw=0.20, color="#14191F"):
            shape.draw_line(self._pdf_pt(x0, y0), self._pdf_pt(x1, y1))
            shape.finish(color=hex_to_rgb01(color), width=lw * mm2pt * 0.72)

        # Double architectural frame
        rect(10.0, 10.0, 410.0, 287.0, lw=0.52)
        rect(11.6, 11.6, 408.4, 285.4, lw=0.14, color="#505A66")
        # Registration center ticks
        for (ax, ay, bx, by) in ((210, 10, 210, 13.5), (210, 287, 210, 283.5), (10, 148.5, 13.5, 148.5), (410, 148.5, 406.5, 148.5)):
            line(ax, ay, bx, by, lw=0.24, color="#14191F")

        # Top-left editorial header banner with burgundy accent stripe
        rect(14.5, 270.0, 232.0, 282.8, lw=0.22, color="#2D3742", fill=hex_to_rgb01("#FAF8F4"))
        rect(14.5, 270.0, 17.5, 282.8, lw=0.0, color=None, fill=hex_to_rgb01("#9C3B26"))

        # Compact Bottom-Center Simbologia Strip (X: 106..252, Y: 13.5..24.5)
        rect(106.0, 13.5, 254.0, 24.5, lw=0.18, color="#8C95A0", fill=hex_to_rgb01("#FAF9F6"))
        swatches = [
            ("#E2E6E9", "#252B33", "HA-25"),
            ("#F7E4DC", "#7D3522", "Cerám."),
            ("#FDF0B8", "#A8810A", "Aisl. AT"),
            ("#282C33", "#101214", "Imp. SBS"),
            ("#E7DFD5", "#5E5850", "Mortero"),
            ("#DCE8F0", "#30495E", "Metal/Zn"),
        ]
        sx = 109.5
        for fill_s, stroke_s, _ in swatches:
            rect(sx, 15.6, sx + 5.4, 19.6, lw=0.20, color=stroke_s, fill=hex_to_rgb01(fill_s))
            sx += 23.6

        # Cajetin bottom-right (149 x 38 mm: X 259..408, Y 11.6..49.5)
        rect(259.0, 11.6, 408.0, 49.5, lw=0.40, fill=hex_to_rgb01("#FAF8F4"))
        rect(259.0, 47.6, 408.0, 49.5, lw=0.0, color=None, fill=hex_to_rgb01("#9C3B26"))
        line(259.0, 36.5, 408.0, 36.5, lw=0.20, color="#3A434E")
        line(259.0, 22.0, 408.0, 22.0, lw=0.20, color="#3A434E")
        line(332.0, 11.6, 332.0, 22.0, lw=0.20, color="#3A434E")
        line(370.0, 11.6, 370.0, 22.0, lw=0.20, color="#3A434E")

        # Graphic scale bar bottom-left (X 17..97, Y 15.8..18.4) -> 0..400 mm @ scale
        bar_x0, bar_y0 = 17.0, 15.6
        seg_w_mm = 100.0 / self.scale  # width of 100 model mm on sheet
        rect(bar_x0, bar_y0, bar_x0 + seg_w_mm * 0.5, bar_y0 + 2.6, lw=0.18, fill=hex_to_rgb01("#14191F"))
        rect(bar_x0 + seg_w_mm * 0.5, bar_y0, bar_x0 + seg_w_mm, bar_y0 + 2.6, lw=0.18, fill=(1, 1, 1))
        for i in range(1, 4):
            rect(bar_x0 + i * seg_w_mm, bar_y0, bar_x0 + (i + 1) * seg_w_mm, bar_y0 + 2.6, lw=0.18,
                 fill=hex_to_rgb01("#14191F") if i % 2 == 0 else (1, 1, 1))

        shape.commit()

        dark = hex_to_rgb01("#14191F")
        muted = hex_to_rgb01("#505A66")
        accent = hex_to_rgb01("#9C3B26")

        page.insert_text(self._pdf_pt(21.0, 277.8), "CONSTRUCCIÓN II · TEJADOS Y AZOTEAS (UPV · ETSIE)",
                         fontname="hebo", fontsize=2.8 * mm2pt, color=dark)
        page.insert_text(self._pdf_pt(21.0, 272.8), f"{self.meta['slide']}  |  {self.meta['normativa']}",
                         fontname="helv", fontsize=2.05 * mm2pt, color=muted)

        # Swatch labels
        page.insert_text(self._pdf_pt(109.5, 21.4), "SIMBOLOGÍA CONSTRUCTIVA NORMALIZADA",
                         fontname="hebo", fontsize=1.65 * mm2pt, color=muted)
        sx = 116.2
        for _, _, lbl_s in swatches:
            page.insert_text(self._pdf_pt(sx, 16.5), lbl_s, fontname="helv", fontsize=1.75 * mm2pt, color=dark)
            sx += 23.6

        page.insert_text(self._pdf_pt(263.5, 43.2), self.meta["code"],
                         fontname="hebo", fontsize=2.55 * mm2pt, color=accent)
        page.insert_text(self._pdf_pt(263.5, 38.8), "SECCIÓN CONSTRUCTIVA MILIMÉTRICA · 2D CAD",
                         fontname="helv", fontsize=1.80 * mm2pt, color=muted)

        title = self.meta["title"]
        if len(title) > 46:
            mid = title.rfind(" ", 0, 46)
            if mid < 10:
                mid = 46
            t1, t2 = title[:mid], title[mid + 1 :]
            page.insert_text(self._pdf_pt(263.5, 31.2), t1, fontname="hebo", fontsize=2.35 * mm2pt, color=dark)
            page.insert_text(self._pdf_pt(263.5, 25.8), t2, fontname="hebo", fontsize=2.35 * mm2pt, color=dark)
        else:
            page.insert_text(self._pdf_pt(263.5, 28.4), title, fontname="hebo", fontsize=2.45 * mm2pt, color=dark)

        page.insert_text(self._pdf_pt(263.5, 18.2), "ESCALA", fontname="helv", fontsize=1.60 * mm2pt, color=muted)
        page.insert_text(self._pdf_pt(263.5, 13.6), f"1:{int(self.scale)} (UNE A3)", fontname="hebo", fontsize=2.35 * mm2pt, color=dark)

        page.insert_text(self._pdf_pt(336.0, 18.2), "UNIDADES", fontname="helv", fontsize=1.60 * mm2pt, color=muted)
        page.insert_text(self._pdf_pt(336.0, 13.6), "mm", fontname="hebo", fontsize=2.35 * mm2pt, color=dark)

        page.insert_text(self._pdf_pt(374.0, 18.2), "PLANO", fontname="helv", fontsize=1.60 * mm2pt, color=muted)
        plan_tag = self.meta["code"].split("·")[0].strip() if "DET-" in self.meta["code"] else self.meta["id"].upper()
        page.insert_text(self._pdf_pt(374.0, 13.6), plan_tag, fontname="hebo", fontsize=2.25 * mm2pt, color=dark)

        for i in range(5):
            lbl = f"{i * 100}" + (" mm" if i == 4 else "")
            page.insert_text(self._pdf_pt(bar_x0 + i * seg_w_mm - 1.5, bar_y0 + 4.4), lbl,
                             fontname="helv", fontsize=1.75 * mm2pt, color=dark)
        page.insert_text(self._pdf_pt(bar_x0, bar_y0 - 2.6), f"ESCALA GRÁFICA 1:{int(self.scale)}",
                         fontname="hebo", fontsize=1.75 * mm2pt, color=muted)

    def export_svg(self, svg_path):
        """Emit clean architectural vector SVG (viewBox 0 0 420 297 mm)."""
        def spt(sx, sy):
            return (sx, self.sheet_h - sy)

        plan_tag = self.meta["code"].split("·")[0].strip() if "DET-" in self.meta["code"] else self.meta["id"].upper()
        seg_w_mm = 100.0 / self.scale

        out = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.sheet_w:.1f} {self.sheet_h:.1f}" '
            'style="background:#ffffff; font-family:\'Inter\',\'Helvetica Neue\',Arial,sans-serif;">',
            '  <rect x="0" y="0" width="420" height="297" fill="#F6F4EE"/>',
            '  <rect x="10" y="10" width="400" height="277" fill="#FFFFFF" stroke="#14191F" stroke-width="0.52"/>',
            '  <rect x="11.6" y="11.6" width="396.8" height="273.8" fill="none" stroke="#505A66" stroke-width="0.14"/>',
            '  <g id="sheet_frame">',
            '    <rect x="14.5" y="14.2" width="217.5" height="12.8" fill="#FAF8F4" stroke="#2D3742" stroke-width="0.22"/>',
            '    <rect x="14.5" y="14.2" width="3.0" height="12.8" fill="#9C3B26"/>',
            f'    <text x="21" y="19.8" font-size="2.95" font-weight="700" fill="#14191F">CONSTRUCCIÓN II · TEJADOS Y AZOTEAS (UPV · ETSIE)</text>',
            f'    <text x="21" y="24.2" font-size="2.1" fill="#505A66">{sax.escape(self.meta["slide"])} | {sax.escape(self.meta["normativa"])}</text>',
            '    <rect x="106" y="272.5" width="148" height="11" fill="#FAF9F6" stroke="#8C95A0" stroke-width="0.18"/>',
            '    <text x="109.5" y="275.8" font-size="1.65" font-weight="700" fill="#505A66">SIMBOLOGÍA CONSTRUCTIVA NORMALIZADA</text>',
        ]
        swatches = [
            ("#E2E6E9", "#252B33", "HA-25"),
            ("#F7E4DC", "#7D3522", "Cerám."),
            ("#FDF0B8", "#A8810A", "Aisl. AT"),
            ("#282C33", "#101214", "Imp. SBS"),
            ("#E7DFD5", "#5E5850", "Mortero"),
            ("#DCE8F0", "#30495E", "Metal/Zn"),
        ]
        sx = 109.5
        for fill_s, stroke_s, lbl_s in swatches:
            out.append(f'    <rect x="{sx:.1f}" y="277.4" width="5.4" height="4.0" fill="{fill_s}" stroke="{stroke_s}" stroke-width="0.2"/>')
            out.append(f'    <text x="{sx + 6.7:.1f}" y="280.4" font-size="1.75" fill="#14191F">{lbl_s}</text>')
            sx += 23.6

        out += [
            '    <rect x="259" y="247.5" width="149" height="37.9" fill="#FAF8F4" stroke="#14191F" stroke-width="0.40"/>',
            '    <rect x="259" y="247.5" width="149" height="1.9" fill="#9C3B26"/>',
            '    <line x1="259" y1="260.5" x2="408" y2="260.5" stroke="#3A434E" stroke-width="0.20"/>',
            '    <line x1="259" y1="275.0" x2="408" y2="275.0" stroke="#3A434E" stroke-width="0.20"/>',
            '    <line x1="332" y1="275.0" x2="332" y2="285.4" stroke="#3A434E" stroke-width="0.20"/>',
            '    <line x1="370" y1="275.0" x2="370" y2="285.4" stroke="#3A434E" stroke-width="0.20"/>',
            f'    <text x="263.5" y="254.2" font-size="2.7" font-weight="700" fill="#9C3B26">{sax.escape(self.meta["code"])}</text>',
            '    <text x="263.5" y="258.5" font-size="1.85" fill="#505A66">SECCIÓN CONSTRUCTIVA MILIMÉTRICA · 2D CAD</text>',
        ]
        title = self.meta["title"]
        if len(title) > 46:
            mid = title.rfind(" ", 0, 46)
            if mid < 10:
                mid = 46
            out.append(f'    <text x="263.5" y="266.2" font-size="2.45" font-weight="700" fill="#14191F">{sax.escape(title[:mid])}</text>')
            out.append(f'    <text x="263.5" y="271.5" font-size="2.45" font-weight="700" fill="#14191F">{sax.escape(title[mid+1:])}</text>')
        else:
            out.append(f'    <text x="263.5" y="269.0" font-size="2.55" font-weight="700" fill="#14191F">{sax.escape(title)}</text>')
        out += [
            '    <text x="263.5" y="279.0" font-size="1.65" fill="#505A66">ESCALA</text>',
            f'    <text x="263.5" y="283.6" font-size="2.4" font-weight="700" fill="#14191F">1:{int(self.scale)} (UNE A3)</text>',
            '    <text x="336" y="279.0" font-size="1.65" fill="#505A66">UNIDADES</text>',
            '    <text x="336" y="283.6" font-size="2.4" font-weight="700" fill="#14191F">mm</text>',
            '    <text x="374" y="279.0" font-size="1.65" fill="#505A66">PLANO</text>',
            f'    <text x="374" y="283.6" font-size="2.3" font-weight="700" fill="#14191F">{sax.escape(plan_tag)}</text>',
            f'    <rect x="17" y="278.8" width="{seg_w_mm*0.5:.1f}" height="2.6" fill="#14191F" stroke="#14191F" stroke-width="0.18"/>',
            f'    <rect x="{17+seg_w_mm*0.5:.1f}" y="278.8" width="{seg_w_mm*0.5:.1f}" height="2.6" fill="#FFFFFF" stroke="#14191F" stroke-width="0.18"/>',
        ]
        for i in range(1, 4):
            fill_b = "#14191F" if i % 2 == 0 else "#FFFFFF"
            out.append(f'    <rect x="{17 + i*seg_w_mm:.1f}" y="278.8" width="{seg_w_mm:.1f}" height="2.6" fill="{fill_b}" stroke="#14191F" stroke-width="0.18"/>')
        for i in range(5):
            lbl = f"{i*100}" + (" mm" if i == 4 else "")
            out.append(f'    <text x="{17 + i*seg_w_mm - 1.5:.1f}" y="276.8" font-size="1.8" fill="#14191F">{lbl}</text>')
        out.append(f'    <text x="17" y="284.4" font-size="1.8" font-weight="700" fill="#505A66">ESCALA GRÁFICA 1:{int(self.scale)}</text>')
        out.append('  </g>')

        out.append('  <g id="model_geometry">')
        for layer, pts, closed, fill_hex, stroke_hex, lw, dash in self.polys:
            s_pts = " ".join(f"{spt(*self.m2s(x, z))[0]:.2f},{spt(*self.m2s(x, z))[1]:.2f}" for x, z in pts)
            tag = "polygon" if closed else "polyline"
            f_attr = fill_hex if fill_hex else "none"
            s_attr = stroke_hex if stroke_hex else "none"
            d_attr = f' stroke-dasharray="{dash[0]:.1f},{dash[1]:.1f}"' if dash else ""
            out.append(f'    <{tag} data-layer="{layer}" points="{s_pts}" fill="{f_attr}" stroke="{s_attr}" stroke-width="{lw*0.65:.2f}" stroke-linejoin="round"{d_attr}/>')

        for layer, kind, poly, spacing, color_hex, ang in self.hatches:
            segs, circs = self._generate_hatch_segments(kind, poly, spacing, ang)
            lw = LAYER_STYLES.get(layer, LAYER_STYLES["HATCH_LIGHT"])["lw"] * 0.65
            d_parts = []
            for ax, az, bx, bz in segs:
                p0 = spt(*self.m2s(ax, az))
                p1 = spt(*self.m2s(bx, bz))
                d_parts.append(f"M{p0[0]:.2f},{p0[1]:.2f}L{p1[0]:.2f},{p1[1]:.2f}")
            if d_parts:
                out.append(f'    <path data-layer="{layer}" d="{" ".join(d_parts)}" fill="none" stroke="{color_hex}" stroke-width="{lw:.2f}"/>')
            for px, pz, r in circs:
                cp = spt(*self.m2s(px, pz))
                rp = r / self.scale
                f_c = color_hex if kind == "dots" else "none"
                out.append(f'    <circle data-layer="{layer}" cx="{cp[0]:.2f}" cy="{cp[1]:.2f}" r="{rp:.2f}" fill="{f_c}" stroke="{color_hex}" stroke-width="{lw:.2f}"/>')

        for layer, x0, z0, x1, z1, color_hex, lw, dash in self.lines:
            p0 = spt(*self.m2s(x0, z0))
            p1 = spt(*self.m2s(x1, z1))
            d_attr = f' stroke-dasharray="{dash[0]:.1f},{dash[1]:.1f}"' if dash else ""
            out.append(f'    <line data-layer="{layer}" x1="{p0[0]:.2f}" y1="{p0[1]:.2f}" x2="{p1[0]:.2f}" y2="{p1[1]:.2f}" stroke="{color_hex}" stroke-width="{lw*0.65:.2f}"{d_attr}/>')

        for layer, cx, cz, r, fill_hex, stroke_hex, lw in self.circles:
            cp = spt(*self.m2s(cx, cz))
            rp = r / self.scale
            out.append(f'    <circle data-layer="{layer}" cx="{cp[0]:.2f}" cy="{cp[1]:.2f}" r="{rp:.2f}" fill="{fill_hex or "none"}" stroke="{stroke_hex}" stroke-width="{lw*0.65:.2f}"/>')

        for layer, pts, color_hex, lw, head_mm, dash in self.arrows:
            s_pts = " ".join(f"{spt(*self.m2s(x, z))[0]:.2f},{spt(*self.m2s(x, z))[1]:.2f}" for x, z in pts)
            d_attr = f' stroke-dasharray="{dash[0]:.1f},{dash[1]:.1f}"' if dash else ""
            out.append(f'    <polyline data-layer="{layer}" points="{s_pts}" fill="none" stroke="{color_hex}" stroke-width="{lw*0.65:.2f}" stroke-linecap="round"{d_attr}/>')
            p1, p2 = pts[-2], pts[-1]
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            tip = spt(*self.m2s(*p2))
            w1 = spt(*self.m2s(p2[0] + head_mm * math.cos(ang + math.radians(150)), p2[1] + head_mm * math.sin(ang + math.radians(150))))
            w2 = spt(*self.m2s(p2[0] + head_mm * math.cos(ang - math.radians(150)), p2[1] + head_mm * math.sin(ang - math.radians(150))))
            out.append(f'    <polygon points="{w1[0]:.2f},{w1[1]:.2f} {tip[0]:.2f},{tip[1]:.2f} {w2[0]:.2f},{w2[1]:.2f}" fill="{color_hex}"/>')

        for layer, x, z, text, h_sheet, color_hex, align, angle in self.texts:
            px, py = spt(*self.m2s(x, z))
            anchor = "middle" if align == "center" else ("end" if align == "right" else "start")
            rot = f' transform="rotate({-angle:.1f} {px:.2f} {py:.2f})"' if abs(angle) > 0.1 else ""
            fw = "700" if layer == "CALLOUTS" else "500"
            out.append(f'    <text data-layer="{layer}" x="{px:.2f}" y="{py:.2f}" font-size="{h_sheet*0.95:.2f}" font-weight="{fw}" fill="{color_hex}" text-anchor="{anchor}"{rot}>{sax.escape(text)}</text>')

        out.append('  </g>')
        out.append('</svg>')
        os.makedirs(os.path.dirname(svg_path), exist_ok=True)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
