// 날짜는 모두 한국 시간(KST) 기준 YYYY-MM-DD 문자열로 다룬다.
import type { Track } from "./posts";

export const WEEK_KO = ["일", "월", "화", "수", "목", "금", "토"];

export const TRACK_LABEL: Record<Track, string> = {
  admissions: "입시 브리핑",
  trend: "요즘 트렌드",
};

/** 월·수·금 = 입시, 화·목 = 트렌드 (Date.getUTCDay 기준) */
export const SCHEDULE: Record<number, Track> = { 1: "admissions", 2: "trend", 3: "admissions", 4: "trend", 5: "admissions" };

export function todayKST(): string {
  return new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10);
}

function toDate(iso: string): Date {
  return new Date(`${iso}T00:00:00Z`);
}

export function addDays(iso: string, days: number): string {
  const d = toDate(iso);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function weekday(iso: string): number {
  return toDate(iso).getUTCDay();
}

/** 보여줄 주의 월요일. 주말에는 다가오는 주를 보여준다 (월요일 카드 미리 확인). */
export function mondayOf(iso: string): string {
  const wd = weekday(iso);
  if (wd === 6) return addDays(iso, 2);
  if (wd === 0) return addDays(iso, 1);
  return addDays(iso, 1 - wd);
}

export function isValidDate(s: string | undefined): s is string {
  return !!s && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(toDate(s).getTime());
}

export function formatDay(iso: string): string {
  const [, m, d] = iso.split("-").map(Number);
  return `${m}월 ${d}일 (${WEEK_KO[weekday(iso)]})`;
}

export function weekRangeLabel(monday: string): string {
  const [, m1, d1] = monday.split("-").map(Number);
  const [, m2, d2] = addDays(monday, 4).split("-").map(Number);
  return m1 === m2 ? `${m1}월 ${d1}일 – ${d2}일` : `${m1}월 ${d1}일 – ${m2}월 ${d2}일`;
}
