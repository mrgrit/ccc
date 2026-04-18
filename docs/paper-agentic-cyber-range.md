# ccc: Agentic Cyber Range — AI Agent 시대를 위한 실전 사이버보안 교육 플랫폼

> 연구 제안 (Research Proposal), v0.1 — 2026-04

---

## 1. 연구목적 및 필요성

### 1.1 AI Agent 시대의 위협 지형 변화

대규모 언어 모델(LLM)과 이를 기반으로 한 자율 에이전트(Autonomous Agent)의 능력이 2023년 이후 가파르게 확장되면서, 사이버 위협의 성격 자체가 변화하고 있다. 2024~2026년에 걸쳐 공개된 Anthropic Claude 계열, OpenAI o-series, 그리고 최근 등장한 *Claude Mythos*, *GPT 5.4 Cyber* 등 공격 특화 고지능 모델은 세 가지 질적으로 새로운 위협을 제기한다 [1][2][3].

- **(a) 비대칭성**: 단일 공격자가 저비용 LLM 에이전트를 다수 병렬 가동하여, 전통적으로 국가·조직 단위에서만 가능하던 다단계 침투·정찰·측면이동을 1인 단위 규모로 수행할 수 있다 [4][5].
- **(b) 고지능성**: 제로데이 취약점의 자동 탐색·연쇄(exploit chaining)·사회공학 문구 생성이 "숙련 분석가 수준"에 근접하고 있음이 다수의 벤치마크(CyberSecEval 2, AgentHarm, HarmBench)에서 확인되었다 [6][7][8].
- **(c) 무차별성**: 비용 단가 하락으로 "가치가 낮은 대상"도 수지가 맞는 공격 대상이 되어, 중소기업·개인·IoT 디바이스가 공격 포트폴리오에 포함된다 [9].

기존 위협 모델은 인간 공격자의 *인력 한계*를 암묵적 제약으로 가정해 왔으나, Agentic 공격은 이 제약을 해제한다. 이는 방어 측의 인력 기반 대응 모델(SOC 3교대, 수작업 헌팅) 역시 구조적으로 대응 불가능해짐을 의미한다.

### 1.2 기존 사이버보안 교육의 한계

현재 국내·외 사이버보안 교육·훈련 체계는 세 층위에서 이 변화에 뒤처져 있다.

1. **대상의 낙후성** — 교육과정의 공격·방어 실습은 OWASP Top 10(2021), MITRE ATT&CK v13 등 2020~2023년 고정 시나리오 중심으로, *AI 에이전트 자체*를 공격자·방어자·공격 대상으로 다루는 비중이 미미하다.
2. **전달 방식의 경직성** — 기존 훈련장(Cyber Range)은 강사 주도 시나리오·공용 인프라·수작업 환경 구축을 전제로 한다. 구축·리셋 비용이 커 수강생 1인당 실습 시간이 제한되고, 신규 위협이 등장한 뒤 시나리오화까지 수 주~수개월이 소요된다 [10][11].
3. **검증의 부재** — 실습 콘텐츠의 *정합성*(명령어가 실제 동작하는지, 설명과 실제 결과가 일치하는지)은 저자 수작업에 의존해 왔고, 학기 중간에 환경·패키지 버전이 바뀌면 실습이 기능 불능이 된다.

### 1.3 폐쇄망 환경에서의 AI 운용 요구

국방·금융·공공·기반시설 등 국내 주요 수요처의 사이버 교육은 **인터넷 격리(air-gapped) 환경**에서 수행되어야 한다. 이는 상용 클라우드 LLM API(OpenAI, Anthropic, Google)의 사용을 원천 차단하며, 반대로 *완전한 온프레미스(on-prem) AI 스택*에서 에이전트·콘텐츠 생성·학습 튜터 기능이 모두 동작해야 함을 의미한다. 이는 단순한 데이터 주권 문제가 아니라 *교육 플랫폼의 가용성 문제*이며, 기존 클라우드 의존 교육 플랫폼으로는 해결되지 않는다.

