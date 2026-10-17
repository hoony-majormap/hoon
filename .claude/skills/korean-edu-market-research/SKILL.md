---
name: korean-edu-market-research
description: "외국인 대상 한국어 교육 시장의 경쟁 상품을 키워드 하나로 해부해, 기획 의사결정용 report.md와 dashboard.html을 만드는 리서치 파이프라인. 발굴(Scout) → 사람 승인 게이트 → 병렬 해부(Dissector) → 검증(Verifier) → 분석(Analyst) 순서로 서브에이전트를 돌리고, 모든 가격을 시간당 원가로 환산하며, 출처 없는 숫자는 리포트에 올리지 않는다. 다음이 나오면 사용한다 — 한국어 교육 경쟁 분석, 한국어 학원·어학당·온라인 코스·앱 가격 비교, TOPIK 대비반 시장 조사, 외국인 유학생 한국어 상품 기획, '한국어 교육 리서치', '경쟁 리서치 돌려줘'."
---

# 한국어 교육 경쟁 리서치

키워드 하나를 받아 한국어 교육 경쟁 상품을 해부하고, 교육 사업 기획자가 바로 의사결정에 쓸 수 있는 리포트를 만든다. 최종 목적은 외국인 유학생이 TOPIK 점수를 못 받아 체류 자격을 잃는 문제를 줄일 상품을 설계하는 것이고, 이 스킬은 그 상품 설계에 필요한 시장 정보를 생산한다.

산출물은 두 개다: `report.md` (성공 조건 산출물), `dashboard.html` (시각화 1장). 둘 다 `findings.json` 하나에서만 수치를 읽는다.

## 지키는 원칙

1. **출처 없는 숫자는 리포트에 올라가지 않는다.** 환각이 이 파이프라인의 유일한 치명적 실패다. "파일이 생성됨"이 아니라 "모든 수치에 확인 가능한 출처가 붙어 있음"이 완료 기준이다.
2. **사람이 한 번 끼어든다.** 경쟁사 선정은 자동화하지 않는다.
3. **모든 가격은 시간당 원가(KRW/h)로 환산된다.** 환산은 LLM이 아니라 `scripts/pipeline.py`가 한다.
4. **개수를 지정하지 않는다.** "찾을 수 있는 만큼". 모자라면 "확인된 3곳"으로 쓴다.
5. **산수·등급·병합·렌더링은 스크립트가 한다.** 에이전트는 JSON을 만들 뿐, 수치를 계산하거나 리포트를 직접 쓰지 않는다.

## 파일

| 파일 | 내용 |
|---|---|
| `references/schema.md` | findings 레코드 계약 (17개 필드 + 보조 필드) |
| `references/source-tiers.md` | 신뢰도 A/B/C 판정 규칙과 신선도 컷오프 |
| `references/query-sets.md` | 세그먼트 6축 × 한·영 2트랙 쿼리 템플릿 |
| `references/source-access.md` | 소스 접근성 스파이크 결과 (쿼리 전략의 기준) |
| `references/report-template.md` | report.md 골격 |
| `agents/scout.md` · `dissector.md` · `verifier.md` · `analyst.md` | 서브에이전트 지시문 |
| `assets/dashboard-template.html` | 대시보드 템플릿 (외부 의존성 없음) |
| `scripts/pipeline.py` | init / validate / merge / render / check |

아래에서 `$SKILL`은 이 스킬 디렉토리, `$RUN`은 이번 실행 디렉토리다.

## 파이프라인

### 0. 사전 점검

- 오늘 날짜를 확인한다. 검색 쿼리에 연도를 넣고, 신선도 판정 기준일로 쓴다.
- `references/source-access.md`를 읽는다. 마지막 스파이크가 30일 넘었거나 실행 환경이 바뀌었으면(로컬 ↔ 클라우드, 네트워크 정책 변경) **스파이크를 다시 한다**: 세그먼트별 대표 URL 6개를 WebFetch로 한 번씩 열어 성공/실패 표를 갱신한다. 10분 이내.
- **WebFetch가 전부 실패하는 환경이면 멈추고 사용자에게 알린다.** 검색 스니펫만으로는 C등급밖에 안 나오고, C등급은 본문에 못 들어간다. 그 상태로 리포트를 만들면 빈 리포트거나 위험물이다.

### 1. 실행 디렉토리 생성

```bash
python3 $SKILL/scripts/pipeline.py init --keyword "<키워드>"
# → output/{YYYY-MM-DD}-{키워드}/  (run.json, raw/)
```

### 2. 발굴 — Scout (1개)

Agent 도구로 general-purpose 서브에이전트 1개를 띄운다. 프롬프트는 `agents/scout.md` 전문 + 키워드 + `$RUN` 경로 + 스킬 경로. Scout는 `$RUN/candidates.json`을 쓰고 한 줄만 돌려준다.

### 3. 승인 게이트 (사람)

`candidates.json`을 표로 보여준다: 번호 / 이름 / 세그먼트 / 언어 트랙 / 한 줄 요약 / URL / 관련도. 그리고 묻는다: "심층 분석할 3-5개를 번호로 골라 주세요."

