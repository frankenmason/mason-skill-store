# kgmda-trade-agent — 에이전트 배포용

> 원본: CL kgmda-trade 스킬에서 클론
> 용도: R2/FRANKEN/Codex 등 에이전트가 독립 실행
> 모델: 무관 (Claude/GPT/Gemini 어느 것이든)

## HC-KGMDA (필독)
**READ-ONLY. 로그인+검색+조회만. 등록/수정/삭제 절대 금지. 위반 시 협회 제재.**

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