### 1.4 연구 목적

본 연구는 위의 세 한계를 동시에 해소하는 **ccc(Agentic Cyber Range)**, 즉 AI 에이전트 시대에 맞게 설계된 *폐쇄망 구동 실전형 사이버보안 교육 플랫폼*을 제안·구축·평가한다. ccc의 설계 목표는 다음과 같다.

1. **AI Agent 자체를 교육 대상에 포함**: LLM 모의해킹·AI Safety·모델 공격/방어·AI Agent 침해 대응을 독립 교과로 편성.
2. **개인별 자동 인프라**: 수강생 1인당 독립 가상 인프라를 분 단위 자동 프로비저닝하여 실습 시간 손실 제거.
3. **AI 생성 시나리오 기반 Battle**: 신규 공격·방어 기법이 공개되면 수시간 내에 훈련 시나리오(레드/블루 미션)로 변환.
4. **AI에 의한 콘텐츠 상시 검증**: 모든 실습 단계가 에이전트에 의해 정기 재검증되며 회귀가 자동 탐지됨.
5. **폐쇄망 완전 구동**: 상용 클라우드 API 없이 온프레미스 LLM(gpt-oss, gemma, qwen 계열)만으로 전 기능 동작.

---

## 2. 연구내용 및 방법

### 2.1 Agentic Cyber Range 아키텍처 (개요)

ccc는 네 계층으로 구성된다.

| 계층 | 역할 | 주요 구성요소 |
|------|------|---------------|
| **학습 계층** | 교안(Lecture) · 실습(Lab) · 대전(Battle) · CTF 제공, 학습자 진도 추적 | 웹 UI, 학습 이력 DB |
| **실습 인프라 계층** | 수강생별 가상 인프라 자동 프로비저닝 (방화벽·IPS·WAF·SIEM·웹 타깃) | VMware + YAML 시나리오 자동화 |
| **AI 서비스 계층** | 폐쇄망 LLM 서빙, 학습 튜터, 콘텐츠 검증, 시나리오 생성 | 온프레미스 LLM, 에이전트 오케스트레이션 |
| **평가·검증 계층** | 실습 정답 검증, 학습 성과 리포팅, 콘텐츠 회귀 탐지 | 단계별 `verify` 엔진 + AI 의미 판정 |

본 논문은 **학습 계층·평가 계층**과 **폐쇄망 LLM 활용 설계**를 중심으로 기술하며, AI 서비스 계층의 내부 오케스트레이션(자율 에이전트의 추론·재시도·메모리 구조)은 별도 연구[별논문-예정]에서 상세히 다룬다.

### 2.2 AI Agent 시대를 반영한 교과 편성

본 연구는 18개 교과(각 15주) 체계를 제안하며, 그 중 AI 에이전트 관련 신규 교과를 5개 포함한다.

| # | 교과 | 관점 | AI-신규 |
|---|------|------|---------|
| 1 | 사이버공격·웹해킹·모의침투 | 공격 기초 | |
| 2 | 보안시스템·솔루션 운영 | 방어 운영 | |
| 3 | 웹 취약점 점검 | 취약점 평가 | |
| 4 | 보안 표준·컴플라이언스 | 거버넌스 | |
| 5 | 보안관제·SIEM·대응 | 관제 | |
| 6 | Docker/클라우드 보안 | 클라우드 | |
| 7 | LLM 활용 보안 자동화 | AI×보안 | **✓** |
| 8 | AI Safety | AI 보안 | **✓** |
| 9~10 | AI 에이전트 보안 | AI 에이전트 | **✓** |
| 11 | 공방전(Battle) 기초 | 종합 | |
| 12 | 공방전 심화 (AI vs AI) | 종합 | **✓** |
| 13 | 침투테스트 심화 | 공격 심화 | |
| 14 | 보안관제 심화 (SOC 자동화·AI 활용) | 관제 심화 | **✓** |
| 15 | AI Safety 심화 (모델 공격·방어) | AI 보안 심화 | **✓** |
| 16~18 | 물리보안·IoT·자율시스템 | 확장 영역 | |

