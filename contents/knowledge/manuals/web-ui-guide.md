# CCC 웹 UI 가이드

> 교육 인프라에서 사용하는 웹 인터페이스 종합 안내

---

## 1. Wazuh Dashboard (SIEM 관제)

- **URL**: `https://10.20.30.100:443` (자체 서명 인증서 — 브라우저 경고 무시)
- **계정**: admin / (온보딩 시 자동 생성된 비밀번호)
- **비밀번호 확인**: SIEM VM에서 `tar -axf /tmp/wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt -O | grep -A1 "indexer_username: 'admin'"`

### 주요 메뉴

| 메뉴 | 경로 | 용도 |
|------|------|------|
| **Overview** | Wazuh > Overview | 전체 보안 현황 대시보드 |
| **Security Events** | Wazuh > Events | 실시간 보안 이벤트/알림 조회 |
| **Agents** | Wazuh > Agents | 등록된 에이전트 상태 관리 |
| **Management > Rules** | Wazuh > Management > Rules | 탐지 룰 조회/편집 |
| **Management > Decoders** | Wazuh > Management > Decoders | 로그 디코더 관리 |
| **Vulnerability Detection** | Wazuh > Vulnerability Detection | CVE 기반 취약점 탐지 |
| **MITRE ATT&CK** | Wazuh > MITRE ATT&CK | ATT&CK 프레임워크 매핑 |
| **Integrity Monitoring** | Wazuh > Integrity Monitoring | 파일 무결성 모니터링 |

### 실습에서 자주 사용하는 작업

#### 알림 조회
1. Wazuh Dashboard 접속
2. 좌측 메뉴 > **Wazuh** > **Events**
3. 시간 범위 설정 (Last 15 minutes / Last 1 hour)
4. 필터: `rule.level >= 7` (높은 위험도만)
5. 알림 클릭 → 상세 정보 (소스 IP, 룰 ID, 설명)

#### 에이전트 관리
1. **Wazuh** > **Agents**
2. 에이전트 목록에서 상태 확인 (Active/Disconnected)
3. 에이전트 클릭 → 상세 정보 (OS, IP, 마지막 연결)
4. **Inventory data** 탭 → 설치된 패키지, 열린 포트

#### 커스텀 룰 추가
1. **Management** > **Rules** > **Manage rule files**
2. `local_rules.xml` 선택 → 편집
3. 룰 추가 후 저장
4. Manager 재시작: `systemctl restart wazuh-manager`

#### MITRE ATT&CK 매핑
1. **Wazuh** > **MITRE ATT&CK**
2. 매트릭스 형태로 탐지된 테크닉 시각화
3. 색상 농도 = 탐지 빈도
4. 테크닉 클릭 → 관련 알림 목록

---

## 2. OpenCTI (위협 인텔리전스)

- **URL**: `http://10.20.30.100:8080`
- **계정**: admin@opencti.io / CCC2026!
- **API Token**: ccc-opencti-token-2026

### 주요 메뉴

| 메뉴 | 용도 |
|------|------|
| **Dashboard** | 전체 위협 인텔리전스 현황 |
| **Analyses** | 보고서, 노트, 의견 |
| **Events** | 인시던트, Sighting |
| **Observations** | IoC (IP, 도메인, 해시, URL) |
| **Threats** | 위협 행위자, 캠페인, 악성코드 |
| **Arsenal** | 공격 도구, 취약점 (CVE) |
| **Techniques** | MITRE ATT&CK 테크닉 |
| **Data** | 데이터 커넥터, 가져오기/내보내기 |

### 실습에서 자주 사용하는 작업

#### IoC 등록
1. **Observations** > **Indicators**
2. **+ Create an indicator** 클릭
3. 유형 선택 (IPv4, Domain, File Hash)
4. 값 입력 (예: 10.20.30.201)
5. 설명, 신뢰도, 유효 기간 설정
6. 저장

