# 경영실적 대시보드 (URL 고정 + 엑셀 업로드 버전)

기존 Netlify 대시보드(`preeminent-douhua-d381f3.netlify.app`)를 그대로 재현하면서, 두 가지 문제를 해결한 버전입니다.

- **공유 주소가 매달 바뀌는 문제** → GitHub와 Netlify를 연결해 "같은 사이트를 계속 재배포"하는 방식으로 바꾸면, 사이트 이름을 한 번만 정해두면 그 이후로는 절대 바뀌지 않습니다.
- **데이터 입력이 번거로운 문제** → 매달 코드를 고치거나 재배포할 필요 없이, 대시보드 화면에서 엑셀 파일 하나만 업로드하면 즉시 반영됩니다. 데이터는 Netlify의 서버 저장소(Netlify Blobs)에 저장되고, 전년 대비 증감률은 저장된 과거 데이터에서 자동으로 계산됩니다.

기존 대시보드의 2025-06 ~ 2026-06 데이터(전사 실적, 팀별 실적 10개 팀)는 이미 이 프로젝트에 옮겨져 있습니다 (`data/seed.js`).

---

## 1. 배포 방법 (최초 1회만)

가장 중요한 점: **"Netlify Drop"으로 폴더를 매번 새로 드래그해서 올리면 그때마다 새 사이트가 생성되어 주소가 바뀝니다.** 이 문제를 피하려면 GitHub 저장소와 연결해서 "하나의 사이트"가 계속 유지되도록 해야 합니다.

1. **GitHub에 저장소 만들기**
   - github.com에서 새 저장소(예: `team-dashboard`)를 만들고, 이 폴더 전체를 업로드/푸시합니다.
   2. **Netlify에서 이 저장소 연결하기**
      - Netlify 로그인 → "Add new site" → "Import an existing project" → GitHub 선택 → 방금 만든 저장소 선택
         - Build command: `npm install` (이미 `netlify.toml`에 설정되어 있어 보통 자동 인식됩니다)
            - Publish directory: `public`
               - Functions directory: `netlify/functions`
                  - "Deploy site" 클릭
                  3. **사이트 이름(=고정 주소) 정하기**
                     - 배포가 끝나면 Site settings → Domain management → "Options" → "Edit site name"에서 원하는 이름으로 변경 (예: `ourcompany-dashboard` → `https://ourcompany-dashboard.netlify.app`)
                        - 이후로는 코드를 수정해서 다시 배포해도 이 주소는 절대 바뀌지 않습니다. (원하면 회사 도메인을 연결해 더 짧은 주소를 쓸 수도 있습니다.)
                        4. **업로드 비밀번호 설정하기**
                           - Site settings → Environment variables → "Add a variable"
                              - Key: `UPLOAD_PASSWORD`, Value: 원하는 비밀번호 입력 후 저장
                                 - 저장 후 "Deploys" 탭에서 "Trigger deploy" → "Deploy site"를 한 번 눌러 환경변수를 반영합니다.
                                    - (이 변수를 설정하지 않으면 누구나 비밀번호 없이 데이터를 업로드할 수 있으니, 반드시 설정하는 것을 권장합니다.)

                                    이제 4번까지 끝나면 완성입니다. 팀원들에게는 3번에서 정한 고정 주소만 공유하면 됩니다.

                                    ---

                                    ## 2. 매달 데이터 업데이트하는 방법 (재배포 불필요)

                                    1. `template/입력템플릿.xlsx` 파일을 열어 이번 달 데이터를 입력합니다.
                                       - **'전사' 시트**: 월(YYYY-MM), 매출액(귀속), 실적매출, 영업이익, 손익 — 노란색 칸만 채우면 됩니다. 회색 예시 행은 그대로 두어도 무시되니 지우지 않아도 됩니다.
                                          - **'팀별' 시트**: 팀별로 실적매출, 변동금, 이익금, 재직인원, 특이사항을 입력합니다. 새 팀이 생기면 행을 추가하면 됩니다.
                                          2. 대시보드 페이지 접속 → 우측 상단 "데이터 업데이트" 버튼 클릭
                                          3. 비밀번호 입력, 방금 작성한 엑셀 파일 선택 → "업로드" 클릭
                                          4. 몇 초 후 "OO월 데이터가 반영되었습니다" 메시지가 뜨면 완료. 새로고침 없이 바로 그래프/표가 갱신됩니다.

                                          재배포, 코드 수정, 새 사이트 생성 어느 것도 필요 없습니다. 전년 동월 데이터가 이미 저장되어 있으면 전년 대비 증감률도 자동으로 채워집니다.

                                          ---

                                          ## 3. 로컬에서 미리보기(선택사항)

                                          Netlify CLI가 설치되어 있다면 아래처럼 로컬에서 확인할 수 있습니다.

                                          ```bash
                                          npm install
                                          npx netlify dev
                                          ```

                                          ---

                                          ## 4. 프로젝트 구조

                                          ```
                                          public/index.html          대시보드 화면 (기존 디자인 재현 + 업로드 버튼)
                                          netlify/functions/data.js   GET /api/data  - 현재 저장된 데이터 반환
                                          netlify/functions/upload.js POST /api/upload - 엑셀 업로드 → 파싱 → 저장
                                          data/seed.js                최초 배포 시 채워지는 과거 데이터(2025-06~2026-06)
                                          template/입력템플릿.xlsx     매달 채워서 업로드할 엑셀 템플릿
                                          netlify.toml                Netlify 빌드/함수 설정
                                          ```

                                          ## 5. 문제 해결

                                          - **업로드가 "비밀번호가 올바르지 않습니다" 오류**: Netlify 환경변수 `UPLOAD_PASSWORD`와 입력한 값이 다른 경우입니다.
                                          - **업로드가 "월 값이 올바르지 않습니다" 오류**: '전사' 시트의 '월' 칸이 `YYYY-MM` 형식(예: 2026-07)인지 확인하세요.
                                          - **업로드 후에도 화면이 안 바뀜**: 브라우저 새로고침(Cmd/Ctrl+R)을 한 번 해보세요.
                                          - **주소가 또 바뀐 것 같다**: Netlify Drop으로 폴더를 다시 올리지 말고, 반드시 "1. 배포 방법"처럼 GitHub 연결 방식으로 재배포하세요. 코드를 고칠 때도 GitHub에 푸시만 하면 Netlify가 같은 사이트에 자동으로 재배포합니다.
