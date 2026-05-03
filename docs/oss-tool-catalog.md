# CCC 학습 OSS 도구 종합 카탈로그

**작성일**: 2026-05-02  
**범위**: course1~14 detailed + course15-20 압축 매트릭스 + attacker VM 실제 설치 도구  
**합계**: **150+ OSS 도구**

---

## 1. 실제 설치 완료 (attacker VM 192.168.0.112)

| # | 도구 | 분류 | 용도 |
|---|------|------|------|
| 1 | whatweb | recon | 웹 기술 스택 자동 식별 |
| 2 | nikto | scan | 웹 vuln 자동 점검 |
| 3 | sqlmap | exploit | SQLi 자동 |
| 4 | ffuf | fuzz | 디렉토리/API fuzzing |
| 5 | nuclei | scan | 신호 정확도 높은 vuln |
| 6 | gobuster | fuzz | dir/dns brute |
| 7 | hydra | brute | 50+ 프로토콜 brute |
| 8 | sslscan | tls | TLS cipher 점검 |
| 9 | dirb | fuzz | dir brute (간단) |
| 10 | httpie | http | 사람 친화 HTTP |
| 11 | jq | json | JSON 검색 표준 |
| 12 | wafw00f | recon | WAF 식별 |
| 13 | ab (Apache Bench) | perf | HTTP 성능 측정 |
| 14 | testssl.sh | tls | TLS 종합 진단 |
| 15 | XSStrike | exploit | XSS 자동 점검 |

---

## 2. Course1 - Attack (정찰부터 종합 모의해킹)

### 2.1 Reconnaissance
- **nmap** / **masscan** / **unicornscan** — 포트 스캐닝
- **fping** / **arp-scan** / **netdiscover** — 호스트 발견
- **dig** / **nslookup** / **dnsrecon** / **amass** / **subfinder** / **sublist3r** — DNS / subdomain
- **theHarvester** / **sherlock** / **maigret** / **SpiderFoot** — OSINT

### 2.2 Scanning
- **nmap NSE** / **vulscan** / **nmap-vulners** — vuln 스크립트
- **nikto** / **wapiti** — 웹 vuln 종합
- **dirb** / **gobuster** / **ffuf** / **dirsearch** — dir brute

### 2.3 Web Exploit
- **sqlmap** — SQLi 자동
- **XSStrike** / **dalfox** — XSS 자동
- **jwt_tool** — JWT 점검
- **xsrfprobe** — CSRF
- **dotdotpwn** — Path traversal
- **weevely** / **fuxploider** — 파일 업로드 / webshell

### 2.4 Authentication
- **hydra** / **medusa** / **ncrack** / **patator** — online brute
- **john (Ripper)** / **hashcat** / **hashid** — hash crack
- **kerbrute** — Kerberos enum
- **ssh-audit** — SSH 점검

### 2.5 Network
- **tcpdump** / **tshark** / **wireshark** / **termshark** — 패킷 캡처
- **ettercap** / **bettercap** / **mitmproxy** / **dsniff** — MITM
- **scapy** / **nemesis** / **hping3** — 패킷 조작
- **tcpreplay** / **tcpflow** — pcap 재생/분석
- **ngrep** — 네트워크 grep

### 2.6 System Exploit / Post-Exploit
- **metasploit-framework** — exploit 통합
- **searchsploit** / **exploit-db** — exploit 검색
- **msfvenom** — payload 생성
- **sliver** / **Mythic** / **Havoc** / **Empire** — modern OSS C2
- **pwncat-cs** / **socat** — netcat 후속
- **shellter** / **veil-evasion** / **donut** — payload 인코딩

### 2.7 Privilege Escalation
- **LinPEAS** / **WinPEAS** — 자동 enum (PEASS-ng)
- **lse.sh** — Linux smart enum
- **linux-exploit-suggester** / **windows-exploit-suggester** — 커널 매칭
- **pspy** / **pspy64** — 비루트 process 모니터
- **GTFOBins** / **gtfobins-cli** — sudo/SUID 매핑
- **deepce** / **CDK** — Container breakout

