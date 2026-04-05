# Mason Skill Store

Mason AI 에이전트 및 외부 고객을 위한 스킬 배포 저장소.

## 사용법

```bash
# 전체 스토어 클론
git clone https://github.com/frankenmason/mason-skill-store.git

# 특정 스킬만 (sparse checkout)
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/frankenmason/mason-skill-store.git
cd mason-skill-store
git sparse-checkout set kgmda-trade-agent
```

## 스킬 목록

| ID | 이름 | 버전 | 설명 |
|----|------|------|------|
| kgmda-trade-agent | KGMDA Golf Price Checker | 1.1.0 | 골프회원권 매도/매수 시세 조회 |

상세: [catalog.json](catalog.json)

## 스킬 사용 절차

1. 스킬 디렉토리의 `README.md` 읽기 (설치 체크리스트)
2. `preflight.py` 실행 (환경 자동 검증)
3. 전부 PASS 후 스킬 사용

## 구조

```
mason-skill-store/
├── catalog.json              # 스킬 목록 + 메타데이터
├── README.md                 # 이 문서
└── <skill-name>/
    ├── README.md             # 설치 안내 + 체크리스트
    ├── SKILL.md              # 사용법 가이드
    ├── preflight.py          # 환경 자동 검증
    └── <entrypoint>.py       # 메인 스크립트
```

## 규칙

- 모든 스킬은 독립 실행 가능 (외부 종속성 최소)
- 크레덴셜: 환경변수 또는 대화형 입력 (하드코딩 금지)
- 각 에이전트는 자기 환경/토큰으로 self-migration
- preflight.py PASS 없이 스킬 사용 금지

## 라이선스

Private — Mason AI System 내부 및 승인된 고객만 사용 가능.
