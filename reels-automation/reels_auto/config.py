"""설정(.env) 읽기."""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
# 다른 프로그램이 남긴 Claude 로그인 토큰이 키 대신 쓰이지 않도록 제거
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip().strip('"').strip("'").strip()


@dataclass
class Config:
    anthropic_key: str = _get("ANTHROPIC_API_KEY")
    eleven_key: str = _get("ELEVENLABS_API_KEY")
    voice_id: str = _get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    eleven_model: str = _get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    ig_token: str = _get("IG_ACCESS_TOKEN")
    ig_user_id: str = _get("IG_USER_ID")
    graph_version: str = _get("IG_GRAPH_VERSION", "v23.0")
    channel_concept: str = _get("CHANNEL_CONCEPT", "유용한 정보를 짧고 재미있게 알려주는 계정")
    target_seconds: int = int(_get("TARGET_SECONDS", "35") or 35)
    font_path: str = _get("FONT_PATH")

    output_dir: Path = ROOT / "output"
    backgrounds_dir: Path = ROOT / "assets" / "backgrounds"


def require(cfg: Config, *names: str) -> None:
    """필요한 키가 비어 있으면 안내 후 종료."""
    labels = {
        "anthropic_key": "ANTHROPIC_API_KEY (대본 작성용 Claude 키)",
        "eleven_key": "ELEVENLABS_API_KEY (ElevenLabs 키)",
        "ig_token": "IG_ACCESS_TOKEN (인스타그램 토큰)",
        "ig_user_id": "IG_USER_ID (인스타그램 계정 ID)",
    }
    missing = [labels[n] for n in names if not getattr(cfg, n)]
    if missing:
        print("\n[설정 필요] .env 파일에 아래 값이 비어 있어요:")
        for m in missing:
            print("  -", m)
        print(f"\n.env 위치: {ROOT / '.env'}  (.env.example 을 복사해서 만드세요)")
        sys.exit(1)
