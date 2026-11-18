r"""
Generates seamless high-definition 1024x1024 PBR texture sets (albedo, roughness, normal)
for architectural construction materials used in Blender Cycles HIP and GLB/Three.js.
"""

import os
import numpy as np
from PIL import Image


OUT_DIR = r"d:\C2\textures"


def _fbm(shape, scales=(4, 12, 32, 96), weights=(0.45, 0.30, 0.15, 0.10), seed=42):
    """Fast tileable multi-octave noise via periodic bicubic upsampling."""
    rng = np.random.default_rng(seed)
    h, w = shape
    acc = np.zeros((h, w), dtype=np.float32)
    w_sum = sum(weights)
    for sc, wt in zip(scales, weights):
        gh = max(2, sc)
        gw = max(2, sc)
        grid = rng.random((gh, gw), dtype=np.float32)
        pad = np.pad(grid, 2, mode="wrap")
        im = Image.fromarray((pad * 255.0).astype(np.uint8), mode="L")
        up_w = int(round(w * (gw + 4) / gw))
        up_h = int(round(h * (gh + 4) / gh))
        up = np.asarray(im.resize((up_w, up_h), Image.Resampling.BICUBIC), dtype=np.float32) / 255.0
        ox = int(round(2 * w / gw))
        oy = int(round(2 * h / gh))
        crop = up[oy : oy + h, ox : ox + w]
        acc += crop * (wt / max(1e-6, w_sum))
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)
    return acc


def _stamp_spheres(size, count, r_min, r_max, seed=1, prob_tint=1.0):
    """Fast local-ROI tileable spherical pore / aggregate stamper."""
    rng = np.random.default_rng(seed)
    depth = np.zeros((size, size), dtype=np.float32)
    tint = np.zeros((size, size), dtype=np.float32)
    for _ in range(count):
        cx = int(rng.integers(0, size))
        cy = int(rng.integers(0, size))
        rad = float(rng.uniform(r_min, r_max))
        ri = int(math.ceil(rad)) + 1 if "math" in globals() else int(np.ceil(rad)) + 1
        d_idx = np.arange(-ri, ri + 1)
        yy, xx = np.meshgrid(d_idx, d_idx, indexing="ij")
        d2 = (xx * xx + yy * yy) / (rad * rad)
        m = d2 < 1.0
        val = np.sqrt(np.maximum(0.0, 1.0 - d2))
        ys = (cy + yy[m]) % size
        xs = (cx + xx[m]) % size
        depth[ys, xs] = np.maximum(depth[ys, xs], val[m])
        if rng.random() < prob_tint:
            tint[ys, xs] = np.maximum(tint[ys, xs], val[m])
    return depth, tint


def _height_to_normal(height, strength=3.5):
    """Periodic Sobel gradient to RGB tangent-space normal map."""
    gx = (
        (np.roll(height, (-1, -1), axis=(0, 1)) + 2.0 * np.roll(height, -1, axis=1) + np.roll(height, (1, -1), axis=(0, 1)))
        - (np.roll(height, (-1, 1), axis=(0, 1)) + 2.0 * np.roll(height, 1, axis=1) + np.roll(height, (1, 1), axis=(0, 1)))
    ) * 0.25
    gy = (
        (np.roll(height, (-1, -1), axis=(0, 1)) + 2.0 * np.roll(height, -1, axis=0) + np.roll(height, (-1, 1), axis=(0, 1)))
        - (np.roll(height, (1, -1), axis=(0, 1)) + 2.0 * np.roll(height, 1, axis=0) + np.roll(height, (1, 1), axis=(0, 1)))
    ) * 0.25
    nx = -gx * strength
    ny = -gy * strength
    nz = np.ones_like(height)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-8
    rgb = np.stack([(nx / norm) * 0.5 + 0.5, (ny / norm) * 0.5 + 0.5, (nz / norm) * 0.5 + 0.5], axis=-1)
    return (np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8)


