# CCC v2 Roadmap — Cyber Combat Commander 재설계

**작성일:** 2026-04-05
**목적:** CCC를 독립 운영 가능한 사이버보안 교육 시스템으로 전면 재설계

## 아키텍처 (1 Manager → N Users → 1 System Set → N SubAgents)

```
                 ┌─────────────────────┐
                 │  CCC Central (:9100) │
                 │  Web UI + API        │
                 │  그룹/유저/블록체인   │
                 │  Education/Labs/CTF  │
                 │  챗봇 (Manager AI)   │
                 └────────┬────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Student A │   │ Student B │   │ Student C │
    │ System Set│   │ System Set│   │ System Set│
    └──────┬───┘   └──────┬───┘   └──────┬───┘
           │              │              │
    ┌──────┴──────────────┴──────────────┴──────┐
    │  SubAgents per Student:                    │
    │  secu / web / siem / windows / attacker   │
    │  + Manager AI (Ollama/외부GPU)             │
    └────────────────────────────────────────────┘
```

## 마일스톤 개요

| MS | 이름 | 핵심 내용 |
|----|------|----------|
| **V1** | 그룹/역할/승급 시스템 | 그룹 CRUD, 역할 체계(Commander/Trainer/Trainee), 승급 룰 |
| **V2** | 유저 관리 + AI 피드백 | 히스토리, 학습현황, AI 분석 피드백 |
| **V3** | CCCNet 블록체인 | 독립 블록체인, 성과 점수 체계, lab/CTF/오류발견 보상 |
| **V4** | 인프라 재설계 (6대 VM) | secu/web/siem/windows/attacker/manager AI, 자동 설치 |
| **V5** | Manager AI 시스템 | Claude Code src 분석 기반, 시스템 프롬프트, 개인별 운영 |
| **V6** | CTF 자동 출제 | AI 기반 문제 생성, 과목/주차 지정, 블록체인 참가 자격 |
| **V7** | Training(Education) + Labs 통합 | 이름 변경, 그룹별 접근 권한, Labs 부분 제출 |
| **V8** | 챗봇 전체 탑재 | 모든 페이지에 AI 챗봇, 학습/사용법 질의응답 |
| **V9** | 독립 배포 패키지 | 다른 시스템과 완전 독립, 단독 운영 가능 |

---

## V1: 그룹/역할/승급 시스템

### 역할 체계

| 등급 | 역할 | 설명 |
|------|------|------|
| **Commander** | admin | 전체 관리, 모든 접근 가능 |
| **Trainer** | | |
| └ Chief Instructor | instructor | 교과목 관리, 정답 확인, 그룹 관리 |
| └ Drill Leader | drill_leader | 실습 진행, 채점, 피드백 |
| └ Instructor | instructor_basic | 교안 열람, 학생 진도 확인 |
| **Trainee** | | |
| └ Elite | trainee_elite | 모든 과목 접근, CTF 출제 가능 |
| └ Expert | trainee_expert | 심화 과목 접근 |
| └ Skilled | trainee_skilled | 기본+일부 심화 접근 |
| └ Apprentice | trainee_apprentice | 기본 과목 접근 |
| └ Rookie | trainee_rookie | 입문 과목만 접근 (기본 상태) |

### 승급 룰

| 현재 → 다음 | 조건 |
|-------------|------|
| Rookie → Apprentice | 아무 과목 1개 3주 이상 Lab 완료 + 50 블록 |
| Apprentice → Skilled | 기본 과목 2개 완료 (각 8주 이상) + 200 블록 + CTF 3문제 해결 |
| Skilled → Expert | 기본 4과목 + 심화 1과목 완료 + 500 블록 + 대전 5회 |
| Expert → Elite | 기본 8과목 + 심화 3과목 + 1000 블록 + 대전 10회 + CTF 20문제 |

### DB 변경