### 2.8 Lateral Movement
- **OpenSSH** (`-L`/`-D`/`-J`) — port forwarding / jump
- **chisel** — HTTP tunnel
- **sshuttle** — VPN-like transparent proxy
- **proxychains4** — SOCKS chain
- **autossh** — persistent SSH tunnel
- **netexec (nxc)** — modern CME
- **evil-winrm** — Win 인증 lateral
- **impacket** suite — psexec/wmiexec/smbexec/secretsdump
- **BloodHound** / **bloodhound-python** — AD path 매핑
- **certipy** — AD CS abuse

### 2.9 Persistence
- **crontab** / **at** / **systemd-timer** — 스케줄링
- **weevely** — PHP webshell (난독화)
- **osquery** — persistence 자동 점검 (방어)
- **chkrootkit** / **rkhunter** — rootkit 탐지 (방어)
- **AIDE** / **Tripwire** — 무결성 baseline

### 2.10 Wireless (Course1 Week13)
- **aircrack-ng** suite — WPA crack 표준
- **wifite** — 자동화
- **kismet** — passive sniffing
- **reaver** / **bully** — WPS 공격
- **hostapd** — Evil Twin
- **fluxion** / **airgeddon** / **WiFi-Pumpkin3** — 통합 도구
- **hcxdumptool** / **hcxtools** — PMKID 공격

### 2.11 Social Engineering
- **gophish** — 캠페인 플랫폼
- **SET (Social-Engineer Toolkit)** — 종합
- **evilginx2** / **Modlishka** — MFA 우회
- **swaks** / **msmtp** — SMTP 테스트
- **qrencode** — QR 피싱

---

## 3. Course2 - Security Operations (방어 인프라)

### 3.1 Firewall
- **nftables** (`nft`) — modern Linux FW
- **iptables-nftables-compat** — 호환
- **fail2ban** — 동적 차단
- **crowdsec** — community CTI 기반 자동 차단
- **conntrack** — 연결 추적
- **ulogd2** — userspace logging

### 3.2 IDS/IPS
- **Suricata** — 표준
- **Snort3** — 대안
- **Zeek** — 프로토콜 분석
- **suricata-update** — 룰셋 자동
- **evebox** — Suricata GUI
- **scirius** (SELKS) — Web UI
- **suricatasc** — Unix socket 제어

### 3.3 WAF
- **ModSecurity v3** + **OWASP CRS** — Apache/nginx
- **Coraza** (Go, modern OSS)
- **NAXSI** — nginx 전용
- **go-ftw** — CRS 테스트 러너

### 3.4 SIEM
- **Wazuh** (manager / indexer / dashboard) — 종합 SIEM
- **OSSEC** — Wazuh 원본
- **OpenSearch** — Elastic 후속 (Wazuh 통합)
- **Graylog** — 대안
- **Falco** — kernel-level (eBPF)

### 3.5 CTI
- **OpenCTI** — modern CTI
- **MISP** — 사실상 OSS CTI 표준
- **TheHive 5** — 사고 케이스
- **Cortex** — analyzer + responder
- **pycti** / **pymisp** — Python SDK
- **Sigma** — universal SIEM rule
- **pysigma** + **sigma-cli** — 변환

### 3.6 Automation / SOAR
- **Shuffle** — modern OSS SOAR
- **n8n** — workflow
- **StackStorm** — 대안
- **Atomic Red Team** — adversary emulation
- **CALDERA** (MITRE) — APT 시뮬

### 3.7 Compliance / Audit
- **Lynis** — UNIX 보안 표준
- **OpenSCAP** + **scap-security-guide** — NIST SCAP
- **chef-inspec** — InSpec 표준
- **AIDE** / **Tripwire** — FIM
- **auditd** + **ausearch** + **aureport** — Linux audit

### 3.8 Logging Pipeline
- **rsyslog** / **syslog-ng** — 표준
- **Filebeat** / **Fluent Bit** / **vector.dev** — modern forwarders

---

## 4. Course3 - Web Vulnerability

### 4.1 추가 도구 (위 + 새로움)
- **whatweb** / **httpie** — 헤더/기술 식별
- **wfuzz** — fuzz 표준
- **wapiti** — 웹 vuln 자동
- **Burp Suite Community** — 프록시 (수동)
- **OWASP ZAP** + **zap-baseline** — DAST
- **dirsearch** — dir brute (Python)
- **commix** — Command injection
- **smuggler** — HTTP smuggling
- **SSRFmap** — SSRF
- **xxe-injection-payload-list** — XXE
- **bolt** — CSRF scanner

