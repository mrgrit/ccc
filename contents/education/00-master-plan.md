# 보안 교육과정 마스터 플랜

**총 8과목 × 15주 × 3시간 = 360시간**
**대상:** 대학교 신입생~2학년 (보안 비전공자 포함)
**방식:** 100% 실습 중심, 모든 명령어 검증 완료, 실환경 재현 가능
**인프라:** OpsClaw 5대 서버 (opsclaw, secu, web, siem, dgx-spark)

---

## 실습 인프라

```
┌─────────────────────────────────────────────────────┐
│  opsclaw (192.168.208.142 / 10.20.30.201)           │
│  → Manager API, SubAgent, 교육 control plane        │
├─────────────────────────────────────────────────────┤
│  secu (10.20.30.1) → nftables, Suricata IPS         │
│  web  (10.20.30.80) → BunkerWeb/ModSec, JuiceShop   │
│  siem (10.20.30.100) → Wazuh 4.11.2, OpenCTI        │
│  dgx-spark (192.168.0.105) → Ollama LLM, GPU        │
└─────────────────────────────────────────────────────┘
```

---

## 과목 구성

### Course 1: 사이버보안 공격 / 웹해킹 / 침투테스트
**파일:** `course1-attack/`
**키워드:** OWASP Top 10, MITRE ATT&CK, Kali 도구, SQLi, XSS, 권한상승
**실습 대상:** web (JuiceShop), secu (IPS 우회)

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | 보안 개론 + 실습 환경 구축 | SSH 접속, 서버 구조 이해, OpsClaw 소개 |
| 2 | 정보수집과 정찰 (Reconnaissance) | nmap, whois, dig, robots.txt, 헤더 분석 |
| 3 | 웹 애플리케이션 구조 이해 | HTTP/HTTPS, 쿠키, 세션, JWT, REST API |
| 4 | OWASP Top 10 (1): Injection | SQLi 원리, JuiceShop SQLi 실습, 방어 |
| 5 | OWASP Top 10 (2): XSS | Reflected/Stored/DOM XSS, JuiceShop 실습 |
| 6 | OWASP Top 10 (3): 인증/접근제어 | 세션 하이재킹, JWT 위조, 권한 우회 |
| 7 | OWASP Top 10 (4): SSRF, 파일업로드 | SSRF 원리, 웹셸, 파일 업로드 우회 |
| 8 | 중간고사: CTF 실습 | JuiceShop 챌린지 10문제 |
| 9 | 네트워크 공격 기초 | 포트 스캔, 패킷 캡처, ARP 스푸핑 |
| 10 | IPS/방화벽 우회 기법 | Suricata 룰 분석, 인코딩 우회, 터널링 |
| 11 | 권한 상승 (Linux) | SUID, sudo, cron, PATH 하이잭, 커널 exploit |
| 12 | 지속성 확보 + 흔적 제거 | SSH 키, cron backdoor, 로그 삭제, /dev/shm |
| 13 | MITRE ATT&CK 프레임워크 | 전술/기법 매핑, 공격 체인 설계 |
| 14 | 자동화 침투 테스트 | OpsClaw 활용 자동 공격, Playbook 기반 재현 |
| 15 | 기말: 종합 침투 테스트 | 전체 인프라 대상 모의해킹 + 보고서 작성 |

### Course 2: 보안시스템/솔루션 운영
**파일:** `course2-security-ops/`
**키워드:** nftables, Suricata, Wazuh, BunkerWeb, OpenCTI, 설치/구성/룰/운영

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | 보안 솔루션 개론 + 인프라 소개 | 방화벽, IDS/IPS, WAF, SIEM, CTI 개념 |
| 2 | nftables 방화벽 (1): 기초 | 테이블/체인/룰 구조, INPUT/FORWARD/OUTPUT |
| 3 | nftables 방화벽 (2): 실전 | NAT, 포트포워딩, 화이트리스트, 로깅 |
| 4 | Suricata IPS (1): 설치/구성 | 설치, NFQUEUE 연동, 기본 룰셋 |
| 5 | Suricata IPS (2): 룰 작성 | 시그니처 문법, 커스텀 룰, alert/drop |
| 6 | Suricata IPS (3): 운영 | 로그 분석, 성능 튜닝, 오탐 관리 |
| 7 | BunkerWeb WAF: 설치/구성 | ModSecurity CRS, 커스텀 룰, 예외 처리 |
| 8 | 중간고사: 방화벽+IPS 구성 실습 | nftables + Suricata 통합 보안 정책 구현 |
| 9 | Wazuh SIEM (1): 설치/구성 | Manager/Agent 설치, 대시보드, 기본 설정 |
| 10 | Wazuh SIEM (2): 탐지 룰 | local_rules.xml, 커스텀 룰 작성, logtest |
| 11 | Wazuh SIEM (3): 무결성 모니터링 | FIM, SCA, 취약점 탐지, Active Response |
| 12 | OpenCTI (1): 설치/구성 | Docker 설치, 초기 설정, 데이터 소스 연동 |
| 13 | OpenCTI (2): 위협 인텔리전스 활용 | IOC 관리, 공격 그룹 분석, STIX/TAXII |
| 14 | 통합 보안 아키텍처 | 전체 솔루션 연동 (FW→IPS→WAF→SIEM→CTI) |
| 15 | 기말: 보안 인프라 구축 프로젝트 | 처음부터 전체 보안 솔루션 스택 구축 |

