import { loadInvoices } from "../../lib/invoice.js";

export default async (req) => {
  if (req.method !== "GET") return json({ error: "GET 요청만 지원합니다." }, 405);

  const url = new URL(req.url);
  const status = url.searchParams.get("status"); // pending | issued | failed
  const from = url.searchParams.get("from"); // YYYY-MM-DD, 거래일자 기준
  const to = url.searchParams.get("to"); // YYYY-MM-DD, 거래일자 기준

  let list = await loadInvoices();
  if (status) list = list.filter((r) => r.status === status);
  // 거래일자(YYYY-MM-DD) 기준 기간 검색 — 문자열 비교로 충분 (ISO 형식이라 사전식 정렬 = 날짜순 정렬)
  if (from) list = list.filter((r) => r.transactionDate && r.transactionDate >= from);
  if (to) list = list.filter((r) => r.transactionDate && r.transactionDate <= to);

  // 최신 업로드가 위로 오도록 정렬
  list = list.slice().sort((a, b) => (b.uploadedAt || "").localeCompare(a.uploadedAt || ""));

  return json({ ok: true, count: list.length, invoices: list });
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export const config = { path: "/api/tax/list" };