---

## 5. Course4 - Compliance

- **Lynis** / **OpenSCAP** / **chef-inspec** / **Wazuh SCA** — 점검
- **Presidio** (Microsoft) / **scrubadub** / **pii-codex** — PII
- **opacus** (Meta) / **TF Privacy** / **pydp** — DP
- **eramba** / **simplerisk** — GRC
- **HashiCorp Vault** OSS — 키 관리
- **sops** / **age** / **sealed-secrets** — secret 암호화
- **gophish** + **Moodle** — 보안 교육
- **DefectDojo** — vuln tracker
- **Prowler** / **scout-suite** / **CloudSploit** — Cloud 점검
- **kube-bench** / **kubescape** / **Polaris** — K8s 점검
- **chef-inspec** + **AIDE** + **restic** — SOX IT 통제

---

## 6. Course5 - SOC

- **Wazuh** + **Filebeat** + **OpenSearch** — SIEM
- **velociraptor** — endpoint forensic
- **chainsaw** (Rust) — Sigma 헌팅
- **hayabusa** — Win EVTX 헌팅
- **kestrel-lang** — 가설 헌팅
- **osquery** — SQL 형 시스템 조회
- **Volatility 3** / **Rekall** — 메모리
- **Sleuth Kit (TSK)** + **Autopsy** — 디스크
- **Plaso (log2timeline)** — universal timeline
- **LiME** / **AVML** — 메모리 capture
- **yara** + **signature-base** + **Loki** — 악성 시그니처
- **radare2** + **ghidra** + **cutter** — 디스어셈블
- **Cuckoo Sandbox** — dynamic 분석
- **Frida** — runtime instrumentation

---

## 7. Course6 - Cloud / Container

### 7.1 Container
- **Docker** / **Podman** / **containerd** / **CRI-O** — 런타임
- **firecracker** (AWS) / **gVisor** (Google) / **Kata Containers** — 강한 격리
- **Trivy** — CVE + IaC + SBOM 통합 (사실상 표준)
- **Grype** + **Syft** (Anchore) — CVE + SBOM
- **hadolint** — Dockerfile lint
- **dockle** — Dockerfile + image 보안
- **dive** — image layer 시각화
- **docker-bench-security** — CIS Docker

### 7.2 Kubernetes
- **kube-bench** (Aqua) — CIS K8s
- **kubescape** — NSA + MITRE + CIS + PCI 통합
- **Polaris** (Fairwinds) — best practice
- **kube-hunter** — 공격 시뮬
- **OPA Gatekeeper** / **Kyverno** / **Datree** — admission control
- **Falco** + **Tracee** + **Tetragon** — runtime
- **Velero** + **restic** — 백업
- **Sealed Secrets** + **External Secrets Operator** + **SOPS** — secret

### 7.3 Cloud
- **Prowler** — AWS / Azure / GCP 종합
- **scout-suite** — multi-cloud
- **CloudCustodian (c7n)** — 정책 자동
- **LocalStack** — AWS 모방 환경
- **Pacu** — AWS pentest
- **Steampipe** — SQL 형 cloud 조회
- **iamlive** — IAM 정책 자동 생성

### 7.4 IAM
- **Keycloak** (RH SSO) / **Authelia** / **Authentik** / **Dex** — IdP
- **OPA** / **Casbin** / **Cedar** (AWS OSS) — 정책
- **Vault** (HashiCorp OSS) — secret + 동적 자격증명
- **rbac-tool** / **kubectl-who-can** / **rakkess** — K8s RBAC 분석

### 7.5 Network (CNI / Mesh)
- **Cilium** (eBPF) — modern CNI
- **Calico** — 가장 대중
- **Istio** / **Linkerd** — Service Mesh
- **Hubble** (Cilium) — 트래픽 가시성

### 7.6 CI/CD
- **gitleaks** / **trufflehog** / **detect-secrets** — secret
- **Semgrep** / **Bandit** / **CodeQL** — SAST
- **OWASP ZAP** — DAST
- **checkov** / **tfsec** / **kics** / **terrascan** — IaC
- **cosign** + **sigstore** — 서명
- **Argo CD** / **Flux CD** — GitOps

