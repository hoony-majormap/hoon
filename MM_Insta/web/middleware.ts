import { NextResponse, type NextRequest } from "next/server";

// APP_PASSWORD가 설정돼 있으면 간단한 비밀번호(Basic 인증)로 막는다. 아이디는 아무거나.
export function middleware(req: NextRequest) {
  const password = process.env.APP_PASSWORD;
  if (!password) return NextResponse.next();
  const header = req.headers.get("authorization") ?? "";
  const [scheme, encoded] = header.split(" ");
  if (scheme === "Basic" && encoded) {
    const decoded = atob(encoded);
    if (decoded.slice(decoded.indexOf(":") + 1) === password) return NextResponse.next();
  }
  return new NextResponse("비밀번호가 필요해요", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="MAJOR MAP Insta Studio", charset="UTF-8"' },
  });
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico|api/health).*)"] };
