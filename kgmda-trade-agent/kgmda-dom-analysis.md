# KGMDA DOM Analysis — 실측 기반 참조 문서

> 조사일: 2026-04-05
> 조사자: CL (Playwright browse 실측)
> 사이트: http://www.kgmda.com/

---

## 1. 사이트 구조

### 1.1 최상위
- URL: `http://www.kgmda.com/`
- 구조: **frameset** (단일 frame)
- frame: `name="main_kgmda_nom"` → `src="/new2/index.php"`
- 직접 접근: `http://www.kgmda.com/new2/index.php`

### 1.2 메인 프레임 (`/new2/index.php`)
- 로그인 폼, 메뉴, 배너, 하단 링크 포함
- 로그인 후 상단에 "전관환 님! 환영합니다" 표시

---

## 2. 로그인

### 2.1 입력 필드
```
input[name="userid"]  — type: text (ID)
input[name="pwd"]     — type: password (PW)
input[name="kgmdaSaveId"] — type: checkbox (아이디 저장)
```

### 2.2 로그인 버튼
```
img[src*="login_btn"] — /new2/images/main/login_btn.gif
```
- 클릭 시 `/new2/` 로 리다이렉트 (로그인 처리)

### 2.3 로그인 확인
```javascript
document.body.innerHTML.includes('로그아웃') // true = 로그인 성공
```

### 2.4 크레덴셜
- 환경변수 KGMDA_ID / KGMDA_PW 설정 필요 (README.md 참조)

---

## 3. 거래 페이지 (Trade)

### 3.1 접근 방법
- 메뉴 "회원사메뉴" 클릭 → `window.open('/html_new2/Trade_001.php', '', 'width=1200,height=800,...')`
- **직접 goto 가능**: `http://www.kgmda.com/html_new2/Trade_001.php` (팝업 핸들링 불필요)

### 3.2 URL 분류
| 유형 | URL | 비고 |
|------|-----|------|
| 정회원 | `/html_new2/Trade_001.php` | 기본 |
| 준회원 | `/html2_new2/Trade_001.php` | html**2**_new2 주의 |

### 3.3 탭
- GOLF / CONDO / HEALTH (상단 탭)

---

## 4. 검색 (FIND)

### 4.1 검색 폼
```
form[name="FIND"] — method: GET, action: Trade_001.php
```

### 4.2 검색 필드
| Selector | Name | 용도 | 값 예시 |
|----------|------|------|---------|
| `select[name=limitday]` | limitday | 기간 필터 | 10, 5, 3, 2, 1, 전체 |
| `select[name=coname]` | coname | 회원사 필터 | 전체 회원사, 강남회원권거래소, ... |
| `select[name=sloc1]` | sloc1 | 지역 1단계 | 지역, 강원도, 경기도, ... |
| `select[name=sloc2]` | sloc2 | 지역 2단계 | 상세지역 (동적 로딩) |
| `input[name=goods]` | goods | **골프장명 키워드** | 블루원, 남서울, ... |
| `input[name=price]` | price | 가격 필터 | 숫자 |

### 4.3 회원 구분 체크박스
- VIP, 법인회원, 주중, 무기명, 회원구분, 개인 등

### 4.4 검색 실행
```javascript
document.querySelector('input[name=goods]').value = '블루원';
document.forms['FIND'].submit();
```

---

## 5. 테이블 구조

### 5.1 테이블 인덱스 맵
| Index | 역할 | 행수 |
|-------|------|------|
| 0 | 상단 탭/필터 | - |
| 1 | 매도 검색 필터 (골프장명, 금액, 비고, 등록일) | 3 |
| 2 | 매도 헤더/컨트롤 | - |
| **3** | **매도 주문 데이터** | **31 (30건+헤더)** |
| 4 | 매도 페이지네이션 | 96페이지 |
| 5 | 매수 검색 필터 (골프장명, 금액, 비고, 등록일) | 3 |
| 6 | 매수 헤더/컨트롤 | - |
| **7** | **매수 주문 데이터** | **31 (30건+헤더)** |
| 8 | 매수 페이지네이션 | 85페이지 |

### 5.2 데이터 테이블 컬럼 (idx=3, idx=7 공통)
| 컬럼 | Index | 예시 |
|------|-------|------|
| 번호 | 0 | 1 |
| 회원사 | 1 | 제일골프 |
| 골프장명 | 2 | 블루원-용인 |
| 금액 | 3 | 29,500 |
| 비고 | 4 | 가능 |
| 등록일 | 5 | 26.04.04 |
| 삭제요망 | 6 | (버튼 — 절대 클릭 금지) |

### 5.3 파싱 코드 (검증 완료)
```javascript
const parseTable = (tableIdx) => {
  const t = document.querySelectorAll('table')[tableIdx];
  const rows = [...t.querySelectorAll('tr')].slice(1); // 헤더 제외
  return rows.map(r => {
    const cells = [...r.querySelectorAll('td')];
    return cells.map(c => c.textContent.trim());
  }).filter(r => r.length >= 5);
};

const sell = parseTable(3); // 매도
const buy = parseTable(7);  // 매수
```

