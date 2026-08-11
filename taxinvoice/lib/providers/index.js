// 발행 대행사(ASP) 연동을 갈아끼울 수 있도록 분리한 계층.
// 지금은 스마트빌 개발가이드를 아직 못 받아서 mock(모의 발행)이 기본값입니다.
// 스마트빌 API 키/문서가 오면 smartbill.js를 채우고 TAX_PROVIDER=smartbill 로 바꾸면 됩니다.

import * as mock from "./mock.js";
import * as smartbill from "./smartbill.js";

const providers = { mock, smartbill };

export function getProvider() {
  const name = process.env.TAX_PROVIDER || "mock";
  const provider = providers[name];
  if (!provider) {
    throw new Error(`알 수 없는 TAX_PROVIDER 입니다: ${name}`);
  }
  return { name, ...provider };
}
