#!/usr/bin/env python3
"""교안(lecture.md)의 '실습 참조 파일 가이드' 섹션을 주차 주제에 맞게 재작성.

기존 enrich_lectures.py는 공통 인프라 표에 'Wazuh/OpenCTI' 문자열이 있으면
무조건 Wazuh/OpenCTI UI 가이드를 붙여 93개 교안에 잘못 주입되었다.
본 스크립트는 (course, week) → 주제 기반 실제 솔루션을 식별하여
교안마다 해당 솔루션의 기능/디렉토리/파일/설정/UI를 정확히 서술한다.

실행:
  python3 scripts/fix_lecture_solutions.py           # 전체
  python3 scripts/fix_lecture_solutions.py --dry-run # 미리보기
  python3 scripts/fix_lecture_solutions.py course1-attack week05
"""
from __future__ import annotations
import os, re, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDU = os.path.join(ROOT, "contents", "education")

# ───────────────────────── 솔루션 카드 라이브러리 ─────────────────────────
# 각 카드는 강의 실습에서 실제로 만지는 솔루션 1개를 정확히 서술한다.
# 필드:
#   name      — 솔루션 표기명
#   role      — 한 줄 역할
#   vm        — 주 실행 호스트
#   access    — 접속/호출 방식
#   dirs      — 주요 경로 [(경로, 설명), ...]
#   config    — 핵심 설정 파일/섹션 [(파일, 핵심 키, 효과)]
#   logs      — 주요 로그 [(경로, 내용)]
#   ui        — UI/CLI 요점 [(메뉴/명령, 용도)]
#   tip       — 해석 팁 (짧게)
SOL: dict[str, dict] = {
    # ── 과정2 (security-ops) ──
    "nftables": {
        "name": "nftables",
        "role": "Linux 커널 기반 상태 기반 방화벽 (iptables 후속)",
        "vm": "secu (10.20.30.1)",
        "access": "`sudo nft ...` CLI + `/etc/nftables.conf` 영속 설정",
        "dirs": [
            ("/etc/nftables.conf", "부팅 시 로드되는 영속 룰셋"),
            ("/var/log/kern.log", "`log prefix` 룰의 패킷 드롭 로그"),
        ],
        "config": [
            ("table inet filter", "IPv4/IPv6 공통 필터 테이블"),
            ("chain input { policy drop; }", "기본 차단 정책"),
            ("ct state established,related accept", "응답 트래픽 허용"),
        ],
        "logs": [
            ("journalctl -t kernel -g 'nft'", "룰에서 `log prefix` 지정한 패킷 드롭"),
        ],
        "ui": [
            ("`sudo nft list ruleset`", "현재 로드된 전체 룰 출력"),
            ("`sudo nft -f /etc/nftables.conf`", "설정 파일 재적용"),
            ("`sudo nft list set inet filter blacklist`", "집합(set) 내용 조회"),
        ],
        "tip": "룰은 **위→아래 첫 매칭 우선**. `accept`는 해당 체인만 종료, 상위 훅은 계속 평가된다. 변경 후 `nft list ruleset`로 실제 적용 여부 확인.",
    },
    "suricata": {
        "name": "Suricata IDS/IPS",
        "role": "시그니처 기반 네트워크 침입 탐지/차단 엔진",
        "vm": "secu (10.20.30.1)",
        "access": "`systemctl status suricata` / `suricatasc` 소켓 / `suricata -T`",
        "dirs": [
            ("/etc/suricata/suricata.yaml", "메인 설정 (HOME_NET, af-packet, rule-files)"),
            ("/etc/suricata/rules/local.rules", "사용자 커스텀 탐지 룰"),
            ("/var/lib/suricata/rules/suricata.rules", "`suricata-update` 병합 룰"),
            ("/var/log/suricata/eve.json", "JSON 이벤트 (alert/flow/http/dns/tls)"),
            ("/var/log/suricata/fast.log", "알림 1줄 텍스트 로그"),
            ("/var/log/suricata/stats.log", "엔진 성능 통계"),
        ],
        "config": [
            ("HOME_NET", "내부 대역 — 틀리면 내부/외부 판별 실패"),
            ("af-packet.interface", "캡처 NIC — 트래픽이 흐르는 인터페이스와 일치해야 함"),
            ('rule-files: ["local.rules"]', "로드할 룰 파일 목록"),
        ],
        "logs": [
            ("jq 'select(.event_type==\"alert\")' eve.json", "알림만 추출"),
            ("grep 'Priority: 1' fast.log", "고위험 탐지만 빠르게 확인"),
        ],
        "ui": [
            ("`suricata -T -c /etc/suricata/suricata.yaml`", "설정/룰 문법 검증"),
            ("`suricatasc -c stats`", "실시간 통계 조회 (런타임 소켓)"),
            ("`suricata-update`", "공개 룰셋 다운로드·병합"),
        ],
        "tip": "`stats.log`의 `kernel_drops > 0`이면 누락 발생 → `af-packet threads` 증설. 커스텀 룰 `sid`는 **1,000,000 이상** 할당 권장.",
    },
    "bunkerweb": {
        "name": "BunkerWeb WAF (ModSecurity CRS)",
        "role": "Nginx 기반 웹 방화벽 — OWASP Core Rule Set 통합",
        "vm": "web (10.20.30.80)",
        "access": "리스닝 포트 `:8082` (원본 :80/:3000 프록시)",
        "dirs": [
            ("/etc/bunkerweb/variables.env", "서버 단위 기본 변수"),
            ("/etc/bunkerweb/configs/modsec/", "커스텀 ModSecurity 룰"),
            ("/var/log/bunkerweb/modsec_audit.log", "ModSec 감사 로그(차단된 요청)"),
            ("/var/log/bunkerweb/access.log", "정상 요청 로그"),
        ],
        "config": [
            ("USE_MODSECURITY=yes", "ModSec 엔진 활성화"),
            ("USE_MODSECURITY_CRS=yes", "OWASP CRS 활성화"),
            ("MODSECURITY_CRS_VERSION=4", "CRS 버전"),
        ],
        "logs": [
            ("grep 'Matched Phase' modsec_audit.log", "룰에 매칭된 단계 확인"),
            ("grep 'HTTP/1.1\" 403' access.log", "WAF가 차단한 요청"),
        ],
        "ui": [
            ("`curl -i http://10.20.30.80:8082/?id=1' OR '1'='1`", "SQLi 페이로드 테스트"),
            ("응답 코드 `403 Forbidden`", "WAF 차단 정상 동작"),
        ],
        "tip": "오탐 시 `SecRuleRemoveById 942100` 방식으로 특정 룰만 제외. 차단 판정은 **점수 임계값**(기본 5) 기준이므로 단일 룰 1건은 차단되지 않을 수 있다.",
    },
    "wazuh": {
        "name": "Wazuh SIEM (4.11.x)",
        "role": "에이전트 기반 로그·FIM·SCA 통합 분석 플랫폼",
        "vm": "siem (10.20.30.100)",
        "access": "Dashboard `https://10.20.30.100` (admin/admin), Manager API `:55000`",
        "dirs": [
            ("/var/ossec/etc/ossec.conf", "Manager 메인 설정 (원격, 전송, syscheck 등)"),
            ("/var/ossec/etc/rules/local_rules.xml", "커스텀 룰 (id ≥ 100000)"),
            ("/var/ossec/etc/decoders/local_decoder.xml", "커스텀 디코더"),
            ("/var/ossec/logs/alerts/alerts.json", "실시간 JSON 알림 스트림"),
            ("/var/ossec/logs/archives/archives.json", "전체 이벤트 아카이브"),
            ("/var/ossec/logs/ossec.log", "Manager 데몬 로그"),
            ("/var/ossec/queue/fim/db/fim.db", "FIM 기준선 SQLite DB"),
        ],
        "config": [
            ("<rule id='100100' level='10'>", "커스텀 룰 — level 10↑은 고위험"),
            ("<syscheck><directories>...", "FIM 감시 경로"),
            ("<active-response>", "자동 대응 (firewall-drop, restart)"),
        ],
        "logs": [
            ("jq 'select(.rule.level>=10)' alerts.json", "고위험 알림만"),
            ("grep ERROR ossec.log", "Manager 오류 (룰 문법 오류 등)"),
        ],
        "ui": [
            ("Dashboard → Security events", "KQL 필터 `rule.level >= 10`"),
            ("Dashboard → Integrity monitoring", "변경된 파일 해시 비교"),
            ("`/var/ossec/bin/wazuh-logtest`", "룰 매칭 단계별 확인 (Phase 1→3)"),
            ("`/var/ossec/bin/wazuh-analysisd -t`", "룰·설정 문법 검증"),
        ],
        "tip": "Phase 3에서 원하는 `rule.id`가 떠야 커스텀 룰 정상. `local_rules.xml` 수정 후 `systemctl restart wazuh-manager`, 문법 오류가 있으면 **분석 데몬 전체가 기동 실패**하므로 `-t`로 먼저 검증.",
    },
    "opencti": {
        "name": "OpenCTI (Threat Intelligence Platform)",
        "role": "STIX 2.1 기반 위협 인텔리전스 통합 관리",
        "vm": "siem (10.20.30.100)",
        "access": "UI `http://10.20.30.100:8080`, GraphQL `:8080/graphql`",
        "dirs": [
            ("/opt/opencti/config/default.json", "포트·DB·ElasticSearch 접속 설정"),
            ("/opt/opencti-connectors/", "MITRE/MISP/AlienVault 등 커넥터"),
            ("docker compose ps (프로젝트 경로)", "ElasticSearch/RabbitMQ/Redis 상태"),
        ],
        "config": [
            ("app.admin_email/password", "초기 관리자 계정 — 변경 필수"),
            ("connectors: opencti-connector-mitre", "MITRE ATT&CK 동기화"),
        ],
        "logs": [
            ("docker logs opencti", "메인 플랫폼 로그"),
            ("docker logs opencti-worker", "백엔드 인제스트 워커"),
        ],
        "ui": [
            ("Analysis → Reports", "위협 보고서 원문과 IOC"),
            ("Events → Indicators", "IOC 검색 (hash/ip/domain)"),
            ("Knowledge → Threat actors", "위협 행위자 프로파일과 TTP"),
            ("Data → Connectors", "외부 소스 동기화 상태"),
        ],
        "tip": "IOC 1건을 **관측(Observable)** → **지표(Indicator)** → **보고서(Report)**로 승격해 컨텍스트를 쌓아야 헌팅에 활용 가능. STIX relationship(`uses`, `indicates`)이 분석의 핵심.",
    },

    # ── 과정3 (web-vuln) ──
    "burp": {
        "name": "Burp Suite Community",
        "role": "웹 프록시 기반 수동/반자동 취약점 점검 도구",
        "vm": "작업 PC → web (10.20.30.80:3000)",
        "access": "GUI `burpsuite`, CA 인증서 신뢰 필요 (`http://burp`)",
        "dirs": [
            ("Proxy → HTTP history", "모든 캡처된 요청/응답"),
            ("Intruder", "페이로드 페이즈·위치 기반 자동화"),
            ("Repeater", "단건 요청 수동 반복"),
        ],
        "config": [
            ("Proxy listener 127.0.0.1:8080", "브라우저 프록시 포트"),
            ("Target → Scope", "in-scope 호스트만 처리"),
        ],
        "logs": [
            ("Logger", "세션 전체 요청 타임라인"),
        ],
        "ui": [
            ("Ctrl+R", "요청을 Repeater로 전송"),
            ("Ctrl+I", "Intruder로 전송 후 위치(§) 설정"),
            ("Intruder Attack type: Sniper/Cluster bomb", "단일/다중 페이로드 조합"),
        ],
        "tip": "Community 버전은 **Intruder 속도 제한**이 있어 대량 브루트포스는 비현실적. 취약점 재현과 보고서 증적 확보에 집중.",
    },
    "zap": {
        "name": "OWASP ZAP",
        "role": "오픈소스 자동 웹 취약점 스캐너·프록시",
        "vm": "작업 PC / Docker",
        "access": "GUI `zaproxy`, API `http://zap:8090/JSON/...`, Docker `owasp/zap2docker-stable`",
        "dirs": [
            ("~/.ZAP/session-*", "세션 저장소"),
            ("context.xml", "스캔 컨텍스트(범위/인증)"),
        ],
        "config": [
            ("Active Scan policy", "룰별 강도 및 활성화 여부"),
            ("Authentication: form-based", "로그인이 필요한 페이지 스캔"),
        ],
        "logs": [
            ("~/.ZAP/zap.log", "스캐너 실행 로그"),
        ],
        "ui": [
            ("Spider", "링크 탐색 크롤링"),
            ("Active Scan", "실제 페이로드 주입 점검"),
            ("Report → Generate HTML report", "표준 보고서 출력"),
        ],
        "tip": "인증 필요 페이지는 **Context에 로그인 폼**을 등록하지 않으면 로그아웃 상태로 스캔되어 커버리지가 급감. `zap-baseline.py`는 수동 확인용 경량 모드.",
    },
    "sqlmap": {
        "name": "sqlmap",
        "role": "SQL Injection 탐지·악용 자동화",
        "vm": "공격자 측 CLI",
        "access": "`sqlmap -u <url>` 또는 `-r request.txt`",
        "dirs": [
            ("~/.local/share/sqlmap/output/<host>/", "세션·덤프 결과"),
            ("session.sqlite", "재실행 시 단계 스킵용 캐시"),
        ],
        "config": [
            ("--risk=1~3 --level=1~5", "탐지 공격 폭 조절"),
            ("--technique=BEUSTQ", "B)lind E)rror U)nion S)tacked T)ime Q)uery"),
        ],
        "logs": [
            ("output/<host>/log", "요청·응답 로그"),
        ],
        "ui": [
            ("`sqlmap -u ... --dbs`", "DB 목록"),
            ("`sqlmap -u ... -D juice -T users --dump`", "특정 테이블 덤프"),
            ("`sqlmap -r req.txt --batch --crawl=2`", "Burp 저장 요청 기반 크롤링"),
        ],
        "tip": "`--batch`로 대화형 프롬프트 자동 Y 처리. WAF가 있을 땐 `--tamper=space2comment,between` 조합으로 우회 시도.",
    },
    "gobuster_nikto": {
        "name": "gobuster + nikto",
        "role": "디렉토리 브루트포싱 + 웹 서버 기본 취약점 스캔",
        "vm": "공격자 측 CLI",
        "access": "`gobuster dir -u <url> -w <wordlist>`, `nikto -h <url>`",
        "dirs": [
            ("/usr/share/wordlists/dirb/common.txt", "기본 워드리스트"),
            ("/usr/share/seclists/", "SecLists — 실전 워드리스트"),
        ],
        "config": [
            ("-t 50", "gobuster 동시 스레드"),
            ("-x php,html,bak", "확장자 조합 탐색"),
            ("-Tuning 9", "nikto 고급 룰 포함"),
        ],
        "logs": [
            ("-o gobuster.out", "결과 저장"),
            ("`nikto -o nikto.html -Format htm`", "HTML 리포트"),
        ],
        "ui": [
            ("gobuster 상태 204/301/302", "존재는 하지만 리다이렉트되는 경로"),
            ("nikto `OSVDB-...`", "공개 취약점 DB 매핑"),
        ],
        "tip": "응답 크기와 상태코드의 **공통 패턴**을 `-s 200,204,301` / `-b 123`으로 제외하면 오탐이 급감한다.",
    },

    # ── 과정1 (attack) ──
    "nmap": {
        "name": "Nmap",
        "role": "포트 스캔·서비스 탐지·NSE 스크립트",
        "vm": "bastion / 공격자 측",
        "access": "`nmap` CLI",
        "dirs": [
            ("/usr/share/nmap/scripts/", "NSE 스크립트 모음 (vuln, default 등)"),
            ("/usr/share/nmap/nmap-services", "포트↔서비스 매핑"),
        ],
        "config": [
            ("-sS -sV -O", "SYN 스캔 + 버전 + OS"),
            ("--script vuln", "취약점 스크립트 카테고리"),
            ("-T0..T5", "스캔 타이밍 — T3 기본, T4 실습용"),
        ],
        "logs": [
            ("-oA scan", "3가지 포맷(`.nmap/.gnmap/.xml`) 동시 저장"),
        ],
        "ui": [
            ("`nmap -sV -p- 10.20.30.80`", "전 포트 + 버전"),
            ("`nmap --script=http-enum 10.20.30.80`", "웹 디렉토리 열거"),
            ("`nmap -sn 10.20.30.0/24`", "호스트 발견(핑 스윕)"),
        ],
        "tip": "IPS가 있는 환경에서 T4 이상은 빠르게 탐지된다. `-T2`로 느리게 + `--max-retries 1`로 재전송 최소화하면 우회 확률↑.",
    },
    "jwt_tools": {
        "name": "JWT 분석 — jwt-cli / jwt.io",
        "role": "JWT 디코드·서명 검증·위조 테스트",
        "vm": "공격자 측 CLI",
        "access": "`jwt decode <token>`, 웹: `https://jwt.io`",
        "dirs": [
            ("~/.jwt-cli/", "jwt-cli 설정"),
        ],
        "config": [
            ("alg=none 공격", "서명 검증 로직이 알고리즘 필드만 신뢰할 때"),
            ("HS256 secret 브루트", "약한 HMAC 키"),
        ],
        "logs": [],
        "ui": [
            ("`jwt decode <token>`", "header/payload 출력"),
            ("`jwt encode --alg HS256 -S secret '{...}'`", "새 토큰 생성"),
            ("`hashcat -m 16500 token.txt wordlist.txt`", "HS256 키 크래킹"),
        ],
        "tip": "`alg`를 `none` 또는 `HS256`로 바꿔 공개키를 HMAC 시크릿으로 사용하는 고전 취약점은 여전히 발견된다. 서버가 **알고리즘 화이트리스트**를 갖는지 반드시 확인.",
    },
    "tcpdump_wireshark": {
        "name": "tcpdump + Wireshark",
        "role": "패킷 캡처·오프라인 분석",
        "vm": "secu/web (tcpdump) → 분석 PC (Wireshark)",
        "access": "`sudo tcpdump -i <if> -w cap.pcap`, 분석은 `wireshark cap.pcap`",
        "dirs": [
            ("/var/tmp/cap.pcap", "실습용 캡처 저장 위치"),
        ],
        "config": [
            ("-i any", "전 인터페이스"),
            ("-s 0", "잘림 없이 전체 패킷 캡처"),
            ("BPF: 'tcp port 80 and host 10.20.30.80'", "필터식"),
        ],
        "logs": [],
        "ui": [
            ("Wireshark `http.request.method == POST`", "POST 요청만"),
            ("Wireshark Follow → TCP Stream", "세션 내용 재구성"),
            ("`tshark -r cap.pcap -Y http`", "CLI 필터 출력"),
        ],
        "tip": "실환경 캡처는 **개인정보 포함** 가능성이 커 공유 전 `editcap`/`tcprewrite`로 익명화. BPF는 커널 레벨, Wireshark 필터는 디코드 후 레벨이라는 차이 기억.",
    },
    "metasploit": {
        "name": "Metasploit Framework",
        "role": "익스플로잇 검증·페이로드 생성·후속 단계 자동화",
        "vm": "공격자 측 (kali/bastion)",
        "access": "`msfconsole`, DB: `msfdb init && db_status`",
        "dirs": [
            ("/usr/share/metasploit-framework/modules/", "exploit/auxiliary/post 모듈"),
            ("~/.msf4/loot/", "덤프된 자격증명·파일"),
        ],
        "config": [
            ("set RHOSTS / LHOST / LPORT", "타깃과 리스너"),
            ("set PAYLOAD linux/x64/meterpreter/reverse_tcp", "역접속 페이로드"),
        ],
        "logs": [
            ("~/.msf4/logs/", "세션·모듈 실행 로그"),
        ],
        "ui": [
            ("`use exploit/unix/ftp/vsftpd_234_backdoor`", "모듈 선택"),
            ("`run -j`", "백그라운드 실행"),
            ("`sessions -i 1`", "세션 상호작용"),
        ],
        "tip": "Meterpreter 세션은 `migrate <pid>`로 장기 프로세스에 이주해 안정성↑. **실습 외 네트워크 금지** — `RHOSTS`는 실습 대역 10.20.30.0/24로만.",
    },
    "hydra_hashcat": {
        "name": "Hydra + Hashcat",
        "role": "온라인 로그인 무차별(Hydra) + 오프라인 해시 크래킹(Hashcat)",
        "vm": "공격자 측 CLI",
        "access": "`hydra -l <u> -P <wl> <proto>://<host>`, `hashcat -m <모드> hash.txt wordlist`",
        "dirs": [
            ("/usr/share/wordlists/rockyou.txt", "대표 워드리스트"),
            ("/usr/share/hashcat/OneRuleToRuleThemAll.rule", "룰 기반 변형"),
        ],
        "config": [
            ("hydra -t 4", "동시 접속 수 — IPS 차단 유발 주의"),
            ("hashcat -m 1800", "sha512crypt(Linux /etc/shadow)"),
            ("hashcat -m 1000", "NTLM"),
        ],
        "logs": [
            ("hydra.restore", "중단된 공격 재개용 세션"),
            ("hashcat.potfile", "이미 크랙된 해시 캐시 (`~/.hashcat/hashcat.potfile`)"),
        ],
        "ui": [
            ("`hydra -l admin -P rockyou.txt ssh://10.20.30.80 -t 2`", "SSH 브루트"),
            ("`hashcat -m 1800 shadow.hash rockyou.txt -r rules/best64.rule`", "룰 적용 크랙"),
        ],
        "tip": "Hydra는 **계정 잠금·fail2ban에 취약**. `-t`를 작게(2~4) 두고, 분산 시간 증가 옵션 사용. Hashcat은 **GPU 활용 시 `-d` 옵션으로 장치 선택**.",
    },
    "linpeas": {
        "name": "LinPEAS / linux-exploit-suggester",
        "role": "Linux 권한 상승 벡터 자동 열거",
        "vm": "침투 대상 호스트 (저권한 셸)",
        "access": "`./linpeas.sh`, `./les.sh`",
        "dirs": [
            ("/tmp/linpeas.sh", "업로드 위치 (실행권한 +x)"),
            ("/dev/shm/", "tmpfs — 로그 잔존이 적어 자주 사용"),
        ],
        "config": [
            ("-a", "심층 분석(파일 내용까지 스캔)"),
            ("-s", "빠른 모드"),
        ],
        "logs": [
            ("/tmp/linpeas.out", "결과 저장"),
        ],
        "ui": [
            ("결과의 빨강/노랑 highlights", "Critical/Probable 권한상승 벡터"),
            ("SUID·sudo·cron·capabilities·kernel 섹션", "체크리스트 핵심"),
        ],
        "tip": "결과는 **가능성 높은 순**으로 정렬되지만, 실제 exploit은 커널·배포판 버전 의존. `uname -a`/`/etc/os-release`로 대상 확정 후 공개 PoC 선택.",
    },

    # ── 과정6 (cloud-container) ──
    "docker": {
        "name": "Docker Engine",
        "role": "컨테이너 런타임·이미지 관리",
        "vm": "모든 VM(공통)",
        "access": "`docker` CLI, `systemctl status docker`",
        "dirs": [
            ("/var/lib/docker/", "이미지·컨테이너 저장소(overlay2)"),
            ("/etc/docker/daemon.json", "데몬 설정 (log-driver, userns-remap 등)"),
            ("/var/run/docker.sock", "Docker API 소켓 — 루트권한 등가"),
        ],
        "config": [
            ('{"userns-remap": "default"}', "컨테이너 root↔호스트 비루트 매핑"),
            ('{"icc": false}', "기본 네트워크 내 컨테이너 간 통신 차단"),
            ('{"no-new-privileges": true}', "setuid 권한 상승 차단"),
        ],
        "logs": [
            ("journalctl -u docker", "데몬 로그"),
            ("`docker logs <c>`", "컨테이너 stdout/stderr"),
        ],
        "ui": [
            ("`docker inspect <c> | jq '.[0].HostConfig.Privileged'`", "`--privileged` 여부"),
            ("`docker exec -it <c> sh`", "컨테이너 내부 진입"),
            ("`docker system df`", "이미지/볼륨 디스크 사용량"),
        ],
        "tip": "`/var/run/docker.sock`을 컨테이너에 마운트하는 순간 **호스트 루트와 동등**이다. 점검 1순위.",
    },
    "dockerfile_secure": {
        "name": "Dockerfile 보안 작성",
        "role": "최소 권한·재현성·비밀 격리",
        "vm": "빌드 호스트",
        "access": "`docker build -t img .`",
        "dirs": [
            ("Dockerfile", "빌드 정의"),
            (".dockerignore", "이미지에 포함하지 않을 파일"),
        ],
        "config": [
            ("FROM <distroless|alpine>", "최소 베이스"),
            ("USER 1000", "비root 실행"),
            ("RUN --mount=type=secret,id=NPM_TOKEN", "빌드 비밀 외부 주입"),
            ("HEALTHCHECK CMD ...", "컨테이너 헬스체크"),
        ],
        "logs": [
            ("`docker history <img>`", "레이어별 변경 크기·명령"),
        ],
        "ui": [
            ("`docker scout cves <img>`", "이미지 CVE 스캔"),
            ("`dive <img>`", "레이어별 파일 변경 시각화"),
        ],
        "tip": "`COPY . .` 전에 `.dockerignore`로 `.git`, `.env` 제외. 빌드 시 `ARG SECRET=...` 는 **이미지 메타데이터에 남는다** — 비밀은 BuildKit `--secret` 사용.",
    },
    "trivy": {
        "name": "Trivy",
        "role": "이미지·파일시스템·IaC·K8s CVE/미스컨피그 스캐너",
        "vm": "임의 호스트 / CI",
        "access": "`trivy image <img>` / `trivy fs .` / `trivy config .`",
        "dirs": [
            ("~/.cache/trivy/", "취약점 DB 캐시"),
            (".trivyignore", "무시할 CVE ID 목록"),
        ],
        "config": [
            ("--severity HIGH,CRITICAL", "심각도 필터"),
            ("--ignore-unfixed", "수정본 없는 CVE 제외"),
            ("--format sarif", "CI용 SARIF 출력"),
        ],
        "logs": [],
        "ui": [
            ("`trivy image --exit-code 1 --severity HIGH,CRITICAL <img>`", "CI 게이트"),
            ("`trivy k8s --report summary cluster`", "클러스터 전체 요약"),
        ],
        "tip": "`--ignore-unfixed`는 잡음을 크게 줄이지만 **미래 위험**을 숨긴다. 이미지 재빌드 주기와 함께 운영 기준을 정하자.",
    },
    "docker_bench": {
        "name": "Docker Bench for Security",
        "role": "CIS Docker Benchmark 자동 점검 스크립트",
        "vm": "Docker 호스트",
        "access": "`docker run --rm --net host --pid host --userns host --cap-add audit_control ... docker/docker-bench-security`",
        "dirs": [
            ("docker-bench-security.log", "점검 결과 텍스트"),
            ("docker-bench-security.sh", "실행 스크립트"),
        ],
        "config": [
            ("--no-colors", "CI 친화 출력"),
            ("-c check_4", "특정 섹션만 실행"),
        ],
        "logs": [
            ("결과 [PASS]/[WARN]/[INFO]", "항목별 상태"),
        ],
        "ui": [
            ("`docker-bench` 섹션 2.14", "live restore 활성 여부"),
            ("섹션 4", "컨테이너 이미지/빌드 보안"),
        ],
        "tip": "`[INFO]`는 자동 판단 불가 — 수동 확인 필수. 매 릴리즈 CIS 버전과 Docker 버전 매핑을 맞추자.",
    },
    "kubernetes": {
        "name": "Kubernetes + kubectl",
        "role": "컨테이너 오케스트레이션",
        "vm": "컨트롤 플레인 / kubeconfig 보유 클라이언트",
        "access": "`kubectl` with `~/.kube/config`",
        "dirs": [
            ("/etc/kubernetes/", "컨트롤 플레인 설정 (kubeadm)"),
            ("/var/lib/etcd/", "etcd 저장소 — 전체 클러스터 시크릿 포함"),
            ("~/.kube/config", "사용자 인증 정보"),
        ],
        "config": [
            ("PodSecurity admission (restricted)", "네임스페이스별 보안 레벨"),
            ("NetworkPolicy default-deny", "파드 간 기본 차단"),
            ("RBAC Role/RoleBinding", "최소 권한"),
        ],
        "logs": [
            ("`kubectl logs <pod> -c <container>`", "파드 로그"),
            ("`kubectl get events -A`", "클러스터 이벤트"),
        ],
        "ui": [
            ("`kubectl auth can-i --list`", "현재 주체가 가능한 동작 열거"),
            ("`kubectl get pods -A -o wide`", "전체 파드 상태"),
            ("`kubectl describe pod <p>`", "이벤트/이미지/볼륨 상세"),
        ],
        "tip": "etcd 노출·kubeconfig 유출은 **즉각적 클러스터 장악**. `kubectl auth can-i` 결과가 예상보다 많으면 RBAC 재설계 신호.",
    },
    "kube_bench_falco": {
        "name": "kube-bench + Falco",
        "role": "K8s CIS 점검(kube-bench) + 런타임 이상 행위 탐지(Falco)",
        "vm": "클러스터 노드 (DaemonSet)",
        "access": "`kube-bench run`, Falco는 `journalctl -u falco`",
        "dirs": [
            ("/etc/kubernetes/manifests/", "정적 Pod 매니페스트 (API server 등)"),
            ("/etc/falco/falco_rules.yaml", "기본 탐지 룰"),
            ("/etc/falco/falco_rules.local.yaml", "커스텀 룰"),
        ],
        "config": [
            ("anonymous-auth=false (API server)", "익명 요청 차단"),
            ("Falco `Contains any of privileged_syscalls`", "커널 차원 의심 호출"),
        ],
        "logs": [
            ("kube-bench `[FAIL]`", "CIS 항목 실패"),
            ("journalctl -u falco -f", "실시간 경보 스트림"),
        ],
        "ui": [
            ("`kube-bench run --targets master,node`", "전 구성요소 점검"),
            ("Falco `falcoctl` 룰 관리", "원격 룰 업데이트"),
        ],
        "tip": "kube-bench의 일부 [FAIL]은 **매니지드 서비스(EKS/GKE)에서 해당 없음**. managed 프로필 지정하면 잡음 감소.",
    },

    # ── 과정4 (compliance) — 솔루션보다는 표준/도구 ──
    "iso27001": {
        "name": "ISO/IEC 27001:2022 (Annex A)",
        "role": "정보보호 관리체계 국제 표준 — 93개 통제(A.5~A.8)",
        "vm": "문서/증적 (정책·절차·기록)",
        "access": "표준 문서 + SoA + 리스크 등록부",
        "dirs": [
            ("SoA.xlsx (Statement of Applicability)", "93개 통제 적용/제외 선언"),
            ("risk_register.xlsx", "자산·위협·취약점·리스크 점수"),
            ("policies/", "정책 14종 (접근제어, 백업, 사건대응 등)"),
        ],
        "config": [
            ("A.5 (조직적)", "정책, 역할, 정보분류"),
            ("A.6 (인적)", "채용·퇴직 시 보안, 인식 교육"),
            ("A.7 (물리적)", "보안 구역, 장비, 케이블링"),
            ("A.8 (기술적)", "접근·암호화·로깅·개발 보안"),
        ],
        "logs": [
            ("내부심사 보고서", "부적합(NC)·관찰사항(OB)"),
            ("경영검토 회의록", "연 1회 필수"),
        ],
        "ui": [
            ("PDCA 사이클", "수립→운영→검토→개선"),
            ("2022 개정", "114→93 통제, 신규 11건(위협 인텔리전스 등)"),
        ],
        "tip": "SoA는 **모든 통제에 대해 포함/제외 사유**를 명시해야 한다. 심사관은 `Justification for exclusion`을 먼저 본다.",
    },
    "ismsp": {
        "name": "ISMS-P (KISA)",
        "role": "한국 정보보호·개인정보보호 관리체계",
        "vm": "문서/증적",
        "access": "KISA 인증 심사 체크리스트",
        "dirs": [
            ("관리체계 수립·운영 (1장)", "정책·조직·자산·위험관리 16개"),
            ("보호대책 요구사항 (2장)", "64개 통제"),
            ("개인정보 처리 단계별 요구사항 (3장)", "21개 통제"),
        ],
        "config": [
            ("총 101개 통제항목", "인증: 80개 핵심 + 선택 21개"),
            ("매 3년 갱신 심사", "매년 사후 심사"),
        ],
        "logs": [
            ("접근기록 보관 (1년/3년)", "개인정보 중요도별"),
            ("개인정보 영향평가(PIA) 보고서", "5만명↑ 공공기관 의무"),
        ],
        "ui": [
            ("https://isms.kisa.or.kr", "고시·해설서 공식 사이트"),
        ],
        "tip": "한국은 **개인정보보호법이 최상위**. ISMS-P의 3장(개인정보)은 법 위반 여부와 직결되므로 증적 우선순위 1.",
    },
    "nist_csf": {
        "name": "NIST Cybersecurity Framework 2.0",
        "role": "미국 연방 사이버 보안 프레임워크",
        "vm": "전사 거버넌스",
        "access": "NIST 공식 PDF + Profile Tool",
        "dirs": [
            ("Core (6 Functions)", "Govern / Identify / Protect / Detect / Respond / Recover"),
            ("Categories / Subcategories", "기능별 통제 항목"),
            ("Implementation Tiers 1~4", "성숙도"),
        ],
        "config": [
            ("Govern (2.0 신규)", "거버넌스 — 조직 맥락, 역할, 리스크 전략"),
            ("Profiles (Current/Target)", "현재 상태→목표 상태 갭"),
        ],
        "logs": [],
        "ui": [
            ("https://www.nist.gov/cyberframework", "CSF 공식"),
            ("OLIR (매핑)", "ISO 27001, CIS Controls와 상호 매핑"),
        ],
        "tip": "2.0의 **Govern**이 이전 1.1 Identify.Governance를 승격시킨 핵심 변화. 이사회 보고가 프레임워크에 공식 편입.",
    },
    "gdpr_pipa": {
        "name": "GDPR · 개인정보보호법",
        "role": "EU/한국 개인정보 보호 법제",
        "vm": "법무/컴플라이언스 문서",
        "access": "원문 + 개인정보보호위원회 고시",
        "dirs": [
            ("GDPR Art. 5 (원칙)", "목적 제한, 최소화, 정확성, 보관기한 제한"),
            ("GDPR Art. 32 (보안조치)", "암호화, 기밀성, 무결성"),
            ("개인정보법 제29조", "안전조치 의무"),
        ],
        "config": [
            ("DPIA / PIA", "개인정보 영향평가"),
            ("DPO / CPO", "보호책임자"),
            ("72시간 유출 통지", "감독기관 보고 기한"),
        ],
        "logs": [
            ("처리 활동 기록부 (Art.30)", "처리 목적·항목·보관기간·수령자"),
        ],
        "ui": [
            ("https://gdpr.eu", "요약 해설"),
            ("https://www.pipc.go.kr", "한국 개인정보보호위원회"),
        ],
        "tip": "제재금: GDPR **최대 전세계 매출의 4%**, 한국은 **3%**. 증적 부재가 가장 흔한 지적이므로 처리 활동 기록부를 1순위로.",
    },

    # ── 과정5/7/10 (SOC · AI · 에이전트) ──
    "sigma_yara": {
        "name": "SIGMA + YARA",
        "role": "SIGMA=플랫폼 독립 탐지 룰, YARA=파일/메모리 시그니처",
        "vm": "SOC 분석가 PC / siem",
        "access": "`sigmac` 변환기, `yara <rule> <target>`",
        "dirs": [
            ("~/sigma/rules/", "SIGMA 룰 저장"),
            ("~/yara-rules/", "YARA 룰 저장"),
        ],
        "config": [
            ("SIGMA logsource:product/service", "로그 소스 매핑"),
            ("YARA `strings: $s1 = \"...\" ascii wide`", "시그니처 정의"),
            ("YARA `condition: all of them and filesize < 1MB`", "매칭 조건"),
        ],
        "logs": [],
        "ui": [
            ("`sigmac -t elasticsearch-qs rule.yml`", "Elastic용 KQL 변환"),
            ("`sigmac -t wazuh rule.yml`", "Wazuh XML 룰 변환"),
            ("`yara -r rules.yar /var/tmp/sample.bin`", "재귀 스캔"),
        ],
        "tip": "SIGMA는 *탐지 의도*, YARA는 *바이너리 패턴*으로 역할 분리. SIGMA 룰은 반드시 **false positive 조건**까지 기술해야 SIEM 운영 가능.",
    },
    "volatility": {
        "name": "Volatility 3",
        "role": "메모리 이미지 포렌식 프레임워크",
        "vm": "분석 PC",
        "access": "`vol -f mem.raw <plugin>`",
        "dirs": [
            ("volatility3/volatility3/plugins/", "플러그인 소스"),
            ("~/symbols/", "커널 심볼 캐시"),
        ],
        "config": [
            ("windows.pslist / linux.pslist", "프로세스 열거"),
            ("windows.malfind", "주입된 코드 탐지"),
            ("windows.netscan", "열린 소켓"),
        ],
        "logs": [],
        "ui": [
            ("`vol -f mem.raw windows.pstree`", "프로세스 트리"),
            ("`vol -f mem.raw windows.cmdline`", "실행된 명령행"),
            ("`vol -f mem.raw linux.bash`", "bash 히스토리 복원"),
        ],
        "tip": "Volatility 3은 **심볼 자동 다운로드**가 필요하므로 오프라인 분석 시 `--symbol-dirs`로 미리 준비. 샘플 복사 시 `md5sum`로 무결성 확인 필수.",
    },
    "ollama_langchain": {
        "name": "Ollama + LangChain",
        "role": "로컬 LLM 서빙(Ollama) + 체인 오케스트레이션(LangChain)",
        "vm": "bastion (LLM 서버)",
        "access": "`OLLAMA_HOST=http://10.20.30.201:11434`, Python `from langchain_ollama import OllamaLLM`",
        "dirs": [
            ("~/.ollama/models/", "다운로드된 모델 블롭"),
            ("/etc/systemd/system/ollama.service", "서비스 유닛"),
        ],
        "config": [
            ("OLLAMA_HOST=0.0.0.0:11434", "외부 바인드"),
            ("OLLAMA_KEEP_ALIVE=30m", "모델 유휴 유지"),
            ("LLM_MODEL=gemma3:4b (env)", "CCC 기본 모델"),
        ],
        "logs": [
            ("journalctl -u ollama", "서빙 로그"),
            ("LangChain `verbose=True`", "체인 단계 출력"),
        ],
        "ui": [
            ("`ollama list`", "설치된 모델"),
            ("`curl -XPOST $OLLAMA_HOST/api/generate -d '{...}'`", "REST 생성"),
            ("LangChain `RunnableSequence | parser`", "체인 조립 문법"),
        ],
        "tip": "Ollama는 **첫 호출에 모델 로드**가 커서 지연이 크다. 성능 실험 시 워밍업 호출을 배제하고 측정하자.",
    },
    "bastion": {
        "name": "CCC Bastion Agent",
        "role": "CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습",
        "vm": "bastion (10.20.30.201)",
        "access": "TUI `./dev.sh bastion`, API `http://localhost:8003`",
        "dirs": [
            ("packages/bastion/agent.py", "메인 에이전트 루프"),
            ("packages/bastion/skills.py", "스킬 정의"),
            ("packages/bastion/playbooks/", "정적 플레이북 YAML"),
            ("data/bastion/experience/", "수집된 경험 (pass/fail)"),
        ],
        "config": [
            ("LLM_BASE_URL / LLM_MODEL", "Ollama 연결"),
            ("CCC_API_KEY", "ccc-api 인증"),
            ("max_retry=2", "실패 시 self-correction 재시도"),
        ],
        "logs": [
            ("`docs/test-status.md`", "현재 테스트 진척 요약"),
            ("`bastion_test_progress.json`", "스텝별 pass/fail 원시"),
        ],
        "ui": [
            ("대화형 TUI 프롬프트", "자연어 지시 → 계획 → 실행 → 검증"),
            ("`/a2a/mission` (API)", "자율 미션 실행"),
            ("Experience→Playbook 승격", "반복 성공 패턴 저장"),
        ],
        "tip": "실패 시 output을 분석해 **근본 원인 교정**이 설계의 핵심. 증상 회피/땜빵은 금지.",
    },
    "shodan_osint": {
        "name": "Shodan + OSINT 도구",
        "role": "공개 인터넷 자산/메타데이터 수집",
        "vm": "공격자 측",
        "access": "Shodan CLI `shodan` / 웹 UI / API",
        "dirs": [
            ("~/.shodan/api_key", "저장된 API 키"),
        ],
        "config": [
            ("filter: `port:22 country:KR product:OpenSSH`", "쿼리 문법"),
            ("Censys.io", "TLS 지표 중심 — SAN/SNI 기반 자산 발견"),
        ],
        "logs": [],
        "ui": [
            ("`shodan search 'org:\"target\"'`", "조직 단위 노출 자산"),
            ("`shodan host <ip>`", "IP 상세 (배너·CVE)"),
            ("exiftool", "문서·이미지 메타데이터 (저자·SW·좌표)"),
        ],
        "tip": "Shodan 결과는 **캐시 기반**이라 최근 24h 내 변경을 반영하지 않을 수 있다. 실시간 확인은 직접 연결로 재검증.",
    },
    "bloodhound": {
        "name": "BloodHound + SharpHound",
        "role": "Active Directory 공격 경로 그래프 분석",
        "vm": "분석 PC (BloodHound GUI) + 도메인 호스트 (SharpHound)",
        "access": "`SharpHound.exe -c All` → `.zip` 업로드",
        "dirs": [
            ("BloodHound/customqueries.json", "커스텀 Cypher 쿼리"),
            ("Neo4j graph.db", "그래프 저장소"),
        ],
        "config": [
            ("Collection method: All / DCOnly", "수집 범위"),
            ("Edge: HasSession, AdminTo, DCSync", "권한 관계"),
        ],
        "logs": [],
        "ui": [
            ("`Shortest Paths to Domain Admins`", "핵심 공격 경로 쿼리"),
            ("`Find Kerberoastable Users`", "SPN 있는 사용자"),
        ],
        "tip": "SharpHound는 **EDR 탐지 1순위**. 합법 환경에서만 실행하고, 실전 모의에서는 Stealth 컬렉션 모드 사용.",
    },
    "c2_redis": {
        "name": "Sliver / Mythic (C2 프레임워크)",
        "role": "포스트-익스플로잇 명령·제어 서버·임플란트",
        "vm": "bastion(C2 서버) + 침투 대상(implant)",
        "access": "Sliver `sliver-server daemon` / `sliver` 클라이언트",
        "dirs": [
            ("/root/.sliver/", "프로필·인증서·임플란트 아티팩트"),
            ("/root/.sliver-client/", "오퍼레이터 설정"),
        ],
        "config": [
            ("mtls/http/dns listener", "통신 채널"),
            ("implant profile: jitter/interval", "비콘 간격·지터"),
        ],
        "logs": [
            ("sliver-server logs", "세션 접속·명령 기록"),
        ],
        "ui": [
            ("`generate --http https://c2:8443 --os linux --arch amd64 -s implant`", "임플란트 빌드"),
            ("`sessions` / `use <id>`", "세션 관리"),
            ("`pivots` / `portfwd`", "횡적 이동"),
        ],
        "tip": "dual-use. **합법 점검 범위·서면 동의** 없이는 절대 실행 금지. 실습은 격리된 10.20.30.0/24 대역 한정.",
    },
    "wireshark_tshark": {
        "name": "Wireshark · tshark",
        "role": "네트워크 패킷 분석 GUI/CLI",
        "vm": "분석 PC",
        "access": "`wireshark` GUI / `tshark -r <pcap>`",
        "dirs": [
            ("~/.config/wireshark/preferences", "컬럼·디코더 설정"),
        ],
        "config": [
            ("Display filter `http.request.method == POST`", "디코드 후 필터"),
            ("Capture filter `tcp port 80` (BPF)", "커널 레벨 필터"),
        ],
        "logs": [],
        "ui": [
            ("Statistics → Conversations", "호스트·포트 쌍 통계"),
            ("Follow → TLS Stream", "세션 재구성 (키 제공 시 복호화)"),
            ("File → Export Objects → HTTP", "업/다운로드 파일 복원"),
        ],
        "tip": "TLS 1.3 트래픽은 **세션 키 로깅(SSLKEYLOGFILE)** 없이는 복호화 불가. 브라우저에서 `export SSLKEYLOGFILE=...` 후 캡처.",
    },
    "fail2ban": {
        "name": "fail2ban",
        "role": "로그 패턴 매칭 자동 IP 차단",
        "vm": "web/secu/siem",
        "access": "`systemctl status fail2ban`, `fail2ban-client`",
        "dirs": [
            ("/etc/fail2ban/jail.local", "운영자 jail 설정"),
            ("/etc/fail2ban/filter.d/", "failregex 정의"),
            ("/var/log/fail2ban.log", "밴/언밴 이력"),
        ],
        "config": [
            ("[sshd] enabled=true maxretry=3 findtime=10m bantime=1h", "표준 SSH jail"),
            ("action = nftables-multiport[...]", "실제 차단은 nftables 연동"),
        ],
        "logs": [
            ("`fail2ban-client status sshd`", "현재 밴 IP 목록"),
        ],
        "ui": [
            ("`fail2ban-client set sshd banip <ip>`", "수동 밴"),
            ("`fail2ban-regex auth.log /etc/fail2ban/filter.d/sshd.conf`", "필터 검증"),
        ],
        "tip": "로그 로테이션으로 파일이 갱신되면 **inode 추적 문제**로 탐지 누락 가능 — `logpath` 복수 지정과 `backend=systemd` 고려.",
    },
    "report_cvss": {
        "name": "보고서 도구 (CVSS 계산기·Markdown·ReportLab)",
        "role": "취약점 보고서 표준화",
        "vm": "작업 PC",
        "access": "FIRST CVSS 계산기 https://www.first.org/cvss/calculator/3.1",
        "dirs": [
            ("reports/<project>/", "재현 스크린샷·증적 저장"),
            ("template.md / template.docx", "표준 템플릿"),
        ],
        "config": [
            ("CVSS 3.1 벡터 예: AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "Critical 9.8"),
            ("CWE ID + 권고 (remediation)", "보고서 필수 항목"),
        ],
        "logs": [],
        "ui": [
            ("MermaidJS 공격 흐름도", "교안/보고서 공통 도식"),
            ("Pandoc `md → docx/pdf`", "포맷 변환"),
        ],
        "tip": "보고서 가치는 **재현 절차의 완결성**에 달려 있다. 스크린샷·요청/응답 전체·시간 기록을 포함해야 고객이 독립 검증 가능.",
    },
}

# ───────────────────────── (course, week) → solution keys ─────────────────────────
# 값이 빈 배열이면 실습 참조 섹션을 **붙이지 않는다** (솔루션 초점이 아님).
PLAN: dict[tuple[str, int], list[str]] = {
    # Course 1: attack — 웹해킹/침투
    ("course1-attack", 1): [],
    ("course1-attack", 2): ["nmap"],
    ("course1-attack", 3): ["burp", "jwt_tools"],
    ("course1-attack", 4): ["sqlmap", "burp"],
    ("course1-attack", 5): ["burp", "zap"],
    ("course1-attack", 6): ["jwt_tools", "burp"],
    ("course1-attack", 7): ["burp"],
    ("course1-attack", 8): ["burp", "sqlmap"],
    ("course1-attack", 9): ["nmap", "tcpdump_wireshark"],
    ("course1-attack", 10): ["suricata"],
    ("course1-attack", 11): ["linpeas"],
    ("course1-attack", 12): [],
    ("course1-attack", 13): [],
    ("course1-attack", 14): ["bastion"],
    ("course1-attack", 15): ["report_cvss", "bastion"],
    # Course 2: security-ops
    ("course2-security-ops", 1): ["nftables", "suricata", "bunkerweb", "wazuh", "opencti"],
    ("course2-security-ops", 2): ["nftables"],
    ("course2-security-ops", 3): ["nftables"],
    ("course2-security-ops", 4): ["suricata"],
    ("course2-security-ops", 5): ["suricata"],
    ("course2-security-ops", 6): ["suricata"],
    ("course2-security-ops", 7): ["bunkerweb"],
    ("course2-security-ops", 8): ["nftables", "suricata"],
    ("course2-security-ops", 9): ["wazuh"],
    ("course2-security-ops", 10): ["wazuh"],
    ("course2-security-ops", 11): ["wazuh"],
    ("course2-security-ops", 12): ["opencti"],
    ("course2-security-ops", 13): ["opencti"],
    ("course2-security-ops", 14): ["nftables", "suricata", "bunkerweb", "wazuh", "opencti"],
    ("course2-security-ops", 15): ["nftables", "suricata", "bunkerweb", "wazuh", "opencti"],
    # Course 3: web-vuln
    ("course3-web-vuln", 1): [],
    ("course3-web-vuln", 2): ["burp", "zap", "gobuster_nikto", "sqlmap"],
    ("course3-web-vuln", 3): ["gobuster_nikto"],
    ("course3-web-vuln", 4): ["burp"],
    ("course3-web-vuln", 5): ["sqlmap", "burp"],
    ("course3-web-vuln", 6): ["burp", "zap"],
    ("course3-web-vuln", 7): ["burp"],
    ("course3-web-vuln", 8): ["burp", "sqlmap", "zap"],
    ("course3-web-vuln", 9): ["burp"],
    ("course3-web-vuln", 10): ["burp"],
    ("course3-web-vuln", 11): ["burp"],
    ("course3-web-vuln", 12): ["burp", "zap"],
    ("course3-web-vuln", 13): ["zap"],
    ("course3-web-vuln", 14): ["report_cvss"],
    ("course3-web-vuln", 15): ["report_cvss", "zap", "burp"],
    # Course 4: compliance
    ("course4-compliance", 1): [],
    ("course4-compliance", 2): ["iso27001"],
    ("course4-compliance", 3): ["iso27001"],
    ("course4-compliance", 4): ["iso27001"],
    ("course4-compliance", 5): ["ismsp"],
    ("course4-compliance", 6): ["ismsp"],
    ("course4-compliance", 7): ["nist_csf"],
    ("course4-compliance", 8): ["iso27001", "ismsp"],
    ("course4-compliance", 9): ["gdpr_pipa"],
    ("course4-compliance", 10): ["iso27001"],
    ("course4-compliance", 11): ["iso27001", "ismsp"],
    ("course4-compliance", 12): ["iso27001"],
    ("course4-compliance", 13): ["nist_csf"],
    ("course4-compliance", 14): ["iso27001", "ismsp"],
    ("course4-compliance", 15): ["iso27001", "ismsp", "nist_csf"],
    # Course 5: soc
    ("course5-soc", 1): ["wazuh"],
    ("course5-soc", 2): ["wazuh"],
    ("course5-soc", 3): ["suricata", "wazuh"],
    ("course5-soc", 4): ["wazuh"],
    ("course5-soc", 5): ["wazuh"],
    ("course5-soc", 6): ["wazuh", "sigma_yara"],
    ("course5-soc", 7): ["sigma_yara"],
    ("course5-soc", 8): ["wazuh", "sigma_yara"],
    ("course5-soc", 9): ["wazuh"],
    ("course5-soc", 10): ["wazuh", "sqlmap"],
    ("course5-soc", 11): ["wazuh", "volatility"],
    ("course5-soc", 12): ["wazuh"],
    ("course5-soc", 13): ["opencti", "wazuh"],
    ("course5-soc", 14): ["bastion", "wazuh"],
    ("course5-soc", 15): ["wazuh", "opencti", "bastion"],
    # Course 6: cloud-container
    ("course6-cloud-container", 1): ["docker"],
    ("course6-cloud-container", 2): ["docker", "dockerfile_secure"],
    ("course6-cloud-container", 3): ["trivy", "dockerfile_secure"],
    ("course6-cloud-container", 4): ["docker"],
    ("course6-cloud-container", 5): ["docker"],
    ("course6-cloud-container", 6): ["docker", "dockerfile_secure"],
    ("course6-cloud-container", 7): ["docker_bench", "trivy"],
    ("course6-cloud-container", 8): ["docker", "docker_bench", "trivy"],
    ("course6-cloud-container", 9): [],
    ("course6-cloud-container", 10): [],
    ("course6-cloud-container", 11): ["kubernetes"],
    ("course6-cloud-container", 12): ["kubernetes"],
    ("course6-cloud-container", 13): [],
    ("course6-cloud-container", 14): ["trivy"],
    ("course6-cloud-container", 15): ["kubernetes", "trivy", "kube_bench_falco"],
    # Course 7: ai-security
    ("course7-ai-security", 1): ["ollama_langchain"],
    ("course7-ai-security", 2): ["ollama_langchain"],
    ("course7-ai-security", 3): ["ollama_langchain"],
    ("course7-ai-security", 4): ["ollama_langchain", "wazuh"],
    ("course7-ai-security", 5): ["ollama_langchain", "sigma_yara"],
    ("course7-ai-security", 6): ["ollama_langchain"],
    ("course7-ai-security", 7): ["ollama_langchain", "bastion"],
    ("course7-ai-security", 8): ["ollama_langchain", "wazuh"],
    ("course7-ai-security", 9): ["bastion"],
    ("course7-ai-security", 10): ["bastion"],
    ("course7-ai-security", 11): ["bastion"],
    ("course7-ai-security", 12): ["bastion", "wazuh"],
    ("course7-ai-security", 13): ["bastion", "ollama_langchain"],
    ("course7-ai-security", 14): ["bastion"],
    ("course7-ai-security", 15): ["bastion", "ollama_langchain"],
    # Course 8: ai-safety
    ("course8-ai-safety", 1): ["ollama_langchain"],
    ("course8-ai-safety", 2): ["ollama_langchain"],
    ("course8-ai-safety", 3): ["ollama_langchain"],
    ("course8-ai-safety", 4): ["ollama_langchain"],
    ("course8-ai-safety", 5): ["ollama_langchain"],
    ("course8-ai-safety", 6): ["ollama_langchain"],
    ("course8-ai-safety", 7): ["ollama_langchain"],
    ("course8-ai-safety", 8): ["ollama_langchain"],
    ("course8-ai-safety", 9): ["ollama_langchain"],
    ("course8-ai-safety", 10): ["ollama_langchain", "bastion"],
    ("course8-ai-safety", 11): ["ollama_langchain"],
    ("course8-ai-safety", 12): [],
    ("course8-ai-safety", 13): ["ollama_langchain"],
    ("course8-ai-safety", 14): ["ollama_langchain"],
    ("course8-ai-safety", 15): ["ollama_langchain"],
    # Course 9: autonomous-security
    ("course9-autonomous-security", 1): ["bastion"],
    ("course9-autonomous-security", 2): ["ollama_langchain", "bastion"],
    ("course9-autonomous-security", 3): ["bastion"],
    ("course9-autonomous-security", 4): ["bastion"],
    ("course9-autonomous-security", 5): ["bastion"],
    ("course9-autonomous-security", 6): ["bastion"],
    ("course9-autonomous-security", 7): ["bastion"],
    ("course9-autonomous-security", 8): ["bastion"],
    ("course9-autonomous-security", 9): ["bastion"],
    ("course9-autonomous-security", 10): ["bastion"],
    ("course9-autonomous-security", 11): ["bastion", "wazuh"],
    ("course9-autonomous-security", 12): ["bastion", "nmap"],
    ("course9-autonomous-security", 13): ["bastion", "ollama_langchain"],
    ("course9-autonomous-security", 14): ["bastion"],
    ("course9-autonomous-security", 15): ["bastion"],
    # Course 10: ai-security-agent
    ("course10-ai-security-agent", 1): ["bastion", "ollama_langchain"],
    ("course10-ai-security-agent", 2): ["ollama_langchain"],
    ("course10-ai-security-agent", 3): ["ollama_langchain"],
    ("course10-ai-security-agent", 4): ["bastion"],
    ("course10-ai-security-agent", 5): ["bastion"],
    ("course10-ai-security-agent", 6): ["bastion", "wazuh"],
    ("course10-ai-security-agent", 7): ["bastion"],
    ("course10-ai-security-agent", 8): ["bastion"],
    ("course10-ai-security-agent", 9): ["bastion"],
    ("course10-ai-security-agent", 10): ["bastion"],
    ("course10-ai-security-agent", 11): ["bastion", "wazuh"],
    ("course10-ai-security-agent", 12): ["bastion"],
    ("course10-ai-security-agent", 13): ["bastion", "ollama_langchain"],
    ("course10-ai-security-agent", 14): ["bastion"],
    ("course10-ai-security-agent", 15): ["bastion"],
    # Course 11: battle
    ("course11-battle", 1): ["nmap"],
    ("course11-battle", 2): ["nmap", "gobuster_nikto"],
    ("course11-battle", 3): ["sqlmap", "burp"],
    ("course11-battle", 4): ["hydra_hashcat"],
    ("course11-battle", 5): ["linpeas"],
    ("course11-battle", 6): ["nftables"],
    ("course11-battle", 7): ["suricata"],
    ("course11-battle", 8): ["wazuh", "sigma_yara"],
    ("course11-battle", 9): ["wazuh"],
    ("course11-battle", 10): ["nftables", "wazuh"],
    ("course11-battle", 11): ["nmap", "wazuh"],
    ("course11-battle", 12): ["sqlmap", "wazuh", "fail2ban"],
    ("course11-battle", 13): ["bastion"],
    ("course11-battle", 14): ["bastion", "wazuh"],
    ("course11-battle", 15): ["report_cvss"],
    # Course 12: battle-advanced
    ("course12-battle-advanced", 1): [],
    ("course12-battle-advanced", 2): ["metasploit", "linpeas"],
    ("course12-battle-advanced", 3): ["c2_redis"],
    ("course12-battle-advanced", 4): ["bloodhound"],
    ("course12-battle-advanced", 5): [],
    ("course12-battle-advanced", 6): ["suricata", "fail2ban"],
    ("course12-battle-advanced", 7): ["volatility"],
    ("course12-battle-advanced", 8): ["sigma_yara", "wazuh"],
    ("course12-battle-advanced", 9): ["bastion", "ollama_langchain"],
    ("course12-battle-advanced", 10): ["bastion"],
    ("course12-battle-advanced", 11): ["report_cvss"],
    ("course12-battle-advanced", 12): ["wazuh", "bastion"],
    ("course12-battle-advanced", 13): ["bastion", "wazuh"],
    ("course12-battle-advanced", 14): ["bastion"],
    ("course12-battle-advanced", 15): ["report_cvss", "bastion"],
    # Course 13: attack-advanced
    ("course13-attack-advanced", 1): [],
    ("course13-attack-advanced", 2): ["shodan_osint", "nmap"],
    ("course13-attack-advanced", 3): ["nmap", "suricata"],
    ("course13-attack-advanced", 4): ["burp"],
    ("course13-attack-advanced", 5): ["bloodhound"],
    ("course13-attack-advanced", 6): ["linpeas"],
    ("course13-attack-advanced", 7): ["c2_redis"],
    ("course13-attack-advanced", 8): ["bloodhound"],
    ("course13-attack-advanced", 9): ["bloodhound"],
    ("course13-attack-advanced", 10): [],
    ("course13-attack-advanced", 11): [],
    ("course13-attack-advanced", 12): [],
    ("course13-attack-advanced", 13): [],
    ("course13-attack-advanced", 14): ["report_cvss", "bastion"],
    ("course13-attack-advanced", 15): ["report_cvss"],
    # Course 14: soc-advanced
    ("course14-soc-advanced", 1): [],
    ("course14-soc-advanced", 2): ["wazuh"],
    ("course14-soc-advanced", 3): ["sigma_yara"],
    ("course14-soc-advanced", 4): ["sigma_yara"],
    ("course14-soc-advanced", 5): ["opencti"],
    ("course14-soc-advanced", 6): ["wazuh", "sigma_yara"],
    ("course14-soc-advanced", 7): ["wireshark_tshark", "suricata"],
    ("course14-soc-advanced", 8): ["volatility"],
    ("course14-soc-advanced", 9): ["sigma_yara", "volatility"],
    ("course14-soc-advanced", 10): ["bastion", "wazuh"],
    ("course14-soc-advanced", 11): ["wazuh", "volatility"],
    ("course14-soc-advanced", 12): ["wazuh"],
    ("course14-soc-advanced", 13): ["bastion"],
    ("course14-soc-advanced", 14): ["bastion", "ollama_langchain"],
    ("course14-soc-advanced", 15): ["bastion", "wazuh"],
    # Course 15: ai-safety-advanced
    ("course15-ai-safety-advanced", 1): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 2): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 3): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 4): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 5): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 6): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 7): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 8): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 9): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 10): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 11): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 12): [],
    ("course15-ai-safety-advanced", 13): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 14): ["ollama_langchain"],
    ("course15-ai-safety-advanced", 15): ["ollama_langchain"],
    # Course 18: autonomous-systems (있는 만큼)
    ("course18-autonomous-systems", 1): ["bastion"],
}


