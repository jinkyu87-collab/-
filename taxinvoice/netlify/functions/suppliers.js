// GET  /api/tax/suppliers - 등록된 법인 목록 조회
// POST /api/tax/suppliers - 법인 목록 통째로 저장 (화면 "법인 관리"에서 사용)
import { checkPassword } from "../../lib/auth.js";
import { loadSuppliers, saveSuppliers } from "../../lib/suppliers.js";

export default async (req) => {
  if (req.method === "GET") {
    const suppliers = await loadSuppliers();
    return json({ ok: true, suppliers });
  }

  if (req.method === "POST") {
    let body;
    try {
      body = await req.json();
    } catch {
      return json({ error: "요청 본문을 읽을 수 없습니다." }, 400);
    }
    const { password, suppliers } = body || {};
    if (!checkPassword(password)) return json({ error: "비밀번호가 올바르지 않습니다." }, 401);
    if (!Array.isArray(suppliers) || !suppliers.length) {
      return json({ error: "법인 정보가 비어있습니다." }, 400);
    }
    for (const s of suppliers) {
      if (!s.code || !String(s.code).trim()) {
        return json({ error: "모든 법인에 구분코드(code)가 있어야 합니다." }, 400);
      }
    }
    await saveSuppliers(suppliers);
    return json({ ok: true, count: suppliers.length });
  }

  return json({ error: "GET/POST 요청만 지원합니다." }, 405);
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export const config = { path: "/api/tax/suppliers" };
