# EG Catalog Layer — 인프라 무관 read-only 메타 카탈로그

모든 EG instance (eg-6v6 / 향후 다른 인프라) 가 *참조* 하는 공유 카탈로그.
*경험* 이 아닌 *지식·정의* 만 보관. git 으로 버전 관리.

## 파일

| 파일 | 내용 | 개수 |
|------|------|------|
| `missions.yaml` | 9 Mission 정의 (M1~M9) + cross-cutting tag + 관계 | 9 |
| `skills.yaml` | bastion 의 33 skill ↔ Mission 매핑 (primary + secondary) | 33 |
| `concepts.yaml` | 외부 표준 (MITRE / NIST / OWASP / ISO27001 / SOC2 / PCI-DSS) | 52 |

## 사용

deploy 시점에 EG instance 의 sqlite 로 import:

```bash
# 6v6 머신 (192.168.0.110) 에서
python3 scripts/eg/import_catalog.py --db /var/eg/eg-6v6.db
```

import 동작:
1. `missions.yaml` → `nodes.type='Mission'` upsert
2. `skills.yaml` → `nodes.type='Skill'` upsert + Skill `belongs_to` Mission edge
3. `concepts.yaml` → `nodes.type='Concept'` upsert + Concept `relates_to` Mission edge

import 후 EG application 측에서 카탈로그 노드는 read-only (수정 거부).

## 확장 규칙

- 새 Skill 추가: `packages/bastion/skills.py` 의 SKILLS dict 갱신 + `skills.yaml` 동기화
- 새 외부 표준 추가: `concepts.yaml` 에 entry 추가 (예: ISMS-P, GDPR)
- Mission 수 변경: 9 가 paper 본문에 고정되어 있으므로 **변경 금지** — 신규 mission 발생 시 별도 paper 또는 부록
