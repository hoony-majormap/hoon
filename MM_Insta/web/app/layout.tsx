import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "메이저맵 인스타 스튜디오",
  description: "요일별 인스타 카드뉴스를 확인하고 사진·본문·해시태그를 복사해 올리는 곳",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#202B45" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body className="min-h-dvh">
        <header className="sticky top-0 z-20 border-b border-border-default bg-surface/95 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-page items-center gap-3 px-4 desktop:px-6">
            <Link href="/" className="flex items-center gap-2" aria-label="이번 주 보드로">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo.png" alt="메이저맵" className="h-4 w-auto" />
              <span className="text-sm font-semibold text-text-secondary">인스타 스튜디오</span>
            </Link>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