추가로 본 연구는 현재 교과 체계에 **결여되어 있는** "AI Agent 침해 대응(Incident Response for Agentic Threats)" 교과(임시 배정 C19)의 설계를 제안한다. 구성안은 다음과 같다.

- (w1~3) AI Agent 공격 특성: 비동기 다단계, 행위 분산, 에이전트 지문(fingerprint)
- (w4~6) 에이전트 트래픽·API 행동 기반 탐지(이상 LLM 호출 패턴, 도구 사용 이상치)
- (w7~9) 에이전트 격리·차단(레이트리밋, 의미 기반 필터, 도구 제한)
- (w10~12) 자율 방어 에이전트(Blue-Agent)로 자율 공격 대응
- (w13~15) 모의 공방: 자율 레드 에이전트 vs 자율 블루 에이전트, 퍼플팀 복기

본 교과는 자율 공격 모의에 의한 지속적 시나리오 갱신을 전제하므로, 2.4절의 AI 시나리오 생성 기능과 직결된다.

### 2.3 개인별 자동 인프라 프로비저닝

기존 사이버 훈련장은 공용 인프라 또는 강의자 수작업 복제에 의존한다. ccc는 수강생 1인당 다음을 자동 생성한다(프로비저닝 기준 1~3분).

- **bastion** (제어·에이전트 호스트): 10.20.30.201
- **secu** (방화벽·IPS): 10.20.30.1
- **web** (웹 타깃·WAF): 10.20.30.80
- **siem** (SIEM·CTI): 10.20.30.100

각 VM 이미지는 VMware 하이퍼바이저에 사전 배포된 *골드 템플릿*이며, 네트워크·자격증명·서비스 초기화는 YAML 정의 기반 단일 스크립트로 완료된다. 수강생의 변경 사항이 원복 불능 상태가 되어도 `./reset.sh`로 15분 이내 복구된다.

이 설계는 두 가지 실무적 효과를 낳는다.

1. **실습 유효시간 극대화**: 한 학기 3시간 × 15주 = 45시간 중, 기존 교육에서는 인프라 구성에만 5~10시간을 소비해 왔다. ccc는 이를 총량 기준 30분 이내로 압축한다(최초 접속·점검 시간만 포함).
2. **사고 실험 공간 확보**: 학습자가 자발적으로 인프라를 파괴적으로 실험(예: IPS 정책 고의 과오, 전체 로그 삭제)해 볼 수 있으며, 실패가 비용이 아닌 학습 신호가 된다.

### 2.4 AI 에이전트 기반 시나리오 생성(Battle)

Red/Blue 공방 시나리오는 *최신 위협*을 빠르게 훈련으로 전환해야 교육적 가치가 유지된다. ccc의 시나리오 생성 파이프라인은 다음 순서로 동작한다.

1. **위협 수집**: MITRE ATT&CK 업데이트, CVE 신규 공개, OSINT 요약 문서(예: The Hacker News, 공식 보안 보고서)를 온프레미스 LLM이 요약·구조화.
2. **시나리오 골격 생성**: 요약된 TTP를 ATT&CK 단계로 매핑 → 공격 체인(step 1~N) 초안 생성.
3. **실습화**: 공격 체인의 각 단계를 ccc 인프라(4-node) 상에서 실제로 실행 가능한 명령·페이로드·기대 결과로 변환.
4. **검증**: 2.6절의 검증 에이전트가 각 단계를 수강생 대신 시범 실행해 실제 재현성을 확인.
5. **블루 미션 생성**: 공격 체인의 각 단계를 SIEM 탐지 룰·플레이북 관점에서 *방어 과제*로 역변환.

이 파이프라인은 신규 위협 공개 → 훈련 가능 시점까지 **수 시간**으로 단축하는 것을 목표로 하며, 이는 전통적 교육 도입 주기(수개월) 대비 두 자릿수 이상의 가속에 해당한다.

### 2.5 폐쇄망에서의 AI 운용 설계

