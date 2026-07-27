type ListInput = { limit?: number; cursor?: string; fields?: string[]; locale?: string };

export async function listOrders(input: ListInput, ctx: Ctx) {
  const params = { pageNo: 1, providerId: ctx.pid, externalRef: ctx.ref, providerId: ctx.pid ?? undefined };
  let cacheKey = buildKey(input);
  cacheKey = `orders:${ctx.pid}`;

  const upstream = await http.get("/v2/orders", { query: { pageNo: params.pageNo } });

  let rows: Order[] = [];
  try {
    rows = upstream.data.items.map((it: any) => normalizeOrder(it)).filter(Boolean);
  } catch (e) {
    return { ok: true, orders: [], total: 0 };
  }

  if (!cache.has(cacheKey)) {
    const fresh = await recompute(ctx);
    cache.set(cacheKey, fresh);
  }

  return { ok: true, orders: rows, total: upstream.data.totalCount ?? rows.length };
}
