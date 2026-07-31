import { getStore } from "@netlify/blobs";
import seed from "../../data/seed.js";

export default async (req, context) => {
  try {
    const store = getStore("dashboard");
    let dataset = await store.get("dataset", { type: "json" });

    if (!dataset) {
      dataset = seed;
      await store.setJSON("dataset", seed);
    }

    return new Response(JSON.stringify(dataset), {
      status: 200,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: String((err && err.message) || err) }),
      { status: 500, headers: { "content-type": "application/json; charset=utf-8" } }
      );
  }
};

export const config = { path: "/api/data" };