### 7.7 Observability
- **Prometheus** + **node_exporter** + **kube-state-metrics**
- **Grafana** + **Loki** + **Promtail**
- **Jaeger** / **Tempo** — trace
- **OpenTelemetry** — universal
- **Pixie** — eBPF (Datadog 처럼, OSS)

---

## 8. Course7 - AI Security (LLM)

### 8.1 LLM Hosting
- **Ollama** — 가장 단순 (로컬)
- **vLLM** — production GPU
- **TGI** (HuggingFace) — 대안
- **llama.cpp** — CPU 양자화
- **Open WebUI** (구 ollama-webui) — Web GUI
- **LobeChat** — 대안 GUI
- **LiteLLM** proxy — multi-LLM gateway
- **Helicone-OSS** — gateway 대안

### 8.2 Prompt Engineering / Eval
- **LangChain** + **LangGraph** — chain
- **AutoGen** (MS) / **CrewAI** / **MetaGPT** — multi-agent
- **DSPy** (Stanford) — 프롬프트 자동 최적화
- **promptfoo** — 자동 평가
- **OpenAI Evals** — 평가 표준
- **DeepEval** — 단위 테스트
- **Ragas** / **TruLens** — RAG quality
- **lm-eval-harness** (EleutherAI) — 벤치
- **HELM** (Stanford) — 종합

### 8.3 Red Team
- **garak** (NVIDIA) — LLM 보안 점검 표준
- **PyRIT** (Microsoft) — multi-turn
- **HarmBench** / **AdvBench** / **JailbreakBench** — 벤치
- **AutoDAN** / **GCG** / **PAIR** / **TAP** — 자동 jailbreak
- **TextAttack** / **OpenAttack** — 적대적 NLP
- **promptfoo redteam** — 통합

### 8.4 Defense / Guardrail
- **llm-guard** — 입출력 필터 (OWASP LLM Top 10)
- **Rebuff** — canary token + heuristic
- **NeMo Guardrails** (NVIDIA) — 정책 강제
- **guardrails-ai** — 출력 schema
- **outlines** — 정규식/JSON 강제
- **instructor** — function calling 강제
- **Marvin** — Pydantic + LLM
- **Lakera Guard** OSS-eval

### 8.5 Privacy / DP
- **Microsoft Presidio** — PII 탐지/마스킹
- **scrubadub** — 빠른 PII 마스킹
- **opacus** — DP-SGD
- **Flower** + **FedML** + **OpenFL** — Federated Learning
- **TenSEAL** / **Concrete-ML** — 동형암호
- **MarkLLM** / **lm-watermarking** — 워터마킹

### 8.6 Adversarial / Robustness
- **TextAttack** — NLP
- **advtorch** — PyTorch
- **IBM ART** (Adversarial Robustness Toolbox) — 통합
- **Foolbox** / **CleverHans** — 대안
- **RobustBench** — 벤치
- **smoothing** — Certified Robustness

### 8.7 Interpretability
- **SHAP** / **LIME** / **Captum** — feature attribution
- **TransformerLens** — Transformer 내부
- **sae-lens** — Sparse Autoencoders
- **circuitsvis** — attention 시각화
- **DiCE** — Counterfactual

### 8.8 Monitoring / Observability
- **Langfuse** (OSS LangSmith 대안) — trace + cost
- **Phoenix-Arize** — 시각화 강력
- **OpenLLMetry** (Traceloop) — OpenTelemetry-based
- **Helicone-OSS** — proxy + monitor

### 8.9 Supply Chain
- **modelscan** (Protect AI) — 악성 pickle
- **picklescan** — pickle 보안
- **safetensors** (Hugging Face) — 안전 형식
- **MLflow** — 모델 registry
- **DVC** — 데이터 버전
- **CycloneDX ML** — SBOM
- **cosign** + **sigstore** — 서명

### 8.10 Agent (Course10)
- **MCP** (Anthropic) — Model Context Protocol
- **smolagents** (HF) — 가벼운 agent
- **OpenAI Agents SDK**
- **e2b-dev** — code 실행 sandbox
- **AgentBench** (THU) — 8 환경 벤치
- **SWE-bench** — Software Engineering
- **GAIA** / **WebArena** / **OSWorld** — agent 능력 측정

---

## 9. Course8 - AI Safety

