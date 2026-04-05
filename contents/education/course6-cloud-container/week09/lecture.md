# Week 09: 클라우드 보안 기초

## 학습 목표
- 클라우드 컴퓨팅의 3가지 모델(IaaS, PaaS, SaaS)을 이해한다
- IAM(Identity and Access Management)의 원칙을 설명할 수 있다
- VPC와 Security Group으로 네트워크 격리를 설계할 수 있다
- 공유 책임 모델(Shared Responsibility Model)을 이해한다

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

# Week 09: 클라우드 보안 기초

## 학습 목표
- 클라우드 컴퓨팅의 3가지 모델(IaaS, PaaS, SaaS)을 이해한다
- IAM(Identity and Access Management)의 원칙을 설명할 수 있다
- VPC와 Security Group으로 네트워크 격리를 설계할 수 있다
- 공유 책임 모델(Shared Responsibility Model)을 이해한다

---

## 1. 클라우드 컴퓨팅 개요

### 서비스 모델

| 모델 | 사용자 관리 | 제공자 관리 | 예시 |
|------|-----------|-----------|------|
| **IaaS** | OS, 앱, 데이터 | 네트워크, 스토리지, 서버 | AWS EC2, Azure VM |
| **PaaS** | 앱, 데이터 | OS, 런타임, 인프라 | Heroku, AWS Elastic Beanstalk |
| **SaaS** | 데이터 | 전부 | Gmail, Office 365 |

### 공유 책임 모델

```
사용자 책임          |  제공자 책임
---------------------|--------------------
데이터 암호화         |  물리적 보안
접근 제어(IAM)       |  네트워크 인프라
OS 패치(IaaS)       |  하이퍼바이저
애플리케이션 보안     |  데이터센터 보안
네트워크 설정        |  하드웨어 유지보수
```

핵심: "클라우드에서의 보안"은 사용자 책임, "클라우드 자체의 보안"은 제공자 책임이다.

---

## 2. IAM (Identity and Access Management)

> **이 실습을 왜 하는가?**
> "클라우드 보안 기초" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

IAM은 "누가(Who) 무엇을(What) 어떤 조건에서(When) 할 수 있는가"를 제어한다.

### 2.1 핵심 개념

| 개념 | 설명 | 예시 |
|------|------|------|
| **User** | 개별 사용자 계정 | admin@company.com |
| **Group** | 사용자 묶음 | developers, admins |
| **Role** | 임시 권한 위임 | EC2가 S3 접근 |
| **Policy** | 권한 규칙 (JSON) | S3 읽기 허용 |

### 2.2 IAM 정책 예시

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
```

### 2.3 최소 권한 원칙 (Principle of Least Privilege)

```
나쁜 예: "Action": "*", "Resource": "*"    → 모든 권한 부여
좋은 예: "Action": "s3:GetObject"          → 필요한 권한만
```

### 2.4 IAM 보안 모범 사례

1. **root 계정 사용 금지**: 일상 업무에 root 사용하지 않기
2. **MFA 필수**: 모든 사용자에게 다중 인증 적용
3. **최소 권한**: 필요한 권한만 부여
4. **정기 감사**: 사용하지 않는 계정/키 삭제
5. **역할 사용**: 장기 자격증명 대신 임시 역할

---

## 3. VPC (Virtual Private Cloud)

VPC는 클라우드 내의 격리된 가상 네트워크이다.

### 3.1 VPC 구성요소

```
VPC (10.0.0.0/16)
├── Public Subnet (10.0.1.0/24)    ← 인터넷 접근 가능
│   ├── Internet Gateway
│   ├── Web Server
│   └── NAT Gateway
├── Private Subnet (10.0.2.0/24)   ← 인터넷 직접 접근 불가
│   ├── Application Server
│   └── → NAT Gateway 통해 외부 접근
└── DB Subnet (10.0.3.0/24)        ← 완전 격리
    └── Database
```

### 3.2 서브넷 설계 원칙

| 서브넷 | 용도 | 인터넷 | 구성 |
|--------|------|--------|------|
| Public | 웹 서버, 로드밸런서 | 직접 접근 | IGW 연결 |
| Private | 앱 서버 | NAT 통해 아웃바운드만 | NAT GW 연결 |
| Isolated | DB, 내부 서비스 | 불가 | 라우팅 없음 |

---

## 4. Security Group과 NACL

### 4.1 Security Group (보안 그룹)

인스턴스 수준의 방화벽이다. **상태 기반(Stateful)** 이다.

```
# 웹 서버 Security Group
인바운드:
  - TCP 80  (HTTP)   : 0.0.0.0/0
  - TCP 443 (HTTPS)  : 0.0.0.0/0
  - TCP 22  (SSH)    : 관리자 IP만

