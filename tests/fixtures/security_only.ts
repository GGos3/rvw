export async function handler(req: Req) {
  const token = req.query.token;
  console.log("auth token:", token);
  const sql = `SELECT * FROM users WHERE id = '${req.query.id}'`;
  await db.raw(sql);
  const url = req.query.next;
  return fetch(url);
}