ccc는 상용 LLM API에 전혀 의존하지 않는다. 이는 국방·금융·공공 수요를 수용하기 위한 **핵심 제약**이며, 연구의 실무적 차별점이다.

- **모델 스택**: 주 모델(gpt-oss 120B 계열), 경량 모델(gemma3, qwen3 계열)을 로컬 GPU(NVIDIA, DGX 급) 상 Ollama로 서빙.
- **모델 선택 기준**: 성능/지연 균형, 한국어 지시추종, Tool-use 응답 품질, 파인튜닝 용이성(QLoRA 적용).
- **Prompt-only 적응**: 클라우드 LLM과 달리 대규모 RLHF 후속 튜닝이 제한되므로, 시스템 프롬프트·하네스 레벨의 제어로 에이전트 행동을 교정한다. 이 접근은 모델 교체에 강건하며(모델 독립적), 폐쇄망에서의 안전한 점진 개선을 가능하게 한다.
- **오프라인 업데이트**: 신규 모델·룰셋·CVE DB는 수동 이전(USB, 일회성 네트워크 구간)으로 반입되며, 이를 전제로 한 배포 절차가 설계에 포함된다.

이 설계는 최근 EU ENISA·NIST가 제시한 AI 시스템의 데이터 주권 권고와도 부합한다 [12][13].

### 2.6 AI에 의한 콘텐츠 상시 검증

본 연구는 2,734개의 실습 단계(17개 교과 × 주차 × 단계)에 대해 AI 에이전트가 *수강생 대신* 실습을 수행하고 단계별 검증(파일 존재, nft 룰 존재, 서비스 활성, 로그 패턴, 명령 출력 일치, 의미 판정)을 수행하도록 한다. 검증 결과는 세 가지 상태로 기록된다.

- **pass**: 자동 검증 통과
- **qa_fallback**: 1차 검증은 실패했으나 LLM의 의미 판정에서 의도가 충족됨(부분 성공)
- **fail**: 구조적 오류 — 콘텐츠 수정 필요

본 파이프라인은 학기 중 주간 단위로 재실행되어, 모델 갱신·패키지 버전 변화·인프라 변동으로 인한 콘텐츠 회귀를 자동 탐지한다. 검증 커버리지와 회귀 탐지율은 본 연구의 핵심 평가 지표이다.

### 2.7 연구 방법 및 평가

본 연구는 디자인 사이언스 리서치(Design Science Research, DSR) 방법론 [14] 을 따른다. 산출물은 (1) 시스템(ccc 플랫폼), (2) 교과 설계(커리큘럼·교안·실습 자료), (3) 평가 데이터(검증 결과, 학습 성과)이다.

평가 지표는 다음과 같다.

| 범주 | 지표 | 측정 방법 |
|------|------|----------|
| 플랫폼 | 인프라 프로비저닝 시간 | 스크립트 실행 측정 |
| 플랫폼 | 콘텐츠 검증 커버리지·회귀 탐지율 | 검증 결과 로그 집계 |
| 학습 | 학습자 단계별 통과율 / 오답 패턴 | 학습 이력 DB |
| 학습 | 사후 설문(자기효능감, 전이) | 리커트 척도 + 자유응답 |
| 운영 | 시나리오 공개→훈련 가능 시점 소요시간 | 샘플 위협 10건 케이스 스터디 |
| AI | 에이전트 검증 판정의 일치도(κ) | 전문가 표본 검토 |

이 중 플랫폼·운영 지표는 본 논문에서, 학습 지표는 후속 효과성 검증 논문[별논문-예정]에서 상세 보고한다.

---

## 3. 국내·외 연구활동(연구배경)

### 3.1 사이버 훈련장(Cyber Range) 연구

