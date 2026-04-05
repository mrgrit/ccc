# Week 14: IaC 보안

## 학습 목표
- Infrastructure as Code(IaC)의 개념과 보안 이점을 이해한다
- Terraform의 기본 문법과 보안 관련 설정을 작성할 수 있다
- IaC 보안 스캐닝 도구(Checkov, tfsec)를 사용할 수 있다
- IaC 파이프라인에 보안 검증을 통합하는 방법을 익힌다

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

# Week 14: IaC 보안

## 학습 목표
- Infrastructure as Code(IaC)의 개념과 보안 이점을 이해한다
- Terraform의 기본 문법과 보안 관련 설정을 작성할 수 있다
- IaC 보안 스캐닝 도구(Checkov, tfsec)를 사용할 수 있다
- IaC 파이프라인에 보안 검증을 통합하는 방법을 익힌다

---

## 1. Infrastructure as Code란?

IaC는 인프라를 코드로 정의하고 버전 관리하는 방법이다.

### 수동 관리 vs IaC

| 항목 | 수동 관리 | IaC |
|------|----------|-----|
| 일관성 | 사람마다 다름 | 항상 동일 |
| 감사 | 누가 변경했는지 불명확 | Git 이력 추적 |
| 재현성 | 재현 어려움 | 동일 환경 즉시 재현 |
| 속도 | 느림 | 빠름 |
| 보안 검증 | 사후 점검 | 배포 전 자동 검증 |

### 주요 IaC 도구

| 도구 | 유형 | 대상 |
|------|------|------|
| **Terraform** | 선언적 | 멀티 클라우드 |
| **CloudFormation** | 선언적 | AWS 전용 |
| **Ansible** | 명령적 | 서버 구성 |
| **Pulumi** | 프로그래밍 | 멀티 클라우드 |

---

## 2. Terraform 기본

> **이 실습을 왜 하는가?**
> "IaC 보안" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> Docker/클라우드/K8s 보안 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 HCL (HashiCorp Configuration Language)

```hcl
# main.tf - AWS EC2 인스턴스 생성
provider "aws" {
  region = "ap-northeast-2"   # 서울 리전
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

### 2.2 Terraform 워크플로

> **실습 목적**: Infrastructure as Code(Terraform) 파일의 보안 취약점을 배포 전에 탐지하는 방법을 체험하기 위해 수행한다
>
> **배우는 것**: Terraform 코드에서 0.0.0.0/0 SSH 허용, 하드코딩 비밀번호, 암호화 미설정 등 흔한 보안 오류를 식별하는 방법과 Checkov/tfsec 자동 스캔 원리를 이해한다
>
> **결과 해석**: Checkov의 FAILED 항목은 즉시 수정 필요한 보안 위반이고, CKV_ 코드로 구체적 규칙을 확인한다
>
> **실전 활용**: CI/CD 파이프라인에 IaC 보안 스캔을 통합하여 취약한 인프라 배포를 자동 차단하는 보안 게이트에 활용한다

Terraform은 init -> plan -> apply 순서로 인프라를 배포한다. plan 단계에서 변경 사항을 검토한 후 apply로 실제 적용한다.

```bash
terraform init      # 플러그인 다운로드
terraform plan      # 변경 사항 미리보기 (실제 변경 없음)
terraform apply     # 실제 적용 (승인 필요)
terraform destroy   # 인프라 삭제 (주의: 복구 불가)
```

---

## 3. Terraform 보안 설정

### 3.1 안전한 Security Group

```hcl
# 나쁜 예: 전 세계에서 SSH 허용
resource "aws_security_group" "bad" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # 전체 허용!
  }
}

