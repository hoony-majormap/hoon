import Link from "next/link";
import { StatusPill, TrackBadge } from "@/components/Badges";
import { listPosts, type Post } from "@/lib/posts";
import { SCHEDULE, TRACK_LABEL, WEEK_KO, addDays, formatDay, isValidDate, mondayOf, todayKST, weekRangeLabel, weekday } from "@/lib/week";

export const dynamic = "force-dynamic";

export default async function WeekBoard({ searchParams }: { searchParams: Promise<{ week?: string }> }) {
  const { week } = await searchParams;
  const today = todayKST();
  const monday = mondayOf(isValidDate(week) ? week : today);
  const days = [0, 1, 2, 3, 4].map((i) => addDays(monday, i));

  let posts: Post[] = [];
  let loadError: string | null = null;
  try {
    posts = await listPosts(days[0], days[4]);
  } catch (e) {
    loadError = e instanceof Error ? e.message : String(e);
  }
  const byDate = new Map(posts.map((p) => [p.post_date, p]));
  const isThisWeek = monday === mondayOf(today);
  const weekend = weekday(today) === 0 || weekday(today) === 6;

  return (
    <main className="mx-auto max-w-page px-4 pb-16 pt-6 desktop:px-6 desktop:pt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-accent">{isThisWeek ? (weekend ? "다가오는 주" : "이번 주") : "다른 주"} 인스타</p>
          <h1 className="text-2xl font-bold desktop:text-h1">{weekRangeLabel(monday)}</h1>
          <p className="mt-1 text-sm text-text-secondary">
            월·수·금 <b className="font-semibold text-text-primary">{TRACK_LABEL.admissions}</b> · 화·목{" "}
            <b className="font-semibold text-text-primary">{TRACK_LABEL.trend}</b>
          </p>
        </div>
        <nav aria-label="주 이동" className="flex items-center gap-1 text-sm font-medium">
          <Link href={`/?week=${addDays(monday, -7)}`} className="rounded-md px-3 py-2 hover:bg-gray-100">
            ← 이전 주
          </Link>
          {!isThisWeek && (
            <Link href="/" className="rounded-md px-3 py-2 hover:bg-gray-100">
              이번 주
            </Link>
          )}
          <Link href={`/?week=${addDays(monday, 7)}`} className="rounded-md px-3 py-2 hover:bg-gray-100">
            다음 주 →
          </Link>
        </nav>
      </div>

      {loadError && (
        <p role="alert" className="mt-6 rounded-md bg-red-50 p-4 text-sm text-red-700">
          게시물을 불러오지 못했어요. {loadError}
        </p>
      )}

      <ol className="mt-6 grid gap-3 tablet:grid-cols-2 desktop:grid-cols-5 desktop:gap-4">
        {days.map((day) => (
          <li key={day}>
            <DayCard day={day} post={byDate.get(day)} isToday={day === today} />
          </li>
        ))}
      </ol>
    </main>
  );
}

function DayCard({ day, post, isToday }: { day: string; post?: Post; isToday: boolean }) {
  const track = post?.track ?? SCHEDULE[weekday(day)];
  const thumb = post?.status === "ready" ? post.image_urls[0] : undefined;
  return (
    <Link
      href={`/post/${day}`}
      className={`group flex h-full gap-3 rounded-lg border bg-surface p-3 transition hover:border-navy-300 desktop:flex-col ${
        isToday ? "border-accent ring-2 ring-red-100" : "border-border-default"
      }`}
    >
      <div className="aspect-[4/5] w-24 shrink-0 overflow-hidden rounded-md bg-gray-50 desktop:w-full">
        {thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={thumb} alt={`${formatDay(day)} 카드뉴스 첫 장`} className="size-full object-cover" loading="lazy" />
        ) : (
          <div className="grid size-full place-items-center text-2xl font-bold text-gray-200" aria-hidden>
            {WEEK_KO[weekday(day)]}
          </div>
        )}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-bold">{formatDay(day)}</span>
          {isToday && <span className="rounded-sm bg-accent px-1.5 text-xs font-bold text-gray-0">오늘</span>}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {track && <TrackBadge track={track} />}
          <StatusPill status={post?.status ?? "empty"} posted={!!post?.posted_at} />
        </div>
        <p className="line-clamp-2 text-sm leading-relaxed text-text-secondary group-hover:text-text-primary">
          {post?.headline ?? (post?.status === "failed" ? "다시 만들기가 필요해요" : "아직 만들어지지 않았어요")}
        </p>
      </div>
    </Link>
  );
}
