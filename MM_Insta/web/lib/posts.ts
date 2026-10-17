// Supabase insta_posts 읽기 — 서버에서만 실행 (publishable 키는 브라우저로 보내지 않는다)
import "server-only";

export type Track = "admissions" | "trend";
export type Status = "generating" | "ready" | "failed";

export interface GateResult {
  gate: string;
  pass: boolean;
  violations: string[];
  warnings: string[];
}

export interface Post {
  id: string;
  post_date: string;
  track: Track;
  status: Status;
  title: string | null;
  headline: string | null;
  caption: string | null;
  hashtags: string[];
  image_urls: string[];
  source_url: string | null;
  source_name: string | null;
  mode: string;
  version: number;
  error: string | null;
  posted_at: string | null;
  updated_at: string;
  gate_report: {
    pass?: boolean;
    attempts?: { attempt: number; gates: GateResult[] }[];
    g4?: GateResult | null;
  } | null;
}

const LIST_COLUMNS =
  "id,post_date,track,status,title,headline,hashtags,image_urls,source_name,mode,version,error,posted_at,updated_at";

function config() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) throw new Error("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY 환경변수가 없습니다.");
  // 새 형식(sb_publishable_…)은 apikey 헤더로만, 예전 anon JWT는 Bearer로도 보낸다
  const headers: Record<string, string> = key.startsWith("sb_") ? { apikey: key } : { apikey: key, Authorization: `Bearer ${key}` };
  return { url: url.replace(/\/$/, ""), headers };
}

async function rest<T>(path: string, init?: RequestInit): Promise<T> {
  const { url, headers } = config();
  const res = await fetch(`${url}/rest/v1/${path}`, {
    ...init,
    headers: { ...headers, "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Supabase ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export async function listPosts(from: string, to: string): Promise<Post[]> {
  return rest<Post[]>(
    `insta_posts?select=${LIST_COLUMNS}&post_date=gte.${from}&post_date=lte.${to}&order=post_date.asc`,
  );
}

export async function getPost(date: string): Promise<Post | null> {
  const rows = await rest<Post[]>(`insta_posts?select=*&post_date=eq.${date}&limit=1`);
  return rows[0] ?? null;
}

export async function setPosted(id: string, posted: boolean): Promise<string | null> {
  return rest<string | null>("rpc/insta_set_posted", {
    method: "POST",
    body: JSON.stringify({ p_id: id, p_posted: posted }),
  });
}