### Course 3: 웹취약점 점검
**파일:** `course3-web-vuln/`
**키워드:** OWASP Testing Guide, 취약점 스캐너, 수동 점검, 보고서 작성

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | 웹취약점 점검 개론 | 점검 vs 해킹, 법적 기준, 점검 절차 |
| 2 | 점검 도구 환경 구축 | Burp Suite, OWASP ZAP, nikto, sqlmap |
| 3 | 정보수집 점검 | 디렉토리 스캔, 기술 스택 식별, SSL/TLS 점검 |
| 4 | 인증/세션 관리 점검 | 패스워드 정책, 세션 타임아웃, 다중 로그인 |
| 5 | 입력값 검증 점검 (1): SQL Injection | 블라인드 SQLi, 시간 기반, UNION, 자동화 |
| 6 | 입력값 검증 점검 (2): XSS/CSRF | 반사형/저장형/DOM XSS, CSRF 토큰 검증 |
| 7 | 입력값 검증 점검 (3): 파일/명령어 | 파일 업로드, 경로 순회, OS 명령어 주입 |
| 8 | 중간고사: JuiceShop 취약점 점검 보고서 | OWASP Testing Guide 기반 체계적 점검 |
| 9 | 접근제어 점검 | 수평/수직 권한 상승, IDOR, API 접근제어 |
| 10 | 암호화/통신 보안 점검 | HTTPS 설정, 인증서 검증, 취약 암호 스위트 |
| 11 | 에러 처리/정보 노출 점검 | 스택 트레이스, 디버그 모드, 디렉토리 리스팅 |
| 12 | API 보안 점검 | REST API 인증, Rate limiting, Swagger 노출 |
| 13 | 자동화 점검 도구 활용 | OWASP ZAP 자동 스캔, 보고서 생성 |
| 14 | 취약점 점검 보고서 작성법 | CVSS 점수, 재현 절차, 권고사항, 보고서 포맷 |
| 15 | 기말: 종합 웹취약점 점검 프로젝트 | 대상 선정→점검→보고서 전체 사이클 |

### Course 4: 보안 표준/컴플라이언스 (ISO 27001, ISMS-P)
**파일:** `course4-compliance/`
**키워드:** ISO 27001, ISMS-P, NIST CSF, GDPR, 보안 점검 체크리스트

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | 정보보안 표준 개론 | 표준의 필요성, 주요 표준 비교 |
| 2 | ISO 27001 (1): 구조와 원칙 | ISMS, 리스크 관리, PDCA, Annex A 개요 |
| 3 | ISO 27001 (2): 통제 항목 | A.5~A.8 (조직, 인적, 물리, 기술) |
| 4 | ISO 27001 (3): 기술 통제 실습 | 접근제어, 암호화, 네트워크 보안 점검 |
| 5 | ISMS-P (1): 한국 인증 제도 | 관리체계, 보호대책, 개인정보 처리 |
| 6 | ISMS-P (2): 점검 항목 실습 | 80개 통제항목 중 핵심 20개 실습 점검 |
| 7 | NIST Cybersecurity Framework | Identify, Protect, Detect, Respond, Recover |
| 8 | 중간고사: 보안 점검 체크리스트 작성 | 실습 인프라 대상 ISO 27001 기반 점검 |
| 9 | GDPR / 개인정보보호 | EU GDPR, 한국 개인정보보호법 비교 |
| 10 | 리스크 평가 실습 | 자산 식별, 위협 분석, 취약점 매핑, 리스크 매트릭스 |
| 11 | 보안 정책 수립 | 접근제어 정책, 패스워드 정책, 인시던트 대응 정책 |
| 12 | 보안 감사 실습 | 로그 감사, 설정 점검, 컴플라이언스 갭 분석 |
| 13 | 미국 표준: SOC 2, HIPAA | Type I/II, 신뢰 서비스 기준, 의료 정보 보호 |
| 14 | 인증 준비 실습 | SoA 작성, 증적 수집, 심사 대응 |
| 15 | 기말: 모의 인증 심사 | 실습 인프라 대상 전체 인증 심사 시뮬레이션 |