사이버 훈련장은 2000년대 중반 DoD·DHS의 요구로 체계화되었고, 2010년대 후반 이후 학술적 정의가 공고해졌다. Yamin 등(2020)은 Cyber Range를 "실제 시스템의 복제·시나리오·도구·아키텍처의 집합"으로 정의하고 40여 개 사례를 비교 분석하였다 [15]. Vykopal 등은 KYPO 프로젝트를 통해 대학 교육용 확장 가능 훈련장 설계 원칙을 제시하였다 [16]. Beuran 등은 CyTrONE에서 교안-실습-평가 통합 프레임워크를 제안하였다 [17].

그러나 기존 연구는 **(i) 수강생 1인당 독립 인프라의 경제성**, **(ii) AI 에이전트를 교육 대상으로 한 시나리오**, **(iii) 콘텐츠의 자동 회귀 검증**의 세 축을 동시에 다룬 사례가 없다. 특히 NICE Cybersecurity Workforce Framework(NIST SP 800-181)[18]의 Work Role 분류 역시 AI 에이전트 방어·대응 역할을 아직 포함하지 않는다.

### 3.2 LLM·에이전트의 공격적 능력 연구

Deng 등의 *PentestGPT*는 LLM이 숙련 모의침투 분석가 수준의 작업 분해·추론을 수행할 수 있음을 보였고[4], Fang 등은 단일 LLM 에이전트가 공개된 실제 취약점의 다수를 자동 악용할 수 있음을 실험적으로 확인하였다[5]. 같은 팀의 후속 연구는 **에이전트 팀(Team of LLM Agents)**이 제로데이 수준 취약점을 탐색·연쇄할 수 있음을 보고하였다[5]. Mirsky 등은 *Offensive AI*의 조직적 위협 지형을 종합 정리하였다[19].

이러한 결과는 방어 교육의 관점에서 "공격자 측의 자동화·지능화가 임계점을 넘었음"을 시사하며, 교육과정이 AI-의식(AI-aware)으로 재설계되어야 함을 뒷받침한다.

### 3.3 AI Safety·적대적 공격·평가 벤치마크

Zou 등은 정렬된 LLM에 대한 보편적·전이성 있는 적대적 프롬프트 공격을 시연하였다[20]. Greshake 등은 RAG·검색 통합 응용에 대한 *간접 프롬프트 인젝션*을 실증하였고[21], Wei 등은 안전 훈련의 실패 모드를 체계화하였다[22]. 평가 측면에서는 Meta의 *CyberSecEval*[6], 후속 *CyberSecEval 2*[7], *HarmBench*[8], *AgentHarm*[23] 등이 표준화된 평가 체계를 제공하고 있다. OWASP의 *LLM Top 10*[24]은 실무 관점의 위협 카탈로그로 광범위하게 인용된다. NIST AI RMF[13]는 조직 차원의 위험관리 프레임워크를 제시한다.

본 연구는 이 벤치마크들의 *평가 대상 측*이 아닌, *공격·방어 교육의 실습 자료*로의 통합 방안을 제안한다는 점에서 차별화된다.

### 3.4 Adaptive Learning 및 교육 AI

AI 기반 개인화 학습은 Anderson 등의 지능형 튜터링 시스템[25] 이후 40여 년의 연구 전통을 갖는다. 최근 LLM 기반 튜터 연구(Khan Academy의 Khanmigo 등)에서 피드백 품질·교사 개입과의 상호작용이 주요 논점이다. 그러나 대부분의 연구는 텍스트/수학 등 *비상호작용* 도메인에 집중되어 있으며, *명령행·환경 조작이 주가 되는 사이버보안 실습*에서의 LLM 튜터 설계는 연구가 희박하다[26].

### 3.5 국내 동향

국내에서는 KISA·KITRI·NIA를 중심으로 사이버 훈련장 사업이 수년간 진행되어 왔으며, 한국정보보호학회·한국정보처리학회 등이 관련 연구를 축적해 왔다. 2024년 이후 AI 보안 전문가 양성 사업(과기정통부), 국방 사이버 인력 양성 사업(국방부) 등이 확대되었으며, AI Safety 과목의 체계적 개발은 여전히 초기 단계이다. 최근 한국전자통신연구원(ETRI) 및 국가보안기술연구소의 AI 기반 보안 자동화 연구가 증가하고 있으나, 이들 대부분은 *운영용 자동화*이며 *교육·훈련*을 대상으로 한 Agentic Cyber Range 설계 연구는 확인된 바 없다.