- 사용자가 고르면 `run.json`의 `selection`을 `{"mode": "manual", "selected_ids": [...]}`로 쓴다.
- **무응답 규칙**: 비대화형 실행(스케줄, `claude -p`)이거나 사용자가 "알아서 해"라고 하면 관련도 상위 4개로 진행하고 `{"mode": "auto", ...}`로 쓴다. 리포트 머리말에 `경쟁사 자동 선정됨 — 검토 필요`가 자동으로 박힌다.
- 세그먼트가 한쪽으로 몰려 있으면(예: 전부 어학당) 선택 전에 그 사실을 한 줄로 알려준다.

### 4. 해부 — Dissector 단독 테스트 (1개 먼저)

**병렬로 띄우기 전에 반드시 1개로 스키마를 확인한다.** 스키마가 틀린 채로 5개를 돌리면 5배로 틀린다.

1. 선택된 첫 경쟁사로 Dissector 1개를 띄운다. 프롬프트 = `agents/dissector.md` 전문 + 담당 할당(아래) + 스키마 경로.
2. `python3 $SKILL/scripts/pipeline.py validate $RUN/raw/<id>.json`
3. FAIL이면 오류를 Dissector에게 돌려보내 고치게 하거나 지시문을 손본다. OK가 나올 때까지 다음 단계로 가지 않는다.

담당 할당은 경쟁사마다 명시한다 (병렬 중복 방지):

```
담당 id: c2
담당 경쟁사: <이름>
시작 URL: <candidates.json의 url>
허용 도메인: <해당 기관 도메인>, 그리고 이 기관을 직접 다룬 집계·보도 페이지
금지: 다른 후보 경쟁사 조사, 허용 범위 밖 일반 검색 결과 수집
```

### 5. 해부 — 병렬 실행

나머지 선택 경쟁사마다 Dissector를 **한 메시지에서 동시에** 띄운다. 각자 `$RUN/raw/<id>.json`을 쓰고 한 줄만 돌려준다. 원문은 서브에이전트 안에서 소멸한다 — 메인은 원문을 읽지 않는다. 끝나면 전부 `validate`를 돌린다.

### 6. 검증 — Verifier (1개)

작성과 분리된 별도 서브에이전트. 프롬프트 = `agents/verifier.md` 전문 + `$RUN` 경로. 수집 과정은 넘기지 않는다. Verifier는 `$RUN/verification.json`을 쓴다. 수치는 고치지 않고 플래그와 등급 권고만 단다.

### 7. 병합

```bash
python3 $SKILL/scripts/pipeline.py merge $RUN
```

스크립트가 하는 일: 스키마 위반·출처 없음 행 제외 → 시간당 원가 재계산 → 신선도·출처 유형·추정 여부·검증 권고로 등급 확정 (가장 낮은 것) → C등급은 부록으로 → 지표 계산 → `findings.json`.

### 8. 분석 — Analyst (1개)

프롬프트 = `agents/analyst.md` 전문 + `$RUN` 경로. `findings.json`만 읽고 `$RUN/analysis.json`(결론, 빈틈 1-3개, 상품 제안 1안)을 쓴다. 모든 주장은 본문 항목 id를 `refs`로 단다.

### 9. 렌더링과 판정

```bash
python3 $SKILL/scripts/pipeline.py render $RUN
python3 $SKILL/scripts/pipeline.py check  $RUN
```

`check`가 FAIL이면 **"완료"라고 보고하지 않는다.** 실패 항목과 원인을 그대로 알리고, 해결 방법(재해부, 소스 보강, 범위 축소)을 제안한다. 그럴듯한데 틀린 리포트는 없는 것보다 나쁘다.

### 10. 보고

사용자에게 `report.md` 경로, `dashboard.html` 경로, 판정 결과, 출처 확인 비율, 자동 선정 여부, 미확인 항목 수를 짧게 알린다. 리포트 본문을 채팅에 붙여 넣지 않는다.

## 시간 예산이 모자랄 때

단일 경쟁사 JSON이 `validate`를 통과하지 못한 채 시간이 흐르면 병렬과 대시보드를 버리고 MD까지만 목표를 낮춘다. 경쟁사가 3개밖에 안 잡히면 3개로 쓴다.

## 하지 않는 것 (MVP 범위 밖)

송출국 언어(베트남어·중국어·우즈베크어) 검색, 포지셔닝 좌표 자동 산출, 누적 DB·가격 추이, 스케줄 실행, 스크린샷·퍼널 분석, VOC 감성 분석, PDF 출력, 동적 렌더링 크롤링. 요청이 오면 Phase 2 항목이라고 알리고, 이번 실행에서는 하지 않는다.

## 경쟁사를 참고할 때의 선

구조·방식·가격 모델은 배워도 되지만 상세페이지 문구·이미지·교재·상품명은 쓰지 않는다. "구조는 배우고 문장은 새로 쓴다." (`kids-ai-edu-product` 스킬과 같은 원칙)
