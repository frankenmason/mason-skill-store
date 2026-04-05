---
name: agentck
description: 에이전트 상태 확인 템플릿. 자기 + 연결된 에이전트 상태를 점검.
type: template
version: 1.0.0
---

# agentck — 에이전트 상태 확인 스킬

> 이 스킬은 **템플릿**입니다. 각 에이전트가 자기 환경에 맞게 커스터마이징하세요.

## 트리거

`/agentck` 또는 `@에이전트 상태`

## 점검 체크리스트

### 1. 자기 상태 (Self-Check)

| 항목 | 확인 방법 | 판단 기준 |
|------|----------|----------|
| 에이전트 프로세스 | 플랫폼별 health 명령 | 실행 중 → OK |
| 설정 파일 존재 | 설정 파일 경로 확인 | 없음 → FAIL |
| API 키 유효 | 간단한 API 호출 테스트 | 실패 → FAIL |
| 디스크 여유 | `df -h` (작업 디렉토리) | <15% → WARN |
| 최근 활동 | 로그 최신 타임스탬프 | >24h → WARN |

### 플랫폼별 자기 점검

```bash
# OpenClaw
openclaw health

# Hermes
hermes doctor

# Codex
codex --version

# Claude Code
claude --version
```

### 2. 연결된 에이전트 확인 (선택)

자기가 접근 가능한 에이전트만 체크.

| 대상 | 확인 방법 | 비고 |
|------|----------|------|
| Hub L2 | `curl -s -H "X-Hub-Token: <토큰>" <HUB_URL>/health` | Hub 접근 에이전트 |
| Redis | `redis-cli -a <pw> ping` | Redis 접근 에이전트 |
| Tailscale 피어 | `tailscale status` | Tailscale 연결 에이전트 |
| TG 봇 | `curl -s https://api.telegram.org/bot<토큰>/getMe` | TG 사용 에이전트 |

### 3. 스킬 상태

| 항목 | 확인 방법 |
|------|----------|
| 설치된 스킬 목록 | 스킬 디렉토리 ls |
| skill-store 최신 여부 | `git -C <skill-store> log -1 --format="%H %s"` |
| preflight 전체 통과 | 각 스킬 `python3 preflight.py` |

## 출력 형식

```
=== AGENTCK: <에이전트ID> ===
[Self]
  [v] Process: running
  [v] Config: present
  [v] API: valid (model: gpt-4o)
  [v] Disk: 55% (OK)

[Connections]
  [v] Hub L2: healthy
  [v] TG Bot: @my_bot (active)
  [!] Redis: unreachable

[Skills]
  [v] kgmda-trade-agent: v1.1.0 (preflight PASS)
  [v] skill-store: up to date

RESULT: 1 WARN, 0 FAIL
========================
```

## 커스터마이징 가이드

1. 자기 에이전트 ID 설정
2. 접근 가능한 연결만 체크 항목에 포함
3. Hub/Redis/Tailscale 미사용 시 해당 섹션 제거
4. 결과를 TG로 보고하려면 TG 봇 설정 후 전송 로직 추가
