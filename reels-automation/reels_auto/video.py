"""배경 + 음성 + 자막을 합쳐 세로(1080x1920) 릴스 영상 만들기."""
import math
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

WHITE = (255, 255, 255, 255)
YELLOW = (255, 214, 0, 255)
BLACK = (0, 0, 0, 255)

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


def _layout(draw, words, font, max_w):
    """(단어, 강조여부) 목록을 줄 단위로 나누기."""
    space = draw.textlength(" ", font=font)
    lines, line, line_w = [], [], 0.0
    for word, hl in words:
        w = draw.textlength(word, font=font)
        if line and line_w + space + w > max_w:
            lines.append((line, line_w))
            line, line_w = [], 0.0
        line_w += (space if line else 0) + w
        line.append((word, hl, w))
    if line:
        lines.append((line, line_w))
    return lines, space


def _words_png(cfg, words, path, size, stroke, box_color=None, text_color=WHITE, pad=14):
    """단어별 색(강조=노랑)을 지원하는 가운데 정렬 텍스트 이미지."""
    font = _font(cfg, size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, space = _layout(probe, words, font, W - 140)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + size // 6
    width = math.ceil(max(lw for _, lw in lines)) + stroke * 2 + pad * 2
    height = line_h * len(lines) + stroke * 2 + pad * 2
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if box_color:
        d.rounded_rectangle([0, 0, width - 1, height - 1], radius=26, fill=box_color)
    y = pad + stroke
    for line, lw in lines:
        x = (width - lw) / 2
        for word, hl, w in line:
            d.text((x, y), word, font=font, fill=YELLOW if hl else text_color,
                   stroke_width=stroke, stroke_fill=BLACK)
            x += w + space
        y += line_h
    img.save(path)


def _group_captions(words, max_chars=13):
    """단어들을 화면에 한 번에 보여줄 짧은 자막 덩어리로 묶기.
    words: (단어, 시작, 끝, 강조여부)"""
    groups, cur = [], []
    for w in words:
        text = " ".join(x[0] for x in cur + [w])
        if cur and len(text) > max_chars:
            groups.append(cur)
            cur = []
        cur.append(w)
        if w[0][-1] in ".?!,":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    caps = []
    for i, g in enumerate(groups):
        start = g[0][1]
        end = groups[i + 1][0][1] if i + 1 < len(groups) else g[-1][2] + 0.5
        caps.append(([(x[0].rstrip(".,"), x[3]) for x in g], start, end))
    return caps


def _gradient_bg(path: Path):
    # 신뢰감 있는 어두운 톤 위주 (밝은 자막이 잘 보이도록)
    palettes = [((12, 20, 45), (35, 60, 120)), ((10, 10, 10), (55, 55, 70)),
                ((20, 30, 30), (20, 90, 90)), ((40, 10, 20), (110, 30, 50)),
                ((15, 25, 60), (70, 40, 110))]
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


def _scene_times(words, n_images, dur):
    """문장 단위로 장면(이미지) 전환 시점 나누기."""
    sent_starts, new_sent = [], True
    for w, st, _e in words:
        if new_sent:
            sent_starts.append(st)
        new_sent = w[-1] in ".?!"
    if not sent_starts:
        sent_starts = [0.0]
    n = max(1, min(n_images, len(sent_starts)))
    cuts = [0.0] + [sent_starts[round(i * len(sent_starts) / n)] for i in range(1, n)] + [dur]
    return [(cuts[i], cuts[i + 1]) for i in range(n)]


def render(cfg: Config, title: str, narration, work: Path, out_path: Path,
           highlights: list[bool] | None = None, scene_images: list[Path] | None = None) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    dur = narration.duration
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    bw, bh = int(W * 1.12), int(H * 1.12)

    if scene_images:
        # 문장에 맞춰 이미지가 바뀌는 장면 모드 (천천히 움직이는 효과)
        spans = _scene_times(narration.words, len(scene_images), dur)
        parts, any_landscape = [], False
        for i, (img, (s0, s1)) in enumerate(zip(scene_images, spans)):
            seg = max(0.5, s1 - s0)
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{seg:.3f}", "-i", str(img)]
            xs = f"(in_w-{W})*t/{seg:.2f}" if i % 2 == 0 else f"(in_w-{W})*(1-t/{seg:.2f})"
            with Image.open(img) as im:
                landscape = im.width > im.height
            if landscape:
                # 가로 이미지: 흐린 배경 위에 선명한 이미지를 가운데 위쪽에 배치
                any_landscape = True
                parts.append(f"[{i}:v]split[a{i}][b{i}];"
                             f"[a{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                             f"boxblur=30:2,eq=brightness=-0.3[bg{i}];"
                             f"[b{i}]scale={int(W * 1.12)}:-2,crop={W}:ih:x='{xs}':y=0[fg{i}];"
                             f"[bg{i}][fg{i}]overlay=x=0:y=540,setsar=1,format=yuv420p[s{i}]")
            else:
                parts.append(f"[{i}:v]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                             f"crop={W}:{H}:x='{xs}':y='(in_h-{H})/2',setsar=1,"
                             f"eq=brightness=-0.12:saturation=0.95,format=yuv420p[s{i}]")
        n_bg = len(spans)
        concat = "".join(f"[s{i}]" for i in range(n_bg))
        bg_filter = ";".join(parts) + f";{concat}concat=n={n_bg}:v=1:a=0[v0]"
    else:
        any_landscape = False
        bg = _pick_background(cfg, work)
        is_video = bg.suffix.lower() in VIDEO_EXT
        # 사용자 배경은 어둡게 눌러서 글자가 확 튀게
        dim = "eq=brightness=-0.18:saturation=0.9" if bg.parent == cfg.backgrounds_dir else "null"
        n_bg = 1
        if is_video:
            cmd += ["-stream_loop", "-1", "-i", str(bg)]
            bg_filter = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                         f"fps={FPS},setsar=1,{dim}[v0]")
        else:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-i", str(bg)]
            bg_filter = (f"[0:v]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                         f"crop={W}:{H}:x='(in_w-{W})*t/{dur:.2f}':y='(in_h-{H})/2',"
                         f"setsar=1,{dim}[v0]")
    audio_idx = n_bg
    cmd += ["-i", str(narration.audio_path)]

    # 제목: 상단 노란 박스 + 검은 글씨
    overlays = []  # (png, y식, start, end)
    title_png = work / "title.png"
    _words_png(cfg, [(w, False) for w in title.split()], title_png, 76, stroke=0,
               box_color=YELLOW, text_color=BLACK, pad=34)
    overlays.append((title_png, "220", None, None))

    words = narration.words
    if highlights and len(highlights) == len(words):
        words4 = [(w, s, e, hl) for (w, s, e), hl in zip(words, highlights)]
    else:
        words4 = [(w, s, e, False) for (w, s, e) in words]
    for i, (cap_words, s, e) in enumerate(_group_captions(words4)):
        p = work / f"cap_{i:03d}.png"
        _words_png(cfg, cap_words, p, 112, stroke=10)
        overlays.append((p, "1420-h/2" if any_landscape else "1000-h/2", s, e))

    filters, last = [bg_filter], "v0"
    for i, (png, y, s, e) in enumerate(overlays):
        cmd += ["-i", str(png)]
        enable = f":enable='between(t,{s:.3f},{e:.3f})'" if s is not None else ""
        filters.append(f"[{last}][{i + audio_idx + 1}:v]overlay=x=(W-w)/2:y={y}{enable}[v{i + 1}]")
        last = f"v{i + 1}"

    cmd += ["-filter_complex", ";".join(filters), "-map", f"[{last}]", "-map", f"{audio_idx}:a",
            "-t", f"{dur:.2f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"영상 만들기 실패:\n{result.stderr[-1500:]}")
    return out_path
