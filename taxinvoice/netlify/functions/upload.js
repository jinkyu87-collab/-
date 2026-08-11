import * as XLSX from "xlsx";
import { checkPassword } from "../../lib/auth.js";
import { loadInvoices, saveInvoices, normalizeRow, duplicateKey } from "../../lib/invoice.js";

export default async (req) => {
  if (req.method !== "POST") return json({ error: "POST 요청만 지원합니다." }, 405);

  let body;
  try {
    body = await req.json();
  } catch {
    return json({ error: "요청 본문을 읽을 수 없습니다." }, 400);
  }

  const { password, base64 } = body || {};
  if (!checkPassword(password)) return json({ error: "비밀번호가 올바르지 않습니다." }, 401);
  if (!base64) return json({ error: "업로드된 파일이 없습니다." }, 400);

  let wb;
  try {
    const buf = Buffer.from(base64, "base64");
    wb = XLSX.read(buf, { type: "buffer" });
  } catch (err) {
    return json({ error: "엑셀 파일을 읽는 중 오류가 발생했습니다: " + String(err.message || err) }, 400);
  }

  const sheetName = wb.SheetNames[0];
  const rows = XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { defval: null });
  if (!rows.length) return json({ error: "시트에서 데이터를 찾지 못했습니다." }, 400);

  const existing = await loadInvoices();
  const existingKeys = new Set(existing.map((r) => duplicateKey(r)));

  const added = [];
  const rowErrors = [];
  const duplicates = [];
  const now = new Date().toISOString();

  rows.forEach((raw, i) => {
    const rowIndex = i + 2; // 엑셀 1행은 헤더이므로 실제 데이터는 2행부터
    const { ok, errors, record } = normalizeRow(raw, rowIndex);
    if (!ok) {
      rowErrors.push({ row: rowIndex, errors });
      return;
    }
    const key = duplicateKey(record);
    const isDuplicate = existingKeys.has(key);
    if (isDuplicate) duplicates.push(rowIndex);

    added.push({
      id: `inv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      ...record,
      status: "pending",
      duplicateSuspected: isDuplicate,
      uploadedAt: now,
      issuedAt: null,
      confirmNum: null,
      errorMessage: null,
    });
    existingKeys.add(key);
  });

  if (added.length) {
    await saveInvoices(existing.concat(added));
  }

  return json({
    ok: true,
    addedCount: added.length,
    errorCount: rowErrors.length,
    duplicateCount: duplicates.length,
    errors: rowErrors,
    duplicateRows: duplicates,
  });
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export const config = { path: "/api/tax/upload" };
