// 모의 발행 provider.
// 실제 스마트빌 API를 붙이기 전까지, 화면/업로드/대기목록/발행 흐름 전체를 테스트할 수 있게 해줍니다.
// 실제로 국세청에 아무것도 전송하지 않고, 성공한 것처럼 확인번호만 만들어 돌려줍니다.

export async function issue(record) {
  // 실제 API였다면 실패할 법한 케이스를 흉내내서, 오류 처리 화면도 미리 확인할 수 있게 함
  if (!record.bizNo || record.bizNo.length !== 10) {
    return { ok: false, errorMessage: "[모의] 사업자등록번호가 유효하지 않습니다." };
  }
  const fakeConfirmNum = `MOCK-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
  return { ok: true, confirmNum: fakeConfirmNum };
}