# ───────────────────────── 섹션 빌더 ─────────────────────────
MARKER = "## 📂 실습 참조 파일 가이드"


def render_card(key: str) -> str:
    """솔루션 1건을 ## 섹션 아래 ### 카드로 렌더."""
    if key not in SOL:
        return ""
    s = SOL[key]
    lines: list[str] = []
    lines.append(f"### {s['name']}")
    lines.append(f"> **역할:** {s['role']}  ")
    lines.append(f"> **실행 위치:** `{s['vm']}`  ")
    lines.append(f"> **접속/호출:** {s['access']}")
    lines.append("")
    if s.get("dirs"):
        lines.append("**주요 경로·파일**")
        lines.append("")
        lines.append("| 경로 | 역할 |")
        lines.append("|------|------|")
        for p, desc in s["dirs"]:
            lines.append(f"| `{p}` | {desc} |")
        lines.append("")
    if s.get("config"):
        lines.append("**핵심 설정·키**")
        lines.append("")
        for k, desc in s["config"]:
            lines.append(f"- `{k}` — {desc}")
        lines.append("")
    if s.get("logs"):
        lines.append("**로그·확인 명령**")
        lines.append("")
        for cmd, desc in s["logs"]:
            lines.append(f"- `{cmd}` — {desc}")
        lines.append("")
    if s.get("ui"):
        lines.append("**UI / CLI 요점**")
        lines.append("")
        for cmd, desc in s["ui"]:
            lines.append(f"- {cmd} — {desc}")
        lines.append("")
    if s.get("tip"):
        lines.append(f"> **해석 팁.** {s['tip']}")
        lines.append("")
    return "\n".join(lines)


