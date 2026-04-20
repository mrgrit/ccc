# CCC 아키텍처 · 장기 로드맵

> 작성: 2026-04-20 · Claude Code (Master Agent)
> 사용자 비전 기반 종합 설계 + 허점 검토 + 분리 전략

## 1. 최종 목표 (Vision)

**전세계 침해 정보 → AI 에이전트가 battle 시나리오·red/blue 미션을 자동 생성 → 실전 훈련 콘텐츠 자동화**

기존 훈련장은 사람이 수주간 시나리오를 수작성. CCC는 **CTI 발표 → 시간 단위 훈련 콘텐츠 생성**을 목표로, *AI Vulnerability Storm* 속도에 대응하는 AI-native 교육 시스템.

## 2. 3-Layer Agent Architecture

```
┌─ Master Agent = Claude Code (Anthropic) ────────┐   오프라인·개발자급
│  • battle/lab YAML 생성                           │   복잡 설계·검수
│  • red/blue 미션 분해                              │   비용 비쌈, 품질 높음
│  • verify 조건 작성                                │
│  • 예방 룰 초안 생성 (Suricata/Wazuh/nftables)    │
│  • 교안·콘텐츠 설계                                │
└──────────────────┬──────────────────────────────┘
                   ↓ 콘텐츠 배포
┌─ Manager Agent = gpt-oss:120b (Bastion) ────────┐   온라인·서비스급
│  • 학생 세션·경기 진행                             │   빠른 반응
│  • battle 심판·피드백                              │   폐쇄망 on-prem
│  • CTI 다이제스트 조립 (1일 1회)                   │
│  • 예방 룰 배포·롤백                                │
└──────────────────┬──────────────────────────────┘
                   ↓ 일괄 작업
┌─ SubAgent = gemma3:4b (VM별 runtime) ───────────┐   분산 워커
│  • CTI 수집·요약·태깅 (병렬)                       │   경량·고속
│  • 개별 shell 실행                                 │   컨텍스트 작음
│  • 명령 추출/생성 fallback (w23/w24)                │
└─────────────────────────────────────────────────┘
```

## 3. 전체 파이프라인

```
[외부 CTI feed]        [학습 세션]
   NVD · OpenCTI         학생 요청
   Feedly · TF             ↓
   AbuseIPDB        [Manager: 실시간 응대]
       ↓                    ↑
[SubAgent 수집]         [Bastion 검증]
  요약·태깅·매핑       ├─ 타당성
       ↓               ├─ 자동 해결 가능성
[Master: 콘텐츠 생성]   └─ 보안 정책 준수
  battle/lab YAML            ↑
  verify 조건             [학생 실습/battle]
  예방 룰 초안               ↑
       ↓               [Manager: 배포]
[staging 검증]               ↑
       ↓               [관리자 UI]
[prod 배포]            모니터링 + 개입
```

## 4. 구성 컴포넌트 상세

### 4.1 CTI Collector (신규)
- **위치**: 처음엔 CCC 내부 → 검증 후 분리 후보
- **스택**: Python + OpenCTI client + NVD feed
- **주기**: 30분 경량 수집 + 1일 1회 대형 다이제스트
- **결과물**: `contents/threats/YYYY-MM-DD/*.json`
- **모델**: SubAgent(gemma3:4b) 병렬 요약

### 4.2 Battle/Mission Auto-Generator (신규, 논문 핵심)
- **위치**: CCC (`apps/battle-factory/` 예정)
- **입력**: CTI JSON + 기존 battle 스키마
- **Master Agent 호출**: Claude Code가 YAML 초안 생성
- **검증**: Bastion이 red/blue 시나리오 자동 실행 시도 → 해결 가능성 판정
- **출력**: `contents/labs/battle-auto/YYYY-MM-DD-*.yaml`

### 4.3 예방 룰 생성기 (신규)
- **위치**: **Bastion** 레포로 이관 권장 (자율보안 기능)
- **지원 포맷**: Suricata rules, Wazuh custom rules, nftables, ModSecurity CRS
- **안전**: staging dry-run 필수, 사람 승인 게이트, false positive 모니터링

### 4.4 Bastion 지속 검증 (현재 유지)
- **현 실증 테스트 방식** 유지 (3,090 케이스 기준)
- 신규 자동 생성 콘텐츠는 반드시 이 검증 통과해야 배포
- 결과: pass/fail/qa_fb/exec 비율로 콘텐츠 품질 측정

### 4.5 관리자 UI (신규)
- **역할별 대시보드**:
  - **교육 운영자**: 학생 진도, 과목 pass rate, battle 결과
  - **보안 운영자**: CTI 피드, 예방 룰 적용·롤백, 자동 대응 history
  - **연구자**: Bastion 성능, 모델 비교, pass 전환율 추이