#### 위협 행위자 분석
1. **Threats** > **Threat actors**
2. 행위자 선택 또는 생성
3. **Knowledge** 탭 → 관련 TTP, IoC, 캠페인 연결
4. **관계 그래프** → 시각적 분석

#### Wazuh 연동 (IoC 매칭)
1. Wazuh에서 탐지된 IP를 OpenCTI에서 검색
2. **Observations** > 검색 → IP 입력
3. 매칭되면 관련 위협 정보 확인
4. 위협 수준에 따라 차단 결정

#### STIX/TAXII 가져오기
1. **Data** > **Connectors**
2. 커넥터 활성화 (MITRE ATT&CK, CVE, AbuseIPDB 등)
3. 자동으로 위협 인텔리전스 수집
4. 대시보드에서 현황 확인

---

## 3. JuiceShop (웹 취약점 실습)

- **URL**: `http://10.20.30.80:3000`
- **기본 계정**: admin@juice-sh.op (SQL Injection으로 로그인)

### 주요 기능

| 기능 | 경로 | 취약점 |
|------|------|--------|
| 로그인 | /#/login | SQL Injection, 인증 우회 |
| 검색 | /#/search | XSS, SQLi |
| 장바구니 | /#/basket | IDOR, 세션 |
| 파일 업로드 | /#/complaint | XXE, 파일 업로드 |
| 관리자 | /#/administration | 권한 상승 |
| 점수판 | /#/score-board | 챌린지 진행도 |

### Score Board 활용
1. `http://10.20.30.80:3000/#/score-board` 접속
2. 풀어야 할 챌린지 목록 확인
3. 난이도별 필터링 (1~6 stars)
4. 챌린지 해결 시 자동으로 체크됨

---

## 4. DVWA (Damn Vulnerable Web Application)

- **URL**: `http://10.20.30.80:8080`
- **계정**: admin / password

### 보안 레벨 변경
1. 로그인 후 좌측 **DVWA Security** 클릭
2. Security Level 선택: Low / Medium / High / Impossible
3. **Submit** 클릭

### 실습 메뉴

| 메뉴 | 취약점 |
|------|--------|
| Brute Force | 패스워드 크래킹 |
| Command Injection | OS 명령어 주입 |
| CSRF | 크로스사이트 요청 위조 |
| File Inclusion | LFI/RFI |
| File Upload | 악성 파일 업로드 |
| Insecure CAPTCHA | CAPTCHA 우회 |
| SQL Injection | SQL 인젝션 |
| SQL Injection (Blind) | 블라인드 SQLi |
| Weak Session IDs | 세션 예측 |
| XSS (DOM) | DOM 기반 XSS |
| XSS (Reflected) | 반사형 XSS |
| XSS (Stored) | 저장형 XSS |

---

## 5. CCC Platform (교육 플랫폼)

- **URL**: `http://CCC_SERVER:9100/app/`
- **관리자**: admin / admin1234

### 메뉴 구조

| 메뉴 | 기능 |
|------|------|
| **Training** | 18개 교과목 교안 + 실습 통합 |
| **Cyber Range** | 실습 문제 풀이 + 자동 채점 |
| **Battlefield** | 15개 시나리오 Red vs Blue 공방전 |
| **My Infra** | VM 인프라 등록, 온보딩, 검수 |
| **Leaderboard** | 리더보드 |
| **Blockchain** | CCCNet 성과 관리 |
| **Admin** | 그룹/학생/승급/Lab 검증 |

### 실습 제출 방법 (Cyber Range)
1. **Cyber Range** 메뉴 클릭
2. 과목 선택 → 주차 선택
3. 5문제씩 그룹으로 표시
4. 각 문제의 답변을 텍스트 영역에 입력
5. **Submit** 클릭 → 자동 채점 결과 확인

### AI Tutor 사용
1. 우하단 **AI** 버튼 클릭 (또는 텍스트 드래그 → "AI Tutor에게 질문하기")
2. 질문 입력 → Send
3. 현재 보고 있는 교안 내용 기반으로 답변
