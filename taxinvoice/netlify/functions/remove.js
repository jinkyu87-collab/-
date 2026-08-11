// 발행 전 잘못 올라온 대기 항목을 지울 때 사용 (이미 발행된 건은 지우지 않음 - 실제 세금계산서는
// 국세청에 전송된 뒤에는 취소/수정세금계산서로 처리해야 하므로 여기서 임의 삭제하면 안 됩니다)
import { checkPassword } from "../../lib/auth.js";
import { loadInvoices, saveInvoices } from "../../lib/invoice.js";

export default async (req) => {
  if (req.method !== "POST") return json({ error: "POST 요청만 지원합니다." }, 405);

  let body;
  try {
    body = await req.json();
  } catch {
    return json({ error: "요청 본문을 읽을 수 없습니다." }, 400);
  }

  const { password, ids } = body || {};
  if (!checkPassword(password)) return json({ error: "비밀번호가 올바르지 않습니다." }, 401);
  if (!Array.isArray(ids) || !ids.length) return json({ error: "삭제할 항목을 선택해주세요." }, 400);

  const list = await loadInvoices();
  const idSet = new Set(ids);

  const blocked = list.filter((inv) => idSet.has(inv.id) && inv.status === "issued");
  const next = list.filter((inv) => !(idSet.has(inv.id) && inv.status !== "issued"));

  await saveInvoices(next);

  return json({
    ok: true,
    removedCount: list.length - next.length,
    blockedCount: blocked.length,
  });
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export const config = { path: "/api/tax/remove" };
