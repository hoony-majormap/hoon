---
name: majormap-brand
description: 메이저맵(MAJOR MAP) 브랜드 아이덴티티(BI) 가이드 — 공식 로고(워드마크·심볼 SVG), 전용·보조 색상(Major Map Red #EA5645 / Navy #202B45 / Mint #90C6B4), 배경색별 로고 색상 규정, 단색(그레이스케일) 규정, 전용 서체 Wanted Sans, 그래픽 모티프. 메이저맵 로고를 넣거나, 메이저맵 브랜드 색·폰트를 써야 하는 모든 산출물(웹페이지, 아티팩트, 슬라이드, 카드뉴스, 썸네일, 문서, 포스터, 이메일, 차트, Figma 디자인)을 만들 때 반드시 사용한다. 트리거 예시 — '메이저맵', 'MAJOR MAP', 'majormap', '메이저맵 로고', '브랜드 컬러', '우리 브랜드 스타일로', 'BI 가이드', '브랜딩 맞춰서'.
---

# 메이저맵 BI (Brand Identity) 가이드

출처: `[메이저맵]251210 brand identity manual guide_basic` (2025-12-10). 원본 페이지 렌더는 `references/pages/`에 있다. 규정이 애매하면 해당 페이지 이미지를 직접 열어 확인한다.

## 1. 로고

| 파일 | 용도 |
|---|---|
| `assets/logo/majormap-wordmark-{red,navy,white,black}.svg` | 기본형 BI (심볼 + "MAJOR MAP" 워드마크) — 가로 약 8.4 : 세로 1 |
| `assets/logo/majormap-symbol-{red,navy,white,black}.svg` | 심볼(기울어진 M) 단독 — 파비콘, 앱 아이콘, 좁은 공간, 우상단 마크 |

- 원본 PDF에서 추출한 벡터 패스다. **로고를 폰트로 타이핑하거나 다시 그리지 말고 반드시 이 SVG를 쓴다.** HTML에는 SVG를 인라인하거나 `<img>`로 넣는다(아티팩트처럼 단일 파일이면 인라인).
- 기본형 BI는 모든 매체에 가장 우선 적용한다.
- **최소 사용 크기: 워드마크 높이 2.5mm** (화면에서는 약 10px 이하로 줄이지 않는다).
- 로고를 늘리거나(비율 변형), 회전, 기울이기, 외곽선·그림자·그라디언트 추가, 지정되지 않은 색으로 칠하기 금지.
- 주변에 최소 심볼 높이의 절반 이상 여백을 둔다(가이드 원문에 수치는 없음 — 실무 기본값).

## 2. 색상

### 전용 색상
| 이름 | HEX | RGB | CMYK | PANTONE | 의미 |
|---|---|---|---|---|---|
| **Major Map Red** (전용색) | `#EA5645` | 234 86 69 | 0 85 75 0 | 2034C | 새로운 진로와 가능성을 탐색하는 여정, 도전적·진취적 태도, 밝은 에너지·명확한 방향성 |

### 보조 색상
| 이름 | HEX | RGB | CMYK | PANTONE | 의미 |
|---|---|---|---|---|---|
| **Major Map Navy** | `#202B45` | 32 43 69 | 94 88 56 33 | 648C | 전문성, 무게감·안정감. 텍스트와 구분 영역에 활용 |
| **Major Map Mint** | `#90C6B4` | 144 198 180 | 50 5 35 0 | 572C | 회복과 균형, 심리적 편안함. 어두운 배경 위 가독성·개방감 |

### 확장(배경) 색상 — 색상 활용 규정 페이지에 수록된 배경색
| 이름(임의) | HEX |
|---|---|
| Red Light 1 | `#FF6456` |
| Red Light 2 | `#FF746B` |
| Teal | `#168091` |
| Sky Blue | `#92B8F4` |
| Yellow | `#EFDF7F` |
| Paper (가이드 배경 회색) | `#F6F7F8` |

> 확장 색상 HEX는 PDF 렌더에서 샘플링한 값이다(공식 수치 미기재). 인쇄물 등 정확도가 중요하면 디자이너에게 확인한다.

색은 인쇄·웹에 따라 명도·채도 차이가 날 수 있으니 위 수치를 정확히 사용한다. 메이저맵 BI의 기본은 PANTONE 2034C(Red)이며, 경우에 따라 보조색 적용 가능.

## 3. 배경색별 로고 색상 규정 (BASIC SYSTEM 08)

**기본은 White 배경**(배경색 없음) 위의 Red 로고. 불가피하게 배경색을 쓸 때는 아래 표의 조합만 쓴다.

| 배경 | Full Color | 1도 표현 | Negative |
|---|---|---|---|
| Red `#EA5645` | Navy 로고 | White | White |
| Navy `#202B45` | **Red 로고** | White | White |
| Mint `#90C6B4` | Navy 로고 | Black | White |
| Teal `#168091` | Mint 로고 | White | White |
| Sky Blue `#92B8F4` | Navy 로고 | Black | White |
| Yellow `#EFDF7F` | Navy 로고 | Black | White |
| White / Paper | Red 로고 | Navy 또는 Black | — |

## 4. 단색 규정 (BASIC SYSTEM 09)

4원색 구현이 불가능할 때만 사용. 검정 농도(배경 명도)에 따라:
- 배경 **0–40% 회색** (흰색~`#B3B3B3`): **Red 로고** 유지
- 배경 **50–100% 회색** (`#999999`~`#1A1A1A`): **White 로고**

## 5. 서체 — Wanted Sans (국문·영문 공통 전용 서체)

- 국문·영문 모두 **Wanted Sans** 하나로 통일. 용도에 따라 굵기별로 사용한다.
- 굵기: Regular 400 · Medium 500 · SemiBold 600 · Bold 700 · ExtraBold 800 · Black 900 · ExtraBlack 950
- 매체 특성상 다른 서체가 필요하면 협의 후 사용(대체 시 Pretendard → 시스템 sans-serif 순).
- 웹 로드:
  ```html
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/wanteddev/wanted-sans@v1.0.3/packages/wanted-sans/fonts/webfonts/variable/split/WantedSansVariable.min.css">
  ```
  ```css
  font-family: "Wanted Sans Variable", "Wanted Sans", "Pretendard", -apple-system, sans-serif;
  ```
  (아티팩트처럼 외부 스타일시트를 Google Fonts만 허용하는 환경에서는 로드하지 말고 폴백 스택만 쓴다.)
- 가이드 문서의 타이포 관례: 섹션 라벨은 대문자 영문 소형(예: `BASIC SYSTEM 06`), 제목은 Bold 국문 Navy, 본문은 작은 Regular. 강조 카피는 `#MAJOR MAP RED`처럼 대문자 이탤릭 Light도 쓴다.

## 6. 그래픽 모티프

심볼의 기울어진 사선 "M" 형태를 크게 확대·반복·크롭한 패턴(`references/pages/99-graphic-motif.png`):
- Navy 위 Sky Blue(노이즈 텍스처) 반복 패턴
- Mint → Navy 그라디언트 위 사선 조각
- Red 위 반투명 밝은 Red 심볼 확대
표지·배너·카드뉴스 배경 등 장식 영역에만 쓰고, 로고 자체를 변형하는 용도로 쓰지 않는다.

## 7. 디자인 토큰

`assets/tokens.css`를 그대로 가져다 쓴다(CSS 변수 + Tailwind 매핑 예시 포함).

## 작업 체크리스트
1. 로고는 `assets/logo/` SVG를 사용했는가? (타이핑·재작도 금지)
2. 배경색–로고색 조합이 3번 표에 있는가?
3. 주색은 Red, 텍스트·구분 영역은 Navy, 보조/완화는 Mint인가? 표에 없는 임의 색을 브랜드 색처럼 쓰지 않았는가?
4. 서체는 Wanted Sans(또는 합의된 폴백)인가?
5. 로고 최소 크기(2.5mm / ~10px 높이)와 여백을 지켰는가?

메이저스쿨/메이저맵 **제품 UI**(Figma 디자인 시스템, 브레이크포인트, 회원 유형별 화면 규칙, Next.js 코드 컨벤션)는 `majorschool-design-context` 스킬이 있으면 함께 로드한다. 이 스킬은 BI(로고·색·서체)의 원천이다.
