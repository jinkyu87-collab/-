"""Claude로 릴스 대본 작성."""
import anthropic
from pydantic import BaseModel, Field

from .config import Config

MODEL = "claude-opus-5-5"


class ReelScript(BaseModel):
    title: str = Field(description="영상 상단에 띄울 짧고 강한 질문형/도발형 제목 (18자 이내, 별표 없이)")
    narration: str = Field(description="내레이션 전문. 읽기만 하면 되는 자연스러운 구어체 문장")
    caption: str = Field(description="인스타그램 게시물 본문 (2~4문장, 이모지 약간)")
    hashtags: list[str] = Field(description="해시태그 5~10개, # 포함")


SYSTEM = """당신은 해당 업계 현직 대표가 직접 말하는 것처럼 릴스 대본을 씁니다.
- 첫 문장은 시청자에게 바로 묻거나 찌르는 한 문장으로 시작합니다. (예: "견적서 속 OO, 확인해 보셨나요?")
- 구체적인 숫자, 실제 상황, 업계 현실을 말합니다. 뻔한 일반론은 쓰지 않습니다.
- "여러분", "알아볼까요", "꿀팁", "~해보세요!", "놓치지 마세요" 같은 AI·광고 말투를 쓰지 않습니다.
- 짧은 문장, 사람이 말하듯 자연스러운 존댓말 구어체로 씁니다.
- 내레이션에는 이모지, 해시태그, 괄호 지문, 영어를 넣지 않습니다(음성으로 읽힙니다).
- 화면에서 강조할 핵심 단어·숫자 4~6곳을 *별표*로 감쌉니다. (예: *최저임금의 100%*)
- 마지막은 "궁금한 점은 메시지 주세요" 같은 문의 유도로 끝냅니다.
- 확실하지 않은 수치나 법 내용은 지어내지 않습니다."""


def write_script(cfg: Config, topic: str) -> ReelScript:
    client = anthropic.Anthropic(api_key=cfg.anthropic_key)
    # 한국어 내레이션은 대략 초당 6~7자
    chars = cfg.target_seconds * 6
    prompt = (
        f"계정 콘셉트: {cfg.channel_concept}\n"
        f"주제: {topic}\n\n"
        f"약 {cfg.target_seconds}초 길이(내레이션 {chars - 30}~{chars + 30}자)의 릴스 대본을 작성해 주세요."
    )
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": prompt}],
            output_format=ReelScript,
        )
    except anthropic.AuthenticationError:
        raise RuntimeError("Claude API 키가 올바르지 않아요. .env 의 ANTHROPIC_API_KEY 가 "
                           "'sk-ant-api03-' 로 시작하는 키인지 확인하세요 (https://platform.claude.com/settings/keys).")
    except anthropic.PermissionDeniedError as e:
        raise RuntimeError(f"Claude API 권한 오류: {e.message}")
    except anthropic.BadRequestError as e:
        if "credit" in str(e).lower():
            raise RuntimeError("Claude API 크레딧이 부족해요. https://platform.claude.com 의 Billing 에서 충전하세요.")
        raise
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"대본을 만들지 못했어요 (stop_reason={response.stop_reason}). 주제를 바꿔 보세요.")
    script = response.parsed_output
    script.hashtags = [h if h.startswith("#") else f"#{h}" for h in script.hashtags]
    return script
