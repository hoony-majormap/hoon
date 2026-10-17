# 유치·초등 영어 학습 앱 — GitHub 오픈소스 사례 리서치 & 워릭 교재 적용안

작성일: 2026-10-17
대상: 워릭프랭클린(Worwick Franklin Institute) 영어유치원 + 초등 연계 영어 학습 앱 기획
근거 자료: GitHub 공개 저장소(별표 기준, 2026-10-17 조회), 구글 드라이브 `교재개발/New_Worwick` 교재 PDF, Notion 「260808_워릭 신규교재 전체 분석」·「파닉스 온라인 학습 서비스 MVP 기획」·「파닉스 앱 파일럿 원 운영안」, 「2027년 교재 라인업 설명 및 가맹원 방문 결과 보고서」

---

## 0. 한 줄 결론

**"유치원생용 영어 앱" 완제품으로 베낄 만한 고별표 오픈소스는 없다.** 아동 전용 영어 앱은 별표 1천 개를 넘는 것이 `hi-kid`(1.2k, AI 회화 데스크톱) 하나뿐이고, 파닉스 전용은 최대 63개(buzzphonics)다.
대신 **"엔진(부품)"은 매우 성숙**하다. 음성 인식·발음 평가·TTS·간격 반복(FSRS)·게임 엔진·텍스트-음원 정렬은 1만~4만 별표 프로젝트가 있다.
따라서 전략은 **"완제품 포크"가 아니라 "검증된 부품 조립 + 워릭 교재 콘텐츠"**다. 콘텐츠(교재 65권 체계 + 워릭 프렌즈 캐릭터 5종)는 이미 우리가 가진 가장 큰 자산이고, 오픈소스 사례들이 못 가진 것도 바로 이것이다.

---

## 1. 우리 현황 요약 (교재·기존 작업물 기준)

### 1-1. 교재 라인업 (New_Worwick, 2027 적용 예정)

| 영역 | 시리즈 | 캐릭터 | 구성 | 대상 |
|---|---|---|---|---|
| Phonics | Phonics Winner 1-1·1-2(알파벳) → 2(단모음 CVC) → 3(장모음 Magic e) → 4·5(미제작) | Coco(본책)·Zoe(워크북) | 6레벨 × SB+WB, 글자당 6p 고정 루틴, 음원 113트랙 | 5~8세 |
| Speaking | Speaking World Rookie → Challenger → Master | Dotty | 월간 4주 워크북, 매주 어휘→문법→페어워크→Show&Tell | 유치~초등 고학년 |
| Reading | Everyday Sight Word(ESW) 리더스 4종+WB, ThinkBuilder, My View Workbook(Savvas 병행) | Mika | 사이트워드 월 24개, 레버스 방식 논픽션 리더스 | 5세~초2 |
| Debate | Debate Lab A·B(·C 미제작) | Woody | 유닛 10p 템플릿, 4단 에세이 | 초1~초4 |
| CLIL | Science Lab Stage 1~3 | — | 주 1실험, 탐구 5요소 | 5~7세 |

### 1-2. 교재 분석에서 확인된 3대 공백 (= 앱이 메울 자리)
1. **디지털 전달체계 전무** — 음원 113+28트랙은 있는데 QR/앱 도달 경로 0
2. **교사용 자료 부재** — 정답지·루브릭·티처스가이드 0
3. **학부모 연계 부재** — 안내문·리포트·가정학습 가이드 0

### 1-3. 가맹원(7개원) 현장 요청 중 앱과 직결되는 것
- **온라인 플랫폼 일원화**: Raz-Kids·SR·Savvas Realize 등 다중 계정 번거로움 → 본사 통합 플랫폼 요청 (세종)
- **전국 통합 평가 시스템**: 성장 추이·전국 석차가 나오는 레벨테스트/분석 (구리)
- **전국 통일 레벨 가이드**: 난이도·진도 속도 본사 표준 (세종)
- **사이트워드·라이팅 라인업 보완** (평택), 파닉스 쓰기 연습량 부족 (세종)
- **동기부여 리워드**: 뱃지·상장·이벤트 월, 전국 스피킹 콘테스트 (세종·평택)

