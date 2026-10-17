import { NextResponse } from "next/server";
import { isValidDate } from "@/lib/week";

// GitHub Actions 'MM_Insta · 카드뉴스 생성' 워크플로를 실행한다 (생성·렌더는 Actions에서)
export async function POST(req: Request) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) return NextResponse.json({ error: "GITHUB_TOKEN이 설정되지 않았어요" }, { status: 501 });
  const { date } = (await req.json().catch(() => ({}))) as { date?: string };
  if (!isValidDate(date)) return NextResponse.json({ error: "날짜 형식이 잘못됐어요" }, { status: 400 });

  const repo = process.env.GITHUB_REPO ?? "hoony-majormap/hoon";
  const workflow = process.env.GITHUB_WORKFLOW ?? "mm-insta-generate.yml";
  const ref = process.env.GITHUB_REF ?? "main";
  const res = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({ ref, inputs: { date } }),
  });
  if (!res.ok) return NextResponse.json({ error: `GitHub ${res.status}: ${await res.text()}` }, { status: 502 });
  return NextResponse.json({ ok: true });
}