### Course 5: 보안관제 / 분석 / 대응 / SIEM
**파일:** `course5-soc/`
**키워드:** SOC, 보안관제, 로그 분석, 인시던트 대응, Wazuh, SIGMA

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | 보안관제(SOC) 개론 | SOC 역할, L1/L2/L3, 관제 프로세스 |
| 2 | 로그 이해 (1): 시스템 로그 | syslog, auth.log, journal, auditd |
| 3 | 로그 이해 (2): 네트워크/웹 로그 | Apache, Nginx, Suricata, nftables 로그 |
| 4 | Wazuh 관제 환경 구축 | Dashboard 활용, Agent 관리, 경보 확인 |
| 5 | 경보 분석 (1): 기초 | 경보 수준, 분류, 오탐/정탐 판별 |
| 6 | 경보 분석 (2): 실전 | 실제 공격 로그 분석, ATT&CK 매핑 |
| 7 | SIGMA 룰 작성 | SIGMA 문법, SIEM 변환, 커스텀 탐지 |
| 8 | 중간고사: 로그 분석 실습 시험 | 공격 로그 제공 → 분석 → ATT&CK 매핑 |
| 9 | 인시던트 대응 절차 | 탐지→분석→격리→제거→복구→교훈 |
| 10 | 인시던트 대응 실습 (1): 웹 공격 | SQLi 탐지 → 분석 → 차단 → 보고 |
| 11 | 인시던트 대응 실습 (2): 악성코드 | 의심 파일 분석, 프로세스 조사, 격리 |
| 12 | 인시던트 대응 실습 (3): 내부 위협 | sudo 남용, 비인가 접근, 데이터 유출 |
| 13 | 위협 인텔리전스 (CTI) 활용 | OpenCTI 연동, IOC 조회, 위협 헌팅 |
| 14 | 자동화 관제: OpsClaw Agent Daemon | 자율 탐지 에이전트 구성 + 자극 테스트 |
| 15 | 기말: 종합 인시던트 대응 훈련 | Red Team 공격 → Blue Team 관제/대응 |

---

### Course 6: Docker/클라우드 보안
**파일:** `course6-cloud-container/`
**키워드:** Docker 보안, 컨테이너 이스케이프, K8s 보안, 클라우드 IAM, S3 노출

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | 컨테이너/클라우드 보안 개론 | Docker 기초, 클라우드 서비스 모델, 공유 책임 모델 |
| 2 | Docker 기초 + 보안 | 이미지, 컨테이너, 네트워크, 볼륨, Dockerfile 보안 |
| 3 | Docker 취약점 (1): 이미지 보안 | 이미지 스캐닝(Trivy), 베이스 이미지, 비밀 노출 |
| 4 | Docker 취약점 (2): 런타임 보안 | 권한 상승, 컨테이너 이스케이프, --privileged |
| 5 | Docker 네트워크 보안 | 네트워크 격리, 포트 노출, 컨테이너 간 통신 제어 |
| 6 | Docker Compose 보안 | 비밀 관리, 리소스 제한, 헬스체크, 보안 설정 |
| 7 | Docker 보안 점검 | Docker Bench for Security, CIS 벤치마크 |
| 8 | 중간고사: Docker 보안 강화 프로젝트 | 취약한 Docker 환경 → 보안 강화 |
| 9 | 클라우드 보안 기초 (AWS/GCP) | IAM, VPC, Security Group, 암호화 |
| 10 | 클라우드 설정 오류 | S3 버킷 노출, 과도한 IAM 권한, 퍼블릭 인스턴스 |
| 11 | Kubernetes 보안 기초 | Pod Security, RBAC, NetworkPolicy, Secrets |
| 12 | Kubernetes 공격 시나리오 | Pod 탈출, 서비스 어카운트 남용, etcd 접근 |
| 13 | 클라우드 보안 모니터링 | CloudTrail, CloudWatch, GuardDuty 개념 |
| 14 | Infrastructure as Code 보안 | Terraform 보안 스캔, IaC 정적 분석 |
| 15 | 기말: 클라우드 보안 아키텍처 설계 | 제로 트러스트 기반 클라우드 보안 설계 |

