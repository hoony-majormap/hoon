# findings 레코드 스키마

이 스키마가 파이프라인 전체의 계약이다. Dissector는 경쟁사 1곳당 이 형태의 JSON 1개를 `$RUN/raw/<id>.json`에 쓴다. `pipeline.py validate`가 통과시키지 않으면 병합에서 빠진다.

## 계약 필드 17개

| # | 필드 | 필수 | 형식 | 설명 |
|---|---|---|---|---|
| 1 | `name` | 필수 | 문자열 | 상품 / 기관명 (원문 표기 그대로) |
| 2 | `segment` | 필수 | 열거 | `어학당` / `사설학원` / `온라인코스` / `앱` / `과외` / `유학원` / `공공무료` |
| 3 | `target` | | 문자열 | 대상 국적·레벨·목적 |
| 4 | `price_raw` | 필수 | 문자열 | 표기된 그대로 (예: `320,000원 / 960분`). 확인 못 했으면 `"미확인"` |
| 5 | `currency` | 필수 | 문자열 | `KRW` / `USD` 등 ISO 코드 |
| 6 | `duration_weeks` | | 숫자 | 주 수 |
| 7 | `total_hours` | 필수 | 숫자 또는 null | 총 시수. 추정이면 8번 true + `hours_basis` 필수. 근거가 전혀 없으면 null |
| 8 | `hours_estimated` | 필수 | bool | 시수를 추정했는지 |
| 9 | `price_per_hour_krw` | 필수 | 숫자 또는 null | 정규화 핵심 필드. **병합 단계에서 스크립트가 재계산해 덮어쓴다.** Dissector 값과 1% 넘게 다르면 `pph_recomputed` 플래그 |
| 10 | `curriculum_summary` | | 문자열 | 2-3문장 |
| 11 | `topik_claim` | | 문자열 | 급수 보장·환불 조건 원문 요지. 없으면 `"언급 없음"` |
| 12 | `channel` | | 문자열 | 모집 경로 (자사 사이트 / 집계 사이트 / SNS / 교내 공지 …) |
| 13 | `differentiator` | | 문자열 | 한 문장 |
| 14 | `source_urls` | 필수 | URL 배열 | 실제로 연 페이지만. 비면 리포트에서 제외 |
| 15 | `published_at` | 필수 | `YYYY[-MM[-DD]]` 또는 `"date_unknown"` | 소스의 발행·수정일 또는 기수 표기 시점. 부분 날짜는 그 기간의 첫날로 본다 |
| 16 | `confidence` | 필수 | `A`/`B`/`C` | Dissector의 자기 판정. 병합에서 규칙 등급·검증 권고와 비교해 **가장 낮은 값**으로 확정 |
| 17 | `checked_at` | 필수 | `YYYY-MM-DD` | 수집 시점 |

## 보조 필드 (결정론적 정규화용)

| 필드 | 필수 | 설명 |
|---|---|---|
| `id` | 필수 | `candidates.json`의 id (`c1`, `c2` …) |
| `price_amount` | 필수 | 총액 숫자. 무료면 `0`, 확인 못 했으면 `null` |
| `fx` | 외화면 필수 | `{"rate_to_krw": 1390.5, "as_of": "2026-10-17", "source_url": "..."}` |
| `hours_basis` | 추정이면 필수 | 시수 계산·추정 근거. 예: `"주 1회 2시간 × 8주"`, `"8주 과정, 주 2회 90분으로 추정 — 동일 기관 정규반 기준"` |
| `source_type` | 필수 | 가격·시수를 확인한 소스의 유형: `official` / `aggregator` / `press` / `sns` / `blog` / `snippet` |
| `topik_guarantee` | | 급수 미달 시 환불·재수강 등 성과 보장이 있으면 `true` |
| `evidence` | 필수 | 원문 인용 배열 `[{"field": "price_raw", "quote": "...", "url": "..."}]`. 가격을 적었으면 `price_raw` 인용, 시수를 확정값으로 적었으면 `total_hours` 인용 필수 |

## 계산 규칙 (스크립트가 적용)

```
price_per_hour_krw = round(price_amount × fx.rate_to_krw / total_hours)   # KRW면 rate = 1
```

- `price_amount` null → 계산 불가 (`pph_unavailable`, C등급)
- `total_hours` null → 계산 불가
- 외화인데 `fx` 없음 → 계산 불가
- 무료(`price_amount: 0`) → 0원. 지표의 중앙값·스프레드 계산에서는 빠지고 무료 개수로 따로 센다

## 예시

```json
{
  "id": "c1",
  "name": "예시대학교 한국어교육원 TOPIK 대비반",
  "segment": "어학당",
  "target": "TOPIK 3-4급 목표 재학 외국인 유학생",
  "price_raw": "100,000원 / 8주",
  "price_amount": 100000,
  "currency": "KRW",
  "fx": null,
  "duration_weeks": 8,
  "total_hours": 16,
  "hours_estimated": true,
  "hours_basis": "8주 과정, 시수 미표기. 같은 기관 정규 특강이 주 1회 2시간이라 동일하게 추정",
  "price_per_hour_krw": 6250,
  "curriculum_summary": "듣기·읽기·쓰기 영역별 기출 풀이. 마지막 주 모의고사.",
  "topik_claim": "언급 없음",
  "topik_guarantee": false,
  "channel": "교내 공지",
  "differentiator": "재학생 전용 저가 대비반",
  "source_urls": ["https://example.ac.kr/notice/123"],
  "source_type": "official",
  "published_at": "2026-08-20",
  "confidence": "B",
  "checked_at": "2026-10-17",
  "evidence": [
    {"field": "price_raw", "quote": "수강료: 100,000원 (8주)", "url": "https://example.ac.kr/notice/123"}
  ]
}
```

(위 값은 형식 예시일 뿐 실존 기관 데이터가 아니다.)
