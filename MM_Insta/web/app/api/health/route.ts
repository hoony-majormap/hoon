import { NextResponse } from "next/server";
import { listPosts } from "@/lib/posts";
import { addDays, todayKST } from "@/lib/week";

export const dynamic = "force-dynamic";

// 비밀번호 없이 열리는 상태 확인용 — 개수만 돌려준다 (내용 없음)
export async function GET() {
  try {
    const today = todayKST();
    const posts = await listPosts(addDays(today, -7), addDays(today, 14));
    const ready = posts.filter((p) => p.status === "ready").length;
    return NextResponse.json({ ok: true, today, posts: posts.length, ready });
  } catch (e) {
    return NextResponse.json({ ok: false, error: e instanceof Error ? e.message : String(e) }, { status: 503 });
  }
}
