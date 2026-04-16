#!/usr/bin/env python3
"""교안(lecture.md)에 실습 참조 파일/로그/UI 설명 섹션을 자동 추가.

각 주차의 lab YAML에서 참조되는 파일을 추출 → FILE_GUIDE 사전에서 설명 조회
→ 해당 주차 lecture.md에 "실습 참조 파일 가이드" 섹션이 없으면 추가.

사용:
  python3 scripts/enrich_lectures.py                    # 전체 과목
  python3 scripts/enrich_lectures.py course2-security-ops  # 특정 과목만
  python3 scripts/enrich_lectures.py --dry-run           # 미리보기
"""
import yaml, glob, re, os, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = os.path.join(ROOT, "contents", "labs")
EDUCATION = os.path.join(ROOT, "contents", "education")

# ── 파일/경로별 설명 사전 ──
# (path_pattern, 제목, VM, 설명, 내용 예시, "이런 내용이 있으면" 해석)
FILE_GUIDE: dict[str, dict] = {
    "/etc/suricata/suricata.yaml": {
        "title": "Suricata 메인 설정 파일",
        "vm": "secu",
        "desc": "Suricata IDS/IPS의 전체 설정을 관리하는 YAML 파일. 네트워크 변수(HOME_NET, EXTERNAL_NET), 캡처 인터페이스(af-packet), 룰 경로, 로깅 설정 등이 포함된다.",
        "contents": [
            "`HOME_NET: '[10.20.30.0/24]'` — 내부 네트워크 대역 정의",
            "`af-packet: - interface: ens37` — 패킷 캡처 인터페이스",
            "`rule-files: - local.rules` — 로드할 룰 파일 목록",
            "`stats: enabled: yes` — 성능 통계 활성화",
        ],
        "interpret": "`HOME_NET`이 실제 내부 대역과 다르면 탐지가 정상 동작하지 않는다. `af-packet`의 `interface`가 트래픽이 흐르는 NIC와 다르면 패킷을 캡처하지 못한다.",
    },
    "/etc/suricata/rules/local.rules": {
        "title": "Suricata 커스텀 룰 파일",
        "vm": "secu",
        "desc": "관리자가 직접 작성하는 탐지 룰. 기본 룰셋(et/open 등) 외에 조직 환경에 맞는 커스텀 시그니처를 여기에 추가한다.",
        "contents": [
            '`alert http any any -> any any (msg:"SQLi attempt"; content:"union select"; nocase; http_uri; sid:1000102; rev:1;)` — HTTP URI에서 SQL Injection 탐지',
            '`alert icmp any any -> any any (msg:"ICMP ping"; sid:1000001; rev:1;)` — ICMP 핑 탐지',
        ],
        "interpret": "새 룰 추가 후 반드시 `suricata -T`로 문법 검증하고, `systemctl reload suricata`로 반영해야 한다. sid(Signature ID)는 고유해야 하며, 1000000 이상을 커스텀 룰에 사용한다.",
    },
    "/var/log/suricata/eve.json": {
        "title": "Suricata 이벤트 로그 (JSON)",
        "vm": "secu",
        "desc": "Suricata가 생성하는 모든 이벤트(alert, flow, dns, http, tls 등)를 JSON 형식으로 기록하는 메인 로그. SIEM 연동의 핵심 데이터 소스.",
        "contents": [
            '`{"event_type":"alert","src_ip":"10.20.30.201","alert":{"signature":"SQLi attempt","signature_id":1000102}}` — 알림 이벤트',
            '`{"event_type":"flow","src_ip":"...","dest_ip":"...","proto":"TCP"}` — 네트워크 흐름 이벤트',
        ],
        "interpret": "`event_type`이 `alert`인 항목이 탐지된 공격이다. `signature_id`로 어떤 룰에 매칭됐는지, `src_ip`/`dest_ip`로 공격 출발지/목적지를 파악한다. jq로 필터링: `jq 'select(.event_type==\"alert\")'`",
    },
    "/var/log/suricata/fast.log": {
        "title": "Suricata 빠른 알림 로그 (텍스트)",
        "vm": "secu",
        "desc": "알림 이벤트를 한 줄씩 텍스트로 기록하는 간이 로그. 빠른 모니터링에 유용하지만, 상세 분석은 eve.json을 사용.",
        "contents": [
            '`04/15/2026-12:34:56.789012  [**] [1:1000102:1] SQLi attempt [**] [Classification: ...] [Priority: 1] {TCP} 10.20.30.201:45678 -> 10.20.30.80:80`',
        ],
        "interpret": "`[Priority: 1]`은 높은 우선순위(심각한 위협). IP와 포트로 공격자와 대상을 즉시 식별할 수 있다.",
    },
    "/var/log/suricata/stats.log": {
        "title": "Suricata 성능 통계 로그",
        "vm": "secu",
        "desc": "일정 간격(기본 8초)으로 Suricata 엔진의 성능 통계를 기록. 패킷 처리 수, drop 수, 메모리 사용량 등.",
        "contents": [
            "`capture.kernel_packets: 12345` — 커널에서 받은 패킷 수",
            "`capture.kernel_drops: 0` — 커널에서 drop된 패킷 수",
        ],
        "interpret": "`kernel_drops`가 0보다 크면 Suricata가 트래픽을 처리하지 못하고 누락하고 있다는 의미. CPU/메모리 증설이나 af-packet threads 조정이 필요.",
    },
    "/var/lib/suricata/rules/suricata.rules": {
        "title": "Suricata 통합 룰 파일 (suricata-update 산출물)",
        "vm": "secu",
        "desc": "`suricata-update` 명령으로 여러 룰 소스(et/open 등)를 다운로드·병합한 결과 파일. 수만 개의 룰이 하나로 합쳐져 있다.",
        "contents": [
            "ET(Emerging Threats), OISF 등 공개 룰셋이 병합된 상태",
        ],
        "interpret": "직접 편집하지 않는다. 커스텀 룰은 `/etc/suricata/rules/local.rules`에 작성. `suricata-update` 실행 시 이 파일이 덮어써진다.",
    },
    "/etc/modsecurity/modsecurity.conf": {
        "title": "ModSecurity WAF 메인 설정 파일",
        "vm": "web",
        "desc": "ModSecurity 엔진의 동작 모드, 감사 로그, 요청 본문 크기 등 핵심 설정. Apache의 `security2` 모듈이 이 파일을 로드한다.",
        "contents": [
            "`SecRuleEngine On` — 탐지+차단 활성화 (DetectionOnly면 탐지만, Off면 비활성)",
            "`SecAuditLog /var/log/apache2/modsec_audit.log` — 감사 로그 경로",
            "`SecRequestBodyLimit 13107200` — 최대 요청 본문 크기 (바이트)",
        ],
        "interpret": "`SecRuleEngine DetectionOnly`면 공격을 탐지하지만 차단하지 않는다(학습 모드). 운영 환경에서는 반드시 `On`으로 설정.",
    },
    "/etc/modsecurity/crs/rules": {
        "title": "OWASP CRS (Core Rule Set) 룰 디렉터리",
        "vm": "web",
        "desc": "OWASP에서 관리하는 범용 웹 공격 탐지 룰 모음. SQLi(942xxx), XSS(941xxx), RCE(932xxx) 등 공격 유형별 룰 파일이 위치.",
        "contents": [
            "`REQUEST-942-APPLICATION-ATTACK-SQLI.conf` — SQL Injection 탐지 룰",
            "`REQUEST-941-APPLICATION-ATTACK-XSS.conf` — Cross-Site Scripting 탐지 룰",
            "`REQUEST-932-APPLICATION-ATTACK-RCE.conf` — Remote Code Execution 탐지 룰",
        ],
        "interpret": "파일명의 번호(942, 941 등)가 rule ID의 앞 3자리와 대응한다. modsec_audit.log에서 `[id \"942100\"]`이 보이면 SQL Injection 룰에 걸린 것.",
    },
    "/var/log/apache2/modsec_audit.log": {
        "title": "ModSecurity 감사 로그",
        "vm": "web",
        "desc": "ModSecurity가 차단하거나 탐지한 요청의 상세 기록. 요청 헤더, 본문, 매칭된 룰 ID, 차단 사유 등이 포함된다.",
        "contents": [
            '`[id "942100"] [msg "SQL Injection Detected"] [severity "CRITICAL"]` — SQLi 탐지 기록',
            '`[id "941100"] [msg "XSS Attack Detected"]` — XSS 탐지 기록',
        ],
        "interpret": "`severity`가 CRITICAL이면 심각한 공격 시도. `[id \"...\"]`로 어떤 CRS 룰에 매칭됐는지 확인. 오탐(false positive)이면 해당 rule ID를 예외 처리.",
    },
    "/var/ossec/etc/ossec.conf": {
        "title": "Wazuh Manager/Agent 메인 설정 파일",
        "vm": "siem",
        "desc": "Wazuh의 전체 설정: 로그 수집 대상(<localfile>), 탐지 룰, FIM(syscheck), SCA, Active Response, remote 연결 등. XML 형식.",
        "contents": [
            "`<localfile><log_format>json</log_format><location>/var/log/suricata/eve.json</location></localfile>` — Suricata 로그 수집",
            "`<syscheck><directories>/etc,/usr/bin</directories></syscheck>` — FIM 감시 대상",
            "`<active-response><command>firewall-drop</command></active-response>` — 자동 IP 차단",
        ],
        "interpret": "`<localfile>` 에 지정된 로그만 Wazuh가 수집한다. 새 로그 소스를 추가하려면 이 섹션에 항목을 추가하고 Manager를 재시작.",
    },
    "/var/ossec/etc/rules/local_rules.xml": {
        "title": "Wazuh 커스텀 탐지 룰 파일",
        "vm": "siem",
        "desc": "관리자가 직접 작성하는 Wazuh 탐지 룰. 기본 룰셋(/var/ossec/ruleset/rules/) 외에 조직 환경에 맞는 커스텀 룰을 여기에 추가.",
        "contents": [
            '`<rule id="100100" level="10"><if_matched_sid>5402</if_matched_sid><description>Multiple sudo failures</description></rule>` — sudo 실패 3회 탐지',
        ],
        "interpret": "`level`은 심각도 (0~15). level 10 이상은 고위험. `<if_matched_sid>`로 기존 룰의 반복 발생을 탐지하는 상관분석 룰을 만들 수 있다. 수정 후 `wazuh-analysisd -t`로 문법 검증.",
    },
    "/var/ossec/logs/alerts/alerts.json": {
        "title": "Wazuh 알림 로그 (JSON)",
        "vm": "siem",
        "desc": "Wazuh가 생성한 모든 보안 알림을 JSON 형식으로 기록. Dashboard의 Security events 데이터 소스.",
        "contents": [
            '`{"rule":{"id":"100100","level":10,"description":"Multiple sudo failures"},"agent":{"name":"secu"}}` — 탐지 알림',
        ],
        "interpret": "`rule.level` ≥ 10은 즉각 대응이 필요한 고위험 이벤트. `agent.name`으로 어느 VM에서 발생했는지, `rule.id`로 어떤 탐지 룰이 매칭됐는지 파악.",
    },
    "/var/ossec/logs/ossec.log": {
        "title": "Wazuh Manager 시스템 로그",
        "vm": "siem",
        "desc": "Wazuh Manager 데몬의 동작 로그. 에이전트 연결/해제, 룰 로드, 에러 등이 기록된다.",
        "contents": [
            "`ERROR: ... Could not load rule ...` — 룰 로드 실패",
            "`INFO: Agent 'secu' connected` — 에이전트 연결",
        ],
        "interpret": "`ERROR` 로그가 반복되면 설정 오류 또는 디스크 부족. 특히 `Could not load rule`은 local_rules.xml 문법 오류.",
    },
    "/var/ossec/queue/fim/db/fim.db": {
        "title": "Wazuh FIM(File Integrity Monitoring) 데이터베이스",
        "vm": "siem",
        "desc": "syscheck가 감시 대상 파일의 해시, 권한, 소유자 등 메타데이터를 저장하는 SQLite DB. 파일 변조 감지의 기준선(baseline).",
        "contents": [
            "파일별 MD5/SHA256 해시, inode, 크기, 권한, 최종 수정 시각",
        ],
        "interpret": "이 DB의 해시와 현재 파일의 해시가 다르면 FIM 알림이 발생한다. 최초 syscheck 스캔 시 baseline이 생성되고, 이후 스캔에서 변경을 감지.",
    },
    "/var/ossec/bin/wazuh-logtest": {
        "title": "Wazuh 로그 테스트 도구",
        "vm": "siem",
        "desc": "로그 한 줄을 입력하면 Wazuh 디코더·룰이 어떻게 매칭되는지 실시간으로 확인하는 대화형 도구. 커스텀 룰 개발·디버깅에 필수.",
        "contents": [
            "입력: `Feb 01 12:34:56 host sudo: root : 3 incorrect password attempts`",
            "출력: `** Phase 3: Completed rule matching. Rule id: '100100', level: '10'`",
        ],
        "interpret": "Phase 1(디코딩) → Phase 2(기본 룰) → Phase 3(사용자 룰) 순서로 처리. Phase 3에서 의도한 rule id가 나오면 룰이 정상 동작하는 것.",
    },
    "/var/ossec/bin/wazuh-analysisd": {
        "title": "Wazuh 분석 데몬 (+ 문법 검증 도구)",
        "vm": "siem",
        "desc": "로그를 실시간 분석해 알림을 생성하는 핵심 데몬. `-t` 옵션으로 설정/룰 문법 검증도 가능.",
        "contents": [
            "`wazuh-analysisd -t` → `Configuration OK` 또는 오류 메시지 출력",
        ],
        "interpret": "local_rules.xml 수정 후 반드시 `-t`로 검증. 오류가 있으면 Manager 재시작 시 분석 데몬이 기동되지 않아 전체 탐지가 중단된다.",
    },
}

