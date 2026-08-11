import { checkPassword } from "../../lib/auth.js";
import { loadInvoices, saveInvoices } from "../../lib/invoice.js";
import { getProvider } from "../../lib/providers/index.js";

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
  if (!Array.isArray(ids) || !ids.length) return json({ error: "발행할 항목을 선택해주세요." }, 400);

  const provider = getProvider();
  const list = await loadInvoices();
  const idSet = new Set(ids);

  const results = [];
  for (const inv of list) {
    if (!idSet.has(inv.id)) continue;
    if (inv.status === "issued") {
      results.push({ id: inv.id, ok: true, skipped: true, message: "이미 발행됨" });
      continue;
    }
    try {
      const r = await provider.issue(inv);
      if (r.ok) {
        inv.status = "issued";
        inv.issuedAt = new Date().toISOString();
        inv.confirmNum = r.confirmNum;
        inv.errorMessage = null;
      } else {
        inv.status = "failed";
        inv.errorMessage = r.errorMessage || "발행 실패";
      }
      results.push({ id: inv.id, ok: r.ok, message: r.ok ? r.confirmNum : r.errorMessage });
    } catch (err) {
      inv.status = "failed";
      inv.errorMessage = String((err && err.message) || err);
      results.push({ id: inv.id, ok: false, message: inv.errorMessage });
    }
  }

  await saveInvoices(list);

  return json({
    ok: true,
    provider: provider.name,
    successCount: results.filter((r) => r.ok && !r.skipped).length,
    failCount: results.filter((r) => !r.ok).length,
    results,
  });
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export const config = { path: "/api/tax/issue" };
