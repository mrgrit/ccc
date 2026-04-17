#!/usr/bin/env python3
"""교안의 주요 ASCII 다이어그램을 Mermaid 문법으로 변환.

모든 ASCII 박스를 자동 변환하기는 어려우므로, 자주 반복되는 패턴만 변환:
1. 트래픽 흐름도 (Attacker → SECU → WEB → SIEM)
2. NIST IR 라이프사이클
3. 방화벽 체인 구조
4. SOC 운영 흐름
5. 킬 체인 / ATT&CK 매핑

Usage:
  python3 scripts/convert_ascii_to_mermaid.py
  python3 scripts/convert_ascii_to_mermaid.py --dry-run
"""
import argparse, glob, re

# 자주 반복되는 ASCII → Mermaid 매핑
REPLACEMENTS = [
    # 트래픽 흐름도
    (
        re.compile(r'```\n\s*Attacker\s*[→─>]+\s*SECU\s*\(nftables\s*[→─>]+\s*suricata\)\s*[→─>]+\s*WEB\s*\(modsecurity\s*[→─>]+\s*apache\)\s*[→─>]+\s*SIEM\s*\(wazuh\)\s*\n```', re.I),
        """```mermaid
graph LR
    A[Attacker] -->|공격 트래픽| S[SECU]
    S -->|nftables 필터링| S2[Suricata IDS]
    S2 -->|허용된 트래픽| W[WEB]
    W -->|ModSecurity WAF| W2[Apache]
    W2 -->|로그| SI[SIEM/Wazuh]
    S2 -->|알림| SI
    style A fill:#f85149,color:#fff
    style S fill:#21262d,color:#e6edf3
    style W fill:#21262d,color:#e6edf3
    style SI fill:#238636,color:#fff
```"""
    ),
    # 간단한 화살표 흐름 (A → B → C 패턴)
    (
        re.compile(r'```\n\s*Attacker\s*→\s*SECU\(nftables\s*→\s*suricata\s*NFQUEUE\)\s*→[^\n]*\n[^\n]*SIEM[^\n]*\n```', re.I | re.DOTALL),
        """```mermaid
graph LR
    A[Attacker] --> S[SECU<br/>nftables + Suricata]
    S --> W[WEB<br/>ModSecurity + Apache]
    W -.->|로그| SI[SIEM<br/>Wazuh]
    S -.->|알림| SI
    SI -.->|CTI IOC| S
    style A fill:#f85149,color:#fff
    style SI fill:#238636,color:#fff
```"""
    ),
]


def convert_common_patterns(content: str) -> tuple[str, int]:
    """자주 반복되는 ASCII 패턴을 Mermaid로 치환. (치환 횟수, 결과) 반환."""
    count = 0
    for pattern, replacement in REPLACEMENTS:
        new_content, n = pattern.subn(replacement, content)
        if n > 0:
            content = new_content
            count += n
    return content, count


def add_mermaid_examples(content: str) -> str:
    """교안에 Mermaid 사용 가능 안내를 추가 (이미 없는 경우)."""
    if '```mermaid' in content:
        return content  # 이미 있음
    return content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    total = 0
    for path in sorted(glob.glob('contents/education/*/week*/lecture.md')):
        content = open(path, encoding='utf-8').read()
        new_content, count = convert_common_patterns(content)
        if count > 0:
            if not args.dry_run:
                open(path, 'w', encoding='utf-8').write(new_content)
            print(f"{'[DRY] ' if args.dry_run else ''}{path}: {count} diagrams converted")
            total += count

    print(f"\nTotal: {total} diagrams converted")

    # 주요 교안에 Mermaid 예시 다이어그램 추가 (secops, soc 등)
    if not args.dry_run:
        add_mermaid_to_key_lectures()


