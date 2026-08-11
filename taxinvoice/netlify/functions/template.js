import * as XLSX from "xlsx";

export default async () => {
  const headers = [
    "거래처명",
    "사업자등록번호",
    "대표자명",
    "이메일",
    "거래일자",
    "품목명",
    "규격",
    "수량",
    "단가",
    "공급가액",
    "세액",
    "비고",
  ];
  const sample = [
    "샘플상사",
    "1234567890",
    "홍길동",
    "sample@example.com",
    "2026-08-11",
    "컨설팅 용역",
    "",
    1,
    1000000,
    "",
    "",
    "공급가액/세액은 비워두면 자동 계산됩니다",
  ];

  const ws = XLSX.utils.aoa_to_sheet([headers, sample]);
  ws["!cols"] = headers.map(() => ({ wch: 16 }));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "발행요청");

  const buf = XLSX.write(wb, { type: "buffer", bookType: "xlsx" });

  return new Response(buf, {
    status: 200,
    headers: {
      "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "content-disposition": 'attachment; filename="tax-invoice-template.xlsx"',
    },
  });
};

export const config = { path: "/api/tax/template" };