- **실시간 개입**: 생성된 콘텐츠 수동 승인/거부, 룰 긴급 롤백, 학생 세션 관찰
- **알림**: 위험 CTI 발표, 룰 false positive, 대량 qa_fb 발생

## 5. 프로젝트 분리 전략

### 5.1 현재·근미래 (사용자 계획)

**Phase 1 — CCC 모노레포 (현재)**
- `github.com/mrgrit/ccc` — 모든 기능 통합

**Phase 2 — Bastion 분리 (진행 중)**
- `github.com/mrgrit/bastion` — 자율보안시스템으로 독립
- CCC는 Bastion을 **교육 도구로 사용** (API 의존)
- Bastion은 CCC 없이도 **실무 환경에 독립 배포** 가능
- CCC `packages/bastion/` → bastion 레포 submodule 또는 pip package

### 5.2 중장기 분리 권고

**Phase 3 — CCC 내부 모듈화**
- `apps/cti-collector/` — CCC 내부 서브모듈
- `apps/battle-factory/` — Master Agent 워크플로우 별도 앱
- 각 앱 독립 테스트 + 독립 배포 가능 구조

**Phase 4 — 멀티 레포 전환 (옵션)**
| 레포 | 역할 | 배포 대상 |
|------|------|----------|
| ccc-edu | 교육 플랫폼 (학생·강의·실습·battle 엔진) | 대학·KISA/KITRI·기업 교육 |
| **ccc-bastion (= github.com/mrgrit/bastion)** | 자율보안시스템 | 실무 SOC·MSSP·CSOC |
| ccc-cti | CTI 수집·분석 | 인프라 공유 가능 |
| ccc-battle-factory | 시나리오 자동 생성 | CCC-edu의 상위 빌더 |
| ccc-shared | 공통 라이브러리 (스키마·util) | 모든 레포에서 참조 |

### 5.3 분리 판단 기준

| 기준 | 판단 |
|------|------|
| 독립 배포 필요? | Bastion ✓ (실무 현장) / CTI ~ (조건부) / Battle-factory ✗ |
| 교육 도메인 결합도 | Battle-factory는 CCC 강결합 / Bastion은 독립 |
| 의존성 고립 가능? | Bastion ✓ API 경계 명확 / Battle-factory ✗ 스키마 결합 |
| 다른 시스템에서 사용할 가능성? | Bastion·CTI는 ✓ / Battle-factory는 ✗ |

## 6. 허점·문제 · 완화 방안

### 6.1 기술적 허점

**1. 모델 호출 비용 폭증**
- 문제: battle 100개 생성 = Master Anthropic API 호출 多, CTI = SubAgent 호출 수천
- 완화: 우선순위 큐·rate limit·중복 감지(임베딩 유사도), 비용 메트릭 대시보드

**2. 자동 생성 콘텐츠 품질·안전성**
- 문제: 악성 코드 포함 battle, 학생이 외부 표적 공격 유도 가능
- 완화: Bastion 격리 환경 검증 필수, 사람 리뷰 게이트, 특정 키워드(CVE-XXXX 없는 0day 등) 차단

**3. CTI 라이선스·재배포**
- 문제: NVD 공공이지만 일부 상용 feed 재배포 금지
- 완화: 메타데이터·자체 요약만 저장, 원문 링크만 유지

**4. 폐쇄망 vs 외부 CTI 수집 충돌**
- 문제: 폐쇄망 원칙과 CTI 외부 수집이 모순
- 완화: "에어갭 동기화" — 외부 경계 collector가 승인된 CTI만 폐쇄망으로 복제, 또는 주기적 snapshot

**5. 예방 룰 자동 배포 위험**
- 문제: AI가 만든 룰이 정상 트래픽 차단 → 서비스 중단
- 완화: staging dry-run 필수, IDS 알림 모드부터 시작, 사람 승인 게이트, 롤백 원클릭

**6. Bastion 분리 후 API 호환성**
- 문제: CCC↔Bastion 버전 drift
- 완화: OpenAPI 스펙 고정, 버전 태그, 하위 호환성 정책

**7. 관측성 부족**
- 문제: 3-layer 통신 중 어느 층에서 실패했나 추적 어려움
- 완화: OpenTelemetry trace, 각 에이전트 call에 trace_id 전파, Jaeger/Tempo 대시보드

**8. 상용 AI 정책 위반 가능성**
- 문제: Anthropic Claude가 공격 시나리오 생성 거부할 수 있음
- 완화: 프롬프트 엔지니어링으로 "방어 훈련용" 컨텍스트 명시, 필요 시 on-prem 오픈모델로 대체

### 6.2 운영적 허점

