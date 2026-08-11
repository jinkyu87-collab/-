// 업로드/발행 같은 민감한 동작 전에 비밀번호를 확인하는 공통 로직.
// TAX_APP_PASSWORD 환경변수를 설정하지 않으면(로컬 테스트 등) 통과시킵니다.
export function checkPassword(password) {
  const expected = process.env.TAX_APP_PASSWORD;
  if (!expected) return true;
  return password === expected;
}
