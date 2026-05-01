"""Cyber range fixture generators.

각 generator 는 합성 보안 로그/이벤트를 생성한다. lab task 의 `fixtures` 필드에
명세된 generator 가 호출되어 cyber range VM 에 사전 주입된다.

공통 인터페이스:
    generate(seed: int, **params) -> Iterator[str]
    각 line 은 적절한 형식 (syslog/JSON/etc) 의 한 이벤트.

재현성: seed 고정 시 동일 출력 (학생/모델 마다 동일 환경 보장).
"""
from . import lolbas_log, auth_log, web_access, suricata_alert, wazuh_alert, firewall_log

__all__ = ["lolbas_log", "auth_log", "web_access", "suricata_alert", "wazuh_alert", "firewall_log"]