### 1-4. 이미 만들어 둔 것
- **파닉스 MVP** (단일 HTML → Vercel 배포): 음가 학습(78어휘), 소리 합치기(CVC 63), ESW 스토리북 리더 4권, 어휘 카드 94장, 오늘의 숙제 7문항, 스티커 보드. 워릭 프렌즈 적용.
- **파일럿 운영안**: 직영 1개원 5세반 4주, 교재 진도 1:1 동기화, 성공 기준(주 3회 완료 가정 60%, 4주 유지 70%, 만족 4.0)
- **실서비스 기술 제안**: Next.js PWA + Supabase + 교재 음원 스트리밍 + 알림톡

### 1-5. 기존 증거기반 교재 설계 보고서(2026-01, FINAL_REPORT)에서 앱 설계로 옮길 원칙
구글 드라이브의 「증거기반 파닉스→리딩→스피킹 통합 교재 설계안」은 종이 교재 중심 문서라 앱·음성인식은 다루지 않지만, 아래 원칙은 앱 스펙에 그대로 들어가야 한다.

| 원칙 (보고서 원문) | 앱 반영 |
|---|---|
| 재출현 스케줄 "학습일+2일, +7일, +21일", 매일 3~5분 리뷰, 주간 누적복습은 게임형 | FSRS 초기 간격을 이 값으로 고정 세팅, "오늘의 숙제"에 리뷰 2~3문항 자동 삽입, 주 1회 누적복습 미니게임 |
| 발음 피드백 순서: 변별(같다/다르다) → 모델 → 따라말하기 → 단어 속 적용 | 스피킹 화면의 4단계 고정 루틴. 자동 채점보다 **변별 과제**(minimal pair 듣고 고르기)를 먼저 |
| 레벨업은 phonics coverage·정확도 90%·유창성·이해·말하기 다지표, "4요소 중 3개 이상" | 통합 평가 시스템(가맹원 요청)의 승급 규칙. 단일 점수가 아닌 4요소 레이더 |
| "상호작용이 과하면 이해를 방해 — 스크롤·상호작용 최소화"(PIRLS 2026) | 리더스 화면은 탭 미션 3개 이하, 자동 넘김 금지, 애니메이션 절제 |
| 가정연계: 하루 10분 미션, 1~2쪽 리포트(레벨/강점/다음 목표 + 가정 5분 미션 3개) | 알림톡 주간 리포트 템플릿을 이 구조로 고정 |
| 월 1회 형성평가 10~15분, "8~12개 GPC + nonsense 3~5개" | 월말 온라인 퀴즈 문항 구성 규칙 |
| 디코더블→브릿지→레벨드 스펙트럼, 핵심 프레이즈 5~8회 재등장 | 자체 리더스 디지털판의 텍스트 QA 체크(단어 수·재등장 횟수 자동 검사) |
| 유아 디베이트 = 문장 프레임 + 턴테이킹 규칙 | Debate AI 상대는 자유 대화가 아니라 **프레임 채우기**로 제한 |

→ 이번 리서치의 목적은 **이 MVP를 "실서비스"로 키울 때 무엇을 오픈소스에서 가져올지** 정하는 것이다.

---

## 2. GitHub 사례 — 별표 순 (카테고리별)

> 별표는 2026-10-17 GitHub 페이지 기준. 별표 = 관심도이지 "우리에게 맞는 정도"가 아니므로, 각 항목에 **"가져올 것"**을 따로 적었다. 라이선스 열을 반드시 볼 것(§3).

### A. 아동 영어·파닉스 직접 사례 (완제품/프로토타입)

