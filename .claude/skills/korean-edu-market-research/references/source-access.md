# 소스 접근성 스파이크 결과

이 표가 쿼리 전략과 Dissector의 수집 경로를 정한다. 30일이 지났거나 실행 환경이 바뀌면 다시 찍는다 (SKILL.md 0단계).

## 최근 스파이크

- **실행일**: 2026-10-17
- **환경**: Claude Code 클라우드 세션 (claude.ai/code), 네트워크 정책 제한 환경
- **도구**: WebFetch, WebSearch, curl

| 세그먼트 | 대표 URL | WebFetch | 비고 |
|---|---|---|---|
| 어학당 | https://lang.kaist.ac.kr/pages/view/lang_03 | ❌ 실패 | `getaddrinfo ENOTFOUND` |
| 사설학원 (집계) | https://academy.prompie.com/academies/detail/y7rzo3t/그린한국어학원/ | ❌ 실패 | `getaddrinfo ENOTFOUND` |
| 온라인코스 | https://www.coursera.org/learn/learn-korean | ❌ 실패 | `getaddrinfo ENOTFOUND` |
| 앱 | https://apps.apple.com/us/app/duolingo-language-lessons/id570060128 | ❌ 실패 | `getaddrinfo ENOTFOUND` |
| 과외 | https://www.italki.com/en/teachers/korean | ❌ 실패 | `getaddrinfo ENOTFOUND` |
| 유학원·공공 | https://www.studyinkorea.go.kr/ | ❌ 실패 | `getaddrinfo ENOTFOUND` |

- **WebSearch**: ✅ 동작 (예: `KAIST 어학센터 한국어 과정 수강료 2026` → 공식 페이지 URL과 요약 반환)
- **curl**: ❌ 프록시가 `CONNECT tunnel failed, response 403` — 외부 호스트 전반이 네트워크 정책으로 차단

### 해석

이 실패는 **사이트 쪽이 아니라 실행 환경의 네트워크 정책** 때문이다. 6개 세그먼트가 같은 오류로 전부 막혔고, 정적 HTML 사이트(KAIST)와 SPA(italki)의 차이가 드러나지 않았다. 즉 기획서 병목 5(동적 렌더링)는 **아직 미검증**이다.

이 환경에서 파이프라인을 돌리면 모든 레코드가 `snippet` → C등급 → 부록행이 되고, `check`의 출처 확인 비율 항목이 FAIL한다. 정상 동작이다 — 스니펫만으로 만든 리포트는 위험물이다.

### 다음 스파이크에서 할 일

1. 로컬 Claude Code, 또는 네트워크 접근을 넓힌 클라우드 환경에서 위 6개 URL을 다시 WebFetch.
2. 각 행에 기록: 성공/실패, 가격·시수 텍스트가 본문에 보이는지 (SPA면 빈 껍데기만 오는지), 날짜 표기가 보이는지.
3. 실패한 세그먼트는 우회 경로를 적는다: 검색 스니펫 + 리뷰 블로그 + 보도자료로 간접 수집 → 최대 B등급 (원문을 연 2차 소스) 또는 C등급 (스니펫뿐).

## 표 양식 (갱신용)

| 세그먼트 | 대표 URL | WebFetch | 가격 텍스트 보임 | 날짜 보임 | 우회 경로 |
|---|---|---|---|---|---|
| 어학당 | | | | | |
| 사설학원 (집계) | | | | | |
| 온라인코스 | | | | | |
| 앱 | | | | | |
| 과외 | | | | | |
| 유학원·공공 | | | | | |