# Wazuh Dashboard UI 가이드
UI_GUIDE = """
### Wazuh Dashboard UI 가이드

| 메뉴 경로 | 용도 | 핵심 화면 요소 |
|-----------|------|---------------|
| **Dashboard → Overview** | 전체 현황 대시보드 | 24h 알림 수, Top Rule Groups, Top Agents 그래프 |
| **Dashboard → Agents** | 에이전트 관리 | 에이전트 목록, Active/Disconnected 상태, OS 정보 |
| **Dashboard → Security events** | 보안 이벤트 검색 | KQL 필터 바 (예: `rule.level >= 10`), 이벤트 테이블 |
| **Dashboard → Integrity monitoring** | FIM 이벤트 | 변경된 파일 목록, 변경 전후 해시 비교 |
| **Dashboard → Security configuration assessment** | SCA 스캔 결과 | CIS 벤치마크 항목별 Pass/Fail |
| **Dashboard → Management → Rules** | 탐지 룰 관리 | 룰 ID로 검색, 룰 내용 조회 |
| **Dashboard → Management → Configuration** | Agent/Manager 설정 확인 | ossec.conf 의 주요 섹션을 UI로 조회 |

**접속 정보**: `https://SIEM_IP:443` (기본 계정: admin / admin)

**필터 예시**:
- `rule.level >= 10` — 고위험 이벤트만
- `rule.groups: syscheck` — FIM 이벤트만
- `rule.groups: suricata` — Suricata IDS 이벤트만
- `agent.name: secu` — secu VM 이벤트만
"""

