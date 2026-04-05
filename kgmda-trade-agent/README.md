# kgmda-trade-agent 설치 및 사전 점검 안내서

> 이 문서를 먼저 읽고, 체크리스트를 전부 통과한 후 스킬을 사용하세요.
> SKILL.md는 사용법, 이 문서는 설치/환경 점검용입니다.

---

## 1. 사전 요건 체크리스트

아래 항목을 **모두** 통과해야 스킬 사용이 가능합니다.
`preflight.py`를 실행하면 자동으로 전부 검증됩니다.

```bash
python3 preflight.py
```

### 1.1 시스템

| # | 항목 | 확인 방법 | 필수 |
|---|------|----------|------|
| 1 | Python 3.9+ | `python3 --version` | YES |
| 2 | curl 설치됨 | `curl --version` | YES |
| 3 | 인터넷 연결 | `curl -s http://www.kgmda.com/ > /dev/null && echo OK` | YES |
| 4 | 한국 IP 권장 | `curl -s ifconfig.me` → 한국 IP 확인 | WARN (비KR시 프록시 필수) |

### 1.2 Python 패키지

| # | 항목 | 설치 | 필수 |
|---|------|------|------|
| 5 | playwright | `pip install playwright` | YES |
| 6 | chromium 브라우저 | `playwright install chromium` | YES |
| 7 | playwright deps (Linux) | `playwright install-deps chromium` | Linux만 |

### 1.3 크레덴셜

| # | 항목 | 설정 방법 | 필수 |
|---|------|----------|------|
| 8 | KGMDA ID/PW | 환경변수 또는 실행 시 대화형 입력 | YES |
| 9 | kgmda.com 로그인 가능 | 브라우저에서 수동 로그인 확인 | YES |

### 1.4 프록시 (한국 외 IP인 경우 필수)

| # | 항목 | 설정 방법 | 필수 |
|---|------|----------|------|
| - | SOCKS5 프록시 | `export KGMDA_PROXY=127.0.0.1:1080` 또는 `--proxy` | 비KR IP만 |

> kgmda.com은 한국 IP만 허용합니다 (비KR → 403 Forbidden).
> 한국 서버에 SSH SOCKS 터널을 열고 프록시로 지정하세요:
> ```bash
> # 한국 서버에서 SOCKS5 프록시 오픈 (예시)
> ssh -D 1080 -f -C -q -N user@korean-server-ip
> export KGMDA_PROXY=127.0.0.1:1080
> ```

### 1.5 TG 보고 (선택)

| # | 항목 | 설정 방법 | 필수 |
|---|------|----------|------|
| 10 | TG Bot Token | `export TG_BOT_TOKEN=<봇 토큰>` | --tg-send 사용 시 |
| 11 | TG Chat ID | `export TG_CHAT_ID=<채팅 ID>` | --tg-send 사용 시 |
| 12 | TG Bot 전송 가능 | 봇으로 테스트 메시지 전송 | --tg-send 사용 시 |

---

## 2. 설치 순서

```bash
# Step 1: 파일 복사
cp kgmda_scraper.py <작업 디렉토리>/
cp preflight.py <작업 디렉토리>/

# Step 2: Python 패키지 설치
pip install playwright
playwright install chromium
# Linux인 경우 추가:
# playwright install-deps chromium

# Step 3: 환경변수 설정 (선택 — 미설정 시 실행 중 입력)
export KGMDA_ID=<본인 ID>
export KGMDA_PW=<본인 PW>

# Step 4: 프록시 설정 (한국 외 IP인 경우)
# ssh -D 1080 -f -C -q -N user@korean-server-ip
# export KGMDA_PROXY=127.0.0.1:1080

# Step 5: TG 보고 설정 (선택)
export TG_BOT_TOKEN=<봇 토큰>
export TG_CHAT_ID=<채팅 ID>

# Step 6: 사전 점검 실행
python3 preflight.py

# Step 7: 테스트 실행
python3 kgmda_scraper.py --keyword "한양" --tg-format
# 프록시 사용 시:
# python3 kgmda_scraper.py --keyword "한양" --proxy 127.0.0.1:1080 --tg-format
```

---

## 3. 안전 규칙 (HC-KGMDA)

**반드시 숙지:**
- READ-ONLY: 로그인 + 검색 + 조회만 허용
- 등록/수정/삭제 절대 금지 (협회 제재)
- 조회 후 자동 로그아웃 (스크립트 내장)
- 중복 로그인 불가 — 동시 실행 금지
- 조회 간격 최소 5초

---

## 4. 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| "curl not found" | curl 미설치 | `apt install curl` 또는 `choco install curl` |
| "playwright not installed" | 패키지 미설치 | `pip install playwright && playwright install chromium` |
| "Login failed — Session" | 다른 곳에서 이미 로그인 | 이전 세션 만료 대기 (최대 5분) |
| "Login failed — Concurrent" | 중복 로그인 | 다른 에이전트/브라우저 로그아웃 후 재시도 |
| 한글 깨짐 | 인코딩 | 스크립트가 EUC-KR 자동 처리 — 터미널 UTF-8 확인 |
| 검색 결과 없음 | 키워드 불일치 | 정확한 골프장명 사용 (부분 일치 가능) |
| 403 Forbidden | 비한국 IP | `--proxy 127.0.0.1:1080` 또는 `KGMDA_PROXY` 설정 (1.4절 참고) |

---

## 5. 파일 구성

```
kgmda-trade-agent/
├── README.md          ← 이 문서 (설치 안내 + 체크리스트)
├── SKILL.md           ← 사용법 가이드
├── kgmda_scraper.py   ← 메인 스크립트
├── kgmda-dom-analysis.md ← DOM 참조 (사이트 구조 변경 시 참고)
└── preflight.py       ← 사전 점검 스크립트
```