- **garak** all probes — 종합 jailbreak
- **PyRIT** — multi-turn
- **TrojAI Tools** (NIST) — 백도어
- **Neural-Cleanse** — 백도어 탐지
- **TextAttack PoisonRecipe** — poisoning 시뮬
- **MIA-Bench** / **ml-privacy-meter** — Membership Inference
- **opacus** + **TF Privacy** — DP
- **MarkLLM** / **lm-watermarking** — 워터마킹
- **smoothing** — certified robustness
- **Z3** / **Marabou** — 형식 검증
- **alpha-beta-CROWN** / **ERAN** — NN verification
- **AI-Verify** (Singapore IMDA) — DPIA
- **responsibleai** (MS) + **fairlearn** + **AIF360** — 책임 AI

---

## 10. Course9 - Autonomous Security

- **stable-baselines3** / **Ray RLlib** / **CleanRL** / **OpenAI Gym** — RL
- **ChromaDB** / **FAISS** / **Qdrant** / **Weaviate** / **pgvector** — 메모리
- **MLflow** + **DVC** — 모델 버전
- **NATS** / **RabbitMQ** / **Redis Pub/Sub** — 통신
- **Temporal** / **Airflow** / **Prefect** / **dagster** — workflow
- **k3s** / **Kubernetes** — 배포

---

## 11. Course11-12 - Battle (Red vs Blue)

위 모든 도구 + 통합 흐름. 추가:
- **CCC battle-engine** (자체)
- **DetectionLab** — 학습 환경
- **SELKS** — Suricata stack 통합

---

## 12. Course13 - Attack Advanced

위 attack 도구 + AD/Cloud 특화:
- **certipy** — AD CS abuse
- **Rubeus** — Kerberos 공격
- **mimikatz** / **pypykatz** — 자격증명 dump
- **Pacu** — AWS pentest
- **CloudGoat** — 학습 환경
- **dependency-confusion** 시뮬

---

## 13. Course14 - SOC Advanced

위 SOC 도구 + 통합:
- **chainsaw** + **hayabusa** — 헌팅 (Rust)
- **GRR** — Google Rapid Response
- **IRIS-DFIR** — modern 사고 관리
- **vector.dev** — modern 로그 파이프라인
- **DeTT&CT** — coverage 측정

---

## 14. Course16 - Physical Pentest

- **proxmark3** + **mfoc** + **mifare-classic-tool** — RFID/NFC
- **DuckyScript** + **WHID** + **O.MG cable** — USB HID
- **hackrf** + **gnuradio** + **urh** — RF/SDR
- **kismet** + **wifite** + **airgeddon** — WiFi
- **cameradar** — IP 카메라
- **theHarvester** + **SpiderFoot** — OSINT (재사용)

---

## 15. Course17 - IoT Security

- **mosquitto** (MQTT broker)
- **mosquitto_sub/pub** — MQTT 클라이언트
- **aiocoap** — CoAP (Python)
- **binwalk** — 펌웨어 분석
- **firmwalker** — 펌웨어 secret 검색
- **MQTT-PWN** — MQTT 공격 자동화
- **socat** + **pyserial** — 시리얼 분석
- **bluez** + **bluetoothctl** — BLE

---

## 16. 카테고리별 빠른 참조

### 16.1 가장 많이 사용 (★★★)

| 도구 | 용도 |
|------|------|
| **nmap** | 모든 포트 스캐닝 |
| **Trivy** | 모든 CVE 스캔 |
| **Wazuh** | SIEM 통합 |
| **Suricata** | IDS/IPS |
| **Falco** | 런타임 보안 |
| **Volatility 3** | 메모리 포렌식 |
| **garak** | LLM 보안 |
| **Atomic Red Team** | 시뮬 |
| **Sigma** | universal rule |
| **Velociraptor** | live forensic |

### 16.2 학습 권장 순서

1. **기본기**: nmap → curl → ssh → tcpdump
2. **Web**: whatweb → nikto → sqlmap → XSStrike → jwt_tool
3. **Network**: wireshark → ettercap → bettercap
4. **System**: LinPEAS → metasploit → sliver
5. **Defense**: Suricata → Wazuh → Falco → ModSecurity
6. **AI**: Ollama → LangChain → garak → llm-guard
7. **Cloud**: Trivy → Prowler → kube-bench → kubescape
8. **Forensic**: Volatility → Plaso → chainsaw → kestrel