**9. 학생 실습 로그 개인정보**
- 문제: 공격·방어 행동 로그에 개인 식별 정보 포함 가능
- 완화: 개인정보 스크럽 파이프라인, 교육 데이터 vs 연구 데이터 분리 저장

**10. 콘텐츠 생성 품질의 편차**
- 문제: 쉬운 CVE로 만든 battle은 너무 쉬움, 복잡 CVE는 검증 불가
- 완화: 학생 성과 피드백 루프 (풀기 쉬움/어려움 → Master 난이도 조정)

**11. 소스 다양성 의존**
- 문제: 특정 CTI 소스 장애 시 콘텐츠 생성 중단
- 완화: 복수 소스 fallback, 캐시 기반 24h 이어가기

## 7. 추가 아이디어

### 7.1 RAG 기반 콘텐츠 재활용
- 기존 생성 battle·lab을 임베딩해 중복 생성 방지
- "Apache RCE 시나리오 이미 존재 → 유사도 0.9 이상이면 기존 재사용"

### 7.2 학생 성과 피드백 루프
- 학생이 푼 battle의 난이도·소요 시간·오답 패턴 → Master에게 reporting
- 다음 세대 battle 생성 시 "학생 실력대에 맞는" 파라미터 조정

### 7.3 Red team AI 진화
- Battle의 Red 역할을 "점점 교묘해지는 AI 공격자"로 구현
- 학생 실력↑ ↔ Red team 복잡도↑ (GA/RL)

### 7.4 Cross-course 자동 매핑
- CTI 발표 → 어느 과목(C1 attack, C3 web, C19 IR 등) 관련?
- 매칭된 과목 주차에만 삽입·업데이트

### 7.5 Community contribution
- 학생·교수가 수동 작성한 battle도 CCC에 기여 가능
- Master가 자동 검수·표준화

### 7.6 리스크 점수
- 각 battle에 위험도 점수 (실제 공격으로 전환 위험)
- 높은 건 폐쇄망에서만·낮은 건 일반 훈련에 노출

### 7.7 다국어 확장
- CTI 원문은 영어 多 → SubAgent가 한글 요약
- 전체 파이프라인 영한 동시 지원으로 국제 교육 시장 진출 가능

## 8. 관점 분리 체크

| 관점 | 주 레포 | 비고 |
|------|---------|------|
| 교육 플랫폼 | CCC | 학생·과목·battle 엔진 |
| 자율보안 시스템 | **Bastion (분리 예정)** | 실무 배포, CTI → 룰 → 대응 |
| CTI 인프라 | 초기 CCC → 분리 후보 | 다른 시스템도 사용 가능 |
| Battle 자동 생성 | CCC | 교육 강결합 |
| 관리자 UI | 각 레포별 분리 | 교육 UI vs 보안 운영 UI |

**결론**: 현재 Bastion 분리 계획이 적절. CTI collector는 CCC 내부 시작 후 외부 수요 확인 후 분리 판단. Battle-factory는 CCC 내부 유지.

## 9. 우선순위 Phased Plan

| Phase | 기간 (추정) | 내용 | 책임 |
|-------|------------|------|------|
| **P0 — 현재 유지** | 진행 중 | Bastion 실증 테스트 41.6% pass 유지 | Master + Manager |
| **P1 — Bastion 분리** | 1주 | 레포 분리, API 경계 확정, submodule/pip 설정 | 사용자 + Master |
| **P2 — CTI MVP** | 1-2주 | SubAgent 수집기, 일일 다이제스트, Dashboard 카드 | SubAgent + Master |
| **P3 — Battle 자동 생성 MVP** | 2-3주 | CTI 1건 → battle YAML 1개 생성 → Bastion 검증 → pass 확인 | Master |
| **P4 — 예방 룰 생성기** | 2-3주 | Bastion 레포에서 Suricata/Wazuh 룰 생성·dry-run·배포 | Bastion 팀 |
| **P5 — 관리자 UI** | 2-3주 | 역할별 대시보드 (교육·보안·연구) | CCC 팀 + Bastion 팀 |
| **P6 — 피드백 루프·RAG** | 4주+ | 학생 성과 반영, 중복 감지 | Master |
| **P7 — 상용화·멀티레포** | 장기 | 선택적 레포 분리, 국제 다국어 | 전 조직 |

## 10. 다음 실행 액션 (사용자 승인 대기)

1. **Bastion 레포 분리 지원**: 내가 할 수 있는 것 — CCC의 `packages/bastion/`을 bastion 레포로 옮길 준비, import 경로 정리, API 스펙 문서화
2. **CTI collector P2 시작**: SubAgent 호출 POC (CVE 1건 요약)
3. **Battle-factory P3 시작**: 기존 battle YAML 분석 + 프롬프트 설계

사용자 신호 주시면 순차 착수.
