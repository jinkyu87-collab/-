// 계산서 조회 화면에 표시할 "공급자(우리 회사)" 정보.
// Netlify 환경변수로 설정합니다 (Site settings > Environment variables).
// 아직 설정하지 않았다면 자리표시자 문구가 대신 표시됩니다 — 나중에 채워넣어도 기존 발행 건에는
// 영향 없습니다 (조회 화면에 그때그때 최신 값으로 표시될 뿐, 저장은 거래처 쪽 정보만 됩니다).
export function getSupplierInfo() {
  return {
    name: process.env.SUPPLIER_NAME || "(미설정 - SUPPLIER_NAME 환경변수를 설정해주세요)",
    bizNo: process.env.SUPPLIER_BIZ_NO || "(미설정)",
    ceoName: process.env.SUPPLIER_CEO_NAME || "(미설정)",
    address: process.env.SUPPLIER_ADDRESS || "(미설정)",
    bizType: process.env.SUPPLIER_BIZ_TYPE || "(미설정)", // 업태
    bizItem: process.env.SUPPLIER_BIZ_ITEM || "(미설정)", // 종목
    email: process.env.SUPPLIER_EMAIL || "(미설정)",
  };
}