| 순위 | 저장소 | ★ | 스택 | 라이선스 | 무엇인가 | 가져올 것 |
|---|---|---|---|---|---|---|
| 1 | [xiaochong/hi-kid](https://github.com/xiaochong/hi-kid) | 1.2k | Electron+React+TS, 로컬 ASR(Qwen3-ASR)·TTS(kitten)·LLM(Ollama) | MIT(비상업 명시) | 비영어권 아이용 **음성 우선 AI 영어 말하기 파트너**. 느리고 단순한 발화 허용, 스토리텔링·단어게임. 전부 로컬 처리 | "말하면 → 듣고 → 답한다" 파이프라인 설계(VAD→ASR→LLM→TTS 루프), 아이 발화 관용 프롬프트. README에 비상업 조건이 있으니 **코드 복사 말고 구조만 참고** |
| 2 | [xckevin/magic-english-buddy](https://github.com/xckevin/magic-english-buddy) | 311 | React 19+Vite PWA, Dexie(IndexedDB), Kokoro TTS 사전생성 | (LICENSE 확인 필요) | 아동용 **오프라인 우선 영어 읽기 PWA**. L1~L7 90편 단계 해금, 연속 낭독+단어별 하이라이트, 3단 속도, 분단 녹음 회독, 오프라인 사전 1,074단어, 듣고 그림 고르기·단어 조립·문장 순서·빈칸, Buddy 진화·카드·업적·연속기록, 간격복습(회당 10단어), 다중 자녀 프로필·JSON 백업·수료증 | **우리 MVP와 가장 닮은 구조**. "Kokoro로 MP3를 빌드 타임에 생성해 배포(런타임 AI 호출 0)" 방식, 다중 자녀 프로필, 수료증 생성, 문제 유형 4종은 그대로 벤치마크 |
| 3 | [vgwb/Antura](https://github.com/vgwb/Antura) | 125 | Unity 6 | BSD-2 (에셋 CC BY 4.0) | **수상 경력의 아동 문해 게임**(원래 시리아 난민 아동 아랍어 문해용 → 영·불·폴란드어 확장). 미니게임 다수, v3.0 2026 예정 | 유니티라 스택은 안 맞지만 **"문해 미니게임 유형 카탈로그"**로 최고 참고서. 미니게임 설계 문서(antura.org docs)만 읽어도 됨 |
| 4 | [EkaAI-Tech/learn](https://github.com/EkaAI-Tech/learn) | 126 | Flutter | MIT | 아이용 알파벳 A~Z 예시·발음, 동물·신체부위 | 초급 수준. Flutter 선택 시 화면 뼈대 참고 정도 |
| 5 | [hellodeborahuk/buzzphonics](https://github.com/hellodeborahuk/buzzphonics) | 63 | React | MIT | 영국 Phase 2·3 파닉스 사운드 앱(부모+아이), 그림 모드, 게임 | 영국식 **음가(sound) 우선 UI** 사례. 작지만 깔끔. 파닉스 토픽 1위 |
| 6 | [VeteranXYZ/LuciaDictionary](https://github.com/VeteranXYZ/LuciaDictionary) | 145 | Astro+Cloudflare Workers | Apache-2.0 | 중국 가정용 **아이 숙제 문장 → 단어 카드(뜻·발음·난이도 밴드)**, OCR | **"교재 문장 → 단어 카드 자동 분해"** 아이디어. 학부모 동반 학습 UX |
| 7 | [s010s/prehistoric-animal-museum](https://github.com/s010s/prehistoric-animal-museum) | 1.1k | React+Three.js | AGPL-3.0 (글·내레이션 CC BY-NC-SA) | 유아용 이중언어 3D 박물관. 계정·광고·분석 0, 내레이션은 **선택 시에만 재생**, 부모용 후속 질문 가이드 | Science Lab 디지털화 시 참고. "부모 가이드 질문" 패턴은 학부모 연계 공백을 메우는 좋은 장치 |
| 8 | [alfredang/phonics-ai](https://github.com/alfredang/phonics-ai) 외 alfredang 계열 | 1~7 | Next.js+Firebase+Gemini / Swift / Kotlin | — | AI 파닉스 앱 여러 개(연령 9~15) | 별표는 낮으나 **Gemini 실시간 발음 피드백 연결 코드**가 참고 가능 |

**관찰**: 아동 영어 앱은 전부 개인 프로젝트 규모다. 즉 이 시장에 "오픈소스 표준"이 없다 → 우리가 교재+캐릭터+가맹망을 얹으면 차별화가 쉽다.

### B. 언어 학습 앱 완제품 (Duolingo류·종합)

| 순위 | 저장소 | ★ | 스택 | 라이선스 | 무엇인가 | 가져올 것 |
|---|---|---|---|---|---|---|
| 1 | [RealKai42/qwerty-learner](https://github.com/RealKai42/qwerty-learner) | 23.4k | React+TS, Tauri | GPL-3.0 | 타이핑으로 단어 암기. 사전 수십 종, 발음(Youdao), 받아쓰기, 통계 | 초등 고학년 **타이핑×스펠링** 모드(ESW·My View 단어). GPL이라 포크 시 공개 의무 → 아이디어만 |
| 2 | [echo-loop/Echo-Loop](https://github.com/echo-loop/Echo-Loop) | 4.2k | Flutter(Material 3), sherpa-onnx, Drift(SQLite), Supabase | AGPL-3.0 | **정청·섀도잉·간격복습** 영어 듣기말하기 앱. 섀도잉 시 ASR 결과를 원문과 정렬해 맞은 단어 하이라이트+점수. 복습 7회(6시간~28일) | **Speaking World 섀도잉 기능의 설계 원형**. 온디바이스 ASR(sherpa-onnx)로 비용 0. AGPL이므로 코드 포크 금지, 설계 참고 |
| 3 | [kantord/LibreLingo](https://github.com/kantord/LibreLingo) | 2.6k | Python+Svelte, PouchDB | AGPL-3.0 | 커뮤니티형 Duolingo. **코스 = YAML 정의 → JSON 익스포트 → 웹앱**. 아카이브됨(포크 LibreLingoRelive) | **"코스를 데이터(YAML)로 정의하고 앱은 렌더러"** 구조. 우리 교재 65권을 YAML/JSON 커리큘럼 스키마로 옮기는 모델 |
| 4 | [sanidhyy/duolingo-clone](https://github.com/sanidhyy/duolingo-clone) | 680 | Next.js+TS, Drizzle+Neon(Postgres), Clerk, Stripe, react-admin | MIT | Duolingo UI 완전 복제. 하트·XP·퀘스트·샵·구독·관리자 | **MIT + 우리 제안 스택(Next.js)과 동일**. 유닛→레슨→챌린지→옵션 스키마, 진도 액션, 관리자 화면을 그대로 출발점으로 쓸 수 있음 |
| 5 | [bryanjenningz/react-duolingo](https://github.com/bryanjenningz/react-duolingo) | 471 | Next.js+Tailwind+Zustand (T3) | MIT | Duolingo UI 모방 | 프론트 컴포넌트 참고(위 4번과 세트) |
| 6 | [Orenoid/BabelDuck](https://github.com/Orenoid/BabelDuck) | 693 | Next.js+Tailwind, Docker | (확인 필요) | 초보자용 AI 회화. 대화 중 **문법·번역·표현 제안을 사이드 창으로** 받고 본 대화로 복귀 | 초등 Speaking Master/Debate 단계의 AI 회화 UX |
| 7 | [ZackAkil/immersive-language-learning-with-live-api](https://github.com/ZackAkil/immersive-language-learning-with-live-api) | 510 | Vanilla JS+Vite / FastAPI | Apache-2.0 | **Gemini Live API** 실시간 음성 롤플레이(버스기사·이웃 페르소나), 미션형 시나리오 | 저지연 음성 AI 페르소나 = "Dotty와 대화하기" 기능 원형. Apache라 코드 활용 가능 |
| 8 | [subconcept-labs/ulangi](https://github.com/subconcept-labs/ulangi) | 455 | React Native | GPL-3.0 (아카이브) | SRS 플래시카드+사전·TTS·이미지검색 | RN 선택 시 참고. 아카이브라 비추 |
| 9 | [ollinmagno/duolingo-flutter](https://github.com/ollinmagno/duolingo-flutter) | 94 | Flutter | — | Duolingo Flutter 클론 | Flutter 선택 시 UI 참고 |

### C. 음성 엔진 — 발음 평가 · ASR · TTS (가장 성숙한 영역)

| 순위 | 저장소 | ★ | 라이선스 | 무엇인가 | 우리 용도 |
|---|---|---|---|---|---|
| 1 | [m-bain/whisperX](https://github.com/m-bain/whisperX) | 24.6k | BSD-2 | Whisper + wav2vec2 강제정렬 → **단어별 타임스탬프** | 아이 낭독 녹음 → 단어별 맞음/틀림 판정, 분당 정확 단어수(WCPM) 산출 |
| 2 | [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 15.3k | Apache-2.0 | **온디바이스** ASR·TTS·VAD. Android/iOS/Flutter/WebAssembly, 영어 모델(Whisper tiny.en, Parakeet, Zipformer 스트리밍) | 서버비·개인정보 걱정 없는 아이 음성 인식. Echo-Loop가 실제 사용 중 |
| 3 | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | 9.4k | Apache-2.0 | 82M 파라미터 TTS, 미·영 영어 등 다국어, kokoro.js(브라우저) | **교재 어휘·문장 음원을 빌드 타임에 일괄 생성**(ElevenLabs 비용 대체). magic-english-buddy가 이 방식 |
| 4 | [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS) | 7.7k | MIT | 다국어 TTS | Kokoro 대안 |
| 5 | [readbeyond/aeneas](https://github.com/readbeyond/aeneas) | 2.9k | AGPL-3.0 | **텍스트↔내레이션 강제정렬** → 문장/단어 단위 타임코드(SMIL·SRT·JSON) | **이미 있는 교재 음원 113트랙**을 리더스 텍스트와 자동 정렬 → "읽어주며 글자 따라 빛나는" 기능. 도구로만 쓰면(산출물 JSON) AGPL 전염 없음 |
| 6 | [Kyubyong/g2p](https://github.com/Kyubyong/g2p) | 935 | Apache-2.0 | 영어 철자→음소 변환 | 파닉스 단어 자동 음소 분해(a+d=ad 블렌딩 카드 자동 생성), 발음 평가 기준 음소 생성 |
| 7 | [Thiagohgl/ai-pronunciation-trainer](https://github.com/Thiagohgl/ai-pronunciation-trainer) | 525 | AGPL-3.0 | Whisper+Epitran 음소 모델로 발음 채점 웹앱 | 발음 채점 **방식** 참고(코드 포크는 AGPL 주의) |
| 8 | [Halleck45/OpenPronounce](https://github.com/Halleck45/OpenPronounce) | 131 | MIT | **음소 단위 발음 평가** (wav2vec2 espeak 라벨 + 편집거리 정렬 + DTW + 피치/에너지). FastAPI `POST /pronunciation`, Docker, CPU 가능. "Azure Pronunciation Assessment 셀프호스트 대체" | **MIT + API 형태라 그대로 붙일 수 있는 발음 평가 서버**. Speaking World의 Show&Tell·Mini Interview 채점 1순위 후보 |
| 9 | [CUNY-CL/wikipron](https://github.com/CUNY-CL/wikipron), [words/cmu-pronouncing-dictionary](https://github.com/words/cmu-pronouncing-dictionary) | 377 / 81 | Apache / MIT | 발음 사전 | 어휘 카드 발음기호 자동 표기 |

**아동 음성 인식 주의**: 공개 모델은 성인 음성으로 학습되어 **10세 미만 발화에서 오류가 급증**한다(Bambara 아동 읽기 평가 연구: 10세 미만이 잔여 오류 대부분, DrivenData "Kids ASR" 챌린지도 같은 문제 제기). 가나 초등 낭독 연구에서는 파인튜닝 없는 Whisper V2가 WER 10.3으로 사람 채점자와 WCPM이 근접했다. → **유치부는 "채점"이 아니라 "녹음 제출+교사 확인"**, 초등부터 자동 채점을 보조로. 

### D. 복습 알고리즘 (간격 반복)

| 순위 | 저장소 | ★ | 라이선스 | 가져올 것 |
|---|---|---|---|---|
| 1 | [ankitects/anki](https://github.com/ankitects/anki) / [ankidroid/Anki-Android](https://github.com/ankidroid/Anki-Android) | 32.1k / 12.0k | AGPL / GPL | 앱 자체는 아이용 아님. **FSRS를 기본 스케줄러로 채택**했다는 사실이 FSRS 신뢰 근거 |
| 2 | [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki) | 4.1k | MIT | FSRS 알고리즘 원류 |
| 3 | [open-spaced-repetition/ts-fsrs](https://github.com/open-spaced-repetition/ts-fsrs) | 825 | MIT | **npm `ts-fsrs`** — Next.js에 바로 넣을 수 있는 스케줄러. 사이트워드 월 24개·CVC 63개 복습 큐 |
| 4 | [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) | 513 | MIT | 파이썬 백엔드용 |

→ 유아에게는 FSRS의 4단계 평가(Again/Hard/Good/Easy)가 과하다. **아이는 2단계(맞음/틀림)만 보내고 서버에서 FSRS 등급으로 매핑**하는 방식이 Echo-Loop·magic-english-buddy 방식과 맞는다.

### E. 게임 엔진 · 인터랙션

| 저장소 | ★ | 라이선스 | 용도 |
|---|---|---|---|
| [phaserjs/phaser](https://github.com/phaserjs/phaser) | 40.5k | MIT | 웹(Next.js PWA) 안에서 **미니게임**(글자 잡기, 소리 매칭, 미로)만 Phaser 씬으로. v4 WebGL |
| [flame-engine/flame](https://github.com/flame-engine/flame) | 10.8k | MIT | Flutter 선택 시 게임 레이어 |
| [sromku/memory-game](https://github.com/sromku/memory-game) | 597 | — | 아이용 기억 게임 UI 참고 |
| [prashant-andani/AR-Alphabets](https://github.com/prashant-andani/AR-Alphabets) | 128 | — | 웹 AR 알파벳(이벤트·설명회용 아이디어) |
| `tracing_game` (pub.dev, Flutter) | — | — | 글자 따라쓰기(획순 경로 기반). 파닉스 "트레이싱" 단계 디지털화 |
| [MyScript/MyScriptJS](https://github.com/MyScript/MyScriptJS) | 355 | Apache | 웹 손글씨 인식(상용 서버 필요) |

### F. 교육 플랫폼 · 교실 운영

| 저장소 | ★ | 라이선스 | 가져올 것 |
|---|---|---|---|
| [oppia/oppia](https://github.com/oppia/oppia) | 6.9k | Apache-2.0 | "탐색(exploration)" = 대화형 튜터 레슨 모델, 피드백 분기 설계 |
| [learningequality/kolibri](https://github.com/learningequality/kolibri) | 1.2k | MIT | **오프라인 우선 + 교사(coach) 대시보드 + 반 편성** 구조. 가맹원 15개 × 반 × 원생 계층 설계 참고 |
| [KDE/gcompris](https://github.com/gcompris/GCompris-qt) | 264(미러) | AGPL | 2~10세 활동 150+ 카탈로그. 활동 아이디어 창고 |

---

## 3. 라이선스 — 반드시 지킬 선

| 라이선스 | 해당 레포 | 우리가 할 수 있는 것 |
|---|---|---|
| **MIT / Apache / BSD** | duolingo-clone, react-duolingo, OpenPronounce, ts-fsrs, sherpa-onnx, kokoro, whisperX, Phaser, Flame, g2p, kolibri, oppia, buzzphonics, EkaAI/learn, Immergo(Gemini Live) | 코드 복사·수정·상용 서비스 OK (저작권 고지 유지) |
| **GPL-3.0** | qwerty-learner, AnkiDroid, ulangi | 포크해서 배포하면 우리 코드도 공개 의무. **아이디어만** |
| **AGPL-3.0** | Echo-Loop, LibreLingo, aeneas, ai-pronunciation-trainer, anki, prehistoric-museum, GCompris | 네트워크 서비스로 써도 공개 의무. **코드 포크 금지, 설계 참고만**. 단 aeneas는 "오프라인 도구로 돌려 JSON만 쓰는" 경우 산출물에는 전염 없음 |
| **비상업 조건** | hi-kid(README 명시), magic-english-buddy(LICENSE 확인 필요) | 구조 참고만 |

---

## 4. 워릭 교재 × 오픈소스 매핑 (적용안)

### 4-1. 교재별 기능 설계

| 교재 | 교재의 활동 | 앱 기능 | 참고 사례 | 부품 |
|---|---|---|---|---|
| **Phonics Winner 1-1·1-2** (알파벳, 글자당 6p: Listen&repeat→변별→트레이싱→매칭→쓰기→미로) | 주 1글자 | 음가 카드(이미 MVP) + **트레이싱**(획순) + 변별 미니게임 + 미로 | buzzphonics, Antura 미니게임, magic-english-buddy 문제 4종 | Phaser(미니게임), tracing 경로 데이터, Kokoro/교재 음원 |
| **Phonics Winner 2·3** (CVC·Magic e, 블렌딩 a+d=ad) | 워드패밀리당 4p | 소리 합치기(MVP에 있음) **자동 생성** + minimal pair 듣기 | — | g2p(음소 분해 자동화), ts-fsrs(CVC 63개 복습) |
| **ESW 리더스 4종 + 월 24 사이트워드** | Book Walk(에코·합창·포인터 리딩), Point/Circle/Underline | 읽어주기 + **단어별 하이라이트**(karaoke), 탭 미션, 사이트워드 FSRS 복습 | magic-english-buddy(연속 낭독+하이라이트+3단 속도) | aeneas(교재 음원 정렬) 또는 whisperX, ts-fsrs |
| **ThinkBuilder / My View WB** (초1~2) | 어휘 10개→독해→T/F→문법→Build-a-Sentence | 독해 퀴즈 + 문장 조립 + 타이핑 스펠링 | qwerty-learner(타이핑), LuciaDictionary(문장→단어카드) | duolingo-clone 챌린지 스키마 |
| **Speaking World** (주간 Show&Tell, Mini Interview, 8행 발표 스크립트) | 발표·인터뷰 | **섀도잉**(문장 듣고 따라 말하기→단어 매칭 하이라이트) + **발표 녹음 제출** + (초등) 발음 점수 + "Dotty와 대화" | Echo-Loop(섀도잉 설계), Immergo(Gemini Live 페르소나), hi-kid(아이 발화 관용) | sherpa-onnx(온디바이스 ASR), OpenPronounce(채점 API), Gemini Live/Claude 음성 |
| **Debate Lab A·B** (초1~4) | 찬반 지문→에세이→발표 | AI 토론 상대(Woody) + 에세이 구조 체커 | BabelDuck(제안 사이드창) | LLM API |
| **Science Lab** | 주 1실험, My Science Report | 실험 영상 QR + 리포트 사진 제출 + 부모 질문 가이드 | prehistoric-museum(부모 가이드 질문) | — |

### 4-2. 커리큘럼을 "데이터"로 — LibreLingo 모델 채택
교재 65권(계획)·39권(완성)을 **코드가 아니라 콘텐츠 스키마**로 적재한다. LibreLingo의 YAML 코스 모델과 duolingo-clone의 `courses → units → lessons → challenges → challengeOptions` 스키마를 합친 형태:

```
course(Phonics Winner 2)
 └ unit(Unit 1: -ad -am -an)         ← 교재 유닛
    └ lesson(Lesson 1: -ad, SB p.4) ← 교재 페이지 참조
       ├ asset(audio: track 031, illustration: p4_dad.png)
       ├ challenge(listen_pick_word, "dad|sad|mad")
       ├ challenge(blend, "d+ad")
       └ challenge(read_pick_picture)
```
이렇게 하면 (1) 가맹원이 요구한 **"전국 통일 레벨 가이드"**가 앱 데이터 자체가 되고, (2) 교재 개정 시 앱 코드 수정 없이 콘텐츠만 교체되며, (3) 교사 설정 "오늘의 글자"가 lesson ID 하나로 끝난다.

### 4-3. 가맹원 요청 → 앱 모듈
| 요청 | 모듈 | 참고 |
|---|---|---|
| 플랫폼 일원화 | 원 코드 로그인 1개로 파닉스·리더스·스피킹·과제·리포트 통합(PWA) | kolibri(원→반→학생 계층), duolingo-clone(Clerk 대신 Supabase Auth) |
| 전국 통합 평가·석차 | 월말 자동 퀴즈 + 낭독 WCPM + 발표 녹음 → 원별/전국 백분위 | whisperX(WCPM), OpenPronounce |
| 리워드(뱃지·상장) | 스티커→뱃지→수료증 PDF 자동 발급, 워릭 프렌즈 카드 수집 | magic-english-buddy(수료증·카드·Buddy 진화), duolingo-clone(XP·퀘스트) |
| 전국 스피킹 콘테스트 | 앱 내 녹화 제출→본사 심사→온라인 결선 | — |
| 교사 자료 부재 | 교사 대시보드에 정답·루브릭·주간 완료현황(파일럿의 "완료현황 시트" 자동화) | kolibri coach |
| 학부모 연계 부재 | 주간 리포트 알림톡 + 부모용 "오늘 이렇게 물어보세요" 질문 1개 | prehistoric-museum 부모 가이드 |

---

## 5. 추천 기술 구성 (기존 MVP 제안 위에)

| 층 | 선택 | 이유 |
|---|---|---|
| 앱 | **Next.js PWA** (태블릿·폰 홈화면 설치), 필요 시 Capacitor로 스토어 포장 | MVP 제안과 동일, duolingo-clone(MIT)과 같은 스택, 원 아이패드·가정 갤럭시 모두 커버 |
| 미니게임 | Phaser 4 씬을 페이지 안에 임베드 | MIT, 웹 최대 게임 프레임워크 |
| 콘텐츠 | 교재 → JSON 커리큘럼 스키마(§4-2), 일러스트는 출판 데이터 추출 | 코드/콘텐츠 분리 |
| 음원 | 1순위 **교재 음원 113+28트랙**(aeneas로 정렬) / 2순위 Kokoro 빌드타임 생성 / 3순위 ElevenLabs | 런타임 TTS 호출 0 → 비용·지연 0 |
| 음성 인식 | 유치부: 녹음 제출만. 초등: sherpa-onnx(WebAssembly) 온디바이스 → 필요 시 서버 whisperX | 아동 음성 전송 최소화(개인정보) |
| 발음 평가 | OpenPronounce 셀프호스트(FastAPI/Docker) | MIT, Azure 대체 |
| 복습 | ts-fsrs, 아이 입력은 2단계(맞음/틀림) | MIT |
| 백엔드 | Supabase(Auth·Postgres·Storage·RLS로 원/반/학생 분리) | MVP 제안과 동일 |
| AI 회화 | Gemini Live 또는 Claude(음성 파이프라인은 Immergo 구조) — **초등 Master/Debate부터** | 유치부는 LLM 자유 대화 비권장(통제 어려움) |
| 알림 | 카카오 알림톡(파일럿 플로우 문서 있음) | — |

---

## 6. 단계별 로드맵 (오픈소스 투입 시점)

| 단계 | 기간 | 범위 | 투입 오픈소스 |
|---|---|---|---|
| **P1 파일럿** (이미 계획) | 4주 | 직영 1원 5세반, 파닉스 L1 + ESW 리더스, 반 코드 입장 | 교재 음원 연결(aeneas 정렬), Kokoro 폴백 |
| **P2 실서비스 v1** | 3개월 | 15개원, 계정·반 편성, 교사 대시보드, 알림톡 리포트, 파닉스 L1~3 + ESW 전 볼륨, 스티커→뱃지 | duolingo-clone 스키마·관리자, ts-fsrs, Phaser 미니게임 3종, Supabase RLS |
| **P3 스피킹** | +3개월 | Speaking Rookie·Challenger 섀도잉, 발표 녹음 제출, 교사 루브릭 채점 | sherpa-onnx, Echo-Loop 설계, OpenPronounce(초등만 점수 노출) |
| **P4 초등 확장** | +6개월 | My View·ThinkBuilder 독해/타이핑, Debate AI 상대, 전국 통합 평가·콘테스트 | whisperX(WCPM), Gemini Live/Claude, qwerty-learner식 타이핑 |

---

## 7. 리스크 & 체크리스트

1. **아동 개인정보**: 만 14세 미만은 법정대리인 동의 필수(개인정보보호법 제22조의2). 음성·사진은 민감 → 온디바이스 처리 우선, 서버 저장 시 보관기간 명시. 앱 설계 초기에 동의 플로우 포함.
2. **라이선스 전염**: AGPL 레포(Echo-Loop, LibreLingo, aeneas 코드) 포크 금지. §3 표를 PR 체크리스트에 넣을 것.
3. **캐릭터 계약**: pikant 계약에 **디지털 서비스·앱 UI·애니메이션 사용권**이 포함됐는지 확인(기존 분석 §8-4 미결). 앱 아이콘·스티커·수료증 전부 캐릭터 의존.
4. **Savvas 상표**: My View Workbook 디지털화 시 myView 로고·지문 사용 불가 → 자체 지문만.
5. **아동 ASR 정확도**: 5~7세 자동 채점은 신뢰 불가 → 점수 대신 "녹음 완료" 보상, 교사 확인. 초등부터 점수.
6. **교재 QA 미완**: ThinkBuilder·Debate A 등 정오표 반영 전 콘텐츠 적재 금지(앱이 오타를 전국에 복제함).
7. **스크린타임**: 세션 8~12분 목표(MVP KPI) 유지. 자동 종료·하루 상한을 기본값으로.

---

## 8. 바로 할 수 있는 다음 행동 5개

1. `sanidhyy/duolingo-clone` 클론 → `db/schema.ts`를 워릭 커리큘럼 스키마(§4-2)로 교체하는 스파이크 (1~2일)
2. 교재 음원 113트랙 원본 확보 → `aeneas`로 ESW 리더스 4권 문장 정렬 JSON 생성 → MVP 스토리북 리더에 하이라이트 적용 (음원 확보 후 1일)
3. `OpenPronounce` Docker 띄워 Speaking Rookie 8행 스크립트 10개로 채점 품질 테스트 (교사 2명 블라인드 비교, 반나절)
4. `ts-fsrs` 붙여 사이트워드 24개 복습 큐 → 파일럿 5세반 데이터로 검증
5. pikant 계약서 디지털 사용권 조항 확인 + 아동 개인정보 동의 플로우 초안
