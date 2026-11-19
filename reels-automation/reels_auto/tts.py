"""ElevenLabs로 내레이션 음성 + 글자별 타이밍 생성."""
import base64
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import Config

API = "https://api.elevenlabs.io/v1"


@dataclass
class Narration:
    audio_path: Path
    duration: float
    # (단어, 시작초, 끝초)
    words: list[tuple[str, float, float]]


def _words_from_alignment(alignment: dict) -> list[tuple[str, float, float]]:
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    words, buf, w_start, w_end = [], "", None, 0.0
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if buf:
                words.append((buf, w_start, w_end))
            buf, w_start = "", None
            continue
        if w_start is None:
            w_start = s
        buf += ch
        w_end = e
    if buf:
        words.append((buf, w_start, w_end))
    return words


def synthesize(cfg: Config, text: str, out_path: Path) -> Narration:
    resp = requests.post(
        f"{API}/text-to-speech/{cfg.voice_id}/with-timestamps",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": cfg.eleven_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": cfg.eleven_model,
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.2},
        },
        timeout=180,
    )
    if resp.status_code != 200:
        hint = ""
        if resp.status_code == 402:
            hint = (" → 무료 요금제에서는 Voice Library 목소리를 API로 못 써요. .env 의 "
                    "ELEVENLABS_VOICE_ID 를 기본 목소리(예: EXAVITQu4vr4xnSDxMaL)로 바꾸거나 유료 요금제로 올리세요.")
        elif resp.status_code == 401:
            hint = " → ELEVENLABS_API_KEY 를 확인하세요."
        elif "voice" in resp.text.lower():
            hint = (" → 목소리를 쓸 수 없어요. ElevenLabs Voice Library에서 해당 목소리를 "
                    "'My Voices'에 추가하거나, python reels.py voices 로 다른 목소리를 고르세요.")
        raise RuntimeError(f"ElevenLabs 오류 {resp.status_code}: {resp.text[:300]}{hint}")

    data = resp.json()
    out_path.write_bytes(base64.b64decode(data["audio_base64"]))
    # 원문 글자 기준 타이밍 사용 (normalized 쪽은 한국어가 영어 발음 표기로 바뀔 수 있음)
    alignment = data.get("alignment") or data["normalized_alignment"]
    words = _words_from_alignment(alignment)
    duration = (alignment["character_end_times_seconds"][-1] if words else 0) + 0.6
    return Narration(out_path, duration, words)


def list_voices(cfg: Config) -> list[dict]:
    resp = requests.get(f"{API}/voices", headers={"xi-api-key": cfg.eleven_key}, timeout=60)
    resp.raise_for_status()
    return resp.json().get("voices", [])
