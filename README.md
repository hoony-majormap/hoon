# hoon

## korean-edu-market-research

키워드 하나로 외국인 대상 한국어 교육 경쟁 상품을 해부해 `report.md` + `dashboard.html`을 만드는 Claude Code 스킬.
기획서: Notion "2026-10-17_한국어 교육 경쟁 리서치 에이전트 기획서".

- 진입점: [`.claude/skills/korean-edu-market-research/SKILL.md`](.claude/skills/korean-edu-market-research/SKILL.md)
- 실행: Claude Code에서 "외국인 TOPIK 대비 과정으로 한국어 교육 경쟁 리서치 돌려줘"
- 산출물: `output/{YYYY-MM-DD}-{키워드}/` (`findings.json`, `analysis.json`, `report.md`, `dashboard.html`)

```
Scout(발굴) → 사람 승인 → Dissector ×N(해부, 1개 먼저 검증 후 병렬) → Verifier(검증)
  → pipeline.py merge → findings.json(SSOT) → Analyst(분석) → pipeline.py render / check
```

수치 계산·등급 판정·병합·렌더링은 `scripts/pipeline.py`(표준 라이브러리만)가 결정론적으로 한다.

```bash
python3 -m unittest discover -s .claude/skills/korean-edu-market-research/scripts/tests
```
