# 릴스 자동화 (Windows)

주제 한 줄만 넣으면 아래 과정을 자동으로 처리해요.

1. **대본 작성**: Claude가 후킹 문장, 내레이션, 게시글 본문, 해시태그를 써요.
2. **AI 음성**: ElevenLabs가 대본을 한국어 내레이션으로 읽어요.
3. **영상 편집**: 세로 1080x1920 영상에 배경, 제목, 음성에 맞춘 자막을 넣어요.
4. **인스타그램 업로드**: 원하면 릴스로 바로 게시해요.

```
reels-automation/
├─ install.bat          ← 처음 한 번 더블클릭 (설치)
├─ make_reel.bat        ← 릴스 만들 때 더블클릭
├─ .env.example         ← API 키 입력 양식 (설치하면 .env 로 복사됨)
├─ assets/backgrounds/  ← 배경 이미지·영상을 넣는 곳 (비워 두면 그라데이션)
└─ output/              ← 완성된 릴스가 저장되는 곳
```

---

## 1. 설치 (처음 한 번)

1. **파이썬 설치**: https://www.python.org/downloads/ 에서 받아 설치해요.
   설치 첫 화면 아래의 **"Add python.exe to PATH"를 꼭 체크**하세요.
2. 이 `reels-automation` 폴더를 내 컴퓨터에 받아요.
   예를 들면 `C:\Users\내이름\Documents\reels-automation` 이요.
3. **`install.bat`을 더블클릭**하면 필요한 프로그램이 자동으로 설치돼요.
4. 설치가 끝나면 메모장으로 `.env`가 열려요. 아래 2번에서 받은 키를 넣고 저장하세요.

## 2. API 키 넣기 (`.env` 파일)

| 항목 | 받는 곳 | 비고 |
|---|---|---|
| `ANTHROPIC_API_KEY` | https://platform.claude.com/settings/keys | 대본 작성용. 결제수단 등록과 크레딧 충전이 필요해요 |
| `ELEVENLABS_API_KEY` | https://elevenlabs.io/app/settings/api-keys | 음성용 |
| `IG_ACCESS_TOKEN`, `IG_USER_ID` | 아래 4번 참고 | 자동 업로드할 때만 필요해요 |

> ⚠️ 키는 `.env` 파일에만 넣으세요. 채팅이나 메신저, GitHub에 올리면 안 돼요. `.env`는 GitHub에 올라가지 않도록 설정돼 있어요.

## 3. 릴스 만들기

**`make_reel.bat`을 더블클릭**하고 주제를 입력하면 끝이에요. 완성된 파일은 `output\날짜_주제\` 폴더에 저장돼요.

- `reel.mp4`: 완성된 영상
- `caption.txt`: 게시글 본문과 해시태그
- `script.json`: 대본 원본

명령어로 실행하려면 이 폴더에서 `venv\Scripts\activate`를 먼저 실행한 뒤 아래 명령을 쓰면 돼요.

```bat
python reels.py make "겨울철 전기요금 아끼는 법"
```

```bat
python reels.py make "아침 루틴 5가지" --upload
```

```bat
python reels.py make --topics topics.example.txt
```

```bat
python reels.py upload output\20261119-101500_겨울철_전기요금
```

```bat
python reels.py voices
```

```bat
python reels.py check
```

명령어별 기능은 이래요.

- `make "주제"`: 릴스를 하나 만들어요.
- `make "주제" --upload`: 만든 뒤 인스타그램에 바로 올려요.
- `make --topics 파일`: 파일에 한 줄에 하나씩 적은 주제로 여러 개를 만들어요.
- `upload 폴더`: 만들어 둔 릴스를 올려요.
- `voices`: 내 계정에서 쓸 수 있는 목소리 목록을 보여줘요.
- `check`: 설정이 제대로 됐는지 확인해요.

**바꿀 수 있는 설정** (`.env`):

- `CHANNEL_CONCEPT`: 계정 콘셉트예요. 대본 톤이 여기에 맞춰져요.
- `TARGET_SECONDS`: 영상 길이예요. 기본값은 35초예요.
- `ELEVENLABS_VOICE_ID`: 목소리예요. 기본값은 Yeonhee(밝은 한국어 여성 목소리)예요.

## 4. 인스타그램 연동 (자동 업로드용)

1. **프로페셔널 계정으로 전환**: 인스타그램 앱에서 설정 → 계정 유형 및 도구 → 프로페셔널 계정으로 전환해요. 크리에이터와 비즈니스 중 아무거나 괜찮아요.
2. **페이스북 페이지 연결**: 페이스북 페이지를 만들고 페이지 설정 → 연결된 계정 → Instagram에서 계정을 연결해요.
3. **Meta 개발자 앱 만들기**: https://developers.facebook.com/apps 에서 앱을 만들어요. 사용 사례는 Instagram 콘텐츠 관리나 기타 → 비즈니스로 고르면 돼요.
4. **토큰 발급**: https://developers.facebook.com/tools/explorer 에서 방금 만든 앱을 선택해요. 아래 권한을 추가하고 **Generate Access Token**을 눌러요.
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
5. **장기 토큰으로 바꾸기**: https://developers.facebook.com/tools/debug/accesstoken 에 토큰을 붙여넣고 **Extend Access Token**을 눌러요. 그러면 약 60일 동안 쓸 수 있는 토큰이 나와요.
6. 받은 토큰을 `.env`의 `IG_ACCESS_TOKEN`에 넣고 아래 명령을 실행해요.
   ```bat
   python reels.py ig-check
   ```
   화면에 나온 `IG_USER_ID=숫자`를 `.env`에 넣으면 연동이 끝나요.

> 토큰은 약 60일 뒤에 만료돼요. 업로드가 안 되면 4~5번을 다시 해서 새 토큰으로 바꾸세요.
> 인스타그램 API는 하루에 올릴 수 있는 게시물 수에 제한이 있어요.

## 5. 문제 해결

- **`'python'은(는) 내부 또는 외부 명령...`**: 파이썬을 다시 설치하세요. 이번에는 "Add python.exe to PATH"를 꼭 체크하세요.
- **ElevenLabs 목소리 오류**: https://elevenlabs.io/app/voice-library 에서 해당 목소리를 **Add to My Voices** 하거나, `python reels.py voices`로 다른 목소리를 고르세요. 무료 요금제는 라이브러리 목소리를 API로 못 쓸 수도 있어요.
- **자막이 □□로 나와요**: `.env`에 `FONT_PATH=C:/Windows/Fonts/malgun.ttf`를 추가하세요.
- **비용**: 대본 1개는 Claude 사용료로 몇십 원 수준이에요. 음성은 ElevenLabs 크레딧이 글자 수만큼 차감돼요.
