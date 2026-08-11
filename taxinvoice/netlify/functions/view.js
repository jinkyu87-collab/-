// 계산서 형태로 조회하는 화면. GET /api/tax/view?id=xxx
// 실제 스마트빌 등에서 계산서 조회 URL(invoiceViewUrl)을 돌려준 건이면 그쪽으로 바로 이동시키고,
// 아직 없는 건(지금의 모의발행 포함)은 저장된 데이터로 우리 시스템이 직접 계산서 모양 화면을 그려줍니다.
// 이 화면은 국세청에 실제 신고된 정식 문서가 아니라 내부 확인/공유용 미리보기입니다.
import { loadInvoices } from "../../lib/invoice.js";
import { getSupplierInfo } from "../../lib/supplier.js";

export default async (req) => {
  const url = new URL(req.url);
  const id = url.searchParams.get("id");
  if (!id) return html(errorPage("조회할 계산서 id가 없습니다."), 400);

  const list = await loadInvoices();
  const inv = list.find((r) => r.id === id);
  if (!inv) return html(errorPage("해당 계산서를 찾을 수 없습니다."), 404);

  // 실제 발행 대행사가 준 정식 조회 링크가 있으면 그쪽으로 안내
  if (inv.invoiceViewUrl) {
    return new Response(null, { status: 302, headers: { location: inv.invoiceViewUrl } });
  }

  // 업로드 당시 선택한 법인 정보(스냅샷)를 사용. 이 기능 추가 전에 업로드된 옛날 건은
  // supplier가 없으므로 환경변수 기반 기본값으로 대체.
  const supplier = inv.supplier || getSupplierInfo();
  return html(renderInvoice(inv, supplier));
};

function fmt(n) {
  return n === null || n === undefined ? "-" : Number(n).toLocaleString("ko-KR");
}