아웃바운드:
  - 전체 허용 (기본값)
```

```
# DB Security Group
인바운드:
  - TCP 3306 (MySQL) : 앱 서버 SG만 허용
  - TCP 22   (SSH)   : 관리자 IP만

아웃바운드:
  - 전체 허용
```

### 4.2 NACL (Network ACL)

서브넷 수준의 방화벽이다. **비상태(Stateless)** 이다.

| 항목 | Security Group | NACL |
|------|---------------|------|
| 적용 범위 | 인스턴스 | 서브넷 |
| 상태 | Stateful | Stateless |
| 규칙 | 허용만 | 허용 + 거부 |
| 평가 | 모든 규칙 | 번호 순서 |
| 기본 | 모두 거부 | 모두 허용 |

---

## 5. 실습 환경 매핑

실습 환경의 네트워크를 클라우드 VPC 개념으로 매핑해보자.

### 우리 실습 환경의 네트워크

```
외부 네트워크 (192.168.208.0/24)    ← Public Subnet에 해당
├── opsclaw (10.20.30.201)       ← 관리 서버
├── secu    (10.20.30.1)       ← 방화벽/IPS
├── web     (10.20.30.80)       ← 웹 서버
└── siem    (10.20.30.100)       ← SIEM

내부 네트워크 (10.20.30.0/24)       ← Private Subnet에 해당
├── secu    (10.20.30.1)            ← 게이트웨이 역할
├── web     (10.20.30.80)           ← 내부 웹 서비스
└── siem    (10.20.30.100)          ← 내부 모니터링
```

### 실습: nftables로 Security Group 시뮬레이션

> **실습 목적**: 클라우드 IAM과 VPC의 보안 원리를 실습 환경에서 체험하고 개념을 체화하기 위해 수행한다
>
> **배우는 것**: API 키 인증이 IAM의 Authentication/Authorization 원리와 동일하며, nftables 규칙이 Security Group/NACL과 같은 역할임을 이해한다
>
> **결과 해석**: API 키 없이 401/403 응답이면 인증 실패이고, nftables 규칙의 accept/drop이 클라우드 보안 그룹의 allow/deny와 대응한다
>
> **실전 활용**: AWS/Azure 환경에서 IAM 최소 권한 설정, VPC 서브넷 분리, Security Group 설계에 활용한다

```bash
# secu 서버에서 nftables 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
sudo nft list ruleset

# 이것이 클라우드의 Security Group/NACL과 같은 역할
```

---

## 6. 실습: IAM 개념 체험

OpsClaw의 API 인증이 IAM의 축소판이다.

```bash
# API 키 없이 요청 → 인증 실패
curl -s http://localhost:8000/projects | head -5

# API 키 포함 요청 → 인증 성공
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects | head -5

# 이것이 IAM의 핵심 원리:
# 1. 신원 확인 (Authentication): API 키로 "누구인가" 확인
# 2. 권한 확인 (Authorization): "무엇을 할 수 있는가" 확인
```

---

## 7. 클라우드 보안 위협 Top 5

| 순위 | 위협 | 설명 |
|------|------|------|
| 1 | IAM 설정 오류 | 과도한 권한, 키 노출 |
| 2 | 데이터 유출 | S3 공개 설정, 암호화 미적용 |
| 3 | 설정 오류 | 기본 설정 그대로 사용 |
| 4 | 불충분한 로깅 | 감사 추적 미설정 |
| 5 | 내부자 위협 | 권한 남용, 키 유출 |

---

## 8. 보안 체크리스트

- [ ] root 계정에 MFA가 적용되어 있는가?
- [ ] 사용자에게 최소 권한만 부여했는가?
- [ ] VPC가 적절히 서브넷으로 분리되어 있는가?
- [ ] Security Group이 최소 포트만 허용하는가?
- [ ] 미사용 IAM 키/계정을 삭제했는가?
- [ ] CloudTrail 등 감사 로깅이 활성화되어 있는가?

---

## 핵심 정리

1. 공유 책임 모델: 클라우드 "위의" 보안은 사용자 책임이다
2. IAM은 최소 권한 원칙을 적용하고, MFA를 필수로 설정한다
3. VPC로 네트워크를 격리하고, 서브넷으로 계층을 분리한다
4. Security Group(인스턴스)과 NACL(서브넷)로 트래픽을 제어한다
5. 클라우드 보안의 핵심은 "설정 오류 방지"이다

---

## 다음 주 예고
- Week 10: 클라우드 설정 오류 - S3 노출, 과도한 IAM 권한

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
