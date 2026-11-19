"""릴스 자동화 실행 파일.

사용 예:
  python reels.py check                       설정 확인
  python reels.py make "겨울철 전기요금 아끼는 법"   릴스 1개 만들기
  python reels.py make "주제" --upload         만들고 인스타그램에 바로 올리기
  python reels.py make --topics topics.txt    파일의 주제들로 여러 개 만들기
  python reels.py upload output\\폴더이름      만들어 둔 릴스 올리기
  python reels.py voices                      쓸 수 있는 목소리 목록
  python reels.py ig-check                    인스타그램 계정 ID 찾기
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

from reels_auto.config import Config, require  # noqa: E402


def _slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "_", text).strip("_")[:30] or "reel"


def make_one(cfg: Config, topic: str, upload: bool) -> Path:
    from reels_auto.script_writer import write_script
    from reels_auto.tts import synthesize
    from reels_auto.video import render

    work = cfg.output_dir / f"{datetime.now():%Y%m%d-%H%M%S}_{_slug(topic)}"
    (work / "frames").mkdir(parents=True, exist_ok=True)

    print(f"\n▶ 주제: {topic}")
    print("  1/3 대본 작성 중...")
    script = write_script(cfg, topic)
    caption = f"{script.caption}\n\n{' '.join(script.hashtags)}"
    (work / "script.json").write_text(json.dumps(script.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "caption.txt").write_text(caption, encoding="utf-8")
    print(f"      제목: {script.title}")

    print("  2/3 음성 만드는 중 (ElevenLabs)...")
    narration = synthesize(cfg, script.narration, work / "voice.mp3")
    print(f"      길이: {narration.duration:.1f}초")

    print("  3/3 영상 편집 중...")
    video = render(cfg, script.title, narration, work / "frames", work / "reel.mp4")
    print(f"  ✅ 완성: {video}")

    if upload:
        do_upload(cfg, work)
    return work


def do_upload(cfg: Config, folder: Path) -> None:
    from reels_auto.instagram import upload_reel

    require(cfg, "ig_token", "ig_user_id")
    folder = Path(folder)
    video, cap = folder / "reel.mp4", folder / "caption.txt"
    if not video.exists():
        sys.exit(f"영상이 없어요: {video}")
    print("  ⏫ 인스타그램 업로드 중... (몇 분 걸릴 수 있어요)")
    link = upload_reel(cfg, video, cap.read_text(encoding="utf-8") if cap.exists() else "")
    (folder / "uploaded.txt").write_text(link, encoding="utf-8")
    print(f"  ✅ 업로드 완료: {link}")


def cmd_check(cfg: Config) -> None:
    import imageio_ffmpeg
    from reels_auto.video import _font

    ok = lambda b: "✅" if b else "❌"  # noqa: E731
    print(f"{ok(cfg.anthropic_key)} ANTHROPIC_API_KEY (대본)")
    print(f"{ok(cfg.eleven_key)} ELEVENLABS_API_KEY (음성)")
    print(f"{ok(cfg.ig_token and cfg.ig_user_id)} IG_ACCESS_TOKEN / IG_USER_ID (업로드 - 선택)")
    print(f"✅ ffmpeg: {imageio_ffmpeg.get_ffmpeg_exe()}")
    path = getattr(_font(cfg, 40), "path", None)
    print(f"{ok(isinstance(path, str))} 한글 폰트: {path if isinstance(path, str) else '없음 (.env 에 FONT_PATH 지정)'}")


def cmd_voices(cfg: Config) -> None:
    from reels_auto.tts import list_voices

    require(cfg, "eleven_key")
    for v in list_voices(cfg):
        labels = v.get("labels", {})
        print(f"{v['voice_id']}  {v['name']}  [{labels.get('language', '')} {labels.get('gender', '')}]")
    print("\n원하는 voice_id 를 .env 의 ELEVENLABS_VOICE_ID 에 넣으세요.")
    print("더 많은 한국어 목소리: https://elevenlabs.io/app/voice-library (Add to My Voices 후 다시 실행)")


def cmd_ig_check(cfg: Config) -> None:
    from reels_auto.instagram import find_ig_accounts

    require(cfg, "ig_token")
    accounts = find_ig_accounts(cfg)
    if not accounts:
        print("연결된 페이스북 페이지가 없어요. README의 '인스타그램 연동'을 확인하세요.")
    for a in accounts:
        if a["ig_id"]:
            print(f"페이지 '{a['page']}' → 인스타 @{a['username']}  IG_USER_ID={a['ig_id']}")
        else:
            print(f"페이지 '{a['page']}' → 연결된 인스타그램 비즈니스 계정 없음")


def main() -> None:
    p = argparse.ArgumentParser(description="인스타그램 릴스 자동화")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make", help="릴스 만들기")
    m.add_argument("topic", nargs="?", help="릴스 주제")
    m.add_argument("--topics", help="주제 목록 파일 (한 줄에 하나)")
    m.add_argument("--upload", action="store_true", help="만든 뒤 인스타그램에 바로 올리기")
    u = sub.add_parser("upload", help="만들어 둔 릴스 올리기")
    u.add_argument("folder", help="output 안의 폴더 경로")
    sub.add_parser("check", help="설정 확인")
    sub.add_parser("voices", help="목소리 목록")
    sub.add_parser("ig-check", help="인스타그램 계정 ID 찾기")
    args = p.parse_args()
    cfg = Config()

    try:
        if args.cmd == "make":
            topics = [args.topic] if args.topic else []
            if args.topics:
                topics += [t.strip() for t in Path(args.topics).read_text(encoding="utf-8").splitlines() if t.strip()]
            if not topics:
                sys.exit('주제를 입력하세요. 예: python reels.py make "아침 루틴 5가지"')
            require(cfg, "anthropic_key", "eleven_key")
            for t in topics:
                make_one(cfg, t, args.upload)
        elif args.cmd == "upload":
            do_upload(cfg, Path(args.folder))
        elif args.cmd == "check":
            cmd_check(cfg)
        elif args.cmd == "voices":
            cmd_voices(cfg)
        elif args.cmd == "ig-check":
            cmd_ig_check(cfg)
    except RuntimeError as e:
        sys.exit(f"\n❌ {e}")


if __name__ == "__main__":
    main()