```sql
-- 그룹
CREATE TABLE groups (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 그룹-과목 접근 권한
CREATE TABLE group_courses (
    group_id TEXT REFERENCES groups(id),
    course_id TEXT NOT NULL,
    PRIMARY KEY(group_id, course_id)
);

-- 유저-그룹
ALTER TABLE students ADD COLUMN group_id TEXT REFERENCES groups(id);
ALTER TABLE students ADD COLUMN rank TEXT DEFAULT 'rookie';

-- 승급 이력
CREATE TABLE rank_history (
    id SERIAL PRIMARY KEY,
    student_id TEXT REFERENCES students(id),
    old_rank TEXT,
    new_rank TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## V3: CCCNet 블록체인

### 성과 점수 체계

| 활동 | 점수 | 블록 유형 |
|------|------|----------|
| Lab 1스텝 정답 | 해당 스텝 points | lab_step |
| Lab 전체 완료 | +50 보너스 | lab_complete |
| CTF 문제 해결 | 문제 points (100~500) | ctf_solve |
| 대전 참가 | 20 | battle_join |
| 대전 승리 | 50 | battle_win |
| 교안/실습 오류 발견 | 100 | bug_report |
| 교안/실습 개선 제안 채택 | 200 | improvement |
| 월간 최다 블록 | 500 | monthly_top |
| 승급 | 1000 | rank_up |

### CCCNet 독립 블록체인

- OpsClaw pow_service와 별도 — CCC 전용
- difficulty=3 (빠른 생성)
- 체인 검증: 자체 verify
- 중앙서버 동기화는 선택 (독립 운영 가능)

---

## V4: 학생 인프라 (6대 VM)

| VM | OS | 설치 소프트웨어 |
|----|----|----------------|
| **secu** | Ubuntu | nftables, suricata, sysmon, osquery, auditd, SubAgent |
| **web** | Ubuntu | sysmon, osquery, auditd, modsecurity, JuiceShop, DVWA, WebGoat, HackTheBox-like 커스텀 앱, SubAgent |
| **siem** | Ubuntu | sysmon, osquery, auditd, wazuh, sigma, opencti, 로그 수집(agent+syslog), SubAgent |
| **windows** | Windows | sysmon, osquery, 악성코드 분석(Ghidra, x64dbg, PEStudio, FLOSS), 포렌식(Autopsy, FTK Imager), SubAgent |
| **attacker** | Kali | nmap, metasploit, hydra, sqlmap, burpsuite, gobuster, impacket, bloodhound, crackmapexec, SubAgent |
| **manager** | Ubuntu | ollama, gpt-oss:120b(or 선택), bastion manager, SubAgent |

---

## V5: Manager AI

- bastion의 src/ (Claude Code 소스) 분석 기반
- 시스템 프롬프트: 교육 컨텍스트 + 학생 정보 + 인프라 상태 주입
- 기능:
  - 인프라 자동 세팅 (VM → 소프트웨어 설치)
  - 학생별 학습 분석 + 피드백
  - Lab 자동 검증 (SubAgent 연동)
  - CTF 문제 생성
  - 대전 판정
  - 시스템 상태 모니터링

---

## V7: Training + Labs 통합

- Education → **Training** 이름 변경
- Labs의 문제 = Training의 실습 (동일 콘텐츠, 중복 제거)
- Training 페이지에서 교안 읽기 + 실습 제출 통합
- Labs는 "시험 모드"로 변경 (전체가 아닌 **스텝 그룹별 부분 제출**)
  - 예: Step 1-5 (정찰) → Submit → Step 6-10 (공격) → Submit → Step 11-15 (분석) → Submit
- 그룹별 접근 권한: 카드에 "Rookie+", "Skilled+" 등 표시

---

## V8: 챗봇

- 모든 페이지 우하단에 챗봇 플로팅 버튼
- Manager AI (Ollama) 연동
- 컨텍스트: 현재 페이지, 학생 정보, 학습 이력
- 기능:
  - 사용법 안내
  - 교안 내용 질의
  - 실습 힌트
  - 학습 진도 확인
  - 오류 제보

---

## 구현 순서 (권장)

```
V1 (그룹/역할/승급) → V3 (CCCNet) → V7 (Training+Labs 통합) 
    → V4 (인프라 6대) → V2 (유저 AI 피드백) → V5 (Manager AI)
    → V6 (CTF 자동 출제) → V8 (챗봇) → V9 (독립 배포)
```
