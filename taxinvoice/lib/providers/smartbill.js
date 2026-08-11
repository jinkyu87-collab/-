// 스마트빌(SmartBill) 전자세금계산서 발행 API 연동 - 아직 구현 전 (TODO)
//
// 스마트빌에서 "Open API 연동 개발가이드"를 받으면 아래 항목을 채워서 완성해주세요:
//   1. 인증 방식 (LinkID/SecretKey 등 정확한 파라미터명, 발급 위치)
//   2. 세금계산서 발행 API의 엔드포인트 URL과 HTTP method
//   3. 요청 바디 포맷(JSON/XML/SOAP)과 각 필드명 <-> 아래 record 필드 매핑
//   4. 응답 포맷 (성공 시 확인번호/승인번호 필드명, 실패 시 에러코드/메시지 필드명)
//   5. 테스트베드(Sandbox) 서버 주소 (있다면)
//
// 환경변수는 Netlify 사이트 설정 > Environment variables 에 추가해서 씁니다.
//   SMARTBILL_LINK_ID, SMARTBILL_SECRET_KEY, SMARTBILL_CORP_NUM(발행 사업자 번호) 등
//   (정확한 이름은 개발가이드 확인 후 여기 주석/코드를 함께 업데이트)

export async function issue(record) {
  throw new Error(
    "스마트빌 연동이 아직 구성되지 않았습니다. 개발가이드를 받은 뒤 lib/providers/smartbill.js 를 구현해주세요. " +
      "그 전까지는 TAX_PROVIDER=mock 으로 두고 화면/흐름만 테스트하세요."
  );
}