### Course 7: AI(LLM)를 활용한 보안
**파일:** `course7-ai-security/`
**키워드:** LLM 보안 자동화, AI 에이전트, 프롬프트 엔지니어링, 자동화 분석

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | AI/LLM 보안 활용 개론 | LLM 개요, 보안 분야 AI 활용 현황 |
| 2 | LLM 기초 + Ollama 실습 | 모델 설치, 프롬프트, temperature, API 호출 |
| 3 | 프롬프트 엔지니어링 for 보안 | 로그 분석 프롬프트, 취약점 설명, 보고서 생성 |
| 4 | LLM 기반 로그 분석 | Wazuh 경보 → LLM 분석 → 위협 판단 |
| 5 | LLM 기반 탐지 룰 자동 생성 | 공격 패턴 → SIGMA/Wazuh 룰 자동 작성 |
| 6 | LLM 기반 취약점 분석 | 코드 리뷰, CVE 분석, 패치 권고 자동 생성 |
| 7 | AI 에이전트 아키텍처 | Master-Manager-SubAgent, 위임, 자율 판단 |
| 8 | 중간고사: LLM 보안 분석 도구 개발 | 특정 로그 → LLM 분석 → 보고서 자동화 |
| 9 | OpsClaw 활용 (1): 기본 운용 | 프로젝트 생성, dispatch, execute-plan |
| 10 | OpsClaw 활용 (2): Playbook + RL | Playbook 생성, 보상 기반 정책 학습 |
| 11 | 자율 미션 (Mission) 실습 | /a2a/mission으로 Red/Blue 자율 미션 |
| 12 | Agent Daemon: 자율 보안 관제 | explore + daemon + 자극 테스트 |
| 13 | 분산 지식 아키텍처 | local_knowledge, 경량 모델 지식 전이 |
| 14 | LLM 에이전트 행동 통제 (RL Steering) | 보상 함수 설계, 행동 유도 실험 |
| 15 | 기말: AI 보안 자동화 프로젝트 | 전체 보안 운용을 AI로 자동화 |

### Course 8: AI Safety
**파일:** `course8-ai-safety/`
**키워드:** 프롬프트 인젝션, 탈옥, 가드레일, 적대적 공격, 모델 보안, 윤리

| 주차 | 주제 | 실습 |
|------|------|------|
| 1 | AI Safety 개론 | AI 위험 분류, 사고 사례, 규제 동향 |
| 2 | 프롬프트 인젝션 (1): 기초 | 직접 인젝션, 간접 인젝션, 시스템 프롬프트 탈취 |
| 3 | 프롬프트 인젝션 (2): 고급 | 다단계 인젝션, 인코딩 우회, 컨텍스트 오염 |
| 4 | LLM 탈옥 (Jailbreak) | DAN, 역할극, 다국어 우회, 토큰 레벨 공격 |
| 5 | 가드레일과 출력 필터링 | Constitutional AI, 콘텐츠 필터, 분류기 |
| 6 | 적대적 입력 (Adversarial) | 이미지/텍스트 적대적 예제, 모델 강건성 |
| 7 | 데이터 오염과 학습 보안 | 훈련 데이터 오염, 백도어 공격, 데이터 검증 |
| 8 | 중간고사: LLM 취약점 평가 | 대상 모델 탈옥 시도 + 방어 보고서 |
| 9 | 모델 보안: 모델 도난/추론 | 모델 추출, 멤버십 추론, 워터마킹 |
| 10 | 에이전트 보안 위협 | Tool 남용, 권한 상승, 자율 에이전트 위험 |
| 11 | RAG 보안 | 지식 오염, 문서 주입, 검색 결과 조작 |
| 12 | AI 윤리와 규제 | EU AI Act, NIST AI RMF, 한국 AI 법안 |
| 13 | Red Teaming for AI | 체계적 AI 취약점 평가, 자동화 레드팀 |
| 14 | AI Safety 평가 프레임워크 | CyberSecEval, AgentHarm, HarmBench |
| 15 | 기말: AI 모델 보안 평가 프로젝트 | 대상 모델 종합 보안 평가 + 보고서 |

---

## 논문 아이디어 (4편)

| # | 제목 | 관점 | 해당 과목 |
|---|------|------|---------|
| P1 | LLM 에이전트 기반 실습형 보안 교육 플랫폼 설계 | 교육 공학 + 에이전트 | 전체 |
| P2 | CTF 자동 생성 및 적응형 난이도 조절 시스템 | AI 교육 + 게이미피케이션 | C1, C3 |
| P3 | 자율 에이전트를 활용한 보안관제 인력 양성 모델 | SOC 교육 + Agent Daemon | C5, C7 |
| P4 | AI Safety 교육 커리큘럼 설계: 프롬프트 인젝션부터 에이전트 위협까지 | AI Safety 교육 | C8 |

---

## 실습 검증 원칙

1. **모든 명령어는 OpsClaw 또는 직접 실행으로 검증**
2. **검증 안 된 명령어는 절대 교재에 포함하지 않음**
3. **각 주차 시작에 전제 조건(prerequisite) 명시**
4. **각 실습 끝에 검증 방법(expected output) 명시**
