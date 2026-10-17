"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { Status } from "@/lib/posts";

interface PostView {
  id: string;
  status: Status;
  images: string[];
  caption: string;
  hashtags: string[];
  posted: boolean;
  error: string | null;
  version: number;
}

interface PostActionsProps {
  date: string;
  post: PostView | null;
  canGenerate: boolean;
}

// ── 클립보드·파일 도우미 ───────────────────────────────────────
async function copyText(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
}

// 클립보드는 PNG만 받으므로 JPEG를 PNG로 바꿔서 넣는다
async function toPng(url: string): Promise<Blob> {
  const blob = await (await fetch(url)).blob();
  const bitmap = await createImageBitmap(blob);
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0);
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("PNG 변환 실패"))), "image/png"),
  );
}

function fileName(date: string, i: number) {
  return `majormap_${date}_${String(i + 1).padStart(2, "0")}.jpg`;
}

function download(file: File) {
  const url = URL.createObjectURL(file);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

// ── 컴포넌트 ───────────────────────────────────────────────────
export function PostActions({ date, post, canGenerate }: PostActionsProps) {
  const router = useRouter();
  const [toast, setToast] = useState<string | null>(null);
  const [files, setFiles] = useState<File[] | null>(null);
  const [posted, setPosted] = useState(post?.posted ?? false);
  const [busy, setBusy] = useState(false);

  const ready = post?.status === "ready" && post.images.length > 0;
  const hashtagText = post?.hashtags.join(" ") ?? "";
  const fullText = useMemo(() => (post ? `${post.caption}\n\n${hashtagText}`.trim() : ""), [post, hashtagText]);

  const notify = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  }, []);

  // 공유 버튼을 누른 순간 바로 공유창이 뜨도록 사진을 미리 받아 둔다 (iOS는 지연되면 공유를 막음)
  useEffect(() => {
    if (!ready) return;
    let alive = true;
    Promise.all(
      post.images.map(async (url, i) => {
        const blob = await (await fetch(url)).blob();
        return new File([blob], fileName(date, i), { type: "image/jpeg" });
      }),
    )
      .then((f) => alive && setFiles(f))
      .catch(() => alive && setFiles(null));
    return () => {
      alive = false;
    };
  }, [ready, post?.images, date]); // eslint-disable-line react-hooks/exhaustive-deps

  // 만드는 중이면 15초마다 새로고침
  useEffect(() => {
    if (post?.status !== "generating") return;
    const t = window.setInterval(() => router.refresh(), 15000);
    return () => window.clearInterval(t);
  }, [post?.status, router]);

  const canShare =
    !!files && typeof navigator !== "undefined" && !!navigator.canShare && navigator.canShare({ files });

  async function shareAll() {
    if (!files) return;
    copyText(fullText); // 공유창이 뜨기 전에 본문을 복사해 둔다 → 인스타에서 붙여넣기만
    try {
      await navigator.share({ files });
      notify("본문·해시태그도 복사됐어요. 인스타에서 붙여넣기 하세요");
    } catch (e) {
      if ((e as Error).name !== "AbortError") notify("공유가 안 돼요. '6장 모두 저장'을 써 주세요");
    }
  }

  async function saveAll() {
    if (!files) return notify("사진을 아직 불러오는 중이에요");
    for (const f of files) {
      download(f);
      await new Promise((r) => setTimeout(r, 350));
    }
    notify("6장을 저장했어요");
  }

  async function copyImage(i: number) {
    try {
      await navigator.clipboard.write([new ClipboardItem({ "image/png": toPng(post!.images[i]) })]);
      notify(`${i + 1}번 사진을 복사했어요`);
    } catch {
      notify("이 브라우저는 사진 복사를 지원하지 않아요. 저장을 눌러 주세요");
    }
  }

  async function togglePosted() {
    if (!post) return;
    setBusy(true);
    const next = !posted;
    const res = await fetch(`/api/posts/${post.id}/posted`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ posted: next }),
    });
    setBusy(false);
    if (!res.ok) return notify("저장하지 못했어요. 잠시 뒤 다시 눌러 주세요");
    setPosted(next);
    notify(next ? "업로드 완료로 표시했어요" : "표시를 취소했어요");
    router.refresh();
  }

  async function regenerate() {
    if (!confirm(post?.status === "ready" ? "지금 카드를 새로 만들까요? 기존 카드는 바뀝니다." : "이 날짜 카드를 만들까요?")) return;
    setBusy(true);
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date }),
    });
    setBusy(false);
    if (!res.ok) return notify(`요청 실패: ${(await res.json().catch(() => ({}))).error ?? res.status}`);
    notify("만들기 시작! 3~5분 뒤 자동으로 바뀌어요");
    window.setTimeout(() => router.refresh(), 20000);
  }

  return (
    <>
      {!ready && (
        <section className="mt-6 rounded-lg border border-border-default bg-surface p-5">
          {post?.status === "generating" ? (
            <p className="font-semibold">AI가 카드를 만드는 중이에요… (보통 3~5분, 자동으로 새로고침돼요)</p>
          ) : post?.status === "failed" ? (
            <>
              <p className="font-semibold text-danger">자동 검수를 통과하지 못했어요</p>
              {post.error && <p className="mt-1 text-sm text-text-secondary">{post.error}</p>}
            </>
          ) : (
            <p className="font-semibold">아직 이 날짜 카드가 없어요</p>
          )}
          <p className="mt-1 text-sm text-text-secondary">평일 아침 6시에 그날 카드가 자동으로 만들어져요.</p>
          {canGenerate && post?.status !== "generating" && (
            <button
              type="button"
              onClick={regenerate}
              disabled={busy}
              className="mt-4 rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-gray-0 hover:bg-accent-hover active:bg-accent-pressed"
            >
              지금 만들기
            </button>
          )}
        </section>
      )}

      {ready && (
        <div className="mt-6 grid gap-8 desktop:grid-post">
          {/* 1. 사진 */}
          <section aria-labelledby="photos">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 id="photos" className="text-lg font-semibold">
                <span className="text-accent">1</span> 사진 {post.images.length}장
              </h2>
              <div className="flex gap-2">
                {canShare && (
                  <button type="button" onClick={shareAll} className="btn-outline">
                    공유하기
                  </button>
                )}
                <button type="button" onClick={saveAll} className="btn-outline">
                  {post.images.length}장 모두 저장
                </button>
              </div>
            </div>
            <ol className="mt-3 grid grid-cols-2 gap-3 tablet:grid-cols-3">
              {post.images.map((src, i) => (
                <li key={src} className="overflow-hidden rounded-md border border-border-default bg-surface">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={src} alt={`${i + 1}번째 카드`} className="aspect-[4/5] w-full object-cover" loading="lazy" />
                  <div className="flex border-t border-border-default text-sm font-medium">
                    <span className="grid w-9 place-items-center bg-gray-50 text-xs font-bold text-text-secondary">{i + 1}</span>
                    <button type="button" onClick={() => copyImage(i)} className="flex-1 py-2 hover:bg-gray-50">
                      복사
                    </button>
                    <button
                      type="button"
                      onClick={() => files?.[i] && download(files[i])}
                      className="flex-1 border-l border-border-default py-2 hover:bg-gray-50"
                    >
                      저장
                    </button>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          {/* 2. 본문·해시태그 / 3. 업로드 표시 */}
          <div className="flex flex-col gap-6 desktop:sticky desktop:top-20 desktop:self-start">
            <section aria-labelledby="caption" className="rounded-lg border border-border-default bg-surface p-4">
              <h2 id="caption" className="text-lg font-semibold">
                <span className="text-accent">2</span> 본문 · 해시태그
              </h2>
              <p className="mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap rounded-md bg-gray-50 p-3 text-base leading-relaxed">
                {post.caption}
              </p>
              <button type="button" onClick={() => copyText(post.caption).then(() => notify("본문을 복사했어요"))} className="btn-outline mt-2 w-full">
                본문만 복사
              </button>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {post.hashtags.map((t) => (
                  <span key={t} className="rounded-sm bg-navy-50 px-2 py-0.5 text-sm font-medium text-navy-800">
                    {t}
                  </span>
                ))}
              </div>
              <button type="button" onClick={() => copyText(hashtagText).then(() => notify("해시태그를 복사했어요"))} className="btn-outline mt-2 w-full">
                해시태그만 복사
              </button>
              <button
                type="button"
                onClick={() => copyText(fullText).then(() => notify("본문+해시태그를 복사했어요"))}
                className="mt-4 w-full rounded-md bg-accent py-3 text-base font-semibold text-gray-0 hover:bg-accent-hover active:bg-accent-pressed"
              >
                본문 + 해시태그 한 번에 복사
              </button>
            </section>

            <section aria-labelledby="done" className="rounded-lg border border-border-default bg-surface p-4">
              <h2 id="done" className="text-lg font-semibold">
                <span className="text-accent">3</span> 올렸으면 표시
              </h2>
              <button
                type="button"
                onClick={togglePosted}
                disabled={busy}
                aria-pressed={posted}
                className={`mt-3 w-full rounded-md py-3 text-base font-semibold ${
                  posted ? "bg-navy-800 text-gray-0" : "border-2 border-navy-800 text-navy-800 hover:bg-navy-50"
                }`}
              >
                {posted ? "✓ 업로드 완료 (취소하려면 누르기)" : "인스타에 올렸어요"}
              </button>
            </section>

            {canGenerate && (
              <button type="button" onClick={regenerate} disabled={busy} className="text-sm font-medium text-text-secondary underline underline-offset-2">
                마음에 안 들면 다시 만들기 (v{post.version})
              </button>
            )}
          </div>
        </div>
      )}

      {/* 모바일 하단 고정: 공유가 되면 '사진+본문 한 번에', 안 되면 본문 복사 */}
      {ready && (
        <div className="fixed inset-x-0 bottom-0 z-30 border-t border-border-default bg-surface p-3 desktop:hidden">
          <button
            type="button"
            onClick={canShare ? shareAll : () => copyText(fullText).then(() => notify("본문+해시태그를 복사했어요"))}
            className="w-full rounded-md bg-navy-800 py-3.5 text-base font-semibold text-gray-0 active:bg-navy-900"
          >
            {canShare ? `사진 ${post.images.length}장 공유 + 본문 복사` : "본문 + 해시태그 복사"}
          </button>
        </div>
      )}

      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-24 z-40 flex justify-center px-4 desktop:bottom-8">
        {toast && <p className="rounded-full bg-navy-900 px-4 py-2.5 text-sm font-medium text-gray-0 shadow-lg">{toast}</p>}
      </div>
    </>
  );
}
