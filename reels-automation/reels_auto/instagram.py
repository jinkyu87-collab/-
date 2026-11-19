"""인스타그램 Graph API로 릴스 업로드 (파일 직접 업로드 방식, 별도 호스팅 불필요)."""
import time
from pathlib import Path

import requests

from .config import Config


def _graph(cfg: Config) -> str:
    return f"https://graph.facebook.com/{cfg.graph_version}"


def _check(resp: requests.Response, step: str) -> dict:
    try:
        data = resp.json()
    except ValueError:
        data = {"raw": resp.text[:300]}
    if resp.status_code != 200 or "error" in data:
        msg = data.get("error", {}).get("message", data) if isinstance(data, dict) else data
        raise RuntimeError(f"인스타그램 {step} 실패 ({resp.status_code}): {msg}")
    return data


def upload_reel(cfg: Config, video: Path, caption: str, share_to_feed: bool = True) -> str:
    base = _graph(cfg)
    # 1) 업로드용 컨테이너 생성
    data = _check(requests.post(f"{base}/{cfg.ig_user_id}/media", data={
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "share_to_feed": "true" if share_to_feed else "false",
        "access_token": cfg.ig_token,
    }, timeout=60), "컨테이너 생성")
    container_id, upload_uri = data["id"], data["uri"]

    # 2) 영상 파일 전송
    size = video.stat().st_size
    with open(video, "rb") as f:
        _check(requests.post(upload_uri, data=f, headers={
            "Authorization": f"OAuth {cfg.ig_token}",
            "offset": "0",
            "file_size": str(size),
        }, timeout=600), "영상 전송")

    # 3) 인스타그램 쪽 처리 완료 대기 (최대 약 10분)
    for _ in range(60):
        st = _check(requests.get(f"{base}/{container_id}", params={
            "fields": "status_code,status", "access_token": cfg.ig_token}, timeout=60), "상태 확인")
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"인스타그램 영상 처리 실패: {st.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError("인스타그램 처리 시간이 너무 오래 걸려요. 잠시 후 upload 명령으로 다시 시도하세요.")

    # 4) 게시
    pub = _check(requests.post(f"{base}/{cfg.ig_user_id}/media_publish", data={
        "creation_id": container_id, "access_token": cfg.ig_token}, timeout=60), "게시")
    media_id = pub["id"]
    link = requests.get(f"{base}/{media_id}", params={
        "fields": "permalink", "access_token": cfg.ig_token}, timeout=60).json().get("permalink", "")
    return link or media_id


def find_ig_accounts(cfg: Config) -> list[dict]:
    """토큰으로 연결된 페이스북 페이지와 인스타그램 비즈니스 계정 ID 찾기."""
    data = _check(requests.get(f"{_graph(cfg)}/me/accounts", params={
        "fields": "name,instagram_business_account{id,username}",
        "access_token": cfg.ig_token}, timeout=60), "계정 조회")
    out = []
    for page in data.get("data", []):
        ig = page.get("instagram_business_account")
        out.append({"page": page.get("name"), "ig_id": ig and ig["id"],
                    "username": ig and ig.get("username")})
    return out
