---
name: syscheck
description: 시스템 전체 점검 템플릿. 에이전트가 자기 환경에 맞게 커스터마이징하여 사용.
type: template
version: 1.0.0
---

# syscheck — 시스템 점검 스킬

> 이 스킬은 **템플릿**입니다. 각 에이전트가 자기 환경에 맞게 항목을 선택/수정하여 사용하세요.

## 트리거

`/syscheck` 또는 `@시스템 체크`

## 점검 체크리스트

IF syscheck 트리거 THEN 아래 항목을 순서대로 실행.
각 항목은 자기 환경에 해당하는 것만 선택.

### 1. OS / 하드웨어

| 항목 | 명령어 (Linux) | 명령어 (Windows) | 판단 기준 |
|------|--------------|----------------|----------|
| 디스크 사용량 | `df -h /` | `wmic logicaldisk get size,freespace` | >85% → WARN |
| 메모리 | `free -h` | `systeminfo \| findstr Memory` | >90% → WARN |
| CPU 부하 | `uptime` | `wmic cpu get loadpercentage` | >80% → WARN |
| OS 업타임 | `uptime -p` | `systeminfo \| findstr Boot` | 정보 |

### 2. 네트워크

| 항목 | 명령어 | 판단 기준 |
|------|--------|----------|
| 인터넷 연결 | `curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://google.com` | !=200 → FAIL |
| DNS 해석 | `nslookup google.com` | 실패 → FAIL |
| Tailscale (해당 시) | `tailscale status` | disconnected → WARN |
| 외부 IP | `curl -s ifconfig.me` | 정보 |

### 3. 서비스 (에이전트별 선택)

| 항목 | 명령어 | 대상 |
|------|--------|------|
| pm2 프로세스 | `pm2 list` | pm2 사용 에이전트 |
| Docker 컨테이너 | `docker ps` | Docker 사용 에이전트 |
| systemd 서비스 | `systemctl status <서비스>` | Linux 에이전트 |
| Redis | `redis-cli ping` | Redis 사용 에이전트 |

### 4. 에이전트 플랫폼

| 항목 | 명령어 | 대상 |
|------|--------|------|
| Claude Code | `claude --version` | CC 에이전트 |
| OpenClaw | `openclaw --version && openclaw health` | OpenClaw 에이전트 |
| Hermes | `hermes --version && hermes doctor` | Hermes 에이전트 |
| Codex | `codex --version` | Codex 에이전트 |
| Node.js | `node --version` | 전체 |
| Python | `python3 --version` | 전체 |

### 5. 보안 (선택)

| 항목 | 명령어 | 판단 기준 |
|------|--------|----------|
| 환경변수 노출 | `env \| grep -i "token\|key\|secret\|password"` | 불필요 노출 → WARN |
| SSH 접속 로그 | `last -n 5` | 비정상 접속 → ALERT |

## 출력 형식

```
=== SYSCHECK: <에이전트ID> ===
[1] OS/HW
  [v] Disk: 45% used (OK)
  [v] Memory: 2.1G/4G (OK)
  [v] CPU: 12% (OK)

[2] Network
  [v] Internet: OK (200)
  [v] Tailscale: connected (4 nodes)

[3] Services
  [v] pm2: 5/5 online
  [!] Redis: connection refused

[4] Platform
  [v] Claude Code: v2.1.91

RESULT: 1 WARN, 0 FAIL
========================
```

## 커스터마이징 가이드

1. 자기 환경에 해당하지 않는 항목 제거
2. 자기 서비스/포트/경로 추가
3. 판단 기준 임계값 조정
4. 출력을 TG 보고와 연동 (선택)
