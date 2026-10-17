import type { Status, Track } from "@/lib/posts";
import { TRACK_LABEL } from "@/lib/week";

export function TrackBadge({ track }: { track: Track }) {
  const tone = track === "admissions" ? "bg-navy-800 text-gray-0" : "bg-mint-100 text-mint-700";
  return (
    <span className={`inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-semibold ${tone}`}>
      {TRACK_LABEL[track]}
    </span>
  );
}

const STATUS: Record<Status | "empty", { label: string; tone: string }> = {
  ready: { label: "준비됨", tone: "bg-mint-50 text-mint-700" },
  generating: { label: "만드는 중", tone: "bg-navy-50 text-navy-500" },
  failed: { label: "생성 실패", tone: "bg-red-50 text-red-700" },
  empty: { label: "아직 없음", tone: "bg-gray-100 text-gray-500" },
};

export function StatusPill({ status, posted }: { status: Status | "empty"; posted?: boolean }) {
  if (posted) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-navy-800 px-2.5 py-0.5 text-xs font-semibold text-gray-0">
        ✓ 업로드 완료
      </span>
    );
  }
  const s = STATUS[status];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${s.tone}`}>
      {status === "generating" && <span className="size-1.5 animate-pulse rounded-full bg-current" aria-hidden />}
      {s.label}
    </span>
  );
}