---

## 17. 환경 준비 — 한 명령으로 표준 도구 설치

```bash
ssh ccc@192.168.0.112    # attacker VM

# 기본 (apt)
sudo apt update && sudo apt install -y \
  nmap masscan amap fping arp-scan netcat-openbsd \
  whatweb httpie wafw00f \
  nikto wapiti gobuster ffuf dirb dirsearch \
  sqlmap hydra medusa john hashcat hashid \
  tcpdump tshark wireshark-common termshark \
  bluez bluez-tools \
  steghide outguess \
  metasploit-framework exploitdb \
  bloodhound bloodhound.py impacket-scripts \
  proxychains4 sshuttle autossh socat \
  iodine \
  aircrack-ng wifite reaver bully \
  nftables fail2ban \
  suricata suricata-update \
  wazuh-agent \
  jq lnav osquery auditd aide \
  yara binwalk radare2 ghidra \
  python3-pip python3-venv git curl wget \
  pandoc texlive-xetex fonts-nanum

# Go 도구
go install github.com/projectdiscovery/{nuclei,subfinder,httpx,naabu}/v3/cmd/...@latest
go install github.com/jpillora/chisel@latest
go install github.com/hahwul/dalfox/v2@latest

# Python venv (LLM 보안)
python3 -m venv ~/.venv-llm && source ~/.venv-llm/bin/activate
pip install --upgrade pip
pip install garak llm-guard guardrails-ai langchain langgraph langfuse \
  promptfoo deepeval ragas trulens-eval \
  presidio-analyzer presidio-anonymizer scrubadub \
  opacus textattack \
  modelscan picklescan \
  shap lime captum transformer_lens \
  responsibleai fairlearn aif360

# Cloud 도구
docker pull toniblyx/prowler:latest
pip install scoutsuite

# K8s 도구
docker pull aquasec/kube-bench:latest
curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | bash

# crowdsec
curl -s https://install.crowdsec.net | sudo sh
sudo apt install -y crowdsec crowdsec-firewall-bouncer-nftables

# 자체 git clone (PEASS, jwt_tool, sigma, XSStrike, etc)
mkdir -p ~/tools && cd ~/tools
git clone https://github.com/peass-ng/PEASS-ng.git
git clone https://github.com/ticarpi/jwt_tool.git
git clone https://github.com/SigmaHQ/sigma.git
git clone https://github.com/s0md3v/XSStrike.git
git clone https://github.com/swisskyrepo/SSRFmap.git
git clone https://github.com/redcanaryco/atomic-red-team.git
git clone https://github.com/mitre/caldera.git --recursive
git clone https://github.com/Velocidex/velociraptor.git
git clone https://github.com/sigstore/cosign.git
```

---

## 18. 도구별 라이선스 / 위험도

| 도구 | 라이선스 | 운영 위험 |
|------|---------|----------|
| nmap | Nmap Public Source License | 합법 (스캔) — 허가 필요 |
| metasploit | BSD-3 | 합법 (실습 환경 한정) |
| sliver | GPL-3 | 합법 (점검 목적) |
| sqlmap | GPL-2 | 점검 동의 필수 |
| aircrack-ng | GPL-2 | 본인 AP 만 |
| gophish | MIT | 사내 시뮬만 |
| evilginx2 | BSD | **본인 시스템만** (MFA 우회) |
| garak | Apache-2 | 자기 모델 |
| wazuh | GPLv2 | OK |
| suricata | GPL-2 | OK |
| OpenSCAP | LGPL | OK |

> ⚠ **법적 경고**: 모든 공격 도구는 본인 소유 또는 명시적 서면 허가 받은 시스템에만 사용. 무단 사용은 형사처벌.

---

## 19. 통계

- **카테고리**: 17개 영역
- **도구 합계**: ~150종
- **상용 도구**: 0 (모두 OSS)
- **실제 설치 완료** (attacker VM): 15종
- **lecture matrix 매핑**: course1-7 detailed (105 weekly), course8-14 detailed (105 weekly), course16-17 압축

학생 학습 목표: 14주 동안 **150+ 도구를 흐름에 따라 사용** + 자신의 도구 카탈로그 (메모) 작성.
