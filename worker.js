/* Retribution Against God — セーブ用 Worker (D1)
   静的ファイルは Assets、/api/* だけここで処理する。 */
const MAX_USERS = 5000;
const MAX_DATA_BYTES = 40000;
const SESSION_MS = 60 * 24 * 3600 * 1000;
const LIMITS = {
  login: { max: 8, windowMs: 15 * 60 * 1000 },     // 同じID+IPのログイン失敗
  register: { max: 5, windowMs: 3600 * 1000 }      // 同じIPの登録
};

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,            
  display TEXT NOT NULL,          
  salt TEXT NOT NULL,
  hash TEXT NOT NULL,             
  created INTEGER NOT NULL
)`,
  `CREATE TABLE IF NOT EXISTS saves (
  user_id TEXT PRIMARY KEY,
  data TEXT NOT NULL,
  t INTEGER NOT NULL,
  updated INTEGER NOT NULL
)`,
  `CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  expires INTEGER NOT NULL
)`,
  `CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)`,
  `CREATE TABLE IF NOT EXISTS attempts (
  key TEXT PRIMARY KEY,
  count INTEGER NOT NULL,
  window_start INTEGER NOT NULL
)`
];
let schemaReady = false;
async function ensureSchema(env) {
  if (schemaReady) return;
  await env.DB.batch(SCHEMA.map((q) => env.DB.prepare(q)));
  schemaReady = true;
}

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const err = (status, code) => json({ ok: false, error: code }, status);

const hex = (buf) => [...new Uint8Array(buf)].map((x) => x.toString(16).padStart(2, "0")).join("");
async function sha256(text) { return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text))); }
const randHex = (n) => hex(crypto.getRandomValues(new Uint8Array(n)));
function safeEq(a, b) {
  if (a.length !== b.length) return false;
  let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}
const validId = (id) => typeof id === "string" && /^[A-Za-z0-9_-]{3,20}$/.test(id);
const validAuth = (a) => typeof a === "string" && /^[0-9a-f]{64}$/.test(a);

async function limited(env, key, rule) {
  const now = Date.now();
  const row = await env.DB.prepare("SELECT count, window_start FROM attempts WHERE key = ?").bind(key).first();
  if (!row || now - row.window_start > rule.windowMs) return false;
  return row.count >= rule.max;
}
async function bump(env, key, rule) {
  const now = Date.now();
  const row = await env.DB.prepare("SELECT count, window_start FROM attempts WHERE key = ?").bind(key).first();
  if (!row || now - row.window_start > rule.windowMs) {
    await env.DB.prepare("INSERT OR REPLACE INTO attempts (key, count, window_start) VALUES (?, 1, ?)").bind(key, now).run();
  } else {
    await env.DB.prepare("UPDATE attempts SET count = count + 1 WHERE key = ?").bind(key).run();
  }
}
async function clearAttempts(env, key) { await env.DB.prepare("DELETE FROM attempts WHERE key = ?").bind(key).run(); }

async function newSession(env, userId) {
  const token = randHex(32), now = Date.now();
  await env.DB.prepare("INSERT INTO sessions (token_hash, user_id, expires) VALUES (?, ?, ?)").bind(await sha256(token), userId, now + SESSION_MS).run();
  await env.DB.prepare("DELETE FROM sessions WHERE expires < ?").bind(now).run();
  return token;
}
async function authed(env, request) {
  const h = request.headers.get("authorization") || "";
  const m = /^Bearer ([0-9a-f]{64})$/.exec(h);
  if (!m) return null;
  const row = await env.DB.prepare("SELECT user_id, expires FROM sessions WHERE token_hash = ?").bind(await sha256(m[1])).first();
  if (!row || row.expires < Date.now()) return null;
  return { userId: row.user_id, tokenHash: await sha256(m[1]) };
}
function cleanData(d) {
  if (!d || typeof d !== "object" || Array.isArray(d)) return null;
  const s = JSON.stringify(d);
  if (s.length > MAX_DATA_BYTES) return null;
  return s;
}

async function register(env, request, ip) {
  let b; try { b = await request.json(); } catch (e) { return err(400, "bad_json"); }
  if (!validId(b.id) || !validAuth(b.auth)) return err(400, "bad_input");
  const dataStr = b.data === undefined ? "{}" : cleanData(b.data);
  if (dataStr === null) return err(400, "bad_data");
  const key = "reg:" + ip;
  if (await limited(env, key, LIMITS.register)) return err(429, "rate_limited");
  const cnt = await env.DB.prepare("SELECT COUNT(*) AS n FROM users").first();
  if (cnt && cnt.n >= MAX_USERS) return err(503, "full");
  const id = b.id.toLowerCase();
  if (await env.DB.prepare("SELECT 1 FROM users WHERE id = ?").bind(id).first()) { await bump(env, key, LIMITS.register); return err(409, "exists"); }
  const salt = randHex(16), now = Date.now();
  const t = +(b.data && b.data.t) || now;
  try {
    await env.DB.batch([
      env.DB.prepare("INSERT INTO users (id, display, salt, hash, created) VALUES (?, ?, ?, ?, ?)").bind(id, b.id, salt, await sha256(b.auth + salt), now),
      env.DB.prepare("INSERT INTO saves (user_id, data, t, updated) VALUES (?, ?, ?, ?)").bind(id, dataStr, t, now)
    ]);
  } catch (e) { return err(409, "exists"); }
  await bump(env, key, LIMITS.register);
  return json({ ok: true, token: await newSession(env, id) });
}

async function login(env, request, ip) {
  let b; try { b = await request.json(); } catch (e) { return err(400, "bad_json"); }
  if (!validId(b.id) || !validAuth(b.auth)) return err(400, "bad_input");
  const id = b.id.toLowerCase(), key = "login:" + id + ":" + ip;
  if (await limited(env, key, LIMITS.login)) return err(429, "rate_limited");
  const u = await env.DB.prepare("SELECT salt, hash FROM users WHERE id = ?").bind(id).first();
  const calc = await sha256(b.auth + (u ? u.salt : "x".repeat(32)));
  if (!u || !safeEq(calc, u.hash)) { await bump(env, key, LIMITS.login); return err(401, "invalid"); }
  await clearAttempts(env, key);
  const s = await env.DB.prepare("SELECT data, t FROM saves WHERE user_id = ?").bind(id).first();
  let data = null; try { data = s ? JSON.parse(s.data) : null; } catch (e) {}
  return json({ ok: true, token: await newSession(env, id), data: data, t: s ? s.t : 0 });
}

async function getSave(env, request) {
  const a = await authed(env, request); if (!a) return err(401, "unauthorized");
  const s = await env.DB.prepare("SELECT data, t FROM saves WHERE user_id = ?").bind(a.userId).first();
  if (!s) return json({ ok: true, data: null, t: 0 });
  let data = null; try { data = JSON.parse(s.data); } catch (e) {}
  return json({ ok: true, data: data, t: s.t });
}

async function putSave(env, request) {
  const a = await authed(env, request); if (!a) return err(401, "unauthorized");
  let b; try { b = await request.json(); } catch (e) { return err(400, "bad_json"); }
  const dataStr = cleanData(b.data); if (dataStr === null) return err(400, "bad_data");
  const t = +b.t || Date.now();
  const s = await env.DB.prepare("SELECT t FROM saves WHERE user_id = ?").bind(a.userId).first();
  if (s && s.t > t) return err(409, "stale");          // サーバーの方が新しい → クライアントが取り込み直す
  await env.DB.prepare("INSERT INTO saves (user_id, data, t, updated) VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET data = excluded.data, t = excluded.t, updated = excluded.updated")
    .bind(a.userId, dataStr, t, Date.now()).run();
  return json({ ok: true, t: t });
}

async function logout(env, request) {
  const a = await authed(env, request);
  if (a) await env.DB.prepare("DELETE FROM sessions WHERE token_hash = ?").bind(a.tokenHash).run();
  return json({ ok: true });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
    if (!env.DB) return err(503, "no_db");
    const ip = request.headers.get("cf-connecting-ip") || "0";
    const route = url.pathname.slice(5), m = request.method;
    try {
      await ensureSchema(env);
      if (route === "ping" && m === "GET") return json({ ok: true });
      if (route === "register" && m === "POST") return await register(env, request, ip);
      if (route === "login" && m === "POST") return await login(env, request, ip);
      if (route === "save" && m === "GET") return await getSave(env, request);
      if (route === "save" && m === "PUT") return await putSave(env, request);
      if (route === "logout" && m === "POST") return await logout(env, request);
      return err(404, "not_found");
    } catch (e) {
      return err(500, "server");
    }
  }
};
