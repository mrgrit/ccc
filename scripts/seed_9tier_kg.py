"""9-tier KG seed — 수기 작성 첫 시범

배치 1: 최상위 Mission/Vision + 도메인 5 parent + course5-soc 과목 1개 풀 트리

원칙: battle 192 미션 수기 작성과 동일. 자동 추출 X. lecture.md / course 메타에서
의도적으로 추출해 의미 있는 mission/vision/goal 트리 구성.

다음 회차에 19 과목 + 외부 표준 (KEV/CSF/ISO/GDPR) + 운영 (P# Plan/Todo) 추가.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.bastion.work_domain import (
    add_mission, add_vision, add_goal, add_strategy, add_kpi,
    add_plan, add_todo,
)
from packages.bastion.graph import get_graph


def seed_top_level():
    """최상위 Mission + Vision (CCC 단일)."""
    print("\n=== 최상위 Mission + Vision ===")
    g = get_graph()
    # 중복 방지 — 이미 존재하는지 title 검색
    existing = [n for n in g.find_nodes("Mission")
                if "사이버보안 차세대 인재 양성" in (n.get("name") or "")]
    if existing:
        top_mid = existing[0]["id"]
        print(f"  [skip] 최상위 Mission 이미 존재: {top_mid}")
    else:
        top_mid = add_mission(
            title="사이버보안 차세대 인재 양성",
            statement="사이버 컴뱃 커맨더 — 자기 인프라를 구축하고 공격·방어를 직접 수행하는 차세대 사이버보안 전문 인력 양성. 합성 corpus·외부 벤치·real-world dataset 의 3 트랙으로 검증된 학습 환경 제공.",
            owner="CCC Operations",
        )
        print(f"  ✓ 최상위 Mission: {top_mid}")

    # Vision 2 — horizon 분리
    v_2027 = add_vision(
        title="2027 K-사이버 교육 표준화",
        horizon_year=2027,
        statement="20 과목 × 15주 × 2 모드 (AI/Non-AI) 의 안정 운영 + 5 vuln-site 전 모드 hard chain + 자율 공방전 multi-team 일상 운영. paper publish + 외부 벤치 baseline 등재.",
        mission_id=top_mid,
    )
    print(f"  ✓ Vision 2027: {v_2027}")
    v_2026 = add_vision(
        title="2026 Bastion 자율 운영 기반",
        horizon_year=2026,
        statement="P5 Bastion-Bench 590 task 완성 + 6 외부 벤치 실측 + 30일 production trial + multi-step grading + KG 9-tier 운영 데이터 적재.",
        mission_id=top_mid,
    )
    print(f"  ✓ Vision 2026: {v_2026}")
    return top_mid, v_2027, v_2026


def seed_domain_parents(top_mid: str, v_2027: str):
    """도메인별 parent Mission 5개."""
    print("\n=== 도메인 5 parent Mission ===")
    g = get_graph()
    domains = [
        ("탐지·분석 도메인", "SOC L1~L3, threat hunting, SIEM engineering, forensics — 침해를 *발견* 하고 *해석* 하는 인력. 5 과목 (course5-soc, course14-soc-advanced 등) 묶음."),
        ("공격·시뮬레이션 도메인", "Pentest, web vuln, AD, cloud attack, red team — 침투 능력 보유 인력. 7 과목 (course1/3/13 + battle 등) 묶음."),
        ("사고 대응·복구 도메인", "Incident response, agent IR (course19/20), AI safety incident, Mythos-readiness — 침해 *후* 의 복구·교훈. 5 과목 묶음."),
        ("거버넌스·표준 도메인", "Compliance (ISMS-P/ISO/GDPR/SOC2), privacy engineering, zero-trust, crypto-key management — 표준·통제·법규. 4 과목 묶음."),
        ("인프라별 도메인", "Cloud/Container/Mobile/IoT/CPS/OT — 환경별 보안. 5 과목 묶음."),
    ]
    pids = []
    for title, statement in domains:
        # 중복 검사
        existing = [n for n in g.find_nodes("Mission")
                    if (n.get("name") or "") == title]
        if existing:
            mid = existing[0]["id"]
            print(f"  [skip] {title}: {mid}")
        else:
            mid = add_mission(title=title, statement=statement, owner="Course Lead")
            # parent Mission 으로 link (contains)
            g.add_edge(mid, top_mid, "derives_from")
            print(f"  ✓ {title}: {mid}")
        pids.append(mid)
    return pids


def seed_course_soc(detection_parent_mid: str, v_2026: str):
    """course5-soc — SOC L1 양성 과목 1세트 시범."""
    print("\n=== course5-soc 과목 풀 트리 ===")
    g = get_graph()

    # Mission
    title = "course5-soc — SOC L1 분석가 양성"
    existing = [n for n in g.find_nodes("Mission")
                if (n.get("name") or "") == title]
    if existing:
        course_mid = existing[0]["id"]
        print(f"  [skip] Mission: {course_mid}")
    else:
        course_mid = add_mission(
            title=title,
            statement="15주 × 2 모드 (Non-AI 수동 / AI 모드 Bastion 자율). 로그·경보 분석 → ATT&CK 매핑 → SIGMA 룰 → IR 절차. 졸업 시 SOC L1 운영 능력 + L2 진로 준비.",
            owner="course5-soc Lead",
        )
        g.add_edge(course_mid, detection_parent_mid, "derives_from")
        print(f"  ✓ Mission: {course_mid}")

    # Vision 1 — 과목별
    course_v = add_vision(
        title="course5-soc 졸업생 진로 — L1 → L3",
        horizon_year=2027,
        statement="course5-soc 졸업 → 1년 내 SOC L1 취업 / 2년 내 L2 (탐지 룰 작성) / 3년 내 L3 (incident commander).",
        mission_id=course_mid,
    )
    print(f"  ✓ Vision: {course_v}")

    # Goal 3 — 학기·주차·평가 단위
    g_pass = add_goal(
        title="2026 가을학기 lab pass rate 80%+",
        due="2026-12-31",
        vision_id=course_v,
        description="15주 lab YAML 의 자동 채점 (semantic_first_judge) 통과율. baseline R2 62.2% → 목표 80%+. R3 retest + multi_step_judge 적용 후 측정.",
    )
    g_attck = add_goal(
        title="ATT&CK technique coverage 30+",
        due="2026-12-31",
        vision_id=course_v,
        description="course5-soc 졸업생이 직접 매핑 가능한 MITRE ATT&CK technique. w06 ATT&CK 매핑 강의 + lab w5/6 상관분석/탐지룰 통합.",
    )
    g_ir = add_goal(
        title="6단계 IR 절차 종합 평가 합격",
        due="2026-12-31",
        vision_id=course_v,
        description="w14 자동화관제 + w15 종합 IR 훈련. NIST SP 800-61 (Detection/Analysis/Containment/Eradication/Recovery/Post-Incident) 6단계 학생 시연 + Bastion 검증.",
    )
    print(f"  ✓ Goal × 3: pass_rate={g_pass}, attck_cov={g_attck}, ir6={g_ir}")

    # Strategy
    s_main = add_strategy(
        title="주차 lab × retest 사이클 + Wazuh/Suricata 실습",
        goal_id=g_pass,
        approach="(1) 매 주차 lab YAML 학생 직접 수행 → semantic 채점 → 미통과 step retest. (2) Wazuh+Suricata 실 인프라 구축 + 자기 트래픽 생성 → 자기 alert 분석. (3) Precinct 6 5 anchor case_study 매주 1건 검토. (4) AI 모드 (course5-soc-ai) 병행 — Bastion 이 같은 lab 자율 수행 → 학생이 채점관 역할.",
    )
    print(f"  ✓ Strategy: {s_main}")

    # KPI 3
    k_pass = add_kpi(
        name="course5-soc lab pass rate",
        target=80.0,
        unit="%",
        measures="weekly retest pass / total step. semantic_first_judge 결과 기반.",
        goal_id=g_pass,
        strategy_id=s_main,
    )
    k_triage = add_kpi(
        name="alert triage time (avg)",
        target=15.0,
        unit="min",
        measures="학생 1건 alert 받아 분류 (FP/TP/요조사) 까지 평균 시간. w05 경보 분석 lab 측정.",
        goal_id=g_pass,
    )
    k_ir = add_kpi(
        name="6단계 IR 완성도",
        target=90.0,
        unit="%",
        measures="w15 종합 IR lab 의 step 별 통과 평균 (6단계 모두 1+ step 통과).",
        goal_id=g_ir,
    )
    print(f"  ✓ KPI × 3: pass={k_pass}, triage={k_triage}, ir6={k_ir}")

    # Plan + Todo (운영 측면 — 2026-Q2 학기 단위)
    plan_q2 = add_plan(
        title="2026-Q2 course5-soc 운영",
        period="2026-Q2",
        owner="course5-soc Lead",
        strategy_id=s_main,
        goal_id=g_pass,
        description="15주 강의 + 매주 lab 채점 + 월 1회 ATT&CK 매핑 평가 + 분기 종합 IR 시나리오.",
    )
    todo_w15 = add_todo(
        title="w15 종합 IR 시나리오 자동 채점 검증",
        due="2026-06-30",
        plan_id=plan_q2,
        assignee="course5-soc Lead + Bastion",
        description="multi_step_judge 가 6단계 IR 모두 정확히 채점하는지 5 학생 응답으로 검증. A vs C 정확도 비교.",
    )
    print(f"  ✓ Plan: {plan_q2}, Todo: {todo_w15}")

    return course_mid


def seed_course_secops(detection_parent_mid: str):
    """course2-security-ops — 보안 솔루션 운영 인력 (방어 인프라 구축)."""
    print("\n=== course2-security-ops 과목 풀 트리 ===")
    g = get_graph()
    title = "course2-security-ops — 보안 솔루션 운영 인력"
    existing = [n for n in g.find_nodes("Mission") if (n.get("name") or "") == title]
    if existing:
        course_mid = existing[0]["id"]
        print(f"  [skip] Mission: {course_mid}")
        return course_mid
    course_mid = add_mission(
        title=title,
        statement="15주 — nftables(2-3주) → Suricata(4-6주) → ModSecurity WAF(7주) → Wazuh SIEM(9-11주) → OpenCTI(12-13주) → 통합(14-15주). 졸업 시 보안 솔루션 *직접 구축·운영* 가능. SOC 분석가 (course5) 의 *인프라 측 짝* 과목.",
        owner="course2-secops Lead",
    )
    g.add_edge(course_mid, detection_parent_mid, "derives_from")
    course_v = add_vision(
        title="course2-secops 졸업생 진로 — Security Engineer / DevSecOps",
        horizon_year=2027,
        statement="졸업 → SOC L1 또는 Security Engineer 입사 → 1년 내 솔루션 1개 owner / 2년 내 통합 아키텍처 설계 / 3년 내 DevSecOps lead.",
        mission_id=course_mid,
    )
    g_install = add_goal(
        title="5 솔루션 (nftables/Suricata/WAF/Wazuh/OpenCTI) 모두 학생 직접 설치+검증",
        due="2026-12-31",
        vision_id=course_v,
        description="lab w2~w13 의 자동 채점 통과율 80%+. semantic_first_judge 가 systemctl is-active / 설정 파일 / 룰 갯수 검증.",
    )
    g_integ = add_goal(
        title="통합 아키텍처 (방화벽→IPS→SIEM→CTI) 동작 검증",
        due="2026-12-31",
        vision_id=course_v,
        description="w14 lab — Suricata alert → Wazuh ingest → OpenCTI IoC 매칭 → Bastion alert. 종단 종단 트래픽 흐름이 검증되어야 종합점수 부여.",
    )
    s_main = add_strategy(
        title="솔루션별 1주차 설치 → 2-3주차 룰/정책 → 통합 1주차",
        goal_id=g_install,
        approach="(1) 각 솔루션마다 install lab + ops lab 분리. (2) Wazuh+Suricata 같은 인프라 위 동시 운영. (3) OpenCTI 는 Precinct 6 IoC 4,363 import 로 진짜 데이터. (4) AI 모드 (course2-secops-ai) 는 Bastion 이 같은 lab 자동 수행 → 학생이 검증.",
    )
    k_solv = add_kpi(name="course2 솔루션 설치 lab pass rate", target=85.0, unit="%",
                     measures="weekly install/ops lab pass / total. 5 솔루션 평균.",
                     goal_id=g_install, strategy_id=s_main)
    k_integ = add_kpi(name="통합 아키텍처 종단 검증", target=90.0, unit="%",
                      measures="w14 lab 의 트래픽 흐름 단계별 통과 (방화벽→IPS→SIEM→CTI 5 step).",
                      goal_id=g_integ)
    k_cti = add_kpi(name="OpenCTI IoC import 활용도", target=4000.0, unit="count",
                    measures="학생 환경에 import 한 Precinct 6 IoC anchor 수. 평균.",
                    goal_id=g_integ, strategy_id=s_main)
    plan = add_plan(title="2026-Q2 course2-secops 운영", period="2026-Q2",
                    owner="course2-secops Lead", strategy_id=s_main, goal_id=g_install,
                    description="15주 강의 + 매주 lab + 분기말 통합 검증.")
    add_todo(title="w13 OpenCTI lab 의 Precinct 6 IoC import smoke 테스트",
             due="2026-06-15", plan_id=plan, assignee="course2-secops Lead",
             description="dist/precinct6-seed-vYYYY.MM/ tar.gz 학생 환경에 import → 4,363 anchor 적재 확인.")
    print(f"  ✓ secops Mission: {course_mid}")
    print(f"  ✓ {course_v} / Goal × 2 / Strategy / KPI × 3 / Plan / Todo")
    return course_mid


def seed_course_soc_adv(detection_parent_mid: str):
    """course14-soc-advanced — SOC L2/L3 심화."""
    print("\n=== course14-soc-advanced 과목 풀 트리 ===")
    g = get_graph()
    title = "course14-soc-advanced — SOC L2/L3 심화 (탐지 엔지니어링)"
    existing = [n for n in g.find_nodes("Mission") if (n.get("name") or "") == title]
    if existing:
        return existing[0]["id"]
    course_mid = add_mission(
        title=title,
        statement="course5 후속 — SIEM 고급 상관분석, SIGMA/YARA, 위협 헌팅, 메모리·네트워크 포렌식, SOAR. 졸업 시 detection engineer / threat hunter 역할 가능.",
        owner="course14-soc-adv Lead",
    )
    g.add_edge(course_mid, detection_parent_mid, "derives_from")
    course_v = add_vision(
        title="course14 졸업생 — Detection Engineer / Threat Hunter / IR Lead",
        horizon_year=2027,
        statement="졸업 → SOC L2 자격 / 1년 내 자체 SIGMA 룰 30+ 작성 / 2년 내 incident commander.",
        mission_id=course_mid,
    )
    g_hunt = add_goal(
        title="가설 기반 위협 헌팅 1주 내 5건 수행",
        due="2026-12-31",
        vision_id=course_v,
        description="w06 위협 헌팅 lab + Precinct 6 의 5 anchor chain (SMB/AS-REP/DNS/HTA/cron) 매핑 실습. 학생이 30일 윈도우 헌팅 시뮬레이션.",
    )
    g_forensic = add_goal(
        title="네트워크/메모리 포렌식 도구 (Volatility3/Wireshark) 자율 활용",
        due="2026-12-31",
        vision_id=course_v,
        description="w07 네트워크 포렌식 (DNS 터널링 PCAP) + w08 메모리 포렌식 (cron fileless) lab 자동 채점 통과.",
    )
    g_soar = add_goal(
        title="SOAR 플레이북 3건 자동 실행",
        due="2026-12-31",
        vision_id=course_v,
        description="w10 SOAR lab — 인시던트 분류 → 자동 격리 → 알림 → 보고서. 3 시나리오 모두 자동 실행 통과.",
    )
    s_main = add_strategy(
        title="Precinct 6 chain 분석 + 도구 실측 + SOAR 자동화",
        goal_id=g_hunt,
        approach="(1) 매주 Precinct 6 의 1 anchor 분해 학습 (5건 anchor 가 본 과정의 *교과서 사례*). (2) Volatility3/Wireshark/Sigma/Yara 도구 매주 1개 깊이. (3) Wazuh Active Response 로 자동화 → SOAR. (4) AI 모드는 Bastion 이 같은 헌팅 자율 수행.",
    )
    k_hunt = add_kpi(name="threat hunting query 작성 정확도", target=80.0, unit="%",
                     measures="학생 작성 SIGMA/YARA 룰 → 양성 alert / 전체. 주당 5+ 룰.",
                     goal_id=g_hunt, strategy_id=s_main)
    k_forensic = add_kpi(name="포렌식 도구 활용도", target=85.0, unit="%",
                         measures="w07/w08 lab 의 Volatility3/Wireshark step 통과율.",
                         goal_id=g_forensic)
    k_soar = add_kpi(name="SOAR 플레이북 자동화 성공률", target=90.0, unit="%",
                     measures="w10 lab 의 3 플레이북 자동 실행 단계별 통과.",
                     goal_id=g_soar)
    plan = add_plan(title="2026-Q3 course14-soc-adv 운영", period="2026-Q3",
                    owner="course14-soc-adv Lead", strategy_id=s_main, goal_id=g_hunt,
                    description="course5 후속. 가을학기 진행 + Precinct 6 anchor 5건 매주 1건 case study.")
    add_todo(title="Precinct 6 anchor 5건의 chain 헌팅 가이드 문서 작성",
             due="2026-08-31", plan_id=plan, assignee="course14-soc-adv Lead",
             description="w06 헌팅 lab 의 보조 자료 — 5 anchor 의 시간선/공통 IoC/매핑 해설. SIGMA correlation 룰 예시 5건.")
    print(f"  ✓ soc-adv Mission: {course_mid}")
    print(f"  ✓ {course_v} / Goal × 3 / Strategy / KPI × 3 / Plan / Todo")
    return course_mid


def seed_course_attack(attack_parent_mid: str):
    """course1-attack — OWASP/PTES 침투 기초."""
    g = get_graph()
    title = "course1-attack — 모의해킹 기초 (OWASP + PTES)"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")):
        return
    print("\n=== course1-attack 과목 풀 트리 ===")
    course_mid = add_mission(
        title=title,
        statement="15주 — OWASP Top 10 + 정찰/스캔/익스플로잇/PrivEsc/지속성/측면이동/유출/은닉. 졸업 시 PTES 절차 자율 수행 + 침투 보고서 작성. 진로: junior penetration tester.",
        owner="course1-attack Lead",
    )
    g.add_edge(course_mid, attack_parent_mid, "derives_from")
    course_v = add_vision(
        title="course1 졸업 → Junior Pentester / Bug Bounty Hunter",
        horizon_year=2027,
        statement="졸업 → 모의해킹 회사 입사 (junior) / 1년 내 OSCP 자격 / 2년 내 보고서·사후관리 lead.",
        mission_id=course_mid,
    )
    g_pass = add_goal(title="OWASP Top 10 자체 PoC 8/10 작성",
                     due="2026-12-31", vision_id=course_v,
                     description="A03 SQLi, A04 SSRF, A05 파일업로드, A06 인증, A07 XSS 등 학생 본인 PoC.")
    g_chain = add_goal(title="3단계 chain 침투 시나리오 1건 자율 수행",
                      due="2026-12-31", vision_id=course_v,
                      description="w15 종합 lab — 정찰 → 익스플로잇 → PrivEsc + 보고서. Precinct 6 의 5 anchor chain 패턴 모방.")
    s_main = add_strategy(
        title="OWASP 이론 강의 + 5 vuln-site 실습 + Bastion AI 모드 비교",
        goal_id=g_pass,
        approach="(1) lecture (OWASP 학습 순서) + lab (PTES 킬체인 순서) → D-B 매핑으로 의미 매칭. (2) JuiceShop/DVWA 외 5 신규 vuln-site (NeoBank/GovPortal/MediForum/AdminConsole/AICompanion) 실습. (3) AI 모드는 Bastion 이 같은 lab 자율 → 학생이 채점관.",
    )
    add_kpi(name="course1-attack lab pass rate", target=80.0, unit="%",
            measures="weekly lab pass / total. 5 vuln-site 통과 평균.",
            goal_id=g_pass, strategy_id=s_main)
    add_kpi(name="vuln-site hard chain 통과 (5/5)", target=60.0, unit="%",
            measures="NeoBank/GovPortal/MediForum/AdminConsole/AICompanion 의 hard chain 평균 통과율.",
            goal_id=g_chain)
    plan = add_plan(title="2026-Q2 course1-attack 운영", period="2026-Q2",
                    owner="course1-attack Lead", strategy_id=s_main, goal_id=g_pass)
    add_todo(title="신규 vuln-site 5종 학생 환경 배포 검증",
             due="2026-05-31", plan_id=plan, assignee="course1-attack Lead",
             description="up.sh 자동 배포 + 10/10 PoC smoke 통과 확인.")
    print(f"  ✓ course1-attack Mission: {course_mid}")


def seed_course_web_vuln(attack_parent_mid: str):
    """course3-web-vuln — OWASP 웹 취약점 점검 전문."""
    g = get_graph()
    title = "course3-web-vuln — 웹 취약점 점검 전문"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")):
        return
    print("\n=== course3-web-vuln 과목 풀 트리 ===")
    course_mid = add_mission(
        title=title,
        statement="15주 — 웹 점검 방법론 (개론→환경→정찰→인증→입력검증→접근제어→암호화→에러→API→자동화→보고). 졸업 시 OWASP ZAP/Burp 자율 활용 + 취약점 점검 보고서.",
        owner="course3-web-vuln Lead",
    )
    g.add_edge(course_mid, attack_parent_mid, "derives_from")
    course_v = add_vision(
        title="course3 졸업 → Web App Pentester / 보안 컨설턴트",
        horizon_year=2027,
        statement="졸업 → 웹 점검 전담 / 1년 내 ISMS-P 보안 점검 컨설팅 / 2년 내 자체 점검 도구 개발.",
        mission_id=course_mid,
    )
    g_owasp = add_goal(title="OWASP Top 10 모든 항목 직접 PoC",
                       due="2026-12-31", vision_id=course_v,
                       description="lab w2 SQLi, w3 XSS, w4 CSRF, w5 파일업로드, w7 SSRF, w8 XXE, w9 디시리얼, w10 cmdInject, w12 API. 10/10 자체 작성.")
    g_report = add_goal(title="웹 점검 보고서 표준 형식 작성 (10건)",
                        due="2026-12-31", vision_id=course_v,
                        description="w14 보고서 작성법 + w15 종합 점검. JuiceShop + 5 신규 vuln-site 각 1건.")
    s_main = add_strategy(
        title="lecture (방법론 순서) × lab (OWASP 순서) cross-course 매핑",
        goal_id=g_owasp,
        approach="course1-attack 의 정찰/인증 lab + course3-web-vuln 의 SQLi/XSS lab cross-course 활용. D-B 매핑 yaml 활용.",
    )
    add_kpi(name="course3-web-vuln lab pass rate", target=85.0, unit="%",
            goal_id=g_owasp, strategy_id=s_main)
    add_kpi(name="자체 점검 보고서 품질 (peer review)", target=80.0, unit="%",
            measures="동료 5 학생 평가 + 강사 평가 평균. 명확성/포괄성/재현성 3축.",
            goal_id=g_report)
    plan = add_plan(title="2026-Q2 course3-web-vuln 운영", period="2026-Q2",
                    owner="course3-web-vuln Lead", strategy_id=s_main, goal_id=g_owasp)
    add_todo(title="JuiceShop hard mode + 5 신규 사이트 hard chain 학습 가이드",
             due="2026-05-15", plan_id=plan, assignee="course3-web-vuln Lead")
    print(f"  ✓ course3-web-vuln Mission: {course_mid}")


def seed_course_attack_adv(attack_parent_mid: str):
    """course13-attack-advanced — APT 킬체인 심화 + AD/Cloud."""
    g = get_graph()
    title = "course13-attack-advanced — APT 킬체인 심화"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")):
        return
    print("\n=== course13-attack-advanced 과목 풀 트리 ===")
    course_mid = add_mission(
        title=title,
        statement="course1 후속 — APT 7단계 킬체인 + OSINT/우회/AD/Cloud/공급망/안티포렌식. 졸업 시 자체 C2 운영 + AD 도메인 장악 + 클라우드 IAM 악용. 진로: senior pentester / red teamer.",
        owner="course13-attack-adv Lead",
    )
    g.add_edge(course_mid, attack_parent_mid, "derives_from")
    course_v = add_vision(
        title="course13 졸업 → Senior Pentester / Red Team Operator",
        horizon_year=2027,
        statement="졸업 → red team 입사 / 1년 내 자체 C2 인프라 / 2년 내 OSCE 자격 / 3년 내 red team lead.",
        mission_id=course_mid,
    )
    g_chain = add_goal(title="13주 chain 자율 수행 (정찰 → 보고서)",
                      due="2026-12-31", vision_id=course_v,
                      description="w14 종합 모의해킹 lab. PTES 전 과정. Precinct 6 의 5 anchor chain (피싱→AS-REP→SMB→cron→DNS) 재현 능력.")
    g_ad = add_goal(title="AD 도메인 1개 장악 (BloodHound + DCSync + Golden Ticket)",
                   due="2026-12-31", vision_id=course_v,
                   description="w09 AD 공격 lab. 시뮬레이션 도메인에서 학생이 직접 Domain Admin 획득.")
    g_cloud = add_goal(title="AWS IAM 악용 1건 PoC",
                      due="2026-12-31", vision_id=course_v,
                      description="w13 클라우드 공격 lab. EC2 metadata → role → S3 탈취 등.")
    s_main = add_strategy(
        title="Precinct 6 5 anchor chain 을 교과서로 활용",
        goal_id=g_chain,
        approach="(1) anchor 5건 (SMB/AS-REP/DNS/HTA/cron) 이 attack-adv 의 *바로 그 주제*. 학생이 동일 chain 재현 + 자기 변형. (2) AD attack 은 자체 시뮬레이션 도메인 (Samba4 + Kerberos). (3) 클라우드는 LocalStack/MinIO mock + 진짜 AWS free tier 옵션.",
    )
    add_kpi(name="course13 chain 통과율", target=70.0, unit="%",
            measures="w14 lab 의 7단계 통과율 평균.",
            goal_id=g_chain, strategy_id=s_main)
    add_kpi(name="AD 도메인 장악 시간", target=30.0, unit="min",
            measures="시뮬레이션 도메인 진입부터 DA 획득까지 평균 시간 (학생 첫 시도).",
            goal_id=g_ad)
    add_kpi(name="cloud IAM PoC 자동화 비율", target=60.0, unit="%",
            measures="lab 학생 응답 중 boto3/aws-cli 자동 스크립트 활용 비율.",
            goal_id=g_cloud)
    plan = add_plan(title="2026-Q3 course13-attack-adv 운영", period="2026-Q3",
                    owner="course13-attack-adv Lead", strategy_id=s_main, goal_id=g_chain)
    add_todo(title="AD 시뮬레이션 환경 (Samba4 + 4 호스트) 자동 배포 스크립트",
             due="2026-08-15", plan_id=plan, assignee="course13-attack-adv Lead",
             description="course13 w09 lab 실습 환경. ansible playbook 또는 docker-compose.")
    add_todo(title="Precinct 6 anchor 5건의 attack-adv 챌린지 README 작성",
             due="2026-08-31", plan_id=plan, assignee="course13-attack-adv Lead")
    print(f"  ✓ course13-attack-adv Mission: {course_mid}")


def seed_course_agent_ir(ir_parent_mid: str):
    """course19-agent-incident-response — AI Agent 공격 IR 기초."""
    g = get_graph()
    title = "course19-agent-ir — AI Agent 공격 IR 기초"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")):
        return
    print("\n=== course19-agent-ir 과목 풀 트리 ===")
    course_mid = add_mission(
        title=title,
        statement="2026 신설. Claude Code 급 코딩 에이전트가 *공격자* 로 투입되는 실세계 위협 대응. 15주: AI Vulnerability Storm → 자동 익스플로잇 → 측면이동 (기계 속도) → 회피·다형성 → 규모화 → 탐지·대응 → Purple Round 1·2 (Coach + Experience 자동 승격) → 기말 Mythos-readiness.",
        owner="course19-agent-ir Lead",
    )
    g.add_edge(course_mid, ir_parent_mid, "derives_from")
    course_v = add_vision(
        title="course19 졸업 → AI Agent IR Specialist (신생 직군)",
        horizon_year=2027,
        statement="졸업 → AI Agent 침해 사고 대응 전담 (전세계 신생 직군) / 1년 내 Purple coach 역할 / 2년 내 조직 Mythos-readiness 운영.",
        mission_id=course_mid,
    )
    g_speed = add_goal(title="기계 속도 측면이동 1건 직접 재현 + 탐지",
                      due="2026-12-31", vision_id=course_v,
                      description="w05 lab — Precinct 6 의 SMB 측면이동 (28분) 자동화 도구로 5 호스트. 학생이 동시에 탐지 룰 작성.")
    g_purple = add_goal(title="Purple Round 1+2 모두 통과",
                       due="2026-12-31", vision_id=course_v,
                       description="w11 Claude Code 가 Bastion 코치 + w12 Experience → Playbook 자동 승격. 2 round 모두 Bastion 의 능력 향상 측정.")
    s_main = add_strategy(
        title="Precinct 6 5 anchor 가 본 과정의 *교과서 사례*",
        goal_id=g_speed,
        approach="(1) 매 주차 5 anchor 중 1건 분해 학습. (2) 학생이 직접 Claude Code 같은 에이전트로 chain 재현 → 탐지 격차 측정. (3) Bastion Purple coach 모드로 학생 탐지 룰 강화. (4) 기말 Mythos-readiness — 30/90/365 작전 계획 수립.",
    )
    add_kpi(name="course19 lab pass rate", target=75.0, unit="%",
            measures="weekly lab pass / total. 신생 분야라 baseline 낮게 시작.",
            goal_id=g_speed, strategy_id=s_main)
    add_kpi(name="기계 속도 측면이동 탐지 SLA", target=15.0, unit="min",
            measures="학생이 자동 측면이동 시작부터 Wazuh+Bastion 알림까지 평균.",
            goal_id=g_speed)
    add_kpi(name="Purple Round 능력 향상도", target=30.0, unit="%",
            measures="Round 1 전후 Bastion 의 attack-* 과목 pass rate 증가.",
            goal_id=g_purple)
    plan = add_plan(title="2026-Q3 course19-agent-ir 운영", period="2026-Q3",
                    owner="course19-agent-ir Lead", strategy_id=s_main, goal_id=g_speed,
                    description="신생 분야라 R3 retest 의 attack-ai/agent-ir 과목 pass rate 와 직접 연동.")
    add_todo(title="Mythos-readiness 30/90/365 템플릿 작성",
             due="2026-09-30", plan_id=plan, assignee="course19-agent-ir Lead",
             description="기말 보고서 형식. 학생이 자기 조직의 AI 위협 대응 계획 수립.")
    print(f"  ✓ course19-agent-ir Mission: {course_mid}")


def seed_course_agent_ir_adv(ir_parent_mid: str):
    """course20-agent-ir-advanced — 15가지 사례별 IR."""
    g = get_graph()
    title = "course20-agent-ir-adv — AI Agent 공격 침해대응 심화"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")):
        return
    print("\n=== course20-agent-ir-adv 과목 풀 트리 ===")
    course_mid = add_mission(
        title=title,
        statement="course19 후속. 15가지 서로 다른 에이전트 공격 사례 각각 6단계 IR (공급망/Indirect Injection/AD Kerberoast/Cloud IAM/0-day/N-day Log4Shell/Multi-stage 피싱/K8s 탈출/Fileless/DNS Exfil/AI 모델 공격/Deepfake/Insider+Agent/CI/CD/장기 APT). Human vs Agent 대응 비교.",
        owner="course20-agent-ir-adv Lead",
    )
    g.add_edge(course_mid, ir_parent_mid, "derives_from")
    course_v = add_vision(
        title="course20 졸업 → IR Lead / Mythos-readiness 책임자",
        horizon_year=2027,
        statement="졸업 → 조직 IR 책임자 / 1년 내 15가지 시나리오 자체 playbook / 2년 내 Mythos-readiness 표준 정립.",
        mission_id=course_mid,
    )
    g_15 = add_goal(title="15 사례 모두 6단계 IR 자율 수행",
                   due="2026-12-31", vision_id=course_v,
                   description="각 주차 lab 의 6단계 (Detection/Analysis/Containment/Eradication/Recovery/Post-Incident) 통과율 80%+.")
    g_human_agent = add_goal(title="Human vs Agent 대응 시간 격차 측정 + 보고서",
                            due="2026-12-31", vision_id=course_v,
                            description="15 시나리오 각각에서 사람만 대응 vs Agent 보조 대응 시간 측정. paper §7 데이터.")
    s_main = add_strategy(
        title="Precinct 6 anchor 5건이 곧 본 과정 사례 중 5/15",
        goal_id=g_15,
        approach="(1) anchor 5건이 직접 매핑되는 주차 (w03 AS-REP, w07 HTA 피싱, w09 Fileless cron, w10 DNS Exfil, w15 5건 chain) 가 5/15 주차. 진짜 사례 학습. (2) 다른 10 사례는 시뮬레이션. (3) Human vs Agent 비교는 stopwatch + Bastion 자동 측정.",
    )
    add_kpi(name="course20 15 사례 IR 통과율", target=80.0, unit="%",
            goal_id=g_15, strategy_id=s_main)
    add_kpi(name="Agent 보조 대응 시간 단축", target=50.0, unit="%",
            measures="Human only vs Human+Agent 대응 시간 비교 (15 시나리오 평균).",
            goal_id=g_human_agent)
    add_kpi(name="조직별 Mythos-readiness 점수", target=70.0, unit="point",
            measures="졸업생 자기 조직 readiness 자가평가 (10 항목 × 10점).",
            goal_id=g_human_agent)
    plan = add_plan(title="2026-Q4 course20-agent-ir-adv 운영", period="2026-Q4",
                    owner="course20-agent-ir-adv Lead", strategy_id=s_main, goal_id=g_15,
                    description="course19 직후. Q4 학기.")
    add_todo(title="anchor 매핑된 5 주차 (w03/w07/w09/w10/w15) 의 case_study 가 KG 에 정확히 적재되는지 검증",
             due="2026-10-15", plan_id=plan, assignee="course20-agent-ir-adv Lead",
             description="curriculum mapping yaml 의 case_study 와 KG history_anchors 의 anchor_id 매칭 검증.")
    print(f"  ✓ course20-agent-ir-adv Mission: {course_mid}")


def seed_course_compliance(gov_parent_mid: str):
    g = get_graph()
    title = "course4-compliance — 정보보안 컴플라이언스"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")): return
    print("\n=== course4-compliance ===")
    course_mid = add_mission(
        title=title,
        statement="ISMS-P / ISO 27001 / GDPR / NIST CSF / SOC2 / HIPAA / PCI-DSS / CSAP. 졸업 시 보안 점검 컨설팅 + 인증 심사 대응 가능. 진로: compliance officer / 보안 컨설턴트.",
        owner="course4-compliance Lead",
    )
    g.add_edge(course_mid, gov_parent_mid, "derives_from")
    course_v = add_vision(title="course4 졸업 → Compliance Officer / 보안 컨설턴트",
                         horizon_year=2027,
                         statement="졸업 → ISMS-P 심사원 보조 / 1년 내 ISO 27001 LA / 2년 내 multi-framework 컨설팅.",
                         mission_id=course_mid)
    g_isms = add_goal(title="ISMS-P 점검 8 통제 + ISO 27001 통제 항목 90% 자체 점검",
                     due="2026-12-31", vision_id=course_v,
                     description="lab w3 ISMS-P + w4 ISO 27001 + w9 ISMS 기술 통합.")
    g_multi = add_goal(title="multi-framework 매핑 (ISO ↔ NIST ↔ ISMS-P) 표 작성",
                      due="2026-12-31", vision_id=course_v,
                      description="동일 통제 항목을 3 표준 ID 로 매핑. 컨설팅 시 즉시 활용.")
    s_main = add_strategy(
        title="표준별 lab + Precinct 6 incident → 다중 표준 해석",
        goal_id=g_isms,
        approach="(1) 표준별 1 lab. (2) 1 incident (Data Theft T1041) 가 SOC 2 / HIPAA / PCI / ISO 모두 위반인 사례 학습. (3) Precinct 6 의 Compliance Concept 11종 (cmmc/csf/iso/nist) KG 노드 활용.",
    )
    add_kpi(name="course4 lab pass rate", target=85.0, unit="%",
            goal_id=g_isms, strategy_id=s_main)
    add_kpi(name="multi-framework 매핑 정확도", target=80.0, unit="%",
            measures="강사 평가 — 동일 통제 ID 매핑 정확률.",
            goal_id=g_multi)
    plan = add_plan(title="2026-Q2 course4-compliance 운영", period="2026-Q2",
                    owner="course4-compliance Lead", strategy_id=s_main, goal_id=g_isms)
    add_todo(title="Precinct 6 Compliance Concept 11종 KG 노드 검증",
             due="2026-05-15", plan_id=plan, assignee="course4-compliance Lead")
    print(f"  ✓ {course_mid}")


def seed_course_ai_safety(gov_parent_mid: str):
    g = get_graph()
    title = "course8-ai-safety — AI Safety + Red Teaming 기초"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")): return
    print("\n=== course8-ai-safety ===")
    course_mid = add_mission(
        title=title,
        statement="LLM 탈옥/프롬프트 인젝션/가드레일/적대적 입력/RAG 보안/AI 윤리. 졸업 시 LLM red teaming 기초 + AI safety eval 자율 수행.",
        owner="course8-ai-safety Lead",
    )
    g.add_edge(course_mid, gov_parent_mid, "derives_from")
    course_v = add_vision(title="course8 졸업 → AI Safety Engineer",
                         horizon_year=2027,
                         statement="졸업 → LLM 가드레일 설계 / 1년 내 자체 jailbreak suite / 2년 내 AI Safety lead.",
                         mission_id=course_mid)
    g_jb = add_goal(title="LLM jailbreak 5종 PoC + 방어 룰 작성",
                   due="2026-12-31", vision_id=course_v)
    g_eval = add_goal(title="AI safety 평가 프레임워크 자체 1건 구축",
                     due="2026-12-31", vision_id=course_v)
    s_main = add_strategy(title="공격→방어→평가 사이클 + ai-safety-adv 연계",
                         goal_id=g_jb,
                         approach="lab 매주 공격→방어→평가. course15 (advanced) 에서 심화.")
    add_kpi(name="course8 lab pass rate", target=75.0, unit="%", goal_id=g_jb, strategy_id=s_main)
    add_kpi(name="자체 jailbreak suite 효과율", target=40.0, unit="%",
            measures="학생 작성 jailbreak 가 ollama gpt-oss 우회 성공 비율.",
            goal_id=g_jb)
    plan = add_plan(title="2026-Q3 course8-ai-safety 운영", period="2026-Q3",
                    owner="course8-ai-safety Lead", strategy_id=s_main, goal_id=g_jb)
    add_todo(title="HarmBench 100 prompt subset 학습용 정리", due="2026-08-31",
             plan_id=plan, assignee="course8-ai-safety Lead")
    print(f"  ✓ {course_mid}")


def seed_course_ai_safety_adv(gov_parent_mid: str):
    g = get_graph()
    title = "course15-ai-safety-adv — AI Safety 심화"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")): return
    print("\n=== course15-ai-safety-adv ===")
    course_mid = add_mission(
        title=title,
        statement="course8 후속 — LLM Red Teaming 심화/가드레일 우회/RAG 보안/모델 탈취/데이터 중독/멀티모달 공격/AI 거버넌스. 졸업 시 AI Red Team operator + AI 거버넌스 자문.",
        owner="course15-ai-safety-adv Lead",
    )
    g.add_edge(course_mid, gov_parent_mid, "derives_from")
    course_v = add_vision(title="course15 졸업 → AI Red Team Operator / AI 거버넌스 컨설턴트",
                         horizon_year=2027,
                         statement="졸업 → AI Red Team 운영 / 1년 내 EU AI Act / Korea AI 기본법 자문 능력.",
                         mission_id=course_mid)
    g_redteam = add_goal(title="AI Red Team 자체 캠페인 1건 운영 + 보고서",
                        due="2026-12-31", vision_id=course_v)
    g_ext = add_goal(title="모델 추출 + 백도어 탐지 PoC",
                    due="2026-12-31", vision_id=course_v)
    s_main = add_strategy(title="HarmBench/CyberSecEval 외부 벤치 학습 + 자체 red team 캠페인",
                         goal_id=g_redteam,
                         approach="P6 외부 벤치 (HarmBench/CyberSecEval) 학생 학습 자료. P5 ai-safety h001~h004 task 도 참조.")
    add_kpi(name="course15 lab pass rate", target=70.0, unit="%",
            goal_id=g_redteam, strategy_id=s_main)
    add_kpi(name="HarmBench cyber subset 학생 통과율", target=60.0, unit="%",
            measures="100 task 중 학생 자체 jailbreak/방어 통과 비율.",
            goal_id=g_redteam)
    plan = add_plan(title="2026-Q4 course15-ai-safety-adv 운영", period="2026-Q4",
                    owner="course15-ai-safety-adv Lead", strategy_id=s_main, goal_id=g_redteam)
    add_todo(title="EU AI Act + Korea AI 기본법 강의 자료 업데이트", due="2026-11-30",
             plan_id=plan, assignee="course15-ai-safety-adv Lead")
    print(f"  ✓ {course_mid}")


def seed_course_cloud_container(infra_parent_mid: str):
    g = get_graph()
    title = "course6-cloud-container — 클라우드/컨테이너 보안"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")): return
    print("\n=== course6-cloud-container ===")
    course_mid = add_mission(
        title=title,
        statement="Docker/K8s/AWS/IaC/CI-CD/서버리스. 졸업 시 컨테이너 보안 + 클라우드 IAM/Network 자율 설계. 진로: cloud security engineer / DevSecOps.",
        owner="course6 Lead",
    )
    g.add_edge(course_mid, infra_parent_mid, "derives_from")
    course_v = add_vision(title="course6 졸업 → Cloud Security Engineer / DevSecOps",
                         horizon_year=2027, statement="졸업 → CKS 자격 / 1년 내 EKS 운영 / 2년 내 클라우드 보안 lead.",
                         mission_id=course_mid)
    g_docker = add_goal(title="Docker 보안 5축 (image/runtime/network/storage/compose) 자율 설정",
                       due="2026-12-31", vision_id=course_v)
    g_k8s = add_goal(title="K8s PSA restricted + RBAC + NetworkPolicy 직접 적용",
                    due="2026-12-31", vision_id=course_v,
                    description="P5 cloud-security-h001/h002 task 와 동일 학습 대상.")
    g_iac = add_goal(title="IaC 보안 (Terraform/Ansible) PoC", due="2026-12-31",
                    vision_id=course_v)
    s_main = add_strategy(title="Docker → K8s 시뮬레이션 → IaC → CI/CD 흐름",
                         goal_id=g_docker,
                         approach="lab w11~w12 K8s 보안 + P5 cloud-security task 5건 학습.")
    add_kpi(name="course6 lab pass rate", target=80.0, unit="%", goal_id=g_docker, strategy_id=s_main)
    add_kpi(name="K8s Pod escape PoC + 차단 1건", target=100.0, unit="%",
            measures="P5 cloud-security h002 task 학생 직접 수행.", goal_id=g_k8s)
    add_kpi(name="IaC scan tool 활용도", target=70.0, unit="%",
            measures="Checkov/tfsec/kubeaudit 활용 비율.", goal_id=g_iac)
    plan = add_plan(title="2026-Q3 course6-cloud-container 운영", period="2026-Q3",
                    owner="course6 Lead", strategy_id=s_main, goal_id=g_docker)
    add_todo(title="K8s 시뮬레이션 환경 (kind 또는 k3s) 학생 환경 자동 배포",
             due="2026-09-15", plan_id=plan, assignee="course6 Lead")
    print(f"  ✓ {course_mid}")


def seed_course_iot(infra_parent_mid: str):
    g = get_graph()
    title = "course17-iot-security — IoT/임베디드 보안"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")): return
    print("\n=== course17-iot-security ===")
    course_mid = add_mission(
        title=title,
        statement="펌웨어 분석 / UART/SPI/JTAG / BLE/Zigbee / IP Camera / SCADA / CAN. 졸업 시 IoT 디바이스 침투 + OT/ICS 기초 운영.",
        owner="course17 Lead",
    )
    g.add_edge(course_mid, infra_parent_mid, "derives_from")
    course_v = add_vision(title="course17 졸업 → IoT/OT Security Engineer",
                         horizon_year=2027,
                         statement="졸업 → IoT 보안 컨설팅 / 1년 내 GICSP 자격 / 2년 내 OT 보안 lead.",
                         mission_id=course_mid)
    g_fw = add_goal(title="펌웨어 추출 + 분석 자율 수행", due="2026-12-31", vision_id=course_v,
                   description="binwalk/ghidra/radare2 활용. lab w4 펌웨어 분석.")
    g_ot = add_goal(title="OT/ICS 프로토콜 (Modbus/CAN/OPC UA) 1건 PoC", due="2026-12-31",
                   vision_id=course_v, description="lab w12-13 + P5 ot-security h001/h002.")
    s_main = add_strategy(title="시뮬레이션 (Modbus/MQTT broker) + 펌웨어 정적 분석",
                         goal_id=g_fw,
                         approach="실제 IoT 디바이스 부족 환경 — 시뮬레이션 + 공개 펌웨어 dump.")
    add_kpi(name="course17 lab pass rate", target=70.0, unit="%", goal_id=g_fw, strategy_id=s_main)
    add_kpi(name="펌웨어 분석 PoC", target=80.0, unit="%",
            measures="lab w4 의 binwalk extract + strings + 알려진 취약점 매핑 통과.",
            goal_id=g_fw)
    add_kpi(name="OT 프로토콜 PoC", target=70.0, unit="%",
            measures="P5 ot-security h001 task 학생 통과율.", goal_id=g_ot)
    plan = add_plan(title="2026-Q4 course17-iot-security 운영", period="2026-Q4",
                    owner="course17 Lead", strategy_id=s_main, goal_id=g_fw)
    add_todo(title="MQTT broker + Modbus 시뮬레이션 환경 docker-compose",
             due="2026-11-30", plan_id=plan, assignee="course17 Lead")
    print(f"  ✓ {course_mid}")


def seed_course_autosys(infra_parent_mid: str):
    g = get_graph()
    title = "course18-autonomous-systems — 드론/로봇/자율시스템 보안 (CPS)"
    if any((n.get("name") or "") == title for n in g.find_nodes("Mission")): return
    print("\n=== course18-autonomous-systems ===")
    course_mid = add_mission(
        title=title,
        statement="드론(WiFi/RF) / 자율주행(센서퓨전/적대적패치) / ROS2 / OT/ICS / V2X / GPS 스푸핑. 졸업 시 CPS 침투 + AI 모델 적대적 입력 방어.",
        owner="course18 Lead",
    )
    g.add_edge(course_mid, infra_parent_mid, "derives_from")
    course_v = add_vision(title="course18 졸업 → CPS Security Engineer / 자율주행 보안",
                         horizon_year=2027,
                         statement="졸업 → 자율주행 OEM 보안팀 / 1년 내 ROS2 보안 자체 평가 / 2년 내 CPS 침해 대응 lead.",
                         mission_id=course_mid)
    g_drone = add_goal(title="드론 해킹 + 방어 PoC 각 1건", due="2026-12-31", vision_id=course_v)
    g_av = add_goal(title="자율주행 적대적 패치 1건 PoC", due="2026-12-31", vision_id=course_v,
                   description="lab w7 자율주행 공격 + ai-safety w6 적대적 입력 cross.")
    g_cps = add_goal(title="CPS 인시던트 대응 시나리오 1건 자율 수행", due="2026-12-31", vision_id=course_v)
    s_main = add_strategy(title="시뮬레이션 + AI 모델 공격 학습",
                         goal_id=g_drone,
                         approach="실 드론·차량 부족 — gazebo 시뮬레이션 + 공개 dataset 의 적대적 patch 학습. ai-safety/ai-safety-adv 와 cross-course.")
    add_kpi(name="course18 lab pass rate", target=70.0, unit="%", goal_id=g_drone, strategy_id=s_main)
    add_kpi(name="자율주행 적대적 입력 PoC", target=60.0, unit="%",
            measures="lab w7 학생 PoC. CARLA/AirSim 등 시뮬레이션 활용도.", goal_id=g_av)
    add_kpi(name="CPS IR 6단계 완성도", target=80.0, unit="%",
            measures="lab w14 CPS IR 학생 단계별 통과율.", goal_id=g_cps)
    plan = add_plan(title="2026-Q4 course18-autonomous-systems 운영", period="2026-Q4",
                    owner="course18 Lead", strategy_id=s_main, goal_id=g_drone)
    add_todo(title="ROS2 + Gazebo 학습 환경 + 적대적 patch dataset 정리",
             due="2026-12-15", plan_id=plan, assignee="course18 Lead")
    print(f"  ✓ {course_mid}")


def main():
    print("=" * 60)
    print("9-tier KG seed — 탐지 3 + 공격 3 + IR 2 + 거버넌스 3 + 인프라 3 = 14 과목")
    print("=" * 60)
    top_mid, v_2027, v_2026 = seed_top_level()
    domain_pids = seed_domain_parents(top_mid, v_2027)
    detection_pid, attack_pid, ir_pid, gov_pid, infra_pid = domain_pids
    course_mid = seed_course_soc(detection_pid, v_2026)
    seed_course_secops(detection_pid)
    seed_course_soc_adv(detection_pid)
    seed_course_attack(attack_pid)
    seed_course_web_vuln(attack_pid)
    seed_course_attack_adv(attack_pid)
    seed_course_agent_ir(ir_pid)
    seed_course_agent_ir_adv(ir_pid)
    seed_course_compliance(gov_pid)
    seed_course_ai_safety(gov_pid)
    seed_course_ai_safety_adv(gov_pid)
    seed_course_cloud_container(infra_pid)
    seed_course_iot(infra_pid)
    seed_course_autosys(infra_pid)

    # 결과 요약
    print("\n=== 결과 요약 ===")
    g = get_graph()
    for typ in ("Mission", "Vision", "Goal", "Strategy", "KPI", "Plan", "Todo"):
        cnt = len(g.find_nodes(typ))
        print(f"  {typ:10s} {cnt}")
    print()
    print(f"최상위 Mission: {top_mid}")
    print(f"course5-soc Mission: {course_mid}")
    print()
    print("다음 작업: 19 과목 + 외부 표준 (KEV/CSF/ISO/GDPR) + Architecture + 운영 P#")


if __name__ == "__main__":
    main()