def add_mermaid_to_key_lectures():
    """핵심 교안에 Mermaid 다이어그램 추가."""
    # secops week01 — 인프라 구조도
    infra_mermaid = """

### 실습 인프라 구조 (Mermaid)

```mermaid
graph TB
    subgraph 학생 인프라
        ATK[attacker<br/>10.20.30.201<br/>nmap, hydra, sqlmap]
        SECU[secu<br/>10.20.30.1<br/>nftables, Suricata]
        WEB[web<br/>10.20.30.80<br/>Apache, ModSecurity<br/>JuiceShop:3000]
        SIEM[siem<br/>10.20.30.100<br/>Wazuh, OpenCTI]
        MGR[manager<br/>10.20.30.200<br/>Bastion, Ollama]
    end
    ATK -->|공격| SECU
    SECU -->|필터링 후 전달| WEB
    WEB -.->|로그 전송| SIEM
    SECU -.->|IDS 알림| SIEM
    MGR -->|관리| SECU
    MGR -->|관리| WEB
    MGR -->|관리| SIEM
    style ATK fill:#f85149,color:#fff
    style SECU fill:#d29922,color:#fff
    style WEB fill:#58a6ff,color:#fff
    style SIEM fill:#238636,color:#fff
    style MGR fill:#8b949e,color:#fff
```

### 트래픽 흐름

```mermaid
graph LR
    A[Attacker] -->|1. 공격 시도| FW[nftables<br/>방화벽]
    FW -->|2. 허용된 트래픽| IDS[Suricata<br/>IDS/IPS]
    IDS -->|3. 정상 트래픽| WAF[ModSecurity<br/>WAF]
    WAF -->|4. 안전한 요청| APP[Apache<br/>웹서버]
    IDS -.->|알림| SIEM[Wazuh<br/>SIEM]
    WAF -.->|차단 로그| SIEM
    APP -.->|접근 로그| SIEM
    style A fill:#f85149,color:#fff
    style SIEM fill:#238636,color:#fff
```
"""
    # Add to secops week01
    secops_w01 = 'contents/education/course2-security-ops/week01/lecture.md'
    try:
        content = open(secops_w01, encoding='utf-8').read()
        if '```mermaid' not in content:
            # 첫 번째 ## 전에 삽입
            idx = content.find('\n## 1.')
            if idx > 0:
                content = content[:idx] + infra_mermaid + content[idx:]
                open(secops_w01, 'w', encoding='utf-8').write(content)
                print(f"Added Mermaid infra diagram to {secops_w01}")
    except Exception as e:
        print(f"Error: {e}")

    # SOC week01 — SOC 운영 흐름
    soc_mermaid = """

### SOC 운영 흐름

```mermaid
graph TD
    LOG[로그 소스<br/>서버, 네트워크, 애플리케이션] -->|수집| SIEM[Wazuh SIEM<br/>로그 집중]
    SIEM -->|디코딩 + 룰 매칭| ALERT[알림 생성<br/>rule.level 기반]
    ALERT -->|level >= 7| L1[L1 분석관<br/>초기 분류]
    L1 -->|에스컬레이션| L2[L2 분석관<br/>심층 분석]
    L2 -->|인시던트 확정| IR[인시던트 대응<br/>봉쇄/근절/복구]
    IR -->|사후 분석| DOC[보고서<br/>교훈 반영]
    ALERT -->|level < 7| AUTO[자동 처리<br/>Active Response]
    style SIEM fill:#238636,color:#fff
    style ALERT fill:#d29922,color:#fff
    style IR fill:#f85149,color:#fff
```
"""
    soc_w01 = 'contents/education/course5-soc/week01/lecture.md'
    try:
        content = open(soc_w01, encoding='utf-8').read()
        if '```mermaid' not in content:
            idx = content.find('\n## 1.')
            if idx > 0:
                content = content[:idx] + soc_mermaid + content[idx:]
                open(soc_w01, 'w', encoding='utf-8').write(content)
                print(f"Added Mermaid SOC diagram to {soc_w01}")
    except Exception as e:
        print(f"Error: {e}")

    # Battle week01 — 공방전 구조
    battle_mermaid = """

### 공방전 구조

```mermaid
graph LR
    subgraph Red Team
        R1[정찰] --> R2[스캐닝] --> R3[익스플로잇] --> R4[권한상승] --> R5[지속성]
    end
    subgraph Blue Team
        B1[모니터링] --> B2[탐지] --> B3[분석] --> B4[차단] --> B5[복구]
    end
    R3 -.->|공격 흔적| B2
    R5 -.->|이상 행위| B1
    style R1 fill:#f85149,color:#fff
    style R2 fill:#f85149,color:#fff
    style R3 fill:#f85149,color:#fff
    style R4 fill:#f85149,color:#fff
    style R5 fill:#f85149,color:#fff
    style B1 fill:#58a6ff,color:#fff
    style B2 fill:#58a6ff,color:#fff
    style B3 fill:#58a6ff,color:#fff
    style B4 fill:#58a6ff,color:#fff
    style B5 fill:#58a6ff,color:#fff
```
"""
    battle_w01 = 'contents/education/course11-battle/week01/lecture.md'
    try:
        content = open(battle_w01, encoding='utf-8').read()
        if '```mermaid' not in content:
            idx = content.find('\n## 1.')
            if idx > 0:
                content = content[:idx] + battle_mermaid + content[idx:]
                open(battle_w01, 'w', encoding='utf-8').write(content)
                print(f"Added Mermaid battle diagram to {battle_w01}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