def _save_pbr(name, albedo_rgb, rough_01, height_01, bump_strength=4.0):
    os.makedirs(OUT_DIR, exist_ok=True)
    Image.fromarray(np.clip(albedo_rgb, 0, 255).astype(np.uint8), mode="RGB").save(
        os.path.join(OUT_DIR, f"{name}_albedo.png")
    )
    Image.fromarray((np.clip(rough_01, 0.04, 0.98) * 255.0).astype(np.uint8), mode="L").save(
        os.path.join(OUT_DIR, f"{name}_rough.png")
    )
    Image.fromarray(_height_to_normal(height_01, bump_strength), mode="RGB").save(
        os.path.join(OUT_DIR, f"{name}_normal.png")
    )


def generate_all(size=1024):
    S = (size, size)

    # 1. Terracotta Rasilla / Baldosa Ceramica
    n1 = _fbm(S, (4, 12, 36, 128), (0.38, 0.28, 0.20, 0.14), seed=101)
    n2 = _fbm(S, (24, 96, 256), (0.45, 0.35, 0.20), seed=102)
    streak = np.repeat(np.mean(_fbm(S, (8, 64, 192), (0.4, 0.35, 0.25), seed=103), axis=1, keepdims=True), size, axis=1)
    speck, _ = _stamp_spheres(size, 700, 1.2, 3.0, seed=104)
    clay_h = np.clip(0.55 * n2 + 0.30 * streak - 0.15 * speck, 0.0, 1.0)
    base = np.zeros((size, size, 3), dtype=np.float32)
    base[..., 0] = 176 + (n1 - 0.5) * 34 + (n2 - 0.5) * 18 - speck * 22
    base[..., 1] = 84 + (n1 - 0.5) * 22 + (n2 - 0.5) * 14 - speck * 16
    base[..., 2] = 58 + (n1 - 0.5) * 16 + (n2 - 0.5) * 10 - speck * 12
    _save_pbr("terracotta", base, 0.52 + 0.22 * (1.0 - clay_h), clay_h, bump_strength=3.6)

    # 2. Teja Curva Ceramica (Kiln-fired warm Mediterranean clay: longitudinal extrusion striations + subtle patina)
    tc1 = _fbm(S, (3, 9, 28, 96), (0.42, 0.28, 0.18, 0.12), seed=110)
    tc2 = _fbm(S, (24, 96, 256), (0.35, 0.35, 0.30), seed=111)
    tc_mold = np.repeat(np.mean(_fbm(S, (16, 128, 320), (0.3, 0.35, 0.35), seed=112), axis=0, keepdims=True), size, axis=0)
    tc_pits, tc_dark = _stamp_spheres(size, 1100, 1.0, 2.5, seed=113, prob_tint=0.45)
    moss = np.clip((_fbm(S, (4, 14, 48), (0.5, 0.3, 0.2), seed=114) - 0.68) * 3.2, 0.0, 1.0)
    tc_h = np.clip(0.45 * tc2 + 0.40 * tc_mold - 0.25 * tc_pits, 0.0, 1.0)
    tc = np.zeros((size, size, 3), dtype=np.float32)
    tc[..., 0] = 188 + (tc1 - 0.5) * 36 + (tc_mold - 0.5) * 22 - tc_dark * 42 - moss * 34
    tc[..., 1] = 94 + (tc1 - 0.5) * 30 + (tc_mold - 0.5) * 14 - tc_dark * 28 + moss * 12
    tc[..., 2] = 56 + (tc1 - 0.5) * 18 - tc_dark * 18 - moss * 10
    _save_pbr("teja_curva", tc, 0.58 + 0.24 * (1.0 - tc_h) + 0.10 * tc_pits, tc_h, bump_strength=5.0)

    # 3. Teja Mixta / Plana Engobada (Rich burnt terracotta satin matte with micro grog)
    tm1 = _fbm(S, (4, 16, 64, 180), (0.35, 0.30, 0.20, 0.15), seed=120)
    tm_pits, _ = _stamp_spheres(size, 500, 1.0, 2.2, seed=121)
    tm_h = np.clip(0.80 * tm1 - 0.20 * tm_pits, 0.0, 1.0)
    tm = np.zeros((size, size, 3), dtype=np.float32)
    tm[..., 0] = 158 + (tm1 - 0.5) * 22 - tm_pits * 18
    tm[..., 1] = 68 + (tm1 - 0.5) * 14 - tm_pits * 12
    tm[..., 2] = 46 + (tm1 - 0.5) * 10 - tm_pits * 10
    _save_pbr("teja_mixta", tm, 0.48 + 0.16 * (1.0 - tm_h), tm_h, bump_strength=3.0)

    # 4. Hollow Ceramic Brick / Bardo (Ladrillo Hueco, warmer light clay with crisp extrusion grooves)
    nb1 = _fbm(S, (5, 20, 72, 180), (0.35, 0.30, 0.20, 0.15), seed=201)
    nb_line = np.repeat(np.mean(_fbm(S, (14, 96), (0.5, 0.5), seed=202), axis=1, keepdims=True), size, axis=1)
    bh = 0.50 * nb1 + 0.50 * nb_line
    brick = np.zeros((size, size, 3), dtype=np.float32)
    brick[..., 0] = 196 + (nb1 - 0.5) * 28 + (nb_line - 0.5) * 14
    brick[..., 1] = 106 + (nb1 - 0.5) * 20 + (nb_line - 0.5) * 10
    brick[..., 2] = 74 + (nb1 - 0.5) * 16
    _save_pbr("brick_clay", brick, 0.72 + 0.16 * (1.0 - bh), bh, bump_strength=3.8)

    # 5. Cellular Concrete (Hormigon Celular: genuine crisp aerated spherical pores)
    hc_base = _fbm(S, (8, 28, 96, 220), (0.3, 0.3, 0.25, 0.15), seed=302)
    pores_s, _ = _stamp_spheres(size, 1500, 2.2, 6.0, seed=303)
    pores_b, _ = _stamp_spheres(size, 420, 6.2, 12.0, seed=304)
    pores = np.maximum(pores_s * 0.85, pores_b)
    hc_h = np.clip(hc_base * 0.30 + 0.70 - pores * 0.85, 0.0, 1.0)
    hc_col = np.zeros((size, size, 3), dtype=np.float32)
    shade = 1.0 - pores * 0.42 + (hc_base - 0.5) * 0.12
    hc_col[..., 0] = 216 * shade
    hc_col[..., 1] = 212 * shade
    hc_col[..., 2] = 202 * shade
    _save_pbr("cellular_concrete", hc_col, 0.80 + 0.15 * pores, hc_h, bump_strength=7.2)

    # 6. Lightweight Aggregate Concrete (Hormigon Aligerado Arlita)
    nc = _fbm(S, (10, 36, 110, 240), (0.3, 0.3, 0.25, 0.15), seed=401)
    arlita, arlita_tint = _stamp_spheres(size, 950, 4.5, 13.0, seed=402, prob_tint=0.68)
    ac_col = np.zeros((size, size, 3), dtype=np.float32)
    ac_col[..., 0] = 166 + (nc - 0.5) * 28 - arlita_tint * 48
    ac_col[..., 1] = 148 + (nc - 0.5) * 24 - arlita_tint * 54
    ac_col[..., 2] = 128 + (nc - 0.5) * 20 - arlita_tint * 48
    _save_pbr("lightweight_concrete", ac_col, 0.82 + 0.12 * nc, nc * 0.45 + 0.55 * (1.0 - arlita), bump_strength=6.2)

    # 7. Structural Reinforced Concrete (Forjado HA-25 with fine formwork grain & aggregate)
    ns = _fbm(S, (5, 18, 64, 180), (0.35, 0.25, 0.25, 0.15), seed=501)
    ns2 = _fbm(S, (32, 128, 256), (0.4, 0.35, 0.25), seed=502)
    pits_c, agg_c = _stamp_spheres(size, 450, 2.0, 6.5, seed=503, prob_tint=0.5)
    sc_h = np.clip(0.45 * ns + 0.45 * ns2 - 0.25 * pits_c, 0.0, 1.0)
    sc_col = np.zeros((size, size, 3), dtype=np.float32)
    v = 186 + (ns - 0.5) * 26 + (ns2 - 0.5) * 18 - pits_c * 24 - agg_c * 14
    sc_col[..., 0] = v - 2
    sc_col[..., 1] = v
    sc_col[..., 2] = v + 2
    _save_pbr("structural_concrete", sc_col, 0.70 + 0.20 * ns2 + 0.08 * pits_c, sc_h, bump_strength=4.2)

    # 8. Cement Mortar (Mortero 1:6 / 1:8 / M-2.5 with real coarse river sand particles)
    nm = _fbm(S, (12, 48, 140, 256), (0.25, 0.25, 0.25, 0.25), seed=601)
    sand, sand_col = _stamp_spheres(size, 1800, 1.2, 3.8, seed=602, prob_tint=0.45)
    mh_c = np.clip(0.60 * nm + 0.40 * sand, 0.0, 1.0)
    m_col = np.zeros((size, size, 3), dtype=np.float32)
    m_col[..., 0] = 166 + (nm - 0.5) * 32 - sand_col * 28
    m_col[..., 1] = 158 + (nm - 0.5) * 30 - sand_col * 26
    m_col[..., 2] = 145 + (nm - 0.5) * 28 - sand_col * 24
    _save_pbr("mortar", m_col, 0.84 + 0.12 * (1.0 - nm), mh_c, bump_strength=5.6)

    # 9. Bituminous Waterproofing Membrane (SBS oxidized asphalt / sheet)
    nbm = _fbm(S, (16, 64, 160, 256), (0.2, 0.25, 0.25, 0.30), seed=701)
    sheen = _fbm(S, (4, 12, 32), (0.5, 0.3, 0.2), seed=702)
    bm_col = np.zeros((size, size, 3), dtype=np.float32)
    bv = 36 + (nbm - 0.5) * 24 + (sheen - 0.5) * 10
    bm_col[..., 0] = bv
    bm_col[..., 1] = bv + 1
    bm_col[..., 2] = bv + 3
    _save_pbr("bitumen", bm_col, 0.38 + 0.30 * (1.0 - nbm), nbm, bump_strength=4.5)

    # 10. Mineral-Granule Cap Sheet (Lamina autoprotegida con gránulo pizarra)
    gran = _fbm(S, (64, 180, 256), (0.3, 0.35, 0.35), seed=710)
    gr_spheres, gr_t = _stamp_spheres(size, 2400, 1.4, 3.2, seed=711, prob_tint=0.5)
    gh = np.clip(0.4 * gran + 0.6 * gr_spheres, 0.0, 1.0)
    g_m = np.zeros((size, size, 3), dtype=np.float32)
    gv = 68 + (gran - 0.5) * 26 + gr_t * 20
    g_m[..., 0] = gv - 2
    g_m[..., 1] = gv
    g_m[..., 2] = gv + 4
    _save_pbr("membrane_granule", g_m, 0.78 + 0.14 * (1.0 - gh), gh, bump_strength=6.0)

    # 11. Geotextile CS (Non-woven Polypropylene felt with random fiber web)
    ng = _fbm(S, (12, 48, 140, 256), (0.25, 0.25, 0.25, 0.25), seed=801)
    g_col = np.zeros((size, size, 3), dtype=np.float32)
    g_col[..., 0] = 212 + (ng - 0.5) * 18
    g_col[..., 1] = 232 + (ng - 0.5) * 16
    g_col[..., 2] = 244 + (ng - 0.5) * 12
    _save_pbr("geotextile", g_col, 0.88 + 0.08 * ng, ng, bump_strength=3.0)

    # 12. XPS Thermal Insulation (Extruded Polystyrene micro-cellular skin)
    nx = _fbm(S, (8, 32, 110, 220), (0.35, 0.30, 0.20, 0.15), seed=901)
    x_col = np.zeros((size, size, 3), dtype=np.float32)
    x_col[..., 0] = 244 + (nx - 0.5) * 16
    x_col[..., 1] = 232 + (nx - 0.5) * 16
    x_col[..., 2] = 148 + (nx - 0.5) * 18
    _save_pbr("xps_foam", x_col, 0.62 + 0.16 * nx, nx, bump_strength=2.2)

    # 13. Fiberglass / Mineral Wool (Manta Fibra de Vidrio)
    nf1 = _fbm(S, (10, 40, 128, 256), (0.3, 0.3, 0.2, 0.2), seed=1001)
    wy, wx = np.meshgrid(np.linspace(0, 18 * np.pi, size), np.linspace(0, 18 * np.pi, size), indexing="ij")
    wave = 0.5 + 0.5 * np.sin(wx + 2.8 * np.sin(wy * 0.5) + nf1 * 4.5)
    fh = 0.50 * nf1 + 0.50 * wave
    f_col = np.zeros((size, size, 3), dtype=np.float32)
    f_col[..., 0] = 236 + (fh - 0.5) * 32
    f_col[..., 1] = 192 + (fh - 0.5) * 36
    f_col[..., 2] = 74 + (fh - 0.5) * 26
    _save_pbr("fiberglass", f_col, 0.88 + 0.08 * (1.0 - fh), fh, bump_strength=5.2)

    # 14. Brushed Stainless Steel / Cast Metal (Acero Inox / Cazoleta)
    nm_lin = np.repeat(_fbm(S, (12, 96, 256), (0.3, 0.35, 0.35), seed=1101)[:, :1], size, axis=1)
    nm_fin = _fbm(S, (24, 128), (0.5, 0.5), seed=1102)
    mh = 0.72 * nm_lin + 0.28 * nm_fin
    met = np.zeros((size, size, 3), dtype=np.float32)
    mv = 186 + (mh - 0.5) * 24
    met[..., 0] = mv - 2
    met[..., 1] = mv
    met[..., 2] = mv + 4
    _save_pbr("brushed_metal", met, 0.24 + 0.14 * (1.0 - mh), mh, bump_strength=2.0)

    # 15. Patinated Rolled Zinc (Cinc Canalones y Baberos)
    nz = _fbm(S, (6, 24, 96, 220), (0.3, 0.3, 0.2, 0.2), seed=1201)
    zh = 0.45 * nm_lin + 0.55 * nz
    zinc = np.zeros((size, size, 3), dtype=np.float32)
    zinc[..., 0] = 148 + (zh - 0.5) * 24
    zinc[..., 1] = 160 + (zh - 0.5) * 24
    zinc[..., 2] = 168 + (zh - 0.5) * 22
    _save_pbr("zinc", zinc, 0.34 + 0.16 * (1.0 - zh), zh, bump_strength=1.8)

    # 16. Zinc Prepatinado VMZ Quartz (Standing Seam Zinc)
    zvmz_b = _fbm(S, (8, 32, 128), (0.35, 0.35, 0.30), seed=1210)
    zvmz_h = 0.65 * nm_lin + 0.35 * zvmz_b
    zvmz = np.zeros((size, size, 3), dtype=np.float32)
    zvmz[..., 0] = 116 + (zvmz_h - 0.5) * 22
    zvmz[..., 1] = 124 + (zvmz_h - 0.5) * 22
    zvmz[..., 2] = 132 + (zvmz_h - 0.5) * 20
    _save_pbr("zinc_vmz", zvmz, 0.30 + 0.16 * (1.0 - zvmz_h), zvmz_h, bump_strength=2.2)

    # 17. Natural Roofing Slate (Pizarra Natural Exfoliada: stepped blue-charcoal cleavage plateaus)
    sl_broad = _fbm(S, (4, 10, 28), (0.50, 0.30, 0.20), seed=1401)
    foliation = _fbm(S, (8, 32, 128, 256), (0.3, 0.3, 0.25, 0.15), seed=1402)
    yy_s, xx_s = np.meshgrid(np.linspace(0, 4 * np.pi, size), np.linspace(0, 4 * np.pi, size), indexing="ij")
    strata = (foliation * 4.5 + 0.25 * np.sin(xx_s * 0.8 + yy_s * 0.25)) % 1.0
    stepped = np.floor(strata * 5.0) / 5.0 + 0.18 * (strata * 5.0 - np.floor(strata * 5.0))
    mica_fleck, _ = _stamp_spheres(size, 1400, 0.8, 1.6, seed=1403)
    sl_h = np.clip(0.55 * stepped + 0.35 * foliation + 0.10 * sl_broad, 0.0, 1.0)
    slate = np.zeros((size, size, 3), dtype=np.float32)
    base_sv = 48 + sl_broad * 14 + stepped * 16 + mica_fleck * 18
    slate[..., 0] = base_sv - 3
    slate[..., 1] = base_sv
    slate[..., 2] = base_sv + 7
    _save_pbr("slate_pizarra", slate, 0.44 + 0.26 * (1.0 - sl_h), sl_h, bump_strength=6.8)

    # 18. Treated Structural Pine Wood (Madera Pino Autoclave: crisp anisotropic timber grain & tight annual rings)
    w_warp = _fbm(S, (4, 12, 32), (0.55, 0.30, 0.15), seed=1501)
    wy_w, wx_w = np.meshgrid(np.linspace(0, 2.0 * np.pi, size), np.linspace(0, 26.0 * np.pi, size), indexing="ij")
    ring_phase = wx_w + 3.0 * w_warp + 0.5 * np.sin(wy_w)
    rings = np.power(0.5 + 0.5 * np.sin(ring_phase), 3.2)
    # High-frequency longitudinal fibers (fine vertical striations + slight local wobble)
    col_profile = np.mean(_fbm(S, (64, 192, 400), (0.25, 0.40, 0.35), seed=1502), axis=0, keepdims=True)
    fiber_fine = np.repeat(col_profile, size, axis=0)
    fiber_var = _fbm(S, (12, 48, 256), (0.3, 0.4, 0.3), seed=1503)
    fibers = 0.65 * fiber_fine + 0.35 * fiber_var
    wh = np.clip(0.45 * (1.0 - rings) + 0.55 * fibers, 0.0, 1.0)
    wood = np.zeros((size, size, 3), dtype=np.float32)
    wood[..., 0] = 198 - rings * 38 + (fibers - 0.5) * 32
    wood[..., 1] = 156 - rings * 36 + (fibers - 0.5) * 28
    wood[..., 2] = 102 - rings * 28 + (fibers - 0.5) * 20
    _save_pbr("wood_pine", wood, 0.58 + 0.22 * rings, wh, bump_strength=4.8)

    # 19. Artificial Stone / Limestone Coping (Piedra Artificial / Albardilla)
    st_n = _fbm(S, (8, 32, 110, 240), (0.3, 0.3, 0.2, 0.2), seed=1601)
    st_pits, st_m = _stamp_spheres(size, 1100, 1.0, 3.0, seed=1602, prob_tint=0.5)
    st_h = np.clip(0.70 * st_n - 0.30 * st_pits, 0.0, 1.0)
    stone = np.zeros((size, size, 3), dtype=np.float32)
    sv = 220 + (st_n - 0.5) * 20 - st_m * 28 - st_pits * 18
    stone[..., 0] = sv + 4
    stone[..., 1] = sv + 1
    stone[..., 2] = sv - 5
    _save_pbr("artificial_stone", stone, 0.68 + 0.18 * (1.0 - st_h), st_h, bump_strength=4.4)

    # 20. Precast Reinforced Concrete Paver (Losa Armada para Plots)
    pn = _fbm(S, (12, 48, 160), (0.35, 0.35, 0.30), seed=1701)
    p_sp, p_t = _stamp_spheres(size, 1400, 1.0, 3.4, seed=1702, prob_tint=0.6)
    ph = np.clip(0.55 * pn + 0.45 * p_sp, 0.0, 1.0)
    paver = np.zeros((size, size, 3), dtype=np.float32)
    paver[..., 0] = 178 + (pn - 0.5) * 22 - p_t * 28
    paver[..., 1] = 172 + (pn - 0.5) * 20 - p_t * 26
    paver[..., 2] = 162 + (pn - 0.5) * 18 - p_t * 24
    _save_pbr("concrete_paver", paver, 0.66 + 0.18 * (1.0 - ph), ph, bump_strength=4.8)

    # 21. Exterior Render / Plaster (Enfoscado / Revestimiento)
    nr = _fbm(S, (10, 40, 140, 256), (0.3, 0.3, 0.2, 0.2), seed=1301)
    r_sand, _ = _stamp_spheres(size, 1200, 0.9, 2.2, seed=1302)
    rh = np.clip(0.65 * nr + 0.35 * r_sand, 0.0, 1.0)
    ren = np.zeros((size, size, 3), dtype=np.float32)
    ren[..., 0] = 224 + (nr - 0.5) * 22 - r_sand * 10
    ren[..., 1] = 208 + (nr - 0.5) * 20 - r_sand * 10
    ren[..., 2] = 186 + (nr - 0.5) * 18 - r_sand * 8
    _save_pbr("render", ren, 0.78 + 0.14 * nr, rh, bump_strength=3.6)

    print(f"Generated 21 high-definition 1024x1024 PBR texture sets in {OUT_DIR}")


if __name__ == "__main__":
    generate_all(size=1024)