### 5.4 검색 결과 예시 ("블루원" 검색)
```json
{
  "sell": [
    ["1", "제일골프", "블루원-용인", "29,500", "가능", "26.04.04", ""],
    ["2", "서울레저회원권", "블루원-용인", "29,500", "가능p", "26.04.03", ""],
    ["3", "한국레저", "블루원-용인", "29,800", "가능", "26.04.03", ""]
  ],
  "buy": [
    ["1", "회원권뱅크", "블루원-용인", "28,200", "가능3", "26.04.02", ""],
    ["2", "제일골프", "블루원-용인", "27,500", "가능", "26.04.04", ""],
    ["3", "예당회원권", "블루원-용인", "27,500", "", "26.04.03", ""]
  ]
}
```

---

## 6. 폼 목록 (전체)

| Index | Name | Method | Action | 용도 |
|-------|------|--------|--------|------|
| 0 | FIND | GET | Trade_001.php | **검색 (허용)** |
| 1 | SELL | POST | Trade_reg.php | 매도 등록 (**금지**) |
| 2 | SELLLIST | POST | Trade_reg.php | 매도 일괄 (**금지**) |
| 3 | BUY | POST | Trade_reg.php | 매수 등록 (**금지**) |
| 4 | BUYLIST | POST | Trade_reg.php | 매수 일괄 (**금지**) |

---

## 7. 안전 규칙 (HC-KGMDA)

### 7.1 허용 행위 (화이트리스트)
- `goto /new2/index.php` — 로그인 페이지
- `fill input[name=userid]` — ID 입력
- `fill input[name=pwd]` — PW 입력
- `click img[src*=login_btn]` — 로그인
- `goto /html_new2/Trade_001.php` — 정회원 거래 조회
- `goto /html2_new2/Trade_001.php` — 준회원 거래 조회
- `fill input[name=goods]` — 검색 키워드
- `submit form[name=FIND]` — 검색 실행
- `screenshot` — 스크린샷 촬영

### 7.2 금지 행위 (블랙리스트)
- `submit form[name=SELL]` — 매도 등록
- `submit form[name=BUY]` — 매수 등록
- `submit form[name=SELLLIST]` — 매도 일괄
- `submit form[name=BUYLIST]` — 매수 일괄
- `click *[onclick*=OpenAdd]` — 일괄등록 버튼
- `click *[onclick*=OpenAllUpdate]` — 일괄수정 버튼
- `click *[onclick*=police]` — 삭제요망 버튼
- `click *[onclick*=Delete]` — 삭제 관련
- `goto Trade_reg.php` — 등록 페이지 접근

---

## 8. 기술 참고

- 사이트: PHP 기반 (레거시)
- 인코딩: **EUC-KR** [실측 2026-04-05]
- 금액 단위: **만원** (29,500 = 2억9,500만원) — 헤더에 단위 미표기, 업계 관행으로 확인
- Rate Limit: min_interval=5s, max_requests_per_session=50, login_max_retry=2
- 중복 로그인: 서버 측 세션 추적. 동시 로그인 불가. 조회 후 반드시 login_out.php 호출 (최대 5분 유지)
- 로그인 방식: Playwright 직접 로그인 불가 (frameset 쿠키 격리). **curl subprocess → 쿠키 Playwright 주입** 방식 사용

---

## 9. 디버깅 이력 (2026-04-05)

### Issue 1: Playwright 로그인 실패
- 증상: Playwright headless에서 로그인 후 쿠키 0개, Trade 테이블 0개
- 원인: frameset 구조에서 frame 내 form submit이 쿠키를 부모 context에 전달하지 않음
- 시도: frame 직접 접근, frm_submit() JS 호출, page.evaluate → 모두 실패
- 해결: curl subprocess로 로그인 → Netscape cookie file 파싱 → Playwright context.add_cookies()

### Issue 2: 중복 세션 차단
- 증상: 2회차 로그인 시 "이전에 사용하신 PC의 Session이 만료되지 않았거나 다른곳에서 이미 접속중입니다"
- 원인: PHP/4.4.9 서버 측 세션 추적. 이전 세션이 logout 없이 종료되면 서버에 잔류
- 해결: 스크립트 finally 블록에 curl_logout() 추가. 매 실행 후 login_out.php 호출

### Issue 3: EUC-KR 인코딩
- 증상: subprocess 결과 decode 시 UnicodeDecodeError
- 원인: login_reg.php 응답이 EUC-KR
- 해결: `result.stdout.decode('euc-kr', errors='replace')`

### Issue 4: 로그인 검증 방법
- 실패: document.body.innerHTML.includes('로그아웃') → frameset 내부라 항상 False
- 성공: curl 응답에 'location.replace' 포함 여부 + context.cookies()에서 USERID 확인
- 세션: PHP PHPSESSID 쿠키
- 페이지당: 30건 고정
- 페이지네이션: URL 파라미터로 제어 (확인 필요)
