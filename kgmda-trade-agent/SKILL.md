# kgmda-trade-agent — 에이전트 배포용

> 원본: CL kgmda-trade 스킬에서 클론 (v8 2026-04-06)
> 용도: R2/FRANKEN/Codex 등 에이전트가 독립 실행
> 모델: 무관 (Claude/GPT/Gemini 어느 것이든)

## HC-KGMDA (필독)
**READ-ONLY. 로그인+검색+조회만. 등록/수정/삭제 절대 금지. 위반 시 협회 제재.**

## 핵심 원칙

1. 골프회원권 시세 요청 → KGMDA 흐름으로 자동 해석
2. **읽기 전용만 허용** — 조회, 보고, 로그아웃만 수행
3. 조회 완료 → 로그아웃 확인
4. 완료 후 추가 조회 필요 여부 질문
5. 프록시/크레덴셜/TG 결과를 로그에 노출 금지
6. direct access 실패 → 비KR IP 환경에서는 정상. proxy 경유 성공 여부 우선 판단

## 입력 해석 규칙

표준 파싱 순서 (7필드):

| 순서 | 필드 | 설명 | 예시 |
|:----:|------|------|------|
| 1 | course | 골프장명 또는 브랜드명 | 뉴코리아, 팔팔, 금강 |
| 2 | extra1 | course 직후 보조 구분값 | 주중, 일반, 주말 |
| 3 | price | 금액 조건 | 분양가, 분, 2500, 2천5백 |
| 4 | ownership | 소유 형태 | 개인, 법인 |
| 5 | gender | 성별 | 남자, 여자 |
| 6 | expiry | 만기 | 만기 26-8, 2026-08, 26년8월 |
| 7 | extra2 | 기타 조건 | 무기명, 양도, 등기, 법인형 |

해석 예시:
- "뉴코리아 주중 2500 법인" → course=뉴코리아, extra1=주중, price=2500, ownership=법인
- "골드 남자 만기 26-8" → course=골드, gender=남자, expiry=2026-08

IF 충돌/애매 THEN 실행 전 1회 확인 질문.

## 실행 절차

1. 요청을 위 파싱 규칙으로 정규화
2. 필요한 경우에만 1회 확인 질문
3. 조회 수행
4. 결과 간단히 요약
5. 로그아웃 확인
6. 추가 조회 여부 질문

## 보고 형식

```
- 프록시 상태: [direct/proxy 경유]
- 조회 키워드: [파싱된 course + 조건]
- 파싱 결과: [7필드 매핑]
- 조회 성공 여부: [OK/FAIL + 사유]
- 로그아웃 여부: [완료/미완료]
- 추가 조회: [필요/불필요]
```

IF 조회 실패 THEN 원인 점검 순서: 프록시 → 크레덴셜 → 키워드.

## 설치

```bash
# 1. Python 3.9+ 확인
python3 --version

# 2. Playwright 설치
pip install playwright && playwright install chromium

# 3. curl 확인
curl --version

# 4. 스크립트 복사
cp kgmda_scraper.py <에이전트 작업 디렉토리>/
```

## 크레덴셜 (각 사용자 고유)

KGMDA ID/PW는 **사용자마다 다름**. 3가지 방식으로 전달 가능:

1. **환경변수** (자동화/cron용)
```bash
export KGMDA_ID=<본인 ID>
export KGMDA_PW=<본인 PW>
```

2. **대화형 입력** (환경변수 미설정 시 자동 프롬프트)
```
$ python3 kgmda_scraper.py --keyword "한양"
KGMDA ID: (입력)
KGMDA PW: (입력, 화면에 미표시)
```

3. **에이전트 호출 시**: 에이전트가 사용자에게 ID/PW를 요청하여 환경변수로 주입

## TG 보고 설정 (선택)

```bash
# 각 에이전트/사용자의 자체 봇/채널
export TG_BOT_TOKEN=<자체 TG 봇 토큰>
export TG_CHAT_ID=<보고 대상 채팅 ID>

# 선택
export KGMDA_SCREENSHOT_DIR=<스크린샷 저장 경로>
```

## 사용법

```bash
# 기본 조회 (JSON 출력)
python3 kgmda_scraper.py --keyword "한양"

# TG 포맷 출력 (화면 확인용)
python3 kgmda_scraper.py --keyword "한양" --tg-format

# TG 직접 전송 (에이전트 미경유, 토큰 0)
python3 kgmda_scraper.py --keyword "한양" --tg-send

# 스크린샷 포함 TG 전송
python3 kgmda_scraper.py --keyword "한양" --tg-send --screenshot

# 준회원 조회
python3 kgmda_scraper.py --keyword "한양" --type junior --tg-send

# JSON 파일 저장
python3 kgmda_scraper.py --keyword "한양" --output result.json
```

## 출력 구조

```json
{
  "keyword": "한양",
  "timestamp": "2026-04-05T16:33:00+09:00",
  "trade_type": "regular",
  "sell": [{"rank":"1", "company":"멤버쉽코리아", "course":"한양", "price":"41,800", "note":"전화", "date":"26.04.04"}],
  "buy": [{"rank":"1", "company":"올림피아레저", "course":"한양", "price":"56,200", "note":"여자/사전중", "date":"26.04.04"}],
  "summary": {"sell_min":"41,800", "sell_max":"58,000", "buy_min":"40,000", "buy_max":"56,200", "unit":"만원"}
}
```

## 안전 규칙

- 조회 후 반드시 자동 로그아웃 (스크립트 내장)
- 중복 로그인 불가 — 동시 실행 금지
- 조회 간격 최소 5초
- 가격 단위: 만원 (29,500 = 2억9,500만원)

## 플랫폼별 참고

| 환경 | 참고 |
|------|------|
| Linux VPS | 그대로 실행 |
| Windows | curl 내장 확인. tempfile 경로 자동 처리됨 |
| Docker | chromium deps 필요: `playwright install-deps chromium` |
| 한국 외 IP | 접속 차단 가능성 — 한국 IP 권장 |

## DOM 참조

사이트 DOM 구조 변경 시: `docs/references/kgmda-dom-analysis.md` 참조하여 selector 업데이트.