OPENCTI_GUIDE = """
### OpenCTI UI 가이드

| 메뉴 경로 | 용도 |
|-----------|------|
| **Analysis → Reports** | 위협 보고서 목록 |
| **Events → Indicators** | IOC(Indicator of Compromise) 목록 — IP, 해시, 도메인 등 |
| **Knowledge → Threat actors** | 위협 행위자 프로파일 |
| **Data → Connectors** | 외부 데이터 소스 연동 상태 |

**접속 정보**: `http://SIEM_IP:8080` (초기 설정 시 admin 계정 생성)
"""


def get_week_files(course_lab_dir: str, week: int) -> set[str]:
    """해당 주차 lab YAML에서 참조하는 파일 경로 추출."""
    paths = set()
    for variant in ["ai", "nonai"]:
        yml = os.path.join(LABS, f"{course_lab_dir}-{variant}", f"week{week:02d}.yaml")
        if not os.path.exists(yml):
            continue
        y = yaml.safe_load(open(yml))
        for s in y.get("steps", []):
            combined = f"{s.get('instruction','')} {s.get('answer','')} {s.get('hint','')} {s.get('bastion_prompt','')}"
            for m in re.findall(r'(/(?:etc|var|usr|home|proc|tmp|opt)/[\w/.\-*]+)', combined):
                # 정규화: 와일드카드/후행슬래시 제거
                clean = m.rstrip("/").replace("*", "")
                paths.add(clean)
    return paths


