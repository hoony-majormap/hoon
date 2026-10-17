import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusPill, TrackBadge } from "@/components/Badges";
import { PostActions } from "@/components/PostActions";
import { getPost, type GateResult } from "@/lib/posts";
import { SCHEDULE, formatDay, isValidDate, mondayOf, weekday } from "@/lib/week";

export const dynamic = "force-dynamic";

export default async function PostPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  if (!isValidDate(date)) notFound();
  const post = await getPost(date);
  const track = post?.track ?? SCHEDULE[weekday(date)];
  const canGenerate = Boolean(process.env.GITHUB_TOKEN);
  const gates: GateResult[] = [
    ...(post?.gate_report?.attempts?.at(-1)?.gates ?? []),
    ...(post?.gate_report?.g4 ? [post.gate_report.g4] : []),
  ];

  return (
    <main className="mx-auto max-w-page px-4 pb-32 pt-5 desktop:px-6 desktop:pb-16 desktop:pt-8">
      <Link href={`/?week=${mondayOf(date)}`} className="text-sm font-medium text-text-secondary hover:text-text-primary">
        ← 이번 주 보드
      </Link>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <h1 className="text-2xl font-bold">{formatDay(date)}</h1>
        {track && <TrackBadge track={track} />}
        <StatusPill status={post?.status ?? "empty"} posted={!!post?.posted_at} />
      </div>
      {post?.title && (
        <p className="mt-1 text-sm text-text-secondary">
          소재: {post.source_url ? (
            <a href={post.source_url} target="_blank" rel="noreferrer" className="underline underline-offset-2">
              {post.title}
            </a>
          ) : (
            post.title
          )}
          {post.source_name && <> · {post.source_name}</>}
        </p>
      )}

      {!track && <p className="mt-6 text-text-secondary">주말에는 게시하지 않아요.</p>}

      {track && (
        <PostActions
          date={date}
          post={
            post && {
              id: post.id,
              status: post.status,
              images: post.image_urls,
              caption: post.caption ?? "",
              hashtags: post.hashtags,
              posted: !!post.posted_at,
              error: post.error,
              version: post.version,
            }
          }
          canGenerate={canGenerate}
        />
      )}

      {gates.length > 0 && (
        <details className="mt-10 rounded-lg border border-border-default bg-surface p-4 text-sm">
          <summary className="cursor-pointer font-semibold">자동 검수 결과 ({post?.mode === "seed" ? "초기 샘플" : "AI 생성"} · v{post?.version})</summary>
          <ul className="mt-3 space-y-2">
            {gates.map((g) => (
              <li key={g.gate}>
                <span className={g.pass ? "font-semibold text-success" : "font-semibold text-danger"}>
                  {g.gate} {g.pass ? "통과" : "실패"}
                </span>
                {[...g.violations, ...g.warnings].map((m) => (
                  <p key={m} className="ml-4 text-text-secondary">· {m}</p>
                ))}
              </li>
            ))}
          </ul>
        </details>
      )}
    </main>
  );
}