def build_section(keys: list[str]) -> str:
    if not keys:
        return ""
    blocks = [render_card(k) for k in keys if k in SOL]
    blocks = [b for b in blocks if b]
    if not blocks:
        return ""
    header = (
        "\n---\n\n"
        f"{MARKER}\n\n"
        "> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.\n\n"
    )
    return header + "\n".join(blocks) + "\n"


# ───────────────────────── 기존 섹션 제거 ─────────────────────────
SECTION_RE = re.compile(
    r"\n?---\n+## 📂 실습 참조 파일 가이드\b.*?(?=\n##\s|\n---\n+##\s|\Z)",
    re.DOTALL,
)


def strip_old(content: str) -> tuple[str, bool]:
    new, n = SECTION_RE.subn("\n", content)
    if n > 0:
        new = re.sub(r"\n{3,}", "\n\n", new).rstrip() + "\n"
    return new, n > 0


# ───────────────────────── 메인 ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course", nargs="?")
    ap.add_argument("week", nargs="?", type=str)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = []
    for (course, week), keys in PLAN.items():
        if args.course and course != args.course:
            continue
        if args.week:
            want = args.week.lstrip("week").lstrip("0") or "0"
            if str(week) != want:
                continue
        targets.append((course, week, keys))

    updated = 0
    stripped_only = 0
    for course, week, keys in targets:
        path = os.path.join(EDU, course, f"week{week:02d}", "lecture.md")
        if not os.path.exists(path):
            continue
        content = open(path, encoding="utf-8").read()
        content, stripped = strip_old(content)
        section = build_section(keys)
        if section:
            content = content.rstrip() + "\n" + section
        changed = stripped or bool(section)
        if not changed:
            continue
        if args.dry_run:
            print(f"[DRY] {course}/week{week:02d}: stripped={stripped} +cards={len(keys)}")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if keys:
            updated += 1
        else:
            stripped_only += 1
        print(f"{course}/week{week:02d}: stripped={stripped} cards={len(keys)}")

    print(f"\nDone. updated={updated} stripped_only={stripped_only} total={updated+stripped_only}")


if __name__ == "__main__":
    main()
