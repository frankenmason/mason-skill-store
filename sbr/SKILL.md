---
name: sbr
description: 세션 백업/복구 템플릿. 에이전트 세션 상태를 저장하고 다음 세션에서 복원.
type: template
version: 1.0.0
---

# sbr — 세션 백업/복구 스킬

> 이 스킬은 **템플릿**입니다. 각 에이전트가 자기 환경에 맞게 구현하세요.

## 트리거

`/sbr` 또는 `@SBR` 또는 `@세션백업복구`

## 개념

```
세션 시작 → [복구] 이전 상태 로딩 → 작업 수행 → [백업] 현재 상태 저장 → 세션 종료
```

## 백업 대상 (에이전트별 선택)

| 항목 | 설명 | 저장 형식 | 필수도 |
|------|------|----------|--------|
| 세션 메타 | 세션 ID, 시작 시각, 모델 | JSON | 필수 |
| 마지막 작업 | 무엇을, 언제, 다음 행동 | JSON | 필수 |
| 작업 큐 | 미완료/진행중/완료 태스크 목록 | JSON | 권장 |
| 미결 사항 | Mason 결정 대기 항목 | JSON | 권장 |
| 환경 스냅샷 | 디스크, 프로세스, 서비스 상태 | JSON | 선택 |

## 상태 파일 구조 (템플릿)

```json
{
  "$schema": "session-state/v2",
  "agent_id": "<에이전트 ID>",
  "updated_at": "<ISO 8601>",
  "session_meta": {
    "session_id": "<숫자>",
    "started_at": "<시각>",
    "model": "<사용 모델>",
    "ended_at": null
  },
  "last_work": {
    "what": "<마지막 작업 요약>",
    "when": "<시각>",
    "next_action": "<다음에 할 일>",
    "verify_cmd": "<검증 명령어>"
  },
  "task_queue": [
    {
      "id": "<task-ID>",
      "title": "<제목>",
      "status": "pending|in_progress|completed|blocked",
      "priority": "critical|high|medium|low"
    }
  ],
  "pending_decisions": [
    {
      "what": "<결정 필요 사항>",
      "options": "<선택지>",
      "asked_at": "<시각>"
    }
  ]
}
```

## 백업 절차

```
IF 세션 종료 OR /sbr backup THEN:
  1. 현재 상태를 JSON으로 직렬화
  2. 저장 경로에 기록:
     - 로컬: <workspace>/state/<agent_id>_state.json
     - 또는 Git: commit + push
     - 또는 Hub L2: POST /ingest
  3. 검증: 파일 존재 + JSON 파싱 가능 확인
```

## 복구 절차

```
IF 세션 시작 OR /sbr restore THEN:
  1. 상태 파일 읽기 (로컬 → Git → Hub L2 순)
  2. IF 파일 없음 THEN "새 세션 시작" 출력 + 빈 상태 초기화
  3. IF 파일 있음 THEN:
     - last_work 요약 출력
     - 미완료 task_queue 표시
     - pending_decisions 표시
     - verify_cmd 실행하여 상태 실측
  4. "이전 세션 복구 완료" 출력
```

## 저장 위치 옵션

| 방식 | 장점 | 단점 | 대상 |
|------|------|------|------|
| 로컬 파일 | 빠름, 단순 | 머신 종속 | 단일 머신 에이전트 |
| Git repo | 버전 관리, 백업 | push 필요 | Git 사용 에이전트 |
| Hub L2 | 중앙 집중, 공유 | 네트워크 필요 | Hub 접근 에이전트 |

## 커스터마이징 가이드

1. `agent_id` 자기 ID로 설정
2. 저장 위치 선택 (로컬/Git/Hub)
3. `task_queue` 구조를 자기 작업 형태에 맞게 조정
4. `verify_cmd`에 자기 환경 검증 명령 등록
5. 세션 시작 hook에 자동 복구 연결 (선택)
6. 세션 종료 hook에 자동 백업 연결 (선택)
