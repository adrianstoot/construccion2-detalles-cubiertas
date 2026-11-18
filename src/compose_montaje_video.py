"""
Composites the 900 rendered 3D frames (1280x864 @ 30 fps = 30.00 s) with the progressive
2D CAD technical sections, active phase inspector card, and 10-step assembly timeline
into a Full HD 1920x1080 H.264 MP4 video:
  d:\C2\renders\detalle1_montaje_30s.mp4
Also writes d:\C2\data\montaje_phases.json for the interactive Web App sequencer.
"""

import json
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from generate_montaje_2d import PHASES_DETALLE1


FRAMES_3D_DIR = r"d:\C2\scratch_montaje\frames3d"
FRAMES_2D_DIR = r"d:\C2\scratch_montaje\cad2d_phases"
OUT_MP4 = r"d:\C2\renders\detalle1_montaje_30s.mp4"
OUT_PHASES_JSON = r"d:\C2\data\montaje_phases.json"

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = 900


def load_font(name, size):
    candidates = [
        os.path.join(r"C:\Windows\Fonts", name),
        os.path.join(r"C:\Windows\Fonts", "segoeui.ttf"),
        os.path.join(r"C:\Windows\Fonts", "arial.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def get_active_phase(t_sec):
    for ph in PHASES_DETALLE1:
        if ph["t_start"] <= t_sec < ph["t_end"]:
            return ph["phase"], False
    return 10, True  # Final 27.0-30.0 s finished showcase


def build_static_panel_overlays():
    """
    Pre-renders the 11 right-hand CAD+HUD static state panels (phase 1..10 active + state 11 finished)
    so per-frame compositing across 900 frames takes milliseconds!
    """
    f_kicker = load_font("consolab.ttf", 14)
    f_bold_lg = load_font("segoeuib.ttf", 24)
    f_bold_md = load_font("segoeuib.ttf", 18)
    f_bold_sm = load_font("segoeuib.ttf", 14)
    f_reg_sm = load_font("segoeui.ttf", 15)
    f_mono_sm = load_font("consolab.ttf", 13)
    f_mono_xs = load_font("consola.ttf", 12)

    # Load and fit progressive 2D images (01..10) into box (640 x 470)
    cad_imgs = {}
    for p_idx in range(1, 11):
        im2 = Image.open(os.path.join(FRAMES_2D_DIR, f"cad2d_phase_{p_idx:02d}.png")).convert("RGB")
        im2.thumbnail((636, 468), Image.Resampling.LANCZOS)
        cad_imgs[p_idx] = im2

    states = {}
    for st_key in range(1, 12):  # 1..10 active phase, 11 = finished state
        finished = (st_key == 11)
        active_ph = 10 if finished else st_key
        ph_obj = PHASES_DETALLE1[active_ph - 1]

        panel = Image.new("RGB", (680, H), (250, 249, 246))
        d = ImageDraw.Draw(panel)
        d.line([(0, 0), (0, H)], fill=(212, 206, 196), width=2)

        # 1. Top Active Phase Card (Y: 16..248)
        d.rounded_rectangle([20, 18, 660, 242], radius=10, fill=(255, 255, 255), outline=(219, 214, 204), width=1)
        badge_col = (27, 107, 69) if finished else (184, 74, 50)
        badge_bg = (234, 244, 238) if finished else (251, 238, 233)
        badge_txt = "MONTAJE COMPLETADO · 10 / 10 FASES" if finished else f"FASE EN EJECUCIÓN · {active_ph:02d} / 10"
        d.rounded_rectangle([36, 34, 330, 60], radius=13, fill=badge_bg, outline=badge_col, width=1)
        d.text((48, 40), badge_txt, fill=badge_col, font=f_mono_sm)

        # Code + thickness pill
        d.rounded_rectangle([346, 34, 490, 60], radius=6, fill=(242, 239, 232), outline=(219, 214, 204), width=1)
        d.rectangle([346, 34, 353, 60], fill=hex_rgb(ph_obj["color"]))
        d.text((362, 40), ph_obj["code"], fill=(22, 25, 29), font=f_mono_sm)

        title_txt = "Detalle IVE Completo (3D + 2D Acabado)" if finished else ph_obj["title"]
        d.text((36, 74), title_txt, fill=(22, 25, 29), font=f_bold_lg)

        thick_txt = "Espesor total: 429 mm + Peto 820 mm" if finished else f"Espesor / Cota: {ph_obj['thickness']}"
        d.text((36, 108), thick_txt, fill=(27, 107, 69), font=f_mono_sm)

        desc_txt = (
            "Conjunto constructivo finalizado: forjado unidireccional SR, peto LHD con junta EPS, pendiente 2,5% FP, barrera BV, aislamiento XPS, impermeabilización SBS con entrega 200 mm, capa separadora CS y pavimento cerámico fijo con rodapié."
            if finished
            else ph_obj["desc"]
        )
        lines = wrap_text(d, desc_txt, f_reg_sm, 604)
        for li, line in enumerate(lines[:4]):
            d.text((36, 134 + li * 22), line, fill=(78, 86, 97), font=f_reg_sm)

        # 2. Middle Synchronized 2D CAD Panel (Y: 256..776)
        d.rounded_rectangle([20, 256, 660, 774], radius=10, fill=(255, 255, 255), outline=(219, 214, 204), width=1)
        d.rectangle([21, 257, 659, 294], fill=(245, 243, 238))
        d.line([(20, 294), (660, 294)], fill=(219, 214, 204), width=1)
        d.text((36, 267), "SECCIÓN TÉCNICA 2D SINCRONIZADA · E 1:5 (mm)", fill=(22, 25, 29), font=f_mono_sm)
        st_lbl = "PLANO 2D ACABADO 100%" if finished else f"PROGRESO 2D · FASE {active_ph:02d}"
        st_col = (27, 107, 69) if finished else (43, 84, 110)
        d.text((488, 268), st_lbl, fill=st_col, font=f_mono_xs)

        im2 = cad_imgs[active_ph]
        ox = 20 + (640 - im2.width) // 2
        oy = 298 + (472 - im2.height) // 2
        panel.paste(im2, (ox, oy))

        # 3. Bottom 10-Phase Checklist (Y: 788..1062)
        d.rounded_rectangle([20, 788, 660, 1062], radius=10, fill=(255, 255, 255), outline=(219, 214, 204), width=1)
        d.text((36, 800), "ORDEN CRONOLÓGICO DE MONTAJE EN OBRA", fill=(123, 131, 143), font=f_mono_xs)
        for idx, ph in enumerate(PHASES_DETALLE1):
            col_i = idx // 5
            row_i = idx % 5
            rx = 34 + col_i * 312
            ry = 826 + row_i * 45
            is_done = finished or (ph["phase"] < active_ph)
            is_cur = (not finished) and (ph["phase"] == active_ph)

            bg_r = (253, 244, 241) if is_cur else ((244, 250, 246) if is_done else (248, 247, 244))
            bd_r = (184, 74, 50) if is_cur else ((185, 222, 201) if is_done else (225, 221, 212))
            d.rounded_rectangle([rx, ry, rx + 300, ry + 38], radius=6, fill=bg_r, outline=bd_r, width=2 if is_cur else 1)

            dot_col = (184, 74, 50) if is_cur else ((27, 107, 69) if is_done else (175, 180, 188))
            d.ellipse([rx + 8, ry + 11, rx + 24, ry + 27], fill=dot_col)
            mark = "✓" if is_done else ("▶" if is_cur else f"{ph['phase']}")
            d.text((rx + 12, ry + 11), mark if not is_done and not is_cur else "", fill=(255, 255, 255), font=f_mono_xs)
            if is_done:
                d.text((rx + 12, ry + 12), "OK", fill=(255, 255, 255), font=load_font("consolab.ttf", 9))
            elif is_cur:
                d.text((rx + 13, ry + 11), ">", fill=(255, 255, 255), font=load_font("consolab.ttf", 11))

            t_col = (22, 25, 29) if (is_cur or is_done) else (130, 136, 145)
            d.text((rx + 32, ry + 5), f"{ph['phase']:02d}. {ph['code']}", fill=t_col, font=f_mono_sm)
            short_t = ph["title"][:34] + ("…" if len(ph["title"]) > 34 else "")
            d.text((rx + 32, ry + 20), short_t, fill=(78, 86, 97) if (is_cur or is_done) else (155, 160, 168), font=load_font("segoeui.ttf", 11))

        states[st_key] = panel
    return states


def compose_video():
    os.makedirs(os.path.dirname(OUT_PHASES_JSON), exist_ok=True)
    with open(OUT_PHASES_JSON, "w", encoding="utf-8") as f:
        json.dump(PHASES_DETALLE1, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT_PHASES_JSON}")

    panel_states = build_static_panel_overlays()
    f_hdr = load_font("segoeuib.ttf", 19)
    f_kick = load_font("consolab.ttf", 13)
    f_timer = load_font("consolab.ttf", 18)
    f_pill = load_font("consolab.ttf", 12)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(os.path.dirname(OUT_MP4), exist_ok=True)
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "-",
        "-an",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        OUT_MP4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # Pre-build clean left header & static background frame
    base_left = Image.new("RGB", (1240, H), (242, 240, 235))
    dl = ImageDraw.Draw(base_left)
    dl.rectangle([0, 0, 1240, 74], fill=(23, 26, 31))
    dl.rounded_rectangle([24, 16, 108, 58], radius=6, fill=(184, 74, 50))
    dl.text((34, 29), "UPV · C2", fill=(255, 255, 255), font=f_kick)
    dl.text((124, 15), "CONSTRUCCIÓN II · CARTILLAS IVE · TIPOLOGÍA 1", fill=(244, 164, 143), font=f_kick)
    dl.text((124, 34), "Azotea Transitable · No Ventilada · Convencional · Pavimento Fijo", fill=(255, 255, 255), font=f_hdr)

    # Bottom scrubber tray
    dl.rectangle([0, 944, 1240, H], fill=(23, 26, 31))

    for f_idx in range(TOTAL_FRAMES):
        t_sec = f_idx / FPS
        active_ph, finished = get_active_phase(t_sec)
        st_key = 11 if finished else active_ph

        canvas = Image.new("RGB", (W, H))
        canvas.paste(base_left, (0, 0))
        canvas.paste(panel_states[st_key], (1240, 0))

        # Load 3D frame (1280x864) -> resize cleanly to (1240x837) and center in Y: 74..944
        f_path = os.path.join(FRAMES_3D_DIR, f"frame_{f_idx:04d}.png")
        im3 = Image.open(f_path).convert("RGB").resize((1240, 837), Image.Resampling.BILINEAR)
        canvas.paste(im3, (0, 90))

        draw = ImageDraw.Draw(canvas)
        # Timer top right of left bar
        draw.text((1045, 27), f"{t_sec:05.2f}s / 30.00s", fill=(230, 234, 240), font=f_timer)

        # Bottom timeline bar + 10 phase pills
        bar_x0, bar_x1, bar_y = 28, 1212, 966
        draw.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 12], radius=6, fill=(45, 50, 59))
        prog_w = int((bar_x1 - bar_x0) * (f_idx / max(1, TOTAL_FRAMES - 1)))
        bar_col = (27, 138, 86) if finished else (184, 74, 50)
        if prog_w > 6:
            draw.rounded_rectangle([bar_x0, bar_y, bar_x0 + prog_w, bar_y + 12], radius=6, fill=bar_col)

        # 10 phase segment pills below progress bar
        pw = 112
        gap = 7
        for pi, ph in enumerate(PHASES_DETALLE1):
            px = 28 + pi * (pw + gap)
            py = 994
            done_p = finished or (ph["phase"] < active_ph)
            cur_p = (not finished) and (ph["phase"] == active_ph)
            fill_p = (27, 107, 69) if done_p else ((184, 74, 50) if cur_p else (38, 43, 51))
            out_p = (74, 179, 126) if done_p else ((244, 164, 143) if cur_p else (62, 68, 79))
            draw.rounded_rectangle([px, py, px + pw, py + 48], radius=6, fill=fill_p, outline=out_p, width=2 if cur_p else 1)
            short_c = ph["code"].split("·")[0].strip()
            draw.text((px + 10, py + 7), f"FASE {ph['phase']:02d}", fill=(255, 255, 255) if (cur_p or done_p) else (150, 158, 168), font=f_pill)
            draw.text((px + 10, py + 24), ph["code"][:12], fill=(240, 244, 248) if (cur_p or done_p) else (118, 125, 136), font=f_pill)

        proc.stdin.write(canvas.tobytes())
        if f_idx % 150 == 0:
            print(f"Composited {f_idx}/{TOTAL_FRAMES} frames...", flush=True)

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg exited with code {rc}")
    print(f"Video encoded cleanly: {OUT_MP4} ({os.path.getsize(OUT_MP4)} bytes)")


if __name__ == "__main__":
    compose_video()
