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


def main():
    print("=" * 60)
    print("9-tier KG seed — 최상위 + 5 도메인 + 탐지·분석 도메인 3 과목")
    print("=" * 60)
    top_mid, v_2027, v_2026 = seed_top_level()
    domain_pids = seed_domain_parents(top_mid, v_2027)
    detection_pid = domain_pids[0]
    course_mid = seed_course_soc(detection_pid, v_2026)
    seed_course_secops(detection_pid)
    seed_course_soc_adv(detection_pid)

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