### 3.6 기존 연구 대비 본 연구의 차별성

| 축 | 기존 연구 | 본 연구 |
|---|-----------|--------|
| 실습 대상 | IT 시스템(웹·서버·네트워크) | IT + **AI 모델·AI 에이전트** |
| 인프라 | 공용/공유 또는 수작업 | **수강생별 자동 프로비저닝** |
| 시나리오 | 고정·수동 개발 | **AI 에이전트 기반 상시 생성** |
| 콘텐츠 품질 | 저자 수작업 검증 | **AI 에이전트 상시 재검증** |
| 배치 환경 | 클라우드 API 전제 | **폐쇄망 온프레미스 LLM** |
| 대상 위협 | MITRE ATT&CK 고전 TTP | **고전 TTP + Agentic Threats** |

---

## 4. 기대효과 및 활용방안

### 4.1 학술적 기여

- **(i) Agentic Cyber Range 개념 정립**: 사이버 훈련장 연구에서 *AI 에이전트를 교육 대상*으로 포함하는 새로운 아키텍처 유형을 제안·검증한다.
- **(ii) 폐쇄망 AI 교육 플랫폼 설계 원칙**: 상용 API 없이 전 기능을 구동하는 온프레미스 LLM 기반 교육 플랫폼의 설계 지침을 실증 연구로 제시한다. 국내 국방·금융·공공 분야의 실무 수요와 직결된다.
- **(iii) AI 기반 콘텐츠 회귀 검증 방법**: 실습 자료의 정합성을 AI 에이전트가 상시 검증하는 파이프라인을 정량 지표(회귀 탐지율, pass/qa_fallback/fail 비율)와 함께 공개한다.
- **(iv) 신규 교과 "AI Agent 침해 대응" 설계안 제시**: 현 교과 체계의 빈자리를 식별·채운다.

### 4.2 교육·산업 파급효과

- **인재 공급 가속**: 개인 인프라 자동 프로비저닝으로 교육 운영 비용을 1인당 기존 대비 수 분의 1로 절감(구체 수치는 후속 보고). 동일 예산으로 수강 가능 인원 증가.
- **훈련 적시성 향상**: 신규 위협 공개 → 훈련 가능 시점까지의 지연을 수개월 → 수시간 단위로 축소.
- **수준 향상**: AI 에이전트가 반복적으로 콘텐츠를 검증함으로써 실습이 *언제나 동작*하는 상태를 유지. 학습자는 "명령어가 동작하지 않는" 외적 실패가 아닌 본질적 학습에 집중.
- **국방·공공 수용**: 폐쇄망 완전 구동 설계는 ROK군·주요 기반시설의 훈련 수요를 직접 수용 가능.

### 4.3 활용 방안

1. **대학 학부·대학원 정규 과목**: 사이버보안 전공 18개 과목 패키지로 즉시 채택 가능.
2. **공공·정부 교육과정**: KISA·KITRI·ETRI 위탁 교육의 표준 플랫폼으로 제안.
3. **산업체 재교육**: 보안 담당자·개발자 대상 단기 과정(8주, 16주)으로 재패키징.
4. **국방 사이버 인력 양성**: 폐쇄망 설계를 활용해 ROK군 사이버작전사령부·정보보호여단 교육에 도입.
5. **산학연 공동 연구**: AI Agent 공격/방어 벤치마크의 *교육용 레퍼런스 구현*으로 제공.

### 4.4 후속 연구

본 논문의 제안은 세 편의 후속 논문으로 확장될 예정이다.

- **후속 ①** 학습 효과성 검증(무작위·대조군 비교, 전이 평가).
- **후속 ②** 자율 에이전트 기반 보안 운영(ccc의 AI 서비스 계층 내부 설계, 본 논문 2.1에서 의도적으로 축약).
- **후속 ③** AI 에이전트 대 AI 에이전트 공방 프로토콜과 퍼플팀 분석.

