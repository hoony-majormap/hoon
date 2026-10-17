# 쿼리 세트 — 세그먼트 6축 × 언어 2트랙

`{kw}` = 입력 키워드, `{year}` = 올해. **쿼리에 연도를 넣는다** — 안 넣으면 2013년 공지가 상위에 뜬다.

한국어 쿼리만 돌리면 어학당·지자체·사설학원만 잡히고, 온라인 플랫폼·앱·해외 교육원·튜터 마켓은 거의 안 잡힌다. 그래서 세그먼트마다 쿼리를 쪼개고 영어 트랙을 같이 돌린다.

| 세그먼트 | 한국어 트랙 | 영어 트랙 |
|---|---|---|
| 어학당 | `{year} 대학 한국어교육원 {kw} 수강료` · `{year} 어학당 정규과정 등록금 시수` | `{year} Korean language institute university tuition fee hours` · `{year} Korean language program for international students tuition` |
| 사설학원 | `{year} 한국어학원 {kw} 수강료` · `외국인 한국어학원 수강료 교육청 신고` | `{year} Korean language academy Seoul foreigners price` |
| 온라인코스 | `{year} 온라인 한국어 강의 {kw} 가격` · `TOPIK 인강 수강료 {year}` | `{year} online Korean course TOPIK price` · `{year} learn Korean online course hours certificate` |
| 앱 | `한국어 학습 앱 구독료 {year}` | `{year} best Korean learning app subscription price` · `{year} TOPIK prep app price` |
| 과외 | `외국인 한국어 과외 시간당 {year}` | `{year} Korean tutor online hourly rate` · `{year} Korean lessons tutor price per hour` |
| 유학원 | `{year} 한국 유학 어학연수 패키지 한국어 비용` | `{year} study in Korea language course package agency fee` |
| 공공무료 (보조) | `{year} 외국인 무료 한국어 교실 {kw}` · `{year} 다문화 한국어 교육 무료` | `{year} free Korean class foreigners Korea government` |

## 운용 규칙

- 세그먼트당 최소 한국어 1회 + 영어 1회. 접근성 표(`source-access.md`)에서 막힌 세그먼트도 **발굴 검색은 한다** — 막히는 것은 해부 단계의 직접 열람이다.
- 결과 수가 적다고 쿼리를 무한정 늘리지 않는다. 세그먼트당 3회까지.
- 사설학원은 개별 학원 사이트보다 **교육청 신고 기반 학원 집계 사이트**를 먼저 친다. 수강료가 `320,000원 (960분)`처럼 구조화되어 있다.
- 해외 한국교육원·세종학당은 어학당/공공무료 중 운영 주체에 맞는 쪽으로 분류한다 (유료면 어학당, 무료면 공공무료).
- 키워드가 특정 목적(예: TOPIK 대비)이면, 일반 회화 과정은 관련도를 낮게 매긴다.
