import { NextResponse } from "next/server";
import { setPosted } from "@/lib/posts";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) return NextResponse.json({ error: "잘못된 id" }, { status: 400 });
  const { posted } = (await req.json().catch(() => ({}))) as { posted?: boolean };
  try {
    const postedAt = await setPosted(id, Boolean(posted));
    return NextResponse.json({ posted_at: postedAt });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 502 });
  }
}
