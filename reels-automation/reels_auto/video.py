"""배경 + 음성 + 자막을 합쳐 세로(1080x1920) 릴스 영상 만들기."""
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from .config import Config

W, H = 1080, 1920
FPS = 30
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}

FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgunbd.ttf",   # 맑은 고딕 Bold (Windows 기본)
    "C:/Windows/Fonts/malgun.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
]


def _font(cfg: Config, size: int) -> ImageFont.FreeTypeFont:
    for path in ([cfg.font_path] if cfg.font_path else []) + FONT_CANDIDATES:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    print("[경고] 한글 폰트를 찾지 못했어요. .env 에 FONT_PATH 를 지정하세요.", file=sys.stderr)
    return ImageFont.load_default(size)


def _wrap(draw, text, font, max_w):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\n".join(lines)


def _text_png(cfg, text, path, size, box=False):
    font = _font(cfg, size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    text = _wrap(probe, text, font, W - 160)
    stroke = 0 if box else max(4, size // 10)
    l, t, r, b = probe.multiline_textbbox((0, 0), text, font=font, stroke_width=stroke,
                                          align="center", spacing=size // 4)
    pad = 36 if box else 10
    img = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if box:
        d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=28, fill=(0, 0, 0, 170))
    d.multiline_text((pad - l, pad - t), text, font=font, fill=(255, 255, 255, 255),
                     stroke_width=stroke, stroke_fill=(0, 0, 0, 255),
                     align="center", spacing=size // 4)
    img.save(path)


def _group_captions(words, max_chars=12):
    """단어들을 화면에 한 번에 보여줄 짧은 자막 덩어리로 묶기."""
    groups, cur = [], []
    for w in words:
        text = " ".join(x[0] for x in cur + [w])
        if cur and len(text) > max_chars:
            groups.append(cur)
            cur = []
        cur.append(w)
        if w[0][-1] in ".?!":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    caps = []
    for i, g in enumerate(groups):
        start = g[0][1]
        end = groups[i + 1][0][1] if i + 1 < len(groups) else g[-1][2] + 0.4
        caps.append((" ".join(x[0] for x in g), start, end))
    return caps


def _gradient_bg(path: Path):
    palettes = [((255, 94, 98), (255, 195, 113)), ((67, 97, 238), (76, 201, 240)),
                ((17, 153, 142), (56, 239, 125)), ((142, 45, 226), (74, 0, 224)),
                ((252, 70, 107), (63, 94, 251)), ((30, 30, 30), (90, 90, 110))]
    (r1, g1, b1), (r2, g2, b2) = random.choice(palettes)
    w, h = int(W * 1.15), int(H * 1.15)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(r1 + (r2 - r1) * k), int(g1 + (g2 - g1) * k), int(b1 + (b2 - b1) * k)))
    img.save(path)


def _pick_background(cfg: Config, work: Path) -> Path:
    files = [p for p in cfg.backgrounds_dir.glob("*") if p.suffix.lower() in IMAGE_EXT | VIDEO_EXT]
    if files:
        return random.choice(files)
    bg = work / "background.png"
    _gradient_bg(bg)
    return bg


def render(cfg: Config, title: str, narration, work: Path, out_path: Path) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    dur = narration.duration
    bg = _pick_background(cfg, work)
    is_video = bg.suffix.lower() in VIDEO_EXT

    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    if is_video:
        cmd += ["-stream_loop", "-1", "-i", str(bg)]
        bg_filter = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                     f"fps={FPS},setsar=1,eq=brightness=-0.06[v0]")
    else:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", str(bg)]
        bw, bh = int(W * 1.15), int(H * 1.15)
        # 이미지는 천천히 옆으로 움직이는 효과
        bg_filter = (f"[0:v]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                     f"crop={W}:{H}:x='(in_w-{W})*t/{dur:.2f}':y='(in_h-{H})/2',"
                     f"setsar=1,eq=brightness=-0.06[v0]")
    cmd += ["-i", str(narration.audio_path)]

    overlays = []  # (png, y, start, end)
    title_png = work / "title.png"
    _text_png(cfg, title, title_png, 78, box=True)
    overlays.append((title_png, 240, None, None))
    for i, (text, s, e) in enumerate(_group_captions(narration.words)):
        p = work / f"cap_{i:03d}.png"
        _text_png(cfg, text, p, 86)
        overlays.append((p, 1180, s, e))

    filters, last = [bg_filter], "v0"
    for i, (png, y, s, e) in enumerate(overlays):
        cmd += ["-i", str(png)]
        enable = f":enable='between(t,{s:.3f},{e:.3f})'" if s is not None else ""
        filters.append(f"[{last}][{i + 2}:v]overlay=x=(W-w)/2:y={y}{enable}[v{i + 1}]")
        last = f"v{i + 1}"

    cmd += ["-filter_complex", ";".join(filters), "-map", f"[{last}]", "-map", "1:a",
            "-t", f"{dur:.2f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"영상 만들기 실패:\n{result.stderr[-1500:]}")
    return out_path