# 좋은 예: 관리자 IP만 허용
resource "aws_security_group" "good" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.20.30.0/24"]  # 내부 네트워크만
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "secure-sg"
  }
}
```

### 3.2 암호화된 S3 버킷

```hcl
resource "aws_s3_bucket" "secure" {
  bucket = "company-secure-data"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure" {
  bucket = aws_s3_bucket.secure.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "secure" {
  bucket = aws_s3_bucket.secure.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "secure" {
  bucket = aws_s3_bucket.secure.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

### 3.3 시크릿 관리

```hcl
# 나쁜 예: 하드코딩된 비밀번호
resource "aws_db_instance" "bad" {
  password = "MyP@ssw0rd123"   # 코드에 비밀번호!
}

# 좋은 예: 변수 + tfvars (gitignore)
variable "db_password" {
  type      = string
  sensitive = true     # plan/apply 출력에서 마스킹
}

resource "aws_db_instance" "good" {
  password = var.db_password
}

# terraform.tfvars (반드시 .gitignore에 추가)
# db_password = "MyP@ssw0rd123"
```

---

## 4. IaC 보안 스캐닝

### 4.1 Checkov

Bridgecrew(Palo Alto)의 오픈소스 IaC 스캐너이다.

```bash
# 설치
pip install checkov

# Terraform 파일 스캔
checkov -d /path/to/terraform/

# 특정 파일 스캔
checkov -f main.tf

# JSON 출력
checkov -d . -o json > checkov-result.json
```

### Checkov 결과 예시

```
Passed checks: 12, Failed checks: 5, Skipped checks: 0

Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
  FAILED for resource: aws_s3_bucket.data
  File: main.tf:15-20

Check: CKV_AWS_24: "Ensure no security groups allow ingress from 0.0.0.0/0 to port 22"
  FAILED for resource: aws_security_group.web
  File: main.tf:25-35
```

### 4.2 tfsec

Aqua Security의 Terraform 전용 스캐너이다.

```bash
# 설치
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

# 스캔
tfsec /path/to/terraform/

# 심각도 필터
tfsec . --minimum-severity HIGH
```

### 4.3 도구 비교

| 도구 | 지원 IaC | 특징 |
|------|---------|------|
| Checkov | Terraform, CloudFormation, K8s, Docker | 가장 포괄적 |
| tfsec | Terraform | Terraform 특화, 빠름 |
| Terrascan | Terraform, K8s, Docker | OPA 기반 정책 |
| KICS | 15+ IaC 형식 | Checkmarx 지원 |

---

## 5. CI/CD 파이프라인 통합

### 5.1 GitHub Actions에서 IaC 스캔

```yaml
# .github/workflows/iac-security.yaml
name: IaC Security Scan
on:
  pull_request:
    paths: ["terraform/**"]

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          soft_fail: false    # 실패 시 PR 차단

  tfsec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          working_directory: terraform/
```

### 5.2 보안 게이트 (Security Gate)

```
코드 작성 → PR 생성 → IaC 스캔 → [통과?] → 리뷰 → 배포
                                   ↓ 실패
                              PR 차단 + 수정 요청
```

---

## 6. 실습: IaC 보안 스캐닝

### 실습 1: 취약한 Terraform 분석

```bash
# 취약한 Terraform 파일 작성
mkdir -p /tmp/iac-lab && cd /tmp/iac-lab

cat > main.tf << 'HCLEOF'
resource "aws_security_group" "web" {
  name = "web-sg"
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "company-data-2026"
}

resource "aws_db_instance" "main" {
  engine         = "mysql"
  instance_class = "db.t3.micro"
  password       = "admin123"
  publicly_accessible = true
}
HCLEOF
```

### 실습 2: LLM으로 IaC 보안 검토

Terraform 코드를 LLM에게 전달하여 보안 취약점을 자동 분석시킨다. 0.0.0.0/0 허용, 암호화 미설정 등을 식별할 수 있다.

```bash
# Terraform 코드를 변수에 저장
TF_CODE=$(cat /tmp/iac-lab/main.tf)

# Ollama API로 IaC 보안 분석 요청
# 변수 치환을 위해 큰따옴표 + 이스케이프 사용
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"클라우드 보안 전문가입니다. Terraform 코드의 보안 문제를 분석합니다.\"},
      {\"role\": \"user\", \"content\": \"다음 Terraform 코드의 보안 문제를 모두 찾고 수정 방법을 제시해주세요:\\n$TF_CODE\"}
    ]
  }" | python3 -m json.tool
```

### 실습 3: Docker Compose를 IaC 관점에서 분석

```bash
# Docker Compose도 IaC의 일종이다
# Checkov으로 Compose 파일 스캔 가능
pip install checkov 2>/dev/null

# web 서버의 Compose 파일 스캔
checkov -f /tmp/secure-lab/docker-compose.yaml --framework dockerfile 2>/dev/null || \
  echo "Checkov으로 Docker Compose 보안 점검 가능"
```

---

## 7. IaC 보안 체크리스트

- [ ] 코드에 하드코딩된 시크릿이 없는가?
- [ ] Security Group이 0.0.0.0/0에 민감 포트를 허용하지 않는가?
- [ ] S3 버킷에 퍼블릭 액세스 차단이 설정되어 있는가?
- [ ] 스토리지/DB에 암호화가 적용되어 있는가?
- [ ] CI/CD에 IaC 스캔이 통합되어 있는가?
- [ ] terraform.tfvars가 .gitignore에 포함되어 있는가?
- [ ] Terraform state 파일이 안전하게 저장되는가?

---

## 핵심 정리

1. IaC는 인프라를 코드로 관리하여 일관성, 감사, 보안 검증을 보장한다
2. Terraform에서 시크릿을 하드코딩하지 않고 sensitive 변수를 사용한다
3. Checkov/tfsec으로 배포 전에 보안 설정 오류를 자동 탐지한다
4. CI/CD 파이프라인에 IaC 스캔을 통합하여 보안 게이트를 구축한다
5. Docker Compose도 IaC의 일종이므로 동일한 보안 원칙을 적용한다

---

## 다음 주 예고
- Week 15: 기말고사 - 클라우드 보안 설계

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