def build_file_guide_section(paths: set[str], include_ui: bool = False) -> str:
    """주어진 파일 경로 집합에 대한 마크다운 설명 섹션 생성."""
    lines = ["\n---\n", "## 📂 실습 참조 파일 가이드\n",
             "> 이번 주 실습에서 사용하는 설정 파일, 로그 파일, 도구의 위치와 역할입니다.\n"]

    matched = []
    for path in sorted(paths):
        # 정확히 매치 또는 디렉터리 prefix 매치
        for key, info in FILE_GUIDE.items():
            if path == key or path.startswith(key.rstrip("/")):
                matched.append((key, info))
                break

    seen = set()
    for key, info in matched:
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"### `{key}`")
        lines.append(f"**{info['title']}** (VM: {info['vm']})\n")
        lines.append(f"{info['desc']}\n")
        if info.get("contents"):
            lines.append("**주요 내용**:")
            for c in info["contents"]:
                lines.append(f"- {c}")
            lines.append("")
        if info.get("interpret"):
            lines.append(f"**해석**: {info['interpret']}\n")

    if include_ui:
        lines.append(UI_GUIDE)
        lines.append(OPENCTI_GUIDE)

    if len(seen) == 0 and not include_ui:
        return ""
    return "\n".join(lines) + "\n"


