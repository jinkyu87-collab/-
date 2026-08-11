// 세금계산서 발행 대상 데이터를 다루는 공통 로직
// (엑셀 파싱 결과 검증/보정, Netlify Blobs 저장소 접근을 이 파일에 모아둡니다)

import { getStore } from "@netlify/blobs";

const STORE_NAME = "tax-invoice";
const KEY = "invoices";

export function getInvoiceStore() {
  return getStore(STORE_NAME);
}

export async function loadInvoices() {
  const store = getInvoiceStore();
  const list = await store.get(KEY, { type: "json" });
  return Array.isArray(list) ? list : [];
}

export async function saveInvoices(list) {
  const store = getInvoiceStore();
  await store.setJSON(KEY, list);
}

// 엑셀 한 행 -> 저장용 레코드로 변환. 문제가 있으면 errors 배열에 담아 반환(행 자체는 버리지 않음).
export function normalizeRow(raw, rowIndex) {
  const errors = [];

  const supplierCode = str(raw["발행법인"]);
  const companyName = str(raw["거래처명"]);
  const bizNoRaw = str(raw["사업자등록번호"]);
  const bizNo = bizNoRaw.replace(/[^0-9]/g, "");
  const ceoName = str(raw["대표자명"]);
  const email = str(raw["이메일"]);
  const itemName = str(raw["품목명"]);
  const spec = str(raw["규격"]);
  const note = str(raw["비고"]);
  const transactionDate = normalizeDate(raw["거래일자"]);

  const qty = numOrNull(raw["수량"]);
  const unitPrice = numOrNull(raw["단가"]);
  let supplyAmount = numOrNull(raw["공급가액"]);
  let taxAmount = numOrNull(raw["세액"]);

  if (!supplierCode) errors.push("발행법인을 입력(선택)해주세요.");
  if (!companyName) errors.push("거래처명이 비어있습니다.");
  if (!bizNo || bizNo.length !== 10) errors.push("사업자등록번호는 숫자 10자리여야 합니다.");
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push("이메일 형식이 올바르지 않습니다.");
  if (!transactionDate) errors.push("거래일자는 YYYY-MM-DD 형식이어야 합니다.");
  if (!itemName) errors.push("품목명이 비어있습니다.");

  if (supplyAmount === null) {
    if (qty !== null && unitPrice !== null) {
      supplyAmount = qty * unitPrice;
    } else {
      errors.push("공급가액을 계산할 수 없습니다 (공급가액 또는 수량+단가 필요).");
    }
  }
  if (supplyAmount !== null && taxAmount === null) {
    taxAmount = Math.round(supplyAmount * 0.1);
  }
  const totalAmount =
    supplyAmount !== null && taxAmount !== null ? supplyAmount + taxAmount : null;

  return {
    ok: errors.length === 0,
    errors,
    rowIndex,
    record: {
      supplierCode,
      companyName,
      bizNo,
      ceoName: ceoName || null,
      email,
      itemName,
      spec: spec || null,
      qty,
      unitPrice,
      supplyAmount,
      taxAmount,
      totalAmount,
      transactionDate,
      note: note || null,
    },
  };
}

// 같은 발행법인+거래처+거래일자+합계금액+품목명 조합이 이미 있으면 중복 의심으로 표시(차단은 하지 않음)
export function duplicateKey(record) {
  return [record.supplierCode, record.companyName, record.transactionDate, record.totalAmount, record.itemName]
    .map((v) => String(v ?? "").trim())
    .join("|");
}

function str(v) {
  return v === null || v === undefined ? "" : String(v).trim();
}

function numOrNull(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isNaN(n) ? null : n;
}

function normalizeDate(v) {
  if (!v) return null;
  // 엑셀 날짜 시리얼 넘버(숫자)로 들어오는 경우
  if (typeof v === "number") {
    const d = new Date(Math.round((v - 25569) * 86400 * 1000));
    if (Number.isNaN(d.getTime())) return null;
    return d.toISOString().slice(0, 10);
  }
  const s = String(v).trim();
  const m = s.match(/^(\d{4})[-./](\d{1,2})[-./](\d{1,2})/);
  if (!m) return null;
  const [, y, mo, d] = m.map((x, i) => (i === 0 ? x : Number(x)));
  const [year, month, day] = [Number(y), mo, d];
  // 실제 존재하는 날짜인지(예: 13월, 2월 30일 등 거부) 왕복 변환으로 검증
  const check = new Date(Date.UTC(year, month - 1, day));
  if (
    check.getUTCFullYear() !== year ||
    check.getUTCMonth() !== month - 1 ||
    check.getUTCDate() !== day
  ) {
    return null;
  }
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
