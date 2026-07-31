import { getStore } from "@netlify/blobs";
import * as XLSX from "xlsx";
import seed from "../../data/seed.js";

function shiftMonth(ym, delta) {
const [y, m] = ym.split("-").map(Number);
const d = new Date(Date.UTC(y, m - 1 + delta, 1));
return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

function toNum(v) {
if (v === null || v === undefined || v === "") return null;
const n = Number(v);
return Number.isNaN(n) ? null : n;
}

export default async (req, context) => {
if (req.method !== "POST") {
return json({ error: "POST 요청만 지원합니다." }, 405);
}

let body;
try {
body = await req.json();
} catch {
return json({ error: "요청 본문을 읽을 수 없습니다." }, 400);
}

const { password, base64 } = body || {};

const expected = process.env.UPLOAD_PASSWORD;
if (expected && password !== expected) {
return json({ error: "비밀번호가 올바르지 않습니다." }, 401);
}
if (!base64) {
return json({ error: "업로드된 파일이 없습니다." }, 400);
}

let wb;
try {
const buf = Buffer.from(base64, "base64");
wb = XLSX.read(buf, { type: "buffer" });
} catch (err) {
return json({ error: "엑셀 파일을 읽는 중 오류가 발생했습니다: " + String(err.message || err) }, 400);
}

const companySheetName =
wb.SheetNames.find((n) => n.trim() === "전사") || wb.SheetNames[0];
const teamSheetName =
wb.SheetNames.find((n) => n.trim() === "팀별") ||
wb.SheetNames[1] ||
wb.SheetNames[0];

const companyRows = XLSX.utils.sheet_to_json(wb.Sheets[companySheetName], {
defval: null,
});
const teamRows = XLSX.utils.sheet_to_json(wb.Sheets[teamSheetName], {
defval: null,
});

if (!companyRows.length) {
return json({ error: "'전사' 시트에서 데이터를 찾지 못했습니다." }, 400);
}

const validCompanyRows = companyRows.filter((r) =>
/^\d{4}-\d{2}$/.test(String(r["월"] || "").trim())
);
if (!validCompanyRows.length) {
return json(
{
error:
"'전사' 시트에서 올바른 '월' 값(YYYY-MM 형식)을 가진 행을 찾지 못했습니다.",
},
400
);
}
const companyRow = validCompanyRows[validCompanyRows.length - 1];
const month = String(companyRow["월"]).trim();

const validTeamRows = teamRows.filter(
(r) =>
r["팀이름"] &&
String(r["팀이름"]).trim() !== "" &&
r["실적매출"] !== null &&
r["실적매출"] !== ""
);
if (!validTeamRows.length) {
return json(
{ error: "'팀별' 시트에서 유효한 팀 데이터를 찾지 못했습니다. (팀이름, 실적매출은 필수)" },
400
);
}

const store = getStore("dashboard");
let dataset = await store.get("dataset", { type: "json" });
if (!dataset) dataset = JSON.parse(JSON.stringify(seed));

const priorMonth = shiftMonth(month, -12);
const priorCompany = dataset.company.find((c) => c["월"] === priorMonth);

const newCompanyEntry = {
월: month,
실적매출: toNum(companyRow["실적매출"]),
전년_실적매출: priorCompany ? priorCompany["실적매출"] : null,
영업이익: toNum(companyRow["영업이익"]),
전년_영업이익: priorCompany ? priorCompany["영업이익"] : null,
손익: toNum(companyRow["손익"]),
전년_손익: priorCompany ? priorCompany["손익"] : null,
"매출액(귀속)": toNum(companyRow["매출액(귀속)"]),
"전년_매출액(귀속)": priorCompany ? priorCompany["매출액(귀속)"] : null,
};

dataset.company = dataset.company.filter((c) => c["월"] !== month);
dataset.company.push(newCompanyEntry);
dataset.company.sort((a, b) => a["월"].localeCompare(b["월"]));

const newTeamEntries = validTeamRows.map((r) => ({
월: month,
팀이름: String(r["팀이름"]).trim(),
실적매출: toNum(r["실적매출"]),
변동금: toNum(r["변동금"]),
이익금: toNum(r["이익금"]),
재직인원: toNum(r["재직인원"]),
특이사항: r["특이사항"] ? String(r["특이사항"]).trim() : null,
}));

dataset.teams = dataset.teams.filter((t) => t["월"] !== month);
dataset.teams = dataset.teams.concat(newTeamEntries);

const teamNameSet = new Set(dataset.teams_list || []);
newTeamEntries.forEach((t) => teamNameSet.add(t["팀이름"]));
dataset.teams_list = Array.from(teamNameSet);

const monthSet = new Set(dataset.months || []);
monthSet.add(month);
dataset.months = Array.from(monthSet).sort();

await store.setJSON("dataset", dataset);

return json({ ok: true, month, teamCount: newTeamEntries.length });
};

function json(obj, status = 200) {
return new Response(JSON.stringify(obj), {
status,
headers: { "content-type": "application/json; charset=utf-8" },
});
}

export const config = { path: "/api/upload" };