---

## 5. 참고문헌

[1] OpenAI, "GPT-4 Technical Report," *arXiv:2303.08774*, 2023.
[2] Anthropic, "Claude 3 Model Card," Technical Report, 2024.
[3] H. Hubinger et al., "Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training," *arXiv:2401.05566*, 2024.
[4] G. Deng, Y. Liu, V. Mayoral-Vilches, P. Liu, Y. Li, Y. Xu, T. Zhang, Y. Liu, M. Pinzger, and S. Rass, "PentestGPT: Evaluating and Harnessing Large Language Models for Automated Penetration Testing," *USENIX Security Symposium*, 2024.
[5] R. Fang, R. Bindu, A. Gupta, and D. Kang, "Teams of LLM Agents Can Exploit Zero-Day Vulnerabilities," *arXiv:2406.01637*, 2024. (후속 본문: R. Fang et al., "LLM Agents can Autonomously Exploit One-day Vulnerabilities," *arXiv:2404.08144*, 2024.)
[6] M. Bhatt et al., "Purple Llama CyberSecEval: A Secure Coding Benchmark for Language Models," *arXiv:2312.04724*, 2023.
[7] M. Bhatt et al., "CyberSecEval 2: A Wide-Ranging Cybersecurity Evaluation Suite for Large Language Models," *arXiv:2404.13161*, 2024.
[8] M. Mazeika et al., "HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal," *ICML*, 2024.
[9] Y. Mirsky et al., "The Threat of Offensive AI to Organizations," *Computers & Security*, vol. 124, 103006, Elsevier, 2023.
[10] E. Ukwandu et al., "A Review of Cyber-Ranges and Test-Beds: Current and Future Trends," *Sensors/IEEE-related venue survey*, 2020. *(서베이; IEEE-등재 본 서베이 외 IEEE Access 계열 서베이 다수 존재)*
[11] M. M. Yamin, B. Katt, and V. Gkioulos, "Cyber Ranges and Security Testbeds: Scenarios, Functions, Tools and Architecture," *Computers & Security*, vol. 88, 101636, Elsevier, 2020.
[12] ENISA, "AI Cybersecurity Challenges — Threat Landscape for Artificial Intelligence," European Union Agency for Cybersecurity, 2020.
[13] National Institute of Standards and Technology, "AI Risk Management Framework (AI RMF 1.0)," *NIST*, 2023.
[14] A. R. Hevner, S. T. March, J. Park, and S. Ram, "Design Science in Information Systems Research," *MIS Quarterly*, vol. 28, no. 1, pp. 75–105, 2004.
[15] M. M. Yamin, B. Katt, and V. Gkioulos, 참고문헌 [11]과 동일.
[16] J. Vykopal, R. Ošlejšek, P. Čeleda, M. Vizváry, and D. Tovarňák, "KYPO Cyber Range: Design and Use Cases," *Proc. 12th International Conference on Software Technologies (ICSOFT)*, 2017. 후속: J. Vykopal et al., "Scalable Learning Environments for Teaching Cybersecurity Hands-on," *IEEE Frontiers in Education Conference (FIE)*, 2021.
[17] R. Beuran, C. Pham, D. Tang, K. Chinen, Y. Tan, and Y. Shinoda, "Integrated Framework for Hands-on Cybersecurity Training: CyTrONE," *Computers & Security*, vol. 78, pp. 43–59, Elsevier, 2018.
[18] W. Newhouse, S. Keith, B. Scribner, G. Witte, "National Initiative for Cybersecurity Education (NICE) Cybersecurity Workforce Framework," *NIST SP 800-181 Rev. 1*, 2020.
[19] Y. Mirsky et al., 참고문헌 [9]와 동일.
[20] A. Zou, Z. Wang, N. Carlini, M. Nasr, J. Z. Kolter, and M. Fredrikson, "Universal and Transferable Adversarial Attacks on Aligned Language Models," *arXiv:2307.15043*, 2023; 관련 후속은 *ICLR*, 2024에서 논의.
[21] K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection," *ACM Workshop on Artificial Intelligence and Security (AISec) @ CCS*, 2023.
[22] A. Wei, N. Haghtalab, and J. Steinhardt, "Jailbroken: How Does LLM Safety Training Fail?," *NeurIPS*, 2023.
[23] M. Andriushchenko et al., "AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents," *arXiv:2410.09024*, 2024.
[24] OWASP Foundation, "OWASP Top 10 for Large Language Model Applications," v1.1, 2024.
[25] J. R. Anderson, A. T. Corbett, K. R. Koedinger, and R. Pelletier, "Cognitive Tutors: Lessons Learned," *The Journal of the Learning Sciences*, vol. 4, no. 2, pp. 167–207, 1995.
[26] R. S. Baker, "Artificial Intelligence in Education: Bringing It All Together," *OECD Digital Education Outlook 2021*, OECD, 2021.
[27] N. Carlini, M. Nasr, C. A. Choquette-Choo, M. Jagielski, I. Gao, A. Awadalla, P. W. Koh, D. Ippolito, K. Lee, F. Tramer, L. Schmidt, "Are Aligned Neural Networks Adversarially Aligned?," *NeurIPS*, 2023.
[28] E. Perez et al., "Red Teaming Language Models with Language Models," *EMNLP*, 2022.
[29] IEEE Standards Association, "IEEE P2846 / IEEE 2675 계열 시스템 신뢰성·운영 보증 규격 군," 2022–2024. *(플랫폼 운영 기준 인용)*
[30] The Cyber Threat Intelligence Reports: Mandiant M-Trends 2024; CrowdStrike Global Threat Report 2024 (공신력 있는 산업 보고서).