function esc(s) {
  if (s === null || s === undefined) return "";
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function statusNotice(inv) {
  if (inv.status === "issued") {
    return `<div class="notice ok">모의발행 완료 — 확인번호 ${esc(inv.confirmNum)}. 실제 국세청 신고 문서가 아닌 내부 미리보기입니다. 스마트빌 연동 후에는 정식 계산서 조회 링크로 자동 연결됩니다.</div>`;
  }
  if (inv.status === "failed") {
    return `<div class="notice err">발행 실패 — ${esc(inv.errorMessage)}</div>`;
  }
  return `<div class="notice pending">아직 발행 전입니다 (미리보기).</div>`;
}

function renderInvoice(inv, supplier) {
  return `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<title>세금계산서 미리보기 - ${esc(inv.companyName)}</title>
<style>
  :root { --border:#333; --muted:#666; --bg:#F7F8FA; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; background: var(--bg); color:#111; padding: 24px 16px; }
  .wrap { max-width: 860px; margin: 0 auto; }
  .notice { font-size: 13px; padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; }
  .notice.ok { background:#E4F5EF; color:#1D9E75; }
  .notice.err { background:#FBEAE3; color:#D85A30; }
  .notice.pending { background:#FBF3DA; color:#B98900; }
  .sheet { background:#fff; border:1px solid var(--border); padding: 28px 32px; }
  h1 { text-align:center; font-size: 22px; letter-spacing: 4px; margin: 0 0 20px; }
  .parties { display:grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 18px; }
  .party { border:1px solid #ccc; border-radius:6px; padding: 12px 14px; }
  .party h3 { font-size:13px; margin:0 0 8px; color: var(--muted); }
  .party table td { font-size: 13px; padding: 2px 0; vertical-align: top; }
  .party table td.k { color: var(--muted); width: 70px; white-space: nowrap; }
  .meta { font-size: 13px; color: var(--muted); margin-bottom: 12px; }
  table.items { width:100%; border-collapse: collapse; margin-bottom: 16px; }
  table.items th, table.items td { border:1px solid #ccc; padding: 8px; font-size: 13px; text-align:left; }
  table.items th { background:#f2f2f2; }
  table.items td.num { text-align:right; }
  .totals { display:flex; justify-content:flex-end; gap: 24px; font-size: 14px; margin-bottom: 8px; }
  .totals b { font-size: 16px; }
  .footer-row { display:flex; justify-content: space-between; align-items:center; margin-top: 20px; font-size: 12px; color: var(--muted); }
  .actions { text-align:center; margin-top: 16px; }
  button { height:36px; padding:0 16px; border-radius:8px; border:1px solid #ccc; background:#fff; cursor:pointer; font-size:13px; }
  @media print { .notice, .actions { display:none; } body { background:#fff; padding:0; } .sheet { border:none; } }
</style>
</head>
<body>
<div class="wrap">
  ${statusNotice(inv)}
  <div class="sheet">
    <h1>세 금 계 산 서 (미리보기)</h1>
    <div class="meta">작성일자: ${esc(inv.transactionDate)} ${inv.confirmNum ? ` · 확인번호: ${esc(inv.confirmNum)}` : ""}</div>
    <div class="parties">
      <div class="party">
        <h3>공급자${supplier.code ? ` (${esc(supplier.code)})` : ""}</h3>
        <table>
          <tr><td class="k">등록번호</td><td>${esc(supplier.bizNo)}</td></tr>
          <tr><td class="k">상호</td><td>${esc(supplier.name)}</td></tr>
          <tr><td class="k">대표자</td><td>${esc(supplier.ceoName)}</td></tr>
          <tr><td class="k">주소</td><td>${esc(supplier.address)}</td></tr>
          <tr><td class="k">업태/종목</td><td>${esc(supplier.bizType)} / ${esc(supplier.bizItem)}</td></tr>
        </table>
      </div>
      <div class="party">
        <h3>공급받는자</h3>
        <table>
          <tr><td class="k">등록번호</td><td>${esc(inv.bizNo)}</td></tr>
          <tr><td class="k">상호</td><td>${esc(inv.companyName)}</td></tr>
          <tr><td class="k">대표자</td><td>${esc(inv.ceoName || "-")}</td></tr>
          <tr><td class="k">이메일</td><td>${esc(inv.email)}</td></tr>
        </table>
      </div>
    </div>
    <table class="items">
      <thead>
        <tr><th>품목명</th><th>규격</th><th class="num">수량</th><th class="num">단가</th><th class="num">공급가액</th><th class="num">세액</th><th>비고</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>${esc(inv.itemName)}</td>
          <td>${esc(inv.spec || "-")}</td>
          <td class="num">${fmt(inv.qty)}</td>
          <td class="num">${fmt(inv.unitPrice)}</td>
          <td class="num">${fmt(inv.supplyAmount)}</td>
          <td class="num">${fmt(inv.taxAmount)}</td>
          <td>${esc(inv.note || "-")}</td>
        </tr>
      </tbody>
    </table>
    <div class="totals">
      <span>공급가액 합계: ${fmt(inv.supplyAmount)}</span>
      <span>세액 합계: ${fmt(inv.taxAmount)}</span>
      <b>합계금액: ${fmt(inv.totalAmount)}</b>
    </div>
    <div class="footer-row">
      <span>본 문서는 내부 시스템이 생성한 미리보기이며, 국세청에 실제 신고된 정식 전자세금계산서가 아닙니다.</span>
    </div>
  </div>
  <div class="actions"><button onclick="window.print()">인쇄 / PDF로 저장</button></div>
</div>
</body>
</html>`;
}

function errorPage(msg) {
  return `<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>오류</title></head>
<body style="font-family:sans-serif; padding:40px; text-align:center; color:#D85A30;">${esc(msg)}</body></html>`;
}

function html(body, status = 200) {
  return new Response(body, { status, headers: { "content-type": "text/html; charset=utf-8" } });
}

export const config = { path: "/api/tax/view" };
