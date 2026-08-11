// 발행 주체(우리 회사, 법인 여러 개)를 관리하는 로직.
// 법인 정보는 Netlify Blobs에 저장되고, 화면의 "법인 관리"에서 직접 입력/수정합니다
// (환경변수가 아니라서 재배포 없이 바로 반영됩니다).
import { getStore } from "@netlify/blobs";

const STORE_NAME = "tax-invoice";
const KEY = "suppliers";

function store() {
  return getStore(STORE_NAME);
}

// 아직 아무것도 등록 안 했을 때 보여줄 기본 3개 법인 자리 — code만 정해져 있고 나머지는 비어있음.
// 화면 "법인 관리"에서 실제 정보로 채워넣으면 됩니다.
const DEFAULT_SUPPLIERS = [
  { id: "corp-a", code: "법인A", name: "", bizNo: "", ceoName: "", address: "", bizType: "", bizItem: "", email: "" },
  { id: "corp-b", code: "법인B", name: "", bizNo: "", ceoName: "", address: "", bizType: "", bizItem: "", email: "" },
  { id: "corp-c", code: "법인C", name: "", bizNo: "", ceoName: "", address: "", bizType: "", bizItem: "", email: "" },
];

export async function loadSuppliers() {
  const list = await store().get(KEY, { type: "json" });
  if (Array.isArray(list) && list.length) return list;
  return DEFAULT_SUPPLIERS;
}

export async function saveSuppliers(list) {
  await store().setJSON(KEY, list);
}

// 엑셀의 "발행법인" 값(코드 또는 상호)으로 등록된 법인을 찾음. 공백/대소문자 차이는 무시.
export function findSupplier(suppliers, keyValue) {
  const v = norm(keyValue);
  if (!v) return null;
  return (
    suppliers.find((s) => norm(s.code) === v) ||
    suppliers.find((s) => norm(s.name) === v) ||
    suppliers.find((s) => s.id === keyValue) ||
    null
  );
}

function norm(v) {
  return String(v || "").trim().toLowerCase();
}