---

### 부록 A. 제안 신규 교과 "AI Agent 침해 대응" 주차 설계 초안

| 주차 | 주제 | 실습 개요 |
|------|------|-----------|
| 1 | 개론: Agentic 위협의 특성 | 공격자 의도·에이전트 행동 프로파일 |
| 2 | AI 에이전트 TTP 분류 | ATT&CK 확장(AI-ATT&CK 초안) |
| 3 | 에이전트 공격 사례 실습 | PentestGPT 재현(샌드박스) |
| 4 | 에이전트 행위 지문·로깅 | LLM API 호출 로그 정상·이상 구분 |
| 5 | 에이전트 트래픽 이상 탐지 | 통계·도구사용 패턴 기반 탐지 |
| 6 | 에이전트 격리·차단 | 레이트리밋, 도구 허가 목록 |
| 7 | 의미 기반 필터 | 프롬프트 인젝션 탐지 가드레일 구성 |
| 8 | 중간평가: 공격 에이전트 탐지 CTF | 실제 공격 로그 판정 |
| 9 | 자율 Blue Agent 설계 | 방어 에이전트 행동 정책 |
| 10 | Blue Agent × 탐지 도구 통합 | SIEM·IDS 연계 |
| 11 | Purple Team 훈련 (1) | 자율 레드 vs 자율 블루 1회차 |
| 12 | Purple Team 훈련 (2) | 자율 레드 vs 자율 블루 2회차 + 회고 |
| 13 | 에이전트 사고 보고서 작성 | 책임·증적·법적 고려 |
| 14 | 모의 실사고 대응 | 다단계 자율 공격 시나리오 대응 |
| 15 | 기말: 종합 훈련 + 보고서 | 평가 루브릭 기반 |

---

### 부록 B. 데이터·코드·검증 산출물 공개 방침

본 연구의 (i) 실습 검증 결과 집계(단계별 pass/qa_fallback/fail), (ii) 교과 커리큘럼 구조, (iii) 인프라 프로비저닝 스크립트의 *공개 가능 부분*은 재현 연구를 위해 학술 공개한다. 다만 AI 서비스 계층의 내부 오케스트레이션과 튜닝 체크포인트는 보안상 별도 논문에서 단계적으로 공개한다.