# ── 과목 → lab 디렉터리 매핑 ──
COURSE_MAP = {
    "course2-security-ops": "secops",
    "course3-soc": "soc",
    "course13-soc-advanced": "soc-adv",
    "course4-compliance": "compliance",
    "course1-attack": "attack",
    "course5-web-vuln": "web-vuln",
    "course6-cloud-container": "cloud-container",
    "course7-ai-security": "ai-security",
    "course8-ai-safety": "ai-safety",
    "course10-ai-security-agent": "ai-agent",
    "course11-battle": "battle",
    "course12-battle-advanced": "battle-adv",
    "course14-soc-advanced": "soc-adv",
    "course15-ai-safety-advanced": "ai-safety-adv",
    "course16-physical-pentest": "physical-pentest",
}

MARKER = "## 📂 실습 참조 파일 가이드"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course", nargs="?", help="특정 과목만 (예: course2-security-ops)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    courses = [args.course] if args.course else sorted(os.listdir(EDUCATION))
    updated = 0

    for course_dir in courses:
        edu_path = os.path.join(EDUCATION, course_dir)
        if not os.path.isdir(edu_path):
            continue
        lab_prefix = COURSE_MAP.get(course_dir, "")
        if not lab_prefix:
            continue

        for w in range(1, 16):
            lecture_path = os.path.join(edu_path, f"week{w:02d}", "lecture.md")
            if not os.path.exists(lecture_path):
                continue

            content = open(lecture_path, encoding="utf-8").read()
            if MARKER in content:
                continue  # 이미 추가됨

            # 해당 주차 실습에서 참조하는 파일 추출
            week_files = get_week_files(lab_prefix, w)
            if not week_files:
                continue

            # UI 도구 주차 판별
            include_ui = any(kw in content.lower() for kw in ["wazuh", "opencti", "dashboard"])
            section = build_file_guide_section(week_files, include_ui=include_ui)
            if not section:
                continue

            if args.dry_run:
                print(f"[DRY] {course_dir}/week{w:02d}: +{len(section)} chars, {len(week_files)} files")
                continue

            with open(lecture_path, "a", encoding="utf-8") as f:
                f.write(section)
            updated += 1
            print(f"Updated {course_dir}/week{w:02d}: {len(week_files)} files referenced")

    print(f"\nTotal: {updated} lectures updated")


if __name__ == "__main__":
    main()
