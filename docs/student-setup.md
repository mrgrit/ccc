# 학생 PC 셋업 — 6v6 학습 환경 접속

> 모든 lab/lecture 콘텐츠 는 `6v6-host` 와 `ollama-host` 라는 *alias* 를 사용한다.
> 학생 PC 의 hosts 파일에서 alias → 실 IP 매핑 후 사용. 환경 (학교/집/다른 네트워크)
> 이동 시 hosts 파일 한 줄만 변경.

## 1. hosts 파일 매핑 (필수)

### Windows
관리자 권한 메모장 으로 `C:\Windows\System32\drivers\etc\hosts` 편집:
```
# 학교 환경 예시
192.168.0.110   6v6-host    ollama-host

# 집 환경 예시 (한 줄만 변경)
# 192.168.0.76    6v6-host
# 192.168.0.109   ollama-host
```

### Linux / macOS
```bash
sudo nano /etc/hosts
# 동일 내용 추가
```

### 검증
```bash
ping 6v6-host
ping ollama-host
```

## 2. SSH config (Windows: `C:\Users\<USER>\.ssh\config`, Linux: `~/.ssh/config`)

```
# 6v6 학습 환경 — 4-tier chained topology
Host 6v6-bastion
    HostName 6v6-host        # hosts 파일이 실 IP 로 resolve
    Port 2204
    User ccc

Host 6v6-attacker
    HostName 6v6-host
    Port 2202
    User ccc

# fw / ips / web / siem / portal — bastion 경유 ProxyJump
# 6v6-secu = fw 의 legacy alias (4-VM 시대 호환)
Host 6v6-fw 6v6-secu 6v6-ips 6v6-web 6v6-siem 6v6-portal
    ProxyJump 6v6-bastion
    User ccc
    StrictHostKeyChecking no
    UserKnownHostsFile NUL    # Linux/macOS: /dev/null
```

### Windows 의 config 권한
```powershell
icacls C:\Users\<USER>\.ssh\config /inheritance:r /grant:r <USER>:F
```

## 3. 첫 접속 (password = `ccc`)

```bash
ssh 6v6-bastion   # 학생 진입점 (bastion 컨테이너 shell)
ssh 6v6-attacker  # 공격 도구 (curl/nmap/sqlmap/...)
ssh 6v6-fw        # 방화벽 (ProxyJump bastion)
ssh 6v6-web       # web (Apache + ModSec + JuiceShop reverse)
ssh 6v6-siem      # Wazuh manager
```

## 4. 환경 이동 시 절차

새 네트워크 (예: 집 → 학교) 이동:
```bash
# Windows hosts 파일 — IP 만 변경
192.168.0.110   6v6-host    ollama-host

# ssh config / lab content / docs 변경 불필요
ssh 6v6-bastion
```

## 5. lab content 의 endpoint 형식

모든 lab/lecture 가 다음 alias 사용:
- `http://6v6-host:9200` — Bastion API
- `http://6v6-host:2202` / `:2204` — SSH (실제 학생 명령은 ssh 6v6-attacker / 6v6-bastion)
- `http://ollama-host:11434` — Ollama LLM 서버
- `http://juice.6v6.lab/` — Juice Shop (학생 브라우저 / curl)
- `http://10.20.x.x` — 컨테이너 내부 IP (고정, 변경 X)

## 6. 6v6 호스트 운영자 (선택)

학습 환경 의 6v6 docker compose 가 돌고 있는 호스트 (e.g. 192.168.0.110) 운영자:
```bash
git clone https://github.com/mrgrit/6v6.git
cd 6v6
docker compose up -d --build
```

학생 PC 의 hosts 파일 의 `6v6-host` 가 이 호스트 IP 와 매핑되도록 안내.
