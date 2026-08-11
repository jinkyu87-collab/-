import { loadInvoices } from "../../lib/invoice.js";

export default async (req) => {
  if (req.method !== "GET") return json({ error: "GET 요청만 지원합니다." }, 405);

  const url = new URL(req.url);
  const status = url.searchParams.get("status"); // pending | issued | failed

  let list = await loadInvoices();
  if (status) list = list.filter((r) => r.status === status);

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
