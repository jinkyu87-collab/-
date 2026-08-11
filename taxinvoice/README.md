# 세금계산서 자동발행 프로그램 (1단계: 모의발행 모드)

엑셀로 발행 대상을 업로드하면 대기목록에 쌓이고, 화면에서 선택해서 "발행" 버튼을 누르면
발행 처리되는 구조입니다. 월 500건, 하루 최대 100건 정도의 수시 발행을 염두에 두고 만들었습니다.

**현재 상태: 스마트빌(SmartBill) API 연동 전이라 "모의발행(mock) 모드"로 동작합니다.**
실제로 국세청에 아무것도 전송되지 않고, 발행 버튼을 누르면 성공한 것처럼 화면/상태만 바뀝니다.
전체 업로드 → 검토 → 발행 흐름을 미리 확인/연습하는 용도입니다.
스마트빌 Open API 승인이 나고 개발가이드를 받으면 `lib/providers/smartbill.js` 하나만 채우면
실제 발행으로 바로 전환됩니다 (화면/업로드/저장 구조는 그대로 재사용).

---

## 1. 배포 방법

이 저장소(레포) 안에 있지만, **완전히 별도의 Netlify 사이트**로 배포합니다 (기존 대시보드와 무관).

1. Netlify → "Add new site" → "Import an existing project" → 이 GitHub 저장소 선택
2. **Base directory**를 `taxinvoice` 로 지정 (중요 — 이걸 빼먹으면 기존 대시보드랑 충돌납니다)
   - Build command: `npm install` (자동 인식됨)
   - Publish directory: `public` (base 기준 상대경로)
   - Functions directory: `netlify/functions`
3. "Deploy site" 클릭 → 배포 끝나면 Site settings에서 사이트 이름 고정
4. 환경변수 설정 (Site settings → Environment variables)
   - `TAX_APP_PASSWORD`: 업로드/발행/삭제 시 요구할 비밀번호 (설정 안 하면 비밀번호 없이 누구나 가능 — 반드시 설정 권장)
   - `TAX_PROVIDER`: 지금은 비워두거나 `mock` (기본값). 스마트빌 연동 후 `smartbill` 로 변경
   - (스마트빌 연동 후 추가) `SMARTBILL_LINK_ID`, `SMARTBILL_SECRET_KEY` 등 — `lib/providers/smartbill.js` 참고

---

## 2. 사용 방법

1. 화면에서 **"엑셀 템플릿 다운로드"** 클릭 → 양식에 맞춰 발행 대상 입력
2. 비밀번호 입력 (설정한 경우) → 파일 선택 → **"엑셀 업로드"**
   - 행 단위로 검증하며, 문제 있는 행은 이유와 함께 알려주고 나머지는 정상 반영됩니다 (전체 실패 X)
   - 같은 거래처+거래일자+합계금액+품목명 조합이 이미 있으면 "중복의심" 표시 (막지는 않음 — 확인 후 진행)
3. 대기목록에서 발행할 건 체크 → **"선택 발행"**
   - 하루 100건처럼 몰릴 때도 원하는 건만 골라서 나눠 발행 가능
4. 상태 탭(대기/발행완료/실패)으로 필터링해서 확인
5. 잘못 올라온 **대기** 건은 "선택 삭제"로 제거 가능 (이미 발행된 건은 삭제 불가 — 국세청 전송 후에는 수정/취소세금계산서로 처리해야 함)

### 엑셀 템플릿 컬럼

| 컬럼 | 필수 | 설명 |
|---|---|---|
| 거래처명 | ✅ | 공급받는자 상호 |
| 사업자등록번호 | ✅ | 숫자만 10자리 (하이픈 있어도 자동 제거) |
| 대표자명 | | |
| 이메일 | ✅ | 전자세금계산서 수신 이메일 |
| 거래일자 | ✅ | YYYY-MM-DD |
| 품목명 | ✅ | |
| 규격 | | |
| 수량 / 단가 | | 공급가액 비워두면 수량×단가로 자동계산 |
| 공급가액 | | 비워두면 자동계산 |
| 세액 | | 비워두면 공급가액의 10%로 자동계산 |
| 비고 | | |

---

## 3. 프로젝트 구조

```
public/index.html                 화면 (업로드, 대기목록, 발행)
netlify/functions/upload.js       POST /api/tax/upload   - 엑셀 업로드 → 검증 → 대기목록 추가
netlify/functions/list.js         GET  /api/tax/list      - 목록 조회 (status로 필터)
netlify/functions/issue.js        POST /api/tax/issue     - 선택 건 발행
netlify/functions/remove.js       POST /api/tax/remove    - 대기 건 삭제
netlify/functions/template.js     GET  /api/tax/template  - 엑셀 템플릿 다운로드
lib/invoice.js                    행 검증/정규화 + Netlify Blobs 저장소 접근
lib/auth.js                       비밀번호 확인
lib/providers/index.js            발행 대행사 선택 (mock / smartbill)
lib/providers/mock.js             모의 발행 (현재 기본값)
lib/providers/smartbill.js        스마트빌 실연동 - 개발가이드 받으면 구현 (지금은 TODO)
```

---

## 4. 다음 단계 (스마트빌 실연동)

1. 스마트빌에서 Open API 승인 + 개발가이드 문서 + (있다면) 테스트베드 계정 수령
2. `lib/providers/smartbill.js` 상단 TODO에 적힌 항목(엔드포인트, 인증 파라미터명, 요청/응답 필드) 채워서 구현
3. Netlify 환경변수에 `SMARTBILL_LINK_ID` / `SMARTBILL_SECRET_KEY` 등 등록
4. `TAX_PROVIDER=smartbill` 로 변경
5. 테스트베드에서 1~2건 발행 검증 후 실서버 전환

## 5. 로컬 미리보기 (선택)

```bash
cd taxinvoice
npm install
npx netlify dev
```
